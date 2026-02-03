/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：缓存服务代理
 * 内部逻辑：为API服务添加缓存功能，减少重复请求
 * 设计模式：代理模式、装饰器模式
 * 设计原则：开闭原则、单一职责原则
 */

import { BaseService, type AsyncResult } from './baseService';

/**
 * 缓存配置接口
 */
interface CacheConfig {
  /** 缓存过期时间（毫秒），默认5分钟 */
  ttl?: number;
  /** 是否启用缓存，默认true */
  enabled?: boolean;
  /** 缓存键前缀 */
  keyPrefix?: string;
}

/**
 * 缓存项接口
 */
interface CacheItem<T> {
  /** 缓存数据 */
  data: T;
  /** 过期时间戳 */
  expiresAt: number;
  /** 缓存键 */
  key: string;
}

/**
 * 缓存服务代理类
 * 设计模式：代理模式 - 为真实服务添加缓存功能
 * 职责：
 *   1. 拦截服务请求
 *   2. 检查缓存是否有效
 *   3. 返回缓存数据或执行真实请求
 *   4. 更新缓存
 */
export class CachedServiceProxy extends BaseService {
  /** 属性：被代理的真实服务 */
  private realService: BaseService;

  /** 属性：缓存存储 */
  private cache: Map<string, CacheItem<any>> = new Map();

  /** 属性：缓存配置 */
  private config: Required<CacheConfig>;

  /** 属性：缓存统计 */
  private stats = {
    hits: 0,
    misses: 0,
    sets: 0,
    evictions: 0,
  };

  /**
   * 函数级注释：构造函数
   * 参数：
   *   realService - 被代理的真实服务
   *   config - 缓存配置
   */
  constructor(realService: BaseService, config: CacheConfig = {}) {
    super();
    this.realService = realService;
    this.basePath = realService.basePath;

    // 内部逻辑：设置默认配置
    this.config = {
      ttl: config.ttl ?? 5 * 60 * 1000, // 默认5分钟
      enabled: config.enabled ?? true,
      keyPrefix: config.keyPrefix ?? 'cache',
    };
  }

  /**
   * 函数级注释：生成缓存键
   * 内部逻辑：根据请求参数生成唯一键
   * 参数：path - 请求路径，params - 请求参数
   * 返回值：缓存键字符串
   */
  private generateCacheKey(path: string, params?: any): string {
    const paramsStr = params ? JSON.stringify(params) : '';
    return `${this.config.keyPrefix}:${this.basePath}:${path}:${paramsStr}`;
  }

  /**
   * 函数级注释：获取缓存
   * 参数：key - 缓存键
   * 返回值：缓存数据或null
   */
  private getCache<T>(key: string): T | null {
    const item = this.cache.get(key);

    if (!item) {
      this.stats.misses++;
      return null;
    }

    // 内部逻辑：检查是否过期
    if (Date.now() > item.expiresAt) {
      this.cache.delete(key);
      this.stats.evictions++;
      this.stats.misses++;
      return null;
    }

    this.stats.hits++;
    return item.data as T;
  }

  /**
   * 函数级注释：设置缓存
   * 参数：key - 缓存键，data - 缓存数据
   */
  private setCache<T>(key: string, data: T): void {
    const item: CacheItem<T> = {
      data,
      expiresAt: Date.now() + this.config.ttl,
      key,
    };

    this.cache.set(key, item);
    this.stats.sets++;

    // 内部逻辑：清理过期缓存（防止内存泄漏）
    this.cleanExpired();
  }

  /**
   * 函数级注释：清理过期的缓存
   */
  private cleanExpired(): void {
    const now = Date.now();
    for (const [key, item] of this.cache.entries()) {
      if (now > item.expiresAt) {
        this.cache.delete(key);
        this.stats.evictions++;
      }
    }
  }

  /**
   * 函数级注释：清除指定路径的缓存
   * 参数：pathPattern - 路径模式（支持部分匹配）
   */
  public clearCache(pathPattern?: string): void {
    if (!pathPattern) {
      this.cache.clear();
      return;
    }

    for (const key of this.cache.keys()) {
      if (key.includes(pathPattern)) {
        this.cache.delete(key);
      }
    }
  }

