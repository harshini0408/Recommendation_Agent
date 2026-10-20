# File meanings and responsibilities

This guide covers every source/configuration/documentation file shipped in the ZIP. Paths are relative to the extracted parent folder. Installed dependencies, caches, private `.env` files and generated build output are intentionally excluded.

## How the parts fit together

The frontend collects a message and calls FastAPI. The backend loads memory, asks Groq for a structured patch, validates it, applies policy and catalogue filters, ranks eligible records, constructs factual explanations, and atomically saves the turn. Database setup/migrations/seed happen before starting the application. Tests verify these boundaries.

## backend

### `backend/.env.bootstrap.example`
**Purpose:** Database administrator template.
**How it helps:** Copy to .env.bootstrap for initial role/database provisioning only. The application server never reads this file.

### `backend/.env.example`
**Purpose:** Runtime configuration template.
**How it helps:** Copy to .env and fill PostgreSQL application credentials and Groq key. Controls live/demo mode, timeout and CORS. The running server reads the local copy.

### `backend/.gitignore`
**Purpose:** Protect private and generated files.
**How it helps:** Ignores actual environment files, virtual environments, logs, caches and local database dumps. Templates remain distributable.

### `backend/ANTIGRAVITY_SETUP.md`
**Purpose:** Copy-ready installation handoff.
**How it helps:** Detailed sequential instructions for the local coding agent: preserve old work, install dependencies, configure secrets, create databases, migrate/seed, test, start services, verify browser and update progress.

### `backend/README.md`
**Purpose:** Main project and setup documentation.
**How it helps:** Explains scope, features, Windows/macOS/Linux setup, commands, API, ranking formulas, limitations and assessment submissions.

### `backend/alembic.ini`
**Purpose:** Migration entry configuration.
**How it helps:** Anchors the migration directory and Python path relative to the backend folder; it does not store a database password.

### `backend/app/agent/clarification.py`
**Purpose:** When to ask another question.
**How it helps:** Asks about unsupported scope, conflicts, missing use case/budget or relevant local/cloud ML distinction. Explicit no-budget status prevents repeated budget questions.

### `backend/app/agent/demo.py`
**Purpose:** Explicit limited offline interpretation.
**How it helps:** Provides a small regex parser for setup demonstrations and tests without an API key. It is labelled demo and does not claim general natural-language capability.

### `backend/app/agent/llm_client.py`
**Purpose:** Real Groq HTTP adapter.
**How it helps:** Calls the configured model with strict schema, bounded history/output and timeouts. Handles provider errors and one output-repair attempt. No silent mock or paid fallback.

### `backend/app/agent/orchestrator.py`
**Purpose:** Complete message lifecycle.
**How it helps:** Loads a snapshot, calls extraction outside transactions, merges state, clarifies or filters/ranks, builds factual output and commits with optimistic concurrency/idempotency protection.

### `backend/app/agent/prompts.py`
**Purpose:** Language interpretation instructions.
**How it helps:** Teaches the model field semantics, KEEP/SET/CLEAR, literal evidence, explicit corrections, contradictions, product references and budget-proposal consent. Does not ask it to invent products.

### `backend/app/agent/state.py`
**Purpose:** Validated memory updates.
**How it helps:** Checks quoted evidence, interprets SET/CLEAR values with strict expected types, retains untouched fields, updates provenance and handles pending-budget acceptance/invalidation.

### `backend/app/agent/tools.py`
**Purpose:** Controlled tool boundary.
**How it helps:** Exports only typed application catalogue retrieval and ranking functions. Model output never becomes an arbitrary function or query.

### `backend/app/api/conversations.py`
**Purpose:** Conversation HTTP endpoints.
**How it helps:** Creates and lists conversations, retrieves history/state, validates incoming messages and delegates processing to the orchestrator.

### `backend/app/api/health.py`
**Purpose:** Readiness and non-secret metadata.
**How it helps:** Health verifies products-table access without calling the LLM. Metadata supports visible demo/live mode and missing-key guidance.

### `backend/app/api/products.py`
**Purpose:** Catalogue HTTP endpoints.
**How it helps:** Handles listing/filtering/pagination and individual lookup. Validated parameters feed the controlled service; arbitrary SQL is never accepted.

