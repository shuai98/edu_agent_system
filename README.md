# EduReflex - 多智能体协作学习系统

## 项目简介

EduReflex 是一个基于 **LangGraph 状态机** 的多智能体协作学习系统，实现了从"被动检索"到"主动导学"的升级。

### 核心特性

- 🧠 **多智能体协作**：Planner（规划者）+ Researcher（研究员）+ Critic（反思者）
- 🔄 **自我反思循环**：内容不合格自动重新生成，抑制幻觉
- 🔍 **跨源知识融合**：网络搜索 + RAG 系统联动
- 💾 **状态持久化**：Redis Checkpointer 支持断点续行
- ⚡ **流式输出**：SSE 实时推送思考过程
- 🎯 **异步高性能**：FastAPI + asyncio 并发处理

---

## 技术架构

```
用户请求
   ↓
FastAPI (异步 API)
   ↓
LangGraph 状态机
   ↓
┌─────────────────────────────────┐
│  Planner (规划任务)              │
│  ↓                               │
│  Researcher (调用工具获取知识)   │
│  ↓                               │
│  Critic (评估质量)               │
│  ↓                               │
│  合格? → 是 → 返回结果           │
│       → 否 → 回到 Researcher     │
└─────────────────────────────────┘
   ↓
Redis (状态持久化)
```

### 技术栈

- **核心框架**：LangGraph 0.2.45（状态机编排）
- **大模型**：DeepSeek-V3 / GPT-4o
- **后端**：FastAPI + Uvicorn（异步高性能）
- **持久化**：Redis（状态存储）
- **搜索工具**：DuckDuckGo（免费）/ Tavily（可选）
- **日志**：Loguru

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制模板文件并填入你的 API Key：

```bash
cp .env.template .env
```

编辑 `.env` 文件：

```env
# DeepSeek API（推荐：便宜且快）
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 模型配置
LLM_PROVIDER=deepseek
MODEL_NAME=deepseek-chat

# Redis（可选，不配置则使用内存模式）
REDIS_HOST=localhost
REDIS_PORT=6379

# RAG 系统接口（你的第一个项目）
RAG_API_URL=http://localhost:8000/api/query
```

### 3. 运行模式

#### 模式 1：启动 API 服务（推荐）

```bash
python main.py --mode api
```

访问 API 文档：http://localhost:8001/docs

#### 模式 2：命令行测试

```bash
python main.py --mode test
```

#### 模式 3：可视化图结构

```bash
python main.py --mode visualize
```

---

## API 使用示例

### 非流式请求

```bash
curl -X POST "http://localhost:8001/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "帮我掌握 Python 异步编程",
    "stream": false
  }'
```

### 流式请求（SSE）

```python
import requests

response = requests.post(
    "http://localhost:8001/api/query",
    json={"question": "帮我掌握 Python 异步编程", "stream": True},
    stream=True
)

for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
```

---

## 项目结构

```
EduReflex/
├── main.py                 # 主入口（支持多种运行模式）
├── requirements.txt        # 依赖清单
├── frontend_demo.html      # 前端演示页面
├── README.md              # 项目说明（本文件）
│
├── app/                   # 核心逻辑
│   ├── state.py           # 状态定义（Agent 的"记忆结构"）
│   ├── graph.py           # LangGraph 工作流组装
│   ├── nodes/             # 节点实现
│   │   ├── planner.py     # 规划者：拆解任务
│   │   ├── researcher.py  # 研究员：调用工具
│   │   └── critic.py      # 反思者：评估质量
│   ├── tools/             # 工具封装
│   │   └── search.py      # 搜索 + RAG 接口
│   └── utils/             # 工具函数
│       ├── monitor.py     # 性能监控
│       └── retry.py       # 重试机制
│
├── api/                   # FastAPI 服务
│   └── server.py          # HTTP 接口 + SSE 流式输出
│
├── tests/                 # 测试文件
│   ├── test_simple.py     # 基础测试（推荐先运行）
│   ├── test_complete.py   # 完整测试
│   └── evaluation_comparison.py  # 评测对比实验
│
├── docs/                  # 文档
│   ├── INDEX.md           # 文档索引（从这里开始）
│   ├── INTERVIEW_GUIDE.md # 面试准备手册
│   ├── INTERVIEW_CHECKLIST.md  # 面试检查清单
│   ├── IMPROVEMENTS_COMPLETED.md  # 改进说明
│   └── ...                # 其他文档
│
└── examples/              # 测试案例
    ├── test_case_1.md     # 简单概念查询案例
    └── test_case_2.md     # 复杂主题学习案例
```

