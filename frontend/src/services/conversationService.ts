/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：对话持久化服务层
 * 内部逻辑：封装会话和消息的API调用，处理后端统一的响应格式
 * 设计模式：外观模式 - 简化SSE流式处理调用
 */

import api from './api';
import { SSEHandler, type SSECallbacks } from '../utils/sseHandler';
import type {
  Conversation,
  ConversationDetail,
  CreateConversationRequest,
  SendMessageRequest,
  MessageWithSources,
  MessageSource,
} from '../types/chat';

export const conversationService = {
  /**
   * 函数级注释：获取会话列表
   * 参数：skip - 分页跳过，limit - 分页限制
   * 返回值：Promise<会话列表响应>
   */
  async listConversations(skip: number = 0, limit: number = 20): Promise<{
    conversations: Conversation[];
    total: number;
    has_more: boolean;
  }> {
    return api.get('/conversations', { params: { skip, limit } });
  },

  /**
   * 函数级注释：创建新会话
   * 参数：request - 创建会话请求
   * 返回值：Promise<Conversation> - 新创建的会话
   */
  async createConversation(request: CreateConversationRequest): Promise<Conversation> {
    return api.post('/conversations', request);
  },

  /**
   * 函数级注释：获取会话详情（包含消息列表）
   * 参数：id - 会话ID
   * 返回值：Promise<ConversationDetail> - 会话详情
   */
  async getConversation(id: number): Promise<ConversationDetail> {
    return api.get(`/conversations/${id}`);
  },

  /**
   * 函数级注释：更新会话信息
   * 参数：id - 会话ID，title - 新标题
   * 返回值：Promise<Conversation> - 更新后的会话
   */
  async updateConversation(id: number, title: string): Promise<Conversation> {
    return api.put(`/conversations/${id}`, { title });
  },

  /**
   * 函数级注释：删除会话（物理删除）
   * 参数：id - 会话ID
   * 返回值：Promise<{ deleted: boolean }>
   */
  async deleteConversation(id: number): Promise<{ deleted: boolean }> {
    return api.delete(`/conversations/${id}`);
  },

  /**
   * 函数级注释：发送消息（非流式）
   * 参数：conversationId - 会话ID，request - 消息请求
   * 返回值：Promise<MessageWithSources> - 助手回复消息
   */
  async sendMessage(
    conversationId: number,
    request: SendMessageRequest
  ): Promise<MessageWithSources> {
    return api.post(`/conversations/${conversationId}/messages`, request);
  },

  /**
   * 函数级注释：发送消息（流式）
   * 内部逻辑：使用统一的SSEHandler处理流式响应
   * 设计模式：模板方法模式 - 复用SSEHandler的通用SSE处理逻辑
   *
   * 参数：
   *   conversationId - 会话ID
   *   request - 消息请求
   *   onChunk - 流式数据回调函数，接收content片段
   *   onSources - 来源数据回调函数，接收sources数组
   *   onDone - 完成回调函数
   *
   * 返回值：Promise<void>
   */
  async streamSendMessage(
    conversationId: number,
    request: SendMessageRequest,
    onChunk: (chunk: string) => void,
    onSources?: (sources: MessageSource[]) => void,
    onDone?: () => void
  ): Promise<void> {
    // 内部逻辑：使用SSEHandler.fetchWithStream一站式处理流式请求
    // 内部逻辑：复用SSEHandler中约70行的SSE解析逻辑，消除代码重复
    await SSEHandler.fetchWithStream(
      `/api/v1/conversations/${conversationId}/stream`,
      request,
      { onChunk, onSources, onDone }
    );
  },

  /**
   * 函数级注释：获取会话消息列表
   * 参数：conversationId - 会话ID，skip - 分页跳过，limit - 分页限制
   * 返回值：Promise<消息列表响应>
   */
  async getMessages(
    conversationId: number,
    skip: number = 0,
    limit: number = 50
  ): Promise<{
    messages: MessageWithSources[];
    total: number;
    has_more: boolean;
  }> {
    return api.get(`/conversations/${conversationId}/messages`, {
      params: { skip, limit }
    });
  },
};
