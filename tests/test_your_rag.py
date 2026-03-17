"""
直接测试你的 RAG 接口
"""

import asyncio
import httpx
import json


async def test_your_rag():
    """测试 http://127.0.0.1:8088/api/query"""
    
    url = "http://127.0.0.1:8088/api/query"
    
    # 测试不同的请求格式
    test_cases = [
        {
            "name": "格式1: question",
            "method": "POST",
            "data": {"question": "什么是Python？"}
        },
        {
            "name": "格式2: query",
            "method": "POST",
            "data": {"query": "什么是Python？"}
        },
        {
            "name": "格式3: message",
            "method": "POST",
            "data": {"message": "什么是Python？"}
        },
        {
            "name": "格式4: text",
            "method": "POST",
            "data": {"text": "什么是Python？"}
        },
        {
            "name": "格式5: GET 请求",
            "method": "GET",
            "data": None
        },
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for test in test_cases:
            print(f"\n{'='*60}")
            print(f"测试: {test['name']}")
            print(f"URL: {url}")
            if test['data']:
                print(f"数据: {json.dumps(test['data'], ensure_ascii=False)}")
            print(f"{'='*60}")
            
            try:
                if test['method'] == 'POST':
                    response = await client.post(
                        url,
                        json=test['data'],
                        headers={"Content-Type": "application/json"}
                    )
                else:
                    response = await client.get(url)
                
                print(f"状态码: {response.status_code}")
                print(f"响应头: {dict(response.headers)}")
                
                if response.status_code == 200:
                    print(f"✅ 成功！")
                    try:
                        data = response.json()
                        print(f"响应数据: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
                        print(f"\n🎉 找到正确格式：{test['name']}")
                        print(f"请求数据: {test['data']}")
                        return
                    except:
                        print(f"响应文本: {response.text[:200]}")
                else:
                    print(f"❌ 失败: {response.status_code}")
                    print(f"响应内容: {response.text[:500]}")
                    
            except Exception as e:
                print(f"❌ 异常: {str(e)}")
    
    print(f"\n{'='*60}")
    print("所有测试都失败了")
    print("请检查 RAG 服务是否真的在 8088 端口运行")
    print("尝试在浏览器访问: http://127.0.0.1:8088/docs")


if __name__ == "__main__":
    print("🔍 测试 RAG 接口: http://127.0.0.1:8088/api/query")
    asyncio.run(test_your_rag())


