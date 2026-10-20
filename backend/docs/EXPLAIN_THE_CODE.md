# Explanation guide for the assessment

## Why this stack

FastAPI is mandatory. React satisfies the second FARM component and makes memory and decisions visible. PostgreSQL is a good fit for numeric catalogue filters and transactional state. The brief allows a hosted LLM; Groq's Free Plan avoids local training/hardware requirements, subject to actual free quota.

## Where the intelligence lives

`app/agent/llm_client.py` asks the external model for a typed patch; `prompts.py` describes the allowed meaning. `state.py` validates and applies the patch. `clarification.py` decides whether a material question remains. Model output is not allowed to execute SQL or select unverified facts.

## A message across files

The React composer calls `src/api/client.ts`. FastAPI's conversation route validates `MessageIn` and calls `process_turn`. The orchestrator snapshots persisted state, calls the extractor outside any transaction, merges state, retrieves eligible catalogue products, ranks them, builds a `TurnResponse`, and saves it with a version check. The UI fetches the authoritative history after success.

## Why a timeout does not corrupt memory

No messages/state are committed until processing has produced a valid response. A failed provider call returns a controlled error. If two turns race, only one can update the expected version. The other returns 409. A repeated client request ID returns its stored response, avoiding duplicate turns.

## Hard constraints versus preferences

Price/RAM/weight and explicitly required features are mandatory filters. Portability inferred from carrying a laptop is a preference. Workload hardware targets guide ranking but do not become hidden mandatory constraints. Unknown mandatory measurements fail eligibility.

## Why two products can have different trade-offs

Ranking computes normalized workload, preference and affordability contributions. Cards compare only stored prices, RAM and weights and disclose unknowns. A lower price does not prove better real-world performance; these are synthetic records and heuristic scores.

## Why no-match handling is useful

The application keeps all mandatory filters. It can temporarily omit budget in a diagnostic query while keeping all others. If a cheapest eligible record exists, it proposes that exact price and requires acceptance. It does not quietly spend more for the customer.

## Small changes you should be able to explain

- Ranking weights and workload targets: `app/services/ranking.py`; rerun ranking tests and update README formulas.
- Add a stored product attribute: ORM model + new Alembic migration + Pydantic product schema + seed data + frontend type/detail presentation. Do not edit an already-applied migration.
- Add a hard filter: requirement schema/extraction prompt + merge typing + controlled query + API/UI where applicable + boundary/unknown-value tests.
- Change the model: `.env` and a new live smoke/evaluation run; confirm the model supports the schema and free account access.

## Limits to acknowledge

No live retailer integration, training, vector retrieval, user authentication or cloud deployment. No assurance of model accuracy until measured live. Old context outside saved state/recent messages may need clarification. Demo parsing is limited. Free inference may rate-limit. PostgreSQL setup and browser behavior must be verified locally before claiming final readiness.
