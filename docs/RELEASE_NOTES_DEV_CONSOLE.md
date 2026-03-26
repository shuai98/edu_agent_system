# Release Notes

## Release Title

Developer Console, Long-Term Memory, and Trace Visualization Upgrade

## Summary

This update upgrades EduReflex from a basic multi-agent workflow into a more observable and reusable agent system.

The main improvement areas are:

- developer-facing workflow visibility
- cross-session user memory
- request-level tracing and timeline visualization
- MCP integration for tool exposure
- cleaner API contracts for frontend and debugging

## What Changed

### 1. Added a developer console

A new developer console is now available at:

```text
GET /dev
```

The page shows:

- current `user_id`, `thread_id`, and `trace_id`
- live Planner / Researcher / Critic status
- live SSE event stream
- planner output
- critic output
- final answer
- injected long-term memory summary
- thread state snapshot
- trace timeline

This makes the agent workflow visible in real time instead of treating the system as a black box.

### 2. Added cross-session long-term memory

The system now stores user-level memory in SQLite.

Memory is keyed by `user_id`, so users can keep memory across different sessions and thread ids.

Stored memory includes:

- interaction count
- recent topics
- recent questions
- last plan
- last answer summary

New API:

```text
GET /api/memory/{user_id}
```

### 3. Added trace collection and timeline visualization

Each request now creates a `trace_id` and captures nested spans.

Trace data includes:

- span id
- parent span id
- nesting depth
- status
- duration
- start offset
- end offset

New API:

```text
GET /api/traces/{trace_id}
```

The developer console renders this as a lightweight timeline similar to LangSmith / Jaeger style span views.

### 4. Added workflow introspection API

A new workflow description endpoint was added:

```text
GET /api/workflow
```

This exposes the graph structure, node roles, edges, memory configuration, tracing configuration, and Mermaid diagram text.

### 5. Improved request contracts

`POST /api/query` now supports and returns richer metadata for frontend integration.

Request supports:

- `question`
- `user_id`
- `thread_id`
- `stream`

Response / event stream now includes:

- `trace_id`
- `thread_id`
- `user_id`
- node-level summaries
- result payload

### 6. Improved Researcher behavior

Researcher now follows the intended priority:

- prefer RAG first
- fall back to web search only when RAG is unavailable

This reduces unnecessary search usage and makes the retrieval path easier to explain in interviews.

### 7. Added MCP entrypoint

A new MCP entrypoint was added to expose core agent capabilities as tools.

Current tools include:

- full learning agent query
- RAG query
- public web search
- user memory lookup

## New / Updated Files

### New files

- `api/server_app.py`
- `app/services/memory.py`
- `app/services/tracing.py`
- `app/services/__init__.py`
- `mcp_server.py`
- `docs/DEVELOPER_GUIDE.md`
- `docs/PROJECT_MAP.md`
- `docs/RELEASE_NOTES_DEV_CONSOLE.md`
- `tests/test_dev_console_smoke.py`

### Updated files

- `frontend_demo.html`
- `main.py`
- `app/state.py`
- `app/nodes/planner.py`
- `app/nodes/researcher.py`
- `app/nodes/critic.py`
- `app/tools/search.py`
- `requirements.txt`

## Validation

A smoke test was added to validate the developer console contract end to end without depending on external LLM or RAG services.

Validation covers:

- `/dev`
- `/api/workflow`
- `/api/query` streaming events
- `/api/history/{thread_id}`
- `/api/memory/{user_id}`
- `/api/traces/{trace_id}`

Test file:

- `tests/test_dev_console_smoke.py`

## Suggested GitHub Commit Title

```text
feat: add developer console, long-term memory, and trace timeline support
```

## Suggested GitHub Commit Body

```text
- add /dev developer console for real-time agent workflow inspection
- add SQLite-backed long-term memory keyed by user_id
- add trace collection with nested spans and timeline metadata
- add /api/memory, /api/traces, and /api/workflow endpoints
- update streaming query API with richer frontend event payloads
- switch researcher flow to prefer RAG and fall back to search
- add MCP entrypoint exposing agent, RAG, search, and memory tools
- add developer docs, project map, and smoke test coverage
```
