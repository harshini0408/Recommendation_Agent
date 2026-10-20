# API contract and examples

Base URL: `http://127.0.0.1:8000`. Interactive contracts: `/docs`; machine-readable schema: `/openapi.json`.

## Catalogue

`GET /api/v1/products` returns `{items,total,page,page_size}`. Defaults: laptop, page 1, 20 items. Limits: positive page, page size 1–100. Allowlisted query fields: `category`, `max_price_inr` (1–10000000), `min_ram_gb` (1–1024), `min_storage_gb` (1–100000), `dedicated_gpu` (boolean), `max_weight_kg` (>0–20), `page`, `page_size`, `sort` (`price_asc`, `price_desc`, `name`). Invalid typed values return 422. Unrecognized query names are ignored by FastAPI; they never become SQL identifiers.

Example: `/api/v1/products?max_price_inr=80000&min_ram_gb=16&page=1&page_size=10`.

`GET /api/v1/products/CC-011` returns a record priced at INR 60000. Unknown IDs return 404. Returned fields are the same product fields embedded in recommendations; timestamps are internal.

## Conversation lifecycle

`POST /api/v1/conversations` takes no body, returns 201 with `id`, empty `requirements`, version 0, timestamps, empty messages, and `latest_response:null`.

`POST /api/v1/conversations/{UUID}/messages` accepts:

```json
{
  "content": "Laptop for programming under 80000 with at least 16 GB RAM",
  "client_message_id": "7dc4376d-0a53-432f-bb86-f25b3d47f8e4"
}
```

Generate a fresh UUID for each new customer message. Reuse it only when retrying that same message. Content must be a nonempty string after trimming, maximum 4000 characters. Extra body keys are rejected.

Success (200) includes:

```json
{
  "conversation_id": "server-generated UUID",
  "response_type": "recommendations",
  "assistant_message": "A factual response constructed by the application",
  "requirements": {},
  "state_version": 1,
  "recommendations": [],
  "evidence": {},
  "mode": "live"
}
```

The empty objects/lists above illustrate envelope positions, not a complete real response. Requirements are fully typed and populated. Each recommendation has `product`, `score`, `score_components`, `reasons`, `trade_offs`, `unknowns`. The recommendation list has zero to two items. Response types: `clarification`, `recommendations`, `no_match`, `informational`. Evidence includes changed fields, mandatory filters, eligible count, search flag, ranking description, and an optional pending budget proposal.

`GET /api/v1/conversations/{UUID}` returns the complete ordered history and current state. Each assistant message retains its structured response for reproducibility; the API also returns `latest_response`. Unknown conversation: 404. Invalid UUID: 422.

`GET /api/v1/conversations?page=1&page_size=20` is an additional paginated local-demo history index. It returns IDs, timestamps, and state versions. There is no authentication, so keep it local.

## System routes

`GET /api/v1/health`: 200 with `status:ok,database:ready` when the products table is reachable; 503 before migrations or on database failure. It does not test the provider or count as a live LLM check.

`GET /api/v1/meta`: application name, synthetic catalogue label, `mode`, provider/model name, and whether a nonempty key is configured. It never returns the key. A configured key may still be invalid; use the smoke script.

## Errors and retries

Application errors use:

```json
{"error":{"code":"llm_rate_limit","message":"Human-readable explanation","retryable":true,"request_id":"request UUID"}}
```

| Status | Typical codes | Action |
|---|---|---|
| 404 | `not_found` | Check product/conversation ID |
| 409 | `state_conflict` | Reload state, then retry the same uncommitted message |
| 409 | `idempotency_conflict` | Do not reuse a completed UUID for different content |
| 422 | `validation_error` | Correct body/query/UUID |
| 502 | `invalid_extraction`, `llm_request_rejected` | Rephrase or check configured model/schema |
| 503 | `llm_not_configured`, `llm_auth` | Fix backend key/model configuration |
| 503 | `llm_rate_limit`, `llm_unavailable` | Wait/check service; no paid fallback |
| 503 | `database_unavailable`, `database_error` | Check PostgreSQL and migrations |
| 504 | `llm_timeout` | Retry when service is available |
| 500 | `internal_error` | Inspect server logs using request ID |

A failed provider call does not persist a user/assistant turn or mutate state. An already committed duplicate UUID returns the stored successful response even if the provider is now unavailable.

## Extra-endpoint rationale

The additional conversation index supports inspection/recovery during the demonstration. `/meta` supports an honest UI indicator for demo mode or missing API configuration. Product detail and conversation APIs already cover comparison/history needs; unnecessary mutation routes were not added.
