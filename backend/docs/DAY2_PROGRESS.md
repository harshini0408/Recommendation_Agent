# Progress README — 20 October 2026, 9 PM submission

Date: 20 October 2026. Project: ClearChoice electronics assistant.

## What is implemented

FastAPI backend with all six required endpoints plus two additional endpoints
(`GET /api/v1/conversations`, `GET /api/v1/meta`). React + TypeScript + Vite
frontend. PostgreSQL database with SQLAlchemy ORM and Alembic migration.
Forty synthetic laptop catalogue records. Groq `openai/gpt-oss-20b` structured
extraction with Pydantic validation and KEEP/SET/CLEAR patch semantics.
SQL-based mandatory filters, explainable heuristic ranking, grounded
recommendation cards, no-match budget diagnostic with explicit acceptance,
version-checked atomic persistence, duplicate-request protection, multi-turn
memory with changed-field tracking, and browser conversation restoration.

## What works and was verified locally (20 October 2026)

| Check | Result |
|---|---|
| Backend venv (Python 3.11.7) + dependencies | ✓ Installed |
| Frontend npm ci (70 packages) | ✓ Installed |
| PostgreSQL provisioning (role + 2 databases) | ✓ Created |
| Alembic migration `0001_initial` → head | ✓ Applied |
| Seed: 40 synthetic products (idempotent) | ✓ Confirmed |
| `python -m pytest -q` | ✓ **38 passed, 1 skipped** |
| `python -m scripts.run_postgres_tests` | ✓ **1 passed** (real PostgreSQL) |
| `python -m ruff check .` | ✓ All checks passed |
| `npm run typecheck` + `npm run build` | ✓ No errors, 244 kB bundle |
| `python -m scripts.smoke_llm` | ✓ **LIVE Groq extraction passed** |
| Backend running at http://127.0.0.1:8000 | ✓ health=ok, database=ready |
| Frontend running at http://127.0.0.1:5173 | ✓ HTTP 200 |
| `/api/v1/meta` | ✓ mode=live, llm_configured=true |
| E2E: complete request → 2 live recommendations | ✓ Verified via API |
| E2E: budget change, RAM + use case retained | ✓ Verified via API |
| E2E: no-match + budget proposal | ✓ Verified via API |

## Fix applied during local setup

**`value_json` schema incompatibility with Groq strict mode.**

The model `openai/gpt-oss-20b` correctly returns numeric/array values
for requirement fields, but the original `str | None` schema caused Groq's
strict validator to reject the model's output with a 400 error. Fixed by
adding a custom Pydantic type that generates `anyOf[string, number, boolean,
array(strings), null]` — a non-overlapping union that Groq accepts. The
system prompt was also updated with explicit JSON-encoding instructions.

Files changed: `app/schemas/requirements.py`, `app/agent/prompts.py`,
`app/agent/state.py`. All 38 automated tests passed after the fix.

## Improvements & Fixes Applied (21 October 2026)

**1. ML Mode & Uncertainty Handling in Multi-Turn Conversations:**
- Expanded `ml_mode` from `Literal["local", "cloud"]` to support `both` and `unsure`.
- Contextual interpreter resolves short replies ("both", "not sure", "cloud", "local", "I already told my budget") against pending questions without resetting or looping.
- When ML usage is unsure, the assistant provides plain-language explanation of local vs cloud ML experiments and offers a provisional balanced shortlist under budget.
- Application-managed dialogue metadata (`pending_clarification`, `clarification_field`, `clarification_attempts`, `provisional_assumptions`, `rejected_budget_proposals`) persisted in `Requirements` with backward compatibility for saved conversations.

**2. Ranking & Explanations:**
- Workload heuristic and trade-offs support `both` (target: CPU 4, RAM 16, GPU 3) and `unsure` (provisional target: CPU 3, RAM 16, GPU 2).
- Grounded reasons explain whether the machine fits on-device, cloud, or hybrid ML workloads.

**3. Frontend Enhancements:**
- Quick-reply buttons (`Local`, `Cloud`, `Both`, `Not sure`) appear during ML mode clarification and route directly to the same message API.
- Dynamic catalogue count fetched from `/api/v1/meta`.
- Clear distinction between customer requirements and provisional assumptions in the Requirements panel.

**4. Verification Status (21 October 2026):**
- Automated tests: **53 passed, 1 skipped** (`pytest`).
- Real PostgreSQL test: **1 passed** (`scripts.run_postgres_tests`).
- Ruff linter: **All checks passed!**
- Frontend typecheck: `tsc --noEmit` passed with 0 errors.
- Production build: `npm run build` passed (246 kB bundle).
- Live Groq multi-turn conversation: All 5 turns of failing college ML scenario verified and passing live!

## What remains

- **Browser walkthrough**: http://127.0.0.1:5173 manual UI verification
  (requirements panel, product cards, comparison, mobile layout, keyboard
  navigation, refresh-restores-history). See `docs/DEMO_SCENARIOS.md`.
- **Final submission** (21 October): source archive, final README,
  schema/migrations, sample data, tests, configuration templates.
- **Google Meet demo**: live demonstration and code explanation.

## Limitations and known constraints

- Synthetic laptops only; INR prices; heuristic suitability scores.
- No user authentication; conversation IDs are not access-controlled.
- Groq Free Plan subject to rate limits (free RPM/TPM); rapid consecutive requests can trigger 503 rate limit.
- Python 3.12 launcher entry broken (`D:\python.exe` missing); using 3.11.7.
- Demo mode is a limited English regex parser — visibly labelled, never
  silently activated after a live API failure.
- Full browser walkthrough pending manual verification.

## How to run

```powershell
# From backend/:
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# From frontend/ (separate terminal):
npm run dev
```

Visit http://127.0.0.1:5173 (UI) and http://127.0.0.1:8000/docs (API).

See `README.md` for full setup instructions from scratch.
See `docs/LOCAL_VERIFICATION.md` for all commands and actual outputs.
