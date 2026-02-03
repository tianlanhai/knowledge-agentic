/**
 * 上海宇羲伏天智能科技有限公司出品
 *
/**
 * 文件级注释：任务管理 Hook
 * 内部逻辑：封装任务列表的查询、刷新和状态更新逻辑
 */
import { useEffect, useState } from 'react';
import { ingestService } from '../services/ingestService';
import { useTaskStore } from '../stores/taskStore';
import type { TaskListResponse, TaskStatus } from '../types/ingest';

/**
 * 任务管理 Hook 返回值接口
 */
interface UseTasksReturn {
  /** 任务列表 */
  tasks: TaskListResponse;
  /** 加载状态 */
  loading: boolean;
  /** 错误信息 */
  error: string | null;
  /** 刷新任务列表 */
  refetch: () => Promise<void>;
  /** 按状态筛选任务 */
  filterByStatus: (status: TaskStatus | 'all') => void;
  /** 当前筛选状态 */
  filterStatus: TaskStatus | 'all';
}

/**
 * 任务管理 Hook
 * 内部变量：tasks - 任务列表，loading - 加载状态，error - 错误信息，filterStatus - 筛选状态
 * 内部逻辑：从后端获取任务列表，更新全局状态，支持状态筛选
 * 返回值：UseTasksReturn - 任务管理对象
 */
export const useTasks = (status?: TaskStatus | 'all'): UseTasksReturn => {
  // 内部变量：从全局 store 获取任务和操作方法
  const { setTasks, getTasksByStatus, tasks: storeTasks } = useTaskStore();
  
  // 内部变量：本地状态
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<TaskStatus | 'all'>(status || 'all');

  /**
   * 获取任务列表
   * 内部逻辑：从服务器获取任务列表，更新全局状态
   */
  const fetchTasks = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await ingestService.getAllTasks(0, 100);
      // 内部逻辑：更新全局状态
      setTasks(response.items);
    } catch (err: any) {
      setError(err.message || '获取任务列表失败');
      console.error('获取任务列表失败:', err);
    } finally {
      setLoading(false);
    }
  };

  /**
   * 刷新任务列表
   * 内部逻辑：重新获取任务列表
   */
  const refetch = async () => {
    await fetchTasks();
  };

  /**
   * 按状态筛选任务
   * 内部逻辑：设置筛选状态，返回筛选后的任务
   */
  const filterByStatus = (status: TaskStatus | 'all') => {
    setFilterStatus(status);
  };

  /**
   * 初始化时获取任务列表
   * 内部逻辑：组件挂载时加载任务
   */
  useEffect(() => {
    fetchTasks();
  }, []);

  /**
   * 根据 filterStatus 返回筛选后的任务
   */
  const filteredItems = filterStatus === 'all' 
    ? storeTasks 
    : getTasksByStatus(filterStatus);

  return {
    tasks: {
      items: filteredItems,
      total: filteredItems.length,
    },
    loading,
    error,
    refetch,
    filterByStatus,
    filterStatus,
  };
};
