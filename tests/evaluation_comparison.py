"""
评测对比实验 - Agent vs RAG vs 直接 LLM
==========================================

这个脚本会对比三种方案的效果：
1. 直接 LLM 生成
2. 简单 RAG 检索
3. Agent 系统（完整工作流）

评估维度：
- 内容完整性（是否覆盖核心知识点）
- 结构化程度（是否有清晰的章节）
- 响应时间（端到端延迟）
- 代码示例（是否包含可运行的代码）

使用方法：
python evaluation_comparison.py
"""

import asyncio
import time
import json
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv
from loguru import logger

load_dotenv()


# ===== 测试问题集 =====
TEST_QUESTIONS = [
    {
        "id": 1,
        "question": "什么是 Python 装饰器？",
        "category": "简单概念",
        "expected_keywords": ["装饰器", "函数", "语法糖", "@", "示例"],
    },
    {
        "id": 2,
        "question": "帮我掌握 Python 异步编程",
        "category": "复杂主题",
        "expected_keywords": ["asyncio", "协程", "事件循环", "async", "await", "并发"],
    },
    {
        "id": 3,
        "question": "如何用 FastAPI 实现 RESTful API？",
        "category": "实战应用",
        "expected_keywords": ["FastAPI", "路由", "请求", "响应", "代码示例"],
    },
    {
        "id": 4,
        "question": "解释 Python 的 GIL（全局解释器锁）",
        "category": "深度概念",
        "expected_keywords": ["GIL", "线程", "多进程", "性能", "限制"],
    },
    {
        "id": 5,
        "question": "如何优化 Python 程序的性能？",
        "category": "最佳实践",
        "expected_keywords": ["性能", "优化", "profiling", "缓存", "算法"],
    },
]


# ===== 方案 1：直接 LLM 生成 =====
async def test_direct_llm(question: str) -> Dict:
    """直接使用 LLM 生成答案"""
    from app.nodes.planner import get_llm
    
    logger.info(f"[直接 LLM] 测试问题: {question}")
    
    start_time = time.time()
    
    try:
        llm = get_llm()
        prompt = f"""请详细回答以下问题：

{question}

要求：
1. 内容完整，覆盖核心知识点
2. 结构清晰，有明确的章节
3. 包含代码示例（如果适用）
4. 适合学习和理解
"""
        
        response = await llm.ainvoke(prompt)
        answer = response.content
        
        elapsed = time.time() - start_time
        
        return {
            "method": "直接 LLM",
            "answer": answer,
            "time": round(elapsed, 2),
            "length": len(answer),
            "has_code": "```" in answer or "def " in answer,
        }
    
    except Exception as e:
        logger.error(f"[直接 LLM] 失败: {e}")
        return {
            "method": "直接 LLM",
            "answer": f"错误: {e}",
            "time": 0,
            "length": 0,
            "has_code": False,
        }


# ===== 方案 2：简单 RAG 检索 =====
async def test_simple_rag(question: str) -> Dict:
    """使用 RAG 系统检索并生成答案"""
    from app.tools.search import query_rag
    from app.nodes.planner import get_llm
    
    logger.info(f"[简单 RAG] 测试问题: {question}")
    
    start_time = time.time()
    
    try:
        # 1. 调用 RAG 检索
        rag_result = await query_rag(question)
        
        # 2. 使用 LLM 整合
        llm = get_llm()
        prompt = f"""基于以下检索结果，回答用户的问题：

【用户问题】
{question}

【检索结果】
{rag_result}

要求：
1. 基于检索结果生成答案
2. 结构清晰，有明确的章节
3. 包含代码示例（如果适用）
"""
        
        response = await llm.ainvoke(prompt)
        answer = response.content
        
        elapsed = time.time() - start_time
        
        return {
            "method": "简单 RAG",
            "answer": answer,
            "time": round(elapsed, 2),
            "length": len(answer),
            "has_code": "```" in answer or "def " in answer,
        }
    
    except Exception as e:
        logger.error(f"[简单 RAG] 失败: {e}")
        return {
            "method": "简单 RAG",
            "answer": f"错误: {e}",
            "time": 0,
            "length": 0,
            "has_code": False,
        }


