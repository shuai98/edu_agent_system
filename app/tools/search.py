"""External knowledge tools for web search and RAG access."""

from __future__ import annotations

import os
from typing import Any, Dict, List

import httpx
from loguru import logger

from app.services import trace_span

RAG_FAILURE_CODES = {
    "RAG_NOT_CONFIGURED",
    "RAG_UNAVAILABLE",
    "RAG_TIMEOUT",
    "RAG_ERROR",
    "RAG_INVALID_RESPONSE",
}


def _format_search_results(results: List[Dict[str, Any]]) -> str:
    if not results:
        return "未检索到相关的网络结果。"

    lines: List[str] = []
    for index, result in enumerate(results, start=1):
        title = result.get("title") or "未命名结果"
        snippet = (result.get("body") or "").strip()[:240]
        url = result.get("href") or ""
        lines.append(f"结果 {index}：{title}\n摘要：{snippet}\n来源：{url}")
    return "\n\n".join(lines)


async def search_web(query: str, max_results: int = 3) -> str:
    """Search the public web with DuckDuckGo."""
    try:
        with trace_span("search_web", {"query": query, "max_results": max_results}):
            from ddgs import DDGS

            logger.info(f"[Search] 开始网络搜索：{query}")
            results = list(
                DDGS().text(
                    query,
                    max_results=max_results,
                    region="wt-wt",
                )
            )

        formatted = _format_search_results(results)
        logger.success(f"[Search] 搜索完成，返回 {len(results)} 条结果")
        return formatted
    except Exception as exc:
        logger.error(f"[Search] 失败：{exc}")
        return f"WEB_SEARCH_ERROR: {exc}"


async def query_rag(question: str, top_k: int = 3) -> str:
    """Query the configured RAG backend."""
    rag_url = os.getenv("RAG_API_URL")
    if not rag_url:
        logger.debug("[RAG] 未配置 RAG_API_URL")
        return "RAG_NOT_CONFIGURED"

    rag_key = os.getenv("RAG_API_KEY", "")
    request_formats = [
        {"question": question, "top_k": top_k},
        {"query": question, "top_k": top_k},
        {"message": question, "top_k": top_k},
        {"text": question, "top_k": top_k},
    ]

    try:
        with trace_span(
            "query_rag",
            {"question": question, "top_k": top_k, "rag_url": rag_url},
        ):
            async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
                last_error = "unknown error"
                data: Dict[str, Any] | None = None

                for payload in request_formats:
                    try:
                        response = await client.post(
                            rag_url,
                            json=payload,
                            headers={
                                "Authorization": f"Bearer {rag_key}" if rag_key else "",
                                "Content-Type": "application/json",
                            },
                        )
                    except httpx.TimeoutException:
                        logger.warning("[RAG] 请求超时")
                        return "RAG_TIMEOUT"
                    except Exception as exc:
                        last_error = str(exc)
                        continue

                    if response.status_code != 200:
                        last_error = f"status_code={response.status_code}"
                        continue

                    try:
                        data = response.json()
                    except ValueError:
                        last_error = "invalid json response"
                        continue

                    break

        if data is None:
            logger.warning(f"[RAG] 后端不可用：{last_error}")
            return "RAG_UNAVAILABLE"

        answer = (
            data.get("answer")
            or data.get("response")
            or data.get("result")
            or data.get("output")
            or data.get("content")
            or ""
        )
        sources = data.get("sources") or data.get("references") or []

        if not answer:
            logger.warning(f"[RAG] 响应结构无效：{str(data)[:200]}")
            return "RAG_INVALID_RESPONSE"

        lines = ["[RAG回答]", str(answer).strip()]
        if sources:
            lines.append("")
            lines.append("[RAG来源]")
            for index, source in enumerate(sources[:3], start=1):
                if isinstance(source, dict):
                    title = source.get("title") or source.get("source") or "未知来源"
                    lines.append(f"{index}. {title}")
                else:
                    lines.append(f"{index}. {source}")

        logger.success("[RAG] 查询完成")
        return "\n".join(lines)
    except Exception as exc:
        logger.warning(f"[RAG] 调用失败：{exc}")
        return "RAG_ERROR"


async def search_with_fallback(query: str) -> str:
    """Prefer RAG, fall back to web search when RAG is unavailable."""
    rag_result = await query_rag(query)
    if rag_result in RAG_FAILURE_CODES:
        logger.warning("[Search] RAG 不可用，改用网络搜索")
        return await search_web(query)
    return rag_result
