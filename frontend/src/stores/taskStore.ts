/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：任务状态管理 Store
 * 内部逻辑：使用 Zustand 管理任务列表状态，提供全局任务管理功能
 */
import { create } from 'zustand';
import type { TaskResponse, TaskStatus } from '../types/ingest';

/**
 * 任务 Store 状态接口
 */
export interface TaskState {
  /** 任务列表 */
  tasks: TaskResponse[];
  /** 加载状态 */
  loading: boolean;
  /** 添加任务 */
  addTask: (task: TaskResponse) => void;
  /** 更新任务 */
  updateTask: (taskId: number, task: Partial<TaskResponse>) => void;
  /** 移除任务 */
  removeTask: (taskId: number) => void;
  /** 设置任务列表 */
  setTasks: (tasks: TaskResponse[]) => void;
  /** 按状态筛选任务 */
  getTasksByStatus: (status: TaskStatus) => TaskResponse[];
  /** 获取任务 */
  getTask: (taskId: number) => TaskResponse | undefined;
}

/**
 * 任务 Store
 * 内部变量：set - 状态更新函数
 * 内部逻辑：提供任务列表的增删改查功能
 * 返回值：TaskState - 任务状态对象
 */
export const useTaskStore = create<TaskState>((set, get) => ({
  // 内部变量：初始状态
  tasks: [],
  loading: false,

  /**
   * 添加任务
   * 内部逻辑：将新任务添加到任务列表
   */
  addTask: (task: TaskResponse) => {
    set((state) => ({
      tasks: [task, ...state.tasks],
    }));
  },

  /**
   * 更新任务
   * 内部逻辑：根据任务ID更新任务信息
   */
  updateTask: (taskId: number, updatedFields: Partial<TaskResponse>) => {
    set((state) => ({
      tasks: state.tasks.map((task) =>
        task.id === taskId ? { ...task, ...updatedFields } : task
      ),
    }));
  },

  /**
   * 移除任务
   * 内部逻辑：根据任务ID从列表中移除任务
   */
  removeTask: (taskId: number) => {
    set((state) => ({
      tasks: state.tasks.filter((task) => task.id !== taskId),
    }));
  },

  /**
   * 设置任务列表
   * 内部逻辑：替换整个任务列表
   */
  setTasks: (tasks: TaskResponse[]) => {
    set({ tasks });
  },

  /**
   * 按状态筛选任务
   * 内部逻辑：返回指定状态的所有任务
   */
  getTasksByStatus: (status: TaskStatus) => {
    return get().tasks.filter((task) => task.status === status);
  },

  /**
   * 获取任务
   * 内部逻辑：根据任务ID返回任务对象
   */
  getTask: (taskId: number) => {
    return get().tasks.find((task) => task.id === taskId);
  },
}));
