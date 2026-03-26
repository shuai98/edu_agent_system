# Developer Guide

## What to open

Start the API server, then open:

- `http://localhost:8001/dev`
- `http://localhost:8001/docs`
- `http://localhost:8001/api/workflow`

The `/dev` page is the developer console. It shows:

- current `user_id`, `thread_id`, and `trace_id`
- Planner / Researcher / Critic live status
- live SSE event feed
- planner output
- critic output
- final answer
- injected long-term memory summary
- thread state snapshot
- trace timeline

## How to run

```bash
cd D:\BiShe_code\edu_agent_system
python main.py --mode api
```

If you use your conda environment, run it with the Python interpreter from that environment.

## How cross-session memory works

Memory is keyed by `user_id`, not by `thread_id`.

That means:

- use the same `user_id` across different sessions
- you may change `thread_id`
- long-term memory will still accumulate

Current memory storage is local SQLite:

```text
data/agent_memory.db
```

Memory API:

```text
GET /api/memory/{user_id}
```

## How tracing works

Every request gets a `trace_id`.

Trace API:

```text
GET /api/traces/{trace_id}
```

Each trace includes:

- top-level trace metadata
- spans
- duration
- error count
- nested depth
- start and end offsets

The developer console draws these spans as a timeline.

## How to inspect the workflow

### Check whether RAG was used

1. Run a question from `/dev`
2. Watch the Researcher event summary
3. Check whether trace contains `query_rag`
4. If fallback happened, you will usually also see `search_web`

### Check whether the critic requested another round

1. Watch the Critic panel
2. Check the live event feed
3. Check whether Researcher and Critic appear more than once in the trace

### Check whether memory is injected

1. Reuse the same `user_id`
2. Ask 2-3 related questions
3. Run another question
4. Inspect the `Injected Long-Term Memory` panel
5. Verify with `GET /api/memory/{user_id}`

## Current limits

- the trace UI is a lightweight in-project viewer, not a full Jaeger UI
- OpenTelemetry export still requires the related packages and OTLP endpoint config
- the current `/dev` page is a developer console, not a polished end-user product page