# ===== 方案 3：Agent 系统 =====
async def test_agent_system(question: str) -> Dict:
    """使用完整的 Agent 系统"""
    from app.graph import create_graph
    from app.state import AgentState
    
    logger.info(f"[Agent 系统] 测试问题: {question}")
    
    start_time = time.time()
    
    try:
        app = create_graph(use_redis=False)
        
        test_input: AgentState = {
            "input": question,
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
            "thread_id": f"eval-{int(time.time())}",
            "step_count": 0,
        }
        
        config = {"configurable": {"thread_id": test_input["thread_id"]}}
        
        # 执行工作流
        async for output in app.astream(test_input, config):
            pass  # 只需要等待完成
        
        # 获取最终结果
        final_state = await app.aget_state(config)
        answer = final_state.values.get("final_answer", "")
        revision_count = final_state.values.get("revision_count", 0)
        
        elapsed = time.time() - start_time
        
        return {
            "method": "Agent 系统",
            "answer": answer,
            "time": round(elapsed, 2),
            "length": len(answer),
            "has_code": "```" in answer or "def " in answer,
            "revision_count": revision_count,
        }
    
    except Exception as e:
        logger.error(f"[Agent 系统] 失败: {e}")
        return {
            "method": "Agent 系统",
            "answer": f"错误: {e}",
            "time": 0,
            "length": 0,
            "has_code": False,
            "revision_count": 0,
        }


# ===== 评估指标 =====
def evaluate_answer(answer: str, expected_keywords: List[str]) -> Dict:
    """评估答案质量"""
    
    # 1. 关键词覆盖率
    keywords_found = sum(1 for kw in expected_keywords if kw.lower() in answer.lower())
    keyword_coverage = keywords_found / len(expected_keywords) if expected_keywords else 0
    
    # 2. 结构化程度（检查是否有标题、列表等）
    has_headers = "#" in answer or "##" in answer
    has_lists = "-" in answer or "*" in answer or "1." in answer
    structure_score = (int(has_headers) + int(has_lists)) / 2
    
    # 3. 代码示例
    has_code = "```" in answer or "def " in answer or "class " in answer
    
    # 4. 内容长度（字符数）
    length = len(answer)
    
    # 5. 综合评分（0-10）
    overall_score = (
        keyword_coverage * 4 +  # 关键词覆盖 40%
        structure_score * 3 +    # 结构化 30%
        (1 if has_code else 0) * 2 +  # 代码示例 20%
        min(length / 1000, 1) * 1  # 内容长度 10%
    )
    
    return {
        "keyword_coverage": round(keyword_coverage * 100, 1),
        "structure_score": round(structure_score * 100, 1),
        "has_code": has_code,
        "length": length,
        "overall_score": round(overall_score, 2),
    }


# ===== 运行对比实验 =====
async def run_comparison(question_data: Dict) -> Dict:
    """对单个问题运行三种方案的对比"""
    question = question_data["question"]
    expected_keywords = question_data["expected_keywords"]
    
    logger.info("\n" + "="*60)
    logger.info(f"测试问题 {question_data['id']}: {question}")
    logger.info(f"类别: {question_data['category']}")
    logger.info("="*60)
    
    results = []
    
    # 测试三种方案
    for test_func in [test_direct_llm, test_simple_rag, test_agent_system]:
        result = await test_func(question)
        
        # 评估答案质量
        if result["answer"] and not result["answer"].startswith("错误"):
            evaluation = evaluate_answer(result["answer"], expected_keywords)
            result.update(evaluation)
        else:
            result.update({
                "keyword_coverage": 0,
                "structure_score": 0,
                "overall_score": 0,
            })
        
        results.append(result)
        
        logger.info(f"\n[{result['method']}]")
        logger.info(f"  耗时: {result['time']}秒")
        logger.info(f"  长度: {result['length']} 字符")
        logger.info(f"  关键词覆盖: {result.get('keyword_coverage', 0)}%")
        logger.info(f"  结构化评分: {result.get('structure_score', 0)}%")
        logger.info(f"  综合评分: {result.get('overall_score', 0)}/10")
        
        # 避免 API 限流
        await asyncio.sleep(2)
    
    return {
        "question": question_data,
        "results": results,
    }


