# Tests 目录说明

本目录包含所有测试文件和评测脚本。

---

## 📋 测试文件列表

### 基础测试

#### `test_simple.py` ⭐ 推荐先运行
- **用途**: 快速验证系统各模块是否正常工作
- **测试内容**:
  - LLM 连接测试
  - 搜索工具测试
  - 完整 Agent 工作流测试
- **运行**: `python tests/test_simple.py`
- **耗时**: 约 1-2 分钟

#### `test_complete.py`
- **用途**: 完整的端到端测试，包含多个测试案例
- **测试内容**:
  - 简单概念查询
  - 复杂主题学习
  - 实战代码示例
- **运行**: `python tests/test_complete.py`
- **耗时**: 约 5-10 分钟
- **输出**: 生成 `test_report.json`

---

## 🔬 评测实验

#### `evaluation_comparison.py` ⭐ 面试重点
- **用途**: 对比三种方案的效果
- **对比方案**:
  1. 直接 LLM 生成
  2. 简单 RAG 检索
  3. Agent 系统（完整工作流）
- **评估维度**:
  - 关键词覆盖率
  - 结构化程度
  - 代码示例
  - 响应时间
- **运行**: `python tests/evaluation_comparison.py`
- **耗时**: 约 10-15 分钟
- **输出**: 
  - `evaluation_report.json` - 详细数据
  - `evaluation_report.md` - Markdown 报告

---

## 🔧 RAG 相关测试

#### `test_rag_interface.py`
- **用途**: 测试 RAG 系统接口
- **运行**: `python tests/test_rag_interface.py`

#### `test_post_rag.py`
- **用途**: 测试 RAG POST 请求
- **运行**: `python tests/test_post_rag.py`

#### `test_your_rag.py`
- **用途**: 自定义 RAG 测试
- **运行**: `python tests/test_your_rag.py`

#### `find_rag_service.py`
- **用途**: 查找和验证 RAG 服务
- **运行**: `python tests/find_rag_service.py`

---

## 🚀 推荐测试流程

### 第一次使用
```bash
# 1. 基础测试（必须）
python tests/test_simple.py

# 2. 完整测试（建议）
python tests/test_complete.py
```

### 面试准备
```bash
# 运行评测对比实验
python tests/evaluation_comparison.py

# 查看生成的报告
cat evaluation_report.md
```

---

## 📊 测试报告说明

### test_report.json
```json
{
  "timestamp": "2024-03-09 10:30:00",
  "summary": {
    "total_cases": 3,
    "total_time": 25.5,
    "avg_time": 8.5
  },
  "cases": [...]
}
```

### evaluation_report.md
包含：
- 总体对比表格
- 各方案的平均指标
- 详细的测试结果

---

## ⚠️ 注意事项

1. **API 限流**: 评测实验会调用多次 API，注意限流
2. **网络连接**: 搜索工具需要网络连接
3. **RAG 服务**: 部分测试需要 RAG 服务运行
4. **环境变量**: 确保 `.env` 文件配置正确

---

## 🐛 常见问题

**Q: test_simple.py 失败怎么办？**
A: 检查环境变量配置，确保 DEEPSEEK_API_KEY 正确

**Q: 评测实验太慢？**
A: 可以减少测试问题数量，修改 `TEST_QUESTIONS` 列表

**Q: RAG 测试失败？**
A: 确保 RAG 服务正在运行，或跳过 RAG 相关测试

