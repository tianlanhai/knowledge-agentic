/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：useDocuments Hook单元测试
 * 内部逻辑：测试文档获取和删除功能
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useDocuments } from './useDocuments';
import { useDocumentStore } from '../stores/documentStore';
import { documentServiceClass } from '../services/documentServiceClass';

// Mock documentStore
vi.mock('../stores/documentStore');

// Mock documentServiceClass
vi.mock('../services/documentServiceClass', () => ({
  documentServiceClass: {
    getDocuments: vi.fn(),
    deleteDocument: vi.fn(),
  },
}));

describe('useDocuments Hook', () => {
  // Mock store state
  const mockSetDocuments = vi.fn();
  const mockSetLoading = vi.fn();
  const mockRemoveDocument = vi.fn();

  const mockStore = {
    documents: [
      { id: 1, name: 'test1.pdf', chunk_count: 10, created_at: '2026-01-01' },
      { id: 2, name: 'test2.pdf', chunk_count: 20, created_at: '2026-01-02' },
    ],
    total: 2,
    loading: false,
    setDocuments: mockSetDocuments,
    setLoading: mockSetLoading,
    removeDocument: mockRemoveDocument,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    // 设置mock store状态
    vi.mocked(useDocumentStore).mockReturnValue(mockStore);
  });

  /**
   * 测试fetchDocuments功能
   */
  it('应该获取文档列表', async () => {
    vi.mocked(documentServiceClass.getDocuments).mockResolvedValue({
      items: mockStore.documents,
      total: mockStore.total,
    });

    const { result } = renderHook(() => useDocuments(0, 10));
    const { refetch } = result.current;

    await act(async () => {
      await refetch();
    });

    expect(documentServiceClass.getDocuments).toHaveBeenCalledWith(0, 10);
    expect(mockSetDocuments).toHaveBeenCalledWith(
      mockStore.documents,
      mockStore.total,
    );
    expect(mockSetLoading).toHaveBeenCalledWith(false);
  });

  /**
   * 测试分页参数
   */
  it('应该使用正确的分页参数', async () => {
    vi.mocked(documentServiceClass.getDocuments).mockResolvedValue({
      items: [],
      total: 0,
    });

    const { result } = renderHook(() => useDocuments(5, 20));
    const { refetch } = result.current;

    await act(async () => {
      await refetch();
    });

    expect(documentServiceClass.getDocuments).toHaveBeenCalledWith(5, 20);
  });

  /**
   * 测试handleDeleteDocument功能
   */
  it('应该删除文档', async () => {
    vi.mocked(documentServiceClass.deleteDocument).mockResolvedValue({ message: '删除成功' });

    const { result } = renderHook(() => useDocuments());
    const { deleteDocument } = result.current;

    await act(async () => {
      await deleteDocument(1);
    });

    expect(documentServiceClass.deleteDocument).toHaveBeenCalledWith(1);
    expect(mockRemoveDocument).toHaveBeenCalledWith(1);
  });

  /**
   * 测试加载状态管理
   */
  it('应该正确管理加载状态', async () => {
    vi.mocked(documentServiceClass.getDocuments).mockImplementation(
      async () => {
        mockStore.loading = true;
        return new Promise(resolve =>
          setTimeout(() => resolve({ items: [], total: 0 }), 100)
        );
      }
    );

    const { result } = renderHook(() => useDocuments());
    const { refetch, loading } = result.current;

    expect(loading).toBe(false);

    await act(async () => {
      await refetch();
    });

    expect(mockSetLoading).toHaveBeenCalledWith(true);
    expect(mockSetLoading).toHaveBeenCalledWith(false);
  });

  /**
   * 测试错误处理
   */
  it('应该处理获取文档错误', async () => {
    vi.mocked(documentServiceClass.getDocuments).mockRejectedValue(new Error('网络错误'));

    const { result } = renderHook(() => useDocuments());
    const { refetch } = result.current;

    await act(async () => {
      await refetch();
    });

    expect(documentServiceClass.getDocuments).toHaveBeenCalled();
    expect(mockSetLoading).toHaveBeenCalledWith(false);
  });

  /**
   * 测试删除错误处理
   */
  it('应该处理删除错误', async () => {
    vi.mocked(documentServiceClass.deleteDocument).mockRejectedValue(new Error('删除失败'));

    const { result } = renderHook(() => useDocuments());
    const { deleteDocument } = result.current;

    await act(async () => {
      await deleteDocument(999);
    });

    expect(documentServiceClass.deleteDocument).toHaveBeenCalledWith(999);
  });
});
