# 🚀 EduReflex 快速启动指南

## 第一步：环境准备（5 分钟）

### 1. 检查 Python 版本
```bash
python --version
# 需要 Python 3.9 或更高版本
```

### 2. 创建虚拟环境（推荐）
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. 安装依赖
```bash
# 使用清华镜像（国内推荐）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或者使用默认源
pip install -r requirements.txt
```

## 第二步：配置 API Key（3 分钟）

### 1. 获取 DeepSeek API Key

访问：https://platform.deepseek.com/

- 注册账号（支持微信/手机号）
- 进入"API Keys"页面
- 点击"创建新密钥"
- 复制 API Key（格式：sk-xxxxxx）

### 2. 创建配置文件

**Windows:**
```bash
copy .env.template .env
notepad .env
```

**Linux/Mac:**
```bash
cp .env.template .env
nano .env
```

### 3. 填入配置

```env
# 必填项
DEEPSEEK_API_KEY=sk-你的密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 其他保持默认即可
LLM_PROVIDER=deepseek
MODEL_NAME=deepseek-chat
```

## 第三步：测试系统（2 分钟）

```bash
python test_simple.py
```

**预期输出：**
```
🧪 EduReflex 系统测试
============================================================
测试 1: LLM 连接
============================================================
✅ LLM 响应: Python 是一种高级编程语言...

============================================================
测试 2: 搜索工具
============================================================
✅ 搜索结果: 1. Python 异步编程...

============================================================
测试 3: 完整 Agent 工作流
============================================================
开始执行工作流...
  ✓ 节点 [planner] 完成
  ✓ 节点 [researcher] 完成
  ✓ 节点 [critic] 完成

✅ 工作流完成
📝 最终答案: 协程是 Python 异步编程的核心...

============================================================
测试总结
============================================================
通过: 3/3
🎉 所有测试通过！系统运行正常。
```

## 第四步：启动服务（1 分钟）

```bash
python main.py --mode api
```

**预期输出：**
```
🔍 检查环境配置...
✅ 环境配置检查通过
🚀 启动 API 服务: http://0.0.0.0:8001
📖 API 文档: http://0.0.0.0:8001/docs
✅ LangGraph 已加载
INFO:     Uvicorn running on http://0.0.0.0:8001
```

## 第五步：使用系统（3 种方式）

### 方式 1：Web 界面（最简单）

1. 保持服务运行
2. 双击打开 `frontend_demo.html`
3. 输入问题："帮我掌握 Python 异步编程"
4. 观察实时思考过程

### 方式 2：API 文档（推荐）

1. 浏览器访问：http://localhost:8001/docs
2. 找到 `POST /api/query` 接口
3. 点击"Try it out"
4. 填入请求体：
```json
{
  "question": "帮我掌握 Python 异步编程",
  "stream": false
}
```
5. 点击"Execute"

### 方式 3：命令行（开发者）

```bash
curl -X POST "http://localhost:8001/api/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "帮我掌握 Python 异步编程", "stream": false}'
```

## 常见问题排查

### ❌ 问题 1：提示"DEEPSEEK_API_KEY 未配置"

**原因：** .env 文件不存在或配置错误

**解决：**
```bash
# 检查文件是否存在
dir .env  # Windows
ls -la .env  # Linux/Mac

# 检查内容
type .env  # Windows
cat .env  # Linux/Mac

# 确保有这一行（替换为你的真实 Key）
DEEPSEEK_API_KEY=sk-xxxxxx
```

### ❌ 问题 2：搜索失败

**原因：** DuckDuckGo 可能被墙

**解决方案 1：** 使用代理
```bash
# Windows
set HTTP_PROXY=http://127.0.0.1:7890
set HTTPS_PROXY=http://127.0.0.1:7890

# Linux/Mac
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
```

**解决方案 2：** 暂时禁用搜索
修改 `app/nodes/researcher.py`，注释掉搜索部分，只使用 RAG。

### ❌ 问题 3：端口被占用

