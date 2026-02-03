-- ============================================================================
-- 文件级注释：知识库智能体系统 - PostgreSQL数据库初始化脚本
-- 功能说明：
--   1. 创建所有表结构（9张表）
--   2. 创建索引和外键约束
--   3. 添加表和字段注释
--   4. 创建触发器
--   5. 插入默认配置数据
-- 使用方法：
--   psql -h localhost -U postgres -d knowledge_db -f init_postgresql.sql
-- 版本：1.0
-- 创建时间：2025-01-26
-- ============================================================================

\echo '========================================'
\echo '开始初始化数据库...'
\echo '========================================'

-- ============================================================================
-- 第一部分：文档管理表
-- ============================================================================

\echo ''
\echo '创建文档管理表...'

-- ----------------------------------------------------------------------------
-- 1. documents 表：文档元数据表
-- 功能说明：存储上传或抓取的文档基本信息
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    file_hash VARCHAR(64) NOT NULL UNIQUE,
    source_type VARCHAR(50) NOT NULL,
    tags VARCHAR(512),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 2. vector_mappings 表：向量索引映射表
-- 功能说明：将文档片段与向量库中的ID关联
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vector_mappings (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL,
    chunk_id VARCHAR(100) NOT NULL,
    chunk_content TEXT NOT NULL,
    CONSTRAINT fk_vector_document FOREIGN KEY (document_id)
        REFERENCES documents(id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 3. ingest_tasks 表：文件摄入任务表
-- 功能说明：用于异步处理文件上传
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ingest_tasks (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(512),
    file_hash VARCHAR(64),
    source_type VARCHAR(50) NOT NULL,
    tags VARCHAR(512),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    progress INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    document_id INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_task_document FOREIGN KEY (document_id)
        REFERENCES documents(id) ON DELETE SET NULL
);

-- ============================================================================
-- 第二部分：对话系统表
-- ============================================================================

\echo '创建对话系统表...'

-- ----------------------------------------------------------------------------
-- 4. conversations 表：对话会话表
-- 功能说明：存储对话会话信息、Token统计、成本等
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL DEFAULT '新对话',
    model_name VARCHAR(100),
    use_agent INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    total_cost DECIMAL(10, 4) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    message_count INTEGER NOT NULL DEFAULT 0
);

-- ----------------------------------------------------------------------------
-- 5. messages 表：对话消息表
-- 功能说明：存储具体的对话消息内容
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    content TEXT NOT NULL,
    streaming_state VARCHAR(20),
    tokens_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_message_conversation FOREIGN KEY (conversation_id)
        REFERENCES conversations(id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 6. message_sources 表：消息来源引用表
-- 功能说明：存储消息引用的文档来源
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS message_sources (
    id SERIAL PRIMARY KEY,
    message_id INTEGER NOT NULL,
    document_id INTEGER,
    chunk_id VARCHAR(100),
    file_name VARCHAR(255) NOT NULL,
    text_segment TEXT NOT NULL,
    score INTEGER,
    position INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT fk_source_message FOREIGN KEY (message_id)
        REFERENCES messages(id) ON DELETE CASCADE,
    CONSTRAINT fk_source_document FOREIGN KEY (document_id)
        REFERENCES documents(id) ON DELETE SET NULL
);

-- ----------------------------------------------------------------------------
-- 7. token_usage 表：Token使用统计表
-- 功能说明：记录LLM调用的Token消耗和成本
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS token_usage (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    prompt_cost DECIMAL(10, 6) NOT NULL DEFAULT 0,
    completion_cost DECIMAL(10, 6) NOT NULL DEFAULT 0,
    total_cost DECIMAL(10, 6) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_token_conversation FOREIGN KEY (conversation_id)
        REFERENCES conversations(id) ON DELETE CASCADE,
    CONSTRAINT fk_token_message FOREIGN KEY (message_id)
        REFERENCES messages(id) ON DELETE CASCADE
);

-- ============================================================================
-- 第三部分：模型配置表
-- ============================================================================

\echo '创建模型配置表...'

-- ----------------------------------------------------------------------------
-- 8. model_config 表：LLM模型配置表
-- 功能说明：存储不同提供商的LLM模型配置信息
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS model_config (
    id VARCHAR(50) PRIMARY KEY,
    provider_id VARCHAR(50) NOT NULL,
    provider_name VARCHAR(100) NOT NULL,
    endpoint VARCHAR(500) NOT NULL,
    api_key VARCHAR(500),
    model_id VARCHAR(100) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL DEFAULT 'text',
    temperature FLOAT NOT NULL DEFAULT 0.7,
    max_tokens INTEGER NOT NULL DEFAULT 8192,
    top_p FLOAT NOT NULL DEFAULT 0.9,
    top_k INTEGER NOT NULL DEFAULT 0,
    device VARCHAR(20) NOT NULL DEFAULT 'auto',
    status INTEGER NOT NULL DEFAULT 1,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 9. embedding_config 表：Embedding模型配置表
-- 功能说明：存储向量化模型的配置信息
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS embedding_config (
    id VARCHAR(50) PRIMARY KEY,
    provider_id VARCHAR(50) NOT NULL,
    provider_name VARCHAR(100) NOT NULL,
    endpoint VARCHAR(500),
    api_key VARCHAR(500),
    model_id VARCHAR(100) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    device VARCHAR(20) NOT NULL DEFAULT 'cpu',
    status INTEGER NOT NULL DEFAULT 1,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 第四部分：索引定义
-- ============================================================================

\echo '创建索引...'

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
-- 第五部分：表和字段注释
-- ============================================================================

\echo '添加表和字段注释...'

-- documents 表注释
COMMENT ON TABLE documents IS '文档元数据表';
COMMENT ON COLUMN documents.id IS '文档ID（主键）';
COMMENT ON COLUMN documents.file_name IS '文件名或网页标题';
COMMENT ON COLUMN documents.file_path IS '文件物理路径或来源URL';
COMMENT ON COLUMN documents.file_hash IS '内容哈希值，用于去重和版本校验';
COMMENT ON COLUMN documents.source_type IS '来源类型（FILE/WEB/DB）';
COMMENT ON COLUMN documents.tags IS '标签列表（JSON字符串存储）';
COMMENT ON COLUMN documents.created_at IS '创建时间（本地时间）';
COMMENT ON COLUMN documents.updated_at IS '更新时间（本地时间）';

-- vector_mappings 表注释
COMMENT ON TABLE vector_mappings IS '向量索引映射表';
COMMENT ON COLUMN vector_mappings.id IS '映射ID（主键）';
COMMENT ON COLUMN vector_mappings.document_id IS '关联文档ID（外键）';
COMMENT ON COLUMN vector_mappings.chunk_id IS '向量库中的Chunk唯一标识';
COMMENT ON COLUMN vector_mappings.chunk_content IS '片段内容备份';

-- ingest_tasks 表注释
COMMENT ON TABLE ingest_tasks IS '文件摄入任务表';
COMMENT ON COLUMN ingest_tasks.id IS '任务ID（主键）';
COMMENT ON COLUMN ingest_tasks.file_name IS '文件名或网页标题';
COMMENT ON COLUMN ingest_tasks.file_path IS '文件物理路径或来源URL';
COMMENT ON COLUMN ingest_tasks.file_hash IS '文件内容哈希值';
COMMENT ON COLUMN ingest_tasks.source_type IS '来源类型（FILE/WEB/DB）';
COMMENT ON COLUMN ingest_tasks.tags IS '标签列表（JSON字符串存储）';
COMMENT ON COLUMN ingest_tasks.status IS '任务状态（pending/processing/completed/failed）';
COMMENT ON COLUMN ingest_tasks.progress IS '处理进度（0-100）';
COMMENT ON COLUMN ingest_tasks.error_message IS '错误信息（如果失败）';
COMMENT ON COLUMN ingest_tasks.document_id IS '关联文档ID（完成后）';
COMMENT ON COLUMN ingest_tasks.created_at IS '创建时间（本地时间）';
COMMENT ON COLUMN ingest_tasks.updated_at IS '更新时间（本地时间）';

-- conversations 表注释
COMMENT ON TABLE conversations IS '对话会话表';
COMMENT ON COLUMN conversations.id IS '会话ID（主键）';
COMMENT ON COLUMN conversations.title IS '会话标题';
COMMENT ON COLUMN conversations.model_name IS '使用的LLM模型名称';
COMMENT ON COLUMN conversations.use_agent IS '是否启用智能体（0/1）';
COMMENT ON COLUMN conversations.total_tokens IS '总Token消耗';
COMMENT ON COLUMN conversations.total_cost IS '总成本（元）';
COMMENT ON COLUMN conversations.created_at IS '创建时间';
COMMENT ON COLUMN conversations.updated_at IS '更新时间';
COMMENT ON COLUMN conversations.message_count IS '消息数量（缓存）';

-- messages 表注释
COMMENT ON TABLE messages IS '对话消息表';
COMMENT ON COLUMN messages.id IS '消息ID（主键）';
COMMENT ON COLUMN messages.conversation_id IS '关联会话ID（外键）';
COMMENT ON COLUMN messages.role IS '消息角色（user/assistant/system）';
COMMENT ON COLUMN messages.content IS '消息内容';
COMMENT ON COLUMN messages.streaming_state IS '流式状态（idle/streaming/completed）';
COMMENT ON COLUMN messages.tokens_count IS 'Token数量';
COMMENT ON COLUMN messages.created_at IS '创建时间';

-- message_sources 表注释
COMMENT ON TABLE message_sources IS '消息来源引用表';
COMMENT ON COLUMN message_sources.id IS '来源ID（主键）';
COMMENT ON COLUMN message_sources.message_id IS '关联消息ID（外键）';
COMMENT ON COLUMN message_sources.document_id IS '引用文档ID（外键，级联SET NULL）';
COMMENT ON COLUMN message_sources.chunk_id IS '向量库中的Chunk ID';
COMMENT ON COLUMN message_sources.file_name IS '文件名（冗余存储）';
COMMENT ON COLUMN message_sources.text_segment IS '引用的文本片段';
COMMENT ON COLUMN message_sources.score IS '相关度评分（0-100）';
COMMENT ON COLUMN message_sources.position IS '排序位置';

-- token_usage 表注释
COMMENT ON TABLE token_usage IS 'Token使用统计表';
COMMENT ON COLUMN token_usage.id IS 'Token记录ID（主键）';
COMMENT ON COLUMN token_usage.conversation_id IS '关联会话ID（外键）';
COMMENT ON COLUMN token_usage.message_id IS '关联消息ID（外键）';
COMMENT ON COLUMN token_usage.model_name IS '模型名称';
COMMENT ON COLUMN token_usage.prompt_tokens IS '输入Token数';
COMMENT ON COLUMN token_usage.completion_tokens IS '输出Token数';
COMMENT ON COLUMN token_usage.total_tokens IS '总Token数';
COMMENT ON COLUMN token_usage.prompt_cost IS '输入成本（元）';
COMMENT ON COLUMN token_usage.completion_cost IS '输出成本（元）';
COMMENT ON COLUMN token_usage.total_cost IS '总成本（元）';
COMMENT ON COLUMN token_usage.created_at IS '创建时间';

-- model_config 表注释
COMMENT ON TABLE model_config IS 'LLM模型配置表';
COMMENT ON COLUMN model_config.id IS '配置ID（使用UUID或nanoid）';
COMMENT ON COLUMN model_config.provider_id IS '提供商ID（ollama/zhipuai/openai等）';
COMMENT ON COLUMN model_config.provider_name IS '提供商名称';
COMMENT ON COLUMN model_config.endpoint IS 'API端点地址';
COMMENT ON COLUMN model_config.api_key IS 'API密钥（加密存储）';
COMMENT ON COLUMN model_config.model_id IS '模型ID';
COMMENT ON COLUMN model_config.model_name IS '模型名称';
COMMENT ON COLUMN model_config.type IS '模型类型（text/embedding）';
COMMENT ON COLUMN model_config.temperature IS '温度参数（0-2）';
COMMENT ON COLUMN model_config.max_tokens IS '最大生成token数';
COMMENT ON COLUMN model_config.top_p IS 'nucleus采样参数';
COMMENT ON COLUMN model_config.top_k IS 'top-k采样参数';
COMMENT ON COLUMN model_config.device IS '运行设备（cpu/cuda/auto）';
COMMENT ON COLUMN model_config.status IS '状态（1启用/0禁用）';
COMMENT ON COLUMN model_config.is_default IS '是否为默认配置';
COMMENT ON COLUMN model_config.created_at IS '创建时间';
COMMENT ON COLUMN model_config.updated_at IS '更新时间';

-- embedding_config 表注释
COMMENT ON TABLE embedding_config IS 'Embedding模型配置表';
COMMENT ON COLUMN embedding_config.id IS '配置ID（主键）';
COMMENT ON COLUMN embedding_config.provider_id IS '提供商ID（ollama/zhipuai/local等）';
COMMENT ON COLUMN embedding_config.provider_name IS '提供商名称';
COMMENT ON COLUMN embedding_config.endpoint IS 'API端点地址（本地模型为空）';
COMMENT ON COLUMN embedding_config.api_key IS 'API密钥（云端提供商需要）';
COMMENT ON COLUMN embedding_config.model_id IS '模型ID';
COMMENT ON COLUMN embedding_config.model_name IS '模型名称';
COMMENT ON COLUMN embedding_config.device IS '运行设备（cpu/cuda/auto）';
COMMENT ON COLUMN embedding_config.status IS '状态（1启用/0禁用）';
COMMENT ON COLUMN embedding_config.is_default IS '是否为默认配置';
COMMENT ON COLUMN embedding_config.created_at IS '创建时间';
COMMENT ON COLUMN embedding_config.updated_at IS '更新时间';

-- ============================================================================
-- 第六部分：触发器（自动更新updated_at字段）
-- ============================================================================

\echo '创建触发器...'

-- 创建通用触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- documents 表触发器
DROP TRIGGER IF EXISTS update_documents_updated_at ON documents;
CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ingest_tasks 表触发器
DROP TRIGGER IF EXISTS update_ingest_tasks_updated_at ON ingest_tasks;
CREATE TRIGGER update_ingest_tasks_updated_at
    BEFORE UPDATE ON ingest_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- conversations 表触发器
DROP TRIGGER IF EXISTS update_conversations_updated_at ON conversations;
CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- model_config 表触发器
DROP TRIGGER IF EXISTS update_model_config_updated_at ON model_config;
CREATE TRIGGER update_model_config_updated_at
    BEFORE UPDATE ON model_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- embedding_config 表触发器
DROP TRIGGER IF EXISTS update_embedding_config_updated_at ON embedding_config;
CREATE TRIGGER update_embedding_config_updated_at
    BEFORE UPDATE ON embedding_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 第七部分：默认配置数据
-- ============================================================================

\echo '插入默认配置数据...'

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
    TRUE
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
    TRUE
WHERE NOT EXISTS (SELECT 1 FROM embedding_config WHERE provider_id = 'ollama');

-- ============================================================================
-- 完成
-- ============================================================================

\echo ''
\echo '========================================'
\echo '数据库初始化完成！'
\echo '========================================'
\echo '已创建的表：'
\echo '  - documents (文档元数据表)'
\echo '  - vector_mappings (向量映射表)'
\echo '  - ingest_tasks (摄入任务表)'
\echo '  - conversations (对话会话表)'
\echo '  - messages (消息表)'
\echo '  - message_sources (消息来源表)'
\echo '  - token_usage (Token统计表)'
\echo '  - model_config (LLM配置表)'
\echo '  - embedding_config (Embedding配置表)'
\echo ''
\echo '已创建的索引：'
SELECT tablename, indexname FROM pg_indexes WHERE schemaname = 'public' ORDER BY tablename, indexname;
\echo ''
\echo '默认配置数据：'
SELECT 'model_config' AS table_name, COUNT(*) AS row_count FROM model_config
UNION ALL
SELECT 'embedding_config', COUNT(*) FROM embedding_config;
\echo '========================================'
