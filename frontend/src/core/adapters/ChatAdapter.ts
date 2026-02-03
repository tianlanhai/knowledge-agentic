/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：聊天服务适配器模块
 * 内部逻辑：适配不同的聊天服务实现，解耦组件与服务
 * 设计模式：适配器模式（Adapter Pattern）+ 依赖注入
 * 设计原则：依赖倒置原则、开闭原则
 */

import { chatService } from '../../services/chatService';
import type { Message, SourceDetail } from '../../types/chat';

/**
 * 接口：聊天服务端口
 * 内部逻辑：定义聊天服务的抽象接口
 * 设计模式：端口适配器模式
 */
export interface IChatServicePort {
  /**
   * 发送消息
   * 参数：request - 聊天请求
   * 返回值：Promise<ChatResponse>
   */
  sendMessage(request: ChatRequest): Promise<ChatResponse>;

  /**
   * 流式发送消息
   * 参数：
   *   request - 聊天请求
   *   callbacks - 回调函数集合
   * 返回值：Promise<void>
   */
  streamSendMessage(
    request: ChatRequest,
    callbacks: StreamCallbacks
  ): Promise<void>;

  /**
   * 获取来源详情
   * 参数：docId - 可选的文档ID
   * 返回值：Promise<SourceDetail[]>
   */
  getSources(docId?: number): Promise<SourceDetail[]>;
}

/**
 * 接口：流式回调
 */
export interface StreamCallbacks {
  /** 数据块回调 */
  onChunk?: (chunk: string) => void;
  /** 来源数据回调 */
  onSources?: (sources: SourceDetail[]) => void;
  /** 完成回调 */
  onComplete?: () => void;
  /** 错误回调 */
  onError?: (error: Error) => void;
}

/**
 * 接口：聊天请求
 */
export interface ChatRequest {
  /** 消息内容 */
  message: string;
  /** 对话历史 */
  history?: Message[];
  /** 是否使用Agent模式 */
  use_agent?: boolean;
  /** 是否流式 */
  stream?: boolean;
}

/**
 * 接口：聊天响应
 */
export interface ChatResponse {
  /** 回答内容 */
  answer: string;
  /** 来源详情 */
  sources: SourceDetail[];
}

/**
 * 类：聊天服务适配器
 * 内部逻辑：适配具体的chatService实现
 * 设计模式：适配器模式
 * 职责：
 *  1. 适配不同的聊天服务实现
 *  2. 提供统一的接口
 *  3. 处理错误和异常
 */
export class ChatServiceAdapter implements IChatServicePort {
  /**
   * 内部变量：适配的服务实例
   */
  private service: typeof chatService;

  constructor(service: typeof chatService = chatService) {
    this.service = service;
  }

  /**
   * 函数级注释：发送消息
   * 参数：request - 聊天请求
   * 返回值：Promise<ChatResponse>
   */
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    return await this.service.chatCompletion({
      message: request.message,
      history: request.history || [],
      use_agent: request.use_agent || false,
      stream: false,
    });
  }

  /**
   * 函数级注释：流式发送消息
   * 参数：
   *   request - 聊天请求
   *   callbacks - 回调函数集合
   * 返回值：Promise<void>
   */
  async streamSendMessage(
    request: ChatRequest,
    callbacks: StreamCallbacks
  ): Promise<void> {
    try {
      await this.service.streamChatCompletion(
        {
          message: request.message,
          history: request.history || [],
          use_agent: request.use_agent || false,
          stream: true,
        },
        callbacks.onChunk || (() => {}),
        callbacks.onSources,
        callbacks.onComplete
      );
    } catch (error) {
      if (callbacks.onError) {
        callbacks.onError(error as Error);
      } else {
        throw error;
      }
    }
  }

  /**
   * 函数级注释：获取来源详情
   * 参数：docId - 可选的文档ID
   * 返回值：Promise<SourceDetail[]>
   */
  async getSources(docId?: number): Promise<SourceDetail[]> {
    return await this.service.getSources(docId);
  }
}

/**
 * 变量：默认适配器实例
 */
export const chatAdapter = new ChatServiceAdapter();

/**
 * 变量：导出所有公共接口
 */
export default chatAdapter;
