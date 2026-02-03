/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：聊天消息建造者模块
 * 内部逻辑：提供流式的聊天消息构建接口
 * 设计模式：建造者模式（Builder Pattern）
 * 设计原则：单一职责原则（SRP）、开闭原则（OCP）
 */

/**
 * 类型：消息角色
 */
export type MessageRole = 'system' | 'user' | 'assistant' | 'tool';

/**
 * 接口：聊天消息接口
 */
export interface ChatMessage {
  /** 内部属性：消息角色 */
  role: MessageRole;
  /** 内部属性：消息内容 */
  content: string;
  /** 内部属性：消息 ID */
  id?: string;
  /** 内部属性：时间戳 */
  timestamp?: number;
  /** 内部属性：元数据 */
  metadata?: Record<string, any>;
  /** 内部属性：工具调用（tool 消息专用） */
  toolCalls?: ToolCall[];
  /** 内部属性：Token 使用量 */
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
}

/**
 * 接口：工具调用
 */
export interface ToolCall {
  /** 内部属性：工具 ID */
  id: string;
  /** 内部属性：工具名称 */
  name: string;
  /** 内部属性：工具参数（JSON 字符串） */
  arguments: string;
}

/**
 * 接口：构建结果
 */
export interface BuildResult<T> {
  /** 内部属性：是否成功 */
  success: boolean;
  /** 内部属性：构建结果 */
  result?: T;
  /** 内部属性：错误列表 */
  errors: string[];
  /** 内部属性：构建耗时（毫秒） */
  duration: number;
}

/**
 * 类级注释：聊天消息建造者
 * 设计模式：建造者模式（Builder Pattern）
 * 职责：
 *   1. 流式构建聊天消息
 *   2. 参数验证
 *   3. 默认值处理
 *
 * @example
 * ```typescript
 * const message = new ChatMessageBuilder()
 *   .withRole('user')
 *   .withContent('Hello, AI!')
 *   .withMetadata({ source: 'web' })
 *   .build();
 * ```
 */
export class ChatMessageBuilder {
  /** 内部变量：消息角色 */
  private _role: MessageRole = 'user';

  /** 内部变量：消息内容 */
  private _content: string = '';

  /** 内部变量：消息 ID */
  private _id?: string;

  /** 内部变量：时间戳 */
  private _timestamp?: number;

  /** 内部变量：元数据 */
  private _metadata: Record<string, any> = {};

  /** 内部变量：工具调用 */
  private _toolCalls: ToolCall[] = [];

