-- ============================================================================
-- 文件级注释：知识库智能体系统 - SQLite数据库初始化脚本
-- 功能说明：
--   1. 创建所有表结构（9张表）
--   2. 创建索引和外键约束
--   3. 创建触发器
--   4. 插入默认配置数据
-- 使用方法：
--   sqlite3 data/metadata.db < init_sqlite.sql
-- 版本：1.0
-- 创建时间：2025-01-26
-- 注：SQLite 不支持 COMMENT ON 语法，注释通过代码中的注释体现
-- ============================================================================

-- 开启外键约束支持
PRAGMA foreign_keys = ON;

-- ============================================================================
-- 第一部分：文档管理表
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. documents 表：文档元数据表
-- 功能说明：存储上传或抓取的文档基本信息
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_hash TEXT NOT NULL UNIQUE,
    source_type TEXT NOT NULL,
    tags TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 2. vector_mappings 表：向量索引映射表
-- 功能说明：将文档片段与向量库中的ID关联
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vector_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    chunk_id TEXT NOT NULL,
    chunk_content TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 3. ingest_tasks 表：文件摄入任务表
-- 功能说明：用于异步处理文件上传
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ingest_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    file_path TEXT,
    file_hash TEXT,
    source_type TEXT NOT NULL,
    tags TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    progress INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    document_id INTEGER,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL
);

-- ============================================================================
-- 第二部分：对话系统表
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 4. conversations 表：对话会话表
-- 功能说明：存储对话会话信息、Token统计、成本等
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL DEFAULT '新对话',
    model_name TEXT,
    use_agent INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    total_cost REAL NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    message_count INTEGER NOT NULL DEFAULT 0
);

-- ----------------------------------------------------------------------------
-- 5. messages 表：对话消息表
-- 功能说明：存储具体的对话消息内容
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    content TEXT NOT NULL,
    streaming_state TEXT,
    tokens_count INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 6. message_sources 表：消息来源引用表
-- 功能说明：存储消息引用的文档来源
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS message_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL,
    document_id INTEGER,
    chunk_id TEXT,
    file_name TEXT NOT NULL,
    text_segment TEXT NOT NULL,
    score INTEGER,
    position INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL
);

-- ----------------------------------------------------------------------------
-- 7. token_usage 表：Token使用统计表
-- 功能说明：记录LLM调用的Token消耗和成本
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS token_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    model_name TEXT NOT NULL,
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    prompt_cost REAL NOT NULL DEFAULT 0,
    completion_cost REAL NOT NULL DEFAULT 0,
    total_cost REAL NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
);

