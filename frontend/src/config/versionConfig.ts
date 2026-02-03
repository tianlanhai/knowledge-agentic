/**
 * 上海宇羲伏天智能科技有限公司出品
 *
/**
 * 文件级注释：镜像版本配置限制模块
 * 内部逻辑：根据后端返回的版本信息限制前端UI显示的配置选项
 *
 * 设计原则：
 * - 第一性原理：镜像版本决定了UI能显示和配置的选项
 * - 单一职责：只负责版本相关的UI限制逻辑
 * - 开闭原则：新增版本时只需添加枚举和映射
 */

/**
 * 镜像版本枚举
 */
export enum ImageVersion {
  V1 = "v1",  // 云LLM + 本地向量
  V2 = "v2",  // 云LLM + 云端向量
  V3 = "v3",  // 本地LLM + 本地向量
  V4 = "v4",  // 本地LLM + 云端向量
}

/**
 * 版本能力接口
 */
export interface VersionCapability {
  /** 镜像版本 */
  version: ImageVersion;
  /** 版本描述 */
  description: string;
  /** 支持的LLM提供商列表 */
  supported_llm_providers: string[];
  /** 支持的Embedding提供商列表 */
  supported_embedding_providers: string[];
  /** 是否支持本地Embedding */
  supports_local_embedding: boolean;
  /** 是否为云LLM版本 */
  is_cloud_llm: boolean;
  /** 是否为本地LLM版本 */
  is_local_llm: boolean;
}

/**
 * LLM提供商类型定义
 */
export interface LLMProvider {
  /** 提供商ID */
  id: string;
  /** 提供商名称 */
  name: string;
  /** 是否支持 */
  supported: boolean;
}

/**
 * Embedding提供商类型定义
 */
export interface EmbeddingProvider {
  /** 提供商ID */
  id: string;
  /** 提供商名称 */
  name: string;
  /** 是否支持 */
  supported: boolean;
}

/**
 * 版本能力映射表（内部变量）
 * 用于前端兜底展示，实际能力以后端API返回为准
 */
export const VERSION_CAPABILITIES: Record<ImageVersion, VersionCapability> = {
  [ImageVersion.V1]: {
    version: ImageVersion.V1,
    description: "云LLM + 本地向量",
    supported_llm_providers: ["zhipuai", "minimax", "moonshot", "openai"],
    supported_embedding_providers: ["local"],
    supports_local_embedding: true,
    is_cloud_llm: true,
    is_local_llm: false,
  },
  [ImageVersion.V2]: {
    version: ImageVersion.V2,
    description: "云LLM + 云端向量",
    supported_llm_providers: ["zhipuai", "minimax", "moonshot", "openai"],
    supported_embedding_providers: ["zhipuai", "openai"],
    supports_local_embedding: false,
    is_cloud_llm: true,
    is_local_llm: false,
  },
  [ImageVersion.V3]: {
    version: ImageVersion.V3,
    description: "本地LLM + 本地向量",
    supported_llm_providers: ["ollama"],
    supported_embedding_providers: ["local"],
    supports_local_embedding: true,
    is_cloud_llm: false,
    is_local_llm: true,
  },
  [ImageVersion.V4]: {
    version: ImageVersion.V4,
    description: "本地LLM + 云端向量",
    supported_llm_providers: ["ollama"],
    supported_embedding_providers: ["zhipuai", "openai"],
    supports_local_embedding: false,
    is_cloud_llm: false,
    is_local_llm: true,
  },
};

/**
 * LLM提供商名称映射（内部变量）
 */
export const LLM_PROVIDER_NAMES: Record<string, string> = {
  zhipuai: "智谱AI",
  minimax: "MiniMax",
  moonshot: "月之暗面",
  openai: "OpenAI",
  ollama: "Ollama (本地)",
};

/**
 * Embedding提供商名称映射（内部变量）
 */
export const EMBEDDING_PROVIDER_NAMES: Record<string, string> = {
  zhipuai: "智谱AI",
  openai: "OpenAI",
  local: "本地模型",
};

/**
 * 当前版本能力（运行时从后端获取）
 */
let currentCapability: VersionCapability | null = null;

/**
 * 获取指定版本的能力信息
 * @param version - 镜像版本
 * @returns 版本能力对象
 */
export function getVersionCapability(version: ImageVersion): VersionCapability {
  return VERSION_CAPABILITIES[version];
}

/**
 * 设置当前版本能力（从后端API获取后调用）
 * @param capability - 版本能力对象
 */
