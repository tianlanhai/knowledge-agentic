# 知识库智能体 - API 接口文档

## 1. 接口概述

帅哥，本项目 API 采用 RESTful 风格，基于 FastAPI 构建。所有接口默认返回 JSON 格式数据，遵循统一的错误处理规范，便于前端展示友好的错误提示。

### 1.1 接口设计原则

- **RESTful 风格**：遵循 REST 架构原则，使用标准的 HTTP 方法（GET、POST、DELETE）
- **统一响应格式**：所有接口返回统一的 JSON 格式，便于前端解析和展示
- **错误处理规范**：返回明确的错误码和错误信息，支持前端显示友好提示
- **响应式数据**：分页接口支持分页参数，便于前端实现虚拟滚动
- **数据冗余**：返回前端渲染所需的所有字段，减少额外请求

### 1.2 统一响应格式

**成功响应格式：**
```json
{
  "success": true,
  "data": {
    // 具体数据
  },
  "message": "操作成功"
}
```

**错误响应格式：**
```json
{
  "success": false,
  "error": {
    "code": 400,
    "message": "请求参数错误",
    "details": "file字段不能为空"
  }
}
```

### 1.3 HTTP 状态码

| 状态码 | 说明 | 前端处理建议 |
|-------|------|------------|
| 200 | 请求成功 | 显示成功提示，更新界面 |
| 400 | 请求参数错误 | 显示错误提示，高亮错误字段 |
| 404 | 资源不存在 | 显示"资源不存在"提示，返回上一页 |
| 500 | 服务器内部错误 | 显示"服务器错误，请稍后重试"提示 |

### 1.4 LLM模型提供商配置

帅哥，本项目支持多种LLM提供商，可通过配置文件灵活切换。

#### 1.4.1 支持的LLM提供商

| 提供商 | 类型 | 支持的模型 | 配置项 |
|-------|------|-----------|---------|
| **Ollama** | 本地 | deepseek-r1:8b, llama3, mistral等 | `LLM_PROVIDER=ollama` |
| **智谱AI** | 云端 | glm-4, glm-3-turbo, glm-4-flash | `LLM_PROVIDER=zhipuai` |
| **MiniMax** | 云端 | abab5.5-chat, abab5.5s-chat | `LLM_PROVIDER=minimax` |
| **月之暗面** | 云端 | moonshot-v1-8k, moonshot-v1-32k | `LLM_PROVIDER=moonshot` |

#### 1.4.2 配置方法

在 `.env` 文件中设置以下配置项：

```bash
# 选择LLM提供商（必填）
LLM_PROVIDER=ollama  # 可选：ollama, zhipuai, minimax, moonshot

# Ollama配置（本地模型）
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:8b

# 智谱AI配置（云端模型）
ZHIPUAI_API_KEY=your_api_key
ZHIPUAI_MODEL=glm-4

# MiniMax配置（云端模型）
MINIMAX_API_KEY=your_api_key
MINIMAX_GROUP_ID=your_group_id
MINIMAX_MODEL=abab5.5-chat

# 月之暗面配置（云端模型）
MOONSHOT_API_KEY=your_api_key
MOONSHOT_MODEL=moonshot-v1-8k

# ============================================================================
# 敏感信息过滤配置
# ============================================================================
# 是否启用敏感信息过滤
ENABLE_SENSITIVE_DATA_FILTER=True

# 敏感信息过滤策略（full=完全替换, partial=部分脱敏, hash=哈希替换）
SENSITIVE_DATA_MASK_STRATEGY=full

# 是否过滤手机号
FILTER_MOBILE=True

# 是否过滤邮箱
FILTER_EMAIL=True
```

#### 1.4.3 API密钥获取

- **智谱AI**：访问 https://open.bigmodel.cn/usercenter/apikeys
- **MiniMax**：访问 https://api.minimax.chat/document/guides/chat
- **月之暗面**：访问 https://platform.moonshot.cn/console/api-keys

#### 1.4.4 切换模型提供商

修改 `.env` 文件中的 `LLM_PROVIDER` 配置项，然后重启服务即可切换模型提供商。

#### 1.4.5 前端展示建议

- 在系统设置页面添加"模型提供商"选择下拉框
- 根据选择的提供商显示对应的配置项
- 验证API密钥有效性后保存配置
- 提示用户需要重启服务才能生效

