# 敏感信息过滤功能文档

## 1. 功能概述

敏感信息过滤功能用于在 AI 回复内容中自动识别和脱敏敏感信息，包括：
- **手机号**：中国大陆手机号（11位，1开头）
- **邮箱**：标准邮箱地址格式

## 2. 架构设计

### 2.1 多层过滤策略

```
用户请求
    ↓
第一层：Prompt约束层（系统级指令，禁止输出敏感信息）
    ↓
第二层：LLM生成层（模型输出原始内容）
    ↓
第三层：后处理过滤层（核心拦截点 - SensitiveDataFilter）
    ↓
第四层：输出层（返回给用户）
```

### 2.2 核心组件

| 组件 | 文件位置 | 说明 |
|------|----------|------|
| 核心过滤器 | `app/utils/sensitive_data_filter.py` | 敏感信息识别和脱敏 |
| 流式过滤器 | `app/utils/sensitive_data_filter.py` | 处理流式输出的缓冲过滤 |
| 配置项 | `app/core/config.py` | 过滤开关和策略配置 |
| 集成点 | `app/services/chat_service.py` | 非流式/流式/Agent模式集成 |

## 3. 配置说明

### 3.1 环境变量

在 `.env` 文件中配置：

```bash
# 是否启用敏感信息过滤
ENABLE_SENSITIVE_DATA_FILTER=True

# 敏感信息过滤策略（full=完全替换, partial=部分脱敏, hash=哈希替换）
SENSITIVE_DATA_MASK_STRATEGY=full

# 是否过滤手机号
FILTER_MOBILE=True

# 是否过滤邮箱
FILTER_EMAIL=True
```

### 3.2 脱敏策略

| 策略 | 值 | 效果示例 |
|------|-----|----------|
| 完全替换 | `full` | `13812345678` → `[已隐藏手机号]` |
| 部分脱敏 | `partial` | `13812345678` → `138****5678` |
| 哈希替换 | `hash` | `13812345678` → `[手机号:1234]` |

## 4. 使用方式

### 4.1 基本使用

```python
from app.utils.sensitive_data_filter import get_filter

# 获取过滤器实例
filter_instance = get_filter()

# 过滤文本
text = "联系电话13812345678，邮箱test@example.com"
result, stats = filter_instance.filter_all(text)

print(result)  # 联系电话[已隐藏手机号]，邮箱[已隐藏邮箱]
print(stats)   # {MOBILE: 1, EMAIL: 1}
```

### 4.2 自定义配置

```python
from app.utils.sensitive_data_filter import (
    SensitiveDataFilter,
    MaskStrategy,
    SensitiveDataType
)

# 创建自定义过滤器
custom_filter = SensitiveDataFilter(
    mask_strategy=MaskStrategy.PARTIAL,
    enable_mobile_filter=True,
    enable_email_filter=True,
    custom_placeholder={
        SensitiveDataType.MOBILE: "***PHONE***",
        SensitiveDataType.EMAIL: "***EMAIL***"
    }
)
```

### 4.3 流式处理

```python
from app.utils.sensitive_data_filter import (
    SensitiveDataFilter,
    StreamingSensitiveFilter
)

# 创建流式过滤器
base_filter = SensitiveDataFilter()
streaming_filter = StreamingSensitiveFilter(base_filter, window_size=20)

# 处理流式数据
for chunk in stream_chunks():
    filtered = streaming_filter.process(chunk)
    if filtered:
        yield filtered

# 刷新剩余内容
remaining = streaming_filter.flush()
if remaining:
    yield remaining
```

## 5. API 参考

### 5.1 SensitiveDataFilter

```python
class SensitiveDataFilter:
    def __init__(
        self,
        mask_strategy: MaskStrategy = MaskStrategy.FULL,
        enable_mobile_filter: bool = True,
        enable_email_filter: bool = True,
        custom_placeholder: Optional[Dict[SensitiveDataType, str]] = None
    )
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| mask_strategy | MaskStrategy | FULL | 脱敏策略 |
| enable_mobile_filter | bool | True | 是否过滤手机号 |
| enable_email_filter | bool | True | 是否过滤邮箱 |
| custom_placeholder | Dict | None | 自定义占位符 |

### 5.2 方法

#### filter_mobile(text: str) -> Tuple[str, int]

过滤手机号。

| 参数 | 说明 |
|------|------|
| text | 待过滤文本 |
| 返回值 | (过滤后文本, 替换数量) |

#### filter_email(text: str) -> Tuple[str, int]

过滤邮箱地址。

| 参数 | 说明 |
|------|------|
| text | 待过滤文本 |
| 返回值 | (过滤后文本, 替换数量) |

#### filter_all(text: str) -> Tuple[str, Dict]

综合过滤所有敏感信息。

| 参数 | 说明 |
|------|------|
| text | 待过滤文本 |
| 返回值 | (过滤后文本, 统计字典) |

#### is_sensitive(text: str) -> bool

检测文本是否包含敏感信息。

| 参数 | 说明 |
|------|------|
| text | 待检测文本 |
| 返回值 | 是否包含敏感信息 |

### 5.3 StreamingSensitiveFilter

```python
class StreamingSensitiveFilter:
    def __init__(
        self,
        filter_instance: SensitiveDataFilter,
        window_size: int = 20
    )
```

| 参数 | 类型 | 说明 |
|------|------|------|
| filter_instance | SensitiveDataFilter | 基础过滤器实例 |
| window_size | int | 缓冲窗口大小（字符数） |

#### process(chunk: str) -> str

处理单个文本块。

#### flush() -> str

刷新缓冲区，输出剩余内容。

## 6. 测试

### 6.1 运行测试

```bash
cd code

# 运行基本测试
python run_test.py

# 运行覆盖率测试
python coverage_test.py
```

### 6.2 测试覆盖率

当前测试覆盖率：**96.4%**

测试用例包括：
- 各种脱敏策略（FULL/PARTIAL/HASH）
- 启用/禁用过滤
- 边界情况处理
- 流式处理
- 自定义占位符

## 7. 注意事项

1. **中文环境兼容**：邮箱正则表达式去除了 `\b` 边界，以兼容中文字符环境

2. **流式输出延迟**：使用流式缓冲方案会引入少量延迟（约 20 字符的缓冲窗口）

3. **姓名过滤**：当前版本不过滤姓名，如需开启请修改代码并添加相应的正则表达式

4. **配置热更新**：修改配置后需重启服务才能生效

## 8. 更新日志

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0.0 | 2026-01-22 | 初始版本，支持手机号和邮箱过滤 |
