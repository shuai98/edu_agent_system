"""FastAPI API entrypoints for EduReflex."""

from __future__ import annotations

import json
import os
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from loguru import logger
from pydantic import BaseModel, Field

from app.graph import create_graph
from app.services import (
    attach_trace,
    begin_trace,
    end_trace,
    get_trace,
    initialize_tracing,
    memory_store,
    reset_trace,
    trace_span,
)
from app.state import AgentState

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STUDENT_CONSOLE_PATH = PROJECT_ROOT / "frontend_student.html"
DEV_CONSOLE_PATH = PROJECT_ROOT / "frontend_demo.html"
graph_app = None

WORKFLOW_OVERVIEW = {
    "entry_point": "planner",
    "nodes": [
        {
            "id": "planner",
            "title": "规划智能体",
            "description": "将学习目标拆解为步骤计划，并生成检索关键词。",
            "inputs": ["input", "memory_context"],
            "outputs": ["plan", "search_queries", "current_task"],
        },
        {
            "id": "researcher",
            "title": "研究智能体",
            "description": "优先使用 RAG，失败时降级到网络搜索，再整合知识生成答案。",
            "inputs": ["search_queries"],
            "outputs": ["search_results", "rag_results", "final_answer"],
        },
        {
            "id": "critic",
            "title": "评审智能体",
            "description": "审查当前答案质量，并决定是否需要继续修订。",
            "inputs": ["final_answer"],
            "outputs": ["critique", "revision_needed", "revision_count"],
        },
    ],
    "edges": [
        {"from": "planner", "to": "researcher", "type": "direct"},
        {"from": "researcher", "to": "critic", "type": "direct"},
        {"from": "critic", "to": "researcher", "type": "conditional", "when": "revision_needed == True"},
        {"from": "critic", "to": "end", "type": "conditional", "when": "revision_needed == False"},
    ],
    "memory": {
        "enabled": True,
        "storage": "sqlite",
        "path": os.getenv("MEMORY_DB_PATH", "data/agent_memory.db"),
    },
    "tracing": {
        "enabled": True,
        "mode": "in-memory + optional OpenTelemetry export",
        "otlp_endpoint": os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", ""),
    },
    "mermaid": """flowchart LR
    User["学生输入"] --> API["FastAPI /api/query"]
    API --> Planner["规划智能体"]
    Planner --> Researcher["研究智能体"]
    Researcher --> Critic["评审智能体"]
    Critic -->|继续修订| Researcher
    Critic -->|审核通过| Answer["最终答案"]
    Researcher --> RAG["RAG 知识库"]
    Researcher --> Search["网络搜索"]
    API --> Memory["SQLite 长期记忆"]
    API --> Trace["Trace 追踪"]""",
}


class QueryRequest(BaseModel):
    question: str = Field(..., description="Learning goal or question", min_length=1)
    user_id: Optional[str] = Field(None, description="Stable user id for long-term memory")
    thread_id: Optional[str] = Field(None, description="Thread id for checkpoint resume")
    stream: bool = Field(True, description="Whether to use SSE streaming")


class QueryResponse(BaseModel):
    thread_id: str
    trace_id: str
    user_id: str
    answer: str
    plan: str
    critique: str
    steps: int


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(item) for item in value]
    if hasattr(value, "model_dump"):
        return json_safe(value.model_dump())
    if hasattr(value, "content"):
        return {
            "type": value.__class__.__name__,
            "content": json_safe(getattr(value, "content", "")),
        }
    return str(value)


def build_initial_state(question: str, thread_id: str, user_id: str, trace_id: str) -> AgentState:
    return {
        "input": question,
        "final_answer": "",
        "plan": "",
        "current_task": "",
        "search_queries": [],
        "search_results": "",
        "rag_results": "",
        "critique": "",
        "revision_needed": False,
        "revision_count": 0,
        "messages": [],
        "user_id": user_id,
        "thread_id": thread_id,
        "memory_context": memory_store.get_memory_context(user_id),
        "trace_id": trace_id,
        "step_count": 0,
    }