### `backend/app/config.py`
**Purpose:** Validated settings and database URL construction.
**How it helps:** Reads backend/.env from an absolute project-relative location, protects secrets and uses SQLAlchemy URL.create for password-safe URLs. Guards test database naming.

### `backend/app/db.py`
**Purpose:** Runtime connection/session factory.
**How it helps:** Creates a pooled PostgreSQL engine with connectivity timeout and per-request sessions. It does not create tables or seed data on startup.

### `backend/app/errors.py`
**Purpose:** Expected application error type.
**How it helps:** Carries HTTP status, safe error code, user-facing message and retryable flag to the centralized error handler.

### `backend/app/main.py`
**Purpose:** FastAPI assembly and error boundaries.
**How it helps:** Creates the application, injects settings/session factory/extractor, registers routes and CORS, supplies safe error envelopes and request IDs. create_app permits isolated tests.

### `backend/app/models/entities.py`
**Purpose:** Database entities and constraints.
**How it helps:** Defines Product, Conversation, Message and RecommendationRun, relationships, numeric checks, sequence/idempotency uniqueness and JSONB state. SQLite JSON is used only by isolated tests.

### `backend/app/schemas/conversations.py`
**Purpose:** Message, recommendation and conversation contracts.
**How it helps:** Validates message length/UUID and shapes factual cards, state, history and response types consistently for API and frontend.

### `backend/app/schemas/products.py`
**Purpose:** Product API and seed validation.
**How it helps:** Defines the exact exposed product fields and paginated product response; ORM data and seed JSON are validated through these models.

### `backend/app/schemas/requirements.py`
**Purpose:** Conversation state and model output contract.
**How it helps:** Defines supported requirement types, preferences, provenance, pending proposal and the strict Extraction/Change schema. Unchanged fields are omitted from patches.

### `backend/app/services/catalogue.py`
**Purpose:** Database filtering and serialization.
**How it helps:** Constructs bound SQL for mandatory numeric/boolean constraints, checks feature membership, performs pagination and converts stored products to the API schema.

### `backend/app/services/ranking.py`
**Purpose:** Suitability score and factual explanations.
**How it helps:** Computes workload/preferences/affordability contributions, deterministic ties, up to two results, reasons, comparison trade-offs and missing-value disclosures.

### `backend/data/products.json`
**Purpose:** Forty synthetic catalogue records.
**How it helps:** Reviewable source data with stable IDs, varied budgets/specifications and deliberate unknowns/boundaries. This is fictional sample inventory, not scraped retailer data.

### `backend/docs/API.md`
**Purpose:** Endpoint-by-endpoint explanation.
**How it helps:** Documents required and extra routes, request examples, response envelope, validation, status codes and retry/idempotency behavior.

### `backend/docs/ARCHITECTURE.md`
**Purpose:** Component and data-flow guide.
**How it helps:** Mermaid diagrams and narrative explain UI/API/orchestrator/model/database responsibilities, relationships and transaction flow.

### `backend/docs/DAY2_PROGRESS.md`
**Purpose:** Honest progress submission snapshot.
**How it helps:** Lists implemented code, package-level checks, remaining local verification, limitations and setup. Update with actual local results before submission.

### `backend/docs/DEMO_SCENARIOS.md`
**Purpose:** Manual evaluation and browser walkthrough.
**How it helps:** Supplies input conversations, expected catalogue behavior, live-evaluation criteria, browser checks and a meeting demonstration sequence.

### `backend/docs/EXPLAIN_THE_CODE.md`
**Purpose:** Interview/meeting preparation.
**How it helps:** Explains the design in plain language and identifies where to change ranking, schema, filters or model configuration safely.

### `backend/docs/FILE_GUIDE.md`
**Purpose:** This file-by-file guide.
**How it helps:** Maps every distributable source/configuration/documentation file to its purpose and role so you can explain the codebase.

### `backend/docs/SCHEMA.sql`
**Purpose:** Reviewable PostgreSQL DDL reference.
**How it helps:** Generated by Alembic offline mode. Shows database objects for review; apply migrations rather than executing this in addition to migrations.

### `backend/docs/VERIFICATION.md`
**Purpose:** Executed checks and limitations.
**How it helps:** Records actual build, lint, test and migration-generation results; explicitly distinguishes checks blocked by environment/key access.

