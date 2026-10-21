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

## Improvements & Debugging Round (21 October 2026)

### Problems Identified & Resolved
1. **Uncertainty Handled Like Out-of-Scope:** When customer answered "not sure" to local vs cloud ML, the model returned `out_of_scope` with no changes, triggering a generic reset message ("I can help compare laptops in this synthetic catalogue. Tell me your use case and budget in INR.").
   - *Fix:* Added contextual interpretation of short answers against pending clarification; updated system prompt to classify uncertainty about laptops as `recommend`; added proactive fallback so uncertainty never resets active requirements.
2. **Missing Dialogue Metadata & Repetitive Clarifications:** The system had no memory of which question was pending or how many attempts had been made, causing infinite clarification loops on short replies.
   - *Fix:* Added application-managed dialogue state (`pending_clarification`, `clarification_field`, `clarification_attempts`, `provisional_assumptions`, `rejected_budget_proposals`) to `Requirements`.
3. **ML Usage States Incomplete:** `ml_mode` was restricted to `Literal["local", "cloud"] | None`. "both" and "unsure" were rejected or misclassified.
   - *Fix:* Expanded `ml_mode` across backend, schemas, prompt, ranking, and frontend to support `"local" | "cloud" | "both" | "unsure" | None`.
4. **Ranking & Trade-off Support for "both" and "unsure":**
   - *Fix:* Implemented deterministic heuristics:
     - `both`: Target `(CPU tier 4, 16 GB RAM, GPU tier 3)`
     - `unsure`: Provisional balanced target `(CPU tier 3, 16 GB RAM, GPU tier 2)` with plain-language explanation of on-device vs cloud ML
5. **No-Match Repeated Proposals:** Rejecting a proposed budget could cause immediate re-prompting.
   - *Fix:* Tracked `rejected_budget_proposals` to prevent repeated identical budget proposals without new user constraints.
6. **Frontend Enhancements:**
   - Quick-reply buttons (`Local`, `Cloud`, `Both`, `Not sure`) rendered when ML mode clarification is active.
   - Dynamic catalogue count fetched from `/api/v1/meta`.
   - Provisional assumptions rendered distinctly from hard user constraints.
   - Clear ML mode label in Requirements panel.

### Test Results (21 October 2026)
| Suite | Command | Result |
|---|---|---|
| Full Pytest Suite | `python -m pytest -q` | **53 passed, 1 skipped** (0 failures) |
| PostgreSQL Integration | `python -m scripts.run_postgres_tests` | **1 passed** (real PostgreSQL database) |
| Ruff Linter | `python -m ruff check .` | **All checks passed!** (0 errors) |
| TypeScript Typecheck | `npm run typecheck` | **0 errors** |
| Production Build | `npm run build` | **Built successfully** (dist bundle 246 kB) |
| Live Groq Reproduction | `reproduce_failure.py` | **5 turns passed live** |
| Live Mixed ML Request | `verify_live_scenarios.py` | **Passed live** |
| Live No-Match Proposal | `verify_live_scenarios.py` | **Passed live** |

## Running servers

| Service | URL | Status |
|---|---|---|
| Backend (FastAPI) | http://127.0.0.1:8000 | Running (uvicorn, port 8000) |
| Frontend (Vite) | http://127.0.0.1:5173 | Running (npm run dev) |
| Interactive docs | http://127.0.0.1:8000/docs | Accessible |
| Health | http://127.0.0.1:8000/api/v1/health | `{"status":"ok","database":"ready"}` |
| Meta | http://127.0.0.1:8000/api/v1/meta | `mode=live, llm_configured=true, catalogue_size=40` |

## Restart instructions

```powershell
# Backend (from backend/):
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Frontend (from frontend/):
npm run dev
```
