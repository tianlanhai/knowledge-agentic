/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：通用聊天逻辑 Hook
 * 内部逻辑：提取 useChat 和 useConversation 中的共同流式聊天逻辑
 * 设计模式：模板方法模式 + 高阶函数模式
 * 职责：统一管理流式聊天的核心流程
 */

import { useState, useCallback } from 'react';
import type { Message } from '../types/chat';
import type { MessageWithSources, MessageSource } from '../types/chat';
import type { SourceDetail } from '../types/chat';
import type { SSECallbacks } from '../utils/sseHandler';

/**
 * 类型定义：流式发送消息函数签名
 * 内部逻辑：定义不同场景下发送消息的函数接口
 */
export type StreamSendMessageFn<TMessage = Message> = (
  content: string,
  callbacks: SSECallbacks<string, any>
) => Promise<void>;

/**
 * 类型定义：聊天逻辑配置选项
 * 内部逻辑：配置化聊天行为
 */
export interface ChatLogicOptions<TMessage = Message> {
  /**
   * 发送消息的函数
   * 内部逻辑：由调用者提供具体的发送实现
   */
  sendMessageFn: StreamSendMessageFn<TMessage>;

  /**
   * 是否启用智能体模式（可选）
   */
  useAgent?: boolean;

  /**
   * 消息列表（用于构建历史记录）
   */
  messages: TMessage[];
}

/**
 * 类型定义：聊天逻辑返回值
 * 内部逻辑：统一返回接口
 */
export interface ChatLogicResult {
  /** 加载状态 */
  loading: boolean;
  /** 发送消息方法 */
  sendMessage: (content: string) => Promise<void>;
  /** 流式发送消息方法 */
  streamSendMessage: (content: string) => Promise<void>;
}

/**
 * 函数级注释：创建通用聊天逻辑 Hook
 * 内部逻辑：封装流式聊天的核心流程，支持配置化
 * 设计模式：工厂模式 + 模板方法模式
 *
 * 参数：
 *   options - 聊天逻辑配置选项
 *
 * 返回值：聊天逻辑结果对象
 *
 * 使用示例：
 * ```typescript
 * // 在 useChat.ts 中使用
 * const chatLogic = useChatLogic({
 *   sendMessageFn: async (content, callbacks) => {
 *     return chatService.streamChatCompletion(
 *       { message: content, history: messages, use_agent: useAgent },
 *       callbacks.onChunk,
 *       callbacks.onSources,
 *       callbacks.onDone
 *     );
 *   },
 *   messages,
 *   useAgent
 * });
 * ```
 */
export function useChatLogic<TMessage extends Message | MessageWithSources = Message>(
  options: ChatLogicOptions<TMessage>
): ChatLogicResult {
  // 内部变量：加载状态
  const [loading, setLoading] = useState(false);

  /**
   * 函数级注释：非流式发送消息
   * 内部逻辑：一次性发送并获取完整响应
   */
  const sendMessage = useCallback(async (content: string) => {
    setLoading(true);

    try {
      // 内部逻辑：调用发送函数
      await options.sendMessageFn(content, {
        onChunk: () => {
          // 非流式模式不需要处理chunk
        },
        onSources: () => {
          // 来源数据由sendMessagesFn内部处理
        },
        onDone: () => {
          // 完成回调
        },
      });
    } catch (error) {
      console.error('Send message error:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [options.sendMessageFn]);

  /**
   * 函数级注释：流式发送消息
   * 内部逻辑：发送消息并流式接收响应，实时更新
   * 设计模式：模板方法模式 - 定义标准流程
   *
   * 流程：
   *   1. 设置加载状态
   *   2. 添加用户消息
   *   3. 添加空的助手消息占位
   *   4. 累积流式内容
   *   5. 完成后标记状态
   */
  const streamSendMessage = useCallback(async (content: string) => {
    setLoading(true);

    // 内部变量：累积的助手消息内容
    let assistantMessage = '';

    // 内部逻辑：定义消息累积器
    const chunkAccumulator = (chunk: string) => {
      assistantMessage += chunk;
    };

    // 内部逻辑：调用配置的发送函数
    try {
      await options.sendMessageFn(content, {
        onChunk: chunkAccumulator,
        onSources: () => {
          // 来源数据由sendMessagesFn内部处理
        },
        onDone: () => {
          // 流式完成回调
        },
        onError: (error) => {
          console.error('Stream error:', error);
        },
      });
    } catch (error) {
      console.error('Stream send message error:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [options.sendMessageFn]);

  return {
    loading,
    sendMessage,
    streamSendMessage,
  };
}

/**
 * 类：聊天状态管理器
 * 内部逻辑：提供更高级的聊天状态管理
 * 设计模式：状态模式
 */
export class ChatStateManager {
  /**
   * 函数级注释：准备发送消息
   * 内部逻辑：设置加载状态，添加用户消息和助手占位消息
   *
   * 参数：
   *   setLoading - 设置加载状态的函数
   *   setStreaming - 设置流式状态的函数
   *   addMessage - 添加消息的函数
   *   content - 用户消息内容
   *
   * 返回值：void
   */
  static prepareSend(
    setLoading: (loading: boolean) => void,
    setStreaming: (streaming: boolean) => void,
    addMessage: (message: Message) => void,
    content: string
  ): void {
    setLoading(true);
    setStreaming(true);
    addMessage({ role: 'user', content });
    addMessage({ role: 'assistant', content: '' });
  }

  /**
   * 函数级注释：完成发送
   * 内部逻辑：重置加载和流式状态，标记流式完成
   *
   * 参数：
   *   setLoading - 设置加载状态的函数
   *   setStreaming - 设置流式状态的函数
   *   markStreamingComplete - 标记流式完成的函数
   *
   * 返回值：void
   */
  static completeSend(
    setLoading: (loading: boolean) => void,
    setStreaming: (streaming: boolean) => void,
    markStreamingComplete: () => void
  ): void {
    setLoading(false);
    setStreaming(false);
    markStreamingComplete();
  }

  /**
   * 函数级注释：处理错误
   * 内部逻辑：记录错误并完成发送
   *
   * 参数：
   *   error - 错误对象
   *   setLoading - 设置加载状态的函数
   *   setStreaming - 设置流式状态的函数
   *   markStreamingComplete - 标记流式完成的函数
   *
   * 返回值：void
   */
  static handleError(
    error: unknown,
    setLoading: (loading: boolean) => void,
    setStreaming: (streaming: boolean) => void,
    markStreamingComplete: () => void
  ): void {
    console.error('Chat error:', error);
    ChatStateManager.completeSend(setLoading, setStreaming, markStreamingComplete);
  }
}

// 内部变量：导出所有公共接口
export default useChatLogic;
