/**
 * 上海宇羲伏天智能科技有限公司出品
 *
/**
 * 文件级注释：模型配置相关类型定义
 * 内部逻辑：定义LLM和Embedding配置的TypeScript类型
 * 参考项目：easy-dataset-file
 */

/**
 * LLM提供商类型
 */
export type LLMProvider = 'ollama' | 'zhipuai' | 'openai' | 'minimax' | 'moonshot' | 'deepseek';

/**
 * Embedding提供商类型
 */
export type EmbeddingProvider = 'ollama' | 'zhipuai' | 'local' | 'openai';

/**
 * 模型类型
 */
export type ModelType = 'text' | 'embedding';

/**
 * LLM模型配置接口
 */
export interface ModelConfig {
  id?: string;
  provider_id: LLMProvider;
  provider_name: string;
  endpoint: string;
  api_key: string;
  model_id: string;
  model_name: string;
  type: ModelType;
  temperature: number;
  max_tokens: number;
  top_p: number;
  top_k: number;
  device?: 'cpu' | 'cuda' | 'auto';  // 设备类型（仅本地模型有效）
  status: number;  // 1=启用使用中, 0=禁用
}

/**
 * 属性级注释：LLM模型配置安全响应类型（API返回，不含完整Key）
 * 属性：api_key_masked 脱敏显示的密钥（格式如 sk-...1234）
 */
export interface ModelConfigSafe {
  id?: string;
  provider_id: LLMProvider;
  provider_name: string;
  endpoint: string;
  api_key_masked: string;  // 脱敏显示，不包含真实值
  model_id: string;
  model_name: string;
  type: ModelType;
  temperature: number;
  max_tokens: number;
  top_p: number;
  top_k: number;
  device?: 'cpu' | 'cuda' | 'auto';
  status: number;
}

/**
 * 属性级注释：API密钥更新请求接口
 */
export interface APIKeyUpdateRequest {
  api_key: string;
}

/**
 * 属性级注释：API密钥更新响应接口
 */
export interface APIKeyUpdateResponse {
  api_key_masked: string;
  message: string;
}

/**
 * 创建模型配置请求接口（所有字段可选）
 */
export interface ModelConfigCreate {
  id?: string;
  provider_id: LLMProvider;
  provider_name: string;
  endpoint: string;
  api_key: string;
  model_id: string;
  model_name: string;
  type?: ModelType;
  temperature?: number;
  max_tokens?: number;
  top_p?: number;
  top_k?: number;
  device?: 'cpu' | 'cuda' | 'auto';  // 设备类型（仅本地模型有效）
  status?: number;
}

/**
 * Embedding模型配置接口
 */
export interface EmbeddingConfig {
  id?: string;
  provider_id: EmbeddingProvider;
  provider_name: string;
  endpoint: string;
  api_key: string;
  model_id: string;
  model_name: string;
  device: 'cpu' | 'cuda' | 'auto';
  status: number;  // 1=启用使用中, 0=禁用
}

/**
 * 属性级注释：Embedding模型配置安全响应类型（API返回，不含完整Key）
 * 属性：api_key_masked 脱敏显示的密钥（格式如 sk-...1234）
 */
export interface EmbeddingConfigSafe {
  id?: string;
  provider_id: EmbeddingProvider;
  provider_name: string;
  endpoint: string;
  api_key_masked: string;  // 脱敏显示，不包含真实值
  model_id: string;
  model_name: string;
  batch_size: number;
  device: 'cpu' | 'cuda' | 'auto';
  status: number;
}

/**
 * 创建Embedding配置请求接口
 */
export interface EmbeddingConfigCreate {
  id?: string;
  provider_id: EmbeddingProvider;
  provider_name: string;
  endpoint: string;
  api_key: string;
  model_id: string;
  model_name: string;
  device?: 'cpu' | 'cuda' | 'auto';
  status?: number;
}

/**
 * 提供商信息接口
 */
export interface ProviderInfo {
  value: string;
  label: string;
  default_endpoint: string;
  default_models: string[];
  type: ModelType;
}

/**
 * 提供商列表响应接口
 */
export interface ProvidersResponse {
  llm_providers: ProviderInfo[];
  embedding_providers: ProviderInfo[];
}

/**
 * Ollama模型信息接口
 */
export interface OllamaModelInfo {
  name: string;
  size: number;
  modified_at?: string;
}

/**
 * Ollama模型列表响应接口
 */
export interface OllamaModelsResponse {
  models: OllamaModelInfo[];
}

/**
 * 模型配置列表响应接口
 */
export interface ModelConfigListResponse {
  configs: ModelConfig[];
}

/**
 * Embedding配置列表响应接口
 */
export interface EmbeddingConfigListResponse {
  configs: EmbeddingConfig[];
}

/**
 * API响应基础接口
 */
export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  message?: string;
}

/**
 * 配置验证响应接口
 */
export interface ValidationResponse {
  valid: boolean;
  field?: string;
}

/**
 * 连接测试请求接口
 * 属性：config_id 配置ID（可选，用于从数据库获取真实密钥）
 */
export interface ConnectionTestRequest {
  provider_id: string;
  endpoint: string;
  api_key: string;
  model_name?: string;
  config_id?: string;  // 配置ID（可选，用于从数据库获取真实密钥）
}

/**
 * 连接测试响应接口
 */
export interface ConnectionTestResponse {
  success: boolean;
  provider_id: string;
  latency_ms: number;
  message: string;
  error?: string;
  models?: string[];
}

/**
 * Embedding连接测试请求接口
 * 属性：config_id 配置ID（可选，用于从数据库获取真实密钥）
 */
export interface EmbeddingConnectionTestRequest {
  provider_id: string;
  endpoint: string;
  api_key: string;
  model_name?: string;
  device?: string;
  config_id?: string;  // 配置ID（可选，用于从数据库获取真实密钥）
}

/**
 * Embedding连接测试响应接口
 */
export interface EmbeddingConnectionTestResponse {
  success: boolean;
  provider_id: string;
  latency_ms: number;
  message: string;
  error?: string;
  models?: string[];
}

/**
 * 本地模型列表响应接口
 */
export interface LocalModelsResponse {
  models: string[];
  base_dir: string;
}
