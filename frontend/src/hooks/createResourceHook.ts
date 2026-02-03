/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：资源 Hook 工厂模块
 * 内部逻辑：提供创建资源获取 Hook 的工厂方法，减少重复代码
 * 设计模式：工厂模式（Factory Pattern）+ 模板方法模式
 * 设计原则：DRY 原则、开闭原则
 */

import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * 资源状态类型
 */
export type ResourceStatus = 'idle' | 'loading' | 'success' | 'error';

/**
 * 资源状态接口
 */
export interface ResourceState<T> {
  /** 数据 */
  data: T | null;
  /** 状态 */
  status: ResourceStatus;
  /** 错误 */
  error: Error | null;
  /** 是否正在加载 */
  isLoading: boolean;
  /** 是否成功 */
  isSuccess: boolean;
  /** 是否错误 */
  isError: boolean;
  /** 最后更新时间 */
  lastUpdated: number | null;
}

/**
 * 资源 Hook 返回值接口
 */
export interface ResourceHookResult<T> extends ResourceState<T> {
  /** 重新获取数据 */
  refetch: () => Promise<void>;
  /** 手动设置数据 */
  setData: (data: T) => void;
  /** 手动设置错误 */
  setError: (error: Error) => void;
  /** 重置状态 */
  reset: () => void;
  /** 是否是首次加载 */
  isFirstLoad: boolean;
}

/**
 * 资源 Hook 配置接口
 */
export interface ResourceHookConfig<T, K> {
  /** 获取数据的函数 */
  fetch: (id: K) => Promise<T>;
  /** 缓存键生成函数 */
  cacheKey?: (id: K) => string;
  /** 缓存过期时间（毫秒） */
  staleTime?: number;
  /** 是否在挂载时自动获取 */
  enabled?: boolean;
  /** 成功回调 */
  onSuccess?: (data: T) => void;
  /** 错误回调 */
  onError?: (error: Error) => void;
  /** 依赖项（变化时重新获取） */
  deps?: any[];
  /** 初始数据 */
  initialData?: T | null;
}

/**
 * 缓存条目接口
 */
interface CacheEntry<T> {
  data: T;
  timestamp: number;
}

/**
 * 类：资源缓存管理器
 * 内部逻辑：管理资源数据的缓存
 * 设计模式：单例模式
 */
class ResourceCacheManager {
  /** 内部变量：单例实例 */
  private static instance: ResourceCacheManager;

  /** 内部变量：缓存存储 */
  private cache: Map<string, CacheEntry<any>>;

  /** 内部变量：过期时间配置 */
  private staleTimes: Map<string, number>;

  /**
   * 私有构造函数
   */
  private constructor() {
    this.cache = new Map();
    this.staleTimes = new Map();
  }

  /**
   * 函数级注释：获取单例实例
   */
  static getInstance(): ResourceCacheManager {
    if (!ResourceCacheManager.instance) {
      ResourceCacheManager.instance = new ResourceCacheManager();
    }
    return ResourceCacheManager.instance;
  }

  /**
   * 函数级注释：获取缓存
   * 泛型参数：
   *   T - 数据类型
   * 参数：
   *   key - 缓存键
   * 返回值：缓存数据或 undefined
   */
  get<T>(key: string): T | undefined {
    const entry = this.cache.get(key);

    if (!entry) {
      return undefined;
    }

    // 内部逻辑：检查是否过期
    const staleTime = this.staleTimes.get(key) || 0;
    if (Date.now() - entry.timestamp > staleTime) {
      this.cache.delete(key);
      return undefined;
    }

    return entry.data;
  }

  /**
   * 函数级注释：设置缓存
   * 泛型参数：
   *   T - 数据类型
   * 参数：
   *   key - 缓存键
   *   data - 缓存数据
   *   staleTime - 过期时间
   */
  set<T>(key: string, data: T, staleTime?: number): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });

    if (staleTime !== undefined) {
      this.staleTimes.set(key, staleTime);
    }
  }

  /**
   * 函数级注释：清除缓存
   * 参数：
   *   key - 缓存键，为 undefined 时清除所有
   */
  clear(key?: string): void {
    if (key) {
      this.cache.delete(key);
      this.staleTimes.delete(key);
    } else {
      this.cache.clear();
      this.staleTimes.clear();
    }
  }

  /**
   * 函数级注释：预加载数据
   */
  preload<T>(key: string, data: T, staleTime?: number): void {
    this.set(key, data, staleTime);
  }
}

/**
 * 内部变量：全局缓存管理器实例
 */
export const resourceCache = ResourceCacheManager.getInstance();

