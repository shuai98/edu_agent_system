# 文档索引
## EduReflex 项目文档导航

---

## 📚 快速开始

- **README.md** - 项目介绍和使用指南（从这里开始）
- **requirements.txt** - 依赖清单

---

## 🧪 测试文件（tests/）

### 基础测试
- `test_simple.py` - 简单功能测试（推荐先运行这个）
- `test_complete.py` - 完整工作流测试

### 评测实验
- `evaluation_comparison.py` - Agent vs RAG vs LLM 对比实验

### RAG 相关测试
- `test_rag_interface.py` - RAG 接口测试
- `test_post_rag.py` - RAG POST 请求测试
- `test_your_rag.py` - 自定义 RAG 测试
- `find_rag_service.py` - RAG 服务查找工具

---

## 📖 文档（docs/）

### 面试准备（重要！）
- `INTERVIEW_GUIDE.md` - 面试准备手册（必读）
- `INTERVIEW_CHECKLIST.md` - 面试前检查清单
- `RESUME_DESCRIPTION.md` - 简历项目描述模板

### 项目改进
- `IMPROVEMENTS_COMPLETED.md` - 已完成的改进说明
- `IMPROVEMENT_PLAN.md` - 完整改进方案
- `FINAL_SUMMARY.md` - 项目总结和面试要点

### 技术文档
- `ARCHITECTURE.md` - 系统架构说明
- `QUICKSTART.md` - 快速开始指南
- `PROJECT_CONSULTATION.md` - 项目咨询记录
- `TODO.md` - 待办事项

---

## 🎯 推荐阅读顺序

### 第一次使用
1. README.md - 了解项目
2. tests/test_simple.py - 运行测试
3. docs/QUICKSTART.md - 快速上手

### 面试准备
1. docs/INTERVIEW_GUIDE.md - 面试准备
2. docs/INTERVIEW_CHECKLIST.md - 检查清单
3. docs/IMPROVEMENTS_COMPLETED.md - 改进亮点
4. docs/RESUME_DESCRIPTION.md - 简历描述

### 深入理解
1. docs/ARCHITECTURE.md - 架构设计
2. docs/FINAL_SUMMARY.md - 技术总结
3. tests/evaluation_comparison.py - 评测实验

---

## 🚀 快速命令

```bash
# 运行基础测试
python tests/test_simple.py

# 运行完整测试
python tests/test_complete.py

# 运行评测对比
python tests/evaluation_comparison.py

# 启动服务
python main.py
```

---

## 📁 项目结构

```
edu_agent_system/
├── main.py                 # 主入口
├── requirements.txt        # 依赖
├── frontend_demo.html      # 前端页面
├── README.md              # 项目说明
│
├── app/                   # 核心代码
│   ├── nodes/            # Agent 节点
│   ├── tools/            # 工具模块
│   ├── utils/            # 工具函数
│   ├── graph.py          # 工作流
│   └── state.py          # 状态定义
│
├── api/                   # API 服务
│   └── server.py
│
├── tests/                 # 测试文件
│   ├── test_simple.py
│   ├── test_complete.py
│   └── evaluation_comparison.py
│
├── docs/                  # 文档
│   ├── INTERVIEW_GUIDE.md
│   ├── ARCHITECTURE.md
│   └── ...
│
└── examples/              # 测试案例
    ├── test_case_1.md
    └── test_case_2.md
```