export function setCurrentCapability(capability: VersionCapability): void {
  currentCapability = capability;
}

/**
 * 获取当前版本能力
 * @returns 当前版本能力对象，未设置则返回默认V1版本
 */
export function getCurrentCapability(): VersionCapability {
  return currentCapability || VERSION_CAPABILITIES[ImageVersion.V1];
}

/**
 * 检查LLM提供商是否被当前版本支持
 * @param provider - LLM提供商ID
 * @param version - 镜像版本，默认为当前版本
 * @returns 是否支持
 */
export function isLlmProviderSupported(
  provider: string,
  version?: ImageVersion
): boolean {
  const capability = version
    ? VERSION_CAPABILITIES[version]
    : getCurrentCapability();
  return capability.supported_llm_providers.includes(provider);
}

/**
 * 检查Embedding提供商是否被当前版本支持
 * @param provider - Embedding提供商ID
 * @param version - 镜像版本，默认为当前版本
 * @returns 是否支持
 */
export function isEmbeddingProviderSupported(
  provider: string,
  version?: ImageVersion
): boolean {
  const capability = version
    ? VERSION_CAPABILITIES[version]
    : getCurrentCapability();
  return capability.supported_embedding_providers.includes(provider);
}

/**
 * 获取支持的LLM提供商列表
 * @param allProviders - 所有可用提供商列表
 * @returns 过滤后的提供商列表
 */
export function getSupportedLlmProviders(
  allProviders: LLMProvider[]
): LLMProvider[] {
  const capability = getCurrentCapability();
  return allProviders.map((p) => ({
    ...p,
    supported: capability.supported_llm_providers.includes(p.id),
  }));
}

/**
 * 获取支持的Embedding提供商列表
 * @param allProviders - 所有可用提供商列表
 * @returns 过滤后的提供商列表
 */
export function getSupportedEmbeddingProviders(
  allProviders: EmbeddingProvider[]
): EmbeddingProvider[] {
  const capability = getCurrentCapability();
  return allProviders.map((p) => ({
    ...p,
    supported: capability.supported_embedding_providers.includes(p.id),
  }));
}

/**
 * 获取LLM提供商显示名称
 * @param providerId - 提供商ID
 * @returns 显示名称
 */
export function getLlmProviderName(providerId: string): string {
  return LLM_PROVIDER_NAMES[providerId] || providerId;
}

/**
 * 获取Embedding提供商显示名称
 * @param providerId - 提供商ID
 * @returns 显示名称
 */
export function getEmbeddingProviderName(providerId: string): string {
  return EMBEDDING_PROVIDER_NAMES[providerId] || providerId;
}

/**
 * 检查当前版本是否支持本地Embedding
 * @returns 是否支持本地Embedding
 */
export function supportsLocalEmbedding(): boolean {
  return getCurrentCapability().supports_local_embedding;
}

/**
 * 检查当前版本是否为云LLM版本
 * @returns 是否为云LLM版本
 */
export function isCloudLlmVersion(): boolean {
  return getCurrentCapability().is_cloud_llm;
}

/**
 * 检查当前版本是否为本地LLM版本
 * @returns 是否为本地LLM版本
 */
export function isLocalLlmVersion(): boolean {
  return getCurrentCapability().is_local_llm;
}

/**
 * 版本配置Hook类型定义
 */
export interface VersionConfigState {
  /** 当前版本能力 */
  capability: VersionCapability | null;
  /** 是否正在加载 */
  loading: boolean;
  /** 错误信息 */
  error: string | null;
}

/**
 * 版本配置Service
 */
export const versionConfigService = {
  /**
   * 从后端获取版本信息
   */
  async fetchVersionInfo(): Promise<VersionCapability> {
    const response = await fetch("/api/v1/version/info");
    if (!response.ok) {
      throw new Error("获取版本信息失败");
    }
    const result = await response.json();
    const capability = result.data as VersionCapability;
    setCurrentCapability(capability);
    return capability;
  },

  /**
   * 验证配置是否与当前版本兼容
   */
  async validateConfig(
    llmProvider: string,
    embeddingProvider: string
  ): Promise<{ valid: boolean; message: string }> {
    const params = new URLSearchParams();
    if (llmProvider) params.append("llm_provider", llmProvider);
    if (embeddingProvider) params.append("embedding_provider", embeddingProvider);

    const response = await fetch(`/api/v1/version/validate?${params}`);
    if (!response.ok) {
      throw new Error("验证配置失败");
    }
    const result = await response.json();
    return result.data;
  },
};
