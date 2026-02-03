/**
 * 上海宇羲伏天智能科技有限公司出品
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { searchService } from './searchService';
import api from './api';
import type { SearchResult } from '../types/search';

vi.mock('./api');

describe('searchService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该执行语义搜索', async () => {
    const mockResults: SearchResult[] = [
      {
        doc_id: 1,
        content: '测试内容1',
        score: 0.9,
      },
      {
        doc_id: 2,
        content: '测试内容2',
        score: 0.8,
      },
    ];
    vi.mocked(api).post.mockResolvedValue(mockResults);

    const response = await searchService.semanticSearch('测试搜索', 5);

    expect(api.post).toHaveBeenCalledWith('/search', { query: '测试搜索', top_k: 5 });
    expect(response).toEqual(mockResults);
  });

  it('应该正确处理默认参数', async () => {
    const mockResults: SearchResult[] = [];
    vi.mocked(api).post.mockResolvedValue(mockResults);

    const response = await searchService.semanticSearch('测试搜索');

    expect(api.post).toHaveBeenCalledWith('/search', { query: '测试搜索', top_k: 5 });
    expect(response).toEqual(mockResults);
  });

  it('应该处理搜索错误', async () => {
    vi.mocked(api).post.mockRejectedValue(new Error('搜索失败'));

    await expect(searchService.semanticSearch('测试搜索')).rejects.toThrow('搜索失败');
  });

  it('应该正确处理空结果', async () => {
    const mockResults: SearchResult[] = [];
    vi.mocked(api).post.mockResolvedValue(mockResults);

    const response = await searchService.semanticSearch('空搜索');

    expect(response).toEqual([]);
    expect(response).toHaveLength(0);
  });

  it('应该正确处理大量结果', async () => {
    const mockResults: SearchResult[] = Array.from({ length: 20 }, (_, i) => ({
      doc_id: i + 1,
      content: `测试内容${i + 1}`,
      score: 0.9 - i * 0.01,
    }));
    vi.mocked(api).post.mockResolvedValue(mockResults);

    const response = await searchService.semanticSearch('大量搜索', 20);

    expect(response).toHaveLength(20);
    expect(response).toEqual(mockResults);
  });

  it('应该正确处理不同 top_k 值', async () => {
    const mockResults: SearchResult[] = [];
    vi.mocked(api).post.mockResolvedValue(mockResults);

    const response1 = await searchService.semanticSearch('测试', 1);
    const response2 = await searchService.semanticSearch('测试', 10);
    const response3 = await searchService.semanticSearch('测试', 15);

    expect(api.post).toHaveBeenNthCalledWith(1, '/search', { query: '测试', top_k: 1 });
    expect(api.post).toHaveBeenNthCalledWith(2, '/search', { query: '测试', top_k: 10 });
    expect(api.post).toHaveBeenNthCalledWith(3, '/search', { query: '测试', top_k: 15 });
  });

  it('应该正确处理特殊字符搜索', async () => {
    const mockResults: SearchResult[] = [];
    vi.mocked(api).post.mockResolvedValue(mockResults);

    const specialQuery = '测试!@#$%^&*()_+-={}[]|\\:;"\'<>?,./';
    const response = await searchService.semanticSearch(specialQuery);

    expect(api.post).toHaveBeenCalledWith('/search', { query: specialQuery, top_k: 5 });
    expect(response).toEqual(mockResults);
  });

  it('应该正确处理长查询', async () => {
    const mockResults: SearchResult[] = [];
    vi.mocked(api).post.mockResolvedValue(mockResults);

    const longQuery = '测试'.repeat(100);
    const response = await searchService.semanticSearch(longQuery);

    expect(api.post).toHaveBeenCalledWith('/search', { query: longQuery, top_k: 5 });
    expect(response).toEqual(mockResults);
  });
});
