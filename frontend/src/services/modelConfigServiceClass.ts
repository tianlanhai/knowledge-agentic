/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：模型配置服务类
 * 内部逻辑：处理LLM和Embedding模型配置的API调用，使用模板方法模式减少重复代码
 * 设计模式：模板方法模式、类继承模式
 * 设计原则：DRY原则、开闭原则
 */

import { BaseService, type AsyncResult } from './baseService';
import type {
  ModelConfig,
  ModelConfigCreate,
  ModelConfigListResponse,
  ModelConfigSafe,
  APIKeyUpdateResponse,
  EmbeddingConfig,
  EmbeddingConfigCreate,
  EmbeddingConfigListResponse,
  EmbeddingConfigSafe,
  ProvidersResponse,
  OllamaModelsResponse,
  ConnectionTestRequest,
  ConnectionTestResponse,
  EmbeddingConnectionTestRequest,
  EmbeddingConnectionTestResponse,
  LocalModelsResponse,
} from '../types/modelConfig';

/**
 * LLM模型配置服务类
 * 设计模式：模板方法模式 - 继承BaseService使用通用模板
 * 职责：
 *   1. 管理LLM模型配置的CRUD操作
 *   2. 提供安全的错误处理
 *   3. 支持默认配置设置
 */
export class LLMConfigService extends BaseService {
  /** 属性：服务基础路径 */
  protected basePath = '/model-config/llm';

  /**
   * 函数级注释：获取LLM模型配置列表
   * 内部逻辑：使用基类的get方法
   * 返回值：Promise<ModelConfigListResponse> - 配置列表响应
   */
  async getConfigs(): Promise<ModelConfigListResponse> {
    return this.get<ModelConfigListResponse>('');
  }

  /**
   * 函数级注释：保存LLM模型配置
   * 内部逻辑：使用基类的create方法
   * 参数：config - 配置数据
   * 返回值：Promise<ModelConfig> - 保存后的配置对象
   */
  async saveConfig(config: ModelConfigCreate): Promise<ModelConfig> {
    return this.create<ModelConfig>(config);
  }

  /**
   * 函数级注释：设置默认LLM模型（触发热切换）
   * 参数：configId - 配置ID
   * 返回值：Promise<ModelConfig> - 更新后的配置对象
   */
  async setDefault(configId: string): Promise<ModelConfig> {
    return this.post<ModelConfig>(`/${configId}/set-default`);
  }

  /**
   * 函数级注释：删除LLM模型配置
   * 内部逻辑：使用基类的remove方法
   * 参数：configId - 配置ID
   * 返回值：Promise<{ deleted: boolean }> - 删除成功标识
   */
  async deleteConfig(configId: string): Promise<{ deleted: boolean }> {
    return this.delete<{ deleted: boolean }>(`/${configId}`);
  }

  /**
   * 函数级注释：测试LLM配置连接
   * 参数：request - 测试请求配置
   * 返回值：Promise<ConnectionTestResponse> - 测试结果响应
   */
  async testConnection(request: ConnectionTestRequest): Promise<ConnectionTestResponse> {
    return this.post<ConnectionTestResponse>('/test', request);
  }

  /**
   * 函数级注释：更新LLM配置的API密钥
   * 参数：configId - 配置ID，apiKey - 新的API密钥
   * 返回值：Promise<APIKeyUpdateResponse> - 更新后的脱敏密钥响应
   */
  async updateAPIKey(configId: string, apiKey: string): Promise<APIKeyUpdateResponse> {
    return this.put<APIKeyUpdateResponse>(`/${configId}/api-key`, { api_key: apiKey });
  }

  /**
   * 函数级注释：安全地获取配置（带错误处理）
   * 内部逻辑：使用基类的safeAsync方法包装错误
   * 返回值：Promise<AsyncResult<ModelConfigListResponse>> - Result模式包装的结果
   */
  async safeGetConfigs(): Promise<AsyncResult<ModelConfigListResponse>> {
    return this.safeAsync(() => this.getConfigs(), '获取LLM配置失败');
  }

  /**
   * 函数级注释：安全地保存配置（带错误处理）
   * 参数：config - 配置数据
   * 返回值：Promise<AsyncResult<ModelConfig>> - Result模式包装的结果
   */
  async safeSaveConfig(config: ModelConfigCreate): Promise<AsyncResult<ModelConfig>> {
    return this.safeAsync(() => this.saveConfig(config), '保存LLM配置失败');
  }

  /**
   * 函数级注释：安全地删除配置（带错误处理）
   * 参数：configId - 配置ID
   * 返回值：Promise<AsyncResult<{ deleted: boolean }>> - Result模式包装的结果
   */
  async safeDeleteConfig(configId: string): Promise<AsyncResult<{ deleted: boolean }>> {
    return this.safeAsync(() => this.deleteConfig(configId), '删除LLM配置失败');
  }
}

/**
 * Embedding模型配置服务类
 * 设计模式：模板方法模式 - 继承BaseService使用通用模板
 * 职责：
 *   1. 管理Embedding模型配置的CRUD操作
 *   2. 提供安全的错误处理
 *   3. 支持默认配置设置
 */
export class EmbeddingConfigService extends BaseService {
  /** 属性：服务基础路径 */
  protected basePath = '/model-config/embedding';

