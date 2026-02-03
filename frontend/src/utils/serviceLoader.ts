/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：服务加载器模块
 * 内部逻辑：提供统一的服务动态导入和缓存机制，消除重复的动态导入代码
 * 设计模式：单例模式、享元模式
 * 设计原则：DRY（不重复）、懒加载
 */

/**
 * 服务加载器类
 * 设计模式：单例模式、享元模式
 * 职责：
 *   1. 统一管理服务的动态导入
 *   2. 缓存已加载的服务模块
 *   3. 提供类型安全的服务获取方法
 */
class ServiceLoaderClass {
  /** 内部变量：单例实例 */
  private static instance: ServiceLoaderClass;

  /** 内部变量：服务模块缓存（享元模式） */
  private cache = new Map<string, any>();

  /** 内部变量：正在加载的Promise缓存（防止重复加载） */
  private loadingPromises = new Map<string, Promise<any>>();

  /** 私有构造函数（单例模式） */
  private constructor() {}

  /**
   * 函数级注释：获取单例实例
   * 返回值：ServiceLoaderClass 单例实例
   */
  static getInstance(): ServiceLoaderClass {
    if (!ServiceLoaderClass.instance) {
      ServiceLoaderClass.instance = new ServiceLoaderClass();
    }
    return ServiceLoaderClass.instance;
  }

  /**
   * 函数级注释：加载服务模块（支持缓存）
   * 内部逻辑：检查缓存 -> 检查正在加载的Promise -> 动态导入 -> 缓存结果
   * 参数：
   *   serviceName - 服务名称（如 'chatService'）
   *   forceReload - 是否强制重新加载（默认false）
   * 返回值：服务模块的Promise
   *
   * @example
   * const { chatService } = await ServiceLoader.load('chatService');
   */
  async load<T = any>(serviceName: string, forceReload = false): Promise<T> {
    // 内部逻辑：强制重新加载时清除缓存
    if (forceReload) {
      this.cache.delete(serviceName);
      this.loadingPromises.delete(serviceName);
    }

    // 内部逻辑：返回缓存结果（享元模式）
    if (this.cache.has(serviceName)) {
      return this.cache.get(serviceName) as T;
    }

    // 内部逻辑：返回正在加载的Promise（防止重复加载）
    if (this.loadingPromises.has(serviceName)) {
      return this.loadingPromises.get(serviceName) as Promise<T>;
    }

    // 内部逻辑：动态导入并缓存
    const loadPromise = import(`../services/${serviceName}`)
      .then((module) => {
        this.cache.set(serviceName, module);
        this.loadingPromises.delete(serviceName);
        return module as T;
      })
      .catch((error) => {
        this.loadingPromises.delete(serviceName);
        throw new Error(`加载服务失败: ${serviceName} - ${error.message}`);
      });

    this.loadingPromises.set(serviceName, loadPromise);
    return loadPromise;
  }

  /**
   * 函数级注释：预加载多个服务
   * 内部逻辑：并发加载多个服务模块
   * 参数：
   *   serviceNames - 服务名称数组
   * 返回值：所有服务加载完成的Promise
   *
   * @example
   * await ServiceLoader.preload(['chatService', 'conversationService']);
   */
  async preload(serviceNames: string[]): Promise<void> {
    await Promise.all(
      serviceNames.map((name) => this.load(name))
    );
  }

  /**
   * 函数级注释：清除指定服务的缓存
   * 参数：
   *   serviceName - 服务名称（不传则清除所有缓存）
   */
  clearCache(serviceName?: string): void {
    if (serviceName) {
      this.cache.delete(serviceName);
      this.loadingPromises.delete(serviceName);
    } else {
      this.cache.clear();
      this.loadingPromises.clear();
    }
  }

  /**
   * 函数级注释：检查服务是否已缓存
   * 参数：
   *   serviceName - 服务名称
   * 返回值：是否已缓存
   */
  isCached(serviceName: string): boolean {
    return this.cache.has(serviceName);
  }

  /**
   * 函数级注释：获取已缓存的服务的数量
   * 返回值：缓存数量
   */
  getCacheSize(): number {
    return this.cache.size;
  }
}

// 导出单例实例
export const ServiceLoader = ServiceLoaderClass.getInstance();

/**
 * 函数级注释：便捷的服务加载函数
 * 参数：
 *   serviceName - 服务名称
 * 返回值：服务模块的Promise
 *
 * @example
 * const { chatService } = await loadService('chatService');
 */
export async function loadService<T = any>(serviceName: string): Promise<T> {
  return ServiceLoader.load<T>(serviceName);
}

/**
 * 函数级注释：服务加载Hook（用于React组件）
 * 返回值：包含加载状态、加载函数和清除缓存函数的对象
 *
 * @example
 * const { load, isLoading, clearCache } = useServiceLoader();
 */
export function useServiceLoader() {
  return {
    /**
     * 加载服务
     */
    load: ServiceLoader.load.bind(ServiceLoader),

    /**
     * 预加载多个服务
     */
    preload: ServiceLoader.preload.bind(ServiceLoader),

    /**
     * 清除缓存
     */
    clearCache: ServiceLoader.clearCache.bind(ServiceLoader),

    /**
     * 检查是否已缓存
     */
    isCached: ServiceLoader.isCached.bind(ServiceLoader),

    /**
     * 获取缓存大小
     */
    getCacheSize: ServiceLoader.getCacheSize.bind(ServiceLoader),
  };
}
