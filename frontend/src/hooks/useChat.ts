/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：聊天Hook（重构版）
 * 内部逻辑：封装聊天相关状态和操作方法，集成状态机管理
 * 设计模式：外观模式 + 状态模式 + 适配器模式
 * 重构说明：
 *   - 使用状态机驱动聊天流程
 *   - 提供状态感知的 API
 *   - 支持错误处理和重试
 *   - 使用适配器模式解耦服务层
 */

import { useCallback } from 'react';
import { useChatStore, useChatMachineState, ChatStateSelectors } from '../stores/chatStore';
import { chatAdapter } from '../core/adapters';
import type { Message, SourceDetail } from '../types/chat';

/**
 * Hook: 使用聊天功能
 * 内部逻辑：提供完整的聊天功能，包括发送消息、状态管理、错误处理
 * 返回值：聊天状态和方法
 */
export const useChat = () => {
  // 内部变量：从 store 中获取状态和方法
  const {
    messages,
    sources,
    addMessage,
    updateLastMessage,
    setSources,
    transition,
    stateMachine,
    useAgent
  } = useChatStore();

  // 内部变量：获取状态机状态
  const machineState = useChatMachineState();

  /**
   * 函数级注释：发送流式消息（状态机驱动）
   * 参数：
   *   content - 消息内容
   * 返回值：Promise<void>
   */
  const streamSendMessage = useCallback(async (content: string) => {
    // 内部逻辑：检查是否可以发送
    if (!machineState.canTransition('send')) {
      console.warn('[useChat] 当前状态不允许发送消息:', machineState.currentState);
      return;
    }

    // 内部变量：累积助手消息内容
    let assistantMessage = '';

    try {
      // 内部逻辑：状态转换 - 准备发送
      await transition('send');

      // 内部逻辑：添加用户消息
      addMessage({ role: 'user', content });

      // 内部逻辑：添加空的助手消息（用于流式更新）
      addMessage({ role: 'assistant', content: '' });

      // 内部逻辑：状态转换 - 开始接收
      await transition('receive_start');

      // 内部逻辑：使用适配器调用流式对话服务（解耦）
      await chatAdapter.streamSendMessage(
        {
          message: content,
          history: messages,
          use_agent: useAgent,
          stream: true,
        },
        {
          onChunk: async (chunk: string) => {
            assistantMessage += chunk;
            updateLastMessage(assistantMessage);
            await transition('stream_chunk');
          },
          onSources: (sources: SourceDetail[]) => {
            setSources(sources);
          },
          onComplete: async () => {
            await transition('stream_end');
            await transition('success');
          },
        }
      );
    } catch (error) {
      // 内部逻辑：错误处理
      console.error('[useChat] Stream chat error:', error);
      await stateMachine.error(error as Error);

      // 内部逻辑：检查是否可以重试
      if (machineState.context.retryCount! < (machineState.context.maxRetries ?? 3)) {
        // 内部逻辑：自动重试
        await transition('retry');
        // 内部逻辑：递归调用重试（实际项目中可加入延迟）
        // setTimeout(() => streamSendMessage(content), 1000);
      }
    }
  }, [messages, useAgent, machineState, transition, addMessage, updateLastMessage, setSources, stateMachine]);

  /**
   * 函数级注释：发送消息（非流式）
   * 参数：
   *   content - 消息内容
   * 返回值：Promise<void>
   */
  const sendMessage = useCallback(async (content: string) => {
    // 内部逻辑：检查是否可以发送
    if (!machineState.canTransition('send')) {
      console.warn('[useChat] 当前状态不允许发送消息:', machineState.currentState);
      return;
    }

    try {
      // 内部逻辑：状态转换 - 准备发送
      await transition('send');

      // 内部逻辑：添加用户消息
      addMessage({ role: 'user', content });

      // 内部逻辑：状态转换 - 开始接收
      await transition('receive_start');

      // 内部逻辑：使用适配器调用非流式对话服务（解耦）
      const response = await chatAdapter.sendMessage({
        message: content,
        history: messages,
        use_agent: useAgent,
        stream: false,
      });

      // 内部逻辑：添加助手回复
      addMessage({ role: 'assistant', content: response.answer });
      setSources(response.sources);

      // 内部逻辑：状态转换 - 成功
      await transition('success');
    } catch (error) {
      // 内部逻辑：错误处理
      console.error('[useChat] Chat error:', error);
      await stateMachine.error(error as Error);
    }
  }, [messages, useAgent, machineState, transition, addMessage, setSources, stateMachine]);

  /**
   * 函数级注释：取消当前操作
   * 返回值：Promise<boolean>
   */
  const cancel = useCallback(async () => {
    if (machineState.canTransition('cancel')) {
      return await transition('cancel');
    }
    return false;
  }, [machineState, transition]);

  /**
   * 函数级注释：重试当前操作
   * 返回值：Promise<boolean>
   */
  const retry = useCallback(async () => {
    if (machineState.canTransition('retry')) {
      return await transition('retry');
    }
    return false;
  }, [machineState, transition]);

  /**
   * 函数级注释：重置聊天状态
   * 返回值：void
   */
  const reset = useCallback(() => {
    stateMachine.reset();
  }, [stateMachine]);

  return {
    // ===== 消息相关 =====
    messages,
    sources,

    // ===== 智能体模式 =====
    useAgent,

    // ===== 状态机相关 =====
    /** 当前聊天状态 */
    chatState: machineState.currentState,
    /** 状态显示文本 */
    stateLabel: machineState.stateLabel,
    /** 是否正在加载 */
    loading: machineState.isLoading,
    /** 是否正在流式 */
    isStreaming: machineState.isStreaming,
    /** 是否有错误 */
    hasError: machineState.hasError,
    /** 是否空闲 */
    isIdle: machineState.isIdle,
    /** 状态上下文 */
    context: machineState.context,
    /** 可用事件列表 */
    availableEvents: machineState.availableEvents,

    // ===== 操作方法 =====
    sendMessage,
    streamSendMessage,
    cancel,
    retry,
    reset,
  };
};

/**
 * Hook: 使用聊天状态机（精简版）
 * 内部逻辑：只返回状态机相关状态，用于组件显示
 * 返回值：状态机状态
 */
export const useChatStateMachine = () => {
  return useChatMachineState();
};

/**
 * Hook: 使用聊天操作方法（精简版）
 * 内部逻辑：只返回操作方法，用于自定义组件
 * 返回值：操作方法集合
 */
export const useChatActions = () => {
  const { transition, stateMachine } = useChatStore();

  return {
    /** 发送消息事件 */
    send: () => transition('send'),
    /** 接收开始事件 */
    receiveStart: () => transition('receive_start'),
    /** 流式数据块事件 */
    streamChunk: () => transition('stream_chunk'),
    /** 流式结束事件 */
    streamEnd: () => transition('stream_end'),
    /** 成功事件 */
    success: () => transition('success'),
    /** 错误事件 */
    error: (err: Error) => stateMachine.error(err),
    /** 重试事件 */
    retry: () => transition('retry'),
    /** 取消事件 */
    cancel: () => transition('cancel'),
    /** 重置事件 */
    reset: () => stateMachine.reset(),
  };
};
