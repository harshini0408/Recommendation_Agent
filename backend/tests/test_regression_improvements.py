"""Comprehensive regression tests covering all 16 improvement and debugging requirements."""

from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.models.entities import Product
from app.schemas.requirements import Requirements, Change, Extraction
from app.agent.state import merge_state, _decode_value
from app.agent.tools import search_products
from app.errors import AppError


def send(client, cid, text, rid=None):
    return client.post(
        f"/api/v1/conversations/{cid}/messages",
        json={"content": text, "client_message_id": rid or str(uuid4())},
    )


def test_exact_failing_conversation_and_budget_retention(client):
    """Regression test 1 & 2: Failing multi-turn college ML conversation retains budget and proceeds."""
    cid = client.post("/api/v1/conversations").json()["id"]

    # Turn 1
    t1 = send(client, cid, "I would like to get a laptop for college that is under 80000").json()
    assert t1["response_type"] == "clarification"
    assert t1["requirements"]["budget_max_inr"] == 80000

    # Turn 2
    t2 = send(client, cid, "probably ML").json()
    assert t2["response_type"] == "clarification"
    assert "machine_learning" in t2["requirements"]["use_cases"]
    assert t2["requirements"]["budget_max_inr"] == 80000
    assert "locally" in t2["assistant_message"].lower() or "cloud" in t2["assistant_message"].lower()

    # Turn 3: Customer expresses uncertainty
    t3 = send(client, cid, "not sure").json()
    # Should NOT reset or classify as out_of_scope
    assert "I can help compare laptops in this synthetic catalogue. Tell me your use case" not in t3["assistant_message"]
    assert t3["requirements"]["budget_max_inr"] == 80000
    assert t3["requirements"]["ml_mode"] == "unsure"
    assert t3["response_type"] == "recommendations"
    assert len(t3["recommendations"]) == 2
    assert "ml_mode" in t3["requirements"]["provisional_assumptions"]

    # Turn 4: Customer confirms budget
    t4 = send(client, cid, "I already told my budget").json()
    assert "80,000" in t4["assistant_message"]
    assert t4["requirements"]["budget_max_inr"] == 80000
    assert t4["response_type"] == "recommendations"

    # Turn 5: "both"
    t5 = send(client, cid, "both").json()
    assert t5["requirements"]["ml_mode"] == "both"
    assert t5["requirements"]["budget_max_inr"] == 80000
    assert t5["response_type"] == "recommendations"
    assert len(t5["recommendations"]) == 2


def test_both_resolves_local_cloud_clarification(client):
    """Regression test 3: 'both' resolves ML clarification directly."""
    cid = client.post("/api/v1/conversations").json()["id"]
    t1 = send(client, cid, "Machine learning under 90000").json()
    assert t1["response_type"] == "clarification"
    t2 = send(client, cid, "both").json()
    assert t2["requirements"]["ml_mode"] == "both"
    assert t2["response_type"] == "recommendations"
    assert len(t2["recommendations"]) == 2


def test_explicit_unsure_does_not_cause_endless_loop(client):
    """Regression test 4: Explicit unsure generates provisional recommendations without looping."""
    cid = client.post("/api/v1/conversations").json()["id"]
    t1 = send(client, cid, "Machine learning under 80000").json()
    assert t1["response_type"] == "clarification"
    t2 = send(client, cid, "not sure").json()
    assert t2["response_type"] == "recommendations"
    assert t2["requirements"]["ml_mode"] == "unsure"
    # Sending another prompt should not repeat the clarification
    t3 = send(client, cid, "show me options").json()
    assert t3["response_type"] == "recommendations"
    assert t3["requirements"]["ml_mode"] == "unsure"


def test_complete_request_proceeds_without_unnecessary_questions(client):
    """Regression test 5: Complete request goes straight to recommendations."""
    cid = client.post("/api/v1/conversations").json()["id"]
    r = send(client, cid, "Laptop for programming under 80000 with 16 GB RAM").json()
    assert r["response_type"] == "recommendations"
    assert len(r["recommendations"]) == 2


def test_budget_change_preserves_unrelated(client):
    """Regression test 6: Changing budget preserves other requirements."""
    cid = client.post("/api/v1/conversations").json()["id"]
    send(client, cid, "Laptop for programming under 80000 with 16 GB RAM")
    r = send(client, cid, "Actually my budget is 60000").json()
    assert r["requirements"]["budget_max_inr"] == 60000
    assert r["requirements"]["min_ram_gb"] == 16
    assert "programming" in r["requirements"]["use_cases"]


