from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from app.models.entities import Product, Message, Conversation
from app.main import create_app
from app.config import Settings
from app.errors import AppError
from scripts.seed import seed


def send(client, cid, text, rid=None):
    return client.post(
        f"/api/v1/conversations/{cid}/messages",
        json={"content": text, "client_message_id": rid or str(uuid4())},
    )


def test_health_and_meta(client):
    assert client.get("/api/v1/health").json()["database"] == "ready"
    assert client.get("/api/v1/meta").json()["mode"] == "demo"


def test_catalogue_pagination_filter_and_detail(client):
    data = client.get(
        "/api/v1/products", params={"max_price_inr": 60000, "min_ram_gb": 16, "page_size": 2}
    ).json()
    assert len(data["items"]) == 2 and data["total"] >= 2
    assert all(p["price_inr"] <= 60000 and p["ram_gb"] >= 16 for p in data["items"])
    assert client.get("/api/v1/products/CC-011").json()["price_inr"] == 60000
    assert client.get("/api/v1/products/missing").status_code == 404
    assert client.get("/api/v1/products", params={"page_size": 101}).status_code == 422
    assert client.get("/api/v1/products", params={"sort": "price;DROP TABLE products"}).status_code == 422


def test_seed_is_repeatable(factory):
    seed(factory)
    with factory() as s:
        assert s.scalar(select(func.count()).select_from(Product)) == 40


def test_unknown_weight_does_not_pass(client):
    rows = client.get("/api/v1/products", params={"max_weight_kg": 20, "page_size": 100}).json()["items"]
    assert rows and all(r["weight_kg"] is not None for r in rows)


def test_vague_request_then_complete_and_update(client):
    c = client.post("/api/v1/conversations")
    assert c.status_code == 201
    cid = c.json()["id"]
    a = send(client, cid, "I need a laptop for college.").json()
    assert a["response_type"] == "clarification"
    b = send(client, cid, "Programming under 80000, 16 GB RAM. I carry it daily.").json()
    assert b["response_type"] == "recommendations" and len(b["recommendations"]) == 2
    assert b["requirements"]["preferences"] == ["lightweight"]
    c = send(client, cid, "Actually my budget is 60000").json()
    assert c["requirements"]["use_cases"] == ["programming"]
    assert c["requirements"]["min_ram_gb"] == 16
    assert all(x["product"]["price_inr"] <= 60000 for x in c["recommendations"])
    restored = client.get(f"/api/v1/conversations/{cid}").json()
    assert len(restored["messages"]) == 6 and restored["state_version"] == 3
    assert client.get("/api/v1/conversations").json()["total"] == 1


def test_complete_request_needs_no_question(client):
    cid = client.post("/api/v1/conversations").json()["id"]
    r = send(client, cid, "Laptop for programming under 80000 with 16 GB RAM").json()
    assert r["response_type"] == "recommendations"
    for card in r["recommendations"]:
        stored = client.get("/api/v1/products/" + card["product"]["id"]).json()
        assert card["product"] == stored


def test_no_match_budget_proposal_requires_confirmation(client):
    cid = client.post("/api/v1/conversations").json()["id"]
    r = send(client, cid, "Laptop for programming under 20000 with 16 GB RAM").json()
    assert r["response_type"] == "no_match" and r["recommendations"] == []
    assert r["requirements"]["budget_max_inr"] == 20000
    proposed = r["requirements"]["pending_budget"]
    assert proposed > 20000
    r = send(client, cid, "yes").json()
    assert r["requirements"]["budget_max_inr"] == proposed
    assert r["response_type"] == "recommendations"


def test_new_requirement_invalidates_proposal(client):
    cid = client.post("/api/v1/conversations").json()["id"]
    send(client, cid, "Programming under 20000, 16 GB RAM")
    r = send(client, cid, "Actually budget is 80000").json()
    assert r["requirements"]["pending_budget"] is None


def test_one_match(client):
    cid = client.post("/api/v1/conversations").json()["id"]
    r = send(client, cid, "General coursework under 28000").json()
    assert r["response_type"] == "recommendations" and len(r["recommendations"]) == 1
    assert r["recommendations"][0]["product"]["price_inr"] == 28000


def test_duplicate_is_idempotent_and_content_checked(client):
    cid = client.post("/api/v1/conversations").json()["id"]
    rid = str(uuid4())
    first = send(client, cid, "Programming under 80000", rid)
    repeated = send(client, cid, "Programming under 80000", rid)
    assert first.json() == repeated.json()
    assert len(client.get(f"/api/v1/conversations/{cid}").json()["messages"]) == 2
    assert send(client, cid, "Different content", rid).status_code == 409


def test_bad_message_and_unknown_conversation(client):
    cid = client.post("/api/v1/conversations").json()["id"]
    assert send(client, cid, " ").status_code == 422
    assert send(client, str(uuid4()), "hello").status_code == 404


def test_no_budget_and_ml_clarification(client):
    cid = client.post("/api/v1/conversations").json()["id"]
    r = send(client, cid, "Machine learning, no fixed budget").json()
    assert r["response_type"] == "clarification" and "cloud" in r["assistant_message"]
    r = send(client, cid, "Mostly cloud").json()
    assert r["response_type"] == "recommendations" and r["requirements"]["no_budget"]


def test_llm_failure_does_not_mutate(factory):
    class Broken:
        mode = "test"

        def extract(self, *args):
            raise AppError(504, "llm_timeout", "Timed out", True)

    with TestClient(create_app(Settings(_env_file=None), factory, Broken())) as client:
        cid = client.post("/api/v1/conversations").json()["id"]
        assert send(client, cid, "hello").status_code == 504
        state = client.get(f"/api/v1/conversations/{cid}").json()
        assert state["state_version"] == 0 and state["messages"] == []


def test_optimistic_conflict_prevents_overwrite(factory):
    from app.agent.demo import DemoExtractor

    class Racing(DemoExtractor):
        mode = "test"

        def extract(self, *args):
            with factory.begin() as s:
                c = s.scalar(select(Conversation))
                c.state_version += 1
            return super().extract(*args)

    with TestClient(create_app(Settings(_env_file=None), factory, Racing())) as client:
        cid = client.post("/api/v1/conversations").json()["id"]
        assert send(client, cid, "Programming under 80000").status_code == 409
        with factory() as s:
            assert s.scalar(select(func.count()).select_from(Message)) == 0


def test_cors(client):
    r = client.options(
        "/api/v1/conversations",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
    )
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_database_error_is_controlled(factory):
    factory.kw["bind"].dispose()
    with TestClient(create_app(Settings(_env_file=None), factory)) as client:
        r = client.get("/api/v1/health")
        assert r.status_code == 503 and r.json()["error"]["code"] == "database_unavailable"
