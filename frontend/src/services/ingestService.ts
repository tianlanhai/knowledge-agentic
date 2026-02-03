/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：知识摄入服务层
 * 内部逻辑：封装知识摄入相关的API调用，处理后端统一的响应格式
 */

import api from './api';
import type { IngestResponse, DBIngestRequest, URLIngestRequest, TaskResponse, TaskListResponse } from '../types/ingest';

export const ingestService = {
  /**
   * 函数级注释：上传文件接口（异步处理）
   * 内部逻辑：使用FormData上传文件，支持标签，立即返回任务ID
   * 参数：
   *   file - 要上传的文件对象
   *   tags - 可选的标签列表
   *   onUploadProgress - 可选的上传进度回调函数
   * 返回值：Promise<TaskResponse> - 任务响应数据
   */
  async uploadFile(
    file: File, 
    tags?: string[], 
    onUploadProgress?: (progressEvent: any) => void
  ): Promise<TaskResponse> {
    const formData = new FormData();
    formData.append('file', file);
    
    // 内部逻辑：如果有标签，添加到FormData
    if (tags && tags.length > 0) {
      tags.forEach((tag, index) => {
        formData.append(`tags`, tag);
      });
    }

    return api.post('/ingest/file', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress,
    });
  },

  /**
   * 函数级注释：获取任务状态
   * 参数：
   *   taskId - 任务ID
   * 返回值：Promise<TaskResponse> - 任务状态数据
   */
  async getTaskStatus(taskId: number): Promise<TaskResponse> {
    return api.get(`/ingest/tasks/${taskId}`);
  },

  /**
   * 函数级注释：获取所有任务列表
   * 参数：
   *   skip - 跳过数量（用于分页）
   *   limit - 返回数量
   * 返回值：Promise<TaskListResponse> - 任务列表数据
   */
  async getAllTasks(skip: number = 0, limit: number = 10): Promise<TaskListResponse> {
    return api.get('/ingest/tasks', { params: { skip, limit } });
  },

  /**
   * 函数级注释：抓取网页接口
   * 参数：
   *   url - 网页URL地址
   *   tags - 可选的标签列表
   * 返回值：Promise<IngestResponse> - 摄入响应数据
   */
  async ingestUrl(url: string, tags?: string[]): Promise<IngestResponse> {
    return api.post('/ingest/url', { url, tags });
  },

  /**
   * 函数级注释：同步数据库接口
   * 参数：config - 数据库同步配置对象
   * 返回值：Promise<IngestResponse> - 摄入响应数据
   */
  async syncDatabase(config: DBIngestRequest): Promise<IngestResponse> {
    return api.post('/ingest/db', config);
  },

  /**
   * 函数级注释：删除任务接口
   * 内部逻辑：删除指定任务记录，仅删除任务，不影响已生成的文档
   * 参数：
   *   taskId - 任务ID
   * 返回值：Promise<{ message: string }> - 删除结果消息
   */
  async deleteTask(taskId: number): Promise<{ message: string }> {
    return api.delete(`/ingest/tasks/${taskId}`);
  },
};
