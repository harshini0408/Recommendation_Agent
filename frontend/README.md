# ClearChoice frontend

React + TypeScript + Vite client for the FastAPI backend.

1. Copy `.env.example` to `.env` only if absent. Set `VITE_API_BASE_URL=http://localhost:8000`. Never put private keys in Vite variables.
2. Use Node 22.12+ (supported LTS recommended).
3. Run `npm ci`, `npm run typecheck`, and `npm run build`.
4. Start the backend as documented in `../backend/README.md`.
5. Run `npm run dev` and open http://127.0.0.1:5173 . Keep both terminals running.

The development server binds locally and fixes port 5173. Configuration changes need a restart. The local browser stores only the current conversation ID, while history/state live in the database. Demo mode is visibly labelled; failures do not silently turn into mocked AI responses.

Full setup: `../backend/ANTIGRAVITY_SETUP.md`. File explanations: `../backend/docs/FILE_GUIDE.md`. Browser test scenarios: `../backend/docs/DEMO_SCENARIOS.md`.