  /** 内部变量：Token 使用量 */
  private _usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };

  /**
   * 函数级注释：设置消息角色
   * 参数：
   *   role - 消息角色
   * 返回值：建造者自身（支持链式调用）
   */
  withRole(role: MessageRole): this {
    this._role = role;
    return this;
  }

  /**
   * 函数级注释：设置消息内容
   * 参数：
   *   content - 消息内容
   * 返回值：建造者自身
   */
  withContent(content: string): this {
    this._content = content;
    return this;
  }

  /**
   * 函数级注释：追加消息内容
   * 参数：
   *   content - 要追加的内容
   * 返回值：建造者自身
   */
  appendContent(content: string): this {
    this._content += content;
    return this;
  }

  /**
   * 函数级注释：设置消息 ID
   * 参数：
   *   id - 消息 ID
   * 返回值：建造者自身
   */
  withId(id: string): this {
    this._id = id;
    return this;
  }

  /**
   * 函数级注释：设置时间戳
   * 参数：
   *   timestamp - 时间戳（默认当前时间）
   * 返回值：建造者自身
   */
  withTimestamp(timestamp?: number): this {
    this._timestamp = timestamp ?? Date.now();
    return this;
  }

  /**
   * 函数级注释：设置元数据
   * 参数：
   *   metadata - 元数据对象
   * 返回值：建造者自身
   */
  withMetadata(metadata: Record<string, any>): this {
    this._metadata = { ...this._metadata, ...metadata };
    return this;
  }

  /**
   * 函数级注释：添加单个元数据
   * 参数：
   *   key - 键
   *   value - 值
   * 返回值：建造者自身
   */
  addMetadata(key: string, value: any): this {
    this._metadata[key] = value;
    return this;
  }

  /**
   * 函数级注释：添加工具调用
   * 参数：
   *   toolCall - 工具调用对象
   * 返回值：建造者自身
   */
  addToolCall(toolCall: ToolCall): this {
    this._toolCalls.push(toolCall);
    return this;
  }

  /**
   * 函数级注释：设置 Token 使用量
   * 参数：
   *   promptTokens - 提示 Token 数
   *   completionTokens - 完成 Token 数
   * 返回值：建造者自身
   */
  withUsage(
    promptTokens: number,
    completionTokens: number
  ): this {
    this._usage = {
      promptTokens,
      completionTokens,
      totalTokens: promptTokens + completionTokens,
    };
    return this;
  }

  /**
   * 函数级注释：构建消息对象
   * 返回值：构建结果
   */
  build(): BuildResult<ChatMessage> {
    const startTime = performance.now();
    const errors: string[] = [];
    let success = true;

    // 内部逻辑：验证必需参数
    if (!this._content) {
      errors.push('消息内容不能为空');
      success = false;
    }

    // 内部逻辑：如果有错误，返回失败结果
    if (!success) {
      return {
        success: false,
        errors,
        duration: performance.now() - startTime,
      };
    }

    // 内部逻辑：构建消息对象
    const message: ChatMessage = {
      role: this._role,
      content: this._content,
    };

    // 内部逻辑：添加可选属性
    if (this._id) {
      message.id = this._id;
    } else {
      // 内部逻辑：自动生成 ID
      message.id = `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    if (this._timestamp !== undefined) {
      message.timestamp = this._timestamp;
    } else {
      message.timestamp = Date.now();
    }

    if (Object.keys(this._metadata).length > 0) {
      message.metadata = { ...this._metadata };
    }

    if (this._toolCalls.length > 0) {
      message.toolCalls = [...this._toolCalls];
    }

    if (this._usage) {
      message.usage = { ...this._usage };
    }

    return {
      success: true,
      result: message,
      errors: [],
      duration: performance.now() - startTime,
    };
  }

  /**
   * 函数级注释：重置建造者状态
   * 返回值：void
   */
  reset(): void {
    this._role = 'user';
    this._content = '';
    this._id = undefined;
    this._timestamp = undefined;
    this._metadata = {};
    this._toolCalls = [];
    this._usage = undefined;
  }

  /**
   * 函数级注释：克隆建造者
   * 返回值：新的建造者实例（包含当前状态）
   */
  clone(): ChatMessageBuilder {
    const builder = new ChatMessageBuilder();
    builder._role = this._role;
    builder._content = this._content;
    builder._id = this._id;
    builder._timestamp = this._timestamp;
    builder._metadata = { ...this._metadata };
    builder._toolCalls = [...this._toolCalls];
    builder._usage = this._usage ? { ...this._usage } : undefined;
    return builder;
  }
}

/**
 * 类级注释：聊天请求建造者
 * 设计模式：建造者模式（Builder Pattern）
 * 职责：构建完整的聊天请求对象
 */
export class ChatRequestBuilder {
  /** 内部变量：用户消息 */
  private _message?: string;

  /** 内部变量：对话历史 */
  private _history: ChatMessage[] = [];

  /** 内部变量：是否使用智能体 */
  private _useAgent: boolean = false;

  /** 内部变量：是否流式输出 */
  private _stream: boolean = false;

  /** 内部变量：温度参数 */
  private _temperature: number = 0.7;

  /** 内部变量：最大 tokens */
  private _maxTokens?: number;

  /** 内部变量：Top P 参数 */
  private _topP: number = 1.0;

  /** 内部变量：频率惩罚 */
  private _frequencyPenalty: number = 0.0;

  /** 内部变量：存在惩罚 */
  private _presencePenalty: number = 0.0;

  /** 内部变量：停止序列 */
  private _stop: string[] = [];

  /** 内部变量：模型名称 */
  private _model?: string;

  /** 内部变量：会话 ID */
  private _conversationId?: string;

  /**
   * 函数级注释：设置用户消息
   */
  withMessage(message: string): this {
    this._message = message;
    return this;
  }

  /**
   * 函数级注释：设置对话历史
   */
  withHistory(history: ChatMessage[]): this {
    this._history = [...history];
    return this;
  }

  /**
   * 函数级注释：添加历史消息
   */
  addHistory(role: MessageRole, content: string): this {
    this._history.push({ role, content, timestamp: Date.now() });
    return this;
  }

  /**
   * 函数级注释：设置智能体模式
   */
  withAgent(enabled: boolean = true): this {
    this._useAgent = enabled;
    return this;
  }

  /**
   * 函数级注释：设置流式输出
   */
  withStreaming(enabled: boolean = true): this {
    this._stream = enabled;
    return this;
  }

  /**
   * 函数级注释：设置温度参数
   */
  withTemperature(temperature: number): this {
    this._temperature = temperature;
    return this;
  }

  /**
   * 函数级注释：设置最大 tokens
   */
  withMaxTokens(maxTokens: number): this {
    this._maxTokens = maxTokens;
    return this;
  }

  /**
   * 函数级注释：设置模型
   */
  withModel(model: string): this {
    this._model = model;
    return this;
  }

  /**
   * 函数级注释：设置会话 ID
   */
  withConversation(conversationId: string): this {
    this._conversationId = conversationId;
    return this;
  }

  /**
   * 函数级注释：构建请求对象
   */
  build(): BuildResult<{
    message: string;
    history: ChatMessage[];
    use_agent: boolean;
    stream: boolean;
    parameters?: Record<string, any>;
    conversation_id?: string;
  }> {
    const startTime = performance.now();
    const errors: string[] = [];
    let success = true;

    // 内部逻辑：验证必需参数
    if (!this._message) {
      errors.push('消息内容不能为空');
      success = false;
    }

    // 内部逻辑：验证参数范围
    if (this._temperature < 0 || this._temperature > 2) {
      errors.push(`温度值必须在 0-2 之间: ${this._temperature}`);
      success = false;
    }

    if (this._topP < 0 || this._topP > 1) {
      errors.push(`top_p 值必须在 0-1 之间: ${this._topP}`);
      success = false;
    }

    if (this._maxTokens !== undefined && this._maxTokens <= 0) {
      errors.push(`max_tokens 必须大于0: ${this._maxTokens}`);
      success = false;
    }

    // 内部逻辑：如果有错误，返回失败结果
    if (!success) {
      return {
        success: false,
        errors,
        duration: performance.now() - startTime,
      };
    }

    // 内部逻辑：构建请求对象
    const request: {
      message: string;
      history: ChatMessage[];
      use_agent: boolean;
      stream: boolean;
      parameters?: Record<string, any>;
      conversation_id?: string;
    } = {
      message: this._message,
      history: this._history,
      use_agent: this._useAgent,
      stream: this._stream,
    };

    // 内部逻辑：添加可选参数
    const params: Record<string, any> = {};

    if (this._temperature !== 0.7) {
      params.temperature = this._temperature;
    }
    if (this._maxTokens !== undefined) {
      params.max_tokens = this._maxTokens;
    }
    if (this._topP !== 1.0) {
      params.top_p = this._topP;
    }
    if (this._frequencyPenalty !== 0.0) {
      params.frequency_penalty = this._frequencyPenalty;
    }
    if (this._presencePenalty !== 0.0) {
      params.presence_penalty = this._presencePenalty;
    }
    if (this._stop.length > 0) {
      params.stop = this._stop;
    }
    if (this._model) {
      params.model = this._model;
    }

    if (Object.keys(params).length > 0) {
      request.parameters = params;
    }

    if (this._conversationId) {
      request.conversation_id = this._conversationId;
    }

    return {
      success: true,
      result: request,
      errors: [],
      duration: performance.now() - startTime,
    };
  }

  /**
   * 函数级注释：重置建造者
   */
  reset(): void {
    this._message = undefined;
    this._history = [];
    this._useAgent = false;
    this._stream = false;
    this._temperature = 0.7;
    this._maxTokens = undefined;
    this._topP = 1.0;
    this._frequencyPenalty = 0.0;
    this._presencePenalty = 0.0;
    this._stop = [];
    this._model = undefined;
    this._conversationId = undefined;
  }
}

/**
 * 类级注释：搜索查询建造者
 * 设计模式：建造者模式（Builder Pattern）
 * 职责：构建搜索查询对象
 */
export class SearchQueryBuilder {
  /** 内部变量：搜索文本 */
  private _text?: string;

  /** 内部变量：过滤条件 */
  private _filters: Record<string, any> = {};

  /** 内部变量：返回数量 */
  private _limit: number = 10;

  /** 内部变量：偏移量 */
  private _offset: number = 0;

  /** 内部变量：排序字段 */
  private _sortBy?: string;

  /** 内部变量：排序方向 */
  private _sortOrder: 'asc' | 'desc' = 'desc';

  /** 内部变量：相似度阈值 */
  private _scoreThreshold?: number;

  /**
   * 函数级注释：设置搜索文本
   */
  withText(text: string): this {
    this._text = text;
    return this;
  }

  /**
   * 函数级注释：设置过滤条件
   */
  withFilters(filters: Record<string, any>): this {
    this._filters = { ...this._filters, ...filters };
    return this;
  }

  /**
   * 函数级注释：添加过滤条件
   */
  addFilter(key: string, value: any): this {
    this._filters[key] = value;
    return this;
  }

  /**
   * 函数级注释：设置分页
   */
  withPagination(limit: number, offset: number = 0): this {
    this._limit = limit;
    this._offset = offset;
    return this;
  }

  /**
   * 函数级注释：设置排序
   */
  withSort(sortBy: string, order: 'asc' | 'desc' = 'desc'): this {
    this._sortBy = sortBy;
    this._sortOrder = order;
    return this;
  }

  /**
   * 函数级注释：设置相似度阈值
   */
  withScoreThreshold(threshold: number): this {
    this._scoreThreshold = threshold;
    return this;
  }

  /**
   * 函数级注释：构建查询对象
   */
  build(): BuildResult<{
    query: string;
    filters?: Record<string, any>;
    limit: number;
    offset: number;
    sort?: { by: string; order: 'asc' | 'desc' };
    score_threshold?: number;
  }> {
    const startTime = performance.now();
    const errors: string[] = [];
    let success = true;

    if (!this._text) {
      errors.push('搜索文本不能为空');
      success = false;
    }

    if (this._limit <= 0) {
      errors.push(`limit 必须大于0: ${this._limit}`);
      success = false;
    }

    if (this._offset < 0) {
      errors.push(`offset 不能为负数: ${this._offset}`);
      success = false;
    }

    if (!success) {
      return {
        success: false,
        errors,
        duration: performance.now() - startTime,
      };
    }

    const query: {
      query: string;
      filters?: Record<string, any>;
      limit: number;
      offset: number;
      sort?: { by: string; order: 'asc' | 'desc' };
      score_threshold?: number;
    } = {
      query: this._text,
      limit: this._limit,
      offset: this._offset,
    };

    if (Object.keys(this._filters).length > 0) {
      query.filters = { ...this._filters };
    }

    if (this._sortBy) {
      query.sort = { by: this._sortBy, order: this._sortOrder };
    }

    if (this._scoreThreshold !== undefined) {
      query.score_threshold = this._scoreThreshold;
    }

    return {
      success: true,
      result: query,
      errors: [],
      duration: performance.now() - startTime,
    };
  }

  /**
   * 函数级注释：重置建造者
   */
  reset(): void {
    this._text = undefined;
    this._filters = {};
    this._limit = 10;
    this._offset = 0;
    this._sortBy = undefined;
    this._sortOrder = 'desc';
    this._scoreThreshold = undefined;
  }
}