## 2. 知识管理接口

### 2.1 上传并处理文件

- **接口地址**: `POST /v1/ingest/file`
- **功能**: 上传本地文件，解析内容并存入向量库
- **Content-Type**: `multipart/form-data`

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 | UI展示建议 |
|-------|------|------|------|------------|
| file | File | 是 | 上传的文件 | 文件上传组件，支持拖拽 |
| tags | List<String> | 否 | 文档标签 | 标签输入组件，标签式选择 |

**请求示例**：
```bash
curl -X POST "http://127.0.0.1:8010/v1/ingest/file" \
  -F "file=@document.pdf" \
  -F "tags=[\"技术文档\",\"API\"]"
```

**响应字段**：

| 字段名 | 类型 | 说明 | UI展示建议 |
|-------|------|------|------------|
| document_id | Integer | 文档唯一标识 | 文档列表中显示 |
| status | String | 处理状态（处理中/已完成/失败） | 状态标签，不同颜色区分 |
| chunk_count | Integer | 切分出的片段数量 | 文档详情中显示 |
| message | String | 提示信息 | 顶部消息提示 |

**响应示例**：
```json
{
  "success": true,
  "data": {
    "document_id": 123,
    "status": "completed",
    "chunk_count": 156,
    "file_name": "document.pdf",
    "tags": ["技术文档", "API"]
  },
  "message": "文件上传成功"
}
```

**UI处理建议**：
- 显示上传进度条（0-100%）
- 上传完成后显示成功提示（绿色消息）
- 自动刷新文档列表
- 错误时显示错误提示（红色消息）

### 2.2 抓取网页知识

- **接口地址**: `POST /v1/ingest/url`
- **功能**: 给定 URL，系统自动爬取正文并向量化
- **Content-Type**: `application/json`

**请求体**：

| 参数名 | 类型 | 必填 | 说明 | UI展示建议 |
|-------|------|------|------|------------|
| url | String | 是 | 网页 URL | URL输入框，带实时验证 |
| tags | List<String> | 否 | 文档标签 | 标签输入组件 |

**请求示例**：
```bash
curl -X POST "http://127.0.0.1:8010/v1/ingest/url" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/article",
    "tags": ["技术文章"]
  }'
```

**响应字段**：同文件上传

**响应示例**：
```json
{
  "success": true,
  "data": {
    "document_id": 124,
    "status": "completed",
    "chunk_count": 89,
    "file_name": "https://example.com/article",
    "url": "https://example.com/article",
    "tags": ["技术文章"]
  },
  "message": "网页抓取成功"
}
```

**UI处理建议**：
- URL格式实时验证
- 显示抓取进度（旋转动画）
- 抓取完成后显示网页标题和摘要预览
- 自动刷新文档列表

### 2.3 数据库同步知识

- **接口地址**: `POST /v1/ingest/db`
- **功能**: 从关系型数据库中同步结构化数据并向量化
- **Content-Type**: `application/json`

**请求体**：

| 参数名 | 类型 | 必填 | 说明 | UI展示建议 |
|-------|------|------|------|------------|
| connection_uri | String | 是 | 数据库连接串 | 输入框，带测试连接按钮 |
| table_name | String | 是 | 表名 | 下拉框，自动获取表列表 |
| content_column | String | 是 | 包含知识的列 | 下拉框，选择内容列 |
| metadata_columns | List<String> | 否 | 元数据列 | 多选框，标签式选择 |

**请求示例**：
```bash
curl -X POST "http://127.0.0.1:8010/v1/ingest/db" \
  -H "Content-Type: application/json" \
  -d '{
    "connection_uri": "sqlite:///data.db",
    "table_name": "documents",
    "content_column": "text",
    "metadata_columns": ["title", "author", "date"]
  }'
```

**响应字段**：同文件上传

**响应示例**：
```json
{
  "success": true,
  "data": {
    "document_id": 125,
    "status": "completed",
    "chunk_count": 234,
    "file_name": "database:documents",
    "tags": ["数据库"]
  },
  "message": "数据库同步成功"
}
```

**UI处理建议**：
- 测试连接按钮，实时反馈连接状态
- 表名下拉框，连接成功后自动加载表列表
- 列选择器，自动获取表的列信息
- 同步进度显示（进度条）

### 2.4 获取文档列表

