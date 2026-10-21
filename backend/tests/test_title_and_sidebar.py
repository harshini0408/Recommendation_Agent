"""Tests for conversation title generation and sidebar summaries endpoint."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.agent.title import generate_title, is_meaningful, _sanitize
from app.main import create_app
from app.config import Settings
from app.agent.demo import DemoExtractor
from app.models.entities import Conversation


def send(client, cid, text, rid=None):
    return client.post(
        f"/api/v1/conversations/{cid}/messages",
        json={"content": text, "client_message_id": rid or str(uuid4())},
    )


# ---------------------------------------------------------------------------
# Title module unit tests
# ---------------------------------------------------------------------------


def test_is_meaningful_rejects_greetings():
    assert not is_meaningful("Hi")
    assert not is_meaningful("Hello!")
    assert not is_meaningful("hey")
    assert not is_meaningful("Good morning")
    assert not is_meaningful("   ")
    assert not is_meaningful("")


def test_is_meaningful_accepts_real_queries():
    assert is_meaningful("I need a laptop for college under 80000")
    assert is_meaningful("Laptop for machine learning and programming")
    assert is_meaningful("Light laptop for video editing")


def test_is_meaningful_rejects_very_short():
    # Fewer than 3 words
    assert not is_meaningful("laptop budget")


def test_sanitize_strips_quotes():
    assert _sanitize('"College Laptop Under 80000"') == "College Laptop Under 80000"
    assert _sanitize("'ML Laptop'") == "ML Laptop"


def test_sanitize_rejects_empty():
    assert _sanitize("") is None
    assert _sanitize("   ") is None


def test_sanitize_truncates_long_title():
    long_title = "A " * 50  # 100 chars
    result = _sanitize(long_title)
    assert result is not None and len(result) <= 80


def test_sanitize_rejects_json_output():
    assert _sanitize('{"title": "something"}') is None


def test_generate_title_no_key_returns_fallback():
    """Without an API key, must return (fallback, 'fallback') without raising."""

    class FakeSettings:
        class _key:
            def get_secret_value(self):
                return ""
        groq_api_key = _key()
        groq_model = "openai/gpt-oss-20b"

    title, status = generate_title(FakeSettings(), "Laptop for programming under 80000")
    assert status == "fallback"
    assert "Laptop" in title or len(title) > 0


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


@pytest.fixture
def client(factory):
    settings = Settings(_env_file=None, llm_mode="demo", groq_api_key="")
    with TestClient(create_app(settings, factory, DemoExtractor())) as c:
        yield c


def test_title_returns_pending_for_empty_conversation(client):
    cid = client.post("/api/v1/conversations").json()["id"]
    r = client.post(f"/api/v1/conversations/{cid}/title")
    assert r.status_code == 200
    data = r.json()
    assert data["title_status"] == "pending"
    assert data["title"] is None


def test_title_returns_pending_for_greeting(client):
    cid = client.post("/api/v1/conversations").json()["id"]
    send(client, cid, "Hello there")
    r = client.post(f"/api/v1/conversations/{cid}/title")
    assert r.status_code == 200
    assert r.json()["title_status"] == "pending"


def test_title_generates_fallback_for_meaningful_message(client):
    cid = client.post("/api/v1/conversations").json()["id"]
    send(client, cid, "Laptop for programming and college under 80000")
    r = client.post(f"/api/v1/conversations/{cid}/title")
    assert r.status_code == 200
    data = r.json()
    # With empty API key in test settings, will be 'fallback' status
    assert data["title_status"] in ("generated", "fallback")
    assert data["title"] is not None and len(data["title"]) > 0


def test_title_idempotent_after_finalisation(client, factory):
    cid = client.post("/api/v1/conversations").json()["id"]
    send(client, cid, "Laptop for programming and college under 80000")
    # Set title directly
    with factory.begin() as session:
        c = session.get(Conversation, cid)
        c.title = "Programming College Laptop"
        c.title_status = "generated"

    r1 = client.post(f"/api/v1/conversations/{cid}/title")
    r2 = client.post(f"/api/v1/conversations/{cid}/title")
    assert r1.json() == r2.json()
    assert r1.json()["title"] == "Programming College Laptop"


def test_title_does_not_alter_state_version(client, factory):
    cid = client.post("/api/v1/conversations").json()["id"]
    send(client, cid, "Laptop for programming under 80000")
    with factory() as session:
        version_before = session.get(Conversation, cid).state_version
    client.post(f"/api/v1/conversations/{cid}/title")
    with factory() as session:
        version_after = session.get(Conversation, cid).state_version
    assert version_before == version_after


def test_title_does_not_alter_requirements(client, factory):
    cid = client.post("/api/v1/conversations").json()["id"]
    send(client, cid, "Laptop for programming under 80000")
    with factory() as session:
        reqs_before = session.get(Conversation, cid).requirements
    client.post(f"/api/v1/conversations/{cid}/title")
    with factory() as session:
        reqs_after = session.get(Conversation, cid).requirements
    assert reqs_before == reqs_after


def test_title_unknown_conversation_returns_404(client):
    r = client.post(f"/api/v1/conversations/{uuid4()}/title")
    assert r.status_code == 404


def test_batch_summaries_returns_known_ids(client):
    cid1 = client.post("/api/v1/conversations").json()["id"]
    cid2 = client.post("/api/v1/conversations").json()["id"]
    r = client.post("/api/v1/conversations/summaries", json={"ids": [cid1, cid2]})
    assert r.status_code == 200
    ids = [s["id"] for s in r.json()]
    assert cid1 in ids and cid2 in ids


def test_batch_summaries_ignores_unknown_ids(client):
    cid = client.post("/api/v1/conversations").json()["id"]
    fake = str(uuid4())
    r = client.post("/api/v1/conversations/summaries", json={"ids": [cid, fake]})
    assert r.status_code == 200
    ids = [s["id"] for s in r.json()]
    assert cid in ids
    assert fake not in ids


def test_batch_summaries_returns_empty_for_no_ids(client):
    r = client.post("/api/v1/conversations/summaries", json={"ids": []})
    assert r.status_code == 200 and r.json() == []


def test_batch_summaries_sorted_by_recent_activity(client):
    """More recently updated conversation comes first."""
    import time
    cid1 = client.post("/api/v1/conversations").json()["id"]
    time.sleep(0.05)
    cid2 = client.post("/api/v1/conversations").json()["id"]
    r = client.post("/api/v1/conversations/summaries", json={"ids": [cid1, cid2]})
    result_ids = [s["id"] for s in r.json()]
    assert result_ids[0] == cid2  # more recently created


def test_conversation_detail_includes_title_fields(client):
    cid = client.post("/api/v1/conversations").json()["id"]
    r = client.get(f"/api/v1/conversations/{cid}")
    assert r.status_code == 200
    data = r.json()
    assert "title" in data
    assert "title_status" in data
    assert data["title_status"] == "pending"
