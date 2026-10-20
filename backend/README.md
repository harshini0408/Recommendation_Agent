# ClearChoice electronics sales assistant

A local assessment application that interprets a customer's laptop requirements, asks focused follow-up questions, remembers changes, and returns up to two products from a synthetic PostgreSQL catalogue. FastAPI and React satisfy the two-component FARM requirement. PostgreSQL supplies persistent catalogue and conversation data.

**Start here:** [Antigravity setup prompt](ANTIGRAVITY_SETUP.md), [file guide](docs/FILE_GUIDE.md), [architecture](docs/ARCHITECTURE.md), [API contract](docs/API.md), and [verification results](docs/VERIFICATION.md).

The archive contains exactly two top-level directories: `backend/` and `frontend/`. This README covers the entire application. Extract into a **new empty folder**, preserve your old project and private environment files, and copy configuration values deliberately. Do not merge old source, `node_modules`, or virtual environments into this package. If the organizer expects a repository-root README, copy this overview there and adjust relative links; the complete docs remain under `backend/docs/`.

## Implemented functionality

- Six required endpoints, plus metadata and paginated conversation-list endpoints.
- Forty fictional laptop records with stable IDs, price, specifications, workload tags, features, and intentionally missing values.
- Groq structured requirement extraction with quoted evidence, typed state validation and KEEP/SET/CLEAR patch semantics.
- A deterministic clarification policy; explicit changes retain unrelated requirements.
- SQL-based mandatory filters and feature membership checks, followed by explainable heuristic ranking.
- One, two, or zero recommendations; all specifications come from database records.
- Budget-only no-match diagnostic with explicit acceptance before changing the budget.
- Version-checked atomic persistence, duplicate request protection, history restoration.
- React chat, requirements panel, product details, ranking evidence, comparison and error states.
- Safe database provisioning, Alembic migrations, idempotent seeding and automated tests.

## What is and is not verified

See `docs/VERIFICATION.md` for the actual package-creation test results. Local tests use an isolated SQLite database and mocked/rule-based extraction. Production configuration uses PostgreSQL only. Passing these tests does **not** establish PostgreSQL deployment or live-model accuracy. Your setup must run PostgreSQL tests, the real Groq smoke test, and the browser walkthrough. The limited demo parser is visibly labelled and never silently replaces a failed live model.

## Requirements

- Python 3.12 recommended (the package was tested on 3.12). Use an existing compatible version if suitable.
- Node.js 22.12+; use a supported Node LTS.
- A running stable PostgreSQL server (16+ recommended).
- Groq account on the **Free Plan** and an API key for live interpretation.
- No GPU, model training, Docker, MongoDB, cloud database, paid inference, or paid hosting is required.

Groq access and limits are account-dependent. Model selection is `openai/gpt-oss-20b`. The model interprets language; it cannot execute SQL or override application filters. Current provider documentation lists this model for strict structured output and Free Plan quotas. Availability must be confirmed in your account. Never enable paid billing to complete this demo.

Official resources: https://console.groq.com/keys , https://console.groq.com/docs/structured-outputs , https://console.groq.com/docs/rate-limits , https://www.postgresql.org/download/ , https://nodejs.org/en/download , https://www.python.org/downloads/ .

## Setup on Windows PowerShell

Open the extracted parent folder. Run commands below in the stated directory; use the project's interpreter explicitly, so activation/execution-policy changes are unnecessary.

### 1. Backend dependencies

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

If Python 3.12 is absent, let the setup agent select an installed compatible Python executable. Do not reuse another project's virtual environment. `requirements.txt` pins runtime dependencies; `requirements-dev.txt` adds the test/lint tools. `requirements-dev.lock` records the full tested dependency set.

### 2. Private configuration

Copy templates **only if the destinations do not already exist**:

```powershell
Copy-Item .env.example .env
Copy-Item .env.bootstrap.example .env.bootstrap
```

