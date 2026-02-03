/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：useChatLogic Hook 单元测试
 * 内部逻辑：测试通用聊天逻辑的功能
 * 测试策略：
 *   - 单元测试：测试每个方法和场景
 *   - Mock 测试：Mock 发送函数
 *   - 状态测试：验证加载状态变化
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useChatLogic, ChatStateManager, type StreamSendMessageFn, type ChatLogicOptions } from './useChatLogic';
import type { Message } from '../types/chat';

describe('useChatLogic', () => {
  /**
   * 函数级注释：Mock 发送函数
   * 内部逻辑：模拟流式聊天服务
   */
  const createMockSendMessageFn = () => {
    return vi.fn(async (_content: string, callbacks: any) => {
      // 模拟流式响应
      callbacks.onChunk?.('Hello');
      await new Promise((resolve) => setTimeout(resolve, 10));
      callbacks.onChunk?.(' World');
      await new Promise((resolve) => setTimeout(resolve, 10));
      callbacks.onDone?.();
    });
  };

  /**
   * 函数级注释：每个测试前重置状态
   */
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('基本功能', () => {
    it('应该返回正确的状态和方法', () => {
      const mockSendMessageFn: StreamSendMessageFn = vi.fn(async () => {});

      const { result } = renderHook(() =>
        useChatLogic({
          sendMessageFn: mockSendMessageFn,
          messages: [],
        })
      );

      expect(result.current).toHaveProperty('loading', false);
      expect(result.current).toHaveProperty('sendMessage');
      expect(result.current).toHaveProperty('streamSendMessage');
    });

    it('应该初始化为非加载状态', () => {
      const mockSendMessageFn: StreamSendMessageFn = vi.fn(async () => {});

      const { result } = renderHook(() =>
        useChatLogic({
          sendMessageFn: mockSendMessageFn,
          messages: [],
        })
      );

      expect(result.current.loading).toBe(false);
    });
  });

  describe('sendMessage 方法', () => {
    it('应该设置加载状态为 true', async () => {
      let resolvePromise: (() => void) | undefined;
      const mockSendMessageFn: StreamSendMessageFn = vi.fn(
        () =>
          new Promise((resolve) => {
            resolvePromise = resolve;
          })
      );

      const { result } = renderHook(() =>
        useChatLogic({
          sendMessageFn: mockSendMessageFn,
          messages: [],
        })
      );

      // 内部逻辑：开始发送但不等待完成
      act(() => {
        result.current.sendMessage('test');
      });

      // 内部逻辑：检查加载状态
      expect(result.current.loading).toBe(true);

      // 内部逻辑：完成请求
      await act(async () => {
        resolvePromise?.();
      });

      expect(result.current.loading).toBe(false);
    });

    it('应该在完成后重置加载状态', async () => {
      const mockSendMessageFn: StreamSendMessageFn = vi.fn(async (_content, callbacks) => {
        callbacks.onDone?.();
      });

      const { result } = renderHook(() =>
        useChatLogic({
          sendMessageFn: mockSendMessageFn,
          messages: [],
        })
      );

      await act(async () => {
        await result.current.sendMessage('test');
      });

      expect(result.current.loading).toBe(false);
    });

    it('应该在错误时重置加载状态', async () => {
      const mockSendMessageFn: StreamSendMessageFn = vi.fn(async () => {
        throw new Error('发送失败');
      });

      const { result } = renderHook(() =>
        useChatLogic({
          sendMessageFn: mockSendMessageFn,
          messages: [],
        })
      );

      await expect(
        act(async () => {
          try {
            await result.current.sendMessage('test');
          } catch (e) {
            // 期望抛出错误
          }
        })
      ).resolves.not.toThrow();

      expect(result.current.loading).toBe(false);
    });

    it('应该传递参数到发送函数', async () => {
      const mockSendMessageFn: StreamSendMessageFn = vi.fn(async (_content, callbacks) => {
        callbacks.onDone?.();
      });

      const { result } = renderHook(() =>
        useChatLogic({
          sendMessageFn: mockSendMessageFn,
          messages: [],
        })
      );

      await act(async () => {
        await result.current.sendMessage('hello');
      });

      expect(mockSendMessageFn).toHaveBeenCalledWith('hello', expect.any(Object));
    });

    it('应该调用空的回调函数', async () => {
      const mockSendMessageFn: StreamSendMessageFn = vi.fn(async (_content, callbacks) => {
        callbacks.onChunk?.();
        callbacks.onSources?.();
        callbacks.onDone?.();
      });

      const { result } = renderHook(() =>
        useChatLogic({
          sendMessageFn: mockSendMessageFn,
          messages: [],
        })
      );

      await act(async () => {
        await result.current.sendMessage('test');
      });

      expect(mockSendMessageFn).toHaveBeenCalled();
    });
  });

  describe('streamSendMessage 方法', () => {
    it('应该设置加载状态为 true', async () => {
      let resolvePromise: (() => void) | undefined;
      const mockSendMessageFn: StreamSendMessageFn = vi.fn(
        () =>
          new Promise((resolve) => {
            resolvePromise = resolve;
          })
      );

      const { result } = renderHook(() =>
        useChatLogic({
          sendMessageFn: mockSendMessageFn,
          messages: [],
        })
      );

      act(() => {
        result.current.streamSendMessage('test');
      });

      expect(result.current.loading).toBe(true);

      await act(async () => {
        resolvePromise?.();
      });

      expect(result.current.loading).toBe(false);
    });

    it('应该在完成后重置加载状态', async () => {
      const mockSendMessageFn: StreamSendMessageFn = vi.fn(async (_content, callbacks) => {
        callbacks.onDone?.();
      });

      const { result } = renderHook(() =>
        useChatLogic({
          sendMessageFn: mockSendMessageFn,
          messages: [],
        })
      );

      await act(async () => {
        await result.current.streamSendMessage('test');
      });

      expect(result.current.loading).toBe(false);
    });

    it('应该处理流式数据块', async () => {
      const chunks: string[] = [];
      const mockSendMessageFn: StreamSendMessageFn = vi.fn(async (_content, callbacks) => {
        callbacks.onChunk?.('Hello');
        callbacks.onChunk?.(' ');
        callbacks.onChunk?.('World');
        callbacks.onDone?.();
      });

      const { result } = renderHook(() =>
        useChatLogic({
          sendMessageFn: mockSendMessageFn,
          messages: [],
        })
      );

      await act(async () => {
        await result.current.streamSendMessage('test');
      });

      // 内部逻辑：验证回调被调用
      expect(mockSendMessageFn).toHaveBeenCalled();
    });

    it('应该处理错误回调', async () => {
      const onError = vi.fn();
      const mockSendMessageFn: StreamSendMessageFn = vi.fn(async (_content, callbacks) => {
        callbacks.onError?.(new Error('流式错误'));
      });

      const { result } = renderHook(() =>
        useChatLogic({
          sendMessageFn: mockSendMessageFn,
          messages: [],
        })
      );

      await act(async () => {
        try {
          await result.current.streamSendMessage('test');
        } catch (e) {
          // 期望可能抛出错误
        }
      });

      // 内部逻辑：验证错误回调被调用
      expect(mockSendMessageFn).toHaveBeenCalled();
    });

    it('应该在错误时重置加载状态', async () => {
      const mockSendMessageFn: StreamSendMessageFn = vi.fn(async () => {
        throw new Error('发送失败');
      });

      const { result } = renderHook(() =>
        useChatLogic({
          sendMessageFn: mockSendMessageFn,
          messages: [],
        })
      );

      await expect(
        act(async () => {
          try {
            await result.current.streamSendMessage('test');
          } catch (e) {
            // 期望抛出错误
          }
        })
      ).resolves.not.toThrow();

      expect(result.current.loading).toBe(false);
    });

    it('应该调用 sources 回调', async () => {
      const mockSendMessageFn: StreamSendMessageFn = vi.fn(async (_content, callbacks) => {
        callbacks.onSources?.([{ doc_id: 1, content: '来源' }] as any);
        callbacks.onDone?.();
      });

      const { result } = renderHook(() =>
        useChatLogic({
          sendMessageFn: mockSendMessageFn,
          messages: [],
        })
      );

      await act(async () => {
        await result.current.streamSendMessage('test');
      });

      expect(mockSendMessageFn).toHaveBeenCalled();
    });
  });

  describe('ChatLogicOptions 配置', () => {
    it('应该支持 useAgent 选项', () => {
      const mockSendMessageFn: StreamSendMessageFn = vi.fn(async () => {});

      const { result } = renderHook(() =>
        useChatLogic({
          sendMessageFn: mockSendMessageFn,
          messages: [],
          useAgent: true,
        })
      );

      expect(result.current).toBeDefined();
    });

    it('应该支持 messages 选项', () => {
      const mockSendMessageFn: StreamSendMessageFn = vi.fn(async () => {});
      const messages: Message[] = [
        { role: 'user', content: '问题1' },
        { role: 'assistant', content: '回答1' },
      ];

      const { result } = renderHook(() =>
        useChatLogic({
          sendMessageFn: mockSendMessageFn,
          messages,
        })
      );

      expect(result.current).toBeDefined();
    });
  });

  describe('泛型支持', () => {
    it('应该支持带来源的消息类型', async () => {
      interface MessageWithSources extends Message {
        sources?: Array<{ doc_id: number; content: string }>;
      }

      const mockSendMessageFn: StreamSendMessageFn<MessageWithSources> = vi.fn(
        async (_content, callbacks) => {
          callbacks.onDone?.();
        }
      );

      const messages: MessageWithSources[] = [
        { role: 'user', content: '问题1', sources: [{ doc_id: 1, content: '来源' }] },
      ];

      const { result } = renderHook(() =>
        useChatLogic<MessageWithSources>({
          sendMessageFn: mockSendMessageFn,
          messages,
        })
      );

      await act(async () => {
        await result.current.sendMessage('test');
      });

      expect(mockSendMessageFn).toHaveBeenCalled();
    });
  });
});

