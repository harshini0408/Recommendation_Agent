# Local verification record

Date: 20 October 2026. Machine: Windows, Python 3.11.7, Node 22.18.0, PostgreSQL 18.

## Prerequisites found

| Item | Version / Status |
|---|---|
| Python | 3.11.7 (used); 3.14.0 also present; 3.12 launcher entry broken (D:\python.exe missing) |
| Node.js | 22.18.0 |
| npm | 10.9.3 |
| PostgreSQL | postgresql-x64-18 — Running |

## Environment files

| File | Status |
|---|---|
| `backend/.env` | Present — DB credentials, Groq key, live mode |
| `backend/.env.bootstrap` | Created — postgres admin credentials |
| `frontend/.env` | Created — `VITE_API_BASE_URL=http://127.0.0.1:8000` |

## Python virtual environment

```
backend/.venv — Python 3.11.7
pip install -r requirements-dev.txt — 33 packages installed OK
```

## Frontend dependencies

```
npm ci — 70 packages installed OK (0 vulnerabilities)
```

## Database provisioning

```
python -m scripts.provision_db --with-test
→ "Project role/database provisioning and application login verified. No existing password was changed."
  - Role: electronics_app (login, no superuser/createdb/createrole)
  - DB:   electronics_assistant (dev)
  - DB:   electronics_assistant_test (test)
```

## Migrations

```
python -m alembic upgrade head
→ Applied: 0001_initial (head)
  - Tables: products, conversations, messages, recommendation_runs
```

## Seed

```
python -m scripts.seed  →  Upserted 40 synthetic catalogue records.
python -m scripts.seed  →  Upserted 40 synthetic catalogue records.  (idempotent ✓)
```

## Setup check

```
python -m scripts.check_setup
→ LLM mode: live
   Groq key configured: True
   Database ready. Catalogue rows: 40
```

## Automated tests (SQLite + demo extraction)

```
python -m pytest -q
→ 38 passed, 1 skipped, 1 warning  ✓
   (StarletteDeprecationWarning: httpx2 — known, non-failing)
```

## PostgreSQL integration tests

```
python -m scripts.run_postgres_tests
→ Migrated + seeded electronics_assistant_test
   1 passed, 38 deselected  ✓
```

## Lint

```
python -m ruff check .
→ All checks passed!  ✓
```

## Frontend typecheck and build

```
npm run typecheck  →  tsc --noEmit  (no errors) ✓
npm run build      →  dist/index.html 0.55 kB, JS 244 kB  ✓
```

## Live Groq smoke test

```
python -m scripts.smoke_llm
→ LIVE Groq extraction and state validation passed. No database changes.  ✓

Model used: openai/gpt-oss-20b (Groq Free Plan)
Extracted: budget_max_inr=80000, min_ram_gb=16, use_cases=["programming"] ✓
```

## Fix applied during local setup

**Problem:** `value_json` in `Change` schema was typed as `str | None`.
Groq's strict JSON Schema mode accepted the schema but the model returned
raw numeric/array JSON values that triggered a Groq-side 400 validation error.

**Root cause confirmed:** Groq 400 error:
> "Generated JSON does not match the expected schema ... value_json does not
> validate with anyOf/0/type: expected string, but got array"

**Fix:** Changed `value_json` to a custom Pydantic type `_AnyJsonValue` that
generates `anyOf[string, number, boolean, array(strings), null]` in the JSON
Schema, avoiding the integer/number overlap Groq also rejects. The model then
correctly JSON-encodes values into strings (e.g. `"80000"`, `"[\"programming\"]"`).
`state.py` remains unchanged — `json.loads()` decodes the strings correctly.

**Files changed:**
- `app/schemas/requirements.py` — Added `_AnyJsonValue` custom type
- `app/agent/prompts.py` — Added CRITICAL section explaining JSON-encoding
- `app/agent/state.py` — Added robust `_decode_value()` helper (fallback)

All 38 automated tests passed before and after the fix.

## Running servers

| Service | URL | Status |
|---|---|---|
| Backend (FastAPI) | http://127.0.0.1:8000 | Running (uvicorn, port 8000) |
| Frontend (Vite) | http://127.0.0.1:5173 | Running (npm run dev) |
| Interactive docs | http://127.0.0.1:8000/docs | Accessible |
| Health | http://127.0.0.1:8000/api/v1/health | `{"status":"ok","database":"ready"}` |
| Meta | http://127.0.0.1:8000/api/v1/meta | `mode=live, llm_configured=true` |

## End-to-end API verification

**Complete request → recommendations:**
```
POST /conversations → cid
POST /conversations/{cid}/messages  {"content": "Laptop for programming under 80000 with 16 GB RAM"}
→ response_type: recommendations
→ mode: live
→ budget_max_inr: 80000, min_ram_gb: 16, use_cases: ["programming"]
→ 2 recommendations from 24 eligible products
→ [1] ClearChoice Code 1 (Synthetic) @ INR 49,000 (score=0.825)
→ [2] ClearChoice Study 6 (Synthetic) @ INR 50,500 (score=0.8196)
```

**Budget change (multi-turn memory):**
```
POST /conversations/{cid}/messages  {"content": "Actually my budget is 60000"}
→ response_type: recommendations
→ budget_max_inr updated: 60000 ✓
→ min_ram_gb RETAINED: 16 ✓
→ use_cases RETAINED: ["programming"] ✓
→ changed_fields: ["budget_max_inr"] ✓
→ 2 recommendations (both ≤ INR 60,000) ✓
```

**No-match with budget proposal:**
```
POST /conversations  → new cid
POST /messages  {"content": "Programming under 20000 with 16 GB RAM"}
→ response_type: no_match ✓
→ budget_max_inr: 20000 (unchanged) ✓
→ pending_budget: 37000 (lowest qualifying price) ✓
→ message: "The lowest price meeting all other constraints is INR 37,000. Would you like to raise the budget to that amount?" ✓
```

## Remaining browser checks (manual)

Browser walkthrough from `docs/DEMO_SCENARIOS.md` not yet completed;
requires manual interaction at http://127.0.0.1:5173.
Items pending:
- [ ] UI renders requirements panel, chat, product cards
- [ ] Keyboard send (Enter), loading indicator, error states
- [ ] Product details modal, side-by-side comparison
- [ ] Browser refresh restores conversation history
- [ ] Mobile layout (390px width)
- [ ] No-match → acceptance → recommendations flow in UI
- [ ] Demo mode label display (only in demo mode — live mode currently active)

## Restart instructions

```powershell
# Backend (from backend/):
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Frontend (from frontend/):
npm run dev
```
