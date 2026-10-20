import pytest
from app.schemas.requirements import Requirements, Extraction, Change
from app.agent.state import merge_state
from app.agent.clarification import clarification
from app.services.catalogue import search_products
from app.services.ranking import rank_products
from app.errors import AppError


def extract(changes=None, conflicts=None):
    return Extraction(
        intent="recommend",
        changes=changes or [],
        conflicts=conflicts or [],
        proposal_decision="none",
        product_ids=[],
    )


def test_keep_set_clear():
    old = Requirements(use_cases=["programming"], budget_max_inr=80000, require_dedicated_gpu=True)
    patch = extract([Change(field="budget_max_inr", action="set", value_json="60000", evidence="60000")])
    state, _ = merge_state(old, patch, "Actually 60000", "m1")
    assert (
        state.budget_max_inr == 60000 and state.use_cases == ["programming"] and state.require_dedicated_gpu
    )
    patch = extract(
        [
            Change(
                field="require_dedicated_gpu",
                action="clear",
                value_json=None,
                evidence="no longer need graphics",
            )
        ]
    )
    state, _ = merge_state(state, patch, "I no longer need graphics", "m2")
    assert state.require_dedicated_gpu is None and state.provenance["require_dedicated_gpu"] == "m2"


@pytest.mark.parametrize("value", ['"80000"', "true", "-1", "null", "80000.5"])
def test_invalid_numeric_patch(value):
    patch = extract([Change(field="budget_max_inr", action="set", value_json=value, evidence="budget")])
    with pytest.raises(AppError):
        merge_state(Requirements(), patch, "budget", "m")


def test_fabricated_evidence_rejected():
    patch = extract([Change(field="min_ram_gb", action="set", value_json="64", evidence="64 GB")])
    with pytest.raises(AppError):
        merge_state(Requirements(), patch, "College laptop", "m")


def test_conflicts_prevent_search():
    state, _ = merge_state(
        Requirements(), extract(conflicts=["Is the maximum 60000 or 80000?"]), "unclear", "m"
    )
    assert "60000" in clarification(state)


def test_unknown_category_is_honest():
    assert "laptops only" in clarification(Requirements(category="phone"))


def test_rank_and_hard_filter(factory):
    r = Requirements(use_cases=["programming"], budget_max_inr=60000, min_ram_gb=16)
    with factory() as s:
        rows = search_products(s, r)
        assert rows and all(p.price_inr <= 60000 and p.ram_gb >= 16 for p in rows)
        a = rank_products(rows, r)
        b = rank_products(list(reversed(rows)), r)
        assert a == b and len(a) == 2
        assert all(abs(sum(x["score_components"].values()) - x["score"]) < 0.0002 for x in a)


def test_unknowns_and_features(factory):
    r = Requirements(required_features=["nonexistent-feature"], no_budget=True, min_ram_gb=8)
    with factory() as s:
        assert search_products(s, r) == []


def test_no_budget_does_not_repeat_question():
    assert clarification(Requirements(use_cases=["general"], no_budget=True)) is None


def test_strict_schema_fields_required():
    schema = Extraction.model_json_schema()
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(schema["properties"])
    for definition in schema.get("$defs", {}).values():
        if "properties" in definition:
            assert definition["additionalProperties"] is False
            assert set(definition["required"]) == set(definition["properties"])