- **接口地址**: `GET /v1/documents`
- **功能**: 分页查询已摄入的文档信息

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 | UI展示建议 |
|-------|------|------|------|------------|
| skip | Integer | 否 | 跳过数量，默认0 | 分页组件 |
| limit | Integer | 否 | 返回数量，默认10 | 每页显示数量选择器 |
| search | String | 否 | 搜索关键词 | 搜索框，实时搜索 |

**请求示例**：
```bash
curl "http://127.0.0.1:8010/v1/documents?skip=0&limit=10&search=技术"
```

**响应字段**：

| 字段名 | 类型 | 说明 | UI展示建议 |
|-------|------|------|------------|
| items | Array | 文档对象列表 | 表格或卡片列表 |
| total | Integer | 总数 | 分页器显示总数 |

**文档对象字段**：

| 字段名 | 类型 | 说明 | UI展示建议 |
|-------|------|------|------------|
| id | Integer | 文档ID | 点击查看详情 |
| file_name | String | 文件名 | 文件名列 |
| source_type | String | 来源类型（file/url/db） | 类型标签，不同颜色 |
| tags | List<String> | 标签列表 | 标签组，可点击筛选 |
| created_at | DateTime | 创建时间 | 时间列，显示相对时间 |
| chunk_count | Integer | 片段数量 | 数量列 |

**响应示例**：
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 123,
        "file_name": "document.pdf",
        "source_type": "file",
        "tags": ["技术文档", "API"],
        "created_at": "2026-01-11T10:00:00",
        "chunk_count": 156
      }
    ],
    "total": 123
  }
}
```

**UI处理建议**：
- 表格展示，支持排序
- 分页器，支持跳转
- 搜索框，实时搜索
- 操作按钮（删除、查看）
- 空状态提示（无数据时显示）

## 3. 任务管理接口

### 3.1 获取任务列表

- **接口地址**: `GET /v1/ingest/tasks`
- **功能**: 分页查询知识摄入任务列表
- **请求参数**：

| 参数名 | 类型 | 必填 | 说明 | UI展示建议 |
|-------|------|------|------|------------|
| skip | Integer | 否 | 跳过数量，默认0 | 分页组件 |
| limit | Integer | 否 | 返回数量，默认10 | 每页显示数量选择器 |

**响应示例**：
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "file_name": "document.pdf",
        "status": "processing",
        "progress": 45,
        "error_message": null,
        "document_id": null,
        "created_at": "2026-01-11T10:00:00",
        "updated_at": "2026-01-11T10:05:00"
      }
    ],
    "total": 10
  }
}
```

**任务状态说明**：
- `pending`: 等待处理
- `processing`: 处理中
- `completed`: 已完成
- `failed`: 失败

### 3.2 获取任务详情

- **接口地址**: `GET /v1/ingest/tasks/{task_id}`
- **功能**: 获取指定任务的详细信息和处理进度

**响应示例**：
```json
{
  "success": true,
  "data": {
    "id": 1,
    "file_name": "document.pdf",
    "status": "completed",
    "progress": 100,
    "error_message": null,
    "document_id": 123,
    "created_at": "2026-01-11T10:00:00",
    "updated_at": "2026-01-11T10:02:00"
  }
}
```

### 3.3 删除任务

- **接口地址**: `DELETE /v1/ingest/tasks/{task_id}`
- **功能**: 删除指定任务记录（不影响已生成的文档）

**响应示例**：
```json
{
  "success": true,
  "data": {"task_id": 1},
  "message": "任务 1 已成功删除"
}
```

## 4. 对话持久化接口

### 4.1 创建会话

- **接口地址**: `POST /v1/conversations`
- **功能**: 创建新的对话会话
- **Content-Type**: `application/json`

**请求体**：

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| title | String | 否 | 会话标题 |
| model | String | 否 | 使用的模型名称 |

**响应示例**：
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "新建对话",
    "model": "deepseek-r1:8b",
    "created_at": "2026-01-11T10:00:00"
  },
  "message": "会话创建成功"
}
```

### 4.2 获取会话列表

- **接口地址**: `GET /v1/conversations`
- **功能**: 分页获取对话会话列表

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| skip | Integer | 否 | 跳过数量，默认0 |
| limit | Integer | 否 | 返回数量，默认20 |

**响应示例**：
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "title": "关于AI的讨论",
        "message_count": 5,
        "created_at": "2026-01-11T10:00:00",
        "updated_at": "2026-01-11T10:30:00"
      }
    ],
    "total": 25
  }
}
```

