# 数据库初始化脚本使用说明

本目录包含知识库智能体系统的数据库初始化脚本。

## 目录结构

```
script/database/
├── init_postgresql.sql    # PostgreSQL 版本初始化脚本
├── init_sqlite.sql         # SQLite 版本初始化脚本
└── README.md              # 本文档
```

## 数据库表清单

系统包含以下9张核心表：

### 文档管理表

| 表名 | 说明 |
|------|------|
| `documents` | 文档元数据表，存储上传或抓取的文档基本信息 |
| `vector_mappings` | 向量索引映射表，关联文档片段与向量库ID |
| `ingest_tasks` | 文件摄入任务表，用于异步处理文件上传 |

### 对话系统表

| 表名 | 说明 |
|------|------|
| `conversations` | 对话会话表，存储会话信息、Token统计、成本等 |
| `messages` | 对话消息表，存储具体的对话消息内容 |
| `message_sources` | 消息来源引用表，存储消息引用的文档来源 |
| `token_usage` | Token使用统计表，记录LLM调用的Token消耗和成本 |

### 模型配置表

| 表名 | 说明 |
|------|------|
| `model_config` | LLM模型配置表，存储不同提供商的LLM配置 |
| `embedding_config` | Embedding模型配置表，存储向量化模型配置 |

## 表结构详情

### 1. documents（文档元数据表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL/INTEGER | 主键 |
| file_name | VARCHAR(255)/TEXT | 文件名或网页标题 |
| file_path | VARCHAR(512)/TEXT | 文件物理路径或来源URL |
| file_hash | VARCHAR(64)/TEXT | 内容哈希值，用于去重 |
| source_type | VARCHAR(50)/TEXT | 来源类型(FILE/WEB/DB) |
| tags | VARCHAR(512)/TEXT | 标签列表(JSON字符串) |
| created_at | TIMESTAMP/DATETIME | 创建时间 |
| updated_at | TIMESTAMP/DATETIME | 更新时间 |

### 2. vector_mappings（向量映射表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL/INTEGER | 主键 |
| document_id | INTEGER | 关联文档ID(外键) |
| chunk_id | VARCHAR(100)/TEXT | 向量库中的Chunk ID |
| chunk_content | TEXT | 片段内容备份 |

### 3. ingest_tasks（摄入任务表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL/INTEGER | 主键 |
| file_name | VARCHAR(255)/TEXT | 文件名或网页标题 |
| file_path | VARCHAR(512)/TEXT | 文件物理路径或来源URL |
| file_hash | VARCHAR(64)/TEXT | 文件内容哈希值 |
| source_type | VARCHAR(50)/TEXT | 来源类型(FILE/WEB/DB) |
| tags | VARCHAR(512)/TEXT | 标签列表(JSON字符串) |
| status | VARCHAR(20)/TEXT | 任务状态(pending/processing/completed/failed) |
| progress | INTEGER | 处理进度(0-100) |
| error_message | TEXT | 错误信息 |
| document_id | INTEGER | 关联文档ID(外键) |
| created_at | TIMESTAMP/DATETIME | 创建时间 |
| updated_at | TIMESTAMP/DATETIME | 更新时间 |

### 4. conversations（会话表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL/INTEGER | 主键 |
| title | VARCHAR(255)/TEXT | 会话标题 |
| model_name | VARCHAR(100)/TEXT | 使用的LLM模型名称 |
| use_agent | INTEGER | 是否启用智能体(0/1) |
| total_tokens | INTEGER | 总Token消耗 |
| total_cost | DECIMAL/REAL | 总成本（元） |
| created_at | TIMESTAMP/DATETIME | 创建时间 |
| updated_at | TIMESTAMP/DATETIME | 更新时间 |
| message_count | INTEGER | 消息数量(缓存) |

### 5. messages（消息表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL/INTEGER | 主键 |
| conversation_id | INTEGER | 关联会话ID(外键) |
| role | VARCHAR(20)/TEXT | 消息角色(user/assistant/system) |
| content | TEXT | 消息内容 |
| streaming_state | VARCHAR(20)/TEXT | 流式状态(idle/streaming/completed) |
| tokens_count | INTEGER | Token数量 |
| created_at | TIMESTAMP/DATETIME | 创建时间 |

