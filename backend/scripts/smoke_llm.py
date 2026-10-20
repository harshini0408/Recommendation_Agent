"""One real extraction request; does not change the database."""

from app.config import get_settings
from app.agent.llm_client import GroqExtractor
from app.schemas.requirements import Requirements
from app.agent.state import merge_state
from app.errors import AppError

if __name__ == "__main__":
    text = "I need a laptop for programming. Maximum budget 80000 INR and at least 16 GB RAM."
    try:
        patch = GroqExtractor(get_settings()).extract(text, Requirements(), [], [])
        state, _ = merge_state(Requirements(), patch, text, "smoke")
        assert state.budget_max_inr == 80000 and state.min_ram_gb == 16 and "programming" in state.use_cases
        print("LIVE Groq extraction and state validation passed. No database changes.")
    except AppError as exc:
        raise SystemExit(exc.code + ": " + exc.message)
    except AssertionError:
        raise SystemExit("Live call returned, but interpreted values did not match the smoke case.")
