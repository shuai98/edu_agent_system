"""
RAG 接口测试脚本
用于测试你的 RAG 系统接口格式
"""

import asyncio
import httpx
import json


async def test_rag_interface():
    """测试 RAG 接口"""
    
    rag_url = "http://localhost:8088/api/query"
    
    # 测试不同的请求格式
    test_cases = [
        {
            "name": "格式1：question + top_k",
            "data": {
                "question": "什么是 Python GIL？",
                "top_k": 3,
            }
        },
        {
            "name": "格式2：query",
            "data": {
                "query": "什么是 Python GIL？",
            }
        },
        {
            "name": "格式3：message",
            "data": {
                "message": "什么是 Python GIL？",
            }
        },
        {
            "name": "格式4：text",
            "data": {
                "text": "什么是 Python GIL？",
            }
        },
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for test in test_cases:
            print(f"\n{'='*60}")
            print(f"测试: {test['name']}")
            print(f"请求数据: {json.dumps(test['data'], ensure_ascii=False)}")
            print(f"{'='*60}")
            
            try:
                response = await client.post(
                    rag_url,
                    json=test['data'],
                    headers={"Content-Type": "application/json"}
                )
                
                print(f"状态码: {response.status_code}")
                print(f"响应头: {dict(response.headers)}")
                
                if response.status_code == 200:
                    print(f"✅ 成功！")
                    data = response.json()
                    print(f"响应数据: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
                    print(f"\n🎉 找到正确格式：{test['name']}")
                    return test['data'], data
                else:
                    print(f"❌ 失败: {response.status_code}")
                    print(f"响应内容: {response.text[:200]}")
                    
            except Exception as e:
                print(f"❌ 异常: {str(e)}")
    
    print(f"\n{'='*60}")
    print("所有格式都失败了，请检查：")
    print("1. RAG 服务是否正在运行？")
    print("2. 端口是否正确？(8088)")
    print("3. 接口路径是否正确？(/api/agent)")
    print(f"{'='*60}")


async def test_simple_get():
    """测试 GET 请求"""
    print(f"\n{'='*60}")
    print("测试 GET 请求（查看接口文档）")
    print(f"{'='*60}")
    
    urls = [
        "http://localhost:8088/",
        "http://localhost:8088/docs",
        "http://localhost:8088/api/agent",
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for url in urls:
            try:
                print(f"\n尝试访问: {url}")
                response = await client.get(url)
                print(f"状态码: {response.status_code}")
                if response.status_code == 200:
                    print(f"内容: {response.text[:200]}")
            except Exception as e:
                print(f"失败: {str(e)}")


if __name__ == "__main__":
    print("🔍 开始测试 RAG 接口...")
    print("请确保你的 RAG 服务已启动在 http://localhost:8088")
    
    asyncio.run(test_simple_get())
    asyncio.run(test_rag_interface())

