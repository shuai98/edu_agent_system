"""
重试机制模块
============

提供异步重试装饰器，用于处理网络请求等可能失败的操作

面试话术：
"我实现了指数退避重试机制，可以优雅地处理网络抖动等临时性故障。
这是生产环境中的最佳实践。"
"""

import asyncio
from functools import wraps
from typing import Callable, Type, Tuple
from loguru import logger


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    异步重试装饰器
    
    参数：
        max_attempts: 最大尝试次数
        delay: 初始延迟时间（秒）
        backoff: 退避倍数（指数退避）
        exceptions: 需要重试的异常类型
    
    用法：
    @async_retry(max_attempts=3, delay=1.0)
    async def fetch_data():
        ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        logger.error(
                            f"❌ {func.__name__} 失败，已重试 {max_attempts} 次: {e}"
                        )
                        raise
                    
                    wait_time = delay * (backoff ** (attempt - 1))
                    logger.warning(
                        f"⚠️  {func.__name__} 失败 (尝试 {attempt}/{max_attempts})，"
                        f"{wait_time:.1f}秒后重试: {e}"
                    )
                    
                    await asyncio.sleep(wait_time)
            
            # 理论上不会到这里，但为了类型检查
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


async def retry_with_fallback(
    primary_func: Callable,
    fallback_func: Callable,
    *args,
    **kwargs
):
    """
    带降级的重试
    
    先尝试主函数，失败后自动切换到备用函数
    
    用法：
    result = await retry_with_fallback(
        query_rag,
        search_web,
        query="Python asyncio"
    )
    """
    try:
        return await primary_func(*args, **kwargs)
    except Exception as e:
        logger.warning(f"⚠️  主函数失败，切换到备用方案: {e}")
        return await fallback_func(*args, **kwargs)

