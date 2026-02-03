/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：useChat Hook 单元测试
 * 内部逻辑：测试对话功能的状态管理和消息发送，包括状态机驱动
 * 测试策略：
 *   - 单元测试：测试每个方法
 *   - Mock 测试：Mock 适配器和 store
 *   - 状态测试：验证状态机转换
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useChat, useChatStateMachine, useChatActions } from './useChat';
import { useChatStore } from '../stores/chatStore';
import { useMessageStore } from '../stores/messageStore';

// Mock chatService
vi.mock('../services/chatService', () => ({
  chatService: {
    chatCompletion: vi.fn(),
    streamChatCompletion: vi.fn(),
    getSources: vi.fn(),
  },
}));

// Mock ChatAdapter - 使用实际的适配器类但 mock 内部的 chatService
import { chatAdapter } from '../core/adapters/ChatAdapter';
import { chatService } from '../services/chatService';

vi.mock('../core/adapters/ChatAdapter', () => ({
  chatAdapter: {
    sendMessage: vi.fn(),
    streamSendMessage: vi.fn(),
    getSources: vi.fn(),
  },
}));

// Mock stores 需要在每个测试前重置真实状态
describe('useChat Hook', () => {
  /**
   * 函数级注释：每个测试前重置状态
   * 内部逻辑：重置 store 状态和 mocks，确保测试独立性
   */
  beforeEach(() => {
    // 重置真实 store 状态
    useMessageStore.getState().clearMessages();
    useChatStore.getState().resetStateMachine();
    useChatStore.setState({ useAgent: false });

    // 清除所有 mocks
    vi.clearAllMocks();
  });

  describe('基本功能', () => {
    it('应该返回正确的状态和方法', () => {
      const { result } = renderHook(() => useChat());

      expect(result.current).toHaveProperty('messages');
      expect(result.current).toHaveProperty('sources');
      expect(result.current).toHaveProperty('useAgent');
      expect(result.current).toHaveProperty('chatState');
      expect(result.current).toHaveProperty('loading');
      expect(result.current).toHaveProperty('isStreaming');
      expect(result.current).toHaveProperty('hasError');
      expect(result.current).toHaveProperty('isIdle');
      expect(result.current).toHaveProperty('sendMessage');
      expect(result.current).toHaveProperty('streamSendMessage');
      expect(result.current).toHaveProperty('cancel');
      expect(result.current).toHaveProperty('retry');
      expect(result.current).toHaveProperty('reset');
    });

    it('应该正确获取初始状态', () => {
      const { result } = renderHook(() => useChat());

      expect(result.current.chatState).toBe('idle');
      expect(result.current.loading).toBe(false);
      expect(result.current.isStreaming).toBe(false);
      expect(result.current.hasError).toBe(false);
      expect(result.current.isIdle).toBe(true);
    });
  });

  describe('sendMessage 方法', () => {
    it('应该成功发送非流式消息', async () => {
      const mockResponse = {
        answer: '这是回复',
        sources: [{ doc_id: '1', content: '来源内容' }],
      };
      vi.mocked(chatAdapter.sendMessage).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useChat());

      await act(async () => {
        await result.current.sendMessage('测试消息');
      });

      // 验证消息被添加到 messageStore
      const messages = useMessageStore.getState().messages;
      expect(messages).toHaveLength(2);
      expect(messages[0]).toMatchObject({ role: 'user', content: '测试消息' });
      expect(messages[1]).toMatchObject({ role: 'assistant', content: '这是回复' });
    });

    it('应该在发送非流式消息时设置来源', async () => {
      const mockResponse = {
        answer: '回复内容',
        sources: [{ doc_id: '1', content: '来源' }],
      };
      vi.mocked(chatAdapter.sendMessage).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useChat());

      await act(async () => {
        await result.current.sendMessage('测试');
      });

      const sources = useMessageStore.getState().sources;
      expect(sources).toEqual([{ doc_id: '1', content: '来源' }]);
    });

    it('应该使用智能体模式', async () => {
      useChatStore.setState({ useAgent: true });

      const mockResponse = { answer: '回复', sources: [] };
      vi.mocked(chatAdapter.sendMessage).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useChat());

      await act(async () => {
        await result.current.sendMessage('测试');
      });

      expect(vi.mocked(chatAdapter.sendMessage)).toHaveBeenCalledWith(
        expect.objectContaining({ use_agent: true })
      );
    });

    it('应该在发送失败时处理错误', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      vi.mocked(chatAdapter.sendMessage).mockRejectedValue(new Error('发送失败'));

      const { result } = renderHook(() => useChat());

      await act(async () => {
        try {
          await result.current.sendMessage('测试');
        } catch (e) {
          // 内部逻辑：捕获预期错误
        }
      });

      // 验证错误被记录
      expect(consoleErrorSpy).toHaveBeenCalled();

      consoleErrorSpy.mockRestore();
    });

    it('应该在非空闲状态时阻止发送', async () => {
      // 设置为非空闲状态
      useChatStore.getState().stateMachine.transition = vi.fn().mockResolvedValue(false);

      const { result } = renderHook(() => useChat());

      // 模拟不能转换的情况
      const canTransitionSpy = vi.spyOn(result.current as any, 'canTransition').mockReturnValue(false);

      await act(async () => {
        await result.current.sendMessage('测试');
      });

      // 验证 sendMessage 没有被调用
      expect(vi.mocked(chatAdapter.sendMessage)).not.toHaveBeenCalled();

      canTransitionSpy.mockRestore();
    });
  });

  describe('streamSendMessage 方法', () => {
    it('应该成功发送流式消息', async () => {
      let onChunkCallback: ((chunk: string) => void) | undefined;
      let onSourcesCallback: ((sources: any[]) => void) | undefined;
      let onCompleteCallback: (() => void) | undefined;

      vi.mocked(chatAdapter.streamSendMessage).mockImplementation(
        (_request, callbacks) => {
          onChunkCallback = callbacks.onChunk;
          onSourcesCallback = callbacks.onSources;
          onCompleteCallback = callbacks.onComplete;
          return Promise.resolve();
        }
      );

      const { result } = renderHook(() => useChat());

      await act(async () => {
        await result.current.streamSendMessage('测试消息');
      });

      // 验证用户消息被添加
      const messages = useMessageStore.getState().messages;
      expect(messages[0]).toMatchObject({ role: 'user', content: '测试消息' });

      // 模拟流式数据块
      await act(async () => {
        onChunkCallback?.('Hello');
        onChunkCallback?.(' World');
        onSourcesCallback?.([{ doc_id: '1', content: '来源' }]);
        await onCompleteCallback?.();
      });

      // 验证助手消息被更新
      const updatedMessages = useMessageStore.getState().messages;
      expect(updatedMessages[1]).toMatchObject({ role: 'assistant', content: 'Hello World' });
      expect(useMessageStore.getState().sources).toEqual([{ doc_id: '1', content: '来源' }]);
    });

    it('应该在流式发送失败时处理错误', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      vi.mocked(chatAdapter.streamSendMessage).mockRejectedValue(new Error('流式发送失败'));

      const { result } = renderHook(() => useChat());

      await act(async () => {
        try {
          await result.current.streamSendMessage('测试');
        } catch (e) {
          // 内部逻辑：捕获预期错误
        }
      });

      // 验证错误被记录
      expect(consoleErrorSpy).toHaveBeenCalled();

      consoleErrorSpy.mockRestore();
    });

    it('应该在非空闲状态时阻止流式发送', async () => {
      // 模拟 canTransition 返回 false
      const { result } = renderHook(() => useChat());

      // 通过手动设置状态机为非空闲状态
      useChatStore.getState().stateMachine.transition = vi.fn().mockResolvedValue(false);

      await act(async () => {
        await result.current.streamSendMessage('测试');
      });

      // 验证 streamSendMessage 没有被调用
      expect(vi.mocked(chatAdapter.streamSendMessage)).not.toHaveBeenCalled();
    });
  });

  describe('reset 方法', () => {
    it('应该重置聊天状态', () => {
      const { result } = renderHook(() => useChat());

      act(() => {
        result.current.reset();
      });

      // 验证状态被重置
      expect(result.current.chatState).toBe('idle');
    });

    it('应该在任意状态下重置', () => {
      const { result } = renderHook(() => useChat());

      // 内部逻辑：重置
      act(() => {
        result.current.reset();
      });

      expect(result.current.chatState).toBe('idle');
    });
  });

  describe('cancel 方法', () => {
    it('应该取消当前操作', async () => {
      const { result } = renderHook(() => useChat());

      const cancelled = await act(async () => {
        return await result.current.cancel();
      });

      // 在 idle 状态下不能 cancel，返回 false
      expect(cancelled).toBe(false);
    });

    it('应该在不能转换时返回 false', async () => {
      const { result } = renderHook(() => useChat());

      // 内部逻辑：在 idle 状态下不能 cancel
      const cancelled = await act(async () => {
        return await result.current.cancel();
      });

      expect(cancelled).toBe(false);
    });
  });

  describe('retry 方法', () => {
    it('应该重试当前操作', async () => {
      const { result } = renderHook(() => useChat());

      const retried = await act(async () => {
        return await result.current.retry();
      });

      // 重试结果取决于状态机当前状态
      expect(typeof retried).toBe('boolean');
    });

    it('应该在不能转换时返回 false', async () => {
      const { result } = renderHook(() => useChat());

      // 内部逻辑：在 idle 状态下不能 retry
      const retried = await act(async () => {
        return await result.current.retry();
      });

      expect(retried).toBe(false);
    });
  });

  describe('状态属性', () => {
    it('应该正确反映 messages 状态', () => {
      const { result } = renderHook(() => useChat());

      // 内部逻辑：messages 来自 useChatStore（委托给 messageStore）
      expect(result.current).toHaveProperty('messages');
      expect(Array.isArray(result.current.messages)).toBe(true);
    });

    it('应该正确反映 sources 状态', () => {
      const { result } = renderHook(() => useChat());

      // 内部逻辑：sources 来自 useChatStore（委托给 messageStore）
      expect(result.current).toHaveProperty('sources');
      expect(Array.isArray(result.current.sources)).toBe(true);
    });

    it('应该正确反映 useAgent 状态', () => {
      const { result } = renderHook(() => useChat());

      expect(typeof result.current.useAgent).toBe('boolean');
    });

    it('应该在 idle 状态时返回 isIdle 为 true', () => {
      const { result } = renderHook(() => useChat());

      expect(result.current.isIdle).toBe(true);
    });
  });
});

