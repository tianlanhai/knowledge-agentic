/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：聊天策略模式模块
 * 内部逻辑：使用策略模式封装不同的聊天处理策略
 * 设计模式：策略模式（Strategy Pattern）
 * 设计原则：开闭原则、单一职责原则
 *
 * 使用场景：
 *   - 不同类型的对话处理
 *   - 动态切换聊天策略
 *   - 策略组合使用
 */

import type { ChatRequest } from '../types/chat';

/**
 * 聊天类型枚举
 */
export enum ChatType {
  /** 智能问答 */
  QA = 'qa',
  /** 文档总结 */
  SUMMARY = 'summary',
  /** 文档对比 */
  COMPARE = 'compare',
  /** 自由对话 */
  CHAT = 'chat',
  /** 创意写作 */
  CREATIVE = 'creative',
  /** 代码助手 */
  CODE = 'code',
}

/**
 * 聊天策略接口
 * 设计模式：策略模式 - 策略接口
 * 职责：定义聊天策略的通用接口
 */
export interface IChatStrategy {
  /**
   * 属性：策略名称
   */
  readonly name: string;

  /**
   * 属性：策略类型
   */
  readonly type: ChatType;

  /**
   * 函数级注释：构建聊天请求
   * 参数：
   *   query - 用户查询
   *   context - 上下文数据
   * 返回值：聊天请求对象
   */
  buildRequest(query: string, context?: any): ChatRequest;

  /**
   * 函数级注释：处理响应
   * 参数：
   *   response - API响应
   * 返回值：处理后的数据
   */
  handleResponse(response: any): any;

  /**
   * 函数级注释：获取系统提示词
   * 返回值：系统提示词字符串
   */
  getSystemPrompt(): string;
}

/**
 * 基础聊天策略
 * 设计模式：策略模式 - 抽象策略
 * 职责：提供默认实现
 */
abstract class BaseChatStrategy implements IChatStrategy {
  abstract readonly name: string;
  abstract readonly type: ChatType;

  /**
   * 函数级注释：构建聊天请求（模板方法）
   */
  buildRequest(query: string, context: any = {}): ChatRequest {
    return {
      query,
      conversation_id: context.conversationId,
      stream: true,
      system_prompt: this.getSystemPrompt(),
      model_config: context.modelConfig,
    };
  }

  /**
   * 函数级注释：处理响应（默认实现）
   */
  handleResponse(response: any): any {
    return response;
  }

  /**
   * 函数级注释：获取系统提示词（子类实现）
   */
  abstract getSystemPrompt(): string;
}

/**
 * 智能问答策略
 * 设计模式：策略模式 - 具体策略
 * 职责：实现智能问答的特定逻辑
 */
export class QAStrategy extends BaseChatStrategy {
  readonly name = '问答策略';
  readonly type = ChatType.QA;

  getSystemPrompt(): string {
    return `你是一个专业的智能问答助手。请根据提供的文档内容回答用户问题。

回答要求：
1. 仅基于提供的文档内容回答，不要编造信息
2. 如果文档中没有相关信息，明确告知用户
3. 回答要准确、简洁、有条理
4. 可以引用文档中的具体内容支持你的回答`;
  }

  buildRequest(query: string, context: any = {}): ChatRequest {
    const request = super.buildRequest(query, context);
    request.enable_search = true;
    request.top_k = context.topK || 5;
    return request;
  }
}

/**
 * 文档总结策略
 * 设计模式：策略模式 - 具体策略
 * 职责：实现文档总结的特定逻辑
 */
export class SummaryStrategy extends BaseChatStrategy {
  readonly name = '总结策略';
  readonly type = ChatType.SUMMARY;

  getSystemPrompt(): string {
    return `你是一个专业的文档总结助手。请对提供的文档内容进行总结。

总结要求：
1. 提取文档的核心观点和关键信息
2. 保持逻辑清晰，层次分明
3. 使用简洁的语言表达
4. 突出文档的价值和意义
5. 总结长度控制在原文的20%-30%`;
  }

  buildRequest(query: string, context: any = {}): ChatRequest {
    const request = super.buildRequest(query, context);
    request.doc_id = context.docId;
    return request;
  }
}