-- ============================================================================
-- 第三部分：模型配置表
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 8. model_config 表：LLM模型配置表
-- 功能说明：存储不同提供商的LLM模型配置信息
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS model_config (
    id TEXT PRIMARY KEY,
    provider_id TEXT NOT NULL,
    provider_name TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    api_key TEXT,
    model_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'text',
    temperature REAL NOT NULL DEFAULT 0.7,
    max_tokens INTEGER NOT NULL DEFAULT 8192,
    top_p REAL NOT NULL DEFAULT 0.9,
    top_k INTEGER NOT NULL DEFAULT 0,
    device TEXT NOT NULL DEFAULT 'auto',
    status INTEGER NOT NULL DEFAULT 1,
    is_default INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 9. embedding_config 表：Embedding模型配置表
-- 功能说明：存储向量化模型的配置信息
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS embedding_config (
    id TEXT PRIMARY KEY,
    provider_id TEXT NOT NULL,
    provider_name TEXT NOT NULL,
    endpoint TEXT,
    api_key TEXT,
    model_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    device TEXT NOT NULL DEFAULT 'cpu',
    status INTEGER NOT NULL DEFAULT 1,
    is_default INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 第四部分：索引定义
-- ============================================================================

-- documents 表索引
CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(file_hash);

-- vector_mappings 表索引
CREATE INDEX IF NOT EXISTS idx_vector_chunk ON vector_mappings(chunk_id);

-- ingest_tasks 表索引
CREATE INDEX IF NOT EXISTS idx_tasks_status ON ingest_tasks(status);

-- conversations 表索引
CREATE INDEX IF NOT EXISTS idx_conversations_updated ON conversations(updated_at DESC);

-- messages 表索引
CREATE INDEX IF NOT EXISTS idx_messages_conv_created ON messages(conversation_id, created_at);

-- message_sources 表索引
CREATE INDEX IF NOT EXISTS idx_message_sources_msg_pos ON message_sources(message_id, position);

-- token_usage 表索引
CREATE INDEX IF NOT EXISTS idx_token_usage_conv ON token_usage(conversation_id);
CREATE INDEX IF NOT EXISTS idx_token_usage_msg ON token_usage(message_id);

-- model_config 表索引
CREATE INDEX IF NOT EXISTS idx_model_config_provider ON model_config(provider_id);
CREATE INDEX IF NOT EXISTS idx_model_config_default ON model_config(is_default);
CREATE INDEX IF NOT EXISTS idx_model_config_status ON model_config(status);
CREATE INDEX IF NOT EXISTS idx_model_config_type ON model_config(type);

-- embedding_config 表索引
CREATE INDEX IF NOT EXISTS idx_embedding_config_provider ON embedding_config(provider_id);
CREATE INDEX IF NOT EXISTS idx_embedding_config_default ON embedding_config(is_default);
CREATE INDEX IF NOT EXISTS idx_embedding_config_status ON embedding_config(status);

-- ============================================================================
-- 第五部分：触发器（自动更新updated_at字段）
-- ============================================================================

-- documents 表触发器
CREATE TRIGGER IF NOT EXISTS update_documents_updated_at
    AFTER UPDATE ON documents
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE documents SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ingest_tasks 表触发器
CREATE TRIGGER IF NOT EXISTS update_ingest_tasks_updated_at
    AFTER UPDATE ON ingest_tasks
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE ingest_tasks SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- conversations 表触发器
CREATE TRIGGER IF NOT EXISTS update_conversations_updated_at
    AFTER UPDATE ON conversations
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- model_config 表触发器
CREATE TRIGGER IF NOT EXISTS update_model_config_updated_at
    AFTER UPDATE ON model_config
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE model_config SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- embedding_config 表触发器
CREATE TRIGGER IF NOT EXISTS update_embedding_config_updated_at
    AFTER UPDATE ON embedding_config
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE embedding_config SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ============================================================================
-- 第六部分：默认配置数据
-- ============================================================================

-- 初始化LLM配置（Ollama为默认）
INSERT INTO model_config (id, provider_id, provider_name, endpoint, api_key, model_id, model_name, type, temperature, max_tokens, top_p, top_k, device, status, is_default)
SELECT
    'ollama-default',
    'ollama',
    'Ollama',
    'http://127.0.0.1:11434/api',
    '',
    'deepseek-r1:8b',
    'deepseek-r1:8b',
    'text',
    0.7,
    8192,
    0.9,
    0,
    'auto',
    1,
    1
WHERE NOT EXISTS (SELECT 1 FROM model_config WHERE provider_id = 'ollama');

-- 初始化Embedding配置（Ollama为默认）
INSERT INTO embedding_config (id, provider_id, provider_name, endpoint, api_key, model_id, model_name, device, status, is_default)
SELECT
    'ollama-emb-default',
    'ollama',
    'Ollama',
    'http://127.0.0.1:11434/api',
    '',
    'mxbai-embed-large',
    'mxbai-embed-large:latest',
    'cpu',
    1,
    1
WHERE NOT EXISTS (SELECT 1 FROM embedding_config WHERE provider_id = 'ollama');

-- ============================================================================
-- 完成
-- ============================================================================

-- 显示创建的表
.mode column
.headers on
SELECT name AS '已创建的表' FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;

-- 显示配置数据
SELECT 'model_config' AS '表名', COUNT(*) AS '记录数' FROM model_config
UNION ALL
SELECT 'embedding_config', COUNT(*) FROM embedding_config;
