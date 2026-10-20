# Package verification

Verified during package creation on 20 October 2026. These results describe this packaged code in the creation environment, not the user's local installation.

| Check | Result | Scope |
|---|---|---|
| `python -m pytest -q` | **38 passed, 1 skipped** | Isolated SQLite and mocked/demo extraction; no external inference |
| `python -m ruff check .` | **Passed** | Backend source/tests lint |
| `python -m compileall -q ...` | **Passed** | Python compilation |
| `npm run typecheck` | **Passed** | Strict TypeScript checking |
| `npm run build` | **Passed** | Vite production bundle |
| `python -m alembic upgrade head --sql` | **Passed** | Offline PostgreSQL DDL generation, exported as SCHEMA.sql |
| Seed repeatability | **Passed in tests** | Forty rows remain after repeated seed on isolated test DB |
| PostgreSQL migration/persistence run | **Not run here** | PostgreSQL server unavailable; opt-in test included |
| Real Groq API call | **Not run here** | No user API key supplied; smoke script included |
| Browser walkthrough/visual QA | **Not run here** | No browser installed; browser download blocked by environment network policy |
| User-machine installation | **Pending** | Follow ANTIGRAVITY_SETUP.md |

One non-failing warning appeared: Starlette's TestClient warns that its HTTPX integration is deprecated in favor of HTTPX2. The packaged tests passed with the pinned dependencies. A dependency migration is not required for this assessment build; do not hide the warning or claim no warnings occurred.

The frontend installed 70 npm packages and built successfully with Node 24.19.0 / npm 11.9.0. Python verification used Python 3.12.14. Exact Python and JavaScript dependencies are recorded in requirements files and package-lock.json.

## Coverage demonstrated by automated checks

- Required route contracts and validation, catalogue filtering/pagination and product details.
- Exact budget limits, unknown weight exclusion and stable ranking.
- Vague and complete requests, memory persistence, budget changes and explicit no-budget state.
- KEEP/SET/CLEAR validation, fabricated extraction evidence and conflicts.
- Zero/one/two products and factual agreement with catalogue records.
- No-match proposal confirmation and invalidation by changed requirements.
- Duplicate request replay, mismatched request-content rejection and optimistic conflict prevention.
- Controlled database and model failures without committed false-success state.
- Provider authentication, quota, server errors, timeouts and bounded format-repair behavior.
- Strict model schema structure and request payload shape.

These tests do not establish live model understanding, PostgreSQL-specific concurrency behavior, public-production security, or browser accessibility. The PostgreSQL test runner, live smoke script and manual demo/browser checklist are included to complete that verification locally. A started development server was not assumed to remain running; use the local setup prompt to start and verify both services on your machine.

## Before final submission

Run the actual PostgreSQL tests and live smoke test, then complete representative multi-turn conversations and the browser checklist. Record dates, commands, actual results and defects in LOCAL_VERIFICATION.md. Update the progress README and known limitations based on that evidence. Do not relabel simulated checks as live model results.
