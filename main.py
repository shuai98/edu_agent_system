"""
EduReflex - 多智能体协作学习系统
主入口文件
================================

这是整个项目的启动入口

使用方法：
1. 安装依赖：pip install -r requirements.txt
2. 配置环境变量：复制 .env.template 为 .env 并填入 API Key
3. 启动服务：python main.py
4. 访问 API 文档：http://localhost:8001/docs
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
from loguru import logger

# 加载环境变量
load_dotenv()

# 配置日志
logger.remove()  # 移除默认处理器
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=os.getenv("LOG_LEVEL", "INFO"),
)


def check_environment():
    """
    检查环境配置
    
    面试话术：
    "在启动前，我们会检查必要的环境变量是否配置。
    这是一个防御性编程的实践，避免运行时才发现配置错误。"
    """
    logger.info("🔍 检查环境配置...")
    
    required_vars = ["DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ 缺少必要的环境变量: {', '.join(missing_vars)}")
        logger.info("💡 请复制 .env.template 为 .env 并填入配置")
        sys.exit(1)
    
    logger.success("✅ 环境配置检查通过")


async def test_agent():
    """
    测试 Agent 工作流（命令行模式）
    
    面试话术：
    "这是一个快速测试函数，可以在不启动 Web 服务的情况下验证 Agent 逻辑。
    在开发阶段非常有用。"
    """
    from app.graph import create_graph
    from app.state import AgentState
    
    logger.info("🧪 开始测试 Agent 工作流...")
    
    # 创建图
    app = create_graph(use_redis=False)
    
    # 构造测试输入
    test_input: AgentState = {
        "input": "帮我快速了解 Python 异步编程的核心概念",
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
        "user_id": "test-user",
        "thread_id": "test-001",
        "memory_context": "",
        "trace_id": "",
        "step_count": 0,
    }
    
    # 流式执行
    logger.info("=" * 60)
    async for output in app.astream(test_input):
        for node_name, state_update in output.items():
            logger.info(f"📍 节点 [{node_name}] 执行完成")
            if state_update.get("messages"):
                logger.info(f"   {state_update['messages'][-1].content}")
    
    logger.info("=" * 60)
    
    # 获取最终状态
    final_state = await app.aget_state({"configurable": {"thread_id": "test-001"}})
    
    logger.success("🎉 测试完成！")
    logger.info(f"\n【最终答案】\n{final_state.values.get('final_answer', '无')}\n")


def start_api_server():
    """
    启动 FastAPI 服务
    
    面试话术：
    "生产模式下，我们使用 uvicorn 启动 FastAPI 服务。
    支持热重载（开发模式）和多进程（生产模式）。"
    """
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8001))
    debug = os.getenv("DEBUG", "true").lower() == "true"
    
    logger.info(f"🚀 启动 API 服务: http://{host}:{port}")
    logger.info(f"📖 API 文档: http://{host}:{port}/docs")
    
    uvicorn.run(
        "api.server_app:app",
        host=host,
        port=port,
        reload=debug,  # 开发模式启用热重载
        log_level="info",
    )


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="EduReflex 多智能体学习系统")
    parser.add_argument(
        "--mode",
        choices=["api", "test", "visualize", "mcp"],
        default="api",
        help="运行模式：api=启动服务, test=测试工作流, visualize=可视化图结构, mcp=MCP 服务",
    )
    
    args = parser.parse_args()
    
    # 检查环境
    check_environment()
    
    if args.mode == "api":
        # 启动 API 服务
        start_api_server()
    
    elif args.mode == "test":
        # 测试模式
        asyncio.run(test_agent())
    
    elif args.mode == "visualize":
        # 可视化图结构
        from app.graph import visualize_graph
        visualize_graph()

    elif args.mode == "mcp":
        from mcp_server import run_mcp_server
        run_mcp_server()


if __name__ == "__main__":
    main()
