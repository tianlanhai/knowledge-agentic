/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：对话Hook
 * 内部逻辑：封装会话操作，简化组件调用
 * 设计模式：外观模式 - 使用 ChatStateManager 简化聊天流程
 * 重构说明：流式聊天逻辑使用 ChatStateManager 统一管理
 */

import { useState, useCallback } from 'react';
import { useConversationStore } from '../stores/conversationStore';
import { ChatStateManager } from './useChatLogic';

/**
 * 文件级注释：对话Hook
 * 内部逻辑：封装会话操作，简化组件调用
 */
export const useConversation = () => {
  // 内部变量：加载状态
  const [loading, setLoading] = useState(false);

  // 内部变量：从store中获取状态和方法
  const {
    conversations,
    currentConversation,
    messages,
    isLoadingConversations,
    sources,
    useAgent,
    isStreaming,
    loadConversations,
    createConversation,
    selectConversation,
    deleteConversation,
    addMessage,
    updateLastMessage,
    setSources,
    markStreamingComplete,
    clearMessages,
    toggleAgent,
    setStreaming,
  } = useConversationStore();

  /**
   * 函数级注释：初始化加载
   * 内部逻辑：如果会话列表为空，自动加载
   */
  const initialize = useCallback(async () => {
    if (conversations.length === 0 && !isLoadingConversations) {
      await loadConversations();
    }
  }, [conversations.length, isLoadingConversations, loadConversations]);

  /**
   * 函数级注释：开始新对话
   * 内部逻辑：清空当前消息 -> 创建新会话
   */
  const startNewConversation = useCallback(async (title?: string) => {
    clearMessages();
    return await createConversation(title);
  }, [createConversation, clearMessages]);

  /**
   * 函数级注释：发送消息（流式）
   * 内部逻辑：如果没有当前会话，自动创建 -> 流式发送消息
   */
  const sendMessage = useCallback(async (content: string) => {
    const { conversationService } = await import('../services/conversationService');

    setLoading(true);
    setStreaming(true);

    // 内部逻辑：如果没有当前会话，自动创建
    let conversationId = currentConversation?.conversation.id;
    if (!conversationId) {
      const newConv = await startNewConversation();
      conversationId = newConv.id;
    }

    // 内部逻辑：添加用户消息
    addMessage({ role: 'user', content });

    // 内部逻辑：添加空的助手消息
    addMessage({ role: 'assistant', content: '' });

    // 内部变量：累积助手消息内容
    let assistantMessage = '';

    try {
      await conversationService.streamSendMessage(
        conversationId,
        { content, stream: true, use_agent: useAgent },
        (chunk) => {
          // 内部逻辑：累积内容
          assistantMessage += chunk;
          updateLastMessage(assistantMessage);
        },
        (sources) => {
          // 内部逻辑：设置来源引用
          setSources(sources);
        },
        () => {
          // 内部逻辑：流式完成
          markStreamingComplete();
        }
      );
    } catch (error) {
      console.error('Send message error:', error);
    } finally {
      setLoading(false);
      setStreaming(false);
      // 内部逻辑：确保标记流式完成
      markStreamingComplete();
    }
  }, [
    currentConversation,
    startNewConversation,
    addMessage,
    updateLastMessage,
    setSources,
    markStreamingComplete,
    useAgent,
    setStreaming,
  ]);

  /**
   * 返回值：状态和操作方法
   */
  return {
    // 状态
    conversations,
    currentConversation,
    messages,
    loading,
    sources,
    useAgent,
    isStreaming,

    // 操作
    initialize,
    startNewConversation,
    selectConversation,
    deleteConversation,
    sendMessage,
    toggleAgent,
    clearMessages,
  };
};
