/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：React Query 客户端配置模块
 * 内部逻辑：配置 TanStack Query 用于服务端状态管理
 * 设计模式：单例模式 + 工厂模式
 * 设计原则：SOLID - 单一职责原则
 *
 * @package frontend/src/core
 */

import { QueryClient, QueryClientConfig, defaultOptions } from '@tanstack/react-query';
import { AxiosError } from 'axios';

/**
 * 类级注释：查询键工厂
 * 设计模式：工厂模式
 * 职责：统一管理所有查询键，避免硬编码和重复
 *
 * @example
 * ```typescript
 * // 获取所有文档的查询键
 * queryKeys.documents.all()
 *
 * // 获取单个文档的查询键
 * queryKeys.documents.detail(123)
 *
 * // 获取文档列表的查询键（带过滤）
 * queryKeys.documents.list({ status: 'active' })
 * ```
 */
export class QueryKeyFactory {
  /**
   * 函数级注释：创建基础查询键
   * 参数：
   *   base - 基础路径
   * 返回值：查询键构建器
   */
  static create<T extends Record<string, any>>(base: string) {
    return {
      /** 内部属性：所有数据的查询键 */
      all: () => [base] as const,
      /** 内部属性：列表数据的查询键 */
      list: (filters?: T) => [base, 'list', filters] as const,
      /** 内部属性：详情数据的查询键 */
      detail: (id: string | number) => [base, 'detail', id] as const,
    };
  }
}

/**
 * 变量：应用查询键
 * 内部逻辑：集中管理所有查询键
 */
export const queryKeys = {
  /** 文档相关查询键 */
  documents: QueryKeyFactory.create<{ status?: string; search?: string }>('documents'),

  /** 对话相关查询键 */
  conversations: QueryKeyFactory.create<{ limit?: number }>('conversations'),

  /** 聊天消息相关查询键 */
  messages: (conversationId: string) => QueryKeyFactory.create<{ limit?: number }>(`conversations/${conversationId}/messages`),

  /** 模型配置相关查询键 */
  modelConfigs: QueryKeyFactory.create<{}>('model-configs'),

  /** 搜索结果相关查询键 */
  search: QueryKeyFactory.create<{ query: string; filters?: Record<string, any> }>('search'),

  /** 摄入任务相关查询键 */
  ingestTasks: QueryKeyFactory.create<{ status?: string }>('ingest-tasks'),
};

/**
 * 接口：查询错误类型
 */
export interface QueryError {
  /** 错误消息 */
  message: string;
  /** 错误代码 */
  code?: string;
  /** 错误详情 */
  details?: unknown;
  /** HTTP 状态码 */
  status?: number;
}

/**
 * 函数级注释：判断是否为网络错误
 * 参数：
 *   error - 错误对象
 * 返回值：是否为网络错误
 */
function isNetworkError(error: Error): boolean {
  return (
    error.message.includes('Network Error') ||
    error.message.includes('timeout') ||
    !navigator.onLine
  );
}

/**
 * 函数级注释：查询错误处理函数
 * 参数：
 *   error - 错误对象
 * 返回值：标准化后的错误对象
 */
function handleQueryError(error: Error): QueryError {
  // 内部逻辑：检查是否为 Axios 错误
  if (error instanceof AxiosError) {
    const status = error.response?.status;
    const data = error.response?.data as any;

    return {
      message: data?.detail || data?.message || error.message,
      code: data?.code || status?.toString(),
      details: data,
      status,
    };
  }

  // 内部逻辑：检查网络错误
  if (isNetworkError(error)) {
    return {
      message: '网络连接失败，请检查网络设置',
      code: 'NETWORK_ERROR',
    };
  }

  // 内部逻辑：默认错误处理
  return {
    message: error.message || '操作失败，请稍后重试',
    code: 'UNKNOWN_ERROR',
  };
}

/**
 * 变量：默认查询配置
 * 内部逻辑：定义所有查询的默认行为
 */
