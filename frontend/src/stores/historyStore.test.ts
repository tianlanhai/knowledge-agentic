/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：historyStore单元测试
 * 内部逻辑：测试对话历史状态管理
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { useHistoryStore } from './historyStore';
import type { Message } from '../types/chat';

/**
 * 内部函数：创建测试消息
 * 参数：role - 消息角色，content - 消息内容
 * 返回值：Message对象
 */
const createMockMessage = (role: 'user' | 'assistant', content: string): Message => ({
  role,
  content,
});

describe('historyStore', () => {
  beforeEach(() => {
    // 清空store
    useHistoryStore.getState().clearHistories();
  });

  afterEach(() => {
    // 每个测试后清空store
    useHistoryStore.getState().clearHistories();
  });

  /**
   * 测试初始状态
   */
  it('应该有初始状态', () => {
    const state = useHistoryStore.getState();

    expect(state.histories).toEqual([]);
    expect(state.currentHistoryId).toBeNull();
    expect(state.loading).toBe(false);
  });

  /**
   * 测试addHistory功能
   */
  it('应该添加新会话', () => {
    const mockMessages = [
      createMockMessage('user', '测试问题'),
      createMockMessage('assistant', '测试回答'),
    ];

    useHistoryStore.getState().addHistory(mockMessages);

    const state = useHistoryStore.getState();

    expect(state.histories).toHaveLength(1);
    expect(state.currentHistoryId).toBeTruthy();
    expect(state.histories[0].messages).toEqual(mockMessages);
    expect(state.histories[0].title).toBe('测试问题');
  });

  /**
   * 测试生成标题 - 长消息
   */
  it('应该为长消息生成带省略号的标题', () => {
    const mockMessages = [
      createMockMessage('user', '这是一条很长的测试消息内容，应该被截断并添加省略号'),
    ];

    useHistoryStore.getState().addHistory(mockMessages);

    const state = useHistoryStore.getState();

    // 期望的标题应该截断到20个字符并添加'...'
    // 前20个字符：这是一条很长的测试消息内容，应该被截断并
    expect(state.histories[0].title).toBe('这是一条很长的测试消息内容，应该被截断并...');
  });

  /**
   * 测试生成标题 - 默认标题
   */
  it('应该为没有用户消息的会话生成默认标题', () => {
    const mockMessages = [
      createMockMessage('assistant', '只有助手消息'),
    ];

    useHistoryStore.getState().addHistory(mockMessages);

    const state = useHistoryStore.getState();

    expect(state.histories[0].title).toContain('对话');
  });

  /**
   * 测试updateHistory功能
   */
  it('应该更新当前会话', () => {
    const mockMessages = [
      createMockMessage('user', '初始消息'),
    ];

    useHistoryStore.getState().addHistory(mockMessages);

    const historyId = useHistoryStore.getState().currentHistoryId!;

    const newMessage = createMockMessage('assistant', '新消息');
    useHistoryStore.getState().updateHistory(newMessage);

    const state = useHistoryStore.getState();

    expect(state.histories[0].messages).toHaveLength(2);
    expect(state.histories[0].updatedAt).toBeInstanceOf(Date);
  });

  /**
   * 测试updateHistory没有当前会话
   */
  it('应该在没有当前会话时不更新', () => {
    const mockMessages = [
      createMockMessage('user', '初始消息'),
    ];

    useHistoryStore.getState().addHistory(mockMessages);

    // 清空currentHistoryId
    useHistoryStore.setState({ currentHistoryId: null });
    const beforeUpdate = useHistoryStore.getState();
    const originalLength = beforeUpdate.histories.length;

    useHistoryStore.getState().updateHistory(createMockMessage('assistant', '新消息'));
    const afterUpdate = useHistoryStore.getState();

    // 由于没有currentHistoryId，不应该更新
    expect(afterUpdate.histories).toHaveLength(originalLength);
  });

  /**
   * 测试updateHistory找不到会话
   * 内部逻辑：验证当currentHistoryId不在histories中时不更新
   */
  it('应该在找不到会话时不更新', () => {
    const mockMessages = [
      createMockMessage('user', '初始消息'),
    ];

    useHistoryStore.getState().addHistory(mockMessages);

    // 设置一个不存在的currentHistoryId
    useHistoryStore.setState({ currentHistoryId: 'non_existent_id' });
    const beforeUpdate = useHistoryStore.getState();
    const originalLength = beforeUpdate.histories.length;
    const originalUpdatedAt = beforeUpdate.histories[0].updatedAt;

    // 等待一下确保时间戳不同
    return new Promise(resolve => {
      setTimeout(() => {
        useHistoryStore.getState().updateHistory(createMockMessage('assistant', '新消息'));
        const afterUpdate = useHistoryStore.getState();

        // 由于找不到会话，不应该更新
        expect(afterUpdate.histories).toHaveLength(originalLength);
        expect(afterUpdate.histories[0].updatedAt).toEqual(originalUpdatedAt);
        resolve(null);
      }, 10);
    });
  });

  /**
   * 测试deleteHistory功能
   */
  it('应该删除会话', () => {
    const mockMessages = [
      createMockMessage('user', '测试问题'),
    ];

    useHistoryStore.getState().addHistory(mockMessages);

    const historyId = useHistoryStore.getState().currentHistoryId!;
    useHistoryStore.getState().deleteHistory(historyId);

    const state = useHistoryStore.getState();

    expect(state.histories).toHaveLength(0);
    expect(state.currentHistoryId).toBeNull();
  });

  /**
   * 测试deleteHistory功能 - 删除当前会话
   */
  it('应该删除当前会话并清空currentHistoryId', () => {
    const mockMessages = [
      createMockMessage('user', '测试问题'),
    ];

    useHistoryStore.getState().addHistory(mockMessages);

    // 删除当前会话
    const historyId = useHistoryStore.getState().currentHistoryId!;
    useHistoryStore.getState().deleteHistory(historyId);

    const state = useHistoryStore.getState();

    expect(state.histories).toHaveLength(0);
    expect(state.currentHistoryId).toBeNull();
  });

  /**
   * 测试deleteHistory功能 - 删除非当前会话
   * 内部逻辑：验证删除非当前会话时保留currentHistoryId
   */
  it('应该在删除非当前会话时保留currentHistoryId', async () => {
    // 内部逻辑：首先清空所有历史
    useHistoryStore.getState().clearHistories();

    const mockMessages1 = [createMockMessage('user', '问题1')];
    const mockMessages2 = [createMockMessage('user', '问题2')];

    // 内部逻辑：添加第一个会话
    useHistoryStore.getState().addHistory(mockMessages1);
    const firstHistoryId = useHistoryStore.getState().currentHistoryId!;

    // 内部逻辑：等待至少1毫秒确保ID不同（因为addHistory使用Date.now()生成ID）
    await new Promise(resolve => setTimeout(resolve, 2));

    // 内部逻辑：添加第二个会话，自动成为当前会话
    useHistoryStore.getState().addHistory(mockMessages2);
    const secondHistoryId = useHistoryStore.getState().currentHistoryId!;

    // 内部逻辑：确认两个ID不同
    expect(firstHistoryId).not.toBe(secondHistoryId);

    // 内部逻辑：确认有两个会话
    expect(useHistoryStore.getState().histories).toHaveLength(2);

    // 内部逻辑：使用loadHistory切换回第一个会话（模拟用户点击第一个会话）
    // 此时第二个会话仍然存在，但不再是当前会话
    useHistoryStore.getState().loadHistory(firstHistoryId);

    // 内部逻辑：验证当前会话已切换到第一个会话
    const stateBeforeDelete = useHistoryStore.getState();
    expect(stateBeforeDelete.currentHistoryId).toBe(firstHistoryId);
    expect(stateBeforeDelete.histories).toHaveLength(2);

    // 内部逻辑：现在删除第二个会话（非当前会话）
    useHistoryStore.getState().deleteHistory(secondHistoryId);

    const afterDelete = useHistoryStore.getState();

    // 内部逻辑：验证只删除了非当前会话，currentHistoryId不变
    expect(afterDelete.histories).toHaveLength(1);
    expect(afterDelete.currentHistoryId).toBe(firstHistoryId);
    expect(afterDelete.histories[0].id).toBe(firstHistoryId);
  });

  /**
   * 测试clearHistories功能
   */
  it('应该清空所有会话', () => {
    const mockMessages = [
      createMockMessage('user', '测试问题'),
    ];

    useHistoryStore.getState().addHistory(mockMessages);
    useHistoryStore.getState().addHistory(mockMessages);

    expect(useHistoryStore.getState().histories).toHaveLength(2);

    useHistoryStore.getState().clearHistories();

    const state = useHistoryStore.getState();

    expect(state.histories).toEqual([]);
    expect(state.currentHistoryId).toBeNull();
  });

  /**
   * 测试loadHistory功能
   */
  it('应该加载会话', () => {
    const mockMessages = [
      createMockMessage('user', '测试问题'),
    ];

    useHistoryStore.getState().addHistory(mockMessages);
    const historyId = useHistoryStore.getState().currentHistoryId!;

    // 创建另一个会话
    useHistoryStore.getState().addHistory([
      createMockMessage('user', '另一个问题'),
    ]);

    useHistoryStore.getState().loadHistory(historyId);

    const state = useHistoryStore.getState();

    expect(state.currentHistoryId).toBe(historyId);
  });

  /**
   * 测试getCurrentHistory功能
   */
  it('应该获取当前会话', () => {
    const mockMessages = [
      createMockMessage('user', '测试问题'),
    ];

    useHistoryStore.getState().addHistory(mockMessages);
    const historyId = useHistoryStore.getState().currentHistoryId!;

    const currentHistory = useHistoryStore.getState().getCurrentHistory();

    expect(currentHistory).toBeDefined();
    expect(currentHistory?.id).toBe(historyId);
    expect(currentHistory?.messages).toEqual(mockMessages);
  });

  /**
   * 测试getCurrentHistory返回undefined
   */
  it('应该在没有当前会话时返回undefined', () => {
    const currentHistory = useHistoryStore.getState().getCurrentHistory();

    expect(currentHistory).toBeUndefined();
  });

  /**
   * 测试generateTitle功能
   */
  it('应该生成标题', () => {
    const mockMessage = createMockMessage('user', '这是一条很长的测试消息内容，应该被截断并添加省略号');

    const title = useHistoryStore.getState().generateTitle([mockMessage]);

    // generateTitle会截断到20个字符并添加省略号
    // 前20个字符：这是一条很长的测试消息内容，应该被截断并
    expect(title).toBe('这是一条很长的测试消息内容，应该被截断并...');
  });

  /**
   * 测试generateTitle为空消息
   */
  it('应该为空消息生成默认标题', () => {
    const title = useHistoryStore.getState().generateTitle([]);

    expect(title).toContain('对话');
  });
});