def test_local_both_cloud_transitions(client):
    """Regression test 7: ML mode transitions from local to both to cloud."""
    cid = client.post("/api/v1/conversations").json()["id"]
    send(client, cid, "Machine learning under 100000")
    t1 = send(client, cid, "local").json()
    assert t1["requirements"]["ml_mode"] == "local"

    t2 = send(client, cid, "both").json()
    assert t2["requirements"]["ml_mode"] == "both"

    t3 = send(client, cid, "cloud").json()
    assert t3["requirements"]["ml_mode"] == "cloud"


def test_unrelated_request_does_not_erase_stored_requirements(factory):
    """Regression test 8: Truly unrelated request does not erase active requirements."""
    class MockOutOfScopeExtractor:
        mode = "test"

        def extract(self, *args):
            return Extraction(
                intent="out_of_scope",
                changes=[],
                conflicts=[],
                proposal_decision="none",
                product_ids=[],
            )

    with TestClient(create_app(Settings(_env_file=None), factory, MockOutOfScopeExtractor())) as client:
        cid = client.post("/api/v1/conversations").json()["id"]
        # Seed initial state directly
        with factory.begin() as s:
            from app.models.entities import Conversation
            c = s.get(Conversation, cid)
            c.requirements = Requirements(budget_max_inr=80000, use_cases=["programming"]).model_dump()

        res = send(client, cid, "Write me a poem about flowers").json()
        # Should keep requirements
        assert res["requirements"]["budget_max_inr"] == 80000
        assert "programming" in res["requirements"]["use_cases"]
        assert "keeping your active requirements" in res["assistant_message"].lower() or "80,000" in res["assistant_message"]


def test_contradictory_mandatory_constraint_prompts_clarification(factory):
    """Regression test 9: Contradictory constraints create clarification without modifying state."""
    class ConflictExtractor:
        mode = "test"

        def extract(self, *args):
            return Extraction(
                intent="recommend",
                changes=[],
                conflicts=["Did you want budget 50000 or 70000?"],
                proposal_decision="none",
                product_ids=[],
            )

    with TestClient(create_app(Settings(_env_file=None), factory, ConflictExtractor())) as client:
        cid = client.post("/api/v1/conversations").json()["id"]
        res = send(client, cid, "Budget 50000 or maybe 70000").json()
        assert res["response_type"] == "clarification"
        assert "50000 or 70000" in res["assistant_message"]


def test_no_match_proposal_requires_contextual_acceptance(client):
    """Regression test 10: Non-budget responses are not interpreted as budget proposal acceptance."""
    cid = client.post("/api/v1/conversations").json()["id"]
    r1 = send(client, cid, "Laptop for programming under 20000 with 16 GB RAM").json()
    assert r1["response_type"] == "no_match"
    proposed = r1["requirements"]["pending_budget"]
    assert proposed is not None and proposed > 20000

    # Sending a clarification or non-acceptance response should NOT accept the proposal
    r2 = send(client, cid, "I need it for college").json()
    assert r2["requirements"]["budget_max_inr"] == 20000

    # Explicit acceptance
    r3 = send(client, cid, "yes").json()
    assert r3["requirements"]["budget_max_inr"] == proposed
    assert r3["response_type"] == "recommendations"


def test_rejecting_proposal_does_not_immediately_repeat(client):
    """Regression test 11: Rejecting proposal does not re-propose same price without new info."""
    cid = client.post("/api/v1/conversations").json()["id"]
    r1 = send(client, cid, "Laptop for programming under 20000 with 16 GB RAM").json()
    assert r1["response_type"] == "no_match"
    proposed = r1["requirements"]["pending_budget"]
    assert proposed is not None

    # Reject
    r2 = send(client, cid, "no").json()
    assert r2["requirements"]["pending_budget"] is None
    assert proposed in r2["requirements"]["rejected_budget_proposals"]

    # In next turn without requirement changes, do not repeat the same budget proposal
    r3 = send(client, cid, "show me options").json()
    assert r3["requirements"]["pending_budget"] is None
    assert "Would you like to raise the budget" not in r3["assistant_message"]


