"""
Graph 模块 - LangGraph 状态机组装
====================================

这是整个系统的核心：将节点连接成有向图

面试重点：
1. 状态机设计：不是简单的顺序链，而是带条件跳转的图
2. 条件边（Conditional Edge）：根据 Critic 的评估结果决定下一步
3. 持久化（Checkpointer）：使用 Redis 保存状态，支持断点续行

工程意义：
- 这是 LangGraph 的核心价值：复杂工作流编排
- 相比 LangChain 的 Chain，Graph 支持循环、分支、并行
"""

import os
from typing import Literal
from loguru import logger
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
# from langgraph.checkpoint.redis import RedisSaver  # 需要时启用

from app.state import AgentState
from app.nodes import planner_node, researcher_node, critic_node


def should_continue(state: AgentState) -> Literal["researcher", "end"]:
    """
    条件路由函数：决定是否需要重做
    
    面试话术：
    "这是 LangGraph 的条件边（Conditional Edge）。
    根据 Critic 的评估结果，决定是回到 Researcher 重新生成，
    还是结束流程。这种动态路由是传统 Chain 做不到的。"
    """
    revision_needed = state.get("revision_needed", False)
    
    if revision_needed:
        logger.info("🔄 [Router] Critic 要求重做，返回 Researcher")
        return "researcher"
    else:
        logger.info("✅ [Router] 内容合格，结束流程")
        return "end"


def create_graph(use_redis: bool = False):
    """
    创建 LangGraph 工作流
    
    参数：
        use_redis: 是否使用 Redis 持久化（生产环境推荐）
    
    返回：
        编译后的可执行图
    
    面试话术：
    "我们使用 StateGraph 构建了一个三节点的协作系统：
    1. Planner 拆解任务
    2. Researcher 收集知识
    3. Critic 评估质量
    
    关键设计是 Critic 到 Researcher 的循环边，实现自我反思。
    我们还集成了 Redis Checkpointer，支持断点续行。"
    """
    
    # ===== 1. 创建图 =====
    workflow = StateGraph(AgentState)
    
    # ===== 2. 添加节点 =====
    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("critic", critic_node)
    
    # ===== 3. 设置入口点 =====
    workflow.set_entry_point("planner")
    
    # ===== 4. 添加边（定义流转逻辑） =====
    # Planner -> Researcher（固定边）
    workflow.add_edge("planner", "researcher")
    
    # Researcher -> Critic（固定边）
    workflow.add_edge("researcher", "critic")
    
    # Critic -> ? （条件边：根据评估结果决定）
    workflow.add_conditional_edges(
        "critic",
        should_continue,  # 路由函数
        {
            "researcher": "researcher",  # 不合格：回到 Researcher
            "end": END,  # 合格：结束
        }
    )
    
    # ===== 5. 配置持久化 =====
    if use_redis:
        # 生产环境：使用 Redis
        try:
            from langgraph.checkpoint.redis import RedisSaver
            import redis
            
            redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                db=int(os.getenv("REDIS_DB", 0)),
                password=os.getenv("REDIS_PASSWORD", None),
                decode_responses=True,
            )
            checkpointer = RedisSaver(redis_client)
            logger.info("✅ 使用 Redis 持久化")
        except ImportError:
            logger.warning("⚠️ Redis 依赖未安装，降级到内存模式")
            checkpointer = MemorySaver()
    else:
        # 开发环境：使用内存
        checkpointer = MemorySaver()
        logger.info("✅ 使用内存持久化（开发模式）")
    
    # ===== 6. 编译图 =====
    app = workflow.compile(checkpointer=checkpointer)
    
    logger.success("🎯 LangGraph 工作流编译完成")
    return app


# ===== 可视化图结构（调试用） =====
def visualize_graph():
    """
    生成图的 Mermaid 可视化代码
    
    面试话术：
    "我们可以将图结构导出为 Mermaid 图，便于文档和演示。
    这在向非技术人员解释系统架构时非常有用。"
    """
    app = create_graph(use_redis=False)
    
    try:
        # LangGraph 支持导出为 Mermaid
        mermaid_code = app.get_graph().draw_mermaid()
        print("\n===== 图结构可视化 =====")
        print(mermaid_code)
        print("===========================\n")
        return mermaid_code
    except Exception as e:
        logger.error(f"可视化失败: {e}")
        return None


if __name__ == "__main__":
    # 测试：打印图结构
    visualize_graph()