Fill `.env` with your application role password, database host/port/names, and Groq key. Fill `.env.bootstrap` with the existing PostgreSQL administrator login, not the pgAdmin master password. Use the same server host/port in both files. Keep the proposed database names unless they collide with unrelated work; if they do, choose unused dedicated names. The test database must end in `_test` and differ from development.

The provisioning script will create the role `electronics_app` using the password you chose in `.env`, plus the project databases. If you already have a suitably restricted project role, enter its existing password. The script will not reset it. If the database already belongs to a different role, choose a new dedicated database instead of changing ownership blindly.

```dotenv
APP_ENV=development
DB_HOST=localhost
DB_PORT=5432
DB_NAME=electronics_assistant
DB_USER=electronics_app
DB_PASSWORD='YOUR_APPLICATION_ROLE_PASSWORD'
TEST_DB_NAME=electronics_assistant_test
GROQ_API_KEY='YOUR_GROQ_KEY'
GROQ_MODEL=openai/gpt-oss-20b
LLM_MODE=live
LLM_TIMEOUT_SECONDS=30
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
```

Replace the placeholder values; do not paste these example passwords verbatim. Quote/escape environment values correctly if they contain quotes, `#`, spaces, or backslashes. Passwords are passed as parameters and assembled with SQLAlchemy URL helpers; you do not manually URL-encode them.

### 3. Provision, migrate and seed

```powershell
.\.venv\Scripts\python.exe -m scripts.provision_db --with-test
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m scripts.seed
.\.venv\Scripts\python.exe -m scripts.check_setup
```

The provisioning step uses bootstrap credentials; runtime uses the application role. Migrations create tables. The seed script upserts only the 40 bundled synthetic IDs and deletes nothing. Repeat the seed command to confirm the count remains 40 (unless you intentionally added other catalogue records).

Optional schema review: `python -m alembic upgrade head --sql` prints PostgreSQL DDL without connecting. `docs/SCHEMA.sql` is the corresponding generated reference. **Use Alembic to install the schema; do not apply both routes.**

### 4. Run verification

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m scripts.run_postgres_tests
.\.venv\Scripts\python.exe -m scripts.smoke_llm
```

The first command requires no server or key. The second migrates/seeds the dedicated test database, verifies persistence and duplicate protection, and leaves synthetic test conversations there. It never drops databases/tables. The third makes one real Groq extraction request (at most one repair attempt if output is malformed) and no database writes.

### 5. Start backend

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Leave this terminal running. Open http://127.0.0.1:8000/docs and http://127.0.0.1:8000/api/v1/health . Use `--reload` only if actively developing; restart after changing `.env`.

### 6. Frontend in a second terminal

From the extracted parent directory:

```powershell
cd frontend
Copy-Item .env.example .env
npm ci
npm run build
npm run dev
```

Copy the environment template only if `.env` does not exist. Visit http://127.0.0.1:5173 . Both servers must stay running. The Vite server uses a fixed port and will report a port conflict rather than silently moving to an unapproved CORS origin. Do not put secrets in `VITE_` variables.

## macOS and Linux equivalents

From `backend/`, use `python3 -m venv .venv`, then `.venv/bin/python` in place of the Windows interpreter path. Use `cp -n .env.example .env` and `cp -n .env.bootstrap.example .env.bootstrap` to preserve existing files. All `python -m ...` commands otherwise match. Frontend npm commands are the same.

## API summary

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/products` | Filtered, paginated catalogue |
| GET | `/api/v1/products/{product_id}` | Recorded product details |
| POST | `/api/v1/conversations` | Start a conversation |
| POST | `/api/v1/conversations/{conversation_id}/messages` | Process a turn |
| GET | `/api/v1/conversations/{conversation_id}` | State and ordered history |
| GET | `/api/v1/health` | Database/schema readiness |
| GET | `/api/v1/conversations` | Paginated recent conversations (additional) |
| GET | `/api/v1/meta` | Non-secret mode/configuration information (additional) |