def persist_long_term_memory(state: AgentState) -> None:
    memory_store.record_interaction(
        user_id=state.get("user_id", "") or state.get("thread_id", "anonymous"),
        thread_id=state.get("thread_id", ""),
        question=state.get("input", ""),
        plan=state.get("plan", ""),
        final_answer=state.get("final_answer", ""),
        critique=state.get("critique", ""),
    )


def summarize_node_update(node_name: str, state_update: dict[str, Any]) -> dict[str, Any]:
    if node_name == "planner":
        queries = state_update.get("search_queries", []) or []
        return {
            "label": "规划智能体",
            "stage": "planning",
            "summary": f"已生成学习计划，并准备了 {len(queries)} 条检索查询。",
            "plan": state_update.get("plan", ""),
            "search_queries": queries,
            "current_task": state_update.get("current_task", ""),
        }

    if node_name == "researcher":
        search_result = state_update.get("search_results", "")
        rag_result = state_update.get("rag_results", "")
        used_fallback = bool(search_result and not str(search_result).startswith("SKIPPED: RAG_OK"))
        summary = (
            "RAG 不可用，已自动降级到网络搜索。"
            if used_fallback
            else "已优先使用 RAG，并完成知识整合。"
        )
        return {
            "label": "研究智能体",
            "stage": "knowledge_collection",
            "summary": summary,
            "search_results": search_result,
            "rag_results": rag_result,
            "final_answer": state_update.get("final_answer", ""),
        }

    if node_name == "critic":
        revision_needed = bool(state_update.get("revision_needed", False))
        summary = (
            "评审认为还需要继续修订。"
            if revision_needed
            else "评审通过，当前答案可以返回。"
        )
        return {
            "label": "评审智能体",
            "stage": "review",
            "summary": summary,
            "critique": state_update.get("critique", ""),
            "revision_needed": revision_needed,
            "revision_count": state_update.get("revision_count", 0),
        }

    return {
        "label": node_name,
        "stage": node_name,
        "summary": f"节点 {node_name} 执行完成。",
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    global graph_app

    logger.info("Starting EduReflex API service...")
    initialize_tracing()
    memory_store.initialize()

    use_redis = os.getenv("REDIS_HOST") is not None
    graph_app = create_graph(use_redis=use_redis)
    logger.success("LangGraph workflow loaded.")

    yield

    logger.info("Stopping EduReflex API service...")


app = FastAPI(
    title="EduReflex API",
    description="Multi-agent learning system API",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "service": "EduReflex API",
        "status": "running",
        "version": "0.3.0",
        "links": {
            "openapi": "/docs",
            "student_console": "/student",
            "developer_console": "/dev",
            "workflow": "/api/workflow",
        },
    }


@app.get("/student")
async def student_console():
    if not STUDENT_CONSOLE_PATH.exists():
        raise HTTPException(status_code=404, detail="student console not found")
    return FileResponse(STUDENT_CONSOLE_PATH)


@app.get("/dev")
async def developer_console():
    if not DEV_CONSOLE_PATH.exists():
        raise HTTPException(status_code=404, detail="developer console not found")
    return FileResponse(DEV_CONSOLE_PATH)


@app.get("/api/workflow")
async def workflow_overview():
    return WORKFLOW_OVERVIEW


@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    if graph_app is None:
        raise HTTPException(status_code=503, detail="service not ready")

    thread_id = request.thread_id or str(uuid.uuid4())
    user_id = request.user_id or thread_id
    trace_id, trace_token = begin_trace(
        {
            "thread_id": thread_id,
            "user_id": user_id,
            "stream": request.stream,
        }
    )

    initial_state = build_initial_state(request.question, thread_id, user_id, trace_id)
    config = {"configurable": {"thread_id": thread_id}}

    if request.stream:
        return StreamingResponse(
            stream_agent_response(initial_state, config, trace_id, thread_id, user_id),
            media_type="text/event-stream",
        )

    try:
        with trace_span("api.query", {"thread_id": thread_id, "user_id": user_id}):
            final_state = await graph_app.ainvoke(initial_state, config)
        persist_long_term_memory(final_state)
        end_trace(
            "ok",
            {
                "steps": final_state.get("step_count", 0),
                "revision_count": final_state.get("revision_count", 0),
            },
        )
        return QueryResponse(
            thread_id=thread_id,
            trace_id=trace_id,
            user_id=user_id,
            answer=final_state.get("final_answer", ""),
            plan=final_state.get("plan", ""),
            critique=final_state.get("critique", ""),
            steps=final_state.get("step_count", 0),
        )
    except Exception as exc:
        logger.error(f"Query failed: {exc}")
        end_trace("error", {"error": str(exc)})
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        reset_trace(trace_token)


async def stream_agent_response(
    initial_state: AgentState,
    config: dict,
    trace_id: str,
    thread_id: str,
    user_id: str,
):
    trace_token = attach_trace(trace_id)
    try:
        start_time = time.time()
        node_start_times: dict[str, float] = {}

        yield f"data: {json.dumps({'event': 'session', 'trace_id': trace_id, 'thread_id': thread_id, 'user_id': user_id, 'memory_context': initial_state.get('memory_context', '')}, ensure_ascii=False)}\n\n"

        async for output in graph_app.astream(initial_state, config):
            for node_name, state_update in output.items():
                if node_name not in node_start_times:
                    node_start_times[node_name] = time.time()

                elapsed = round(time.time() - node_start_times[node_name], 2)
                event_data = {
                    'event': 'node',
                    'trace_id': trace_id,
                    'thread_id': thread_id,
                    'user_id': user_id,
                    'node': node_name,
                    'step': state_update.get('step_count', 0),
                    'elapsed_s': elapsed,
                }
                event_data.update(json_safe(summarize_node_update(node_name, state_update)))
                yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"

        final_state = await graph_app.aget_state(config)
        final_values = final_state.values
        persist_long_term_memory(final_values)

        total_time = round(time.time() - start_time, 2)
        end_trace(
            "ok",
            {
                "steps": final_values.get("step_count", 0),
                "revision_count": final_values.get("revision_count", 0),
                "total_time": total_time,
            },
        )

        result_event = {
            'event': 'result',
            'trace_id': trace_id,
            'thread_id': thread_id,
            'user_id': user_id,
            'answer': final_values.get('final_answer', ''),
            'plan': final_values.get('plan', ''),
            'critique': final_values.get('critique', ''),
            'search_queries': final_values.get('search_queries', []),
            'search_results': final_values.get('search_results', ''),
            'rag_results': final_values.get('rag_results', ''),
            'revision_count': final_values.get('revision_count', 0),
            'step_count': final_values.get('step_count', 0),
            'total_time': total_time,
        }
        yield f"data: {json.dumps(json_safe(result_event), ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'event': 'done', 'done': True, 'trace_id': trace_id, 'thread_id': thread_id, 'user_id': user_id, 'total_time': total_time}, ensure_ascii=False)}\n\n"
    except Exception as exc:
        logger.error(f"Streaming failed: {exc}")
        end_trace("error", {"error": str(exc)})
        yield f"data: {json.dumps({'event': 'error', 'error': str(exc), 'trace_id': trace_id, 'thread_id': thread_id, 'user_id': user_id}, ensure_ascii=False)}\n\n"
    finally:
        reset_trace(trace_token)


@app.get("/api/history/{thread_id}")
async def get_history(thread_id: str):
    if graph_app is None:
        raise HTTPException(status_code=503, detail="service not ready")

    try:
        config = {"configurable": {"thread_id": thread_id}}
        state = await graph_app.aget_state(config)
        return {
            "thread_id": thread_id,
            "state": json_safe(state.values),
            "next_node": json_safe(state.next),
        }
    except Exception as exc:
        logger.error(f"History fetch failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/memory/{user_id}")
async def get_memory(user_id: str):
    return memory_store.get_user_memory(user_id)


@app.get("/api/traces/{trace_id}")
async def get_trace_detail(trace_id: str):
    trace = get_trace(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="trace not found")
    return trace


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8001))

    uvicorn.run(
        "api.server_app:app",
        host=host,
        port=port,
        reload=True,
        log_level="info",
    )
