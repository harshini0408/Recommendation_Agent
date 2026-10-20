# Copy-ready Antigravity setup prompt

Paste the text below into Antigravity after extracting the ZIP into a new empty folder containing backend/ and frontend/. Open that parent folder as the workspace. Keep your old project backup outside it. Real credentials go only in the ignored local environment files.

---

You are setting up an already-written electronics recommendation assistant. The application source is in backend/ and frontend/. Implement the local setup, execute checks, fix concrete defects if found, and report evidence. Do not regenerate or redesign the application.

CONTEXT
The assessment requires FastAPI plus another FARM component; this project uses React and PostgreSQL. It must remember customer needs, ask focused follow-ups, distinguish hard constraints/preferences, retrieve catalogue records through safe tools, recommend up to two eligible products, explain trade-offs and handle no matches. The catalogue has 40 synthetic laptops. Groq Free Plan with openai/gpt-oss-20b supplies structured extraction; filtering/ranking and product facts are controlled by application code. No paid service, local model training, vector database, public deployment or billing activation is authorized.

1. INSPECT FIRST
Read backend/README.md, backend/docs/VERIFICATION.md, backend/docs/FILE_GUIDE.md, backend/docs/API.md, and any existing AGENTS.md. Inspect Git status and the local folder. Preserve user files. If old generated source is mixed in, identify conflicts before replacing files. Do not delete backups or databases. Confirm the actual OS/shell, Python version, Node/npm, PostgreSQL installation/service and available ports.

2. INSTALL ONLY WHAT IS NEEDED
Use Python 3.12 if available; otherwise verify a supported installed interpreter against dependencies. Create a fresh backend/.venv; do not reuse another project's environment. Install backend/requirements-dev.txt through that interpreter. Preserve the pinned versions initially. Use npm ci in frontend/ to respect package-lock.json. Do not repeatedly reinstall successful dependencies. If an install fails, diagnose the actual error and make the minimum compatible change, updating lockfiles and documentation if necessary. Do not install global packages or overwrite system settings unnecessarily. Ask me only for a specific missing OS installer/admin action if it is necessary, and continue independent setup.

3. CONFIGURE SECRETS LOCALLY
If absent, copy backend/.env.example to backend/.env, backend/.env.bootstrap.example to backend/.env.bootstrap, and frontend/.env.example to frontend/.env. Never overwrite existing private values and never print them.
Tell me which local fields still need values:
- backend/.env: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, TEST_DB_NAME, GROQ_API_KEY.
- backend/.env.bootstrap: PG_ADMIN_HOST, PG_ADMIN_PORT, PG_ADMIN_DATABASE, PG_ADMIN_USER, PG_ADMIN_PASSWORD.
The PostgreSQL administrator password is the database role password, not the pgAdmin master password. The bootstrap/runtime host and port must match. Use a dedicated application role and project databases. Test database must end in _test and differ from development. Leave GROQ_MODEL=openai/gpt-oss-20b and LLM_MODE=live for real verification. Only VITE_API_BASE_URL belongs in frontend configuration.
Check Git ignores for all actual secret files. Do not include credentials in logs, command-line arguments, reports or screenshots. Read them through the provided settings modules.

4. SET UP POSTGRESQL
From backend/, run with the project interpreter:
python -m scripts.provision_db --with-test
python -m alembic upgrade head
python -m scripts.seed
python -m scripts.seed
python -m scripts.check_setup
The script creates missing project role/databases but does not reset existing passwords/ownership. If it reports an existing incompatible database/role, use new dedicated names with my input; do not take over unrelated objects. Do not switch authentication to trust, drop databases or expose the port publicly. Confirm 40 seed IDs without duplication. If provisioning credentials are unavailable, continue tests/build and state the precise database blocker.

5. TEST THE CODE AND LIVE MODEL
Run:
python -m pytest -q
python -m scripts.run_postgres_tests
python -m scripts.smoke_llm
python -m ruff check .
In frontend/, run npm run typecheck and npm run build.
The first pytest suite uses isolated SQLite/mock/demo extraction. The PostgreSQL runner migrates/seeds the dedicated test database and checks real persistence. The live smoke script makes a real Groq request. Distinguish all three types in the report. Do not claim the live model works based on demo tests. Keep the account on Free Plan, and do not use a paid fallback. If quota/model access fails, report it and keep the application failure visible. Demo mode may be used only for clearly labelled UI checks; restore live mode for the actual AI demonstration when configured.

6. START BOTH SERVICES
Keep backend and frontend in separate managed terminals:
Backend, from backend/: python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
Frontend, from frontend/: npm run dev
Use the actual project virtual-environment Python executable. Do not interpret a long-running dev server as a stuck installation. After a server starts and reports its URL, move to the other checks; do not wait for it to exit. Resolve port conflicts by identifying the owning process; do not kill unrelated processes. If changing ports is necessary, update frontend URL and CORS consistently.
Confirm http://127.0.0.1:8000/api/v1/health , http://127.0.0.1:8000/docs and http://127.0.0.1:5173 . A successful build alone is not evidence that a server is running.

7. VERIFY END-TO-END
Use backend/docs/DEMO_SCENARIOS.md. Verify vague request -> useful question, complete request -> recommendations, changed budget retaining RAM/use case, one match, no match, explicit budget proposal acceptance, unknown specs and browser reload. Verify all six required routes and the two extras. Test product detail and side-by-side comparison. Check keyboard operation, loading/error states, retry behavior, 390px/mobile and desktop layouts. Confirm cards match API/database facts. Do not simulate successful Groq responses and call them live. If browser tools are unavailable, give me the exact manual walkthrough and mark browser verification pending.

8. FIX AND DOCUMENT
Fix concrete problems discovered, then rerun the checks affected by those fixes. Avoid unrelated rewrites. Update backend/docs/LOCAL_VERIFICATION.md with actual versions, commands, outcomes and remaining blockers. Update backend/README.md and backend/docs/DAY2_PROGRESS.md truthfully with local results. Keep package-creation verification distinct from local verification. If needed, create a repository-root README linking to backend/README.md without deleting existing unrelated documentation.

Today's required progress submission is an updated README describing implemented features, what works, what remains, limitations/blockers and run instructions. Final submission additionally requires source, schema, sample data, tests, environment templates and Google Meet demo; exact meeting time is supplied separately. Do not falsely mark incomplete work as done and do not automatically submit or publish.

9. FINAL REPORT
Give me:
- Exact backend/frontend URLs and actual running process status.
- Database provisioning/migration/seed outcomes.
- Automated, PostgreSQL and live Groq test outcomes separately.
- Browser checks actually performed.
- Remaining defects/blockers.
- Files ready for today's submission and remaining work for final submission.
- A short explanation of how to restart both services.
Do not include secrets. Do not push, publish, deploy, send or submit anything without a separate instruction.
