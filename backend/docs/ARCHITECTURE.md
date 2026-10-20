# Architecture

```mermaid
flowchart TD
  UI[React chat and comparison] -->|HTTP JSON| API[FastAPI routes]
  API --> AG[Conversation orchestrator]
  AG -->|State and recent text| LLM[Groq structured extraction]
  LLM -->|Validated patch| AG
  AG --> POLICY[State merge and clarification policy]
  POLICY --> TOOLS[Typed catalogue tools]
  TOOLS -->|Bound SQL| DB[(PostgreSQL)]
  TOOLS --> RANK[Filtering and deterministic ranking]
  RANK --> FACTS[Database based explanation]
  FACTS -->|Version checked atomic save| DB
  FACTS --> API
  API -->|Response and requirements| UI
```

## One turn

1. Validate input and inspect the completed-request UUID. Replays return persisted output.
2. Snapshot conversation version, requirements, recent messages, and previous recommendations; close the session.
3. Interpret the message using Groq (or explicitly configured demo parser).
4. Validate changes and evidence, merge KEEP/SET/CLEAR, and determine whether clarification is needed.
5. If ready, filter the database, apply required feature membership, rank eligible products, and construct factual cards.
6. If no match, diagnose whether a budget-only change could satisfy all remaining constraints. Store a proposal; do not apply it yet.
7. Compare-and-swap state version and commit user message, assistant response, state, and run evidence atomically.
8. UI reloads authoritative conversation state and displays the latest result.

## Database relationships

```mermaid
erDiagram
  conversations ||--o{ messages : contains
  conversations ||--o{ recommendation_runs : records
  messages ||--o{ recommendation_runs : initiates
  conversations {
    string id PK
    jsonb requirements
    int state_version
  }
  messages {
    string id PK
    string conversation_id FK
    string client_message_id
    int sequence
    jsonb response
  }
  recommendation_runs {
    string id PK
    string conversation_id FK
    string source_message_id FK
    jsonb products
    jsonb requirement_snapshot
  }
  products {
    string id PK
    int price_inr
    int ram_gb
    jsonb feature_tags
  }
```

Run products are factual JSON snapshots with original catalogue IDs, rather than product foreign keys, so the demonstration retains what was shown if seed records are later updated. Current product lookup uses the catalogue table. Message rows are uniquely ordered per conversation; request UUIDs are unique per conversation. Every accepted turn increments version once and creates two ordered messages.

The hosted model cannot access PostgreSQL credentials. It returns data, not SQL. Free API failure remains an explicit error. No production authentication or public hosting is provided.
