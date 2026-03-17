"""
Planner 节点 - 任务规划者
============================

职责：将模糊的学习目标拆解为结构化的子任务

面试重点：
1. 结构化输出：使用 Pydantic 模型确保输出格式正确
2. Prompt 工程：使用 Few-shot 提示（给示例）提高输出质量
3. 异步调用：使用 ainvoke 而非 invoke，不阻塞事件循环

工程意义：
- 这是整个 Agent 的"大脑"，决定了后续的执行路径
- 好的规划能减少无效搜索，提升用户体验
- 结构化输出避免 JSON 解析错误，提高稳定性
"""

import os
import json
from typing import Dict, List
from loguru import logger
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.state import AgentState


# ===== 结构化输出模型 =====
class Task(BaseModel):
    """单个学习任务"""
    id: int = Field(description="任务编号")
    title: str = Field(description="任务标题")
    description: str = Field(description="任务详细说明")
    search_query: str = Field(description="搜索关键词")


class LearningPlan(BaseModel):
    """学习计划"""
    goal: str = Field(description="学习目标")
    tasks: List[Task] = Field(description="子任务列表，3-5个任务")
    
    class Config:
        json_schema_extra = {
            "example": {
                "goal": "掌握 Python 异步编程",
                "tasks": [
                    {
                        "id": 1,
                        "title": "理解异步编程概念",
                        "description": "学习什么是协程、事件循环",
                        "search_query": "Python asyncio 协程 事件循环"
                    }
                ]
            }
        }


# 初始化模型（全局单例，避免重复创建）
def get_llm():
    """
    获取 LLM 实例
    
    面试话术：
    "我们使用工厂函数而非全局变量，方便单元测试时 Mock。
    支持 DeepSeek 和 OpenAI 两种后端，通过环境变量切换。"
    """
    provider = os.getenv("LLM_PROVIDER", "deepseek")
    
    if provider == "deepseek":
        return ChatOpenAI(
            model=os.getenv("MODEL_NAME", "deepseek-chat"),
            openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
            openai_api_base=os.getenv("DEEPSEEK_BASE_URL"),
            temperature=0.7,
        )
    else:  # openai
        return ChatOpenAI(
            model=os.getenv("MODEL_NAME", "gpt-4o"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.7,
        )


async def planner_node(state: AgentState) -> Dict:
    """
    规划节点：拆解学习任务（使用结构化输出）
    
    输入：state["input"] - 用户的学习目标
    输出：state["plan"] - JSON 格式的子任务列表
    
    面试话术：
    "Planner 使用 Pydantic 模型定义结构化输出，避免 JSON 解析错误。
    这是 LangChain 的最佳实践，比传统的字符串解析更稳定。
    我们还使用 Few-shot Prompting 提高输出质量。"
    """
    logger.info("🧠 [Planner] 开始规划任务...")
    
    user_input = state.get("input", "")
    
    # ===== 增强的 Prompt（包含多个示例） =====
    system_prompt = """你是一个专业的学习规划助手。你的任务是将用户的学习目标拆解为 3-5 个有序的子任务。

任务拆解原则：
1. 循序渐进：从基础概念到高级应用
2. 理论结合实践：既有概念讲解，也有代码示例
3. 搜索关键词精准：便于搜索引擎理解

示例 1：
用户输入："帮我掌握 Python 异步编程"
输出：
- 任务1：理解异步编程概念（协程、事件循环）
- 任务2：掌握 async/await 语法
- 任务3：学习并发执行（asyncio.gather）
- 任务4：实战：异步 HTTP 请求
- 任务5：常见陷阱和最佳实践

示例 2：
用户输入："什么是 Python 装饰器？"
输出：
- 任务1：装饰器基本概念和作用
- 任务2：装饰器语法和实现原理
- 任务3：常见应用场景和示例

示例 3：
用户输入："如何用 FastAPI 实现 RESTful API？"
输出：
- 任务1：FastAPI 基础和路由定义
- 任务2：请求参数和数据验证
- 任务3：数据库集成和 ORM
- 任务4：认证和权限控制
- 任务5：部署和性能优化

现在请为用户的学习目标制定计划。"""
    
    user_prompt = f"请为以下学习目标制定计划：\n{user_input}"
    
    # ===== 使用结构化输出 =====
    llm = get_llm()
    
    try:
        # 方法1：使用 with_structured_output（推荐）
        llm_with_structure = llm.with_structured_output(LearningPlan)
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        
        # 调用 LLM，直接返回 Pydantic 对象
        plan: LearningPlan = await llm_with_structure.ainvoke(messages)
        
        logger.success(f"✅ [Planner] 规划完成，共 {len(plan.tasks)} 个子任务")
        
        # 转换为 JSON 字符串
        plan_json = plan.model_dump()
        plan_text = json.dumps(plan_json, ensure_ascii=False, indent=2)
        
        # 提取第一个任务
        first_task = plan.tasks[0] if plan.tasks else None
        
        return {
            "plan": plan_text,
            "current_task": first_task.title if first_task else user_input,
            "search_queries": [first_task.search_query if first_task else user_input],
            "step_count": state.get("step_count", 0) + 1,
            "messages": [HumanMessage(content=f"📋 规划完成：{plan.goal}")],
        }
    
    except Exception as e:
        logger.error(f"❌ [Planner] 结构化输出失败: {e}")
        logger.warning("⚠️ 降级到传统 JSON 解析模式")
        
        # 降级方案：使用传统方式
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
            response = await llm.ainvoke(messages)
            plan_text = response.content.strip()
            
            # 清理 Markdown 标记
            if plan_text.startswith("```json"):
                plan_text = plan_text.replace("```json", "").replace("```", "").strip()
            elif plan_text.startswith("```"):
                plan_text = plan_text.replace("```", "").strip()
            
            # 解析 JSON
            plan_json = json.loads(plan_text)
            
            logger.success(f"✅ [Planner] 降级模式规划完成")
            
            first_task = plan_json["tasks"][0] if plan_json.get("tasks") else {}
            
            return {
                "plan": plan_text,
                "current_task": first_task.get("title", user_input),
                "search_queries": [first_task.get("search_query", user_input)],
                "step_count": state.get("step_count", 0) + 1,
                "messages": [HumanMessage(content=f"📋 规划完成：{plan_json.get('goal', user_input)}")],
            }
        
        except Exception as e2:
            logger.error(f"❌ [Planner] 降级模式也失败: {e2}")
            # 最终降级：简化模式
            return {
                "plan": f"简化模式：{user_input}",
                "current_task": user_input,
                "search_queries": [user_input],
                "step_count": state.get("step_count", 0) + 1,
                "messages": [HumanMessage(content="⚠️ 规划失败，使用简化模式")],
            }