### `backend/migrations/env.py`
**Purpose:** Migration database connection.
**How it helps:** Connects Alembic using validated runtime settings, supplies ORM metadata for future comparisons and supports SQL-only schema generation without a server.

### `backend/migrations/script.py.mako`
**Purpose:** Template for future migrations.
**How it helps:** Used by Alembic when adding a later schema change. Not executed as part of a customer message.

### `backend/migrations/versions/0001_initial.py`
**Purpose:** Frozen initial database schema.
**How it helps:** Creates all four tables, indexes, foreign keys and checks. Does not import changing runtime models. Upgrade is the normal setup action; downgrade is intentionally destructive and not part of setup.

### `backend/pyproject.toml`
**Purpose:** Test/lint configuration.
**How it helps:** Defines test discovery, Python import path, the opt-in PostgreSQL marker and lint rules. It is not an alternate dependency installation mechanism.

### `backend/requirements-dev.lock`
**Purpose:** Full tested Python environment inventory.
**How it helps:** Records the complete pip dependency set from package creation. requirements-dev.txt is the documented installation entry point.

### `backend/requirements-dev.txt`
**Purpose:** Development/test installation entry point.
**How it helps:** Includes requirements.txt and pinned pytest/ruff dependencies. Use this file for assessment setup so both server and tests are available.

### `backend/requirements.txt`
**Purpose:** Pinned runtime dependencies.
**How it helps:** Installs the exact backend dependency versions used for this package, including FastAPI, Pydantic, SQLAlchemy, psycopg, Alembic, Uvicorn and HTTPX plus transitive dependencies.

### `backend/scripts/check_setup.py`
**Purpose:** Non-secret local readiness report.
**How it helps:** Reports inference mode, whether a key exists and catalogue count. It performs no LLM call or database write.

### `backend/scripts/provision_db.py`
**Purpose:** Dedicated role/database provisioning.
**How it helps:** Uses administrator configuration only to create missing project objects. Checks existing privileges/ownership, avoids password resets and verifies application login.

### `backend/scripts/run_postgres_tests.py`
**Purpose:** Guarded PostgreSQL verification runner.
**How it helps:** Selects the separate *_test database, applies migrations/seed, then runs marked integration tests. It never drops a database or tests against development.

### `backend/scripts/seed.py`
**Purpose:** Repeatable catalogue load.
**How it helps:** Validates data/products.json and upserts the known synthetic IDs in one transaction. It does not delete unrelated rows.

### `backend/scripts/smoke_llm.py`
**Purpose:** Real API extraction check.
**How it helps:** Makes a bounded actual Groq request and checks known budget, RAM and use-case extraction. Requires a real free-tier key and does not modify PostgreSQL.

### `backend/tests/conftest.py`
**Purpose:** Isolated test fixtures.
**How it helps:** Creates a temporary in-memory SQLite schema, enables foreign keys, seeds data and injects demo extraction into the application factory.

### `backend/tests/test_api.py`
**Purpose:** API and complete workflow tests.
**How it helps:** Checks catalogue filters, pagination, seed idempotency, turns, restored history, budget proposals, duplicates, errors, CORS and optimistic conflict behavior.

### `backend/tests/test_llm.py`
**Purpose:** Provider adapter contract/failure tests.
**How it helps:** Uses HTTPX mock transport to verify strict payloads, missing credentials, authentication/rate-limit/server errors, timeouts and bounded repair. Makes no real paid/free API request.

### `backend/tests/test_postgres.py`
**Purpose:** Opt-in real database integration test.
**How it helps:** Checks the migrated PostgreSQL schema, persisted turn and idempotent replay on the dedicated test database. Skipped in the default suite unless invoked through the runner.

### `backend/tests/test_state_ranking.py`
**Purpose:** State and business-rule tests.
**How it helps:** Checks KEEP/SET/CLEAR, invalid extraction/evidence, conflicts, scope, ranking reproducibility, feature filtering and strict-schema shape.

## frontend

### `frontend/.env.example`
**Purpose:** Public API URL template.
**How it helps:** Copy to .env and set the backend base URL. Vite variables are public browser configuration; never place API/database secrets here.

### `frontend/.gitignore`
**Purpose:** Frontend private/generated exclusions.
**How it helps:** Ignores local environment configuration, installed npm packages, build output and TypeScript build caches.

