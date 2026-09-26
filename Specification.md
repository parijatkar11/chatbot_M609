# Project Specification — Mortgage Chatbot

**Status:** Initial, reverse-engineered specification of the current implementation
**Last reviewed:** 2026-09-26

This document describes behavior present in the source code. It does not treat roadmap language or older setup documents as implemented functionality. If this specification conflicts with runtime code, verify the code and update this document.

## 1. Purpose and scope

The project provides a browser-based mortgage-chat interface backed by a FastAPI service. The service routes messages through a deterministic, in-process workflow, retains conversation and customer-interaction data in memory, and exposes endpoints for conversation management, workflow inspection, customer data, statistics, and approval status.

The current workflow is a prototype. It does not connect to a bank, fetch actual balances or statements, or invoke an LLM. The balance response is randomly generated. See [Current limitations](#11-current-limitations-and-operational-notes).

## 2. Users and primary use cases

There is no authentication or account system. Any client able to reach the API can call its routes, including the customer-list/export endpoints.

Supported interaction patterns are:

- Start a conversation and optionally submit an initial message.
- Send mortgage/banking questions and display the workflow response.
- Review, switch between, and delete conversations in the current Streamlit session.
- Extract an account number from a supported message pattern and retain it with interaction history for that conversation.
- Inspect workflow structure/execution history and retrieve or clear in-memory customer data.
- View and change the status of approval-queue entries through the API.

## 3. System architecture

| Component | Responsibility |
|---|---|
| Streamlit frontend — [frontend/app.py](frontend/app.py) | Chat UI, per-session conversation history, customer-memory display, local human-review controls, and calls to the API. |
| FastAPI service — [backend/main.py](backend/main.py) | HTTP routes, request validation, conversation/approval dictionaries, CORS, response schemas, and service startup. |
| Workflow and memory — [backend/graph.py](backend/graph.py) | Linear message-processing workflow, keyword intent detection, account-number extraction, in-memory customer interactions, and execution history. |
| Shared settings — [config/settings.py](config/settings.py) | Validated environment profile and process-wide configuration. |
| Frontend launcher — [run_frontend.py](run_frontend.py) | Starts Streamlit using the configured frontend port. |

The backend stores conversation messages and workflow/customer memory separately, both in process memory. The frontend also maintains its own session-local message/history copy.

### Message processing flow

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Streamlit
    participant API as FastAPI
    participant G as Workflow
    participant M as In-memory stores

    U->>UI: Submit message
    UI->>API: POST /chat
    API->>API: Validate request and get/create conversation
    API->>G: process_message(message, conversation_id)
    G->>G: Validate → extract customer info → classify intent
    G->>G: Retrieve context → generate response
    G->>M: Save customer interaction and execution history
    G-->>API: Response, action metadata, workflow nodes
    API->>M: Save user/assistant messages; queue approval if requested
    API-->>UI: Chat response JSON
    UI-->>U: Render response and workflow details
```

## 4. Workflow and response behavior

The workflow in [backend/graph.py](backend/graph.py) is a local, sequential state machine with five nodes:

1. **Input validation** — checks stripped text for empty input and checks configured `MAX_INPUT_LENGTH`.
2. **Customer info extraction** — extracts an account number and adds customer context.
3. **Intent classification** — uses ordered, case-insensitive substring/keyword matching.
4. **Context retrieval** — adds intent, conversation ID, and message-count metadata to user context.
5. **Response generation** — returns the prototype response for the detected intent.

Intent categories, in classifier order, are `balance`, `year_end_statement`, `last_transaction`, `statement`, `mortgage_info`, `interest_rates`, `application`, `refinance`, `payment`, `eligibility`, and `general`. The first category with a matching keyword wins; this is keyword matching, not semantic classification.

Account numbers are recognized by patterns such as `account number 123456`, `account # 123456`, `acct: 123456`, `#12345678`, and `my account is 123456`.

| Intent/result | Implemented response behavior |
|---|---|
| Balance, no account number | Ask for the account number; set `action_required=true` and `action_type=account_number_required`. |
| Balance, account number present | Return a random amount from $400 through $600; no real account lookup occurs. |
| Statement, last transaction, year-end statement | Return `Service not available`. |
| Mortgage, rates, application, refinance, payment, eligibility | Return `Service not available`. |
| General/unknown | Return a request-not-understood message with sample supported intents. |

The graph records the visited node names, a final state, and a timestamp per conversation. The state currently begins with an empty `messages` list, so the workflow's `message_count` context value does not reflect FastAPI's stored conversation history.

## 5. HTTP API

The service is defined in [backend/main.py](backend/main.py). Unless otherwise noted, successful responses are JSON.

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/` | Service metadata and links to health/docs/graph structure. |
| `GET` | `/health` | Health status, graph-node count, conversation count, and approval count. |
| `POST` | `/chat` | Process a message. Body: `message` (required), optional `conversation_id`, optional `user_context`. |
| `POST` | `/conversation/start` | Create a conversation; optional `initial_message`. |
| `GET` | `/conversation/{conversation_id}` | Retrieve stored conversation messages and metadata. |
| `POST` | `/conversation/{conversation_id}/clear` | Clear stored conversation messages. |
| `DELETE` | `/conversation/{conversation_id}` | Delete the conversation and its approval-queue entry. |
| `GET` | `/conversations` | List conversation summaries. |
| `GET` | `/approval/pending` | List entries whose status is `pending`. |
| `POST` | `/approval/{conversation_id}/approve` | Set an existing approval entry to `approved`. |
| `POST` | `/approval/{conversation_id}/reject` | Set an existing approval entry to `rejected`. |
| `GET` | `/graph/structure` | Return workflow node names, edges, start/end nodes, and descriptions. |
| `GET` | `/graph/execution-history/{conversation_id}` | Return the last execution record or `404`. |
| `POST` | `/graph/reset` | Reset the singleton workflow instance and its in-memory customer data. |
| `GET` | `/customer/{conversation_id}/details` | Return customer data; a missing ID initializes an empty customer record. |
| `GET` | `/customer/{conversation_id}/interactions?limit=N` | Return recent customer interactions (default limit: 10). |
| `GET` | `/customer/{conversation_id}/export` | Export customer data and interaction memory; returns `404` if absent. |
| `DELETE` | `/customer/{conversation_id}/clear` | Clear customer details and interaction memory. |
| `GET` | `/customers/all` | Return all in-memory customer records. |
| `GET` | `/stats` | Return conversation/message and approval-status counts. |

When `API_DOCS_ENABLED=true`, Swagger UI is served at `/api/docs` and the OpenAPI document at `/api/openapi.json`. The root response currently includes the docs link even when documentation is disabled.

`POST /chat` rejects whitespace-only messages with `400`. Pydantic validation enforces a nonempty message and the configured maximum length before the handler runs; malformed or out-of-range request bodies receive FastAPI validation errors. An unknown supplied conversation ID is replaced with a newly generated ID. Generated IDs have the form `conv_` followed by eight UUID hex characters.

## 6. Conversation, memory, and approvals

- API conversation messages are stored in the process-local `conversations` dictionary as timestamped user/assistant entries.
- Workflow customer details and interaction history are stored in the graph's `CustomerMemoryManager`, keyed by conversation ID.
- Neither store is durable; data is lost on process restart. There is no database or cross-worker synchronization.
- Clearing a conversation's messages does not clear its customer memory. Clearing customer data does not delete its API conversation. Deleting a conversation removes its conversation and approval entry but does not explicitly clear graph customer memory.
- The API adds an approval-queue entry when a workflow response requires action. Approve/reject routes update only its status; they do not execute or resume a banking operation.
- The Streamlit approval toggle is a separate UI-local interaction. It displays a pending message and locally clears it on approve/reject; the frontend does not call the API approval endpoints.

## 7. Frontend behavior

The frontend uses the selected settings for page title/icon/layout, backend base URL, request timeouts, input limit, and initial model-control values. It provides:

- A new-conversation action and session-local conversation-history list with message previews.
- Chat submission and rendering of assistant responses, timestamps, action information, and workflow-node details.
- A customer-memory panel that requests `/customer/{id}/details`.
- Optional local human-review status and approve/reject buttons.
- An API statistics footer and a debug-information panel.

Conversation history is held in Streamlit session state and is not saved to persistent storage. The model name/temperature/token widgets are displayed in the UI but are not included in chat requests; changing them does not reconfigure the backend workflow at runtime.

## 8. Configuration and environments

Configuration is defined by [config/settings.py](config/settings.py) and the profile files [.env.dev](.env.dev), [.env.test](.env.test), and [.env.prod](.env.prod). `APP_ENV` selects the profile and defaults to `dev`. Values in the process environment take precedence over values in the selected file. Unsupported profile names and invalid/range-inconsistent settings are rejected during settings construction.

The configuration surface includes application metadata; API host, port, debug/reload, logging, explicit base URL, CORS, docs visibility, request timeouts, and input length; model key/name/temperature/token defaults and UI bounds; Streamlit port/page/layout/sidebar and approval controls; and workflow debug/timeout values. [The environment example](.env.example) lists the available variables. API credentials are blank in the profile templates and should be injected through a local secret source or deployment secret manager.

Notable profile defaults:

| Profile | Behavior |
|---|---|
| `dev` (default) | Local API at `127.0.0.1:8000`, API reload/debug enabled, docs enabled, Streamlit at port `8501`. |
| `test` | Local test profile, API port `8001`, docs/debug disabled, short timeouts, Streamlit port `8502`. |
| `prod` | API binds to `0.0.0.0:8000`, debug/docs disabled, CORS uses a placeholder public frontend origin that must be replaced for deployment. |

The frontend can derive its API URL from `API_HOST` and `API_PORT`, or use `API_BASE_URL` when provided. `run_frontend.py` starts Streamlit on `STREAMLIT_PORT`.

## 9. Running and testing

Dependencies are listed in [requirements.txt](requirements.txt); development tools are listed in [requirements-dev.txt](requirements-dev.txt). The documented development setup uses `uv` and the project virtual environment.

From the repository root, select a profile if needed and start the processes separately:

- Backend: `python -m backend.main`
- Frontend: `python run_frontend.py`
- Tests and coverage gate: `python -m pytest`

Pytest configuration in [pytest.ini](pytest.ini) discovers the maintained suite, including [tests/test_api.py](tests/test_api.py) and [tests/test_graph.py](tests/test_graph.py), measures `backend` and `config` coverage, prints a terminal coverage table, and fails below 90%. The Streamlit frontend is not included in that coverage target.

## 10. Data and security boundaries

- Conversation, approval, and customer data are in-memory and volatile.
- API routes have no authentication or authorization; `/customers/all` and customer export are not access-controlled.
- Production profile CORS contains an example origin and requires deployment-specific configuration.
- `OPENAI_API_KEY` and model settings are configurable, but the current response workflow does not use an external model client.
- Balance values are random demonstration values, not financial data. This service must not be treated as a production banking or mortgage decision system.

## 11. Current limitations and operational notes

1. Although `langgraph` is a declared dependency and documentation uses the LangGraph name, [backend/graph.py](backend/graph.py) implements its workflow as a local dictionary of handlers and edges; it does not build or invoke a LangGraph library graph.
2. The workflow's validation node sets a failure state for empty/oversized input but does not short-circuit the remaining nodes. The HTTP API separately rejects blank and over-limit requests before calling the workflow.
3. The approval queue and the Streamlit approval controls are not integrated into a real action execution/resume loop.
4. The project has auxiliary data models in [backend/models.py](backend/models.py) and utility managers in [backend/utils.py](backend/utils.py); the active HTTP route models and in-memory stores are separately defined in [backend/main.py](backend/main.py).
5. Existing documentation may describe real-time/LLM or banking-service behavior more broadly than the current implementation. This specification records only behavior verified in source.
