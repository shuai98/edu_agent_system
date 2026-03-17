# 测试案例 2：复杂主题（展示规划能力）

## 输入问题
```
帮我掌握 Python 异步编程
```

## 预期行为
- Planner 拆解为 3-5 个循序渐进的子任务
- Researcher 针对每个子任务搜集知识
- 展示系统的任务规划和知识整合能力

## 实际运行日志

### 1. Planner 节点

**规划结果**:
```json
{
  "goal": "掌握 Python 异步编程",
  "tasks": [
    {
      "id": 1,
      "title": "理解异步编程概念",
      "description": "学习什么是协程、事件循环、并发与并行的区别",
      "search_query": "Python asyncio 协程 事件循环 概念"
    },
    {
      "id": 2,
      "title": "掌握 async/await 语法",
      "description": "学习如何定义和调用异步函数",
      "search_query": "Python async await 语法 用法"
    },
    {
      "id": 3,
      "title": "学习并发执行",
      "description": "使用 asyncio.gather 和 asyncio.create_task",
      "search_query": "Python asyncio.gather 并发执行"
    },
    {
      "id": 4,
      "title": "实战：异步 HTTP 请求",
      "description": "使用 aiohttp 实现并发请求",
      "search_query": "Python aiohttp 异步请求 示例"
    },
    {
      "id": 5,
      "title": "常见陷阱和最佳实践",
      "description": "避免阻塞事件循环，异常处理",
      "search_query": "Python asyncio 最佳实践 常见错误"
    }
  ]
}
```

**分析**:
- ✅ 任务循序渐进：概念 → 语法 → 并发 → 实战 → 最佳实践
- ✅ 搜索关键词精准，便于检索
- ✅ 覆盖理论和实践

**耗时**: 3.2 秒

### 2. Researcher 节点

**当前任务**: 任务 1 - 理解异步编程概念

**搜索关键词**: "Python asyncio 协程 事件循环 概念"

**网络搜索结果**:
```
异步编程是一种编程范式，允许程序在等待 I/O 操作时执行其他任务。

核心概念：
1. 协程（Coroutine）：可以暂停和恢复的函数
2. 事件循环（Event Loop）：调度和执行协程的核心
3. 并发 vs 并行：
   - 并发：单核 CPU 快速切换任务
   - 并行：多核 CPU 同时执行任务

Python 的 asyncio 库提供了完整的异步编程支持。
```

**RAG 系统结果**:
```
asyncio 是 Python 3.4+ 引入的异步 I/O 框架。

关键组件：
- async def：定义协程函数
- await：等待异步操作完成
- asyncio.run()：运行事件循环
- asyncio.gather()：并发执行多个协程

适用场景：
- 网络请求（爬虫、API 调用）
- 数据库查询
- 文件 I/O
- WebSocket 连接

不适用场景：
- CPU 密集型任务（应该用多进程）
```