See `/docs` and `docs/API.md` for request and response details.

## Filtering and ranking

Mandatory filters are category, maximum price, explicit minimum RAM/storage, explicit dedicated-GPU boolean, maximum weight, minimum recorded battery estimate, and required feature tags. Unknown values cannot satisfy mandatory constraints. Inferred use-case targets are **soft ranking factors**, not unrequested hard filters. `no_budget=true` removes the budget ceiling and prevents repeating the budget question.

Workload fit weight 0.50: for each use case average `min(cpu_tier / target_cpu, 1)`, `min(ram_gb / target_ram, 1)`, and (where relevant) `min(gpu_tier / target_gpu, 1)`; then average across use cases. Targets are general `(2,8,0)`, programming `(3,16,0)`, gaming `(3,16,3)`, creative `(4,32,3)`, local ML `(4,32,4)`, cloud ML `(3,16,0)`. These are demo heuristics, not benchmark promises.

Preference weight 0.30: average explicitly stated preferences. Lightweight is `clamp((3-weight_kg)/2,0,1)`; battery is `min(hours/12,1)`; performance is the mean of `cpu_tier/5`, `min(ram_gb/32,1)`, `gpu_tier/5`; value is `min(40000/price,1)`. Unknown preference measurements score zero and are disclosed.

Affordability weight 0.20: `max(0,1-price/budget)`, only after budget filtering. Unused factors are omitted and remaining weights normalized. Final scores are rounded to four decimals; ties use lower price then product ID. Zero factors means equal scores and deterministic price/ID ordering. Explainable score contributions are stored, not hidden model reasoning.

## Reliability and boundaries

- LLM output is an allowlisted patch, with verbatim evidence from the latest message. Pydantic checks values; it does not guarantee interpretation accuracy.
- Normal model calls are bounded to a 30-second timeout and 2,048 completion tokens, with at most one format-repair request. 429/timeout/auth failures are not silently retried or converted to fake successes. No paid fallback exists.
- Model calls occur outside database transactions. A versioned compare-and-swap protects the final atomic state/message save. Conflicts return 409; replaying the same completed request UUID returns the same stored result.
- Full history is persisted, but only the last six messages plus state and previous product facts are sent to the model. Very old context not captured in state may need clarification.
- API errors use a consistent envelope and request ID. Logs suppress credentials and raw provider bodies.
- No-match recovery diagnoses budget only, holding other hard constraints fixed. Other relaxations require a new explicit customer instruction.
- The UI restores the latest conversation using its ID stored in the browser.

## Known limitations and remaining local work

This is a single-user local assessment demo with no authentication. Conversation IDs and the list endpoint are not access control. Do not expose the server publicly. Catalogue scope is laptops, INR, and synthetic configurations; prices/benchmarks are not live retail facts. Features use literal normalized tags, so unseen synonyms may need clarification. Workload suitability is heuristic. Strict structured output can still misinterpret statements. Groq requires internet and available free quota. Demo mode is a limited English regex parser and does not provide full natural-language behavior.

Remaining before submission: complete local PostgreSQL setup, run the PostgreSQL tests, perform live-model evaluation and the browser walkthrough, update the progress README with those actual results, and confirm the organizer's submission channel/meeting time. Never change the reported verification results without running the corresponding checks.

## Assessment deliverables

**20 October, 9 PM:** updated progress README describing implemented features, what works, what remains, limitations/blockers, and how to run. Use `docs/DAY2_PROGRESS.md` as a truthful snapshot and update local outcomes.

**21 October:** source code, final README, schema/migrations, seed data, tests, configuration templates, and the Google Meet demonstration. Meeting time is communicated separately. `docs/DEMO_SCENARIOS.md` and `docs/EXPLAIN_THE_CODE.md` support rehearsal.

Never include `.env`, `.env.bootstrap`, API keys, virtual environments, `node_modules`, database dumps, or customer conversations in the submitted archive.
