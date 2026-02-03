/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：文档服务类
 * 内部逻辑：封装文档管理相关的API调用，使用模板方法模式减少重复代码
 * 设计模式：模板方法模式、类继承模式、外观模式
 * 设计原则：DRY原则、开闭原则
 */

import { BaseService, type AsyncResult } from './baseService';
import type { DocumentListResponse, Document } from '../types/document';

/**
 * 文档服务类
 * 设计模式：模板方法模式 - 继承BaseService使用通用模板
 * 职责：
 *   1. 管理文档的CRUD操作
 *   2. 提供分页查询
 *   3. 提供安全的错误处理
 */
export class DocumentService extends BaseService {
  /** 属性：服务基础路径 */
  protected basePath = '/documents';

  /**
   * 函数级注释：获取文档列表（带分页）
   * 内部逻辑：使用基类的get方法处理分页请求
   * 参数：
   *   skip - 分页跳过数量，默认0
   *   limit - 分页返回限制，默认10
   * 返回值：Promise<DocumentListResponse> - 文档列表数据
   */
  async getDocuments(skip: number = 0, limit: number = 10): Promise<DocumentListResponse> {
    return this.get<DocumentListResponse>('', { skip, limit });
  }

  /**
   * 函数级注释：根据ID获取单个文档
   * 内部逻辑：使用基类的getById方法
   * 参数：docId - 文档ID
   * 返回值：Promise<Document> - 文档详情
   */
  async getDocument(docId: number): Promise<Document> {
    return this.getById<Document>(docId);
  }

  /**
   * 函数级注释：删除文档
   * 内部逻辑：使用基类的delete方法
   * 参数：docId - 文档ID
   * 返回值：Promise<{ message: string }> - 删除结果消息
   */
  async deleteDocument(docId: number): Promise<{ message: string }> {
    return this.delete<{ message: string }>(`/${docId}`);
  }

  /**
   * 函数级注释：批量删除文档
   * 内部逻辑：使用基类的batchAsync方法并行处理
   * 参数：docIds - 文档ID列表
   * 返回值：Promise<{成功数、失败数、详细结果}> - 批量删除结果
   */
  async batchDeleteDocuments(docIds: number[]): Promise<{
    successCount: number;
    failureCount: number;
    results: Array<{ docId: number; success: boolean; error?: string }>;
  }> {
    const { successes, failures } = await this.batchAsync(
      docIds,
      async (docId) => {
        await this.deleteDocument(docId);
        return { docId, success: true };
      }
    );

    return {
      successCount: successes.length,
      failureCount: failures.length,
      results: [
        ...successes.map((s) => ({ docId: s.item as number, success: true })),
        ...failures.map((f) => ({ docId: f.item as number, success: false, error: f.error.error })),
      ],
    };
  }

  /**
   * 函数级注释：安全地获取文档列表（带错误处理）
   * 内部逻辑：使用基类的safeAsync方法包装错误
   * 参数：skip - 分页跳过数量，limit - 分页返回限制
   * 返回值：Promise<AsyncResult<DocumentListResponse>> - Result模式包装的结果
   */
  async safeGetDocuments(
    skip: number = 0,
    limit: number = 10
  ): Promise<AsyncResult<DocumentListResponse>> {
    return this.safeAsync(() => this.getDocuments(skip, limit), '获取文档列表失败');
  }

  /**
   * 函数级注释：安全地删除文档（带错误处理）
   * 参数：docId - 文档ID
   * 返回值：Promise<AsyncResult<{ message: string }>> - Result模式包装的结果
   */
  async safeDeleteDocument(docId: number): Promise<AsyncResult<{ message: string }>> {
    return this.safeAsync(() => this.deleteDocument(docId), '删除文档失败');
  }

  /**
   * 函数级注释：带重试的文档获取
   * 内部逻辑：使用基类的retryAsync方法处理网络抖动
   * 参数：docId - 文档ID，maxRetries - 最大重试次数
   * 返回值：Promise<AsyncResult<Document>> - Result模式包装的结果
   */
  async retryGetDocument(
    docId: number,
    maxRetries: number = 2
  ): Promise<AsyncResult<Document>> {
    return this.retryAsync(() => this.getDocument(docId), maxRetries, 1000);
  }
}

// 导出单例实例
export const documentServiceClass = new DocumentService();
