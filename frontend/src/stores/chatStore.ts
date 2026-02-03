/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：聊天状态管理 Store（优化版）
 * 内部逻辑：管理聊天状态机和智能体模式，消息管理委托给 messageStore
 * 设计模式：状态模式 + 委托模式
 * 设计原则：单一职责原则、DRY
 *
 * 说明：
 *   - 状态机管理：管理聊天流程的状态转换
 *   - 智能体模式：控制是否启用智能体
 *   - 消息管理：委托给 messageStore，避免状态重复
 */

import { create } from 'zustand';
import type { Message, SourceDetail } from '../types/chat';
import { useMessageStore } from './messageStore';
import {
  ChatStateMachine,
  ChatStateMachineFactory,
  type ChatState as ChatStateMachineState,
  type ChatEvent,
  type ChatStateContext
} from '../core/stateMachine';

/**
 * 接口：聊天状态
 * 内部变量：专注于聊天流程控制，不重复存储消息状态
 */
export interface ChatState {
  // ===== 状态机相关 =====
  /** 内部变量：聊天状态机实例 */
  stateMachine: ChatStateMachine;
  /** 内部变量：当前聊天状态 */
  chatState: ChatStateMachineState;
  /** 内部变量：状态上下文 */
  stateContext: ChatStateContext;

  // ===== 聊天特有属性 =====
  /** 内部变量：是否启用智能体模式 */
  useAgent: boolean;

  // ===== 状态机操作方法 =====
  /** 内部变量：触发状态转换 */
  transition: (event: ChatEvent) => Promise<boolean>;
  /** 内部变量：检查是否可以执行事件 */
  canTransition: (event: ChatEvent) => boolean;
  /** 内部变量：获取可用的事件 */
  getAvailableEvents: () => ChatEvent[];
  /** 内部变量：重置状态机 */
  resetStateMachine: () => void;

  // ===== 聊天特有方法 =====
  /** 内部变量：切换智能体模式 */
  toggleAgent: () => void;

  // ===== 消息管理方法（委托给 messageStore）=====
  /** 内部变量：添加消息 */
  addMessage: (message: Message) => void;
  /** 内部变量：更新最后一条消息 */
  updateLastMessage: (content: string) => void;
  /** 内部变量：设置来源引用 */
  setSources: (sources: SourceDetail[]) => void;
  /** 内部变量：设置流式状态 */
  setStreaming: (isStreaming: boolean) => void;
  /** 内部变量：标记流式完成 */
  markStreamingComplete: () => void;
  /** 内部变量：清空消息 */
  clearMessages: () => void;
}

/**
 * 变量：聊天 Store
 * 内部逻辑：专注于状态机和智能体模式管理，消息操作委托给 messageStore
 */