### 6. message_sources（来源引用表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL/INTEGER | 主键 |
| message_id | INTEGER | 关联消息ID(外键) |
| document_id | INTEGER | 引用文档ID(外键，ON DELETE SET NULL) |
| chunk_id | VARCHAR(100)/TEXT | 向量库中的Chunk ID |
| file_name | VARCHAR(255)/TEXT | 文件名(冗余存储) |
| text_segment | TEXT | 引用的文本片段 |
| score | INTEGER | 相关度评分(0-100) |
| position | INTEGER | 排序位置 |

### 7. token_usage（Token统计表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL/INTEGER | 主键 |
| conversation_id | INTEGER | 关联会话ID(外键) |
| message_id | INTEGER | 关联消息ID(外键) |
| model_name | VARCHAR(100)/TEXT | 模型名称 |
| prompt_tokens | INTEGER | 输入Token数 |
| completion_tokens | INTEGER | 输出Token数 |
| total_tokens | INTEGER | 总Token数 |
| prompt_cost | DECIMAL/REAL | 输入成本（元） |
| completion_cost | DECIMAL/REAL | 输出成本（元） |
| total_cost | DECIMAL/REAL | 总成本（元） |
| created_at | TIMESTAMP/DATETIME | 创建时间 |

### 8. model_config（LLM配置表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(50)/TEXT | 配置ID(主键) |
| provider_id | VARCHAR(50)/TEXT | 提供商ID(ollama/zhipuai/openai等) |
| provider_name | VARCHAR(100)/TEXT | 提供商名称 |
| endpoint | VARCHAR(500)/TEXT | API端点地址 |
| api_key | VARCHAR(500)/TEXT | API密钥(加密存储) |
| model_id | VARCHAR(100)/TEXT | 模型ID |
| model_name | VARCHAR(100)/TEXT | 模型名称 |
| type | VARCHAR(20)/TEXT | 模型类型(text/embedding) |
| temperature | FLOAT/REAL | 温度参数(0-2) |
| max_tokens | INTEGER | 最大生成token数 |
| top_p | FLOAT/REAL | nucleus采样参数 |
| top_k | INTEGER | top-k采样参数 |
| status | INTEGER | 状态(1启用/0禁用) |
| is_default | BOOLEAN/INTEGER | 是否为默认配置 |
| created_at | TIMESTAMP/DATETIME | 创建时间 |
| updated_at | TIMESTAMP/DATETIME | 更新时间 |

### 9. embedding_config（Embedding配置表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(50)/TEXT | 配置ID(主键) |
| provider_id | VARCHAR(50)/TEXT | 提供商ID(ollama/zhipuai/local等) |
| provider_name | VARCHAR(100)/TEXT | 提供商名称 |
| endpoint | VARCHAR(500)/TEXT | API端点地址 |
| api_key | VARCHAR(500)/TEXT | API密钥 |
| model_id | VARCHAR(100)/TEXT | 模型ID |
| model_name | VARCHAR(100)/TEXT | 模型名称 |
| device | VARCHAR(20)/TEXT | 运行设备(cpu/cuda/auto) |
| status | INTEGER | 状态(1启用/0禁用) |
| is_default | BOOLEAN/INTEGER | 是否为默认配置 |
| created_at | TIMESTAMP/DATETIME | 创建时间 |
| updated_at | TIMESTAMP/DATETIME | 更新时间 |

## PostgreSQL 初始化

### 前置条件

- 已安装 PostgreSQL 12+
- 已创建数据库（或使用默认模板数据库）

### 执行初始化

#### 方式一：命令行执行

```bash
psql -h localhost -U postgres -d knowledge_db -f init_postgresql.sql
```

参数说明：
- `-h`：数据库主机地址
- `-U`：数据库用户名
- `-d`：数据库名称
- `-f`：要执行的脚本文件

#### 方式二：交互式执行

```bash
# 连接数据库
psql -h localhost -U postgres -d knowledge_db

# 在 psql 命令行中执行
\i script/database/init_postgresql.sql
```

### 验证初始化

```sql
-- 查看所有表
\dt

-- 查看表结构
\d+ documents
\d+ conversations
\d+ model_config

-- 查看默认配置
SELECT * FROM model_config;
SELECT * FROM embedding_config;

-- 查看索引
\di
```