/**
 * 文档对比策略
 * 设计模式：策略模式 - 具体策略
 * 职责：实现文档对比的特定逻辑
 */
export class CompareStrategy extends BaseChatStrategy {
  readonly name = '对比策略';
  readonly type = ChatType.COMPARE;

  getSystemPrompt(): string {
    return `你是一个专业的文档对比分析助手。请对比分析多个文档的内容。

对比要求：
1. 识别各文档的共同点和差异点
2. 分析各文档的立场和观点
3. 总结各文档的优势和不足
4. 提供客观、中立的对比结论
5. 使用表格或列表形式呈现对比结果`;
  }

  buildRequest(query: string, context: any = {}): ChatRequest {
    const request = super.buildRequest(query, context);
    request.doc_ids = context.docIds || [];
    return request;
  }
}

/**
 * 自由对话策略
 * 设计模式：策略模式 - 具体策略
 * 职责：实现自由对话的特定逻辑
 */
export class ChatStrategy extends BaseChatStrategy {
  readonly name = '对话策略';
  readonly type = ChatType.CHAT;

  getSystemPrompt(): string {
    return `你是一个友好、专业的AI助手。请与用户进行自然对话。

对话要求：
1. 使用友好、自然的语言
2. 根据对话历史保持上下文连贯
3. 适时提供有用的信息和建议
4. 尊重用户，避免偏见和歧视`;
  }

  buildRequest(query: string, context: any = {}): ChatRequest {
    const request = super.buildRequest(query, context);
    request.enable_search = context.enableSearch || false;
    return request;
  }
}

/**
 * 创意写作策略
 * 设计模式：策略模式 - 具体策略
 * 职责：实现创意写作的特定逻辑
 */
export class CreativeStrategy extends BaseChatStrategy {
  readonly name = '创意写作策略';
  readonly type = ChatType.CREATIVE;

  getSystemPrompt(): string {
    return `你是一个富有创造力的写作助手。请帮助用户完成各种创意写作任务。

写作要求：
1. 根据用户需求提供创意内容
2. 语言生动、富有感染力
3. 结构清晰，逻辑连贯
4. 适当运用修辞手法
5. 鼓励创新和独特视角`;
  }

  buildRequest(query: string, context: any = {}): ChatRequest {
    const request = super.buildRequest(query, context);
    request.temperature = context.temperature || 0.9;
    request.max_tokens = context.maxTokens || 2000;
    return request;
  }
}

/**
 * 代码助手策略
 * 设计模式：策略模式 - 具体策略
 * 职责：实现代码助手的特定逻辑
 */
export class CodeStrategy extends BaseChatStrategy {
  readonly name = '代码助手策略';
  readonly type = ChatType.CODE;

  getSystemPrompt(): string {
    return `你是一个专业的编程助手。请帮助用户解决编程相关问题。

代码要求：
1. 提供准确、高效的代码解决方案
2. 代码要有清晰的注释
3. 解释关键逻辑和实现思路
4. 考虑边界情况和错误处理
5. 遵循最佳实践和设计模式`;
  }

  buildRequest(query: string, context: any = {}): ChatRequest {
    const request = super.buildRequest(query, context);
    request.temperature = context.temperature || 0.2;
    request.language = context.language || 'python';
    return request;
  }
}

/**
 * 聊天策略上下文
 * 设计模式：策略模式 - 上下文类
 * 职责：管理当前使用的聊天策略
 */
export class ChatStrategyContext {
  /** 内部变量：当前策略 */
  private strategy: IChatStrategy;

  /** 内部变量：策略缓存 */
  private static strategies: Map<ChatType, IChatStrategy> = new Map<ChatType, IChatStrategy>([
    [ChatType.QA, new QAStrategy()],
    [ChatType.SUMMARY, new SummaryStrategy()],
    [ChatType.COMPARE, new CompareStrategy()],
    [ChatType.CHAT, new ChatStrategy()],
    [ChatType.CREATIVE, new CreativeStrategy()],
    [ChatType.CODE, new CodeStrategy()],
  ] as Array<[ChatType, IChatStrategy]>);

