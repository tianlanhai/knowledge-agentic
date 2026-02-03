/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：历史记录Store
 * 内部逻辑：管理对话历史会话，支持存储到localStorage
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { Message } from '../types/chat';

/**
 * 接口级注释：历史会话数据模型
 * 属性：
 *   id: 会话唯一标识
 *   title: 会话标题
 *   createdAt: 创建时间
 *   messages: 消息列表
 *   updatedAt: 最后更新时间
 */
export interface HistoryItem {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messages: Message[];
}

/**
 * 接口级注释：历史记录状态
 */
export interface HistoryState {
  /**
   * 属性：会话列表
   */
  histories: HistoryItem[];
  /**
   * 属性：当前会话ID
   */
  currentHistoryId: string | null;
  /**
   * 属性：是否加载中
   */
  loading: boolean;

  /**
   * 函数级注释：添加新会话
   * 内部逻辑：创建新会话，设置标题为第一条消息的前20个字符
   * 参数：
   *   messages: 消息列表
   * 返回值：无
   */
  addHistory: (messages: Message[]) => void;

  /**
   * 函数级注释：更新当前会话
   * 内部逻辑：向当前会话添加消息，更新updatedAt
   * 参数：
   *   message: 新消息
   * 返回值：无
   */
  updateHistory: (message: Message) => void;

  /**
   * 函数级注释：删除会话
   * 参数：
   *   historyId: 会话ID
   * 返回值：无
   */
  deleteHistory: (historyId: string) => void;

  /**
   * 函数级注释：清空所有历史
   * 返回值：无
   */
  clearHistories: () => void;

  /**
   * 函数级注释：加载会话
   * 内部逻辑：设置当前会话ID，标记为当前活动会话
   * 参数：
   *   historyId: 会话ID
   * 返回值：无
   */
  loadHistory: (historyId: string) => void;

  /**
   * 函数级注释：获取当前会话
   * 返回值：当前会话对象或undefined
   */
  getCurrentHistory: () => HistoryItem | undefined;

  /**
   * 函数级注释：生成会话标题
   * 内部逻辑：从第一条用户消息提取前20个字符作为标题
   * 参数：
   *   messages: 消息列表
   * 返回值：会话标题字符串
   */
  generateTitle: (messages: Message[]) => string;
}

/**
 * 函数级注释：生成会话标题的辅助函数
 * 参数：messages - 消息列表
 * 返回值：会话标题
 */
const generateTitle = (messages: Message[]): string => {
  // 内部逻辑：查找第一条用户消息
  const firstUserMessage = messages.find((msg) => msg.role === 'user');
  
  // 内部逻辑：如果没有用户消息，使用默认标题
  if (!firstUserMessage) {
    return `对话 ${new Date().toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}`;
  }
  
  // 内部逻辑：提取前20个字符作为标题
  let title = firstUserMessage.content.slice(0, 20);
  
  // 内部逻辑：如果消息被截断，添加省略号
  if (firstUserMessage.content.length > 20) {
    title += '...';
  }
  
  return title;
};

/**
 * 变量：创建历史记录Store，支持持久化存储
 */
export const useHistoryStore = create<HistoryState>()(
  persist(
    (set, get) => ({
      // 内部变量：初始化状态
      histories: [],
      currentHistoryId: null,
      loading: false,

      /**
       * 函数级注释：添加新会话
       */
      addHistory: (messages) =>
        set((state) => {
          // 内部变量：生成唯一ID
          const id = `history_${Date.now()}`;
          
          // 内部变量：生成会话标题
          const title = generateTitle(messages);
          
          // 内部变量：创建新会话对象
          const newHistory: HistoryItem = {
            id,
            title,
            createdAt: new Date(),
            updatedAt: new Date(),
            messages: [...messages],
          };
          
          // 内部逻辑：设置新会话为当前会话
          return {
            histories: [newHistory, ...state.histories],
            currentHistoryId: id,
          };
        }),

      /**
       * 函数级注释：更新当前会话
       */
      updateHistory: (message) =>
        set((state) => {
          // 内部逻辑：如果没有当前会话，则不更新
          if (!state.currentHistoryId) return state;
          
          // 内部逻辑：查找当前会话
          const currentIndex = state.histories.findIndex(
            (h) => h.id === state.currentHistoryId
          );
          
          // 内部逻辑：如果找不到当前会话，则不更新
          if (currentIndex === -1) return state;
          
          // 内部变量：创建更新后的会话列表
          const updatedHistories = [...state.histories];
          
          // 内部逻辑：向当前会话添加消息
          updatedHistories[currentIndex] = {
            ...updatedHistories[currentIndex],
            messages: [...updatedHistories[currentIndex].messages, message],
            updatedAt: new Date(),
          };
          
          return {
            histories: updatedHistories,
          };
        }),

      /**
       * 函数级注释：删除会话
       */
      deleteHistory: (historyId) =>
        set((state) => {
          // 内部逻辑：如果删除的是当前会话，清除currentHistoryId
          const newCurrentId = state.currentHistoryId === historyId ? null : state.currentHistoryId;
          
          return {
            histories: state.histories.filter((h) => h.id !== historyId),
            currentHistoryId: newCurrentId,
          };
        }),

      /**
       * 函数级注释：清空所有历史
       */
      clearHistories: () =>
        set({
          histories: [],
          currentHistoryId: null,
        }),

      /**
       * 函数级注释：加载会话
       */
      loadHistory: (historyId) =>
        set({
          currentHistoryId: historyId,
        }),

      /**
       * 函数级注释：获取当前会话
       */
      getCurrentHistory: () => {
        const state = get();
        // 内部逻辑：根据currentHistoryId查找会话
        return state.histories.find((h) => h.id === state.currentHistoryId);
      },

      /**
       * 函数级注释：生成会话标题
       */
      generateTitle,
    }),
    {
      // 内部逻辑：持久化配置
      name: 'history-storage',
      storage: createJSONStorage(() => localStorage),
    }
  )
);