## SQLite 初始化

### 前置条件

- 已安装 SQLite 3

### 执行初始化

```bash
sqlite3 data/metadata.db < script/database/init_sqlite.sql
```

### 验证初始化

```bash
# 查看所有表
sqlite3 data/metadata.db ".tables"

# 查看表结构
sqlite3 data/metadata.db ".schema documents"

# 查看默认配置
sqlite3 data/metadata.db "SELECT * FROM model_config;"
sqlite3 data/metadata.db "SELECT * FROM embedding_config;"
```

## 默认配置数据

初始化脚本会自动创建以下默认配置：

### LLM 默认配置

| 配置项 | 值 |
|--------|-----|
| ID | ollama-default |
| Provider | ollama |
| Model | deepseek-r1:8b |
| Endpoint | http://127.0.0.1:11434/api |
| Temperature | 0.7 |
| Max Tokens | 8192 |

### Embedding 默认配置

| 配置项 | 值 |
|--------|-----|
| ID | ollama-emb-default |
| Provider | ollama |
| Model | mxbai-embed-large |
| Endpoint | http://127.0.0.1:11434/api |
| Device | cpu |

## 语法差异说明

PostgreSQL 和 SQLite 版本的主要语法差异：

| 特性 | PostgreSQL | SQLite |
|------|------------|--------|
| 自增主键 | `SERIAL` | `INTEGER PRIMARY KEY AUTOINCREMENT` |
| 注释 | `COMMENT ON` | 不支持 |
| 布尔类型 | `BOOLEAN` | `INTEGER (0/1)` |
| 触发器 | `CREATE TRIGGER ... EXECUTE FUNCTION` | `CREATE TRIGGER ... BEGIN ... END` |
| 时间戳 | `TIMESTAMP` | `DATETIME` |
| 外键约束 | 完整支持 | 需要 `PRAGMA foreign_keys=ON` |

## 级联删除说明

- 删除会话时，级联删除其所有消息、Token记录
- 删除消息时，级联删除其来源引用、Token记录
- 删除文档时，级联删除向量映射，message_sources 中的 document_id 置为 NULL

## 重新初始化

如需完全重新初始化数据库，请先删除所有表：

### PostgreSQL

```sql
DROP TABLE IF EXISTS token_usage CASCADE;
DROP TABLE IF EXISTS message_sources CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS conversations CASCADE;
DROP TABLE IF EXISTS ingest_tasks CASCADE;
DROP TABLE IF EXISTS vector_mappings CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS embedding_config CASCADE;
DROP TABLE IF EXISTS model_config CASCADE;

DROP FUNCTION IF EXISTS update_updated_at_column CASCADE;
```

### SQLite

```bash
# 直接删除数据库文件
rm data/metadata.db

# 然后重新执行初始化脚本
```

## 故障排查

### PostgreSQL 问题

**问题：外键约束错误**
```
ERROR: foreign key constraint violated
```

**解决方案**：检查相关表的数据是否存在，或临时禁用外键检查。

**问题：权限不足**
```
ERROR: permission denied for table xxx
```

**解决方案**：使用具有足够权限的用户执行，或授予相应权限。

### SQLite 问题

**问题：外键约束不生效**

**解决方案**：确保执行了 `PRAGMA foreign_keys=ON;`

**问题：数据库文件被锁定**

**解决方案**：确保没有其他进程正在使用数据库文件。

## 注意事项

1. **生产环境**：建议使用 PostgreSQL
2. **开发环境**：可以使用 SQLite 进行快速开发
3. **备份**：执行初始化前建议备份现有数据
4. **字符编码**：确保使用 UTF-8 编码
5. **时区设置**：PostgreSQL 建议设置时区为 `Asia/Shanghai`
6. **ORM 自动创建**：应用程序也会通过 SQLAlchemy ORM 自动创建表，建议只使用一种方式初始化

## 更新日志

| 版本 | 日期 | 说明 |
|------|------|------|
| 2.0 | 2025-01-26 | 整合所有初始化脚本，支持 PostgreSQL 和 SQLite |
| 1.0 | 2025-01-20 | 初始版本，仅包含对话持久化功能 |
