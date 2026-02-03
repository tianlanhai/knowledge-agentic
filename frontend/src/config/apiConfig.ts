/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：API配置管理模块
 * 内部逻辑：集中管理所有API端点配置，使用单例模式确保配置唯一性
 * 设计模式：单例模式（Singleton Pattern）
 * 设计原则：DRY原则、开闭原则
 *
 * 使用场景：
 *   - 统一管理API端点
 *   - 支持环境切换
 *   - 避免API路径硬编码
 */

/**
 * API环境类型枚举
 */
enum ApiEnvironment {
  DEVELOPMENT = 'development',
  PRODUCTION = 'production',
  TEST = 'test',
}

/**
 * API端点配置接口
 */
interface ApiEndpoints {
  /** 聊天相关端点 */
  chat: {
    completions: string;
    stream: string;
    sources: string;
    summary: string;
    compare: string;
  };
  /** 文档相关端点 */
  documents: {
    list: string;
    upload: string;
    download: string;
    delete: string;
    search: string;
  };
  /** 向量相关端点 */
  vectors: {
    ingest: string;
    search: string;
    delete: string;
  };
  /** 模型配置相关端点 */
  models: {
    list: string;
    update: string;
    test: string;
  };
  /** 对话相关端点 */
  conversations: {
    list: string;
    create: string;
    delete: string;
    clear: string;
  };
}

/**
 * API配置类
 * 设计模式：单例模式
 * 职责：
 *   1. 管理API基础URL
 *   2. 管理所有API端点
 *   3. 支持环境切换
 *   4. 提供端点路径获取
 */
class APIConfigManager {
  /** 内部变量：单例实例 */
  private static instance: APIConfigManager;

  /** 内部变量：当前环境 */
  private environment: ApiEnvironment;

  /** 内部变量：API基础URL */
  private baseUrl: string;

  /** 内部变量：API版本前缀 */
  private apiVersion: string;

  /** 内部变量：API端点配置 */
  private endpoints: ApiEndpoints;

  /**
   * 私有构造函数（单例模式）
   */
  private constructor() {
    // 内部逻辑：从环境变量读取配置，提供默认值
    this.environment = this.detectEnvironment();
    this.baseUrl = this.computeBaseUrl();
    this.apiVersion = '/api/v1';
    this.endpoints = this.initEndpoints();
  }

  /**
   * 函数级注释：获取单例实例
   * 返回值：APIConfigManager实例
   */
  static getInstance(): APIConfigManager {
    if (!APIConfigManager.instance) {
      APIConfigManager.instance = new APIConfigManager();
    }
    return APIConfigManager.instance;
  }

