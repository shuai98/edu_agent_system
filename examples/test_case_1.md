# 测试案例 1：简单概念查询

## 输入问题
```
什么是 Python 装饰器？
```

## 预期行为
- Planner 识别为简单概念，不需要复杂拆解
- Researcher 快速搜索并整合
- Critic 一次通过，无需重做

## 实际运行日志

### 1. Planner 节点
```json
{
  "goal": "理解 Python 装饰器",
  "tasks": [
    {
      "id": 1,
      "title": "装饰器基本概念",
      "description": "理解什么是装饰器，为什么需要装饰器",
      "search_query": "Python 装饰器 概念 作用"
    },
    {
      "id": 2,
      "title": "装饰器语法",
      "description": "学习 @ 语法和函数包装",
      "search_query": "Python 装饰器 语法 示例"
    },
    {
      "id": 3,
      "title": "实战应用",
      "description": "常见装饰器应用场景",
      "search_query": "Python 装饰器 应用场景 示例"
    }
  ]
}
```
**耗时**: 2.3 秒

### 2. Researcher 节点

**搜索关键词**: "Python 装饰器 概念 作用"

**网络搜索结果**:
```
装饰器是 Python 中的一种设计模式，用于在不修改原函数代码的情况下，
为函数添加额外功能。本质上是一个接受函数作为参数并返回新函数的高阶函数。

常见应用：
- 日志记录
- 性能测试
- 权限验证
- 缓存
```

**RAG 系统结果**:
```
装饰器（Decorator）是 Python 的语法糖，使用 @decorator_name 语法。

基本结构：
def my_decorator(func):
    def wrapper(*args, **kwargs):
        # 前置处理
        result = func(*args, **kwargs)
        # 后置处理
        return result
    return wrapper

@my_decorator
def my_function():
    pass
```

**整合后内容**:
```markdown
# Python 装饰器详解

## 什么是装饰器？

装饰器是 Python 中的一种设计模式，用于在不修改原函数代码的情况下，
为函数添加额外功能。本质上是一个接受函数作为参数并返回新函数的高阶函数。

## 基本语法

Python 使用 @ 符号作为装饰器的语法糖：

\`\`\`python
def my_decorator(func):
    def wrapper(*args, **kwargs):
        print("函数执行前")
        result = func(*args, **kwargs)
        print("函数执行后")
        return result
    return wrapper

@my_decorator
def say_hello():
    print("Hello!")

# 等价于：say_hello = my_decorator(say_hello)
\`\`\`

## 常见应用场景

1. **日志记录**：自动记录函数调用
2. **性能测试**：统计函数执行时间
3. **权限验证**：检查用户权限
4. **缓存**：缓存函数返回值

## 实战示例

\`\`\`python
import time
from functools import wraps

def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} 耗时: {end - start:.2f}秒")
        return result
    return wrapper

@timer
def slow_function():
    time.sleep(1)
    return "完成"
\`\`\`

## 关键要点

- 装饰器本质是闭包
- 使用 `@wraps` 保留原函数元信息
- 可以叠加多个装饰器
- 支持带参数的装饰器
```

**耗时**: 3.1 秒（并发执行）

### 3. Critic 节点

**评估结果**:
```
评分：9/10

问题：无

建议：内容完整，包含概念、语法、示例和应用场景。
代码示例清晰，适合初学者理解。

结论：通过
```

**耗时**: 1.8 秒

## 性能统计

| 节点 | 耗时 | 占比 |
|------|------|------|
| Planner | 2.3s | 31% |
| Researcher | 3.1s | 42% |
| Critic | 1.8s | 24% |
| **总计** | **7.2s** | **100%** |

## 关键指标

- ✅ 首字响应时间: 2.3 秒
- ✅ 端到端延迟: 7.2 秒
- ✅ 重做次数: 0
- ✅ 内容质量评分: 9/10

## 面试要点

1. **并发优化**: Researcher 同时调用搜索和 RAG，节省时间
2. **一次通过**: 简单问题无需重做，效率高
3. **内容质量**: 包含概念、语法、示例，结构清晰

