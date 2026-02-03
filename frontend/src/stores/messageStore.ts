/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：统一消息状态管理 Store
 * 内部逻辑：提取 chatStore 和 conversationStore 中的共同消息状态管理逻辑
 * 设计模式：组合模式 - 作为基础Store被其他Store组合使用
 * 职责：统一管理消息、来源、流式状态
 */

import { create } from 'zustand';
import type { Message, SourceDetail } from '../types/chat';
import type { MessageWithSources, MessageSource } from '../types/chat';
import { MessageStreamingState } from '../types/chat';

/**
 * 类型定义：消息类型（支持临时消息和持久化消息）
 * 内部逻辑：使用联合类型兼容两种消息格式
 */
export type MessageItem = Message | MessageWithSources;

/**
 * 类型定义：来源类型（支持两种来源格式）
 * 内部逻辑：使用联合类型兼容两种来源格式
 */
export type SourceItem = SourceDetail | MessageSource;

/**
 * 接口：消息状态
 * 内部逻辑：定义消息相关的状态和操作
 */
interface MessageState<TMessage extends MessageItem = MessageItem, TSource extends SourceItem = SourceItem> {
  // 属性
  messages: TMessage[];
  sources: TSource[];
  isStreaming: boolean;

  // 方法
  addMessage: (message: TMessage) => void;
  updateLastMessage: (content: string) => void;
  setSources: (sources: TSource[]) => void;
  setStreaming: (isStreaming: boolean) => void;
  markStreamingComplete: () => void;
  clearMessages: () => void;
}

/**
 * 函数级注释：创建消息 Store
 * 内部逻辑：统一的消息状态管理逻辑
 * 设计模式：工厂模式 - 创建配置化的消息Store
 * 参数：
 *   initialState - 可选的初始状态
 * 返回值：Zustand Store
 */
export const createMessageStore = <
  TMessage extends MessageItem = MessageItem,
  TSource extends SourceItem = SourceItem
>(initialState?: Partial<MessageState<TMessage, TSource>>) => {
  return create<MessageState<TMessage, TSource>>((set) => ({
    // 内部变量：初始化状态
    messages: [],
    sources: [],
    isStreaming: false,

    /**
     * 函数级注释：添加消息到列表
     * 参数：message - 要添加的消息对象
     * 内部逻辑：将新消息追加到消息列表末尾，设置默认流式状态为 IDLE
     */
    addMessage: (message: TMessage) => set((state) => ({
      messages: [...state.messages, { ...message, streamingState: MessageStreamingState.IDLE } as TMessage]
    })),

    /**
     * 函数级注释：更新最后一条消息的内容
     * 参数：content - 新的内容文本
     * 内部逻辑：更新最后一条消息的content字段，并设置流式状态为 STREAMING
     * 返回值：void
     */
    updateLastMessage: (content: string) => set((state) => {
      // Guard Clauses：检查是否有消息
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
      } as TMessage;

      return { messages: updatedMessages };
    }),

    /**
     * 函数级注释：设置来源引用
     * 参数：sources - 来源列表
     * 内部逻辑：更新sources状态
     */
    setSources: (sources: TSource[]) => set((state) => {
      // 内部逻辑：同时更新最后一条消息中的 sources（如果有）
      if (state.messages.length > 0) {
        const updatedMessages = [...state.messages];
        const lastIndex = updatedMessages.length - 1;
        updatedMessages[lastIndex] = {
          ...updatedMessages[lastIndex],
          sources: sources as any,
        } as TMessage;

        return { messages: updatedMessages, sources };
      }

      return { sources };
    }),

    /**
     * 函数级注释：设置流式输出状态
     * 参数：isStreaming - 是否正在流式输出
     * 内部逻辑：更新isStreaming状态
     */
    setStreaming: (isStreaming: boolean) => set({ isStreaming }),

    /**
     * 函数级注释：标记最后一条消息流式完成
     * 内部逻辑：将最后一条消息的 streamingState 设置为 COMPLETED
     */
    markStreamingComplete: () => set((state) => {
      // Guard Clauses：检查是否有消息
      if (state.messages.length === 0) {
        return state;
      }

      // 内部变量：创建新的消息列表，更新最后一条消息的流式状态
      const updatedMessages = [...state.messages];
      const lastIndex = updatedMessages.length - 1;
      updatedMessages[lastIndex] = {
        ...updatedMessages[lastIndex],
        streamingState: MessageStreamingState.COMPLETED,
      } as TMessage;

      return { messages: updatedMessages };
    }),

    /**
     * 函数级注释：清空消息
     * 内部逻辑：重置消息、来源和流式状态
     */
    clearMessages: () => set({ messages: [], sources: [], isStreaming: false }),

    // 内部逻辑：应用自定义初始状态
    ...initialState,
  }));
};

