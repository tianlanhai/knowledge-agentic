/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：文档状态管理 Store
 * 内部逻辑：使用 Zustand 管理文档列表和加载状态
 */

import { create } from 'zustand';
import type { Document } from '../types/document';

export interface DocumentState {
  documents: Document[];
  total: number;
  loading: boolean;
  refreshTrigger: number;
  setDocuments: (documents: Document[], total: number) => void;
  setLoading: (loading: boolean) => void;
  removeDocument: (docId: number) => void;
  triggerRefresh: () => void;
}

export const useDocumentStore = create<DocumentState>((set) => ({
  documents: [],
  total: 0,
  loading: false,
  refreshTrigger: 0,
  setDocuments: (documents, total) => set({ documents, total }),
  setLoading: (loading) => set({ loading }),
  removeDocument: (docId) =>
    set((state) => {
      const filteredDocuments = state.documents.filter((doc) => doc.id !== docId);
      const newTotal = state.total - (filteredDocuments.length < state.documents.length ? 1 : 0);
      return { documents: filteredDocuments, total: newTotal };
    }),
  triggerRefresh: () => set((state) => ({ refreshTrigger: state.refreshTrigger + 1 })),
}));