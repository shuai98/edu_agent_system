"""Critic node: review answer quality and decide whether to revise."""

from __future__ import annotations

from typing import Dict

from langchain_core.messages import HumanMessage
from loguru import logger

from app.nodes.planner import get_llm
from app.services import trace_span
from app.state import AgentState


async def critic_node(state: AgentState) -> Dict:
    logger.info("[Critic] 开始评估内容质量")

    final_answer = state.get("final_answer", "")
    revision_count = state.get("revision_count", 0)
    max_revisions = 2

    if not final_answer:
        logger.warning("[Critic] 没有可评估的内容")
        return {
            "critique": "没有生成可评估的答案。",
            "revision_needed": True,
            "revision_count": revision_count + 1,
            "step_count": state.get("step_count", 0) + 1,
        }

    if revision_count >= max_revisions:
        logger.warning(f"[Critic] 已达到最大重试次数 {max_revisions}，直接接受当前版本")
        return {
            "critique": "已达到最大修订次数，接受当前版本。",
            "revision_needed": False,
            "step_count": state.get("step_count", 0) + 1,
            "messages": [HumanMessage(content="评审通过：已达到修订上限")],
        }

    critique_prompt = f"""
你是一名严格的中文内容评审员，请评估下面这份学习讲解是否适合直接给学生阅读。

【待评估内容】
{final_answer}

评估标准：
1. 是否覆盖了核心知识点。
2. 是否存在明显事实错误或逻辑错误。
3. 是否足够清晰、易懂、结构合理。
4. 是否包含必要的示例、注意事项或实践提示。

请严格使用中文输出，并遵守以下格式：
评分：1-10
主要问题：如果没有问题就写“无”
修改建议：如果不需要修改就写“无需修改”
结论：通过 或 不通过

不要使用 Markdown 标记，不要出现 #、*、``` 等符号。
""".strip()

    try:
        with trace_span(
            "critic_node",
            {
                "thread_id": state.get("thread_id", ""),
                "user_id": state.get("user_id", ""),
                "revision_count": revision_count,
            },
        ):
            llm = get_llm()
            response = await llm.ainvoke(critique_prompt)
            critique_text = response.content

        needs_revision = "不通过" in critique_text or "需要修改" in critique_text

        if needs_revision:
            logger.warning(f"[Critic] 评审未通过，触发第 {revision_count + 1} 次修订")
            return {
                "critique": critique_text,
                "revision_needed": True,
                "revision_count": revision_count + 1,
                "step_count": state.get("step_count", 0) + 1,
                "messages": [HumanMessage(content=f"评审未通过，准备进行第 {revision_count + 1} 次修订")],
            }

        logger.success("[Critic] 内容通过评审")
        return {
            "critique": critique_text,
            "revision_needed": False,
            "step_count": state.get("step_count", 0) + 1,
            "messages": [HumanMessage(content="评审通过，答案可以返回给用户")],
        }
    except Exception as exc:
        logger.error(f"[Critic] 执行失败：{exc}")
        return {
            "critique": f"评审执行失败：{exc}",
            "revision_needed": False,
            "step_count": state.get("step_count", 0) + 1,
            "messages": [HumanMessage(content="评审异常，默认放行当前答案")],
        }
