"""
快速诊断脚本 - 找出 RAG 服务的正确地址
"""

import asyncio
import httpx


async def find_rag_service():
    """尝试找到 RAG 服务"""
    
    # 常见端口
    ports = [8000, 8001, 8080, 8088, 5000, 3000]
    
    # 常见路径
    paths = [
        "/",
        "/docs",
        "/api/agent",
        "/api/query",
        "/agent",
        "/query",
        "/chat",
    ]
    
    print("🔍 开始扫描 RAG 服务...")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for port in ports:
            print(f"\n检查端口 {port}...")
            
            for path in paths:
                url = f"http://localhost:{port}{path}"
                try:
                    response = await client.get(url)
                    if response.status_code in [200, 405]:  # 405 表示方法不允许，但服务存在
                        print(f"  ✅ 找到服务: {url}")
                        print(f"     状态码: {response.status_code}")
                        if response.status_code == 200:
                            print(f"     内容: {response.text[:100]}")
                        
                        # 如果是文档页面，可能是正确的
                        if path == "/docs":
                            print(f"\n🎉 可能的正确地址:")
                            print(f"   基础 URL: http://localhost:{port}")
                            print(f"   文档地址: http://localhost:{port}/docs")
                            
                except httpx.ConnectError:
                    # 端口未开放，跳过
                    break
                except Exception as e:
                    pass
    
    print("\n" + "="*60)
    print("扫描完成！")
    print("\n💡 建议:")
    print("1. 查看你的 RAG 项目启动日志，找到实际端口")
    print("2. 访问 http://localhost:端口/docs 查看 API 文档")
    print("3. 在文档中找到正确的接口路径")


if __name__ == "__main__":
    asyncio.run(find_rag_service())