# ===== 生成对比报告 =====
def generate_report(all_results: List[Dict]):
    """生成详细的对比报告"""
    logger.info("\n" + "="*60)
    logger.info("评测对比报告")
    logger.info("="*60)
    
    # 统计各方案的平均指标
    methods = ["直接 LLM", "简单 RAG", "Agent 系统"]
    stats = {method: {
        "total_time": 0,
        "total_score": 0,
        "total_coverage": 0,
        "code_count": 0,
        "count": 0,
    } for method in methods}
    
    for result in all_results:
        for method_result in result["results"]:
            method = method_result["method"]
            stats[method]["total_time"] += method_result["time"]
            stats[method]["total_score"] += method_result.get("overall_score", 0)
            stats[method]["total_coverage"] += method_result.get("keyword_coverage", 0)
            stats[method]["code_count"] += int(method_result.get("has_code", False))
            stats[method]["count"] += 1
    
    # 打印汇总表格
    logger.info("\n📊 总体对比:")
    logger.info(f"{'方案':<15} {'平均耗时':<12} {'平均评分':<12} {'关键词覆盖':<12} {'代码示例率':<12}")
    logger.info("-" * 60)
    
    for method in methods:
        s = stats[method]
        count = s["count"] or 1
        avg_time = s["total_time"] / count
        avg_score = s["total_score"] / count
        avg_coverage = s["total_coverage"] / count
        code_rate = (s["code_count"] / count) * 100
        
        logger.info(
            f"{method:<15} "
            f"{avg_time:<12.2f} "
            f"{avg_score:<12.2f} "
            f"{avg_coverage:<12.1f}% "
            f"{code_rate:<12.1f}%"
        )
    
    # 保存详细报告
    report_path = Path("evaluation_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": stats,
            "details": all_results,
        }, f, ensure_ascii=False, indent=2)
    
    logger.success(f"\n✅ 详细报告已保存到: {report_path}")
    
    # 生成 Markdown 报告
    generate_markdown_report(all_results, stats)


def generate_markdown_report(all_results: List[Dict], stats: Dict):
    """生成 Markdown 格式的报告"""
    report_path = Path("evaluation_report.md")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Agent 系统评测对比报告\n\n")
        f.write(f"生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 总体对比\n\n")
        f.write("| 方案 | 平均耗时(s) | 平均评分(/10) | 关键词覆盖(%) | 代码示例率(%) |\n")
        f.write("|------|------------|--------------|--------------|-------------|\n")
        
        for method in ["直接 LLM", "简单 RAG", "Agent 系统"]:
            s = stats[method]
            count = s["count"] or 1
            f.write(
                f"| {method} | "
                f"{s['total_time']/count:.2f} | "
                f"{s['total_score']/count:.2f} | "
                f"{s['total_coverage']/count:.1f} | "
                f"{(s['code_count']/count)*100:.1f} |\n"
            )
        
        f.write("\n## 详细结果\n\n")
        
        for result in all_results:
            q = result["question"]
            f.write(f"### 问题 {q['id']}: {q['question']}\n\n")
            f.write(f"**类别**: {q['category']}\n\n")
            
            f.write("| 方案 | 耗时(s) | 评分 | 关键词覆盖 | 代码示例 |\n")
            f.write("|------|---------|------|-----------|----------|\n")
            
            for method_result in result["results"]:
                f.write(
                    f"| {method_result['method']} | "
                    f"{method_result['time']} | "
                    f"{method_result.get('overall_score', 0):.2f} | "
                    f"{method_result.get('keyword_coverage', 0):.1f}% | "
                    f"{'✅' if method_result.get('has_code') else '❌'} |\n"
                )
            
            f.write("\n")
    
    logger.success(f"✅ Markdown 报告已保存到: {report_path}")


# ===== 主函数 =====
async def main():
    """运行完整的评测对比实验"""
    logger.info("🧪 开始评测对比实验")
    logger.info(f"测试问题数: {len(TEST_QUESTIONS)}")
    
    all_results = []
    
    for question_data in TEST_QUESTIONS:
        try:
            result = await run_comparison(question_data)
            all_results.append(result)
        except Exception as e:
            logger.error(f"问题 {question_data['id']} 测试失败: {e}")
    
    # 生成报告
    generate_report(all_results)
    
    logger.success("\n🎉 评测对比实验完成！")


if __name__ == "__main__":
    asyncio.run(main())