  constructor(strategy: IChatStrategy) {
    this.strategy = strategy;
  }

  /**
   * 函数级注释：设置策略
   * 参数：strategy - 新的策略
   */
  setStrategy(strategy: IChatStrategy): void {
    this.strategy = strategy;
  }

  /**
   * 函数级注释：按类型设置策略
   * 参数：type - 策略类型
   */
  setStrategyByType(type: ChatType): void {
    const strategy = ChatStrategyContext.strategies.get(type);
    if (strategy) {
      this.strategy = strategy;
    }
  }

  /**
   * 函数级注释：获取当前策略
   * 返回值：当前策略对象
   */
  getStrategy(): IChatStrategy {
    return this.strategy;
  }

  /**
   * 函数级注释：执行策略
   * 参数：
   *   query - 用户查询
   *   context - 上下文数据
   * 返回值：聊天请求对象
   */
  execute(query: string, context?: any): ChatRequest {
    return this.strategy.buildRequest(query, context);
  }

  /**
   * 函数级注释：获取注册的策略类型
   * 返回值：策略类型列表
   */
  static getAvailableTypes(): ChatType[] {
    return Array.from(ChatStrategyContext.strategies.keys());
  }

  /**
   * 函数级注释：注册自定义策略
   * 参数：
   *   type - 策略类型
   *   strategy - 策略实例
   */
  static registerStrategy(type: ChatType, strategy: IChatStrategy): void {
    ChatStrategyContext.strategies.set(type, strategy);
  }

  /**
   * 函数级注释：获取策略
   * 参数：type - 策略类型
   * 返回值：策略实例
   */
  static getStrategy(type: ChatType): IChatStrategy | undefined {
    return ChatStrategyContext.strategies.get(type);
  }
}

/**
 * 聊天策略工厂
 * 设计模式：工厂模式 + 策略模式
 * 职责：创建和管理聊天策略
 */
export class ChatStrategyFactory {
  /** 内部变量：策略上下文 */
  private context: ChatStrategyContext;

  constructor() {
    // 内部逻辑：默认使用问答策略
    this.context = new ChatStrategyContext(new QAStrategy());
  }

  /**
   * 函数级注释：创建问答策略上下文
   * 返回值：策略上下文
   */
  createQA(): ChatStrategyContext {
    this.context.setStrategyByType(ChatType.QA);
    return this.context;
  }

  /**
   * 函数级注释：创建总结策略上下文
   * 返回值：策略上下文
   */
  createSummary(): ChatStrategyContext {
    this.context.setStrategyByType(ChatType.SUMMARY);
    return this.context;
  }

  /**
   * 函数级注释：创建对比策略上下文
   * 返回值：策略上下文
   */
  createCompare(): ChatStrategyContext {
    this.context.setStrategyByType(ChatType.COMPARE);
    return this.context;
  }

  /**
   * 函数级注释：创建自由对话策略上下文
   * 返回值：策略上下文
   */
  createChat(): ChatStrategyContext {
    this.context.setStrategyByType(ChatType.CHAT);
    return this.context;
  }

  /**
   * 函数级注释：创建创意写作策略上下文
   * 返回值：策略上下文
   */
  createCreative(): ChatStrategyContext {
    this.context.setStrategyByType(ChatType.CREATIVE);
    return this.context;
  }

  /**
   * 函数级注释：创建代码助手策略上下文
   * 返回值：策略上下文
   */
  createCode(): ChatStrategyContext {
    this.context.setStrategyByType(ChatType.CODE);
    return this.context;
  }

  /**
   * 函数级注释：根据类型创建策略上下文
   * 参数：type - 策略类型
   * 返回值：策略上下文
   */
  createByType(type: ChatType): ChatStrategyContext {
    this.context.setStrategyByType(type);
    return this.context;
  }

  /**
   * 函数级注释：获取当前上下文
   * 返回值：策略上下文
   */
  getContext(): ChatStrategyContext {
    return this.context;
  }
}

// 导出工厂单例
export const chatStrategyFactory = new ChatStrategyFactory();