### 4.3 获取会话详情

- **接口地址**: `GET /v1/conversations/{conversation_id}`
- **功能**: 获取会话详情及完整消息列表

**响应示例**：
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "关于AI的讨论",
    "model": "deepseek-r1:8b",
    "messages": [
      {
        "id": 1,
        "role": "user",
        "content": "你好",
        "created_at": "2026-01-11T10:00:00"
      },
      {
        "id": 2,
        "role": "assistant",
        "content": "你好！有什么可以帮助你的吗？",
        "created_at": "2026-01-11T10:00:05"
      }
    ],
    "created_at": "2026-01-11T10:00:00",
    "updated_at": "2026-01-11T10:30:00"
  }
}
```

### 4.4 更新会话

- **接口地址**: `PUT /v1/conversations/{conversation_id}`
- **功能**: 更新会话标题等信息

**请求体**：

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| title | String | 否 | 新的会话标题 |

**响应示例**：
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "新标题",
    "updated_at": "2026-01-11T11:00:00"
  },
  "message": "会话更新成功"
}
```

### 4.5 删除会话

- **接口地址**: `DELETE /v1/conversations/{conversation_id}`
- **功能**: 删除会话及其所有消息

**响应示例**：
```json
{
  "success": true,
  "data": {"deleted": true},
  "message": "会话删除成功"
}
```

### 4.6 发送消息（非流式）

- **接口地址**: `POST /v1/conversations/{conversation_id}/messages`
- **功能**: 向会话发送消息并获取AI回复（非流式）
- **Content-Type**: `application/json`

**请求体**：

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| content | String | 是 | 消息内容 |
| stream | Boolean | 否 | 是否流式，此处必须为false |
| use_agent | Boolean | 否 | 是否启用智能体模式 |

**响应示例**：
```json
{
  "success": true,
  "data": {
    "id": 3,
    "role": "assistant",
    "content": "这是AI的回答内容...",
    "sources": [...],
    "token_usage": {
      "prompt_tokens": 50,
      "completion_tokens": 100,
      "total_tokens": 150
    }
  },
  "message": "消息发送成功"
}
```

### 4.7 发送消息（流式）

- **接口地址**: `POST /v1/conversations/{conversation_id}/stream`
- **功能**: 向会话发送消息并获取AI回复（SSE流式）
- **Content-Type**: `text/event-stream`

**请求体**：同4.6，但`stream`建议为true

**流式响应格式**：
```
data: {"content": "这是"}
data: {"content": "AI的"}
data: {"content": "回答"}
data: {"done": true, "sources": [...]}
```

### 4.8 获取会话消息列表

- **接口地址**: `GET /v1/conversations/{conversation_id}/messages`
- **功能**: 分页获取会话的消息列表

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| skip | Integer | 否 | 跳过数量，默认0 |
| limit | Integer | 否 | 返回数量，默认50 |

