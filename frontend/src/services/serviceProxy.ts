/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：服务代理模块
 * 内部逻辑：为服务调用添加缓存、去重、离线支持等横切关注点
 * 设计模式：代理模式（Proxy Pattern）+ 装饰器模式
 * 设计原则：单一职责原则、开闭原则
 */

import { BaseService } from './baseService';
import type { AsyncResult } from './baseService';

/**
 * 缓存配置接口
 */
export interface CacheConfig {
  /** 缓存条目 */
  data: any;
  /** 过期时间戳 */
  expiresAt: number;
  /** 缓存键 */
  key: string;
}

/**
 * 请求配置接口
 */
export interface RequestConfig {
  /** 是否启用缓存 */
  cache?: boolean;
  /** 缓存过期时间（毫秒） */
  cacheTTL?: number;
  /** 是否启用请求去重 */
  dedupe?: boolean;
  /** 是否重试 */
  retry?: boolean;
  /** 最大重试次数 */
  maxRetries?: number;
  /** 重试延迟（毫秒） */
  retryDelay?: number;
}

/**
 * 请求记录接口
 */
export interface PendingRequest {
  /** 请求 Promise */
  promise: Promise<any>;
  /** 请求时间戳 */
  timestamp: number;
}

/**
 * 统计信息接口
 */
export interface ProxyStats {
  /** 总请求数 */
  totalRequests: number;
  /** 缓存命中数 */
  cacheHits: number;
  /** 缓存未命中数 */
  cacheMisses: number;
  /** 去重命中数 */
  dedupeHits: number;
  /** 重试次数 */
  retryCount: number;
  /** 失败请求数 */
  failedRequests: number;
}

/**
 * 类：服务代理
 * 内部逻辑：包装真实服务，添加缓存、去重等功能
 * 设计模式：代理模式 - 智能引用代理
 * 泛型参数：
 *   T - 服务类型，继承自 BaseService
 */
export class ServiceProxy<T extends BaseService> {
  /** 内部变量：真实服务实例 */
  private _service: T;

  /** 内部变量：缓存存储 */
  private _cache: Map<string, CacheConfig>;

  /** 内部变量：正在进行的请求（用于去重） */
  private _pendingRequests: Map<string, PendingRequest>;

  /** 内部变量：离线存储 */
  private _offlineStorage: Map<string, any>;

  /** 内部变量：是否离线模式 */
  private _isOffline: boolean;

  /** 内部变量：默认配置 */
  private _defaultConfig: RequestConfig;

  /** 内部变量：统计信息 */
  private _stats: ProxyStats;

  /**
   * 函数级注释：构造函数
   * 参数：
   *   service - 真实服务实例
   *   defaultConfig - 默认配置
   */
  constructor(
    service: T,
    defaultConfig: RequestConfig = {
      cache: true,
      cacheTTL: 5 * 60 * 1000, // 5 分钟
      dedupe: true,
      retry: true,
      maxRetries: 2,
      retryDelay: 1000
    }
  ) {
    this._service = service;
    this._cache = new Map();
    this._pendingRequests = new Map();
    this._offlineStorage = new Map();
    this._isOffline = !navigator.onLine;
    this._defaultConfig = defaultConfig;
    this._stats = {
      totalRequests: 0,
      cacheHits: 0,
      cacheMisses: 0,
      dedupeHits: 0,
      retryCount: 0,
      failedRequests: 0
    };

    // 内部逻辑：监听在线/离线状态变化
    this._setupNetworkListener();
  }