/**
 * Hook：createResourceHook
 * 内部逻辑：工厂函数，创建资源获取 Hook
 * 设计模式：工厂模式 + 模板方法模式
 * 泛型参数：
 *   T - 资源数据类型
 *   K - 资源标识类型（默认 string）
 * 参数：
 *   config - Hook 配置
 * 返回值：自定义 Hook 函数
 *
 * @example
 * // 创建文档 Hook
 * const useDocument = createResourceHook({
 *   fetch: (id: number) => documentService.getDocument(id),
 *   cacheKey: (id) => `document-${id}`,
 *   staleTime: 5 * 60 * 1000 // 5 分钟
 * });
 *
 * // 使用
 * function DocumentPage({ id }) {
 *   const { data, isLoading, error, refetch } = useDocument(id);
 *   ...
 * }
 */
export function createResourceHook<T, K = string>(
  config: ResourceHookConfig<T, K>
): (id: K) => ResourceHookResult<T> {
  const {
    fetch,
    cacheKey,
    staleTime = 5 * 60 * 1000, // 默认 5 分钟
    enabled = true,
    onSuccess,
    onError,
    deps = [],
    initialData = null
  } = config;

  /**
   * 生成的 Hook
   */
  return function useResource(id: K): ResourceHookResult<T> {
    // 内部变量：资源状态
    const [state, setState] = useState<ResourceState<T>>({
      data: initialData,
      status: 'idle',
      error: null,
      isLoading: false,
      isSuccess: false,
      isError: false,
      lastUpdated: null
    });

    // 内部变量：是否首次加载
    const isFirstLoad = useRef(true);

    /**
     * 函数级注释：获取数据
     */
    const fetchData = useCallback(async () => {
      // 内部逻辑：生成缓存键
      const key = cacheKey ? cacheKey(id) : String(id);

      // 内部逻辑：检查缓存
      const cached = resourceCache.get<T>(key);
      if (cached !== undefined && state.status !== 'loading') {
        setState({
          data: cached,
          status: 'success',
          error: null,
          isLoading: false,
          isSuccess: true,
          isError: false,
          lastUpdated: Date.now()
        });
        return;
      }

      // 内部逻辑：开始加载
      setState((prev) => ({
        ...prev,
        status: 'loading',
        isLoading: true,
        isError: false
      }));

      try {
        // 内部逻辑：获取数据
        const data = await fetch(id);

        // 内部逻辑：更新缓存
        resourceCache.set(key, data, staleTime);

        // 内部逻辑：更新状态
        setState({
          data,
          status: 'success',
          error: null,
          isLoading: false,
          isSuccess: true,
          isError: false,
          lastUpdated: Date.now()
        });

        // 内部逻辑：成功回调
        if (onSuccess) {
          onSuccess(data);
        }
      } catch (error) {
        const err = error instanceof Error ? error : new Error(String(error));

        // 内部逻辑：更新状态
        setState({
          data: null,
          status: 'error',
          error: err,
          isLoading: false,
          isSuccess: false,
          isError: true,
          lastUpdated: Date.now()
        });

        // 内部逻辑：错误回调
        if (onError) {
          onError(err);
        }
      }
    }, [id, fetch, cacheKey, staleTime, onSuccess, onError]);

    /**
     * 函数级注释：重新获取
     */
    const refetch = useCallback(async () => {
      // 内部逻辑：清除缓存
      const key = cacheKey ? cacheKey(id) : String(id);
      resourceCache.clear(key);

      // 内部逻辑：重新获取
      await fetchData();
    }, [id, cacheKey, fetchData]);

    /**
     * 函数级注释：设置数据
     */
    const setData = useCallback((data: T) => {
      setState({
        data,
        status: 'success',
        error: null,
        isLoading: false,
        isSuccess: true,
        isError: false,
        lastUpdated: Date.now()
      });
    }, []);

    /**
     * 函数级注释：设置错误
     */
    const setError = useCallback((error: Error) => {
      setState({
        data: null,
        status: 'error',
        error,
        isLoading: false,
        isSuccess: false,
        isError: true,
        lastUpdated: Date.now()
      });
    }, []);

    /**
     * 函数级注释：重置状态
     */
    const reset = useCallback(() => {
      setState({
        data: initialData,
        status: 'idle',
        error: null,
        isLoading: false,
        isSuccess: false,
        isError: false,
        lastUpdated: null
      });
      isFirstLoad.current = true;
    }, []);

    /**
     * 函数级注释：副作用 - 自动获取数据
     */
    useEffect(() => {
      if (!enabled) {
        return;
      }

      isFirstLoad.current = false;
      fetchData();

      // 内部逻辑：返回清理函数
      return () => {
        // 内部逻辑：可以在这里取消请求
      };
    }, [id, enabled, fetchData, ...deps]);

    return {
      ...state,
      refetch,
      setData,
      setError,
      reset,
      isFirstLoad: isFirstLoad.current
    };
  };
}

/**
 * Hook：createListResourceHook
 * 内部逻辑：创建列表资源获取 Hook
 * 设计模式：工厂模式 + 模板方法模式
 */
export interface ListResourceConfig<T, P = any> {
  /** 获取列表的函数 */
  fetchList: (params: P) => Promise<{ items: T[]; total: number }>;
  /** 缓存键生成函数 */
  cacheKey?: (params: P) => string;
  /** 缓存过期时间 */
  staleTime?: number;
  /** 是否启用 */
  enabled?: boolean;
  /** 初始参数 */
  initialParams?: P;
}