export const useChatStore = create<ChatState>((set, get) => {
  // 内部变量：创建聊天状态机
  const stateMachine = ChatStateMachineFactory.create();

  // 内部逻辑：订阅状态机变更，同步到 Zustand 状态
  stateMachine.subscribe(({ from, to, event }) => {
    set({
      chatState: stateMachine.currentState,
      stateContext: stateMachine.context
    });
  });

  return {
    // ===== 状态机初始化 =====
    stateMachine,
    chatState: stateMachine.currentState,
    stateContext: stateMachine.context,

    // ===== 聊天特有状态 =====
    useAgent: false,

    // ===== 状态机操作方法 =====

    /**
     * 函数级注释：触发状态转换
     * 参数：event - 聊天事件
     * 返回值：转换是否成功
     */
    transition: async (event: ChatEvent) => {
      const success = await get().stateMachine.transition(event);
      if (success) {
        set({
          chatState: get().stateMachine.currentState,
          stateContext: get().stateMachine.context
        });
      }
      return success;
    },

    /**
     * 函数级注释：检查是否可以执行事件
     * 参数：event - 聊天事件
     * 返回值：是否可以执行
     */
    canTransition: (event: ChatEvent) => {
      return get().stateMachine.can(event);
    },

    /**
     * 函数级注释：获取可用的事件
     * 返回值：可用事件列表
     */
    getAvailableEvents: () => {
      return get().stateMachine.getAvailableEvents();
    },

    /**
     * 函数级注释：重置状态机
     * 返回值：void
     */
    resetStateMachine: () => {
      get().stateMachine.reset();
      set({
        chatState: get().stateMachine.currentState,
        stateContext: get().stateMachine.context
      });
    },

    // ===== 聊天特有方法 =====

    /**
     * 函数级注释：切换智能体模式
     * 返回值：void
     */
    toggleAgent: () => set((state) => ({ useAgent: !state.useAgent })),

    // ===== 消息管理方法（直接委托，不复制状态）=====

    /**
     * 函数级注释：添加消息
     * 参数：message - 消息对象
     */
    addMessage: (message: Message) => {
      useMessageStore.getState().addMessage(message);
    },

    /**
     * 函数级注释：更新最后一条消息
     * 参数：content - 新内容
     */
    updateLastMessage: (content: string) => {
      useMessageStore.getState().updateLastMessage(content);
    },

    /**
     * 函数级注释：设置来源引用
     * 参数：sources - 来源列表
     */
    setSources: (sources: SourceDetail[]) => {
      useMessageStore.getState().setSources(sources);
    },

    /**
     * 函数级注释：设置流式状态
     * 参数：isStreaming - 是否流式中
     */
    setStreaming: (isStreaming: boolean) => {
      useMessageStore.getState().setStreaming(isStreaming);
    },

    /**
     * 函数级注释：标记流式完成
     * 返回值：void
     */
    markStreamingComplete: () => {
      useMessageStore.getState().markStreamingComplete();
    },

    /**
     * 函数级注释：清空消息
     * 返回值：void
     */
    clearMessages: () => {
      useMessageStore.getState().clearMessages();
      get().stateMachine.reset();
      set({
        chatState: get().stateMachine.currentState,
        stateContext: get().stateMachine.context
      });
    },
  };
});

/**
 * 类级注释：聊天状态选择器
 * 内部逻辑：提供常用的状态选择器，优化性能
 */
export class ChatStateSelectors {
  /**
   * 函数级注释：选择加载状态
   * 参数：state - 聊天状态
   * 返回值：是否正在加载
   */
  static isLoading(state: ChatStateMachineState): boolean {
    return ['sending', 'receiving', 'streaming', 'retrying'].includes(state);
  }

  /**
   * 函数级注释：选择错误状态
   * 参数：state - 聊天状态
   * 返回值：是否有错误
   */
  static hasError(state: ChatStateMachineState): boolean {
    return state === 'error';
  }

  /**
   * 函数级注释：选择流式状态
   * 参数：state - 聊天状态
   * 返回值：是否正在流式
   */
  static isStreaming(state: ChatStateMachineState): boolean {
    return state === 'streaming';
  }

  /**
   * 函数级注释：选择空闲状态
   * 参数：state - 聊天状态
   * 返回值：是否空闲
   */
  static isIdle(state: ChatStateMachineState): boolean {
    return state === 'idle' || state === 'success';
  }

  /**
   * 函数级注释：获取状态显示文本
   * 参数：state - 聊天状态
   * 返回值：状态显示文本
   */
  static getStateLabel(state: ChatStateMachineState): string {
    const labels: Record<ChatStateMachineState, string> = {
      idle: '就绪',
      sending: '发送中...',
      receiving: '接收中...',
      streaming: '生成中...',
      success: '完成',
      error: '出错了',
      retrying: '重试中...'
    };
    return labels[state] ?? state;
  }
}

/**
 * Hook: 使用聊天状态机选择器
 * 返回值：计算后的状态
 */
export const useChatMachineState = () => {
  const { chatState, stateContext, canTransition, getAvailableEvents } = useChatStore();

  return {
    /** 当前聊天状态 */
    currentState: chatState,
    /** 状态上下文 */
    context: stateContext,
    /** 是否正在加载 */
    isLoading: ChatStateSelectors.isLoading(chatState),
    /** 是否有错误 */
    hasError: ChatStateSelectors.hasError(chatState),
    /** 是否正在流式 */
    isStreaming: ChatStateSelectors.isStreaming(chatState),
    /** 是否空闲 */
    isIdle: ChatStateSelectors.isIdle(chatState),
    /** 状态显示文本 */
    stateLabel: ChatStateSelectors.getStateLabel(chatState),
    /** 检查是否可以转换 */
    canTransition,
    /** 获取可用事件 */
    availableEvents: getAvailableEvents()
  };
};
