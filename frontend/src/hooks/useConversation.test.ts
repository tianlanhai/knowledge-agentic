/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：useConversation Hook 单元测试
 * 内部逻辑：测试会话持久化相关功能
 * 测试策略：
 *   - 单元测试：测试每个方法
 *   - Mock 测试：Mock conversationService
 *   - 状态测试：验证 store 状态变化
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useConversation } from './useConversation';
import { useConversationStore } from '../stores/conversationStore';

// Mock conversationService
vi.mock('../services/conversationService', () => ({
  conversationService: {
    listConversations: vi.fn(),
    createConversation: vi.fn(),
    getConversation: vi.fn(),
    deleteConversation: vi.fn(),
    streamSendMessage: vi.fn(),
  },
}));

describe('useConversation Hook', () => {
  /**
   * 函数级注释：每个测试前重置状态
   * 内部逻辑：重置 store 状态和 mocks，确保测试独立性
   */
  beforeEach(() => {
    // 重置 store 状态
    useConversationStore.setState({
      conversations: [],
      currentConversation: null,
      messages: [],
      isLoadingConversations: false,
      sources: [],
      useAgent: false,
      isStreaming: false,
    });

    // 清除所有 mocks
    vi.clearAllMocks();
  });

  describe('基本功能', () => {
    it('应该返回正确的状态和方法', () => {
      const { result } = renderHook(() => useConversation());

      expect(result.current).toHaveProperty('conversations');
      expect(result.current).toHaveProperty('currentConversation');
      expect(result.current).toHaveProperty('messages');
      expect(result.current).toHaveProperty('loading');
      expect(result.current).toHaveProperty('sources');
      expect(result.current).toHaveProperty('useAgent');
      expect(result.current).toHaveProperty('isStreaming');
      expect(result.current).toHaveProperty('initialize');
      expect(result.current).toHaveProperty('startNewConversation');
      expect(result.current).toHaveProperty('selectConversation');
      expect(result.current).toHaveProperty('deleteConversation');
      expect(result.current).toHaveProperty('sendMessage');
      expect(result.current).toHaveProperty('toggleAgent');
      expect(result.current).toHaveProperty('clearMessages');
    });

    it('应该正确获取初始状态', () => {
      const { result } = renderHook(() => useConversation());

      expect(result.current.conversations).toEqual([]);
      expect(result.current.currentConversation).toBeNull();
      expect(result.current.messages).toEqual([]);
      expect(result.current.loading).toBe(false);
      expect(result.current.isStreaming).toBe(false);
    });
  });

  describe('initialize 方法', () => {
    it('应该在会话列表为空时加载会话', async () => {
      const { conversationService } = await import('../services/conversationService');
      vi.mocked(conversationService.listConversations).mockResolvedValue({
        conversations: [
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
        ],
      });

      const { result } = renderHook(() => useConversation());

      await act(async () => {
        await result.current.initialize();
      });

      expect(conversationService.listConversations).toHaveBeenCalled();
      expect(result.current.conversations).toHaveLength(1);
    });

    it('应该在会话列表不为空时不重复加载', async () => {
      const { conversationService } = await import('../services/conversationService');

      // 设置已有会话
      useConversationStore.setState({
        conversations: [
          {
            id: 1,
            title: '已有会话',
            use_agent: false,
            total_tokens: 0,
            total_cost: 0,
            created_at: '2024-01-01',
            updated_at: '2024-01-01',
            message_count: 0,
          },
        ],
      });

      const { result } = renderHook(() => useConversation());

      await act(async () => {
        await result.current.initialize();
      });

      expect(conversationService.listConversations).not.toHaveBeenCalled();
    });
  });

  describe('startNewConversation 方法', () => {
    it('应该创建新会话并清空消息', async () => {
      const { conversationService } = await import('../services/conversationService');
      const newConversation = {
        id: 1,
        title: '新会话',
        use_agent: false,
        total_tokens: 0,
        total_cost: 0,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
        message_count: 0,
      };
      vi.mocked(conversationService.createConversation).mockResolvedValue(newConversation);

      const { result } = renderHook(() => useConversation());

      // 先添加一些消息
      useConversationStore.getState().addMessage({ role: 'user', content: '旧消息' });
      expect(useConversationStore.getState().messages).toHaveLength(1);

      await act(async () => {
        const resultConv = await result.current.startNewConversation('新会话');
        expect(resultConv).toEqual(newConversation);
      });

      // 验证消息被清空
      expect(result.current.messages).toHaveLength(0);
      // 验证会话被创建
      expect(conversationService.createConversation).toHaveBeenCalledWith({ title: '新会话' });
    });

    it('应该创建无标题的新会话', async () => {
      const { conversationService } = await import('../services/conversationService');
      vi.mocked(conversationService.createConversation).mockResolvedValue({
        id: 1,
        title: '',
        use_agent: false,
        total_tokens: 0,
        total_cost: 0,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
        message_count: 0,
      });

      const { result } = renderHook(() => useConversation());

      await act(async () => {
        await result.current.startNewConversation();
      });

      expect(conversationService.createConversation).toHaveBeenCalledWith({ title: undefined });
    });
  });

  describe('sendMessage 方法', () => {
    it('应该发送流式消息并更新状态', async () => {
      const { conversationService } = await import('../services/conversationService');
      const chunks = ['流式', '回答', '内容'];

      // 设置当前会话
      const currentConversation = {
        conversation: {
          id: 1,
          title: '测试会话',
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

      vi.mocked(conversationService.streamSendMessage).mockImplementation(
        async (_id, _req, onChunk, onSources, onComplete) => {
          for (const chunk of chunks) {
            onChunk?.(chunk);
          }
          onSources?.([]);
          onComplete?.();
        }
      );

      const { result } = renderHook(() => useConversation());

      await act(async () => {
        await result.current.sendMessage('测试问题');
      });

      // 验证消息被添加
      expect(result.current.messages).toHaveLength(2); // 用户消息 + 助手消息
      expect(result.current.messages[0].content).toBe('测试问题');
      expect(result.current.messages[1].content).toBe('流式回答内容');
    });

    it('应该在没有当前会话时自动创建', async () => {
      const { conversationService } = await import('../services/conversationService');
      const newConversation = {
        id: 1,
        title: '新会话',
        use_agent: false,
        total_tokens: 0,
        total_cost: 0,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
        message_count: 0,
      };
      vi.mocked(conversationService.createConversation).mockResolvedValue(newConversation);
      vi.mocked(conversationService.streamSendMessage).mockResolvedValue(undefined);

      const { result } = renderHook(() => useConversation());

      await act(async () => {
        await result.current.sendMessage('测试问题');
      });

      expect(conversationService.createConversation).toHaveBeenCalled();
      expect(conversationService.streamSendMessage).toHaveBeenCalled();
    });

    it('应该处理来源数据', async () => {
      const { conversationService } = await import('../services/conversationService');
      const sources = [
        {
          id: 1,
          file_name: 'test.pdf',
          text_segment: '来源内容',
          position: 0,
        },
      ];

      useConversationStore.setState({
        currentConversation: {
          conversation: {
            id: 1,
            title: '测试',
            use_agent: false,
            total_tokens: 0,
            total_cost: 0,
            created_at: '2024-01-01',
            updated_at: '2024-01-01',
            message_count: 0,
          },
          messages: [],
        },
      });

      vi.mocked(conversationService.streamSendMessage).mockImplementation(
        async (_id, _req, onChunk, onSources, onComplete) => {
          onChunk?.('回答');
          onSources?.(sources);
          onComplete?.();
        }
      );

      const { result } = renderHook(() => useConversation());

      await act(async () => {
        await result.current.sendMessage('测试问题');
      });

      expect(result.current.sources).toEqual(sources);
    });

    it('应该在智能体模式下发送消息', async () => {
      const { conversationService } = await import('../services/conversationService');

      useConversationStore.setState({
        currentConversation: {
          conversation: {
            id: 1,
            title: '测试',
            use_agent: false,
            total_tokens: 0,
            total_cost: 0,
            created_at: '2024-01-01',
            updated_at: '2024-01-01',
            message_count: 0,
          },
          messages: [],
        },
        useAgent: true,
      });

      vi.mocked(conversationService.streamSendMessage).mockImplementation(
        async (_id, req, _onChunk, _onSources, onComplete) => {
          expect(req.use_agent).toBe(true);
          onComplete?.();
        }
      );

      const { result } = renderHook(() => useConversation());

      await act(async () => {
        await result.current.sendMessage('测试问题');
      });
    });

    it('应该处理发送错误', async () => {
      const { conversationService } = await import('../services/conversationService');

      useConversationStore.setState({
        currentConversation: {
          conversation: {
            id: 1,
            title: '测试',
            use_agent: false,
            total_tokens: 0,
            total_cost: 0,
            created_at: '2024-01-01',
            updated_at: '2024-01-01',
            message_count: 0,
          },
          messages: [],
        },
      });

      vi.mocked(conversationService.streamSendMessage).mockRejectedValue(new Error('发送错误'));

      const { result } = renderHook(() => useConversation());

      await act(async () => {
        await result.current.sendMessage('测试问题');
      });

      // 验证消息仍然被添加
      expect(result.current.messages).toHaveLength(2);
      // 验证加载状态被重置
      expect(result.current.loading).toBe(false);
      expect(result.current.isStreaming).toBe(false);
    });
  });

  describe('selectConversation 方法', () => {
    it('应该选择并加载会话', async () => {
      const { conversationService } = await import('../services/conversationService');
      const conversationDetail = {
        conversation: {
          id: 1,
          title: '测试会话',
          use_agent: false,
          total_tokens: 0,
          total_cost: 0,
          created_at: '2024-01-01',
          updated_at: '2024-01-01',
          message_count: 2,
        },
        messages: [
          { role: 'user' as const, content: '问题' },
          { role: 'assistant' as const, content: '回答' },
        ],
      };
      vi.mocked(conversationService.getConversation).mockResolvedValue(conversationDetail);

      const { result } = renderHook(() => useConversation());

      await act(async () => {
        await result.current.selectConversation(1);
      });

      expect(conversationService.getConversation).toHaveBeenCalledWith(1);
      expect(result.current.currentConversation).toEqual(conversationDetail);
      expect(result.current.messages).toEqual(conversationDetail.messages);
    });
  });

  describe('deleteConversation 方法', () => {
    it('应该删除会话', async () => {
      const { conversationService } = await import('../services/conversationService');

      const conversations = [
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

      vi.mocked(conversationService.deleteConversation).mockResolvedValue(undefined);

      const { result } = renderHook(() => useConversation());

      await act(async () => {
        await result.current.deleteConversation(1);
      });

      expect(conversationService.deleteConversation).toHaveBeenCalledWith(1);
      expect(result.current.conversations).toHaveLength(1);
      expect(result.current.conversations[0].id).toBe(2);
    });
  });

  describe('toggleAgent 方法', () => {
    it('应该切换智能体模式', () => {
      const { result } = renderHook(() => useConversation());

      expect(result.current.useAgent).toBe(false);

      act(() => {
        result.current.toggleAgent();
      });

      expect(result.current.useAgent).toBe(true);

      act(() => {
        result.current.toggleAgent();
      });

      expect(result.current.useAgent).toBe(false);
    });
  });

  describe('clearMessages 方法', () => {
    it('应该清空消息', () => {
      const { result, rerender } = renderHook(() => useConversation());

      // 添加一些消息
      useConversationStore.getState().addMessage({ role: 'user', content: '消息1' });
      useConversationStore.getState().addMessage({ role: 'assistant', content: '回复1' });

      // 重新渲染以获取最新状态
      rerender();

      expect(result.current.messages).toHaveLength(2);

      act(() => {
        result.current.clearMessages();
      });

      // 重新渲染以获取最新状态
      rerender();

      expect(result.current.messages).toHaveLength(0);
    });
  });
});
