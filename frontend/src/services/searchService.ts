/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：搜索服务层
 * 内部逻辑：封装语义搜索相关的API调用
 */

import api from './api';
import type { SearchResult } from '../types/search';

export const searchService = {
  async semanticSearch(query: string, topK: number = 5): Promise<SearchResult[]> {
    return api.post('/search', { query, top_k: topK });
  },
};