**响应示例**：
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "role": "user",
        "content": "你好",
        "created_at": "2026-01-11T10:00:00"
      }
    ],
    "total": 10
  }
}
```

## 5. 模型配置接口

### 5.1 获取LLM配置列表

- **接口地址**: `GET /v1/model-config/llm`
- **功能**: 获取所有LLM模型配置及当前默认配置

**响应示例**：
```json
{
  "success": true,
  "data": {
    "configs": [
      {
        "id": "ollama-deepseek-r1-8b",
        "provider_id": "ollama",
        "provider_name": "Ollama",
        "model_name": "deepseek-r1:8b",
        "api_key": null,
        "endpoint": "http://localhost:11434",
        "is_default": true
      }
    ],
    "default_config_id": "ollama-deepseek-r1-8b"
  }
}
```

### 5.2 保存LLM配置

- **接口地址**: `POST /v1/model-config/llm`
- **功能**: 保存或更新LLM模型配置

**请求体**：

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| provider_id | String | 是 | 提供商ID（ollama/zhipuai/openai等） |
| provider_name | String | 是 | 提供商名称 |
| model_name | String | 是 | 模型名称 |
| api_key | String | 否 | API密钥（云端模型需要） |
| endpoint | String | 否 | 自定义API端点 |

**响应示例**：
```json
{
  "success": true,
  "data": {
    "id": "openai-gpt-4",
    "provider_id": "openai",
    "model_name": "gpt-4",
    ...
  },
  "message": "配置已保存"
}
```

### 5.3 设置默认LLM配置

- **接口地址**: `POST /v1/model-config/llm/{config_id}/set-default`
- **功能**: 设置默认LLM模型（触发热切换）

**响应示例**：
```json
{
  "success": true,
  "data": {...},
  "message": "默认模型已切换，配置已生效"
}
```

### 5.4 删除LLM配置

- **接口地址**: `DELETE /v1/model-config/llm/{config_id}`
- **功能**: 删除指定的LLM配置（不能删除默认配置）

**响应示例**：
```json
{
  "success": true,
  "data": {"deleted": true},
  "message": "配置已删除"
}
```

### 5.5 获取Embedding配置列表

- **接口地址**: `GET /v1/model-config/embedding`
- **功能**: 获取所有Embedding配置

**响应示例**：
```json
{
  "success": true,
  "data": {
    "configs": [
      {
        "id": "zhipuai-embedding",
        "provider_id": "zhipuai",
        "provider_name": "智谱AI",
        "model_name": "embedding-3",
        "is_default": true
      }
    ],
    "default_config_id": "zhipuai-embedding"
  }
}
```

### 5.6 保存Embedding配置

- **接口地址**: `POST /v1/model-config/embedding`
- **功能**: 保存或更新Embedding配置

**请求体**：

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| provider_id | String | 是 | 提供商ID |
| provider_name | String | 是 | 提供商名称 |
| model_name | String | 是 | 模型名称 |
| api_key | String | 否 | API密钥 |

### 5.7 设置默认Embedding配置

- **接口地址**: `POST /v1/model-config/embedding/{config_id}/set-default`

### 5.8 获取提供商列表

- **接口地址**: `GET /v1/model-config/providers`
- **功能**: 获取所有支持的LLM和Embedding提供商信息

**响应示例**：
```json
{
  "success": true,
  "data": {
    "llm_providers": [
      {
        "value": "ollama",
        "label": "Ollama",
        "default_endpoint": "http://localhost:11434",
        "default_models": ["deepseek-r1:8b", "llama3"],
        "type": "local"
      },
      {
        "value": "zhipuai",
        "label": "智谱AI",
        "default_endpoint": "https://open.bigmodel.cn/api/paas/v4",
        "default_models": ["glm-4", "glm-3-turbo"],
        "type": "cloud"
      }
    ],
    "embedding_providers": [
      {
        "value": "zhipuai",
        "label": "智谱AI",
        "default_models": ["embedding-3"],
        "type": "cloud"
      }
    ]
  }
}
```

### 5.9 获取Ollama模型列表

- **接口地址**: `GET /v1/model-config/ollama/models`
- **功能**: 获取Ollama服务中可用的模型列表

**响应示例**：
```json
{
  "success": true,
  "data": {
    "models": [
      {
        "name": "deepseek-r1:8b",
        "size": 4922101140,
        "modified_at": "2026-01-01T00:00:00"
      }
    ]
  }
}
```

### 5.10 拉取Ollama模型

- **接口地址**: `POST /v1/model-config/ollama/pull`
- **功能**: 从Ollama仓库拉取指定模型

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| model_name | String | 是 | 模型名称（如llama3:8b） |

**响应示例**：
```json
{
  "success": true,
  "data": {"model_name": "llama3:8b"},
  "message": "模型 llama3:8b 拉取成功"
}
```

### 5.11 验证配置

- **接口地址**: `POST /v1/model-config/validate`
- **功能**: 验证模型配置的有效性

**请求体**：同5.2保存配置的请求体

**响应示例**：
```json
{
  "success": true,
  "data": {"valid": true},
  "message": "配置验证通过"
}
```

### 5.12 删除Embedding配置

- **接口地址**: `DELETE /v1/model-config/embedding/{config_id}`
- **功能**: 删除指定的Embedding配置（不能删除默认配置）

**响应示例**：
```json
{
  "success": true,
  "data": {"deleted": true},
  "message": "配置已删除"
}
```

### 5.13 测试LLM连接

- **接口地址**: `POST /v1/model-config/llm/test`
- **功能**: 测试LLM配置的连接状态和可用性

**请求体**：

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| provider_id | String | 是 | 提供商ID（ollama/zhipuai/openai等） |
| endpoint | String | 是 | API端点地址 |
| api_key | String | 否 | API密钥 |
| model_name | String | 是 | 模型名称 |

**响应示例**：
```json
{
  "success": true,
  "data": {
    "success": true,
    "provider_id": "zhipuai",
    "latency_ms": 150,
    "message": "连接成功",
    "models": ["glm-4", "glm-3-turbo"]
  },
  "message": "测试完成"
}
```

**错误响应示例**：
```json
{
  "success": true,
  "data": {
    "success": false,
    "provider_id": "zhipuai",
    "message": "连接失败：API密钥无效",
    "error": "invalid_api_key"
  },
  "message": "测试完成"
}
```

### 5.14 测试Embedding连接

- **接口地址**: `POST /v1/model-config/embedding/test`
- **功能**: 测试Embedding配置的连接状态和可用性

**请求体**：

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| provider_id | String | 是 | 提供商ID |
| endpoint | String | 否 | API端点地址 |
| api_key | String | 否 | API密钥 |
| model_name | String | 是 | 模型名称 |
| device | String | 否 | 运行设备（cpu/cuda/auto），仅本地embedding |

**响应示例**：
```json
{
  "success": true,
  "data": {
    "success": true,
    "provider_id": "zhipuai",
    "latency_ms": 200,
    "message": "连接成功"
  },
  "message": "测试完成"
}
```

## 6. 版本信息接口

### 6.1 获取版本信息

- **接口地址**: `GET /v1/version/info`
- **功能**: 获取当前镜像版本的能力信息

**响应示例**：
```json
{
  "success": true,
  "data": {
    "version": "v1",
    "description": "云LLM + 本地向量",
    "llm_type": "cloud",
    "embedding_type": "local",
    "supported_llm_providers": ["zhipuai", "openai", "minimax", "moonshot"],
    "supported_embedding_providers": ["local"],
    "is_cloud_llm": true,
    "is_local_llm": false
  }
}
```

### 6.2 获取所有版本能力

- **接口地址**: `GET /v1/version/capabilities`
- **功能**: 获取所有镜像版本的能力对比信息

**响应示例**：
```json
{
  "success": true,
  "data": {
    "current_version": "v1",
    "all_versions": {
      "v1": {
        "description": "云LLM + 本地向量",
        "llm_type": "cloud",
        "embedding_type": "local"
      },
      "v2": {
        "description": "云LLM + 云端向量",
        "llm_type": "cloud",
        "embedding_type": "cloud"
      }
    }
  }
}
```

### 6.3 验证配置兼容性

- **接口地址**: `GET /v1/version/validate`
- **功能**: 验证配置是否与当前镜像版本兼容

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| llm_provider | String | 否 | LLM提供商名称 |
| embedding_provider | String | 否 | Embedding提供商名称 |

**响应示例**：
```json
{
  "success": true,
  "data": {
    "valid": true,
    "message": "配置与当前镜像版本兼容",
    "current_version": "v1"
  }
}
```

## 7. 对话与检索接口

### 7.1 智能问答

- **接口地址**: `POST /v1/chat/completions`
- **功能**: 基于知识库进行对话，支持流式和非流式返回
- **Content-Type**: `application/json` 或 `text/event-stream`

**请求体**：

| 参数名 | 类型 | 必填 | 说明 | UI展示建议 |
|-------|------|------|------|------------|
| message | String | 是 | 用户当前输入 | 输入框，支持多行 |
| history | List<Message> | 否 | 对话历史列表 | 内部管理，自动传递 |
| use_agent | Boolean | 否 | 是否启用智能体模式 | Toggle开关 |
| stream | Boolean | 否 | 是否启用流式返回 | Toggle开关（可选） |

**Message对象字段**：

| 字段名 | 类型 | 说明 |
|-------|------|------|
| role | String | 角色（user/assistant） |
| content | String | 消息内容 |

**请求示例**（非流式）：
```bash
curl -X POST "http://127.0.0.1:8010/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "如何使用这个系统？",
    "history": [
      {"role": "user", "content": "你好"},
      {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"}
    ],
    "use_agent": true,
    "stream": false
  }'
