"""
性能监控模块
============

提供装饰器和工具函数，用于监控 Agent 节点的执行性能

面试话术：
"我实现了一个性能监控系统，可以追踪每个节点的执行时间。
这对于性能优化和问题排查非常重要。"
"""

import time
from functools import wraps
from typing import Dict, Any
from loguru import logger


def monitor_performance(node_name: str):
    """
    性能监控装饰器
    
    用法：
    @monitor_performance("planner")
    async def planner_node(state):
        ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(state, *args, **kwargs):
            start_time = time.time()
            logger.info(f"⏱️  [{node_name}] 开始执行")
            
            try:
                result = await func(state, *args, **kwargs)
                elapsed = time.time() - start_time
                
                logger.success(f"✅ [{node_name}] 完成，耗时 {elapsed:.2f}秒")
                
                # 将性能数据记录到状态中
                if "performance_metrics" not in result:
                    result["performance_metrics"] = {}
                
                result["performance_metrics"][node_name] = {
                    "duration": round(elapsed, 2),
                    "timestamp": time.time(),
                }
                
                return result
                
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"❌ [{node_name}] 失败，耗时 {elapsed:.2f}秒，错误: {e}")
                raise
                
        return wrapper
    return decorator


class PerformanceTracker:
    """
    性能追踪器
    
    用于统计整个会话的性能指标
    """
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {}
        self.start_time = time.time()
    
    def record_node(self, node_name: str, duration: float):
        """记录节点执行时间"""
        if node_name not in self.metrics:
            self.metrics[node_name] = []
        self.metrics[node_name].append(duration)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        total_time = time.time() - self.start_time
        
        summary = {
            "total_time": round(total_time, 2),
            "nodes": {},
        }
        
        for node_name, durations in self.metrics.items():
            summary["nodes"][node_name] = {
                "count": len(durations),
                "total": round(sum(durations), 2),
                "avg": round(sum(durations) / len(durations), 2),
                "min": round(min(durations), 2),
                "max": round(max(durations), 2),
            }
        
        return summary
    
    def print_summary(self):
        """打印性能摘要"""
        summary = self.get_summary()
        
        logger.info("=" * 60)
        logger.info("性能统计报告")
        logger.info("=" * 60)
        logger.info(f"总耗时: {summary['total_time']}秒")
        logger.info("")
        
        for node_name, stats in summary["nodes"].items():
            logger.info(f"[{node_name}]")
            logger.info(f"  执行次数: {stats['count']}")
            logger.info(f"  总耗时: {stats['total']}秒")
            logger.info(f"  平均: {stats['avg']}秒")
            logger.info(f"  最快: {stats['min']}秒")
            logger.info(f"  最慢: {stats['max']}秒")
            logger.info("")
        
        logger.info("=" * 60)

