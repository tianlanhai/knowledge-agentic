/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：API 服务基类
 * 内部逻辑：提供统一的 API 调用模板和错误处理
 * 设计模式：模板方法模式、工厂模式、装饰器模式
 * 设计原则：DRY、开闭原则
 */

import api from './api';

/**
 * 分页请求参数接口
 */
interface PaginationParams {
  page?: number;
  page_size?: number;
  skip?: number;
  limit?: number;
}

/**
 * 分页响应接口
 */
interface PaginationResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

/**
 * 错误响应类型
 */
export interface ServiceError<T = any> {
  error: string;
  code?: string;
  details?: T;
}

/**
 * 异步操作结果类型（Result模式）
 */
export type AsyncResult<T, E = ServiceError> =
  | { success: true; data: T; error?: never }
  | { success: false; data?: never; error: E };

/**
 * API 服务基类
 * 设计模式：模板方法模式、装饰器模式
 * 职责：
 *   1. 定义 API 调用的通用模板方法
 *   2. 提供统一的错误处理
 *   3. 提供分页查询的通用实现
 *   4. 支持Result模式的错误处理
 */
export abstract class BaseService {
  /**
   * 属性：服务基础路径（子类必须实现）
   */
  protected abstract basePath: string;

  /**
   * 函数级注释：获取完整路径
   * 参数：
   *   path - 相对路径
   * 返回值：完整路径
   */
  protected getFullPath(path: string = ''): string {
    const fullPath = `${this.basePath}${path}`;
    // 内部逻辑：确保路径格式正确
    return fullPath.replace(/\/+/g, '/').replace(/\/$/, '') || '/';
  }

  /**
   * 函数级注释：通用 GET 请求（模板方法）
   * 参数：
   *   path - 请求路径
   *   params - 查询参数
   * 返回值：Promise<T>
   */
  protected async get<T>(path: string = '', params?: any): Promise<T> {
    return api.get(this.getFullPath(path), { params });
  }

  /**
   * 函数级注释：通用 POST 请求（模板方法）
   * 参数：
   *   path - 请求路径
   *   data - 请求体
   * 返回值：Promise<T>
   */
  protected async post<T>(path: string = '', data?: any): Promise<T> {
    return api.post(this.getFullPath(path), data);
  }

  /**
   * 函数级注释：通用 PUT 请求（模板方法）
   * 参数：
   *   path - 请求路径
   *   data - 请求体
   * 返回值：Promise<T>
   */
  protected async put<T>(path: string = '', data?: any): Promise<T> {
    return api.put(this.getFullPath(path), data);
  }

  /**
   * 函数级注释：通用 PATCH 请求（模板方法）
   * 参数：
   *   path - 请求路径
   *   data - 请求体
   * 返回值：Promise<T>
   */
  protected async patch<T>(path: string = '', data?: any): Promise<T> {
    return api.patch(this.getFullPath(path), data);
  }

  /**
   * 函数级注释：通用 DELETE 请求（模板方法）
   * 参数：
   *   path - 请求路径
   * 返回值：Promise<T>
   */
  protected async delete<T>(path: string = ''): Promise<T> {
    return api.delete(this.getFullPath(path));
  }

  /**
   * 函数级注释：分页查询（模板方法）
   * 参数：
   *   params - 分页参数
   * 返回值：Promise<PaginationResponse<T>>
   */
  protected async getPaginated<T>(
    params?: PaginationParams
  ): Promise<PaginationResponse<T>> {
    return this.get<PaginationResponse<T>>('', params);
  }

  /**
   * 函数级注释：按 ID 获取单个资源
   * 参数：
   *   id - 资源 ID
   * 返回值：Promise<T>
   */
  protected async getById<T>(id: string | number): Promise<T> {
    return this.get<T>(`/${id}`);
  }

  /**
   * 函数级注释：创建资源
   * 参数：
   *   data - 资源数据
   * 返回值：Promise<T>
   */
  async create<T>(data: any): Promise<T> {
    return this.post<T>('', data);
  }

  /**
   * 函数级注释：更新资源
   * 参数：
   *   id - 资源 ID
   *   data - 更新数据
   * 返回值：Promise<T>
   */
  async update<T>(id: string | number, data: any): Promise<T> {
    return this.put<T>(`/${id}`, data);
  }

  /**
   * 函数级注释：删除资源
   * 参数：
   *   id - 资源 ID
   * 返回值：Promise<void>
   */
  async remove(id: string | number): Promise<void> {
    return this.delete(`/${id}`);
  }