  /**
   * 函数级注释：获取缓存统计信息
   * 返回值：统计信息对象
   */
  public getStats() {
    return {
      ...this.stats,
      size: this.cache.size,
      hitRate: this.stats.hits / (this.stats.hits + this.stats.misses) || 0,
    };
  }

  /**
   * 函数级注释：重置统计信息
   */
  public resetStats(): void {
    this.stats = {
      hits: 0,
      misses: 0,
      sets: 0,
      evictions: 0,
    };
  }

  /**
   * 函数级注释：代理GET请求
   * 内部逻辑：先检查缓存 -> 命中则返回 -> 未命中则请求真实服务并缓存
   */
  protected async get<T>(path: string = '', params?: any): Promise<T> {
    if (!this.config.enabled) {
      return this.realService.get<T>(path, params);
    }

    const cacheKey = this.generateCacheKey(path, params);
    const cached = this.getCache<T>(cacheKey);

    if (cached !== null) {
      return cached;
    }

    const result = await this.realService.get<T>(path, params);
    this.setCache(cacheKey, result);

    return result;
  }

  /**
   * 函数级注释：代理POST请求
   * 内部逻辑：执行真实请求 -> 清除相关缓存
   */
  protected async post<T>(path: string = '', data?: any): Promise<T> {
    const result = await this.realService.post<T>(path, data);

    // 内部逻辑：POST操作后清除相关缓存
    this.clearCache(this.basePath);

    return result;
  }

  /**
   * 函数级注释：代理PUT请求
   * 内部逻辑：执行真实请求 -> 清除相关缓存
   */
  protected async put<T>(path: string = '', data?: any): Promise<T> {
    const result = await this.realService.put<T>(path, data);

    // 内部逻辑：PUT操作后清除相关缓存
    this.clearCache(this.basePath);

    return result;
  }

  /**
   * 函数级注释：代理DELETE请求
   * 内部逻辑：执行真实请求 -> 清除相关缓存
   */
  protected async delete<T>(path: string = ''): Promise<T> {
    const result = await this.realService.delete<T>(path);

    // 内部逻辑：DELETE操作后清除相关缓存
    this.clearCache(this.basePath);

    return result;
  }

  /**
   * 函数级注释：代理PATCH请求
   * 内部逻辑：执行真实请求 -> 清除相关缓存
   */
  protected async patch<T>(path: string = '', data?: any): Promise<T> {
    const result = await this.realService.patch<T>(path, data);

    // 内部逻辑：PATCH操作后清除相关缓存
    this.clearCache(this.basePath);

    return result;
  }
}

/**
 * 缓存代理工厂
 * 设计模式：工厂模式
 * 职责：创建带缓存功能的服务代理
 */
export class CachedServiceFactory {
  /** 内部变量：代理实例缓存 */
  private static proxies: Map<BaseService, CachedServiceProxy> = new Map();

  /**
   * 函数级注释：创建或获取缓存代理
   * 参数：service - 真实服务，config - 缓存配置
   * 返回值：缓存代理实例
   */
  static create<T extends BaseService>(
    service: T,
    config?: CacheConfig
  ): CachedServiceProxy & T {
    // 内部逻辑：检查是否已存在代理
    let proxy = this.proxies.get(service) as CachedServiceProxy & T;

    if (!proxy) {
      const cachedProxy = new CachedServiceProxy(service, config);
      proxy = new Proxy(cachedProxy as any, {
        get(target, prop) {
          // 内部逻辑：转发所有方法调用
          if (prop in target) {
            return target[prop as keyof typeof target];
          }
          return service[prop as keyof typeof service];
        },
      });
      this.proxies.set(service, proxy as any);
    }

    return proxy;
  }

  /**
   * 函数级注释：清除所有代理
   */
  static clearAll(): void {
    this.proxies.clear();
  }
}

// 导出快捷创建函数
/**
 * 为服务添加缓存功能的快捷函数
 * 参数：service - 真实服务，config - 缓存配置
 * 返回值：带缓存功能的服务代理
 */
export const withCache = <T extends BaseService>(
  service: T,
  config?: CacheConfig
): CachedServiceProxy & T => {
  return CachedServiceFactory.create(service, config);
};

// 导出所有公共接口
export {
  type CacheConfig,
  type CacheItem,
};