const queryDefaultOptions: QueryClientConfig['defaultOptions'] = {
  queries: {
    /**
     * 属性：数据被视为新鲜的时间（毫秒）
     * 内部逻辑：5分钟内不会重新获取相同的数据
     */
    staleTime: 5 * 60 * 1000,

    /**
     * 属性：未使用数据在缓存中保留的时间（毫秒）
     * 内部逻辑：10分钟后清除未使用的缓存
     */
    gcTime: 10 * 60 * 1000,

    /**
     * 属性：重试次数
     * 内部逻辑：失败时自动重试3次
     */
    retry: 3,

    /**
     * 属性：重试延迟函数
     * 内部逻辑：指数退避策略，避免频繁重试
     */
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),

    /**
     * 属性：窗口聚焦时是否重新获取
     * 内部逻辑：默认不重新获取，减少服务器压力
     */
    refetchOnWindowFocus: false,

    /**
     * 属性：重新挂载时是否重新获取
     */
    refetchOnMount: false,

    /**
     * 属性：网络重连时是否重新获取
     */
    refetchOnReconnect: true,

    /**
     * 属性：错误处理函数
     */
    onError: (error) => {
      const queryError = handleQueryError(error as Error);
      console.error('[Query Error]', queryError);
    },
  },

  mutations: {
    /**
     * 属性：变异重试次数
     */
    retry: 1,

    /**
     * 属性：变异错误处理函数
     */
    onError: (error) => {
      const queryError = handleQueryError(error as Error);
      console.error('[Mutation Error]', queryError);
    },
  },
};

/**
 * 类级注释：React Query 客户端管理器
 * 设计模式：单例模式
 * 职责：管理和配置全局 QueryClient 实例
 */
class QueryClientManager {
  /** 内部变量：单例实例 */
  private static instance: QueryClientManager;

  /** 内部变量：QueryClient 实例 */
  private queryClient: QueryClient;

  /**
   * 函数级注释：私有构造函数
   * 参数：
   *   config - 可选的自定义配置
   */
  private constructor(config?: QueryClientConfig) {
    // 内部逻辑：合并默认配置和自定义配置
    const mergedConfig: QueryClientConfig = {
      ...config,
      defaultOptions: {
        ...queryDefaultOptions,
        ...config?.defaultOptions,
        queries: {
          ...queryDefaultOptions.queries,
          ...config?.defaultOptions?.queries,
        },
        mutations: {
          ...queryDefaultOptions.mutations,
          ...config?.defaultOptions?.mutations,
        },
      },
    };

    this.queryClient = new QueryClient(mergedConfig);
  }

  /**
   * 函数级注释：获取单例实例
   * 参数：
   *   config - 可选的自定义配置（仅在首次调用时生效）
   * 返回值：QueryClientManager 实例
   */
  static getInstance(config?: QueryClientConfig): QueryClientManager {
    if (!QueryClientManager.instance) {
      QueryClientManager.instance = new QueryClientManager(config);
    }
    return QueryClientManager.instance;
  }

  /**
   * 函数级注释：获取 QueryClient 实例
   * 返回值：QueryClient 实例
   */
  getClient(): QueryClient {
    return this.queryClient;
  }

  /**
   * 函数级注释：重置查询缓存
   */
  reset(): void {
    this.queryClient.resetQueries();
  }

  /**
   * 函数级注释：清除查询缓存
   */
  clear(): void {
    this.queryClient.clear();
  }

  /**
   * 函数级注释：使特定查询失效
   * 参数：
   *   filters - 查询过滤器
   */
  invalidateQueries(filters?: Parameters<QueryClient['invalidateQueries']>[0]): void {
    this.queryClient.invalidateQueries(filters);
  }

  /**
   * 函数级注释：预取数据
   * 参数：
   *   key - 查询键
   *   fetcher - 数据获取函数
   */
  async prefetch<T>(key: readonly unknown[], fetcher: () => Promise<T>): Promise<void> {
    await this.queryClient.prefetchQuery({
      queryKey: key,
      queryFn: fetcher,
    });
  }

  /**
   * 函数级注释：设置查询数据（直接更新缓存）
   * 参数：
   *   key - 查询键
   *   data - 要设置的数据
   */
  setData<T>(key: readonly unknown[], data: T): void {
    this.queryClient.setQueryData(key, data);
  }

  /**
   * 函数级注释：获取查询数据（从缓存）
   * 参数：
   *   key - 查询键
   * 返回值：缓存的数据或 undefined
   */
  getData<T>(key: readonly unknown[]): T | undefined {
    return this.queryClient.getQueryData<T>(key);
  }

