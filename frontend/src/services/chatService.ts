/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：对话服务层
 * 内部逻辑：封装对话相关的API调用，处理后端统一的响应格式
 * 设计模式：外观模式 - 简化SSE流式处理调用
 */

import api from './api';
import { SSEHandler, type SSECallbacks } from '../utils/sseHandler';
import type { ChatRequest, ChatResponse, SourceDetail, SummaryRequest, SummaryResponse, ComparisonRequest } from '../types/chat';

export const chatService = {
  /**
   * 函数级注释：智能对话接口
   * 参数：request - 对话请求对象
   * 返回值：Promise<ChatResponse> - 对话响应数据
   */
  async chatCompletion(request: ChatRequest): Promise<ChatResponse> {
    return api.post('/chat/completions', request);
  },

  /**
   * 函数级注释：流式对话接口
   * 内部逻辑：使用统一的SSEHandler处理流式响应
   * 设计模式：模板方法模式 - 复用SSEHandler的通用SSE处理逻辑
   *
   * 参数：
   *   request - 对话请求对象
   *   onChunk - 流式数据回调函数，接收content片段
   *   onSources - 来源数据回调函数，接收sources数组
   *   onDone - 完成回调函数
   *
   * 返回值：Promise<void>
   */
  async streamChatCompletion(
    request: ChatRequest,
    onChunk: (chunk: string) => void,
    onSources?: (sources: SourceDetail[]) => void,
    onDone?: () => void
  ): Promise<void> {
    // 内部逻辑：使用SSEHandler.fetchWithStream一站式处理流式请求
    // 内部逻辑：复用SSEHandler中约70行的SSE解析逻辑，消除代码重复
    await SSEHandler.fetchWithStream(
      '/api/v1/chat/completions',
      request,
      { onChunk, onSources, onDone }
    );
  },

  /**
   * 函数级注释：获取来源详情
   * 参数：docId - 可选的文档ID
   * 返回值：Promise<SourceDetail[]> - 来源详情列表
   */
  async getSources(docId?: number): Promise<SourceDetail[]> {
    return api.get('/sources', { params: { doc_id: docId } });
  },

  /**
   * 函数级注释：文档总结接口
   * 参数：docId - 文档ID
   * 返回值：Promise<SummaryResponse> - 总结结果
   */
  async summarizeDocument(docId: number): Promise<SummaryResponse> {
    return api.post('/chat/summary', { doc_id: docId });
  },

  /**
   * 函数级注释：文档对比接口
   * 参数：docIds - 文档ID列表
   * 返回值：Promise<SummaryResponse> - 对比结果
   */
  async compareDocuments(docIds: number[]): Promise<SummaryResponse> {
    return api.post('/chat/compare', { doc_ids: docIds });
  },
};