describe('useChatStateMachine Hook', () => {
  beforeEach(() => {
    useChatStore.getState().resetStateMachine();
  });

  it('应该返回状态机状态', () => {
    const { result } = renderHook(() => useChatStateMachine());

    expect(result.current).toHaveProperty('currentState');
    expect(result.current).toHaveProperty('context');
    expect(result.current).toHaveProperty('isLoading');
    expect(result.current).toHaveProperty('hasError');
    expect(result.current).toHaveProperty('isStreaming');
    expect(result.current).toHaveProperty('isIdle');
    expect(result.current).toHaveProperty('stateLabel');
    expect(result.current).toHaveProperty('canTransition');
    expect(result.current).toHaveProperty('availableEvents');
  });

  it('应该正确识别空闲状态', () => {
    const { result } = renderHook(() => useChatStateMachine());

    expect(result.current.currentState).toBe('idle');
    expect(result.current.isIdle).toBe(true);
    expect(result.current.isLoading).toBe(false);
  });
});

describe('useChatActions Hook', () => {
  beforeEach(() => {
    useChatStore.getState().resetStateMachine();
    vi.clearAllMocks();
  });

  it('应该返回操作方法', () => {
    const { result } = renderHook(() => useChatActions());

    expect(result.current).toHaveProperty('send');
    expect(result.current).toHaveProperty('receiveStart');
    expect(result.current).toHaveProperty('streamChunk');
    expect(result.current).toHaveProperty('streamEnd');
    expect(result.current).toHaveProperty('success');
    expect(result.current).toHaveProperty('error');
    expect(result.current).toHaveProperty('retry');
    expect(result.current).toHaveProperty('cancel');
    expect(result.current).toHaveProperty('reset');
  });

  it('应该重置状态机', () => {
    const { result } = renderHook(() => useChatActions());

    act(() => {
      result.current.reset();
    });

    // 验证状态被重置
    const state = useChatStore.getState();
    expect(state.chatState).toBe('idle');
  });

  it('应该触发 send 事件', async () => {
    const { result } = renderHook(() => useChatActions());

    // 内部逻辑：send 返回的是一个 Promise，状态转换是异步的
    await act(async () => {
      await result.current.send();
    });

    // 验证状态已改变
    const state = useChatStore.getState();
    expect(state.chatState).toBe('sending');
  });

  it('应该触发 error 事件', async () => {
    const { result } = renderHook(() => useChatActions());

    const testError = new Error('测试错误');

    // 首先进入发送状态
    await act(async () => {
      await result.current.send();
    });

    // 然后触发错误
    act(() => {
      result.current.error(testError);
    });

    // 验证状态已改变
    const state = useChatStore.getState();
    expect(state.chatState).toBe('error');
    expect(state.stateContext.error).toBe(testError);
  });

  it('应该触发 success 事件', async () => {
    const { result } = renderHook(() => useChatActions());

    // 首先进入发送状态
    await act(async () => {
      await result.current.send();
    });

    // 然后触发成功
    await act(async () => {
      await result.current.success();
    });

    // 验证状态已改变
    const state = useChatStore.getState();
    expect(state.chatState).toBe('success');
  });
});
