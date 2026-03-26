"""Researcher node: collect knowledge and synthesize the answer."""

from __future__ import annotations

from typing import Dict

from langchain_core.messages import HumanMessage
from loguru import logger

from app.nodes.planner import get_llm
from app.services import trace_span
from app.state import AgentState
from app.tools.search import RAG_FAILURE_CODES, query_rag, search_web


async def researcher_node(state: AgentState) -> Dict:
    logger.info("[Researcher] 开始收集知识")

    search_queries = state.get("search_queries", [])
    if not search_queries or not search_queries[0]:
        logger.warning("[Researcher] Planner 没有生成可用的检索词")
        return {
            "search_results": "NO_SEARCH_QUERY",
            "rag_results": "",
            "step_count": state.get("step_count", 0) + 1,
            "messages": [HumanMessage(content="未生成有效检索词，Researcher 无法继续执行")],
        }

    query = search_queries[0]

    try:
        rag_result = await query_rag(query)
        rag_failed = rag_result in RAG_FAILURE_CODES

        if rag_failed:
            logger.warning("[Researcher] RAG 不可用，降级到网络搜索")
            search_result = await search_web(query)
            search_hint = search_result
            rag_hint = "RAG 当前不可用。"
        else:
            search_result = "SKIPPED: RAG_OK"
            search_hint = "本轮未使用网络搜索，因为 RAG 已成功命中。"
            rag_hint = rag_result

        combined_info = f"""
【网络搜索结果】
{search_hint}

【RAG 结果】
{rag_hint}
""".strip()

        synthesis_prompt = f"""
你是一名中文学习助教。请把下面的多来源资料整理为一份适合学生阅读的中文学习讲解。

{combined_info}

输出要求：
1. 全部使用简体中文，可保留必要英文术语，但要在括号里解释。
2. 不要输出 Markdown 标记，不要出现 #、*、``` 这类符号。
3. 先讲核心结论，再讲概念、原理、示例、注意事项。
4. 如果原始资料是英文，先理解并翻译成中文，再进行整合。
5. 如果 RAG 成功，以 RAG 内容为主；网络搜索只用于补充。
6. 输出风格要自然清晰，适合学生直接阅读，不要写成日志。
""".strip()

        with trace_span(
            "researcher_node",
            {
                "thread_id": state.get("thread_id", ""),
                "user_id": state.get("user_id", ""),
                "query": query,
                "rag_failed": rag_failed,
            },
        ):
            llm = get_llm()
            synthesis_response = await llm.ainvoke(synthesis_prompt)
            synthesized_content = synthesis_response.content

        logger.success("[Researcher] 知识收集完成")
        return {
            "search_results": search_result,
            "rag_results": rag_result,
            "final_answer": synthesized_content,
            "step_count": state.get("step_count", 0) + 1,
            "messages": [HumanMessage(content="知识收集与中文整合已完成")],
        }
    except Exception as exc:
        logger.error(f"[Researcher] 执行失败：{exc}")
        return {
            "search_results": f"RESEARCHER_ERROR: {exc}",
            "rag_results": "",
            "step_count": state.get("step_count", 0) + 1,
            "messages": [HumanMessage(content=f"Researcher 执行失败：{exc}")],
        }