export interface ListResourceResult<T> {
  /** 列表数据 */
  items: T[];
  /** 总数 */
  total: number;
  /** 是否正在加载 */
  isLoading: boolean;
  /** 错误信息 */
  error: Error | null;
  /** 重新获取 */
  refetch: () => Promise<void>;
  /** 加载更多 */
  loadMore: () => Promise<void>;
  /** 是否有更多 */
  hasMore: boolean;
  /** 当前页 */
  page: number;
}

export function createListResourceHook<T, P = any>(
  config: ListResourceConfig<T, P>
): (params?: P) => ListResourceResult<T> {
  const { fetchList, cacheKey, staleTime = 60000, enabled = true, initialParams } = config;

  return function useListResource(params: P = {} as P): ListResourceResult<T> {
    // 内部变量：合并参数
    const mergedParams = { ...initialParams, ...params };

    // 内部变量：列表状态
    const [items, setItems] = useState<T[]>([]);
    const [total, setTotal] = useState(0);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<Error | null>(null);
    const [page, setPage] = useState(1);

    /**
     * 函数级注释：获取列表
     */
    const fetch = useCallback(async () => {
      setIsLoading(true);
      setError(null);

      try {
        const result = await fetchList(mergedParams);

        setItems(result.items);
        setTotal(result.total);
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
      } finally {
        setIsLoading(false);
      }
    }, [mergedParams, fetchList]);

    /**
     * 函数级注释：重新获取
     */
    const refetch = useCallback(async () => {
      const key = cacheKey ? cacheKey(mergedParams) : String(mergedParams);
      resourceCache.clear(key);
      setPage(1);
      await fetch();
    }, [mergedParams, cacheKey, fetch]);

    /**
     * 函数级注释：加载更多
     */
    const loadMore = useCallback(async () => {
      if (isLoading || items.length >= total) {
        return;
      }

      const nextPage = page + 1;
      const newParams = { ...mergedParams, page: nextPage };

      setIsLoading(true);
      try {
        const result = await fetchList(newParams as any);
        setItems((prev) => [...prev, ...result.items]);
        setTotal(result.total);
        setPage(nextPage);
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
      } finally {
        setIsLoading(false);
      }
    }, [isLoading, items.length, total, page, mergedParams, fetchList]);

    /**
     * 函数级注释：副作用
     */
    useEffect(() => {
      if (enabled) {
        fetch();
      }
    }, [enabled, fetch]);

    return {
      items,
      total,
      isLoading,
      error,
      refetch,
      loadMore,
      hasMore: items.length < total,
      page
    };
  };
}

/**
 * Hook：useMutation
 * 内部逻辑：创建变更操作的 Hook
 * 设计模式：工厂模式
 */
export interface MutationConfig<TData, TVariables> {
  /** 变更函数 */
  mutate: (variables: TVariables) => Promise<TData>;
  /** 成功回调 */
  onSuccess?: (data: TData, variables: TVariables) => void;
  /** 错误回调 */
  onError?: (error: Error, variables: TVariables) => void;
  /** 完成回调 */
  onSettled?: (data: TData | undefined, error: Error | null, variables: TVariables) => void;
}

export interface MutationResult<TData, TVariables> {
  /** 执行变更 */
  mutate: (variables: TVariables) => Promise<TData>;
  /** 是否正在变更 */
  isMutating: boolean;
  /** 变更结果数据 */
  data: TData | null;
  /** 变更错误 */
  error: Error | null;
  /** 重置状态 */
  reset: () => void;
}

export function createMutationHook<TData = any, TVariables = void>(
  config: MutationConfig<TData, TVariables>
): () => MutationResult<TData, TVariables> {
  const { mutate: mutateFn, onSuccess, onError, onSettled } = config;

  return function useMutation(): MutationResult<TData, TVariables> {
    const [isMutating, setIsMutating] = useState(false);
    const [data, setData] = useState<TData | null>(null);
    const [error, setError] = useState<Error | null>(null);

    /**
     * 函数级注释：执行变更
     */
    const mutate = useCallback(async (variables: TVariables): Promise<TData> => {
      setIsMutating(true);
      setError(null);

      try {
        const result = await mutateFn(variables);
        setData(result);

        if (onSuccess) {
          onSuccess(result, variables);
        }

        return result;
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);

        if (onError) {
          onError(error, variables);
        }

        throw error;
      } finally {
        setIsMutating(false);

        if (onSettled) {
          onSettled(data, error, variables);
        }
      }
    }, [mutateFn, onSuccess, onError, onSettled, data]);

    /**
     * 函数级注释：重置状态
     */
    const reset = useCallback(() => {
      setData(null);
      setError(null);
    }, []);

    return {
      mutate,
      isMutating,
      data,
      error,
      reset
    };
  };
}

// 导出所有公共接口
export default createResourceHook;
