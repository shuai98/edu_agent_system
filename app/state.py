"""
状态定义模块 - Agent 的"大脑记忆结构"
===========================================

面试重点：
1. TypedDict 是 Python 的类型提示，让代码更安全，IDE 有提示
2. 这个 State 会在所有节点之间传递，类似"全局上下文"
3. LangGraph 的核心就是状态机，每个节点读取和修改这个状态

工程意义：
- 状态集中管理，避免节点间传参混乱
- 支持持久化：整个 State 可以序列化存入 Redis
- 便于调试：打印 State 就能看到整个执行流程
"""

from typing import TypedDict, List, Optional, Annotated
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """
    Agent 状态定义
    
    面试话术：
    "我们使用 TypedDict 定义了一个强类型的状态结构，
    它会在 Planner -> Researcher -> Critic 之间流转。
    每个节点只负责更新自己相关的字段，保证了单一职责原则。"
    """
    
    # ===== 输入输出 =====
    input: str  # 用户的原始问题，如"帮我掌握 Python 异步编程"
    final_answer: str  # 最终生成的学习内容
    
    # ===== Planner 规划阶段 =====
    plan: str  # 学习计划大纲（JSON 格式的子任务列表）
    current_task: str  # 当前正在执行的子任务
    
    # ===== Researcher 研究阶段 =====
    search_queries: List[str]  # 生成的搜索关键词列表
    search_results: str  # 搜索工具返回的原始结果
    rag_results: str  # 从 RAG 系统获取的权威知识
    
    # ===== Critic 反思阶段 =====
    critique: str  # 反思者的评价意见
    revision_needed: bool  # 是否需要重新生成（触发循环的关键）
    revision_count: int  # 已重试次数（防止死循环）
    
    # ===== 消息历史（用于流式输出和调试） =====
    # Annotated[List[BaseMessage], add_messages] 是 LangGraph 的特殊语法
    # add_messages 会自动追加消息而不是覆盖
    messages: Annotated[List[BaseMessage], add_messages]
    
    # ===== 元数据 =====
    thread_id: str  # 会话 ID，用于 Redis 持久化的键
    step_count: int  # 当前执行到第几步（用于前端进度展示）


class GraphConfig(TypedDict):
    """
    图配置 - 控制 Agent 行为的超参数
    
    面试话术：
    "我们将可调参数抽离成配置类，方便 A/B 测试不同策略。
    比如调整 max_revisions 可以平衡质量和响应速度。"
    """
    max_revisions: int  # 最大重试次数，默认 2
    enable_rag: bool  # 是否启用 RAG 工具，默认 True
    enable_search: bool  # 是否启用网络搜索，默认 True
    model_temperature: float  # 模型温度，默认 0.7
    streaming: bool  # 是否启用流式输出，默认 True

