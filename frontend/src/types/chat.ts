/**
 * 上海宇羲伏天智能科技有限公司出品
 *
/**
 * 消息流式状态枚举
 * 内部变量：标识消息的流式输出状态
 */
export enum MessageStreamingState {
  /** 非流式消息或已完成 */
  IDLE = 'idle',
  /** 正在流式输出 */
  STREAMING = 'streaming',
  /** 流式已完成，可格式化 */
  COMPLETED = 'completed'
}

/**
 * 消息接口
 * 属性：role - 消息角色
 * 属性：content - 消息内容
 * 属性：streamingState - 流式状态（可选）
 */
export interface Message {
  role: 'user' | 'assistant';
  content: string;
  streamingState?: MessageStreamingState;
}

export interface ChatRequest {
  message: string;
  query?: string;
  conversation_id?: number;
  system_prompt?: string;
  model_config?: Record<string, any>;
  history?: Message[];
  use_agent?: boolean;
  stream?: boolean;
  formatting_options?: FormattingOptions;
  // 搜索相关
  enable_search?: boolean;
  top_k?: number;
  // 文档相关
  doc_id?: number;
  doc_ids?: number[];
  // 模型参数
  temperature?: number;
  max_tokens?: number;
  language?: string;
}

export interface ChatResponse {
  answer: string;
  sources: SourceDetail[];
  formatting_applied: boolean;
}

export interface SourceDetail {
  doc_id: number;
  file_name: string;
  text_segment: string;
  score: number;
}

export interface FormattingOptions {
  enable_markdown?: boolean;
  enable_structured?: boolean;
  highlight_keywords?: string[];
  max_content_length?: number;
  code_highlighting?: boolean;
  link_target?: string;
  table_styling?: boolean;
  list_styling?: boolean;
  quote_styling?: boolean;
  heading_styling?: boolean;
  highlight_style?: 'background' | 'border' | 'text';
  case_sensitive?: boolean;
  whole_word?: boolean;
}

export interface FormattedContent {
  original: string;
  formatted: string;
  applied_formatting: string[];
}

export interface SummaryRequest {
  doc_id: number;
}

export interface SummaryResponse {
  result: string;
}

export interface ComparisonRequest {
  doc_ids: number[];
}

// ============================================================================
// 对话持久化相关类型
// ============================================================================

/**
 * 消息角色枚举
 */
export enum MessageRole {
  USER = 'user',
  ASSISTANT = 'assistant',
  SYSTEM = 'system'
}

/**
 * 会话接口
 */
export interface Conversation {
  id: number;
  title: string;
  model_name?: string;
  use_agent: boolean;
  total_tokens: number;
  total_cost: number;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message?: string;
}

/**
 * 消息来源引用接口
 */
export interface MessageSource {
  id: number;
  document_id?: number;
  chunk_id?: string;
  file_name: string;
  text_segment: string;
  score?: number;
  position: number;
}

/**
 * 扩展消息接口，添加持久化字段
 */
export interface MessageWithSources extends Message {
  id?: number;
  conversation_id?: number;
  streaming_state?: string;
  tokens_count?: number;
  created_at?: string;
  sources?: MessageSource[];
}

/**
 * 会话详情接口
 */
export interface ConversationDetail {
  conversation: Conversation;
  messages: MessageWithSources[];
}

/**
 * Token使用统计接口
 */
export interface TokenUsage {
  id: number;
  model_name: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  prompt_cost: number;
  completion_cost: number;
  total_cost: number;
}

/**
 * 创建会话请求
 */
export interface CreateConversationRequest {
  title?: string;
  model_name?: string;
  use_agent?: boolean;
}

/**
 * 发送消息请求
 */
export interface SendMessageRequest {
  content: string;
  use_agent?: boolean;
  stream?: boolean;
}