```

**响应字段**：

| 字段名 | 类型 | 说明 | UI展示建议 |
|-------|------|------|------------|
| answer | String | 模型生成的回答内容（已过滤敏感信息） | AI消息气泡，支持Markdown |
| sources | List<Source> | 引用来源列表 | 折叠面板，可展开查看 |
| is_complete | Boolean | 回答是否完成 | 非流式时为true |
| filtered_count | Object | 敏感信息过滤统计（可选） | 显示过滤数量 |

**Source对象字段**：

| 字段名 | 类型 | 说明 | UI展示建议 |
|-------|------|------|------------|
| doc_id | Integer | 文档ID | 点击跳转文档详情 |
| file_name | String | 文档名称 | 文档名称链接 |
| content | String | 片段内容 | 片段预览，高亮关键词 |
| score | Float | 相似度评分 | 进度条显示相关度 |

**响应示例**（非流式）：
```json
{
  "success": true,
  "data": {
    "answer": "这是一个知识库智能体系统，您可以上传文档、网页或数据库，然后进行智能问答和文档分析。",
    "sources": [
      {
        "doc_id": 123,
        "file_name": "使用指南.pdf",
        "content": "系统支持多种数据源，包括PDF、Markdown、Word等文档格式...",
        "score": 0.95
      }
    ],
    "is_complete": true
  }
}
```

**流式响应格式**：
```
data: {"content": "这是"}
data: {"content": "一个"}
data: {"content": "知识库"}
data: {"content": "..."}
data: {"done": true}
```

**UI处理建议**：
- 用户消息立即显示（靠右）
- AI消息流式显示（打字机效果，靠左）
- 来源引用折叠显示在AI消息下方
- 智能体模式开关，状态可视化
- 流式结束显示"完成"标识

### 7.2 智能总结

- **接口地址**: `POST /v1/chat/summary`
- **功能**: 对指定文档进行智能总结
- **Content-Type**: `application/json`

**请求体**：

| 参数名 | 类型 | 必填 | 说明 | UI展示建议 |
|-------|------|------|------|------------|
| doc_id | Integer | 是 | 文档ID | 文档选择下拉框 |

**请求示例**：
```bash
curl -X POST "http://127.0.0.1:8010/v1/chat/summary" \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": 123
  }'
