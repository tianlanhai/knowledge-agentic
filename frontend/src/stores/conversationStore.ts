/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：会话持久化状态管理
 * 内部逻辑：使用Zustand管理会话和消息状态
 * 设计模式：单一职责原则 - 消息操作逻辑与 chatStore 保持一致，便于维护
 * 重构说明：消息操作方法已提取到 messageStore 作为参考实现
 */

import { create } from 'zustand';
import type {
  Conversation,
  ConversationDetail,
  MessageWithSources,
  MessageSource,
} from '../types/chat';

import { MessageStreamingState } from '../types/chat';

/**
 * 会话状态接口
 * 内部变量：conversations - 会话列表
 * 内部变量：currentConversation - 当前会话详情
 * 内部变量：messages - 当前会话消息列表
 * 内部变量：isLoadingConversations - 是否正在加载会话列表
 * 内部变量：sources - 当前消息的来源引用列表
 * 内部变量：useAgent - 是否启用智能体模式
 * 内部变量：isStreaming - 是否正在流式输出
 */
export interface ConversationState {
  // 属性
  conversations: Conversation[];
  currentConversation: ConversationDetail | null;
  messages: MessageWithSources[];
  isLoadingConversations: boolean;
  sources: MessageSource[];
  useAgent: boolean;
  isStreaming: boolean;

  // 会话操作方法
  loadConversations: () => Promise<void>;
  createConversation: (title?: string) => Promise<Conversation>;
  selectConversation: (id: number) => Promise<void>;
  deleteConversation: (id: number) => Promise<void>;
  updateConversationTitle: (id: number, title: string) => void;

  // 消息操作方法
  addMessage: (message: MessageWithSources) => void;
  updateLastMessage: (content: string) => void;
  setSources: (sources: MessageSource[]) => void;
  markStreamingComplete: () => void;
  clearMessages: () => void;

  // 智能体和流式状态方法
  toggleAgent: () => void;
  setStreaming: (streaming: boolean) => void;
}

/**
 * 文件级注释：对话持久化状态管理
 * 内部逻辑：使用Zustand管理会话和消息状态
 */
export const useConversationStore = create<ConversationState>((set, get) => ({
  // 内部变量：初始化状态
  conversations: [],
  currentConversation: null,
  messages: [],
  isLoadingConversations: false,
  sources: [],
  useAgent: false,
  isStreaming: false,

  /**
   * 函数级注释：加载会话列表
   * 内部逻辑：调用API获取会话列表 -> 更新状态
   */
  loadConversations: async () => {
    set({ isLoadingConversations: true });
    try {
      const { conversationService } = await import('../services/conversationService');
      const result = await conversationService.listConversations();
      set({
        conversations: result.conversations,
        isLoadingConversations: false
      });
    } catch (error) {
      console.error('Failed to load conversations:', error);
      set({ isLoadingConversations: false });
    }
  },

  /**
   * 函数级注释：创建新会话
   * 内部逻辑：调用API创建 -> 切换到新会话
   */
  createConversation: async (title?: string) => {
    try {
      const { conversationService } = await import('../services/conversationService');
      const newConv = await conversationService.createConversation({ title });
      set(state => ({
        conversations: [newConv, ...state.conversations],
        currentConversation: {
          conversation: newConv,
          messages: []
        },
        messages: []
      }));
      return newConv;
    } catch (error) {
      console.error('Failed to create conversation:', error);
      throw error;
    }
  },

  /**
   * 函数级注释：选择并加载会话
   * 内部逻辑：获取会话详情 -> 更新当前会话和消息
   */
  selectConversation: async (id: number) => {
    try {
      const { conversationService } = await import('../services/conversationService');
      const detail = await conversationService.getConversation(id);
      set({
        currentConversation: detail,
        messages: detail.messages
      });
    } catch (error) {
      console.error('Failed to load conversation:', error);
      throw error;
    }
  },

  /**
   * 函数级注释：删除会话
   * 内部逻辑：调用API删除 -> 从列表中移除
   */
  deleteConversation: async (id: number) => {
    try {
      const { conversationService } = await import('../services/conversationService');
      await conversationService.deleteConversation(id);
      set(state => {
        // 内部逻辑：从列表中移除
        const conversations = state.conversations.filter(c => c.id !== id);

        // 内部逻辑：如果删除的是当前会话，清空当前会话
        const currentConversation = state.currentConversation?.conversation.id === id
          ? null
          : state.currentConversation;

        // 内部逻辑：如果删除的是当前会话，清空消息
        const messages = state.currentConversation?.conversation.id === id
          ? []
          : state.messages;

        return {
          conversations,
          currentConversation,
          messages
        };
      });
    } catch (error) {
      console.error('Failed to delete conversation:', error);
      throw error;
    }
  },

  /**
   * 函数级注释：更新会话标题
   */
  updateConversationTitle: (id: number, title: string) => {
    set(state => ({
      conversations: state.conversations.map(c =>
        c.id === id ? { ...c, title } : c
      ),
      currentConversation: state.currentConversation?.conversation.id === id
        ? {
            ...state.currentConversation,
            conversation: {
              ...state.currentConversation.conversation,
              title
            }
          }
        : state.currentConversation
    }));
  },

  /**
   * 函数级注释：添加消息
   */
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, {
      ...message,
      streamingState: MessageStreamingState.IDLE
    }]
  })),

  /**
   * 函数级注释：更新最后一条消息
   */
  updateLastMessage: (content) => set((state) => {
    // Guard Clause：检查是否有消息
    if (state.messages.length === 0) {
      return state;
    }

    // 内部变量：创建新的消息列表，更新最后一条消息
    const updatedMessages = [...state.messages];
    const lastIndex = updatedMessages.length - 1;
    updatedMessages[lastIndex] = {
      ...updatedMessages[lastIndex],
      content: content,
      streamingState: MessageStreamingState.STREAMING,
    };

    return { messages: updatedMessages };
  }),

  /**
   * 函数级注释：设置来源引用
   * 内部逻辑：同时更新消息中的 sources 和本地 sources 状态
   */
  setSources: (sources) => set((state) => {
    // Guard Clause：检查是否有消息
    if (state.messages.length === 0) {
      return { sources };
    }

    // 内部变量：创建新的消息列表
    const updatedMessages = [...state.messages];
    const lastIndex = updatedMessages.length - 1;
    updatedMessages[lastIndex] = {
      ...updatedMessages[lastIndex],
      sources: sources
    };

    return { messages: updatedMessages, sources };
  }),

  /**
   * 函数级注释：标记流式完成
   */
  markStreamingComplete: () => set((state) => {
    // Guard Clause：检查是否有消息
    if (state.messages.length === 0) {
      return state;
    }

    // 内部变量：创建新的消息列表，更新最后一条消息的流式状态
    const updatedMessages = [...state.messages];
    const lastIndex = updatedMessages.length - 1;
    updatedMessages[lastIndex] = {
      ...updatedMessages[lastIndex],
      streamingState: MessageStreamingState.COMPLETED,
    };

    return { messages: updatedMessages };
  }),

  /**
   * 函数级注释：清空消息
   */
  clearMessages: () => set({ messages: [], currentConversation: null }),

  /**
   * 函数级注释：切换智能体模式
   * 内部逻辑：切换 useAgent 状态
   */
  toggleAgent: () => set((state) => ({ useAgent: !state.useAgent })),

  /**
   * 函数级注释：设置流式输出状态
   * 内部逻辑：更新 isStreaming 状态
   */
  setStreaming: (streaming: boolean) => set({ isStreaming: streaming }),
}));