/**
 * 变量：默认消息Store（临时聊天使用）
 * 内部逻辑：使用 Message 类型的消息
 */
export const useMessageStore = createMessageStore<Message, SourceDetail>();

/**
 * 类：消息状态管理器
 * 内部逻辑：提供更高级的消息操作方法
 * 设计模式：外观模式 - 简化消息操作
 */
export class MessageStateManager {
  /**
   * 函数级注释：添加用户消息和助手占位消息
   * 内部逻辑：连续添加用户消息和空的助手消息
   * 参数：
   *   store - 消息Store实例
   *   userContent - 用户消息内容
   * 返回值：void
   */
  static addConversationPair<TMessage extends MessageItem, TSource extends SourceItem>(
    store: MessageState<TMessage, TSource>,
    userContent: string
  ): void {
    // 内部逻辑：添加用户消息
    store.addMessage({
      role: 'user',
      content: userContent,
      streamingState: MessageStreamingState.COMPLETED
    } as TMessage);

    // 内部逻辑：添加空的助手消息作为流式输出的占位
    store.addMessage({
      role: 'assistant',
      content: '',
      streamingState: MessageStreamingState.IDLE
    } as TMessage);
  }

  /**
   * 函数级注释：追加内容到最后一条消息
   * 内部逻辑：用于流式输出时追加内容，而非替换
   * 参数：
   *   store - 消息Store实例
   *   chunk - 新增的内容片段
   * 返回值：void
   */
  static appendToLastMessage<TMessage extends MessageItem, TSource extends SourceItem>(
    store: MessageState<TMessage, TSource>,
    chunk: string
  ): void {
    // Guard Clauses：检查是否有消息
    if (store.messages.length === 0) {
      return;
    }

    const lastMessage = store.messages[store.messages.length - 1];
    const updatedContent = lastMessage.content + chunk;

    store.updateLastMessage(updatedContent);
  }

  /**
   * 函数级注释：获取最后一条消息
   * 参数：store - 消息Store实例
   * 返回值：最后一条消息或null
   */
  static getLastMessage<TMessage extends MessageItem, TSource extends SourceItem>(
    store: MessageState<TMessage, TSource>
  ): TMessage | null {
    if (store.messages.length === 0) {
      return null;
    }
    return store.messages[store.messages.length - 1];
  }

  /**
   * 函数级注释：检查是否有正在进行的流式输出
   * 参数：store - 消息Store实例
   * 返回值：是否正在流式输出
   */
  static isStreaming<TMessage extends MessageItem, TSource extends SourceItem>(
    store: MessageState<TMessage, TSource>
  ): boolean {
    return store.isStreaming;
  }

  /**
   * 函数级注释：完成流式输出
   * 参数：store - 消息Store实例
   * 返回值：void
   */
  static completeStreaming<TMessage extends MessageItem, TSource extends SourceItem>(
    store: MessageState<TMessage, TSource>
  ): void {
    store.setStreaming(false);
    store.markStreamingComplete();
  }
}

// 内部变量：导出所有公共接口
export default useMessageStore;