```

**响应字段**：

| 字段名 | 类型 | 说明 | UI展示建议 |
|-------|------|------|------------|
| result | String | 总结内容 | 卡片展示，支持复制 |

**响应示例**：
```json
{
  "success": true,
  "data": {
    "result": "本文档介绍了知识库智能体系统的使用方法，包括文档上传、智能问答、文档分析等功能。"
  }
}
```

**UI处理建议**：
- 显示处理进度（旋转图标）
- 结果卡片展示（玻璃态效果）
- 复制按钮（点击复制到剪贴板）
- 成功提示

### 7.3 文档对比

- **接口地址**: `POST /v1/chat/compare`
- **功能**: 对多个指定文档进行对比分析
- **Content-Type**: `application/json`

**请求体**：

| 参数名 | 类型 | 必填 | 说明 | UI展示建议 |
|-------|------|------|------|------------|
| doc_ids | List<Integer> | 是 | 文档ID列表（2-5个） | 文档多选框 |

**请求示例**：
```bash
curl -X POST "http://127.0.0.1:8010/v1/chat/compare" \
  -H "Content-Type: application/json" \
  -d '{
    "doc_ids": [123, 124, 125]
  }'
```

**响应字段**：

| 字段名 | 类型 | 说明 | UI展示建议 |
|-------|------|------|------------|
| result | String | 对比分析内容 | Bento Grid卡片展示 |

**响应示例**：
```json
{
  "success": true,
  "data": {
    "result": "文档1和文档2都介绍了AI系统，但文档1更侧重于技术实现，文档2更侧重于应用场景。"
  }
}
```

**UI处理建议**：
- Bento Grid布局展示对比结果
- 每个文档使用独立卡片
- 高亮显示差异点
- 导出按钮（支持Markdown、PDF）

### 7.4 查询来源详情

- **接口地址**: `GET /v1/sources`
- **功能**: 根据文档 ID 获取详细的引用片段和元数据

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 | UI展示建议 |
|-------|------|------|------|------------|
| doc_id | Integer | 否 | 文档ID | 可选过滤 |

**请求示例**：
```bash
curl "http://127.0.0.1:8010/v1/sources?doc_id=123"
```

**响应字段**：见Source对象

**响应示例**：
```json
{
  "success": true,
  "data": [
    {
      "doc_id": 123,
      "file_name": "使用指南.pdf",
      "content": "系统支持多种数据源...",
      "score": 0.95
    }
  ]
}
```

**UI处理建议**：
- 卡片列表展示
- 每个来源显示相关度进度条
- 点击跳转文档详情
- 高亮显示关键词

### 7.5 语义搜索（纯检索）

- **接口地址**: `POST /v1/search`
- **功能**: 仅执行向量检索，不调用 LLM 生成回答
- **Content-Type**: `application/json`

**请求体**：

| 参数名 | 类型 | 必填 | 说明 | UI展示建议 |
|-------|------|------|------|------------|
| query | String | 是 | 搜索关键词 | 搜索框，支持回车搜索 |
| top_k | Integer | 否 | 返回结果数量，默认5 | 结果数量选择器 |

**请求示例**：
```bash
curl -X POST "http://127.0.0.1:8010/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "如何使用系统",
    "top_k": 5
  }'
