"""
Critic 节点 - 反思评估者
===========================

职责：评估生成内容的质量，决定是否需要重新生成

面试重点：
1. 自我反思（Self-Reflection）：Agent 的高级能力
2. 循环控制：通过返回 revision_needed 触发图的循环边
3. 幻觉检测：检查内容是否有事实错误或逻辑矛盾

工程意义：
- 这是 LangGraph 相比简单 Chain 的核心优势：支持条件跳转
- 防止 LLM 一本正经地胡说八道
"""

from typing import Dict
from loguru import logger
from langchain_core.messages import HumanMessage

from app.state import AgentState
from app.nodes.planner import get_llm


async def critic_node(state: AgentState) -> Dict:
    """
    反思节点：评估内容质量
    
    输入：state["final_answer"] - 待评估的内容
    输出：state["revision_needed"] - 是否需要重做
    
    面试话术：
    "Critic 是质量把关者。它会检查内容的完整性、准确性和逻辑性。
    如果不合格，会设置 revision_needed=True，触发图的循环边，
    让 Researcher 重新生成。我们设置了最大重试次数，防止死循环。"
    """
    logger.info("🔎 [Critic] 开始评估内容质量...")
    
    final_answer = state.get("final_answer", "")
    revision_count = state.get("revision_count", 0)
    max_revisions = 2  # 最多重试 2 次
    
    if not final_answer:
        logger.warning("⚠️ [Critic] 没有内容可评估")
        return {
            "critique": "无内容",
            "revision_needed": True,
            "revision_count": revision_count + 1,
            "step_count": state.get("step_count", 0) + 1,
        }
    
    # ===== 如果已达到最大重试次数，强制通过 =====
    if revision_count >= max_revisions:
        logger.warning(f"⚠️ [Critic] 已达最大重试次数 ({max_revisions})，强制通过")
        return {
            "critique": "已达最大重试次数，接受当前版本",
            "revision_needed": False,
            "step_count": state.get("step_count", 0) + 1,
            "messages": [HumanMessage(content="✅ 内容审核通过（已达重试上限）")],
        }
    
    # ===== 调用 LLM 进行评估 =====
    critique_prompt = f"""你是一个严格的内容审核员。请评估以下学习材料的质量：

【待评估内容】
{final_answer}

【评估标准】
1. 完整性：是否覆盖了核心知识点？
2. 准确性：是否有明显的事实错误？
3. 逻辑性：内容组织是否清晰？
4. 实用性：是否有代码示例或实战指导？

请按以下格式输出：
评分：[1-10]
问题：[列出主要问题，如果没有则写"无"]
建议：[改进建议，如果不需要则写"无需修改"]
结论：[通过/不通过]
"""
    
    try:
        llm = get_llm()
        response = await llm.ainvoke(critique_prompt)
        critique_text = response.content
        
        # 简单解析结论（生产环境应该用结构化输出）
        needs_revision = "不通过" in critique_text or "需要修改" in critique_text
        
        if needs_revision:
            logger.warning(f"⚠️ [Critic] 内容不合格，触发重做 (第 {revision_count + 1} 次)")
            return {
                "critique": critique_text,
                "revision_needed": True,
                "revision_count": revision_count + 1,
                "step_count": state.get("step_count", 0) + 1,
                "messages": [HumanMessage(content=f"🔄 内容需要改进 (重试 {revision_count + 1}/{max_revisions})")],
            }
        else:
            logger.success("✅ [Critic] 内容合格，通过审核")
            return {
                "critique": critique_text,
                "revision_needed": False,
                "step_count": state.get("step_count", 0) + 1,
                "messages": [HumanMessage(content="✅ 内容审核通过")],
            }
    
    except Exception as e:
        logger.error(f"❌ [Critic] 执行失败: {e}")
        # 失败时默认通过，避免卡住
        return {
            "critique": f"评估失败: {str(e)}",
            "revision_needed": False,
            "step_count": state.get("step_count", 0) + 1,
            "messages": [HumanMessage(content=f"⚠️ 审核异常，默认通过")],
        }