  /**
   * 函数级注释：设置网络状态监听
   */
  private _setupNetworkListener(): void {
    const handleOnline = () => {
      this._isOffline = false;
      console.log('[ServiceProxy] 网络已连接');
      // 内部逻辑：可以在这里同步离线数据
    };

    const handleOffline = () => {
      this._isOffline = true;
      console.log('[ServiceProxy] 网络已断开，进入离线模式');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // 内部逻辑：清理函数（在组件卸载时调用）
    this._cleanupNetworkListener = () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }

  /**
   * 内部方法：清理网络监听器
   */
  private _cleanupNetworkListener: () => void = () => {};

  /**
   * 函数级注释：生成缓存键
   * 参数：
   *   method - 方法名
   *   args - 参数
   * 返回值：缓存键
   */
  private _generateCacheKey(method: string, args: any[]): string {
    // 内部逻辑：基于方法名和参数生成唯一键
    const argsStr = JSON.stringify(args);
    return `${method}:${this._hashString(argsStr)}`;
  }

  /**
   * 函数级注释：字符串哈希函数
   * 参数：
   *   str - 输入字符串
   * 返回值：哈希值
   */
  private _hashString(str: string): string {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash = hash & hash; // 转换为 32 位整数
    }
    return Math.abs(hash).toString(36);
  }

  /**
   * 函数级注释：获取缓存
   * 参数：
   *   key - 缓存键
   * 返回值：缓存值或 undefined
   */
  private _getCache(key: string): any {
    const cached = this._cache.get(key);

    if (!cached) {
      return undefined;
    }

    // 内部逻辑：检查是否过期
    if (Date.now() > cached.expiresAt) {
      this._cache.delete(key);
      return undefined;
    }

    return cached.data;
  }

  /**
   * 函数级注释：设置缓存
   * 参数：
   *   key - 缓存键
   *   data - 缓存数据
   *   ttl - 过期时间（毫秒）
   */
  private _setCache(key: string, data: any, ttl: number): void {
    this._cache.set(key, {
      key,
      data,
      expiresAt: Date.now() + ttl
    });

    // 内部逻辑：限制缓存大小
    const maxCacheSize = 100;
    if (this._cache.size > maxCacheSize) {
      // 内部逻辑：删除最旧的缓存项
      const firstKey = this._cache.keys().next().value;
      this._cache.delete(firstKey);
    }
  }

  /**
   * 函数级注释：调用服务方法
   * 参数：
   *   method - 方法名
   *   args - 参数
   *   config - 请求配置
   * 返回值：异步结果
   */
  async call<K extends keyof T>(
    method: K,
    ...args: any[]
  ): Promise<AsyncResult<any>> {
    // 内部逻辑：生成缓存键
    const cacheKey = this._generateCacheKey(String(method), args);

    // 内部逻辑：合并配置
    const config: RequestConfig = {
      ...this._defaultConfig
    };

    this._stats.totalRequests++;

    // 内部逻辑：检查是否离线
    if (this._isOffline && method !== 'get') {
      // 内部逻辑：离线模式下，尝试从缓存获取
      const cachedData = this._getCache(cacheKey);
      if (cachedData !== undefined) {
        return { success: true, data: cachedData };
      }
      return {
        success: false,
        error: { error: '网络不可用，请检查连接' }
      };
    }

    // 内部逻辑：检查缓存
    if (config.cache) {
      const cachedData = this._getCache(cacheKey);
      if (cachedData !== undefined) {
        this._stats.cacheHits++;
        console.log(`[ServiceProxy] 缓存命中: ${cacheKey}`);
        return { success: true, data: cachedData };
      }
      this._stats.cacheMisses++;
    }

    // 内部逻辑：检查去重
    if (config.dedupe) {
      const pending = this._pendingRequests.get(cacheKey);
      if (pending && Date.now() - pending.timestamp < 30000) {
        // 内部逻辑：30 秒内的相同请求复用
        this._stats.dedupeHits++;
        console.log(`[ServiceProxy] 请求去重: ${cacheKey}`);
        return await pending.promise;
      }
    }

    // 内部逻辑：创建请求 Promise
    const requestPromise = this._executeMethod(
      method,
      args,
      config,
      cacheKey
    );

    // 内部逻辑：记录待处理请求
    if (config.dedupe) {
      this._pendingRequests.set(cacheKey, {
        promise: requestPromise,
        timestamp: Date.now()
      });

      // 内部逻辑：请求完成后清理
      requestPromise.finally(() => {
        this._pendingRequests.delete(cacheKey);
      });
    }

    return await requestPromise;
  }

