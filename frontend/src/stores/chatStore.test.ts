/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：chatStore 测试文件
 * 内部逻辑：测试聊天状态管理 Store 的功能，包括状态机管理、智能体模式和委托的消息管理
 * 测试策略：
 *   - 单元测试：测试每个状态和操作
 *   - 边界测试：测试空消息列表等边界情况
 *   - 集成测试：测试与 messageStore 的委托关系
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { useChatStore } from './chatStore';
import { useMessageStore } from './messageStore';
import type { Message, SourceDetail } from '../types/chat';
import { MessageStreamingState } from '../types/chat';

describe('chatStore', () => {
  /**
   * 函数级注释：每个测试前重置状态
   * 内部逻辑：重置 chatStore 和 messageStore 的状态，确保测试独立性
   */
  beforeEach(() => {
    // 重置 chatStore 的状态机特有状态
    useChatStore.setState({
      useAgent: false,
    });

    // 重置 messageStore 的消息状态
    useMessageStore.getState().clearMessages();

    // 重置状态机
    useChatStore.getState().resetStateMachine();
  });

  /**
   * 函数级注释：每个测试后清理状态
   * 内部逻辑：确保状态完全清理
   */
  afterEach(() => {
    useMessageStore.getState().clearMessages();
    useChatStore.getState().resetStateMachine();
  });

  it('应该正确初始化状态', () => {
    const state = useChatStore.getState();

    expect(state.chatState).toBe('idle');
    expect(state.useAgent).toBe(false);
    expect(useMessageStore.getState().messages).toEqual([]);
    expect(useMessageStore.getState().sources).toEqual([]);
    expect(useMessageStore.getState().isStreaming).toBe(false);
  });

  it('应该添加消息', () => {
    const message: Message = { role: 'user', content: '测试消息' };

    useChatStore.getState().addMessage(message);

    expect(useMessageStore.getState().messages).toHaveLength(1);
    expect(useMessageStore.getState().messages[0]).toEqual({
      ...message,
      streamingState: MessageStreamingState.IDLE,
    });
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

    useChatStore.getState().setSources(sources);

    expect(useMessageStore.getState().sources).toEqual(sources);
  });

  it('应该设置流式状态', () => {
    useChatStore.getState().setStreaming(true);

    expect(useMessageStore.getState().isStreaming).toBe(true);

    useChatStore.getState().setStreaming(false);

    expect(useMessageStore.getState().isStreaming).toBe(false);
  });

  it('应该切换智能体模式', () => {
    expect(useChatStore.getState().useAgent).toBe(false);

    useChatStore.getState().toggleAgent();

    expect(useChatStore.getState().useAgent).toBe(true);

    useChatStore.getState().toggleAgent();

    expect(useChatStore.getState().useAgent).toBe(false);
  });

  it('应该清空消息和来源', () => {
    // 先添加一些数据
    useChatStore.getState().addMessage({ role: 'user', content: '消息1' });
    useChatStore.getState().addMessage({ role: 'assistant', content: '回复1' });
    useChatStore.getState().setSources([
      { doc_id: 1, file_name: 'test.pdf', text_segment: '内容', score: 0.9 },
    ]);
    useChatStore.getState().setStreaming(true);
    useChatStore.getState().toggleAgent();

    // 验证数据已添加
    expect(useMessageStore.getState().messages).toHaveLength(2);
    expect(useMessageStore.getState().sources).toHaveLength(1);
    expect(useMessageStore.getState().isStreaming).toBe(true);
    expect(useChatStore.getState().useAgent).toBe(true);

    // 清空消息
    useChatStore.getState().clearMessages();

    // 验证已清空
    expect(useMessageStore.getState().messages).toHaveLength(0);
    expect(useMessageStore.getState().sources).toHaveLength(0);
    expect(useMessageStore.getState().isStreaming).toBe(false);
    // 状态机应该被重置
    expect(useChatStore.getState().chatState).toBe('idle');
  });

  it('应该正确处理多条消息', () => {
    const messages: Message[] = [
      { role: 'user', content: '消息1' },
      { role: 'assistant', content: '回复1' },
      { role: 'user', content: '消息2' },
      { role: 'assistant', content: '回复2' },
    ];

    messages.forEach((msg) => {
      useChatStore.getState().addMessage(msg);
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

    useChatStore.getState().setSources(sources);

    expect(useMessageStore.getState().sources).toHaveLength(3);
    expect(useMessageStore.getState().sources).toEqual(sources);
  });

  it('应该正确处理用户和助手消息', () => {
    const userMessage: Message = { role: 'user', content: '用户消息' };
    const assistantMessage: Message = { role: 'assistant', content: '助手消息' };

    useChatStore.getState().addMessage(userMessage);
    useChatStore.getState().addMessage(assistantMessage);

    expect(useMessageStore.getState().messages).toHaveLength(2);
    expect(useMessageStore.getState().messages[0].role).toBe('user');
    expect(useMessageStore.getState().messages[1].role).toBe('assistant');
  });

  describe('updateLastMessage 方法', () => {
    it('应该更新最后一条消息的内容', () => {
      useChatStore.getState().addMessage({ role: 'assistant', content: '原始内容' });

      useChatStore.getState().updateLastMessage('更新后的内容');

      expect(useMessageStore.getState().messages[0].content).toBe('更新后的内容');
    });

    it('应该将消息状态设置为 STREAMING', () => {
      useChatStore.getState().addMessage({ role: 'assistant', content: '' });

      useChatStore.getState().updateLastMessage('新内容');

      const lastMessage = useMessageStore.getState().messages[0];
      expect(lastMessage.streamingState).toBe(MessageStreamingState.STREAMING);
      expect(lastMessage.content).toBe('新内容');
    });

    it('应该在空消息列表时不执行任何操作', () => {
      const messagesLength = useMessageStore.getState().messages.length;

      useChatStore.getState().updateLastMessage('新内容');

      expect(useMessageStore.getState().messages.length).toBe(messagesLength);
    });
  });

  describe('markStreamingComplete 方法', () => {
    it('应该将最后一条消息的状态设置为 COMPLETED', () => {
      useChatStore.getState().addMessage({
        role: 'assistant',
        content: '测试消息',
        streamingState: MessageStreamingState.STREAMING,
      });

      useChatStore.getState().markStreamingComplete();

      const lastMessage = useMessageStore.getState().messages[0];
      expect(lastMessage.streamingState).toBe(MessageStreamingState.COMPLETED);
    });

    it('应该在空消息列表时不执行任何操作', () => {
      useChatStore.getState().markStreamingComplete();

      expect(useMessageStore.getState().messages).toHaveLength(0);
    });

    it('应该只更新最后一条消息，不影响其他消息', () => {
      useChatStore.getState().addMessage({ role: 'user', content: '用户消息' });
      useChatStore.getState().addMessage({ role: 'assistant', content: '助手消息1' });
      useChatStore.getState().addMessage({ role: 'assistant', content: '助手消息2' });

      useChatStore.getState().markStreamingComplete();

      const messages = useMessageStore.getState().messages;
      expect(messages[0].streamingState).toBe(MessageStreamingState.IDLE);
      expect(messages[1].streamingState).toBe(MessageStreamingState.IDLE);
      expect(messages[2].streamingState).toBe(MessageStreamingState.COMPLETED);
    });

    it('应该正确处理从 STREAMING 到 COMPLETED 的状态转换', () => {
      useChatStore.getState().addMessage({ role: 'user', content: '用户消息' });
      useChatStore.getState().addMessage({ role: 'assistant', content: '' });

      // 模拟流式更新
      useChatStore.getState().updateLastMessage('部分内容');
      expect(useMessageStore.getState().messages[1].streamingState).toBe(MessageStreamingState.STREAMING);

      // 模拟流式完成
      useChatStore.getState().markStreamingComplete();
      expect(useMessageStore.getState().messages[1].streamingState).toBe(MessageStreamingState.COMPLETED);
    });
  });

  describe('状态机相关方法', () => {
    it('应该正确检查状态转换', () => {
      const state = useChatStore.getState();

      // 初始状态是 idle，应该可以 send
      expect(state.canTransition('send')).toBe(true);
      // 不能直接从 idle 到 error
      expect(state.canTransition('error')).toBe(false);
    });

    it('应该正确获取可用事件', () => {
      const state = useChatStore.getState();
      const events = state.getAvailableEvents();

      // 初始状态应该包含 send 事件（小写）
      expect(events).toContain('send');
    });

    it('应该正确执行状态转换', async () => {
      const state = useChatStore.getState();

      // 使用状态机自身的 send 方法
      const success = await state.stateMachine.send();

      expect(success).toBe(true);
      // 验证状态已转换
      expect(state.stateMachine.currentState).toBe('sending');
    });

    it('应该重置状态机', () => {
      const state = useChatStore.getState();

      // 重置状态机
      state.resetStateMachine();

      expect(state.chatState).toBe('idle');
    });
  });
});
