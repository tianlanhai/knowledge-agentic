/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：React Query 自定义 Hooks 模块
 * 内部逻辑：提供与 React Query 集成的自定义 Hooks
 * 设计模式：工厂模式 + 策略模式
 * 设计原则：DRY、单一职责原则
 *
 * @package frontend/src/hooks
 */

import { useMutation, useQuery, useQueryClient, useInfiniteQuery, type UseQueryOptions } from '@tanstack/react-query';
import { useCallback, useMemo } from 'react';
import type { QueryKey } from '@tanstack/react-query';
import { queryKeys, QueryUtils, queryClientManager } from '@/core/queryClient';
import type { AsyncResult } from '@/services/baseService';

/**
 * 类型：查询选项类型（排除冲突项）
 */
type SafeQueryOptions<TData, TError> = Omit<UseQueryOptions<TData, TError>, 'queryKey' | 'queryFn'>;

/**
 * Hook：useServiceQuery
 * 内部逻辑：从服务获取数据的通用 Hook
 * 设计模式：模板方法模式
 *
 * @param queryKey - 查询键
 * @param queryFn - 数据获取函数，返回 AsyncResult
 * @param options - 查询选项
 * @returns 查询结果
 *
 * @example
 * ```typescript
 * const { data, isLoading, error } = useServiceQuery(
 *   queryKeys.documents.detail(123),
 *   () => documentService.getDocument(123)
 * );
 * ```
 */
export function useServiceQuery<TData, TError = Error>(
  queryKey: QueryKey,
  queryFn: () => Promise<AsyncResult<TData>>,
  options?: SafeQueryOptions<TData, TError>
) {
  return useQuery({
    queryKey,
    queryFn: async () => {
      const result = await queryFn();
      if (result.success) {
        return result.data;
      }
      throw new Error(result.error?.error || '查询失败');
    },
    ...options,
  });
}

/**
 * Hook：useServiceMutation
 * 内部逻辑：执行服务端操作的通用 Hook
 * 设计模式：模板方法模式
 *
 * @param mutationFn - 变异函数，返回 AsyncResult
 * @param options - 变异选项
 * @returns 变异结果
 *
 * @example
 * ```typescript
 * const { mutate, isLoading } = useServiceMutation(
 *   (data) => documentService.createDocument(data),
 *   {
 *     onSuccess: () => {
 *       queryClient.invalidateQueries({ queryKey: queryKeys.documents.all() });
 *     }
 *   }
 * );
 * ```
 */
export function useServiceMutation<TData, TError = Error, TVariables = void>(
  mutationFn: (variables: TVariables) => Promise<AsyncResult<TData>>,
  options?: {
    onSuccess?: (data: TData, variables: TVariables) => void;
    onError?: (error: TError, variables: TVariables) => void;
    onSettled?: (data: TData | undefined, error: TError | null, variables: TVariables) => void;
  }
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (variables: TVariables) => {
      const result = await mutationFn(variables);
      if (result.success) {
        return result.data;
      }
      throw new Error(result.error?.error || '操作失败');
    },
    onSuccess: options?.onSuccess,
    onError: options?.onError,
    onSettled: options?.onSettled,
  });
}

/**
 * Hook：useOptimisticMutation
 * 内部逻辑：乐观更新变异的 Hook
 * 设计模式：模板方法模式
 *
 * @param config - 配置对象
 * @returns 变异结果
 *
 * @example
 * ```typescript
 * const { mutate } = useOptimisticMutation({
 *   mutationFn: (id) => documentService.deleteDocument(id),
 *   optimisticUpdate: (old, id) => old?.filter(doc => doc.id !== id),
 *   queryKey: queryKeys.documents.all()
 * });
 * ```
 */