### `frontend/README.md`
**Purpose:** Frontend-specific quick start.
**How it helps:** Documents environment configuration, npm commands and how the UI connects to the backend.

### `frontend/index.html`
**Purpose:** Browser application shell.
**How it helps:** Defines document metadata and root element, then loads the React entry module.

### `frontend/package-lock.json`
**Purpose:** Resolved npm dependency lock.
**How it helps:** Allows npm ci to reproduce the package dependency tree. Keep it when installing or submitting.

### `frontend/package.json`
**Purpose:** Frontend dependency and command manifest.
**How it helps:** Defines React/UI packages and development/build/typecheck commands with a minimum Node version.

### `frontend/src/App.tsx`
**Purpose:** Page and conversation coordination.
**How it helps:** Loads metadata and saved conversation, creates/restarts conversations, manages retry UUIDs, refreshes authoritative state and renders chat/requirements/results.

### `frontend/src/api/client.ts`
**Purpose:** Browser-to-backend transport.
**How it helps:** Centralizes API URLs, JSON requests, timeouts, safe error messages and typed methods for metadata, conversations, turns and product details.

### `frontend/src/components/ChatPanel.tsx`
**Purpose:** Customer conversation interface.
**How it helps:** Renders message history, starter prompts, pending state, text composer and keyboard send behavior. React safely renders text.

### `frontend/src/components/ComparisonPanel.tsx`
**Purpose:** Two-product comparison.
**How it helps:** Presents returned product values side by side with unknowns preserved; does not invent or fetch retailer specifications.

### `frontend/src/components/ProductCard.tsx`
**Purpose:** Grounded recommendation presentation.
**How it helps:** Shows stored product facts, reasons, trade-offs, unknowns and score contributions; fetches additional details through the product endpoint.

### `frontend/src/components/RequirementsPanel.tsx`
**Purpose:** Visible conversation memory.
**How it helps:** Displays backend-confirmed budget, use cases, must-haves, preferences, conflicts and pending budget proposal; highlights changed fields.

### `frontend/src/main.tsx`
**Purpose:** React entry point.
**How it helps:** Mounts App into the root element, loads CSS and enables React strict mode.

### `frontend/src/styles.css`
**Purpose:** Visual design and responsive behavior.
**How it helps:** Defines typography, panels, cards, chat, state/error styles, desktop/mobile layouts, focus support and reduced-motion handling.

### `frontend/src/types.ts`
**Purpose:** Typed API models and display helpers.
**How it helps:** Defines product, requirements, turn and history interfaces plus INR formatting and human-readable labels.

### `frontend/src/vite-env.d.ts`
**Purpose:** Vite environment TypeScript declarations.
**How it helps:** Provides the type declarations needed for import.meta.env and Vite-managed modules.

### `frontend/tsconfig.json`
**Purpose:** TypeScript checks.
**How it helps:** Enables strict types, JSX and modern browser compilation rules. build/typecheck use this configuration.

### `frontend/vite.config.ts`
**Purpose:** Vite/React development server configuration.
**How it helps:** Registers React tooling, fixes development port 5173, and reports port conflicts instead of silently selecting another port.

## Python package markers

Each following `__init__.py` marks a directory as an importable Python package. It has no database side effects and does not start a service:

- `backend/app/__init__.py`
- `backend/app/agent/__init__.py`
- `backend/app/api/__init__.py`
- `backend/app/models/__init__.py`
- `backend/app/schemas/__init__.py`
- `backend/app/services/__init__.py`
- `backend/scripts/__init__.py`
- `backend/tests/__init__.py`

## Files created only on your machine

| Path | Purpose |
|---|---|
| `backend/.env` | Your private application credentials/settings |
| `backend/.env.bootstrap` | Private administrator credentials used for provisioning only |
| `backend/.venv/` | Installed Python interpreter environment and dependencies |
| `frontend/.env` | Local public API URL |
| `frontend/node_modules/` | Installed npm dependencies |
| `frontend/dist/` | Generated production frontend after build |
| `backend/docs/LOCAL_VERIFICATION.md` | Antigravity’s actual local setup/test evidence |

Do not submit private environment files, installed dependencies, caches, or local conversation dumps. Keep the source, templates, migrations, seed, tests and lockfiles.