  /**
   * 函数级注释：获取Embedding配置列表
   * 返回值：Promise<EmbeddingConfigListResponse> - 配置列表响应
   */
  async getConfigs(): Promise<EmbeddingConfigListResponse> {
    return this.get<EmbeddingConfigListResponse>('');
  }

  /**
   * 函数级注释：保存Embedding配置
   * 参数：config - 配置数据
   * 返回值：Promise<EmbeddingConfig> - 保存后的配置对象
   */
  async saveConfig(config: EmbeddingConfigCreate): Promise<EmbeddingConfig> {
    return this.create<EmbeddingConfig>(config);
  }

  /**
   * 函数级注释：设置默认Embedding（触发热切换）
   * 参数：configId - 配置ID
   * 返回值：Promise<EmbeddingConfig> - 更新后的配置对象
   */
  async setDefault(configId: string): Promise<EmbeddingConfig> {
    return this.post<EmbeddingConfig>(`/${configId}/set-default`);
  }

  /**
   * 函数级注释：删除Embedding模型配置
   * 参数：configId - 配置ID
   * 返回值：Promise<{ deleted: boolean }> - 删除成功标识
   */
  async deleteConfig(configId: string): Promise<{ deleted: boolean }> {
    return this.delete<{ deleted: boolean }>(`/${configId}`);
  }

  /**
   * 函数级注释：测试Embedding配置连接
   * 参数：request - 测试请求配置
   * 返回值：Promise<EmbeddingConnectionTestResponse> - 测试结果响应
   */
  async testConnection(request: EmbeddingConnectionTestRequest): Promise<EmbeddingConnectionTestResponse> {
    return this.post<EmbeddingConnectionTestResponse>('/test', request);
  }

  /**
   * 函数级注释：更新Embedding配置的API密钥
   * 参数：configId - 配置ID，apiKey - 新的API密钥
   * 返回值：Promise<APIKeyUpdateResponse> - 更新后的脱敏密钥响应
   */
  async updateAPIKey(configId: string, apiKey: string): Promise<APIKeyUpdateResponse> {
    return this.put<APIKeyUpdateResponse>(`/${configId}/api-key`, { api_key: apiKey });
  }

  /**
   * 函数级注释：安全地获取配置（带错误处理）
   * 返回值：Promise<AsyncResult<EmbeddingConfigListResponse>> - Result模式包装的结果
   */
  async safeGetConfigs(): Promise<AsyncResult<EmbeddingConfigListResponse>> {
    return this.safeAsync(() => this.getConfigs(), '获取Embedding配置失败');
  }
}

/**
 * 模型配置辅助服务类
 * 设计模式：模板方法模式
 * 职责：处理提供商、模型列表等辅助功能
 */
export class ModelConfigHelperService extends BaseService {
  /** 属性：服务基础路径 */
  protected basePath = '/model-config';

  /**
   * 函数级注释：获取支持的提供商列表
   * 返回值：Promise<ProvidersResponse> - 提供商列表响应
   */
  async getProviders(): Promise<ProvidersResponse> {
    return this.get<ProvidersResponse>('/providers');
  }

  /**
   * 函数级注释：获取Ollama可用模型列表
   * 返回值：Promise<OllamaModelsResponse> - 模型列表响应
   */
  async getOllamaModels(): Promise<OllamaModelsResponse> {
    return this.get<OllamaModelsResponse>('/ollama/models');
  }

  /**
   * 函数级注释：拉取Ollama模型
   * 参数：modelName - 模型名称（如 llama3:8b）
   * 返回值：Promise<{ model_name: string; message: string }> - 拉取结果
   */
  async pullOllamaModel(modelName: string): Promise<{ model_name: string; message: string }> {
    return this.post<{ model_name: string; message: string }>('/ollama/pull', null, {
      params: { model_name: modelName }
    });
  }

  /**
   * 函数级注释：验证配置有效性
   * 参数：config - 待验证的配置
   * 返回值：Promise<{ valid: boolean; field?: string }> - 验证结果
   */
  async validateConfig(config: ModelConfigCreate): Promise<{
    valid: boolean;
    field?: string;
  }> {
    return this.post<{ valid: boolean; field?: string }>('/validate', config);
  }

  /**
   * 函数级注释：获取本地Embedding模型列表
   * 返回值：Promise<LocalModelsResponse> - 本地模型列表响应
   */
  async getLocalModels(): Promise<LocalModelsResponse> {
    return this.get<LocalModelsResponse>('/local/models');
  }
}

/**
 * 模型配置服务聚合器
 * 设计模式：外观模式 - 提供统一的访问入口
 * 职责：聚合所有模型配置相关的服务
 */
export class ModelConfigServiceFacade {
  /** 属性：LLM配置服务实例 */
  public readonly llm: LLMConfigService;

  /** 属性：Embedding配置服务实例 */
  public readonly embedding: EmbeddingConfigService;

  /** 属性：辅助服务实例 */
  public readonly helper: ModelConfigHelperService;

  constructor() {
    this.llm = new LLMConfigService();
    this.embedding = new EmbeddingConfigService();
    this.helper = new ModelConfigHelperService();
  }
}

// 导出单例实例
export const modelConfigService = new ModelConfigServiceFacade();