export function useOptimisticMutation<TData, TVariables, TPreviousData = unknown>({
  mutationFn,
  optimisticUpdate,
  queryKey,
  invalidateQueries,
  onSuccess,
  onError,
}: {
  mutationFn: (variables: TVariables) => Promise<AsyncResult<TData>>;
  optimisticUpdate: (old: TPreviousData | undefined, variables: TVariables) => TPreviousData;
  queryKey: QueryKey;
  invalidateQueries?: QueryKey[];
  onSuccess?: (data: TData, variables: TVariables) => void;
  onError?: (error: Error, variables: TVariables) => void;
}) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (variables: TVariables) => {
      const result = await mutationFn(variables);
      if (result.success) {
        return result.data;
      }
      throw new Error(result.error?.error || '操作失败');
    },
    onMutate: async (variables) => {
      // 内部逻辑：取消相关查询
      await queryClient.cancelQueries({ queryKey });

      // 内部逻辑：保存旧数据
      const previousData = queryClient.getQueryData<TPreviousData>(queryKey);

      // 内部逻辑：乐观更新
      queryClient.setQueryData<TPreviousData>(
        queryKey,
        (old) => optimisticUpdate(old, variables)
      );

      return { previousData };
    },
    onError: (error, variables, context) => {
      // 内部逻辑：回滚到旧数据
      if (context?.previousData !== undefined) {
        queryClient.setQueryData(queryKey, context.previousData);
      }
      onError?.(error as Error, variables);
    },
    onSuccess: (data, variables) => {
      // 内部逻辑：使相关查询失效
      if (invalidateQueries) {
        invalidateQueries.forEach((key) => {
          queryClient.invalidateQueries({ queryKey: key });
        });
      }
      onSuccess?.(data, variables);
    },
  });
}

/**
 * Hook：useInfiniteScrollQuery
 * 内部逻辑：无限滚动查询的 Hook
 * 设计模式：策略模式
 *
 * @param config - 配置对象
 * @returns 无限查询结果
 *
 * @example
 * ```typescript
 * const { data, fetchNextPage, hasNextPage } = useInfiniteScrollQuery({
 *   queryKey: queryKeys.documents.all(),
 *   fetchPage: ({ pageParam }) => documentService.getDocuments({ page: pageParam, limit: 20 }),
 *   getNextPageParam: (lastPage) => lastPage.hasMore ? lastPage.page + 1 : undefined
 * });
 * ```
 */
export function useInfiniteScrollQuery<TData, TError = Error>({
  queryKey,
  fetchPage,
  getNextPageParam,
  options,
}: {
  queryKey: QueryKey;
  fetchPage: (params: { pageParam: unknown | undefined }) => Promise<AsyncResult<TData>>;
  getNextPageParam: (lastPage: TData, allPages: TData[]) => unknown | undefined;
  options?: Omit<UseQueryOptions<TData, TError>, 'queryKey' | 'queryFn' | 'getNextPageParam'>;
}) {
  return useInfiniteQuery({
    queryKey,
    queryFn: async ({ pageParam }) => {
      const result = await fetchPage({ pageParam });
      if (result.success) {
        return result.data;
      }
      throw new Error(result.error?.error || '查询失败');
    },
    getNextPageParam,
    initialPageParam: 1,
    ...options,
  });
}

/**
 * Hook：useDocuments
 * 内部逻辑：文档查询的专用 Hook
 * 设计模式：工厂模式
 *
 * @param filters - 过滤条件
 * @param options - 查询选项
 * @returns 文档列表
 */
export function useDocuments(
  filters?: { status?: string; search?: string },
  options?: SafeQueryOptions<any[], Error>
) {
  return useQuery({
    queryKey: queryKeys.documents.list(filters),
    queryFn: async () => {
      // 内部逻辑：这里应该调用实际的文档服务
      // 暂时返回空数组
      return [];
    },
    ...options,
  });
}

/**
 * Hook：useDocument
 * 内部逻辑：单个文档查询的专用 Hook
 *
 * @param id - 文档 ID
 * @param options - 查询选项
 * @returns 文档详情
 */
export function useDocument(
  id: string | number,
  options?: SafeQueryOptions<any, Error>
) {
  return useQuery({
    queryKey: queryKeys.documents.detail(id),
    queryFn: async () => {
      // 内部逻辑：这里应该调用实际的文档服务
      return null;
    },
    enabled: !!id,
    ...options,
  });
}