**整合后内容**:
```markdown
# Python 异步编程完全指南

## 第一部分：核心概念

### 什么是异步编程？

异步编程是一种编程范式，允许程序在等待 I/O 操作（如网络请求、文件读写）时，
不阻塞主线程，而是去执行其他任务。这大幅提升了 I/O 密集型程序的效率。

### 核心概念

**1. 协程（Coroutine）**
- 可以暂停和恢复执行的函数
- 使用 `async def` 定义
- 比线程更轻量，可以创建成千上万个

**2. 事件循环（Event Loop）**
- asyncio 的核心，负责调度协程
- 类似于一个任务队列，不断取出任务执行
- 使用 `asyncio.run()` 启动

**3. 并发 vs 并行**
- **并发**：单核 CPU 快速切换任务，看起来像同时执行
- **并行**：多核 CPU 真正同时执行多个任务
- asyncio 实现的是并发，不是并行

### 适用场景

✅ **适合异步编程**：
- 网络请求（爬虫、API 调用）
- 数据库查询
- 文件 I/O
- WebSocket 长连接

❌ **不适合异步编程**：
- CPU 密集型任务（图像处理、科学计算）
- 应该用多进程（multiprocessing）

---

## 第二部分：async/await 语法

### 基本语法

\`\`\`python
import asyncio

# 定义异步函数
async def fetch_data():
    print("开始获取数据...")
    await asyncio.sleep(2)  # 模拟 I/O 操作
    print("数据获取完成")
    return "数据"

# 运行异步函数
result = asyncio.run(fetch_data())
\`\`\`

### 关键要点

1. **async def** 定义协程函数
2. **await** 只能在 async 函数内使用
3. **asyncio.run()** 是程序入口，只调用一次

---

## 第三部分：并发执行

### 使用 asyncio.gather

\`\`\`python
import asyncio
import time

async def task(name, delay):
    print(f"任务 {name} 开始")
    await asyncio.sleep(delay)
    print(f"任务 {name} 完成")
    return f"结果 {name}"

async def main():
    # 并发执行多个任务
    results = await asyncio.gather(
        task("A", 2),
        task("B", 1),
        task("C", 3),
    )
    print(f"所有结果: {results}")

# 运行
start = time.time()
asyncio.run(main())
print(f"总耗时: {time.time() - start:.1f}秒")  # 约 3 秒（不是 6 秒）
\`\`\`

**输出**:
```
任务 A 开始
任务 B 开始
任务 C 开始
任务 B 完成
任务 A 完成
任务 C 完成
所有结果: ['结果 A', '结果 B', '结果 C']
总耗时: 3.0秒
```

### 使用 asyncio.create_task

\`\`\`python
async def main():
    # 创建任务（立即开始执行）
    task1 = asyncio.create_task(task("A", 2))
    task2 = asyncio.create_task(task("B", 1))
    
    # 等待任务完成
    result1 = await task1
    result2 = await task2
\`\`\`

---

## 第四部分：实战 - 异步 HTTP 请求

### 使用 aiohttp

\`\`\`python
import aiohttp
import asyncio

async def fetch_url(session, url):
    async with session.get(url) as response:
        return await response.text()

async def main():
    urls = [
        "https://api.github.com/users/python",
        "https://api.github.com/users/microsoft",
        "https://api.github.com/users/google",
    ]
    
    async with aiohttp.ClientSession() as session:
        # 并发请求
        tasks = [fetch_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        
        for url, result in zip(urls, results):
            print(f"{url}: {len(result)} 字节")

asyncio.run(main())
\`\`\`

**性能对比**:
- 同步请求：3 个请求 × 1 秒 = 3 秒
- 异步请求：max(1, 1, 1) = 1 秒
- **提升 3 倍**

---

## 第五部分：常见陷阱和最佳实践

### ❌ 常见错误

**1. 在异步函数中使用阻塞操作**
\`\`\`python
async def bad_example():
    time.sleep(1)  # ❌ 阻塞整个事件循环
    await asyncio.sleep(1)  # ✅ 正确
\`\`\`

**2. 忘记 await**
\`\`\`python
async def bad_example():
    result = fetch_data()  # ❌ 返回协程对象，不是结果
    result = await fetch_data()  # ✅ 正确
\`\`\`

**3. 在同步代码中调用异步函数**
\`\`\`python
def sync_function():
    result = await async_function()  # ❌ SyntaxError
    result = asyncio.run(async_function())  # ✅ 正确
\`\`\`

### ✅ 最佳实践

1. **使用 asyncio.gather 处理异常**
\`\`\`python
results = await asyncio.gather(*tasks, return_exceptions=True)
for result in results:
    if isinstance(result, Exception):
        print(f"任务失败: {result}")
\`\`\`

2. **设置超时**
\`\`\`python
try:
    result = await asyncio.wait_for(slow_task(), timeout=5.0)
except asyncio.TimeoutError:
    print("任务超时")
\`\`\`

3. **优雅关闭**
\`\`\`python
async def main():
    try:
        await long_running_task()
    except KeyboardInterrupt:
        print("正在关闭...")
        # 清理资源
\`\`\`

---

## 总结

| 概念 | 说明 |
|------|------|
| async def | 定义协程函数 |
| await | 等待异步操作 |
| asyncio.run() | 运行事件循环 |
| asyncio.gather() | 并发执行 |
| aiohttp | 异步 HTTP 库 |

**学习路径**：
1. ✅ 理解协程和事件循环
2. ✅ 掌握 async/await 语法
3. ✅ 学会并发执行
4. ✅ 实战异步 HTTP 请求
5. ✅ 避免常见陷阱

**下一步**：
- 阅读 asyncio 官方文档
- 实现一个异步爬虫项目
- 学习 FastAPI（基于 asyncio 的 Web 框架）
```

**耗时**: 5.8 秒（并发执行）

### 3. Critic 节点

**评估结果**:
```
评分：10/10

问题：无

建议：内容非常完整，覆盖了从概念到实战的全部内容。
包含代码示例、性能对比、常见错误和最佳实践。
结构清晰，循序渐进，非常适合系统学习。

结论：通过
```

**耗时**: 2.1 秒

## 性能统计

| 节点 | 耗时 | 占比 |
|------|------|------|
| Planner | 3.2s | 29% |
| Researcher | 5.8s | 52% |
| Critic | 2.1s | 19% |
| **总计** | **11.1s** | **100%** |

## 关键指标

- ✅ 首字响应时间: 3.2 秒
- ✅ 端到端延迟: 11.1 秒
- ✅ 重做次数: 0
- ✅ 内容质量评分: 10/10
- ✅ 任务拆解数量: 5 个
- ✅ 内容字数: 约 2000 字

## 面试要点

1. **规划能力**: 将复杂主题拆解为 5 个循序渐进的子任务
2. **知识整合**: 融合网络搜索和 RAG 系统的结果
3. **内容质量**: 包含概念、语法、实战、最佳实践，结构完整
4. **性能优化**: 并发调用工具，节省时间

## 对比分析

| 方案 | 响应时间 | 内容完整性 | 结构化程度 |
|------|----------|------------|------------|
| 直接 LLM | 5s | ⭐⭐⭐ | ⭐⭐ |
| 简单 RAG | 8s | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Agent 系统** | **11s** | **⭐⭐⭐⭐⭐** | **⭐⭐⭐⭐⭐** |

**结论**: Agent 系统虽然耗时稍长，但内容质量和结构化程度显著提升。

