"""
搜索工具模块 - 封装外部知识获取能力
==========================================

面试重点：
1. 工具封装：将第三方 API 包装成统一接口
2. 异常处理：网络请求必须有超时和重试机制
3. 结果处理：搜索结果需要去重、截断，防止 Token 溢出

工程意义：
- 解耦：节点逻辑不直接依赖具体搜索引擎
- 可测试：可以 Mock 这些函数进行单元测试
- 可扩展：未来可以轻松替换为其他搜索 API
"""

import os
import httpx
from typing import List, Dict, Optional
from loguru import logger


async def search_web(query: str, max_results: int = 3) -> str:
    """
    网络搜索工具（使用 DuckDuckGo，免费无需 API Key）
    
    参数：
        query: 搜索关键词
        max_results: 返回结果数量
    
    返回：
        格式化的搜索结果摘要
    
    面试话术：
    "我们使用 DuckDuckGo 作为免费搜索方案，通过 duckduckgo-search 库。
    为了防止结果过长导致 Token 溢出，我们限制了返回条数并截断每条摘要。
    如果需要更高质量的结果，可以替换为 Tavily API。"
    """
    try:
        # 使用新包名 ddgs（原 duckduckgo-search）
        from ddgs import DDGS
        
        logger.info(f"🔍 开始搜索: {query}")
        
        # 使用同步 API
        ddgs = DDGS()
        results = list(ddgs.text(
            query, 
            max_results=max_results,
            region="wt-wt",  # 全球区域
        ))
        
        if not results:
            return f"未找到关于 '{query}' 的相关信息。"
        
        # 格式化结果
        formatted = []
        for i, result in enumerate(results, 1):
            title = result.get("title", "无标题")
            snippet = result.get("body", "")[:200]  # 截断到 200 字符
            url = result.get("href", "")
            formatted.append(f"{i}. {title}\n   {snippet}\n   来源: {url}")
        
        output = "\n\n".join(formatted)
        logger.success(f"✅ 搜索完成，返回 {len(results)} 条结果")
        return output
    
    except Exception as e:
        logger.error(f"❌ 搜索失败: {str(e)}")
        return f"搜索时发生错误: {str(e)}"


async def query_rag(question: str, top_k: int = 3) -> str:
    """
    调用 RAG 系统接口（你的第一个项目）
    
    参数：
        question: 用户问题
        top_k: 返回的文档数量
    
    返回：
        RAG 系统返回的权威知识
    
    面试话术：
    "这是我们系统的一大亮点：Agent 可以调用我之前开发的 RAG 测评系统。
    这展示了微服务架构的思想 - 新系统不是重复造轮，而是复用已有能力。
    我们使用 httpx 的异步客户端，确保不阻塞 Agent 的其他任务。"
    """
    rag_url = os.getenv("RAG_API_URL")
    
    # 如果没有配置 RAG_API_URL，直接返回
    if not rag_url:
        logger.debug("📚 RAG 系统未配置，跳过")
        return "RAG_NOT_CONFIGURED"
    
    rag_key = os.getenv("RAG_API_KEY", "")
    
    try:
        logger.info(f"📚 调用 RAG 系统: {question}")
        
        # 准备多种可能的请求格式
        request_formats = [
            {"question": question, "top_k": top_k},
            {"query": question},
            {"message": question},
            {"text": question},
        ]
        
        async with httpx.AsyncClient(timeout=10.0) as client:  # 缩短超时时间
            last_error = None
            
            for request_data in request_formats:
                try:
                    response = await client.post(
                        rag_url,
                        json=request_data,
                        headers={
                            "Authorization": f"Bearer {rag_key}" if rag_key else "",
                            "Content-Type": "application/json",
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        break
                    else:
                        last_error = f"状态码 {response.status_code}"
                        continue
                        
                except Exception as e:
                    last_error = str(e)
                    continue
            else:
                # 所有格式都失败了
                logger.warning(f"⚠️ RAG 系统不可用: {last_error}")
                return "RAG_UNAVAILABLE"
        
        # 解析响应（兼容多种格式）
        answer = (
            data.get("answer") or 
            data.get("response") or 
            data.get("result") or 
            data.get("output") or
            data.get("content") or
            ""
        )
        
        sources = data.get("sources", []) or data.get("references", []) or []
        
        if not answer:
            logger.warning(f"⚠️ RAG 返回格式异常: {str(data)[:200]}")
            return "RAG_INVALID_RESPONSE"
        
        # 格式化输出
        output = f"【权威知识】\n{answer}\n\n"
        if sources:
            output += "【参考来源】\n"
            for i, src in enumerate(sources[:3], 1):
                if isinstance(src, dict):
                    title = src.get('title') or src.get('source') or '未知来源'
                    output += f"{i}. {title}\n"
                else:
                    output += f"{i}. {src}\n"
        
        logger.success("✅ RAG 查询完成")
        return output
    
    except httpx.TimeoutException:
        logger.warning("⚠️ RAG 系统请求超时")
        return "RAG_TIMEOUT"
    except Exception as e:
        logger.warning(f"⚠️ RAG 调用失败: {str(e)}")
        return "RAG_ERROR"


async def search_with_fallback(query: str) -> str:
    """
    带降级策略的搜索（先 RAG，失败则用网络搜索）
    
    面试话术：
    "这是一个容错设计。我们优先使用内部 RAG（权威且快），
    如果失败或结果不足，自动降级到网络搜索。
    这种 Fallback 机制在生产环境中非常重要。"
    """
    # 先尝试 RAG
    rag_result = await query_rag(query)
    
    # 如果 RAG 返回特殊标记，说明失败了，降级到搜索
    if rag_result in ["RAG_NOT_CONFIGURED", "RAG_UNAVAILABLE", "RAG_TIMEOUT", "RAG_ERROR", "RAG_INVALID_RESPONSE"]:
        logger.debug("⚠️ RAG 不可用，使用网络搜索")
        return await search_web(query)
    
    return rag_result