  /**
   * 函数级注释：执行方法
   * 参数：
   *   method - 方法名
   *   args - 参数
   *   config - 请求配置
   *   cacheKey - 缓存键
   * 返回值：异步结果
   */
  private async _executeMethod(
    method: keyof T,
    args: any[],
    config: RequestConfig,
    cacheKey: string
  ): Promise<AsyncResult<any>> {
    let lastError: any = null;
    let attempt = 0;
    const maxAttempts = (config.retry ? config.maxRetries || 0 : 0) + 1;

    while (attempt < maxAttempts) {
      try {
        // 内部逻辑：调用真实服务方法
        // eslint-disable-next-line @typescript-eslint/ban-ts-comment
        // @ts-ignore - 动态调用方法
        const result = await this._service[method](...args);

        // 内部逻辑：缓存成功结果
        if (config.cache && config.cacheTTL) {
          this._setCache(cacheKey, result, config.cacheTTL);
        }

        // 内部逻辑：存储到离线缓存
        if (method.toString().startsWith('get')) {
          this._offlineStorage.set(cacheKey, result);
        }

        return { success: true, data: result };
      } catch (error) {
        lastError = error;
        attempt++;

        // 内部逻辑：是否重试
        if (attempt < maxAttempts && config.retry) {
          this._stats.retryCount++;
          const delay = config.retryDelay || 1000;
          console.log(
            `[ServiceProxy] 请求失败，${delay}ms 后重试 (${attempt}/${maxAttempts - 1})`
          );
          await this._sleep(delay);
        }
      }
    }

    // 内部逻辑：所有重试失败
    this._stats.failedRequests++;
    console.error(`[ServiceProxy] 请求失败: ${String(method)}`, lastError);

    return {
      success: false,
      error: {
        error: lastError?.message || '请求失败',
        code: lastError?.code,
        details: lastError
      }
    };
  }

  /**
   * 函数级注释：延迟函数
   * 参数：
   *   ms - 延迟毫秒数
   */
  private _sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * 函数级注释：获取真实服务
   * 返回值：真实服务实例
   */
  getRealService(): T {
    return this._service;
  }

  /**
   * 函数级注释：获取统计信息
   * 返回值：统计信息
   */
  getStats(): ProxyStats {
    return { ...this._stats };
  }

  /**
   * 函数级注释：重置统计信息
   */
  resetStats(): void {
    this._stats = {
      totalRequests: 0,
      cacheHits: 0,
      cacheMisses: 0,
      dedupeHits: 0,
      retryCount: 0,
      failedRequests: 0
    };
  }

  /**
   * 函数级注释：清空缓存
   */
  clearCache(): void {
    this._cache.clear();
    console.log('[ServiceProxy] 缓存已清空');
  }

  /**
   * 函数级注释：设置离线模式
   * 参数：
   *   isOffline - 是否离线
   */
  setOffline(isOffline: boolean): void {
    this._isOffline = isOffline;
    console.log(`[ServiceProxy] 离线模式: ${isOffline}`);
  }

  /**
   * 函数级注释：预加载数据
   * 参数：
   *   method - 方法名
   *   args - 参数
   */
  async preload<K extends keyof T>(
    method: K,
    ...args: any[]
  ): Promise<void> {
    await this.call(method, ...args);
  }

  /**
   * 函数级注释：批量调用
   * 参数：
   *   calls - 调用配置数组
   * 返回值：结果数组
   */
  async batchCall<K extends keyof T>(
    calls: Array<{ method: K; args: any[]; config?: RequestConfig }>
  ): Promise<AsyncResult<any>[]> {
    return Promise.all(
      calls.map(({ method, args, config }) => this.call(method, ...args))
    );
  }