  /**
   * 函数级注释：获取查询状态
   * 参数：
   *   key - 查询键
   * 返回值：查询状态或 undefined
   */
  getQueryState(key: readonly unknown[]) {
    return this.queryClient.getQueryState(key);
  }
}

/**
 * 变量：全局 QueryClient 管理器实例
 * 内部逻辑：导出单例实例供应用使用
 */
export const queryClientManager = QueryClientManager.getInstance();

/**
 * 变量：全局 QueryClient 实例
 * 内部逻辑：直接导出 QueryClient 供 React Query Provider 使用
 */
export const queryClient = queryClientManager.getClient();

/**
 * 类级注释：查询工具类
 * 设计模式：工具类模式
 * 职责：提供常用的查询操作工具方法
 */
export class QueryUtils {
  /**
   * 函数级注释：构建无限滚动查询键
   * 参数：
   *   baseKey - 基础查询键
   *   params - 查询参数
   * 返回值：查询键
   *
   * @example
   * ```typescript
   * const key = QueryUtils.buildInfiniteQueryKey('documents', { status: 'active' });
   * // 结果: ['documents', 'infinite', { status: 'active' }]
   * ```
   */
  static buildInfiniteQueryKey<T>(baseKey: string, params?: T): readonly unknown[] {
    return [baseKey, 'infinite', params] as const;
  }

  /**
   * 函数级注释：构建分页查询键
   * 参数：
   *   baseKey - 基础查询键
   *   page - 页码
   *   pageSize - 每页大小
   * 返回值：查询键
   */
  static buildPaginatedQueryKey(
    baseKey: string,
    page: number,
    pageSize: number
  ): readonly unknown[] {
    return [baseKey, 'paginated', { page, pageSize }] as const;
  }

  /**
   * 函数级注释：使相关查询失效
   * 参数：
   *   baseKey - 基础查询键
   */
  static invalidateRelated(baseKey: string): void {
    queryClientManager.invalidateQueries({
      predicate: (query) => {
        const key = query.queryKey[0] as string;
        return typeof key === 'string' && key.startsWith(baseKey);
      },
    });
  }

  /**
   * 函数级注释：乐观更新辅助函数
   * 参数：
   *   key - 查询键
   *   updater - 更新函数
   * 返回值：回滚函数
   *
   * @example
   * ```typescript
   * const rollback = QueryUtils.optimisticUpdate(
   *   queryKeys.documents.detail(123),
   *   (old) => ({ ...old, title: 'New Title' })
   * );
   * try {
   *   await updateDocument(123, { title: 'New Title' });
   * } catch (error) {
   *   rollback(); // 回滚到旧数据
   * }
   * ```
   */
  static optimisticUpdate<T>(
    key: readonly unknown[],
    updater: (old: T | undefined) => T
  ): () => void {
    // 内部逻辑：保存旧数据
    const previousData = queryClientManager.getData<T>(key);

    // 内部逻辑：立即更新缓存
    queryClientManager.setData(key, updater(previousData));

    // 内部逻辑：返回回滚函数
    return () => {
      queryClientManager.setData(key, previousData);
    };
  }

  /**
   * 函数级注释：批量预取数据
   * 参数：
   *   items - 要预取的项目
   *   keyBuilder - 查询键构建器
   *   fetcher - 数据获取函数
   */
  static async prefetchBatch<T, I>(
    items: I[],
    keyBuilder: (item: I) => readonly unknown[],
    fetcher: (item: I) => Promise<T>
  ): Promise<void> {
    await Promise.all(
      items.map(async (item) => {
        const key = keyBuilder(item);
        await queryClientManager.prefetch(key, () => fetcher(item));
      })
    );
  }

  /**
   * 函数级注释：缓存数据差异比较
   * 参数：
   *   oldData - 旧数据
   *   newData - 新数据
   * 返回值：是否有变化
   */
  static hasDataChanged<T>(oldData: T, newData: T): boolean {
    return JSON.stringify(oldData) !== JSON.stringify(newData);
  }
}

/**
 * 常量：默认分页大小
 */
export const DEFAULT_PAGE_SIZE = 20;

/**
 * 常量：默认无限滚动每页大小
 */
export const DEFAULT_INFINITE_PAGE_SIZE = 15;

// 导出所有公共接口
export default queryClient;
