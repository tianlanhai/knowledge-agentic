/**
 * 上海宇羲伏天智能科技有限公司出品
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ingestService } from './ingestService';
import api from './api';
import type { IngestResponse, DBIngestRequest, TaskResponse, TaskListResponse } from '../types/ingest';

vi.mock('./api');

describe('ingestService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该上传文件（异步）', async () => {
    const mockResponse: TaskResponse = {
      id: 1,
      file_name: 'test.pdf',
      status: 'pending',
      progress: 0,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    };
    vi.mocked(api).post.mockResolvedValue(mockResponse);

    const file = new File(['test content'], 'test.txt', { type: 'text/plain' });
    const tags = ['tag1', 'tag2'];

    const response = await ingestService.uploadFile(file, tags);

    expect(api.post).toHaveBeenCalledWith('/ingest/file', expect.any(FormData), {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    expect(response).toEqual(mockResponse);
  });

  it('应该获取任务状态', async () => {
    const mockResponse: TaskResponse = {
      id: 1,
      file_name: 'test.pdf',
      status: 'processing',
      progress: 50,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:05:00Z',
    };
    vi.mocked(api).get.mockResolvedValue(mockResponse);

    const response = await ingestService.getTaskStatus(1);

    expect(api.get).toHaveBeenCalledWith('/ingest/tasks/1');
    expect(response).toEqual(mockResponse);
  });

  it('应该获取所有任务', async () => {
    const mockResponse: TaskListResponse = {
      items: [
        {
          id: 1,
          file_name: 'test1.pdf',
          status: 'completed',
          progress: 100,
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:10:00Z',
        },
        {
          id: 2,
          file_name: 'test2.docx',
          status: 'processing',
          progress: 60,
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:05:00Z',
        },
      ],
      total: 2,
    };
    vi.mocked(api).get.mockResolvedValue(mockResponse);

    const response = await ingestService.getAllTasks(0, 10);

    expect(api.get).toHaveBeenCalledWith('/ingest/tasks', { params: { skip: 0, limit: 10 } });
    expect(response).toEqual(mockResponse);
  });

  it('应该分页获取任务', async () => {
    const mockResponse: TaskListResponse = {
      items: [
        {
          id: 3,
          file_name: 'test3.pdf',
          status: 'pending',
          progress: 0,
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
      ],
      total: 1,
    };
    vi.mocked(api).get.mockResolvedValue(mockResponse);

    const response = await ingestService.getAllTasks(10, 5);

    expect(api.get).toHaveBeenCalledWith('/ingest/tasks', { params: { skip: 10, limit: 5 } });
    expect(response).toEqual(mockResponse);
  });

  it('应该抓取网页', async () => {
    const mockResponse: IngestResponse = {
      document_id: 2,
      chunk_count: 5,
      status: 'completed',
    };
    vi.mocked(api).post.mockResolvedValue(mockResponse);

    const url = 'https://example.com';
    const tags = ['web'];

    const response = await ingestService.ingestUrl(url, tags);

    expect(api.post).toHaveBeenCalledWith('/ingest/url', { url, tags });
    expect(response).toEqual(mockResponse);
  });

  it('应该同步数据库', async () => {
    const mockResponse: IngestResponse = {
      document_id: 3,
      chunk_count: 20,
      status: 'completed',
    };
    vi.mocked(api).post.mockResolvedValue(mockResponse);

    const config: DBIngestRequest = {
      connection_uri: 'sqlite:///test.db',
      table_name: 'test_table',
      content_column: 'content',
    };

    const response = await ingestService.syncDatabase(config);

    expect(api.post).toHaveBeenCalledWith('/ingest/db', config);
    expect(response).toEqual(mockResponse);
  });

  it('应该正确处理空标签', async () => {
    const mockResponse: IngestResponse = {
      document_id: 1,
      chunk_count: 10,
      status: 'completed',
    };
    vi.mocked(api).post.mockResolvedValue(mockResponse);

    const file = new File(['test content'], 'test.txt', { type: 'text/plain' });

    const response = await ingestService.uploadFile(file, []);

    expect(api.post).toHaveBeenCalledWith('/ingest/file', expect.any(FormData), {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    expect(response).toEqual(mockResponse);
  });

  it('应该正确处理多个标签', async () => {
    const mockResponse: TaskResponse = {
      id: 1,
      file_name: 'test.pdf',
      status: 'completed',
      progress: 100,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:10:00Z',
    };
    vi.mocked(api).post.mockResolvedValue(mockResponse);

    const file = new File(['test content'], 'test.txt', { type: 'text/plain' });
    const tags = ['tag1', 'tag2', 'tag3'];

    const response = await ingestService.uploadFile(file, tags);

    expect(api.post).toHaveBeenCalledWith('/ingest/file', expect.any(FormData), {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    expect(response).toEqual(mockResponse);
  });

  it('应该处理上传错误', async () => {
    vi.mocked(api).post.mockRejectedValue(new Error('上传失败'));

    const file = new File(['test content'], 'test.txt', { type: 'text/plain' });

    await expect(ingestService.uploadFile(file, [])).rejects.toThrow('上传失败');
  });

  it('应该处理抓取错误', async () => {
    vi.mocked(api).post.mockRejectedValue(new Error('抓取失败'));

    await expect(ingestService.ingestUrl('https://example.com', [])).rejects.toThrow('抓取失败');
  });

  it('应该处理同步错误', async () => {
    vi.mocked(api).post.mockRejectedValue(new Error('同步失败'));

    const config: DBIngestRequest = {
      connection_uri: 'sqlite:///test.db',
      table_name: 'test_table',
      content_column: 'content',
    };

    await expect(ingestService.syncDatabase(config)).rejects.toThrow('同步失败');
  });

  /**
   * 测试删除任务
   * 内部逻辑：验证deleteTask接口调用
   */
  it('应该删除任务', async () => {
    const mockResponse = { message: '任务已删除' };
    vi.mocked(api).delete.mockResolvedValue(mockResponse);

    const response = await ingestService.deleteTask(1);

    expect(api.delete).toHaveBeenCalledWith('/ingest/tasks/1');
    expect(response).toEqual(mockResponse);
  });

  /**
   * 测试上传文件带进度回调
   * 内部逻辑：验证onUploadProgress回调被正确传递
   */
  it('应该支持上传进度回调', async () => {
    const mockResponse: TaskResponse = {
      id: 1,
      file_name: 'test.pdf',
      status: 'pending',
      progress: 0,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    };
    vi.mocked(api).post.mockResolvedValue(mockResponse);

    const file = new File(['test content'], 'test.txt', { type: 'text/plain' });
    const onProgress = vi.fn();

    const response = await ingestService.uploadFile(file, undefined, onProgress);

    expect(api.post).toHaveBeenCalledWith('/ingest/file', expect.any(FormData), {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress,
    });
    expect(response).toEqual(mockResponse);
  });
});
