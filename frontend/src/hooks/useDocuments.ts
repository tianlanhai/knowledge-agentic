/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：文档数据Hook
 * 内部逻辑：封装文档列表获取、删除等操作
 * 参数：
 *   skip - 分页跳过数量
 *   limit - 分页返回限制
 * 返回值：文档数据和操作方法
 */

import { useEffect, useState } from 'react';
import { useDocumentStore } from '../stores/documentStore';
import { documentServiceClass } from '../services/documentServiceClass';

/**
 * 文件级注释：文档数据Hook
 * 内部逻辑：封装文档列表获取、删除等操作
 * 参数：
 *   skip - 分页跳过数量
 *   limit - 分页返回限制
 * 返回值：文档数据和操作方法
 */

export const useDocuments = (skip: number = 0, limit: number = 10) => {
  const { documents, total, loading, setDocuments, setLoading, removeDocument, refreshTrigger } = useDocumentStore();
  const [error, setError] = useState<string | null>(null);

  /**
   * 函数级注释：获取文档列表
   * 内部逻辑：调用documentService获取文档列表，更新store状态
   */
  const fetchDocuments = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await documentServiceClass.getDocuments(skip, limit);
      setDocuments(response.items, response.total);
    } catch (err) {
      setError('获取文档列表失败');
      console.error('Fetch documents error:', err);
    } finally {
      setLoading(false);
    }
  };

  /**
   * 函数级注释：删除文档
   * 内部逻辑：调用documentService删除文档，然后更新store状态
   * 参数：docId - 文档ID
   */
  const handleDeleteDocument = async (docId: number) => {
    try {
      await documentServiceClass.deleteDocument(docId);
      removeDocument(docId);
    } catch (err) {
      setError('删除文档失败');
      console.error('Delete document error:', err);
    }
  };

  // 内部逻辑：监听分页参数变化，自动重新获取文档列表
  useEffect(() => {
    fetchDocuments();
  }, [skip, limit, refreshTrigger]);

  return {
    documents,
    total,
    loading,
    error,
    refetch: fetchDocuments,
    deleteDocument: handleDeleteDocument,
  };
};
