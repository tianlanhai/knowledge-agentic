/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：messageStore 测试文件
 * 内部逻辑：测试统一消息状态管理 Store 的功能
 * 测试策略：
 *   - 单元测试：测试每个状态和操作
 *   - 边界测试：测试空消息列表等边界情况
 *   - 类型测试：测试泛型支持
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { useMessageStore, createMessageStore, MessageStateManager } from './messageStore';
import type { Message, SourceDetail } from '../types/chat';
import { MessageStreamingState } from '../types/chat';

describe('messageStore', () => {
  /**
   * 函数级注释：每个测试前重置状态
   * 内部逻辑：重置 messageStore 的状态，确保测试独立性
   */
  beforeEach(() => {
    useMessageStore.getState().clearMessages();
  });

  describe('默认 Store', () => {
    it('应该有初始状态', () => {
      const state = useMessageStore.getState();

      expect(state.messages).toEqual([]);
      expect(state.sources).toEqual([]);
      expect(state.isStreaming).toBe(false);
    });

    it('应该添加消息', () => {
      const message: Message = { role: 'user', content: '测试消息' };

      useMessageStore.getState().addMessage(message);

      expect(useMessageStore.getState().messages).toHaveLength(1);
      expect(useMessageStore.getState().messages[0]).toEqual({
        ...message,
        streamingState: MessageStreamingState.IDLE,
      });
    });

    it('应该更新最后一条消息的内容', () => {
      useMessageStore.getState().addMessage({ role: 'assistant', content: '原始内容' });

      useMessageStore.getState().updateLastMessage('更新后的内容');

      expect(useMessageStore.getState().messages[0].content).toBe('更新后的内容');
      expect(useMessageStore.getState().messages[0].streamingState).toBe(MessageStreamingState.STREAMING);
    });

    it('应该在空消息列表时更新不执行任何操作', () => {
      const messagesLength = useMessageStore.getState().messages.length;

      useMessageStore.getState().updateLastMessage('新内容');

      expect(useMessageStore.getState().messages.length).toBe(messagesLength);
    });

    it('应该设置来源', () => {
      const sources: SourceDetail[] = [
        {
          doc_id: 1,
          file_name: 'test.pdf',
          text_segment: '测试内容',
          score: 0.9,
        },
      ];

      useMessageStore.getState().setSources(sources);

      expect(useMessageStore.getState().sources).toEqual(sources);
    });

    it('应该设置流式状态', () => {
      useMessageStore.getState().setStreaming(true);

      expect(useMessageStore.getState().isStreaming).toBe(true);

      useMessageStore.getState().setStreaming(false);

      expect(useMessageStore.getState().isStreaming).toBe(false);
    });

    it('应该标记流式完成', () => {
      useMessageStore.getState().addMessage({
        role: 'assistant',
        content: '测试消息',
        streamingState: MessageStreamingState.STREAMING,
      });

      useMessageStore.getState().markStreamingComplete();

      expect(useMessageStore.getState().messages[0].streamingState).toBe(MessageStreamingState.COMPLETED);
    });

    it('应该在空消息列表时标记流式完成不执行任何操作', () => {
      useMessageStore.getState().markStreamingComplete();

      expect(useMessageStore.getState().messages).toHaveLength(0);
    });

    it('应该只更新最后一条消息的流式状态', () => {
      useMessageStore.getState().addMessage({ role: 'user', content: '用户消息' });
      useMessageStore.getState().addMessage({ role: 'assistant', content: '助手消息1' });
      useMessageStore.getState().addMessage({ role: 'assistant', content: '助手消息2' });

      useMessageStore.getState().markStreamingComplete();

      const messages = useMessageStore.getState().messages;
      expect(messages[0].streamingState).toBe(MessageStreamingState.IDLE);
      expect(messages[1].streamingState).toBe(MessageStreamingState.IDLE);
      expect(messages[2].streamingState).toBe(MessageStreamingState.COMPLETED);
    });

    it('应该清空消息', () => {
      useMessageStore.getState().addMessage({ role: 'user', content: '消息1' });
      useMessageStore.getState().addMessage({ role: 'assistant', content: '回复1' });
      useMessageStore.getState().setSources([
        { doc_id: 1, file_name: 'test.pdf', text_segment: '内容', score: 0.9 },
      ]);
      useMessageStore.getState().setStreaming(true);

      expect(useMessageStore.getState().messages).toHaveLength(2);
      expect(useMessageStore.getState().sources).toHaveLength(1);
      expect(useMessageStore.getState().isStreaming).toBe(true);

      useMessageStore.getState().clearMessages();

      expect(useMessageStore.getState().messages).toHaveLength(0);
      expect(useMessageStore.getState().sources).toHaveLength(0);
      expect(useMessageStore.getState().isStreaming).toBe(false);
    });

    it('应该正确处理多条消息', () => {
      const messages: Message[] = [
        { role: 'user', content: '消息1' },
        { role: 'assistant', content: '回复1' },
        { role: 'user', content: '消息2' },
        { role: 'assistant', content: '回复2' },
      ];

      messages.forEach((msg) => {
        useMessageStore.getState().addMessage(msg);
      });

      expect(useMessageStore.getState().messages).toHaveLength(4);
      useMessageStore.getState().messages.forEach((msg, index) => {
        expect(msg.content).toEqual(messages[index].content);
        expect(msg.role).toEqual(messages[index].role);
        expect(msg.streamingState).toEqual(MessageStreamingState.IDLE);
      });
    });

    it('应该正确处理多个来源', () => {
      const sources: SourceDetail[] = [
        { doc_id: 1, file_name: 'test1.pdf', text_segment: '内容1', score: 0.9 },
        { doc_id: 2, file_name: 'test2.pdf', text_segment: '内容2', score: 0.8 },
        { doc_id: 3, file_name: 'test3.pdf', text_segment: '内容3', score: 0.7 },
      ];

      useMessageStore.getState().setSources(sources);

      expect(useMessageStore.getState().sources).toHaveLength(3);
      expect(useMessageStore.getState().sources).toEqual(sources);
    });
  });

  describe('createMessageStore 工厂函数', () => {
    it('应该创建具有自定义初始状态的 Store', () => {
      const customStore = createMessageStore<Message, SourceDetail>({
        messages: [{ role: 'user', content: '初始消息' }] as Message[],
        sources: [],
        isStreaming: false,
      });

      expect(customStore.getState().messages).toHaveLength(1);
      expect(customStore.getState().messages[0].content).toBe('初始消息');
    });

    it('应该创建独立的 Store 实例', () => {
      const store1 = createMessageStore();
      const store2 = createMessageStore();

      store1.getState().addMessage({ role: 'user', content: 'Store1 消息' });
      store2.getState().addMessage({ role: 'user', content: 'Store2 消息' });

      expect(store1.getState().messages).toHaveLength(1);
      expect(store2.getState().messages).toHaveLength(1);
      expect(store1.getState().messages[0].content).toBe('Store1 消息');
      expect(store2.getState().messages[0].content).toBe('Store2 消息');
    });
  });

  describe('MessageStateManager 静态方法', () => {
    it('应该添加对话对（用户消息+助手占位）', () => {
      MessageStateManager.addConversationPair(useMessageStore.getState(), '用户消息');

      const messages = useMessageStore.getState().messages;
      expect(messages).toHaveLength(2);
      expect(messages[0].role).toBe('user');
      expect(messages[0].content).toBe('用户消息');
      expect(messages[1].role).toBe('assistant');
      expect(messages[1].content).toBe('');
    });

    it('应该追加内容到最后一条消息', () => {
      useMessageStore.getState().addMessage({ role: 'assistant', content: '初始内容' });

      MessageStateManager.appendToLastMessage(useMessageStore.getState(), ' 追加的内容');

      expect(useMessageStore.getState().messages[0].content).toBe('初始内容 追加的内容');
    });

    it('应该在空消息列表时追加内容不执行任何操作', () => {
      MessageStateManager.appendToLastMessage(useMessageStore.getState(), '测试内容');

      expect(useMessageStore.getState().messages).toHaveLength(0);
    });

    it('应该获取最后一条消息', () => {
      useMessageStore.getState().addMessage({ role: 'user', content: '消息1' });
      useMessageStore.getState().addMessage({ role: 'assistant', content: '回复1' });

      const lastMessage = MessageStateManager.getLastMessage(useMessageStore.getState());

      expect(lastMessage).not.toBeNull();
      expect(lastMessage?.content).toBe('回复1');
    });

    it('应该在空消息列表时返回 null', () => {
      const lastMessage = MessageStateManager.getLastMessage(useMessageStore.getState());

      expect(lastMessage).toBeNull();
    });

    it('应该检查是否正在流式输出', () => {
      expect(MessageStateManager.isStreaming(useMessageStore.getState())).toBe(false);

      useMessageStore.getState().setStreaming(true);

      expect(MessageStateManager.isStreaming(useMessageStore.getState())).toBe(true);
    });

    it('应该完成流式输出', () => {
      useMessageStore.getState().addMessage({ role: 'assistant', content: '测试消息' });
      useMessageStore.getState().setStreaming(true);

      MessageStateManager.completeStreaming(useMessageStore.getState());

      expect(useMessageStore.getState().isStreaming).toBe(false);
      expect(useMessageStore.getState().messages[0].streamingState).toBe(MessageStreamingState.COMPLETED);
    });
  });
});