```

**响应字段**：同Source对象

**响应示例**：
```json
{
  "success": true,
  "data": [
    {
      "doc_id": 123,
      "content": "使用指南：系统支持多种数据源...",
      "score": 0.98
    }
  ]
}
```

**UI处理建议**：
- 实时搜索（输入时自动搜索）
- 结果卡片展示
- 相关度进度条
- 关键词高亮
- 点击跳转文档

## 8. 错误处理与UI建议

### 8.1 错误码规范

| 错误码 | 说明 | HTTP状态码 | UI处理建议 |
|-------|------|-----------|------------|
| 400 | 请求参数错误 | 400 | 显示错误提示，高亮错误字段 |
| 401 | 未授权 | 401 | 跳转登录页面 |
| 403 | 无权限 | 403 | 显示"您没有权限"提示 |
| 404 | 资源不存在 | 404 | 显示"资源不存在"提示 |
| 429 | 请求过于频繁 | 429 | 显示"请求过于频繁，请稍后重试"提示 |
| 500 | 服务器内部错误 | 500 | 显示"服务器错误，请稍后重试"提示 |

### 8.2 UI错误处理最佳实践

**错误提示组件：**
- 使用统一的错误提示组件
- 顶部浮动提示（Message）
- 错误图标 + 错误信息 + 解决方案
- 自动消失（5s）或手动关闭
- 支持错误堆栈展开（开发模式）

**错误提示样式：**
- 成功：绿色背景，白色文字
- 错误：红色背景，白色文字
- 警告：橙色背景，白色文字
- 信息：蓝色背景，白色文字

**错误边界：**
- React ErrorBoundary捕获组件错误
- 显示友好的错误页面
- 提供"刷新页面"和"返回首页"按钮

### 8.3 加载状态处理

**全局加载状态：**
- 顶部进度条（全局）
- 骨架屏（Skeleton）
- 加载动画（Spinner）

**局部加载状态：**
- 按钮加载（旋转图标）
- 卡片加载（骨架屏）
- 表格加载（骨架行）

**加载状态UI建议：**
- 使用主色调渐变
- 加载动画流畅（60fps）
- 提供加载提示文字

## 9. 性能优化建议

### 9.1 请求优化

- **并发请求**：使用axios.all并发处理独立请求
- **请求缓存**：使用缓存减少重复请求
- **请求取消**：使用CancelToken取消未完成的请求
- **请求重试**：失败请求自动重试（最多3次）

### 9.2 数据处理优化

- **分页加载**：大列表使用分页或虚拟滚动
- **懒加载**：图片和组件懒加载
- **数据预处理**：接口返回数据预处理后存储

### 9.3 渲染优化

- **React.memo**：组件记忆化，避免不必要的重渲染
- **useMemo**：计算结果记忆化
- **useCallback**：函数记忆化
- **虚拟滚动**：长列表使用虚拟滚动

## 10. 相关文档

- [操作界面文档](./操作界面.md) - 了解前端界面设计和交互流程
- [技术设计文档](./技术设计.md) - 了解系统架构和技术实现
- [测试指南文档](./测试指南.md) - 学习API测试编写和执行
- [敏感信息过滤文档](./sensitive-data-filter.md) - 了解敏感信息过滤功能
