# Project Map

## Structure Diagram

```mermaid
flowchart TB
    main[main.py] --> api[api/server_app.py]
    main --> mcp[mcp_server.py]
    api --> graph[app/graph.py]
    graph --> planner[app/nodes/planner.py]
    graph --> researcher[app/nodes/researcher.py]
    graph --> critic[app/nodes/critic.py]
    planner --> state[app/state.py]
    researcher --> tools[app/tools/search.py]
    api --> memory[app/services/memory.py]
    api --> tracing[app/services/tracing.py]
    mcp --> graph
    api --> frontend[frontend_demo.html]
```

## Core Files

### Root

- `main.py`: single entrypoint for `api`, `test`, `visualize`, and `mcp` modes.
- `mcp_server.py`: MCP server entrypoint exposing EduReflex tools.
- `frontend_demo.html`: developer console page served by `/dev`.
- `requirements.txt`: project dependencies.

### API Layer

- `api/server_app.py`: current API entrypoint. Exposes `/api/query`, `/api/history/{thread_id}`, `/api/memory/{user_id}`, `/api/traces/{trace_id}`, `/api/workflow`, and `/dev`.
- `api/server.py`: older API file kept for reference, not the current entrypoint.

### Workflow Layer

- `app/graph.py`: defines the LangGraph workflow and the Planner -> Researcher -> Critic loop.
- `app/state.py`: shared Agent state schema.

### Nodes

- `app/nodes/planner.py`: creates the structured learning plan and search queries.
- `app/nodes/researcher.py`: prefers RAG, falls back to web search, then synthesizes the answer.
- `app/nodes/critic.py`: reviews the answer and decides whether another revision is needed.

### Tools

- `app/tools/search.py`: wraps RAG calls and web search calls.

### Services

- `app/services/memory.py`: SQLite-backed long-term memory store.
- `app/services/tracing.py`: in-memory tracing with nested spans and optional OpenTelemetry export hooks.

### Frontend and Docs

- `frontend_demo.html`: live developer console.
- `docs/DEVELOPER_GUIDE.md`: how to use the console, memory, and tracing.
- `docs/PROJECT_MAP.md`: this file.

## Runtime Data Flow

1. client calls `POST /api/query`
2. `api/server_app.py` builds `AgentState`
3. `memory.py` injects long-term memory summary by `user_id`
4. `graph.py` runs Planner -> Researcher -> Critic
5. `researcher.py` calls `query_rag`
6. if RAG fails, `search_web` is used as fallback
7. `critic.py` decides whether to revise or finish
8. final result is stored back into `memory.py`
9. spans are collected in `tracing.py`
10. `/dev` fetches memory, trace, workflow, and thread state for display

## Recommended Reading Order

If you want to understand the project quickly, read in this order:

1. `main.py`
2. `api/server_app.py`
3. `app/graph.py`
4. `app/state.py`
5. `app/nodes/planner.py`
6. `app/nodes/researcher.py`
7. `app/nodes/critic.py`
8. `app/services/memory.py`
9. `app/services/tracing.py`