> 💡 **提示**: 查看 `docs/INDEX.md` 获取完整的文档导航

---

## 核心设计亮点

### 1. 状态机 vs 简单链

传统 LangChain 的 Chain 是线性的：

```
输入 → LLM → 输出
```

LangGraph 的 Graph 支持循环和条件跳转：

```
输入 → Planner → Researcher → Critic
                     ↑            ↓
                     └─── 不合格 ──┘
```

### 2. 自我反思机制

Critic 节点会评估内容质量，如果不合格会触发 `revision_needed=True`，让 Researcher 重新生成。这是抑制 LLM 幻觉的有效手段。

### 3. 异步并发

Researcher 节点同时调用多个工具：

```python
results = await asyncio.gather(
    search_web(query),    # 网络搜索
    query_rag(query),     # RAG 系统
)
```

将串行 6 秒压缩到并行 3 秒。

### 4. 持久化与断点续行

使用 Redis Checkpointer，每个节点执行后自动保存状态。如果服务重启，可以通过 `thread_id` 恢复：

```python
config = {"configurable": {"thread_id": "user-123"}}
state = await graph_app.aget_state(config)
```

### 5. 流式输出

通过 SSE（Server-Sent Events）实时推送节点状态，前端可以显示：

```
🧠 正在规划任务...
🔍 正在搜索知识...
📚 正在整合内容...
🔎 正在审核质量...
✅ 完成！
```

---

## 面试要点总结

### 后端工程能力

1. **异步编程**：全链路 async/await，理解事件循环
2. **并发控制**：asyncio.gather 并发调用工具
3. **状态管理**：TypedDict + LangGraph 状态机
4. **持久化**：Redis Checkpointer 实现断点续行
5. **流式输出**：SSE 协议，提升用户体验

### Agent 核心概念

1. **工具调用（Tool Use）**：Agent 的核心能力
2. **自我反思（Self-Reflection）**：Critic 节点评估质量
3. **多体协同**：Planner + Researcher + Critic 分工协作
4. **条件路由**：根据状态动态决定下一步

### 系统架构思维

1. **微服务联动**：调用已有 RAG 系统，展示全局观
2. **降级策略**：RAG 失败自动切换到网络搜索
3. **防御性编程**：环境检查、异常处理、最大重试次数

---

## 下一步优化方向

1. **前端开发**：React + SSE 实现思考过程可视化
2. **长期记忆**：存储用户画像和学习偏好
3. **并发测试**：使用 Locust 压测多用户场景
4. **评测对比**：RAG vs Agent 的内容质量对比实验

---

## 常见问题

### Q1: 为什么选择 DeepSeek 而不是 OpenAI？

- **价格**：DeepSeek 便宜 10 倍以上
- **速度**：国内访问无需代理
- **能力**：DeepSeek-V3 在推理任务上接近 GPT-4

### Q2: Redis 是必须的吗？

不是。开发阶段可以用 `MemorySaver`（内存模式）。生产环境推荐 Redis，支持多实例共享状态。

### Q3: 如何防止 Agent 死循环？

我们设置了 `max_revisions=2`，最多重试 2 次。超过后强制通过。

### Q4: 搜索工具可以换吗？

可以。修改 `app/tools/search.py`，替换为 Tavily、Google Search 等。

---

## 开发者信息

- **学校**：西安电子科技大学
- **专业**：计算机科学与技术
- **项目定位**：毕业设计 + 求职作品集
- **技术亮点**：LangGraph 状态机 + 多智能体协作 + 异步高性能

---

## 许可证

MIT License