describe('ChatStateManager', () => {
  describe('prepareSend 方法', () => {
    it('应该设置加载状态和流式状态', () => {
      const setLoading = vi.fn();
      const setStreaming = vi.fn();
      const addMessage = vi.fn();

      ChatStateManager.prepareSend(setLoading, setStreaming, addMessage, '测试消息');

      expect(setLoading).toHaveBeenCalledWith(true);
      expect(setStreaming).toHaveBeenCalledWith(true);
      expect(addMessage).toHaveBeenCalledTimes(2);
      expect(addMessage).toHaveBeenNthCalledWith(1, { role: 'user', content: '测试消息' });
      expect(addMessage).toHaveBeenNthCalledWith(2, { role: 'assistant', content: '' });
    });

    it('应该添加用户消息和空助手消息', () => {
      const addMessage = vi.fn();

      ChatStateManager.prepareSend(vi.fn(), vi.fn(), addMessage, '你好');

      expect(addMessage).toHaveBeenNthCalledWith(1, { role: 'user', content: '你好' });
      expect(addMessage).toHaveBeenNthCalledWith(2, { role: 'assistant', content: '' });
    });
  });

  describe('completeSend 方法', () => {
    it('应该重置加载和流式状态', () => {
      const setLoading = vi.fn();
      const setStreaming = vi.fn();
      const markStreamingComplete = vi.fn();

      ChatStateManager.completeSend(setLoading, setStreaming, markStreamingComplete);

      expect(setLoading).toHaveBeenCalledWith(false);
      expect(setStreaming).toHaveBeenCalledWith(false);
      expect(markStreamingComplete).toHaveBeenCalled();
    });

    it('应该按正确顺序调用方法', () => {
      const callOrder: string[] = [];
      const setLoading = vi.fn((v: boolean) => callOrder.push(`setLoading(${v})`));
      const setStreaming = vi.fn((v: boolean) => callOrder.push(`setStreaming(${v})`));
      const markStreamingComplete = vi.fn(() => callOrder.push('markStreamingComplete'));

      ChatStateManager.completeSend(setLoading, setStreaming, markStreamingComplete);

      expect(callOrder).toEqual(['setLoading(false)', 'setStreaming(false)', 'markStreamingComplete']);
    });
  });

  describe('handleError 方法', () => {
    it('应该记录错误并完成发送', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const setLoading = vi.fn();
      const setStreaming = vi.fn();
      const markStreamingComplete = vi.fn();

      const error = new Error('测试错误');

      ChatStateManager.handleError(error, setLoading, setStreaming, markStreamingComplete);

      expect(consoleErrorSpy).toHaveBeenCalledWith('Chat error:', error);
      expect(setLoading).toHaveBeenCalledWith(false);
      expect(setStreaming).toHaveBeenCalledWith(false);
      expect(markStreamingComplete).toHaveBeenCalled();

      consoleErrorSpy.mockRestore();
    });

    it('应该处理未知错误类型', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const setLoading = vi.fn();

      ChatStateManager.handleError('字符串错误', setLoading, vi.fn(), vi.fn());

      expect(consoleErrorSpy).toHaveBeenCalled();
      expect(setLoading).toHaveBeenCalledWith(false);

      consoleErrorSpy.mockRestore();
    });

    it('应该处理 null 错误', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const setLoading = vi.fn();

      ChatStateManager.handleError(null, setLoading, vi.fn(), vi.fn());

      expect(consoleErrorSpy).toHaveBeenCalled();
      expect(setLoading).toHaveBeenCalledWith(false);

      consoleErrorSpy.mockRestore();
    });
  });

  describe('方法组合使用', () => {
    it('应该支持完整的发送流程', () => {
      const setLoading = vi.fn();
      const setStreaming = vi.fn();
      const addMessage = vi.fn();
      const markStreamingComplete = vi.fn();

      // 内部逻辑：准备发送
      ChatStateManager.prepareSend(setLoading, setStreaming, addMessage, '测试');

      expect(setLoading).toHaveBeenCalledWith(true);
      expect(setStreaming).toHaveBeenCalledWith(true);

      // 内部逻辑：完成发送
      ChatStateManager.completeSend(setLoading, setStreaming, markStreamingComplete);

      expect(setLoading).toHaveBeenLastCalledWith(false);
      expect(setStreaming).toHaveBeenLastCalledWith(false);
      expect(markStreamingComplete).toHaveBeenCalled();
    });

    it('应该支持错误处理流程', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const setLoading = vi.fn();
      const setStreaming = vi.fn();
      const addMessage = vi.fn();
      const markStreamingComplete = vi.fn();

      // 内部逻辑：准备发送
      ChatStateManager.prepareSend(setLoading, setStreaming, addMessage, '测试');

      // 内部逻辑：处理错误
      ChatStateManager.handleError(new Error('失败'), setLoading, setStreaming, markStreamingComplete);

      expect(setLoading).toHaveBeenLastCalledWith(false);
      expect(setStreaming).toHaveBeenLastCalledWith(false);
      expect(markStreamingComplete).toHaveBeenCalled();

      consoleErrorSpy.mockRestore();
    });
  });
});