/**
 * Hook：useConversations
 * 内部逻辑：对话列表查询的专用 Hook
 *
 * @param filters - 过滤条件
 * @param options - 查询选项
 * @returns 对话列表
 */
export function useConversations(
  filters?: { limit?: number },
  options?: SafeQueryOptions<any[], Error>
) {
  return useQuery({
    queryKey: queryKeys.conversations.list(filters),
    queryFn: async () => {
      // 内部逻辑：这里应该调用实际的对话服务
      return [];
    },
    ...options,
  });
}

/**
 * Hook：useModelConfigs
 * 内部逻辑：模型配置查询的专用 Hook
 *
 * @param options - 查询选项
 * @returns 模型配置列表
 */
export function useModelConfigs(options?: SafeQueryOptions<any[], Error>) {
  return useQuery({
    queryKey: queryKeys.modelConfigs.all(),
    queryFn: async () => {
      // 内部逻辑：这里应该调用实际的模型配置服务
      return [];
    },
    ...options,
  });
}

/**
 * Hook：usePrefetch
 * 内部逻辑：数据预取的 Hook
 *
 * @returns 预取函数
 *
 * @example
 * ```typescript
 * const prefetch = usePrefetch();
 * prefetch(queryKeys.documents.detail(123), () => fetchDocument(123));
 * ```
 */
export function usePrefetch() {
  const queryClient = useQueryClient();

  return useCallback(
    async <T>(key: QueryKey, fetcher: () => Promise<T>) => {
      await queryClient.prefetchQuery({
        queryKey: key,
        queryFn: fetcher,
      });
    },
    [queryClient]
  );
}

/**
 * Hook：useInvalidateQueries
 * 内部逻辑：使查询失效的 Hook
 *
 * @returns 使失效函数
 *
 * @example
 * ```typescript
 * const invalidate = useInvalidateQueries();
 * invalidate(queryKeys.documents.all());
 * ```
 */
export function useInvalidateQueries() {
  const queryClient = useQueryClient();

  return useCallback(
    (key: QueryKey) => {
      queryClient.invalidateQueries({ queryKey: key });
    },
    [queryClient]
  );
}

/**
 * Hook：useResetQueries
 * 内部逻辑：重置查询的 Hook
 *
 * @returns 重置函数
 */
export function useResetQueries() {
  const queryClient = useQueryClient();

  return useCallback(
    (key?: QueryKey) => {
      if (key) {
        queryClient.resetQueries({ queryKey: key });
      } else {
        queryClient.resetQueries();
      }
    },
    [queryClient]
  );
}

/**
 * Hook：useQueryState
 * 内部逻辑：获取查询状态的 Hook（不触发数据获取）
 *
 * @param key - 查询键
 * @returns 查询状态
 */
export function useQueryState<T>(key: QueryKey) {
  const queryClient = useQueryClient();

  const state = useMemo(() => {
    return queryClient.getQueryState<T>(key);
  }, [queryClient, key]);

  const data = useMemo(() => {
    return queryClient.getQueryData<T>(key);
  }, [queryClient, key]);

  return {
    data,
    state,
    isLoading: state?.fetchStatus === 'fetching',
    isStale: state?.isStale ?? false,
    isValidating: state?.fetchStatus === 'fetching',
  };
}

/**
 * Hook：useCachedData
 * 内部逻辑：获取缓存数据的 Hook
 *
 * @param key - 查询键
 * @returns 缓存的数据
 */
export function useCachedData<T>(key: QueryKey): T | undefined {
  const queryClient = useQueryClient();

  return useMemo(() => {
    return queryClient.getQueryData<T>(key);
  }, [queryClient, key]);
}

// 导出所有公共接口
export default {
  useServiceQuery,
  useServiceMutation,
  useOptimisticMutation,
  useInfiniteScrollQuery,
  useDocuments,
  useDocument,
  useConversations,
  useModelConfigs,
  usePrefetch,
  useInvalidateQueries,
  useResetQueries,
  useQueryState,
  useCachedData,
};