def test_refresh_restores_requirements_and_metadata(client):
    """Regression test 12: GET conversation endpoint restores requirements and dialogue metadata."""
    cid = client.post("/api/v1/conversations").json()["id"]
    send(client, cid, "Machine learning under 80000")
    send(client, cid, "not sure")

    restored = client.get(f"/api/v1/conversations/{cid}").json()
    req = restored["requirements"]
    assert req["budget_max_inr"] == 80000
    assert req["ml_mode"] == "unsure"
    assert "ml_mode" in req["provisional_assumptions"]
    assert restored["state_version"] >= 2


def test_unknown_specifications_cannot_satisfy_mandatory_constraints(factory):
    """Regression test 13: Null/unknown specification cannot satisfy mandatory filter."""
    with factory() as session:
        # Create a product with unknown weight and battery
        p = Product(
            id="TEST-UNKNOWN",
            name="Test Unknown Product",
            category="laptop",
            price_inr=50000,
            cpu_label="Test CPU",
            cpu_tier=3,
            ram_gb=16,
            storage_gb=512,
            storage_type="SSD",
            gpu_label="Test GPU",
            gpu_tier=1,
            weight_kg=None,
            battery_hours=None,
            use_case_tags=["programming"],
            feature_tags=[],
            is_synthetic=True,
        )
        session.add(p)
        session.flush()

        # Strict weight filter
        req_weight = Requirements(category="laptop", max_weight_kg=2.5)
        results = search_products(session, req_weight)
        assert not any(x.id == "TEST-UNKNOWN" for x in results)

        # Strict battery filter
        req_battery = Requirements(category="laptop", min_battery_hours=4.0)
        results_battery = search_products(session, req_battery)
        assert not any(x.id == "TEST-UNKNOWN" for x in results_battery)


def test_duplicate_request_protection(client):
    """Regression test 14: Duplicate request ID protection."""
    cid = client.post("/api/v1/conversations").json()["id"]
    rid = str(uuid4())
    res1 = send(client, cid, "Programming under 80000", rid).json()
    res2 = send(client, cid, "Programming under 80000", rid).json()
    assert res1 == res2

    # Different content with same request ID triggers 409
    diff = send(client, cid, "Different text", rid)
    assert diff.status_code == 409


def test_old_saved_conversation_payloads_load():
    """Regression test 15: Backward-compatible loading of older conversation JSON payloads."""
    old_json = {
        "category": "laptop",
        "use_cases": ["programming"],
        "budget_max_inr": 75000,
        "no_budget": False,
        "min_ram_gb": 16,
        "min_storage_gb": 512,
        "require_dedicated_gpu": None,
        "max_weight_kg": None,
        "min_battery_hours": None,
        "required_features": [],
        "preferences": ["lightweight"],
        "ml_mode": None,
        "conflicts": [],
        "provenance": {"budget_max_inr": "msg-1"},
        "pending_budget": None,
    }
    # Must load successfully with default dialogue metadata
    loaded = Requirements.model_validate(old_json)
    assert loaded.budget_max_inr == 75000
    assert loaded.pending_clarification is None
    assert loaded.provisional_assumptions == {}
    assert loaded.rejected_budget_proposals == []


def test_native_and_json_encoded_values_validation():
    """Regression test 16: Decodes JSON strings and native types with strict type checking."""
    assert _decode_value('"80000"') == "80000"
    assert _decode_value(80000) == 80000
    assert _decode_value(80000.0) == 80000.0
    assert _decode_value('["programming"]') == ["programming"]
    assert _decode_value(["programming"]) == ["programming"]
    assert _decode_value('"local"') == "local"
    assert _decode_value("local") == "local"
    assert _decode_value(None) is None

    # merge_state accepts string-encoded numbers for budget
    extraction = Extraction(
        intent="recommend",
        changes=[
            Change(field="budget_max_inr", action="set", value_json="80000", evidence="80000"),
            Change(field="ml_mode", action="set", value_json='"both"', evidence="both"),
        ],
        conflicts=[],
        proposal_decision="none",
        product_ids=[],
    )
    req, seen = merge_state(Requirements(), extraction, "80000 both", "m1")
    assert req.budget_max_inr == 80000
    assert req.ml_mode == "both"
    assert set(seen) == {"budget_max_inr", "ml_mode"}

    # Invalid type: boolean as budget must fail
    invalid_extraction = Extraction(
        intent="recommend",
        changes=[Change(field="budget_max_inr", action="set", value_json=True, evidence="true")],
        conflicts=[],
        proposal_decision="none",
        product_ids=[],
    )
    with pytest.raises(AppError) as exc_info:
        merge_state(Requirements(), invalid_extraction, "true", "m2")
    assert exc_info.value.code == "invalid_extraction"