  /**
   * 函数级注释：销毁代理
   */
  destroy(): void {
    this._cleanupNetworkListener();
    this._cache.clear();
    this._pendingRequests.clear();
    this._offlineStorage.clear();
  }
}

/**
 * 类：服务代理工厂
 * 内部逻辑：管理和创建服务代理
 * 设计模式：工厂模式 + 单例模式
 */
export class ServiceProxyFactory {
  /** 内部变量：单例实例 */
  private static instance: ServiceProxyFactory;

  /** 内部变量：代理实例缓存 */
  private proxies: Map<string, ServiceProxy<any>>;

  /**
   * 私有构造函数
   */
  private constructor() {
    this.proxies = new Map();
  }

  /**
   * 函数级注释：获取单例实例
   * 返回值：ServiceProxyFactory 实例
   */
  static getInstance(): ServiceProxyFactory {
    if (!ServiceProxyFactory.instance) {
      ServiceProxyFactory.instance = new ServiceProxyFactory();
    }
    return ServiceProxyFactory.instance;
  }

  /**
   * 函数级注释：创建或获取代理
   * 参数：
   *   name - 代理名称
   *   service - 真实服务
   *   defaultConfig - 默认配置
   * 返回值：服务代理实例
   */
  getOrCreateProxy<T extends BaseService>(
    name: string,
    service: T,
    defaultConfig?: RequestConfig
  ): ServiceProxy<T> {
    let proxy = this.proxies.get(name) as ServiceProxy<T>;

    if (!proxy) {
      proxy = new ServiceProxy(service, defaultConfig);
      this.proxies.set(name, proxy);
      console.log(`[ServiceProxyFactory] 创建代理: ${name}`);
    }

    return proxy;
  }

  /**
   * 函数级注释：获取代理
   * 参数：
   *   name - 代理名称
   * 返回值：代理实例或 undefined
   */
  getProxy<T extends BaseService>(name: string): ServiceProxy<T> | undefined {
    return this.proxies.get(name) as ServiceProxy<T> | undefined;
  }

  /**
   * 函数级注释：移除代理
   * 参数：
   *   name - 代理名称
   */
  removeProxy(name: string): void {
    const proxy = this.proxies.get(name);
    if (proxy) {
      proxy.destroy();
      this.proxies.delete(name);
      console.log(`[ServiceProxyFactory] 移除代理: ${name}`);
    }
  }

  /**
   * 函数级注释：清空所有代理
   */
  clearAll(): void {
    this.proxies.forEach((proxy) => proxy.destroy());
    this.proxies.clear();
    console.log('[ServiceProxyFactory] 清空所有代理');
  }

  /**
   * 函数级注释：获取所有代理的统计信息
   * 返回值：统计信息字典
   */
  getAllStats(): Record<string, ProxyStats> {
    const stats: Record<string, ProxyStats> = {};
    this.proxies.forEach((proxy, name) => {
      stats[name] = proxy.getStats();
    });
    return stats;
  }
}

/**
 * 内部变量：全局服务代理工厂实例
 */
export const serviceProxyFactory = ServiceProxyFactory.getInstance();

/**
 * 高阶函数：createProxiedService
 * 内部逻辑：快速创建带代理的服务
 * 设计模式：工厂模式 + 装饰器模式
 */
export function createProxiedService<T extends BaseService>(
  name: string,
  ServiceClass: new (...args: any[]) => T,
  serviceArgs: any[] = [],
  proxyConfig?: RequestConfig
): ServiceProxy<T> {
  // 内部逻辑：创建服务实例
  const service = new ServiceClass(...serviceArgs);

  // 内部逻辑：创建代理
  return serviceProxyFactory.getOrCreateProxy(name, service, proxyConfig);
}

// 导出所有公共接口
export default ServiceProxy;