**错误信息：** `Address already in use`

**解决：**
```bash
# 方法 1：修改端口
# 编辑 .env 文件
API_PORT=8002

# 方法 2：杀掉占用进程（Windows）
netstat -ano | findstr :8001
taskkill /PID <进程ID> /F

# 方法 2：杀掉占用进程（Linux/Mac）
lsof -i :8001
kill -9 <进程ID>
```

### ❌ 问题 4：依赖安装失败

**错误信息：** `Could not find a version that satisfies...`

**解决：**
```bash
# 升级 pip
python -m pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 如果还是失败，逐个安装
pip install langgraph langchain fastapi uvicorn redis python-dotenv loguru
```

### ❌ 问题 5：Redis 连接失败

**错误信息：** `Connection refused`

**解决：** 系统会自动降级到内存模式，不影响使用。如果需要 Redis：

```bash
# Windows: 下载 Redis for Windows
# https://github.com/tporadowski/redis/releases

# Linux
sudo apt install redis-server
sudo systemctl start redis

# Mac
brew install redis
brew services start redis
```

## 进阶使用

### 1. 可视化图结构

```bash
python main.py --mode visualize
```

输出 Mermaid 格式的流程图，可以复制到 https://mermaid.live/ 查看。

### 2. 命令行测试模式

```bash
python main.py --mode test
```

直接在终端看到完整执行过程，适合调试。

### 3. 修改模型参数

编辑 `app/nodes/planner.py` 中的 `get_llm()` 函数：

```python
return ChatOpenAI(
    model="deepseek-chat",
    temperature=0.7,  # 调整创造性（0-1）
    max_tokens=2000,  # 调整输出长度
)
```

### 4. 调整重试次数

编辑 `app/nodes/critic.py`：

```python
max_revisions = 2  # 改为 3 或更多
```

## 下一步

### 学习路径

1. **理解状态机**：阅读 `app/state.py` 和 `app/graph.py`
2. **学习 Prompt 工程**：查看 `app/nodes/planner.py` 的提示词
3. **掌握异步编程**：研究 `app/nodes/researcher.py` 的并发逻辑
4. **理解流式输出**：分析 `api/server.py` 的 SSE 实现

### 扩展项目

1. **添加新节点**：比如"总结者"节点，生成学习大纲
2. **集成新工具**：比如 Wikipedia API、GitHub API
3. **优化 Prompt**：提高规划和评估的准确性
4. **开发前端**：使用 React 实现更好的交互

### 面试准备

1. 阅读 `INTERVIEW_GUIDE.md`（核心概念讲解）
2. 阅读 `ARCHITECTURE.md`（系统架构图）
3. 准备演示：能在 5 分钟内展示完整流程
4. 准备讲解：能清晰解释每个模块的作用

## 技术支持

### 文档索引

- `README.md` - 项目概述
- `INTERVIEW_GUIDE.md` - 面试准备（必读）
- `ARCHITECTURE.md` - 系统架构
- `USAGE.sh` - 使用命令速查

### 调试技巧

1. **查看日志**：终端会实时输出详细日志
2. **降低日志级别**：修改 `.env` 中的 `LOG_LEVEL=DEBUG`
3. **单步调试**：在 VSCode 中设置断点
4. **打印状态**：在节点函数中添加 `print(state)`

### 性能优化

1. **减少 LLM 调用**：缓存常见问题的答案
2. **并行执行**：在 Researcher 中同时调用更多工具
3. **结果截断**：限制搜索结果的长度，防止 Token 溢出

## 成功标志

✅ 测试全部通过  
✅ API 服务正常启动  
✅ 能够回答测试问题  
✅ 前端页面正常显示  
✅ 理解核心代码逻辑  

**恭喜！你已经成功搭建了一个完整的多智能体系统！** 🎉

现在你可以：
- 用它来辅助学习
- 作为毕业设计展示
- 在面试中演示
- 继续扩展功能

祝你在"金三银四"拿到理想的 Offer！💪