  /**
   * 函数级注释：统一的错误处理方法（装饰器模式）
   * 内部逻辑：捕获异常 -> 提取错误信息 -> 返回统一格式
   * 参数：
   *   fn - 异步函数
   *   defaultErrorMessage - 默认错误消息
   * 返回值：AsyncResult包装的结果
   *
   * @example
   * const result = await this.safeAsync(
   *   () => this.get('/resource'),
   *   '获取资源失败'
   * );
   * if (result.success) {
   *   console.log(result.data);
   * } else {
   *   console.error(result.error);
   * }
   */
  protected async safeAsync<T>(
    fn: () => Promise<T>,
    defaultErrorMessage: string = '操作失败'
  ): Promise<AsyncResult<T>> {
    try {
      const data = await fn();
      return { success: true, data };
    } catch (error: any) {
      // 内部逻辑：提取错误信息
      const errorMessage =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        error?.message ||
        defaultErrorMessage;

      return {
        success: false,
        error: {
          error: errorMessage,
          code: error?.response?.status?.toString(),
          details: error?.response?.data,
        },
      };
    }
  }

  /**
   * 函数级注释：带重试的异步操作
   * 内部逻辑：执行操作 -> 失败时重试 -> 达到最大次数后返回错误
   * 参数：
   *   fn - 异步函数
   *   maxRetries - 最大重试次数（默认1）
   *   delay - 重试延迟毫秒数（默认1000）
   * 返回值：AsyncResult包装的结果
   */
  protected async retryAsync<T>(
    fn: () => Promise<T>,
    maxRetries: number = 1,
    delay: number = 1000
  ): Promise<AsyncResult<T>> {
    let lastError: ServiceError | undefined;

    for (let i = 0; i <= maxRetries; i++) {
      const result = await this.safeAsync(fn);
      if (result.success) {
        return result;
      }
      lastError = result.error;

      // 内部逻辑：如果不是最后一次重试，则等待后重试
      if (i < maxRetries) {
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }

    return { success: false, error: lastError! };
  }

  /**
   * 函数级注释：批量执行异步操作（并行）
   * 内部逻辑：并发执行多个操作 -> 收集成功和失败的结果 -> 返回汇总
   * 参数：
   *   items - 待处理的项目数组
   *   fn - 处理函数
   * 返回值：成功和失败的结果数组
   */
  protected async batchAsync<T, R>(
    items: T[],
    fn: (item: T, index: number) => Promise<R>
  ): Promise<{
    successes: Array<{ item: T; result: R; index: number }>;
    failures: Array<{ item: T; error: ServiceError; index: number }>;
  }> {
    const results = await Promise.allSettled(
      items.map((item, index) => fn(item, index))
    );

    const successes: Array<{ item: T; result: R; index: number }> = [];
    const failures: Array<{ item: T; error: ServiceError; index: number }> = [];

    results.forEach((result, index) => {
      if (result.status === 'fulfilled') {
        successes.push({ item: items[index], result: result.value, index });
      } else {
        failures.push({
          item: items[index],
          error: { error: result.reason?.message || '处理失败' },
          index,
        });
      }
    });

    return { successes, failures };
  }
}

/**
 * 服务工厂类
 * 设计模式：工厂模式、单例模式
 * 职责：管理和创建服务实例
 */
class ServiceFactory {
  /** 内部变量：单例实例 */
  private static instance: ServiceFactory;

  /** 内部变量：服务实例缓存 */
  private services: Map<string, BaseService> = new Map();

  /** 私有构造函数 */
  private constructor() {}

  /**
   * 函数级注释：获取单例实例
   */
  static getInstance(): ServiceFactory {
    if (!ServiceFactory.instance) {
      ServiceFactory.instance = new ServiceFactory();
    }
    return ServiceFactory.instance;
  }

  /**
   * 函数级注释：注册服务
   * 参数：
   *   name - 服务名称
   *   service - 服务实例
   */
  registerService(name: string, service: BaseService): void {
    this.services.set(name, service);
  }

  /**
   * 函数级注释：获取服务
   * 参数：
   *   name - 服务名称
   * 返回值：服务实例
   */
  getService<T extends BaseService>(name: string): T | undefined {
    return this.services.get(name) as T;
  }

  /**
   * 函数级注释：创建或获取服务（懒加载）
   * 参数：
   *   name - 服务名称
   *   factory - 服务工厂函数
   * 返回值：服务实例
   */
  getOrCreateService<T extends BaseService>(
    name: string,
    factory: () => T
  ): T {
    let service = this.getService<T>(name);
    if (!service) {
      service = factory();
      this.registerService(name, service);
    }
    return service;
  }
}

// 导出服务工厂单例
export const serviceFactory = ServiceFactory.getInstance();
