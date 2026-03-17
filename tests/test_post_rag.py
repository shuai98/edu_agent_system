"""
直接测试 POST 请求到你的 RAG
"""

import asyncio
import httpx
import json


async def test_post_to_rag():
    """测试 POST 到 http://127.0.0.1:8088/api/query"""
    
    url = "http://127.0.0.1:8088/api/query"
    
    data = {
        "question": "什么是Python？",
        "top_k": 3
    }
    
    print(f"🔍 测试 POST 请求")
    print(f"URL: {url}")
    print(f"数据: {json.dumps(data, ensure_ascii=False)}")
    print("="*60)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                print(f"✅ 成功！")
                result = response.json()
                print(f"\n响应数据:")
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"❌ 失败: {response.status_code}")
                print(f"响应内容: {response.text}")
                
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_post_to_rag())


