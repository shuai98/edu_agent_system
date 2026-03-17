"""
FastAPI 服务 - 对外 API 接口
================================

职责：提供 HTTP 接口，支持流式输出

面试重点：
1. 异步 API：FastAPI 的核心优势，处理高并发
2. SSE（Server-Sent Events）：实时推送 Agent 思考过程
3. 状态管理：通过 thread_id 实现会话隔离

工程意义：
- 前后端分离架构的后端部分
- 流式输出提升用户体验（类似 ChatGPT 的打字效果）
"""

import os
import uuid
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from loguru import logger
from dotenv import load_dotenv

from app.graph import create_graph
from app.state import AgentState

# 加载环境变量
load_dotenv()

# 全局变量：存储编译后的图
graph_app = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    
    面试话术：
    "我们在应用启动时编译 LangGraph，避免每次请求都重新编译。
    这是一个性能优化技巧，类似于数据库连接池的思想。"
    """
    global graph_app
    logger.info("🚀 启动 EduReflex API 服务...")
    
    # 启动时：编译图
    use_redis = os.getenv("REDIS_HOST") is not None
    graph_app = create_graph(use_redis=use_redis)
    logger.success("✅ LangGraph 已加载")
    
    yield
    
    # 关闭时：清理资源
    logger.info("👋 关闭服务...")


# 创建 FastAPI 应用
app = FastAPI(
    title="EduReflex API",
    description="多智能体协作学习系统",
    version="0.1.0",
    lifespan=lifespan,
)

# 配置 CORS（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== 请求/响应模型 =====
class QueryRequest(BaseModel):
    """查询请求"""
    question: str = Field(..., description="学习目标或问题", min_length=1)
    thread_id: Optional[str] = Field(None, description="会话 ID（用于续接）")
    stream: bool = Field(True, description="是否启用流式输出")


class QueryResponse(BaseModel):
    """查询响应（非流式）"""
    thread_id: str
    answer: str
    plan: str
    steps: int


# ===== API 端点 =====
@app.get("/")
async def root():
    """健康检查"""
    return {
        "service": "EduReflex API",
        "status": "running",
        "version": "0.1.0",
    }


@app.post("/api/query")
async def query(request: QueryRequest):
    """
    主查询接口
    
    面试话术：
    "这是核心接口。支持两种模式：
    1. 流式模式（stream=true）：通过 SSE 实时推送节点状态
    2. 非流式模式：等待全部完成后返回结果
    
    我们使用 thread_id 实现会话隔离，支持多用户并发。"
    """
    if graph_app is None:
        raise HTTPException(status_code=503, detail="服务未就绪")
    
    # 生成或使用已有的 thread_id
    thread_id = request.thread_id or str(uuid.uuid4())
    
    # 构造初始状态
    initial_state: AgentState = {
        "input": request.question,
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
        "thread_id": thread_id,
        "step_count": 0,
    }
    
    # 配置（用于持久化）
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }
    
    if request.stream:
        # 流式模式
        return StreamingResponse(
            stream_agent_response(initial_state, config),
            media_type="text/event-stream",
        )
    else:
        # 非流式模式
        try:
            final_state = await graph_app.ainvoke(initial_state, config)
            return QueryResponse(
                thread_id=thread_id,
                answer=final_state.get("final_answer", ""),
                plan=final_state.get("plan", ""),
                steps=final_state.get("step_count", 0),
            )
        except Exception as e:
            logger.error(f"❌ 执行失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))


async def stream_agent_response(initial_state: AgentState, config: dict):
    """
    流式生成器：实时推送 Agent 执行状态
    
    面试话术：
    "这是 SSE（Server-Sent Events）的实现。
    我们使用 astream 方法逐节点推送状态，前端可以实时显示：
    '正在规划...' -> '正在搜索...' -> '正在审核...'
    这种体验类似 ChatGPT 的打字效果，大幅提升用户感知。"
    """
    import json
    import time
    
    try:
        start_time = time.time()
        node_start_times = {}
        
        # astream 返回异步生成器，每个节点执行完会 yield 一次
        async for output in graph_app.astream(initial_state, config):
            # output 格式：{"node_name": {"state_updates": ...}}
            for node_name, state_update in output.items():
                # 记录节点开始时间
                if node_name not in node_start_times:
                    node_start_times[node_name] = time.time()
                
                # 计算节点耗时
                node_time = time.time() - node_start_times[node_name]
                
                # 构造 SSE 消息
                message = ""
                if state_update.get("messages"):
                    message = state_update["messages"][-1].content
                
                event_data = {
                    "node": node_name,
                    "step": state_update.get("step_count", 0),
                    "message": message,
                    "time": round(node_time, 2),
                }
                
                # SSE 格式：data: {json}\n\n
                yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
        
        # 获取最终状态
        final_state = await graph_app.aget_state(config)
        final_answer = final_state.values.get("final_answer", "")
        
        # 计算总耗时
        total_time = time.time() - start_time
        
        # 发送最终答案
        yield f"data: {json.dumps({'answer': final_answer, 'total_time': round(total_time, 2)}, ensure_ascii=False)}\n\n"
        
        # 发送结束标记
        yield f"data: {json.dumps({'done': True, 'total_time': round(total_time, 2)})}\n\n"
    
    except Exception as e:
        logger.error(f"❌ 流式输出失败: {e}")
        error_msg = str(e).replace('"', '\\"')
        yield f"data: {json.dumps({'error': error_msg})}\n\n"


@app.get("/api/history/{thread_id}")
async def get_history(thread_id: str):
    """
    获取会话历史
    
    面试话术：
    "通过 Checkpointer，我们可以查询任意会话的历史状态。
    这对于调试和用户查看学习记录非常有用。"
    """
    if graph_app is None:
        raise HTTPException(status_code=503, detail="服务未就绪")
    
    try:
        config = {"configurable": {"thread_id": thread_id}}
        state = await graph_app.aget_state(config)
        
        if state is None:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return {
            "thread_id": thread_id,
            "state": state.values,
            "next_node": state.next,
        }
    except Exception as e:
        logger.error(f"❌ 获取历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== 启动命令 =====
if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8001))
    
    uvicorn.run(
        "api.server:app",
        host=host,
        port=port,
        reload=True,  # 开发模式：代码变更自动重启
        log_level="info",
    )

