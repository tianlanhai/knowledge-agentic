/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：ChatAdapter 适配器模块单元测试
 * 内部逻辑：测试聊天服务适配器的所有功能
 * 测试策略：
 *   - 单元测试：测试每个适配器方法
 *   - Mock 测试：Mock 底层 chatService
 *   - 异常测试：验证错误处理逻辑
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ChatServiceAdapter, type IChatServicePort, type ChatRequest, type StreamCallbacks } from './ChatAdapter';
import type { Message, SourceDetail } from '../../types/chat';

// Mock chatService
const mockChatService = {
  chatCompletion: vi.fn(),
  streamChatCompletion: vi.fn(),
  getSources: vi.fn(),
};

describe('ChatServiceAdapter', () => {
  /**
   * 函数级注释：每个测试前重置 mocks
   * 内部逻辑：确保每个测试的独立性
   */
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('构造函数', () => {
    it('应该创建适配器实例', () => {
      const adapter = new ChatServiceAdapter(mockChatService as any);
      expect(adapter).toBeInstanceOf(ChatServiceAdapter);
    });

    it('应该使用默认 chatService', () => {
      const adapter = new ChatServiceAdapter();
      expect(adapter).toBeInstanceOf(ChatServiceAdapter);
    });
  });

  describe('sendMessage 方法', () => {
    it('应该成功发送消息并返回响应', async () => {
      // 内部变量：模拟响应数据
      const mockResponse: { answer: string; sources: SourceDetail[] } = {
        answer: '测试回复',
        sources: [{ doc_id: 1, content: '测试来源' }] as SourceDetail[],
      };

      mockChatService.chatCompletion.mockResolvedValue(mockResponse);

      const adapter = new ChatServiceAdapter(mockChatService as any);
      // 内部变量：请求参数
      const request: ChatRequest = {
        message: '你好',
        history: [] as Message[],
        use_agent: false,
        stream: false,
      };

      const response = await adapter.sendMessage(request);

      expect(response.answer).toBe('测试回复');
      expect(response.sources).toHaveLength(1);
      expect(mockChatService.chatCompletion).toHaveBeenCalledWith({
        message: '你好',
        history: [],
        use_agent: false,
        stream: false,
      });
    });

    it('应该处理空历史记录', async () => {
      const mockResponse: { answer: string; sources: SourceDetail[] } = {
        answer: '回复',
        sources: [],
      };

      mockChatService.chatCompletion.mockResolvedValue(mockResponse);

      const adapter = new ChatServiceAdapter(mockChatService as any);
      const request: ChatRequest = {
        message: '测试',
        stream: false,
      };

      await adapter.sendMessage(request);

      expect(mockChatService.chatCompletion).toHaveBeenCalledWith({
        message: '测试',
        history: [],
        use_agent: false,
        stream: false,
      });
    });

    it('应该使用智能体模式', async () => {
      const mockResponse: { answer: string; sources: SourceDetail[] } = {
        answer: 'Agent 回复',
        sources: [],
      };

      mockChatService.chatCompletion.mockResolvedValue(mockResponse);

      const adapter = new ChatServiceAdapter(mockChatService as any);
      const request: ChatRequest = {
        message: '测试',
        use_agent: true,
        stream: false,
      };

      await adapter.sendMessage(request);

      expect(mockChatService.chatCompletion).toHaveBeenCalledWith({
        message: '测试',
        history: [],
        use_agent: true,
        stream: false,
      });
    });

    it('应该传递历史记录', async () => {
      const mockResponse: { answer: string; sources: SourceDetail[] } = {
        answer: '回复',
        sources: [],
      };

      mockChatService.chatCompletion.mockResolvedValue(mockResponse);

      const adapter = new ChatServiceAdapter(mockChatService as any);
      const history: Message[] = [
        { role: 'user', content: '之前的问题' },
        { role: 'assistant', content: '之前的回答' },
      ];
      const request: ChatRequest = {
        message: '新问题',
        history,
        stream: false,
      };

      await adapter.sendMessage(request);

      expect(mockChatService.chatCompletion).toHaveBeenCalledWith({
        message: '新问题',
        history,
        use_agent: false,
        stream: false,
      });
    });

    it('应该在服务出错时抛出错误', async () => {
      const error = new Error('网络错误');
      mockChatService.chatCompletion.mockRejectedValue(error);

      const adapter = new ChatServiceAdapter(mockChatService as any);
      const request: ChatRequest = {
        message: '测试',
        stream: false,
      };

      await expect(adapter.sendMessage(request)).rejects.toThrow('网络错误');
    });
  });

  describe('streamSendMessage 方法', () => {
    it('应该成功发送流式消息', async () => {
      mockChatService.streamChatCompletion.mockResolvedValue(undefined);

      const adapter = new ChatServiceAdapter(mockChatService as any);
      const request: ChatRequest = {
        message: '测试',
        stream: true,
      };

      // 内部变量：回调函数
      const onChunk = vi.fn();
      const onSources = vi.fn();
      const onComplete = vi.fn();

      const callbacks: StreamCallbacks = {
        onChunk,
        onSources,
        onComplete,
      };

      await adapter.streamSendMessage(request, callbacks);

      expect(mockChatService.streamChatCompletion).toHaveBeenCalledWith(
        {
          message: '测试',
          history: [],
          use_agent: false,
          stream: true,
        },
        onChunk,
        onSources,
        onComplete
      );
    });

    it('应该处理没有 onChunk 回调的情况', async () => {
      mockChatService.streamChatCompletion.mockResolvedValue(undefined);

      const adapter = new ChatServiceAdapter(mockChatService as any);
      const request: ChatRequest = {
        message: '测试',
        stream: true,
      };

      const callbacks: StreamCallbacks = {
        onComplete: vi.fn(),
      };

      await adapter.streamSendMessage(request, callbacks);

      expect(mockChatService.streamChatCompletion).toHaveBeenCalled();
    });

    it('应该在出错时调用 onError 回调', async () => {
      const error = new Error('流式错误');
      mockChatService.streamChatCompletion.mockRejectedValue(error);

      const adapter = new ChatServiceAdapter(mockChatService as any);
      const request: ChatRequest = {
        message: '测试',
        stream: true,
      };

      const onError = vi.fn();
      const callbacks: StreamCallbacks = {
        onError,
      };

      await adapter.streamSendMessage(request, callbacks);

      expect(onError).toHaveBeenCalledWith(error);
    });

    it('应该在出错且没有 onError 回调时抛出错误', async () => {
      const error = new Error('流式错误');
      mockChatService.streamChatCompletion.mockRejectedValue(error);

      const adapter = new ChatServiceAdapter(mockChatService as any);
      const request: ChatRequest = {
        message: '测试',
        stream: true,
      };

      await expect(adapter.streamSendMessage(request, {})).rejects.toThrow('流式错误');
    });

    it('应该使用智能体模式', async () => {
      mockChatService.streamChatCompletion.mockResolvedValue(undefined);

      const adapter = new ChatServiceAdapter(mockChatService as any);
      const request: ChatRequest = {
        message: '测试',
        use_agent: true,
        stream: true,
      };

      await adapter.streamSendMessage(request, {});

      expect(mockChatService.streamChatCompletion).toHaveBeenCalledWith(
        expect.objectContaining({
          use_agent: true,
        }),
        expect.any(Function),
        undefined,
        undefined
      );
    });
  });

  describe('getSources 方法', () => {
    it('应该获取来源详情', async () => {
      const mockSources: SourceDetail[] = [
        { doc_id: 1, content: '来源1' } as SourceDetail,
        { doc_id: 2, content: '来源2' } as SourceDetail,
      ];

      mockChatService.getSources.mockResolvedValue(mockSources);

      const adapter = new ChatServiceAdapter(mockChatService as any);

      const sources = await adapter.getSources();

      expect(sources).toEqual(mockSources);
      expect(mockChatService.getSources).toHaveBeenCalledWith(undefined);
    });

    it('应该传递文档 ID', async () => {
      const mockSources: SourceDetail[] = [];
      mockChatService.getSources.mockResolvedValue(mockSources);

      const adapter = new ChatServiceAdapter(mockChatService as any);

      await adapter.getSources(123);

      expect(mockChatService.getSources).toHaveBeenCalledWith(123);
    });

    it('应该在获取来源出错时抛出错误', async () => {
      const error = new Error('获取来源失败');
      mockChatService.getSources.mockRejectedValue(error);

      const adapter = new ChatServiceAdapter(mockChatService as any);

      await expect(adapter.getSources()).rejects.toThrow('获取来源失败');
    });
  });

  describe('接口兼容性', () => {
    it('应该符合 IChatServicePort 接口', () => {
      const adapter: IChatServicePort = new ChatServiceAdapter(mockChatService as any);

      expect(adapter.sendMessage).toBeInstanceOf(Function);
      expect(adapter.streamSendMessage).toBeInstanceOf(Function);
      expect(adapter.getSources).toBeInstanceOf(Function);
    });
  });
});
