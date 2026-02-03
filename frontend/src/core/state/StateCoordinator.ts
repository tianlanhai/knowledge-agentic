/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：状态协调器模块
 * 内部逻辑：统一管理多个store的状态同步和变更通知
 * 设计模式：中介者模式（Mediator Pattern）+ 观察者模式（Observer Pattern）
 * 设计原则：单一职责原则（SRP）
 *
 * 实现说明：
 *   - 协调 chatStore、conversationStore、messageStore 之间的状态同步
 *   - 提供事件订阅机制
 *   - 解耦各个 store 之间的直接依赖
 */

import { useCallback, useEffect } from 'react';
import { useChatStore } from '../../stores/chatStore';
import { useConversationStore } from '../../stores/conversationStore';
import { useMessageStore } from '../../stores/messageStore';
import type { Message } from '../../types/chat';

/**
 * 类型：状态事件
 */
export type StateEvent =
  | 'message_added'
  | 'conversation_changed'
  | 'chat_started'
  | 'chat_completed'
  | 'error_occurred';

/**
 * 类型：事件监听器
 */
type EventListener = (event: StateEvent, payload?: any) => void;

/**
 * 类型：消息同步选项
 */
export interface MessageSyncOptions {
  /** 是否同步到聊天store */
  syncToChat?: boolean;
  /** 是否同步到会话store */
  syncToConversation?: boolean;
  /** 是否保存到数据库 */
  saveToDb?: boolean;
}

/**
 * 类：状态协调器
 * 内部逻辑：协调多个store之间的状态同步
 * 设计模式：中介者模式
 * 职责：
 *   1. 管理事件订阅
 *   2. 同步状态到多个store
 *   3. 解耦store之间的直接依赖
 */
export class StateCoordinator {
  /**
   * 内部变量：事件监听器列表
   */
  private listeners: Map<StateEvent, Set<EventListener>> = new Map();

  /**
   * 函数级注释：注册事件监听器
   * 参数：
   *   event - 事件类型
   *   listener - 监听器函数
   * 返回值：取消监听的函数
   */
  on(event: StateEvent, listener: EventListener): () => void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(listener);

    // 内部逻辑：返回取消监听函数
    return () => {
      this.listeners.get(event)?.delete(listener);
    };
  }

  /**
   * 函数级注释：触发事件
   * 参数：
   *   event - 事件类型
   *   payload - 事件载荷
   */
  emit(event: StateEvent, payload?: any): void {
    const listeners = this.listeners.get(event);
    if (listeners) {
      listeners.forEach(listener => listener(event, payload));
    }
  }

  /**
   * 函数级注释：同步消息到聊天store
   * 参数：
   *   message - 消息对象
   *   options - 同步选项
   */
  syncMessageToChat(message: Message, options: MessageSyncOptions = {}): void {
    const chatStore = useChatStore.getState();

    if (options.syncToChat !== false) {
      chatStore.addMessage(message);
    }

    this.emit('message_added', { message, options });
  }

  /**
   * 函数级注释：同步会话变更
   * 参数：
   *   conversationId - 会话ID
   */
  syncConversationChange(conversationId: string): void {
    const chatStore = useChatStore.getState();
    const conversationStore = useConversationStore.getState();

    // 内部逻辑：加载会话历史
    conversationStore.loadConversation(conversationId);

    this.emit('conversation_changed', { conversationId });
  }

  /**
   * 函数级注释：同步消息到所有相关store
   * 参数：
   *   message - 消息对象
   *   conversationId - 会话ID
   *   options - 同步选项
   */
  syncMessageToAll(message: Message, conversationId?: string, options: MessageSyncOptions = {}): void {
    // 内部逻辑：添加到消息store
    useMessageStore.getState().addMessage(message);

    // 内部逻辑：同步到聊天store
    if (options.syncToChat !== false) {
      this.syncMessageToChat(message, options);
    }

    // 内部逻辑：如果需要，保存到会话store
    if (conversationId && options.syncToConversation !== false) {
      const conversationStore = useConversationStore.getState();
      if (conversationStore.currentConversation) {
        conversationStore.addMessageToConversation(
          conversationStore.currentConversation.id,
          message
        );
      }
    }

    this.emit('message_added', { message, conversationId, options });
  }

  /**
   * 函数级注释：触发聊天开始事件
   * 参数：
   *   query - 用户查询
   */
  notifyChatStarted(query: string): void {
    this.emit('chat_started', { query });
  }

  /**
   * 函数级注释：触发聊天完成事件
   * 参数：
   *   answer - 回答内容
   *   sources - 来源列表
   */
  notifyChatCompleted(answer: string, sources: any[]): void {
    this.emit('chat_completed', { answer, sources });
  }

  /**
   * 函数级注释：触发错误事件
   * 参数：
   *   error - 错误对象
   */
  notifyError(error: Error): void {
    this.emit('error_occurred', { error });
  }
}

/**
 * 变量：全局状态协调器实例
 */
export const stateCoordinator = new StateCoordinator();

/**
 * Hook: 使用状态协调器
 * 内部逻辑：提供状态同步的便捷方法
 * 返回值：
 *   coordinator - 协调器实例
 *   addMessageSync - 同步消息到所有store
 *   syncConversation - 同步会话变更
 */
export const useStateCoordinator = () => {
  /**
   * 函数级注释：添加消息并同步到所有相关store
   * 参数：
   *   message - 消息对象
   *   conversationId - 可选的会话ID
   *   options - 同步选项
   */
  const addMessageSync = useCallback((
    message: Message,
    conversationId?: string,
    options?: MessageSyncOptions
  ) => {
    stateCoordinator.syncMessageToAll(message, conversationId, options);
  }, []);

  /**
   * 函数级注释：同步会话变更
   * 参数：
   *   conversationId - 会话ID
   */
  const syncConversation = useCallback((conversationId: string) => {
    stateCoordinator.syncConversationChange(conversationId);
  }, []);

  /**
   * 函数级注释：订阅事件
   * 参数：
   *   event - 事件类型
   *   listener - 监听器函数
   * 返回值：取消订阅的函数
   */
  const subscribe = useCallback((event: StateEvent, listener: EventListener) => {
    return stateCoordinator.on(event, listener);
  }, []);

  return {
    /** 协调器实例 */
    coordinator: stateCoordinator,
    /** 同步消息到所有store */
    addMessageSync,
    /** 同步会话变更 */
    syncConversation,
    /** 订阅事件 */
    subscribe,
  };
};

/**
 * Hook: 使用消息同步（简化版）
 * 内部逻辑：只提供消息同步相关功能
 * 返回值：消息同步方法
 */
export const useMessageSync = () => {
  const { addMessageSync } = useStateCoordinator();

  /**
   * 函数级注释：添加用户消息
   * 参数：
   *   content - 消息内容
   *   conversationId - 可选的会话ID
   */
  const addUserMessage = useCallback((content: string, conversationId?: string) => {
    addMessageSync({ role: 'user', content }, conversationId);
  }, [addMessageSync]);

  /**
   * 函数级注释：添加助手消息
   * 参数：
   *   content - 消息内容
   *   conversationId - 可选的会话ID
   */
  const addAssistantMessage = useCallback((content: string, conversationId?: string) => {
    addMessageSync({ role: 'assistant', content }, conversationId);
  }, [addMessageSync]);

  return {
    /** 同步消息到所有store */
    addMessageSync,
    /** 添加用户消息 */
    addUserMessage,
    /** 添加助手消息 */
    addAssistantMessage,
  };
};

/**
 * 默认导出
 */
export default stateCoordinator;
