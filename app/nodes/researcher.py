"""
Researcher 节点 - 知识研究员
================================

职责：根据 Planner 的规划，调用工具获取知识

面试重点：
1. 工具调用（Tool Use）：Agent 的核心能力
2. 并发执行：同时调用多个工具，提升效率
3. 结果融合：将多源信息整合成连贯的内容

工程意义：
- 展示了 Agent 与外部系统的交互能力
- 异步并发是后端高性能的关键
"""

import asyncio
from typing import Dict
from loguru import logger
from langchain_core.messages import HumanMessage

from app.state import AgentState
from app.tools.search import search_web, query_rag
from app.nodes.planner import get_llm


async def researcher_node(state: AgentState) -> Dict:
    """
    研究节点：调用工具获取知识
    
    输入：state["search_queries"] - 搜索关键词列表
    输出：state["search_results"] + state["rag_results"]
    
    面试话术：
    "Researcher 是 Agent 的'手'，负责调用外部工具。
    我们使用 asyncio.gather 并发执行搜索和 RAG 查询，
    将原本串行的 6 秒操作压缩到 3 秒，这是异步编程的优势。"
    """
    logger.info("🔍 [Researcher] 开始收集知识...")
    
    search_queries = state.get("search_queries", [])
    if not search_queries or not search_queries[0]:
        logger.warning("⚠️ [Researcher] 没有搜索关键词，跳过")
        return {
            "search_results": "无搜索关键词",
            "rag_results": "",
            "step_count": state.get("step_count", 0) + 1,
        }
    
    # 取第一个关键词（简化版，完整版可以遍历所有）
    query = search_queries[0]
    
    # ===== 并发调用工具（核心亮点） =====
    try:
        # asyncio.gather 会并发执行多个协程
        # 如果其中一个失败，不会影响其他的（return_exceptions=True）
        results = await asyncio.gather(
            search_web(query),
            query_rag(query),
            return_exceptions=True  # 捕获异常而不是抛出
        )
        
        search_result = results[0] if not isinstance(results[0], Exception) else f"搜索失败: {results[0]}"
        rag_result = results[1] if not isinstance(results[1], Exception) else f"RAG 失败: {results[1]}"
        
        logger.success("✅ [Researcher] 知识收集完成")
        
        # ===== 调用 LLM 整合信息 =====
        combined_info = f"""
【网络搜索结果】
{search_result}

【权威知识库】
{rag_result}
"""
        
        synthesis_prompt = f"""请将以下多源信息整合成一段连贯的学习材料：

{combined_info}

要求：
1. 去除重复内容
2. 按逻辑顺序组织（概念 -> 原理 -> 示例）
3. 保留关键代码示例
4. 标注信息来源（网络/知识库）
"""
        
        llm = get_llm()
        synthesis_response = await llm.ainvoke(synthesis_prompt)
        synthesized_content = synthesis_response.content
        
        return {
            "search_results": search_result,
            "rag_results": rag_result,
            "final_answer": synthesized_content,  # 初步答案
            "step_count": state.get("step_count", 0) + 1,
            "messages": [HumanMessage(content="📚 知识收集完成，已整合")],
        }
    
    except Exception as e:
        logger.error(f"❌ [Researcher] 执行失败: {e}")
        return {
            "search_results": f"执行失败: {str(e)}",
            "rag_results": "",
            "step_count": state.get("step_count", 0) + 1,
            "messages": [HumanMessage(content=f"❌ 知识收集失败: {str(e)}")],
        }

