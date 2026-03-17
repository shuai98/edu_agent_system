"""
完整测试脚本 - 展示系统能力
============================

这个脚本会运行多个测试案例，并生成详细的性能报告

使用方法：
python test_complete.py
"""

import asyncio
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

load_dotenv()


async def test_case_1():
    """测试案例 1：简单概念查询"""
    from app.graph import create_graph
    from app.state import AgentState
    
    logger.info("\n" + "="*60)
    logger.info("测试案例 1：简单概念查询")
    logger.info("="*60)
    
    app = create_graph(use_redis=False)
    
    test_input: AgentState = {
        "input": "什么是 Python 装饰器？",
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
        "thread_id": "test-case-1",
        "step_count": 0,
    }
    
    config = {"configurable": {"thread_id": "test-case-1"}}
    
    start_time = time.time()
    node_times = {}
    
    async for output in app.astream(test_input, config):
        for node_name in output.keys():
            node_times[node_name] = node_times.get(node_name, 0) + 1
            logger.info(f"  ✓ 节点 [{node_name}] 完成")
    
    total_time = time.time() - start_time
    
    final_state = await app.aget_state(config)
    answer = final_state.values.get("final_answer", "")
    
    logger.success(f"\n✅ 测试完成，总耗时: {total_time:.2f}秒")
    logger.info(f"📝 答案长度: {len(answer)} 字符")
    logger.info(f"🔄 重做次数: {final_state.values.get('revision_count', 0)}")
    
    return {
        "case": "简单概念查询",
        "question": test_input["input"],
        "total_time": round(total_time, 2),
        "answer_length": len(answer),
        "revision_count": final_state.values.get("revision_count", 0),
        "node_executions": node_times,
    }


async def test_case_2():
    """测试案例 2：复杂主题学习"""
    from app.graph import create_graph
    from app.state import AgentState
    
    logger.info("\n" + "="*60)
    logger.info("测试案例 2：复杂主题学习")
    logger.info("="*60)
    
    app = create_graph(use_redis=False)
    
    test_input: AgentState = {
        "input": "帮我掌握 Python 异步编程",
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
        "thread_id": "test-case-2",
        "step_count": 0,
    }
    
    config = {"configurable": {"thread_id": "test-case-2"}}
    
    start_time = time.time()
    node_times = {}
    
    async for output in app.astream(test_input, config):
        for node_name in output.keys():
            node_times[node_name] = node_times.get(node_name, 0) + 1
            logger.info(f"  ✓ 节点 [{node_name}] 完成")
    
    total_time = time.time() - start_time
    
    final_state = await app.aget_state(config)
    answer = final_state.values.get("final_answer", "")
    plan = final_state.values.get("plan", "")
    
    # 尝试解析任务数量
    task_count = 0
    try:
        plan_json = json.loads(plan)
        task_count = len(plan_json.get("tasks", []))
    except:
        pass
    
    logger.success(f"\n✅ 测试完成，总耗时: {total_time:.2f}秒")
    logger.info(f"📋 任务拆解数: {task_count}")
    logger.info(f"📝 答案长度: {len(answer)} 字符")
    logger.info(f"🔄 重做次数: {final_state.values.get('revision_count', 0)}")
    
    return {
        "case": "复杂主题学习",
        "question": test_input["input"],
        "total_time": round(total_time, 2),
        "task_count": task_count,
        "answer_length": len(answer),
        "revision_count": final_state.values.get("revision_count", 0),
        "node_executions": node_times,
    }


async def test_case_3():
    """测试案例 3：实战代码示例"""
    from app.graph import create_graph
    from app.state import AgentState
    
    logger.info("\n" + "="*60)
    logger.info("测试案例 3：实战代码示例")
    logger.info("="*60)
    
    app = create_graph(use_redis=False)
    
    test_input: AgentState = {
        "input": "如何用 FastAPI 实现 SSE 流式输出？",
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
        "thread_id": "test-case-3",
        "step_count": 0,
    }
    
    config = {"configurable": {"thread_id": "test-case-3"}}
    
    start_time = time.time()
    node_times = {}
    
    async for output in app.astream(test_input, config):
        for node_name in output.keys():
            node_times[node_name] = node_times.get(node_name, 0) + 1
            logger.info(f"  ✓ 节点 [{node_name}] 完成")
    
    total_time = time.time() - start_time
    
    final_state = await app.aget_state(config)
    answer = final_state.values.get("final_answer", "")
    
    # 检查是否包含代码示例
    has_code = "```" in answer or "def " in answer or "async def" in answer
    
    logger.success(f"\n✅ 测试完成，总耗时: {total_time:.2f}秒")
    logger.info(f"📝 答案长度: {len(answer)} 字符")
    logger.info(f"💻 包含代码: {'是' if has_code else '否'}")
    logger.info(f"🔄 重做次数: {final_state.values.get('revision_count', 0)}")
    
    return {
        "case": "实战代码示例",
        "question": test_input["input"],
        "total_time": round(total_time, 2),
        "answer_length": len(answer),
        "has_code": has_code,
        "revision_count": final_state.values.get("revision_count", 0),
        "node_executions": node_times,
    }


def generate_report(results):
    """生成测试报告"""
    logger.info("\n" + "="*60)
    logger.info("测试报告汇总")
    logger.info("="*60)
    
    total_time = sum(r["total_time"] for r in results)
    avg_time = total_time / len(results)
    
    logger.info(f"\n📊 总体统计:")
    logger.info(f"  测试案例数: {len(results)}")
    logger.info(f"  总耗时: {total_time:.2f}秒")
    logger.info(f"  平均耗时: {avg_time:.2f}秒")
    
    logger.info(f"\n📋 各案例详情:")
    for i, result in enumerate(results, 1):
        logger.info(f"\n  案例 {i}: {result['case']}")
        logger.info(f"    问题: {result['question']}")
        logger.info(f"    耗时: {result['total_time']}秒")
        logger.info(f"    答案长度: {result['answer_length']} 字符")
        logger.info(f"    重做次数: {result['revision_count']}")
        
        if "task_count" in result:
            logger.info(f"    任务拆解: {result['task_count']} 个")
        
        if "has_code" in result:
            logger.info(f"    包含代码: {'是' if result['has_code'] else '否'}")
    
    logger.info("\n" + "="*60)
    
    # 保存报告到文件
    report_path = Path("test_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_cases": len(results),
                "total_time": round(total_time, 2),
                "avg_time": round(avg_time, 2),
            },
            "cases": results,
        }, f, ensure_ascii=False, indent=2)
    
    logger.success(f"\n✅ 报告已保存到: {report_path}")


async def main():
    """运行所有测试"""
    logger.info("🧪 开始完整测试")
    
    results = []
    
    try:
        # 测试案例 1
        result1 = await test_case_1()
        results.append(result1)
        await asyncio.sleep(1)  # 避免 API 限流
        
        # 测试案例 2
        result2 = await test_case_2()
        results.append(result2)
        await asyncio.sleep(1)
        
        # 测试案例 3
        result3 = await test_case_3()
        results.append(result3)
        
        # 生成报告
        generate_report(results)
        
        logger.success("\n🎉 所有测试完成！")
        
    except Exception as e:
        logger.error(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

