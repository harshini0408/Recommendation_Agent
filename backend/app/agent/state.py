import json
from pydantic import ValidationError
from app.errors import AppError
from app.schemas.requirements import Requirements

BOOLS = {"no_budget", "require_dedicated_gpu"}
INTS = {"budget_max_inr", "min_ram_gb", "min_storage_gb"}
NUMBERS = {"max_weight_kg", "min_battery_hours"}
LISTS = {"use_cases", "required_features", "preferences"}


def _decode_value(raw):
    """Decode value_json to a Python value.

    The model should return a JSON-encoded string (e.g. "80000", "[\"prog\"]").
    However, because the schema allows str|None and Groq strict mode may still
    let the model place the JSON-encoded payload *inside* a string, we handle
    both paths:
      - If raw is already a non-string Python value (int/float/bool/list),
        use it directly. This should not happen with str|None schema but is a
        safety fallback.
      - If raw is a string, attempt json.loads; if that fails treat as a plain
        string value.
      - If raw is None/null, return None.
    """
    if raw is None:
        return None
    if not isinstance(raw, str):
        # Native type - model did not JSON-encode into string (schema mismatch).
        return raw
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        # Not valid JSON; treat as a bare string value (e.g. "local").
        return raw


def merge_state(old, extraction, message, message_id):
    data = old.model_dump()
    data["conflicts"] = extraction.conflicts[:3]
    seen = set()
    for change in extraction.changes:
        if (
            change.field in seen
            or not change.evidence.strip()
            or change.evidence.casefold() not in message.casefold()
        ):
            raise AppError(
                502, "invalid_extraction", "The model could not validate your change. Please rephrase.", True
            )
        seen.add(change.field)
        field = change.field
        if change.action == "clear":
            value = Requirements().model_dump()[field]
        else:
            value = _decode_value(change.value_json)
            valid = value is not None
            if field in BOOLS:
                valid = type(value) is bool
            elif field in INTS:
                # Allow float-encoded integers (e.g. 80000.0 -> 80000)
                if isinstance(value, float) and value.is_integer():
                    value = int(value)
                valid = type(value) is int
            elif field in NUMBERS:
                valid = type(value) in (int, float)
            elif field in LISTS:
                valid = isinstance(value, list) and all(isinstance(v, str) for v in value)
            else:
                valid = isinstance(value, str)
                if field == "ml_mode" and valid and value.lower().strip() not in ("local", "cloud", "both", "unsure"):
                    valid = False
            if not valid:
                raise AppError(
                    502, "invalid_extraction", "The model returned an invalid requirement type.", True
                )
            if isinstance(value, list):
                value = list(dict.fromkeys(v.lower().strip() for v in value))
            if isinstance(value, str):
                value = value.lower().strip()
        data[field] = value
        data["provenance"][field] = message_id
    if "budget_max_inr" in seen and data["budget_max_inr"] is not None:
        data["no_budget"] = False
    if "no_budget" in seen and data["no_budget"]:
        data["budget_max_inr"] = None
    # Any new requirement invalidates an older proposal and resets rejected proposals.
    if seen:
        data["pending_budget"] = None
        data["rejected_budget_proposals"] = []
    if not seen and extraction.proposal_decision == "accept" and old.pending_budget:
        data["budget_max_inr"] = old.pending_budget
        data["no_budget"] = False
        data["provenance"]["budget_max_inr"] = message_id
        data["pending_budget"] = None
        seen.add("budget_max_inr")
    if extraction.proposal_decision == "reject":
        if old.pending_budget:
            rejected = list(data.get("rejected_budget_proposals") or [])
            if old.pending_budget not in rejected:
                rejected.append(old.pending_budget)
            data["rejected_budget_proposals"] = rejected
        data["pending_budget"] = None
    try:
        return Requirements.model_validate(data), sorted(seen)
    except ValidationError:
        raise AppError(
            502, "invalid_extraction", "The interpreted requirements were invalid. Please rephrase.", True
        )