  /**
   * 函数级注释：检测当前环境
   * 返回值：环境类型
   * @private
   */
  private detectEnvironment(): ApiEnvironment {
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return ApiEnvironment.DEVELOPMENT;
    }
    return ApiEnvironment.PRODUCTION;
  }

  /**
   * 函数级注释：计算API基础URL
   * 返回值：基础URL字符串
   * @private
   */
  private computeBaseUrl(): string {
    // 内部逻辑：优先从环境变量读取，其次使用默认值
    const envBaseUrl = import.meta.env.VITE_API_BASE_URL;
    if (envBaseUrl) {
      return envBaseUrl;
    }

    // 内部逻辑：根据环境返回不同的基础URL
    switch (this.environment) {
      case ApiEnvironment.DEVELOPMENT:
        return 'http://localhost:8010';
      case ApiEnvironment.PRODUCTION:
        return window.location.origin;
      case ApiEnvironment.TEST:
        return 'http://test-api.example.com';
      default:
        return 'http://localhost:8010';
    }
  }

  /**
   * 函数级注释：初始化API端点配置
   * 返回值：端点配置对象
   * @private
   */
  private initEndpoints(): ApiEndpoints {
    const v = this.apiVersion;

    return {
      chat: {
        completions: `${v}/chat/completions`,
        stream: `${v}/chat/completions`,
        sources: `${v}/chat/sources`,
        summary: `${v}/chat/summary`,
        compare: `${v}/chat/compare`,
      },
      documents: {
        list: `${v}/documents`,
        upload: `${v}/documents/upload`,
        download: `${v}/documents/download`,
        delete: `${v}/documents`,
        search: `${v}/documents/search`,
      },
      vectors: {
        ingest: `${v}/vectors/ingest`,
        search: `${v}/vectors/search`,
        delete: `${v}/vectors`,
      },
      models: {
        list: `${v}/models`,
        update: `${v}/models/config`,
        test: `${v}/models/test`,
      },
      conversations: {
        list: `${v}/conversations`,
        create: `${v}/conversations`,
        delete: `${v}/conversations`,
        clear: `${v}/conversations/clear`,
      },
    };
  }

  /**
   * 函数级注释：获取完整的API URL
   * 参数：endpoint - 端点路径
   * 返回值：完整URL
   */
  getFullUrl(endpoint: string): string {
    // 内部逻辑：拼接基础URL和端点路径
    return `${this.baseUrl}${endpoint}`;
  }

  /**
   * 函数级注释：获取端点路径
   * 参数：path - 端点路径数组，如 ['chat', 'completions']
   * 返回值：端点路径字符串
   */
  getEndpoint(...path: string[]): string {
    // 内部逻辑：动态获取嵌套端点
    let endpoint: any = this.endpoints;
    for (const key of path) {
      if (endpoint && typeof endpoint === 'object' && key in endpoint) {
        endpoint = endpoint[key];
      } else {
        console.warn(`端点路径不存在: ${path.join('.')}`);
        return '';
      }
    }
    return endpoint as string;
  }

  /**
   * 函数级注释：获取聊天端点
   * 返回值：聊天端点配置
   */
  getChatEndpoints() {
    return this.endpoints.chat;
  }

  /**
   * 函数级注释：获取文档端点
   * 返回值：文档端点配置
   */
  getDocumentEndpoints() {
    return this.endpoints.documents;
  }

  /**
   * 函数级注释：获取向量端点
   * 返回值：向量端点配置
   */
  getVectorEndpoints() {
    return this.endpoints.vectors;
  }

  /**
   * 函数级注释：获取模型端点
   * 返回值：模型端点配置
   */
  getModelEndpoints() {
    return this.endpoints.models;
  }

  /**
   * 函数级注释：获取对话端点
   * 返回值：对话端点配置
   */
  getConversationEndpoints() {
    return this.endpoints.conversations;
  }

  /**
   * 函数级注释：获取所有端点配置
   * 返回值：端点配置对象
   */
  getAllEndpoints(): ApiEndpoints {
    return this.endpoints;
  }

  /**
   * 函数级注释：获取当前环境
   * 返回值：环境类型
   */
  getEnvironment(): ApiEnvironment {
    return this.environment;
  }

  /**
   * 函数级注释：获取基础URL
   * 返回值：基础URL字符串
   */
  getBaseUrl(): string {
    return this.baseUrl;
  }

  /**
   * 函数级注释：设置基础URL（用于测试或动态切换）
   * 参数：url - 新的基础URL
   */
  setBaseUrl(url: string): void {
    this.baseUrl = url;
  }

  /**
   * 函数级注释：设置环境
   * 参数：env - 环境类型
   */
  setEnvironment(env: ApiEnvironment): void {
    this.environment = env;
    this.baseUrl = this.computeBaseUrl();
  }

  /**
   * 函数级注释：检查是否为开发环境
   * 返回值：是否为开发环境
   */
  isDevelopment(): boolean {
    return this.environment === ApiEnvironment.DEVELOPMENT;
  }

  /**
   * 函数级注释：检查是否为生产环境
   * 返回值：是否为生产环境
   */
  isProduction(): boolean {
    return this.environment === ApiEnvironment.PRODUCTION;
  }
}

// 导出单例实例
export const apiConfig = APIConfigManager.getInstance();

// 导出枚举
export { ApiEnvironment };

// 导出类型
export type { ApiEndpoints };
