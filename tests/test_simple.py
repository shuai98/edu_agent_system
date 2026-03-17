"""
简单测试脚本 - 验证各个模块是否正常工作
==========================================

使用方法：
1. 确保已安装依赖：pip install -r requirements.txt
2. 配置 .env 文件
3. 运行：python test_simple.py
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


async def test_llm():
    """测试 LLM 连接"""
    print("\n" + "="*60)
    print("测试 1: LLM 连接")
    print("="*60)
    
    try:
        from app.nodes.planner import get_llm
        
        llm = get_llm()
        response = await llm.ainvoke("请用一句话介绍 Python")
        print(f"✅ LLM 响应: {response.content[:100]}...")
        return True
    except Exception as e:
        print(f"❌ LLM 测试失败: {e}")
        return False


async def test_search():
    """测试搜索工具"""
    print("\n" + "="*60)
    print("测试 2: 搜索工具")
    print("="*60)
    
    try:
        from app.tools.search import search_web
        
        result = await search_web("Python 异步编程", max_results=2)
        print(f"✅ 搜索结果: {result[:200]}...")
        return True
    except Exception as e:
        print(f"❌ 搜索测试失败: {e}")
        return False


async def test_graph():
    """测试完整工作流"""
    print("\n" + "="*60)
    print("测试 3: 完整 Agent 工作流")
    print("="*60)
    
    try:
        from app.graph import create_graph
        from app.state import AgentState
        
        app = create_graph(use_redis=False)
        
        test_input: AgentState = {
            "input": "什么是协程？",
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
            "thread_id": "test-simple",
            "step_count": 0,
        }
        
        # 配置 thread_id（Checkpointer 需要）
        config = {"configurable": {"thread_id": "test-simple"}}
        
        print("开始执行工作流...")
        async for output in app.astream(test_input, config):
            for node_name in output.keys():
                print(f"  ✓ 节点 [{node_name}] 完成")
        
        # 获取最终结果
        final_state = await app.aget_state({"configurable": {"thread_id": "test-simple"}})
        answer = final_state.values.get("final_answer", "")
        
        print(f"\n✅ 工作流完成")
        print(f"📝 最终答案: {answer[:200]}...")
        return True
    
    except Exception as e:
        print(f"❌ 工作流测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    print("\n🧪 EduReflex 系统测试")
    print("="*60)
    
    # 检查环境变量
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("❌ 错误：未配置 DEEPSEEK_API_KEY")
        print("💡 请复制 .env.template 为 .env 并填入配置")
        return
    
    results = []
    
    # 运行测试
    results.append(await test_llm())
    results.append(await test_search())
    results.append(await test_graph())
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("🎉 所有测试通过！系统运行正常。")
        print("\n下一步：")
        print("  1. 启动 API 服务: python main.py --mode api")
        print("  2. 访问文档: http://localhost:8001/docs")
    else:
        print("⚠️ 部分测试失败，请检查配置和网络连接。")


if __name__ == "__main__":
    asyncio.run(main())

