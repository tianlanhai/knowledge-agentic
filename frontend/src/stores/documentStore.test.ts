/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：documentStore单元测试
 * 内部逻辑：测试文档状态管理
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { useDocumentStore } from './documentStore';
import type { Document } from '../types/document';

/**
 * 内部函数：创建测试文档
 * 参数：id - 文档ID
 * 返回值：Document对象
 */
const createMockDocument = (id: number): Document => ({
  id,
  name: `test-${id}.pdf`,
  chunk_count: id * 10,
  created_at: `2026-01-${id.toString().padStart(2, '0')}`,
});

describe('documentStore', () => {
  beforeEach(() => {
    // 每个测试前清空store
    useDocumentStore.setState({
      documents: [],
      total: 0,
      loading: false,
    });
  });

  /**
   * 测试初始状态
   */
  it('应该有初始状态', () => {
    const state = useDocumentStore.getState();

    expect(state.documents).toEqual([]);
    expect(state.total).toBe(0);
    expect(state.loading).toBe(false);
  });

  /**
   * 测试setDocuments功能
   */
  it('应该设置文档列表', () => {
    const mockDocs = [
      createMockDocument(1),
      createMockDocument(2),
    ];

    useDocumentStore.getState().setDocuments(mockDocs, 2);

    const state = useDocumentStore.getState();

    expect(state.documents).toEqual(mockDocs);
    expect(state.total).toBe(2);
  });

  /**
   * 测试setLoading功能
   */
  it('应该设置加载状态', () => {
    useDocumentStore.getState().setLoading(true);

    const state = useDocumentStore.getState();

    expect(state.loading).toBe(true);

    useDocumentStore.getState().setLoading(false);

    const newState = useDocumentStore.getState();

    expect(newState.loading).toBe(false);
  });

  /**
   * 测试removeDocument功能
   */
  it('应该删除文档', () => {
    const mockDocs = [
      createMockDocument(1),
      createMockDocument(2),
      createMockDocument(3),
    ];

    useDocumentStore.getState().setDocuments(mockDocs, 3);
    useDocumentStore.getState().removeDocument(2);

    const state = useDocumentStore.getState();

    expect(state.documents).toHaveLength(2);
    expect(state.documents[0].id).toBe(1);
    expect(state.documents[1].id).toBe(3);
    expect(state.total).toBe(2);
  });

  /**
   * 测试删除不存在的文档
   */
  it('应该正确处理删除不存在的文档', () => {
    const mockDocs = [
      createMockDocument(1),
      createMockDocument(2),
    ];

    useDocumentStore.getState().setDocuments(mockDocs, 2);
    useDocumentStore.getState().removeDocument(999);

    const state = useDocumentStore.getState();

    expect(state.documents).toHaveLength(2);
    expect(state.total).toBe(2);
  });

  /**
   * 测试删除所有文档
   */
  it('应该删除所有文档', () => {
    const mockDocs = [
      createMockDocument(1),
      createMockDocument(2),
    ];

    useDocumentStore.getState().setDocuments(mockDocs, 2);
    useDocumentStore.getState().removeDocument(1);
    useDocumentStore.getState().removeDocument(2);

    const state = useDocumentStore.getState();

    expect(state.documents).toHaveLength(0);
    expect(state.total).toBe(0);
  });

  /**
   * 测试triggerRefresh功能
   * 内部逻辑：验证refreshTrigger计数器递增
   */
  it('应该触发刷新', () => {
    const state = useDocumentStore.getState();
    const initialTrigger = state.refreshTrigger;

    useDocumentStore.getState().triggerRefresh();

    const newState = useDocumentStore.getState();

    expect(newState.refreshTrigger).toBe(initialTrigger + 1);
  });

  /**
   * 测试多次调用triggerRefresh
   * 内部逻辑：验证每次调用都递增计数器
   */
  it('应该在多次调用triggerRefresh时递增计数器', () => {
    const state = useDocumentStore.getState();
    const initialTrigger = state.refreshTrigger;

    useDocumentStore.getState().triggerRefresh();
    useDocumentStore.getState().triggerRefresh();
    useDocumentStore.getState().triggerRefresh();

    const newState = useDocumentStore.getState();

    expect(newState.refreshTrigger).toBe(initialTrigger + 3);
  });

  /**
   * 测试删除最后一个文档
   * 内部逻辑：验证删除最后一个文档时total减少
   */
  it('应该在删除最后一个文档时减少total', () => {
    const mockDocs = [
      createMockDocument(1),
    ];

    useDocumentStore.getState().setDocuments(mockDocs, 1);

    const beforeState = useDocumentStore.getState();
    expect(beforeState.total).toBe(1);

    useDocumentStore.getState().removeDocument(1);

    const afterState = useDocumentStore.getState();
    expect(afterState.total).toBe(0);
  });

  /**
   * 测试refreshTrigger初始值为0
   * 内部逻辑：验证refreshTrigger初始状态
   */
  it('应该初始化refreshTrigger为0', () => {
    useDocumentStore.setState({
      documents: [],
      total: 0,
      loading: false,
      refreshTrigger: 0,
    });

    const state = useDocumentStore.getState();

    expect(state.refreshTrigger).toBe(0);
  });
});
