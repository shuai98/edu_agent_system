"""MCP entrypoint exposing EduReflex tools."""

from __future__ import annotations

import os
import uuid
from typing import Any, Dict

from loguru import logger

from app.graph import create_graph
from app.services import begin_trace, end_trace, memory_store, reset_trace
from app.tools.search import query_rag, search_web

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover - optional runtime dependency
    FastMCP = None


def _build_initial_state(question: str, thread_id: str, user_id: str, trace_id: str) -> Dict[str, Any]:
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


async def _run_agent(question: str, user_id: str) -> Dict[str, Any]:
    memory_store.initialize()
    thread_id = str(uuid.uuid4())
    trace_id, trace_token = begin_trace({"source": "mcp", "user_id": user_id})
    graph = create_graph(use_redis=os.getenv("REDIS_HOST") is not None)
    initial_state = _build_initial_state(question, thread_id, user_id, trace_id)
    config = {"configurable": {"thread_id": thread_id}}

    try:
        final_state = await graph.ainvoke(initial_state, config)
        memory_store.record_interaction(
            user_id=user_id,
            thread_id=thread_id,
            question=question,
            plan=final_state.get("plan", ""),
            final_answer=final_state.get("final_answer", ""),
            critique=final_state.get("critique", ""),
        )
        end_trace("ok", {"steps": final_state.get("step_count", 0)})
        return {
            "trace_id": trace_id,
            "thread_id": thread_id,
            "answer": final_state.get("final_answer", ""),
            "plan": final_state.get("plan", ""),
            "steps": final_state.get("step_count", 0),
        }
    except Exception as exc:
        logger.error(f"MCP agent query failed: {exc}")
        end_trace("error", {"error": str(exc)})
        raise
    finally:
        reset_trace(trace_token)


if FastMCP is not None:
    mcp = FastMCP("EduReflex")

    @mcp.tool()
    async def query_learning_agent(question: str, user_id: str = "mcp-user") -> Dict[str, Any]:
        """Run the full EduReflex workflow."""
        return await _run_agent(question, user_id)

    @mcp.tool()
    async def query_rag_knowledge(question: str, top_k: int = 3) -> str:
        """Query the configured RAG backend."""
        return await query_rag(question, top_k=top_k)

    @mcp.tool()
    async def search_public_web(query: str, max_results: int = 3) -> str:
        """Search public web results."""
        return await search_web(query, max_results=max_results)

    @mcp.tool()
    def get_user_memory(user_id: str) -> Dict[str, Any]:
        """Return persisted long-term memory for a user."""
        return memory_store.get_user_memory(user_id)


def run_mcp_server() -> None:
    if FastMCP is None:
        raise RuntimeError("MCP support requires installing the `mcp` package.")
    memory_store.initialize()
    mcp.run()
