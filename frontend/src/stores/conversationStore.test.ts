/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：conversationStore 测试文件
 * 内部逻辑：测试会话持久化状态管理 Store 的功能
 * 测试策略：
 *   - 单元测试：测试每个状态和操作
 *   - Mock 测试：Mock API 服务测试异步操作
 *   - 边界测试：测试空会话列表等边界情况
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useConversationStore } from './conversationStore';
import type { Conversation, ConversationDetail, MessageWithSources, MessageSource } from '../types/chat';
import { MessageStreamingState } from '../types/chat';

// Mock conversationService
vi.mock('../services/conversationService', () => ({
  conversationService: {
    listConversations: vi.fn(),
    createConversation: vi.fn(),
    getConversation: vi.fn(),
    deleteConversation: vi.fn(),
  },
}));

describe('conversationStore', () => {
  /**
   * 函数级注释：每个测试前重置状态
   * 内部逻辑：重置 conversationStore 的状态，确保测试独立性
   */
  beforeEach(() => {
    // 重置状态
    useConversationStore.setState({
      conversations: [],
      currentConversation: null,
      messages: [],
      isLoadingConversations: false,
      sources: [],
      useAgent: false,
      isStreaming: false,
    });

    // 清除所有 mock
    vi.clearAllMocks();
  });

  describe('初始状态', () => {
    it('应该有正确的初始状态', () => {
      const state = useConversationStore.getState();

      expect(state.conversations).toEqual([]);
      expect(state.currentConversation).toBeNull();
      expect(state.messages).toEqual([]);
      expect(state.isLoadingConversations).toBe(false);
      expect(state.sources).toEqual([]);
      expect(state.useAgent).toBe(false);
      expect(state.isStreaming).toBe(false);
    });
  });

  describe('消息操作方法', () => {
    it('应该添加消息', () => {
      const message: MessageWithSources = {
        role: 'user',
        content: '测试消息',
      };

      useConversationStore.getState().addMessage(message);

      const messages = useConversationStore.getState().messages;
      expect(messages).toHaveLength(1);
      expect(messages[0]).toEqual({
        ...message,
        streamingState: MessageStreamingState.IDLE,
      });
    });

    it('应该更新最后一条消息', () => {
      useConversationStore.getState().addMessage({ role: 'assistant', content: '原始内容' });

      useConversationStore.getState().updateLastMessage('更新后的内容');

      const lastMessage = useConversationStore.getState().messages[0];
      expect(lastMessage.content).toBe('更新后的内容');
      expect(lastMessage.streamingState).toBe(MessageStreamingState.STREAMING);
    });

    it('应该在空消息列表时更新不执行任何操作', () => {
      const messagesLength = useConversationStore.getState().messages.length;

      useConversationStore.getState().updateLastMessage('新内容');

      expect(useConversationStore.getState().messages.length).toBe(messagesLength);
    });

    it('应该设置来源', () => {
      const sources: MessageSource[] = [
        {
          id: 1,
          file_name: 'test.pdf',
          text_segment: '测试内容',
          position: 0,
        },
      ];

      useConversationStore.getState().addMessage({ role: 'assistant', content: '回复' });
      useConversationStore.getState().setSources(sources);

      expect(useConversationStore.getState().sources).toEqual(sources);
      const lastMessage = useConversationStore.getState().messages[0];
      expect(lastMessage.sources).toEqual(sources);
    });

    it('应该在无消息时设置来源', () => {
      const sources: MessageSource[] = [
        {
          id: 1,
          file_name: 'test.pdf',
          text_segment: '测试内容',
          position: 0,
        },
      ];

      useConversationStore.getState().setSources(sources);

      expect(useConversationStore.getState().sources).toEqual(sources);
    });

    it('应该标记流式完成', () => {
      useConversationStore.getState().addMessage({
        role: 'assistant',
        content: '测试消息',
        streamingState: MessageStreamingState.STREAMING,
      });

      useConversationStore.getState().markStreamingComplete();

      expect(useConversationStore.getState().messages[0].streamingState).toBe(MessageStreamingState.COMPLETED);
    });

    it('应该在空消息列表时标记流式完成不执行任何操作', () => {
      const messagesLength = useConversationStore.getState().messages.length;

      useConversationStore.getState().markStreamingComplete();

      expect(useConversationStore.getState().messages.length).toBe(messagesLength);
    });

    it('应该只更新最后一条消息的流式状态', () => {
      useConversationStore.getState().addMessage({ role: 'user', content: '用户消息' });
      useConversationStore.getState().addMessage({ role: 'assistant', content: '助手消息1' });
      useConversationStore.getState().addMessage({ role: 'assistant', content: '助手消息2' });

      useConversationStore.getState().markStreamingComplete();

      const messages = useConversationStore.getState().messages;
      expect(messages[0].streamingState).toBe(MessageStreamingState.IDLE);
      expect(messages[1].streamingState).toBe(MessageStreamingState.IDLE);
      expect(messages[2].streamingState).toBe(MessageStreamingState.COMPLETED);
    });

    it('应该清空消息', () => {
      useConversationStore.getState().addMessage({ role: 'user', content: '消息1' });
      useConversationStore.getState().addMessage({ role: 'assistant', content: '回复1' });
      useConversationStore.getState().setSources([
        { id: 1, file_name: 'test.pdf', text_segment: '内容', position: 0 },
      ]);

      expect(useConversationStore.getState().messages).toHaveLength(2);
      expect(useConversationStore.getState().sources).toHaveLength(1);

      useConversationStore.getState().clearMessages();

      expect(useConversationStore.getState().messages).toHaveLength(0);
      expect(useConversationStore.getState().currentConversation).toBeNull();
    });

    it('应该正确处理多条消息', () => {
      const messages: MessageWithSources[] = [
        { role: 'user', content: '消息1' },
        { role: 'assistant', content: '回复1' },
        { role: 'user', content: '消息2' },
        { role: 'assistant', content: '回复2' },
      ];

      messages.forEach((msg) => {
        useConversationStore.getState().addMessage(msg);
      });

      expect(useConversationStore.getState().messages).toHaveLength(4);
      useConversationStore.getState().messages.forEach((msg, index) => {
        expect(msg.content).toEqual(messages[index].content);
        expect(msg.role).toEqual(messages[index].role);
        expect(msg.streamingState).toEqual(MessageStreamingState.IDLE);
      });
    });
  });

  describe('智能体和流式状态方法', () => {
    it('应该切换智能体模式', () => {
      expect(useConversationStore.getState().useAgent).toBe(false);

      useConversationStore.getState().toggleAgent();

      expect(useConversationStore.getState().useAgent).toBe(true);

      useConversationStore.getState().toggleAgent();

      expect(useConversationStore.getState().useAgent).toBe(false);
    });

    it('应该设置流式状态', () => {
      useConversationStore.getState().setStreaming(true);

      expect(useConversationStore.getState().isStreaming).toBe(true);

      useConversationStore.getState().setStreaming(false);

      expect(useConversationStore.getState().isStreaming).toBe(false);
    });
  });

  describe('会话操作方法', () => {
    it('应该更新会话标题', () => {
      const conversations: Conversation[] = [
        {
          id: 1,
          title: '原标题',
          use_agent: false,
          total_tokens: 0,
          total_cost: 0,
          created_at: '2024-01-01',
          updated_at: '2024-01-01',
          message_count: 0,
        },
      ];

      useConversationStore.setState({ conversations });

      useConversationStore.getState().updateConversationTitle(1, '新标题');

      expect(useConversationStore.getState().conversations[0].title).toBe('新标题');
    });

    it('应该更新当前会话的标题', () => {
      const currentConversation: ConversationDetail = {
        conversation: {
          id: 1,
          title: '原标题',
          use_agent: false,
          total_tokens: 0,
          total_cost: 0,
          created_at: '2024-01-01',
          updated_at: '2024-01-01',
          message_count: 0,
        },
        messages: [],
      };

      useConversationStore.setState({ currentConversation });

      useConversationStore.getState().updateConversationTitle(1, '新标题');

      expect(useConversationStore.getState().currentConversation?.conversation.title).toBe('新标题');
    });

    it('应该在删除会话时从列表中移除', async () => {
      const conversations: Conversation[] = [
        {
          id: 1,
          title: '会话1',
          use_agent: false,
          total_tokens: 0,
          total_cost: 0,
          created_at: '2024-01-01',
          updated_at: '2024-01-01',
          message_count: 0,
        },
        {
          id: 2,
          title: '会话2',
          use_agent: false,
          total_tokens: 0,
          total_cost: 0,
          created_at: '2024-01-01',
          updated_at: '2024-01-01',
          message_count: 0,
        },
      ];

      useConversationStore.setState({ conversations });

      // Mock API 调用
      const { conversationService } = await import('../services/conversationService');
      vi.mocked(conversationService.deleteConversation).mockResolvedValue(undefined);

      await useConversationStore.getState().deleteConversation(1);

      expect(useConversationStore.getState().conversations).toHaveLength(1);
      expect(useConversationStore.getState().conversations[0].id).toBe(2);
    });

    it('应该在删除当前会话时清空当前会话和消息', async () => {
      const conversations: Conversation[] = [
        {
          id: 1,
          title: '会话1',
          use_agent: false,
          total_tokens: 0,
          total_cost: 0,
          created_at: '2024-01-01',
          updated_at: '2024-01-01',
          message_count: 0,
        },
      ];

      const currentConversation: ConversationDetail = {
        conversation: conversations[0],
        messages: [
          { role: 'user', content: '消息1' },
          { role: 'assistant', content: '回复1' },
        ],
      };

      useConversationStore.setState({ conversations, currentConversation });

      // Mock API 调用
      const { conversationService } = await import('../services/conversationService');
      vi.mocked(conversationService.deleteConversation).mockResolvedValue(undefined);

      await useConversationStore.getState().deleteConversation(1);

      expect(useConversationStore.getState().currentConversation).toBeNull();
      expect(useConversationStore.getState().messages).toHaveLength(0);
    });

    it('应该在删除非当前会话时保留当前会话', async () => {
      const conversations: Conversation[] = [
        {
          id: 1,
          title: '会话1',
          use_agent: false,
          total_tokens: 0,
          total_cost: 0,
          created_at: '2024-01-01',
          updated_at: '2024-01-01',
          message_count: 0,
        },
        {
          id: 2,
          title: '会话2',
          use_agent: false,
          total_tokens: 0,
          total_cost: 0,
          created_at: '2024-01-01',
          updated_at: '2024-01-01',
          message_count: 0,
        },
      ];

      const currentConversation: ConversationDetail = {
        conversation: conversations[1],
        messages: [],
      };

      useConversationStore.setState({ conversations, currentConversation });

      // Mock API 调用
      const { conversationService } = await import('../services/conversationService');
      vi.mocked(conversationService.deleteConversation).mockResolvedValue(undefined);

      await useConversationStore.getState().deleteConversation(1);

      expect(useConversationStore.getState().currentConversation).not.toBeNull();
      expect(useConversationStore.getState().currentConversation?.conversation.id).toBe(2);
    });
  });
});
