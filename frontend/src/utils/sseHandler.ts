/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：SSE流式数据处理工具
 * 内部逻辑：提供统一的SSE流式响应解析功能，支持多种事件类型回调
 */

/**
 * 类型定义：SSE事件回调接口
 * 内部逻辑：定义各种SSE事件的回调函数类型
 */
export interface SSECallbacks<TChunk = string, TSources = any> {
  /** 内容分块回调，接收流式返回的内容片段 */
  onChunk?: (chunk: TChunk) => void;
  /** 来源数据回调，接收检索到的相关文档来源 */
  onSources?: (sources: TSources[]) => void;
  /** 完成回调，流式传输结束时触发 */
  onDone?: () => void;
  /** 错误回调，接收错误信息 */
  onError?: (error: string) => void;
}

/**
 * 类型定义：SSE数据结构
 * 内部逻辑：定义后端返回的SSE数据格式
 */
interface SSEData {
  /** 回答内容片段 */
  answer?: string;
  /** 来源数据 */
  sources?: any[];
  /** 完成标志 */
  done?: boolean;
  /** 错误信息 */
  error?: string;
}

/**
 * 类：SSE流式处理器
 * 设计模式：模板方法模式
 * 职责：统一处理SSE流式响应，解析事件数据并分发到对应回调
 */
export class SSEHandler {
  /**
   * 内部变量：SSE数据前缀常量
   * 内部逻辑：定义SSE标准格式前缀
   */
  private static readonly SSE_DATA_PREFIX = 'data: ';

  /**
   * 函数级注释：处理SSE流式响应
   * 内部逻辑：读取Response流，按行解析SSE格式数据，分发到对应回调
   * 设计模式：模板方法模式，定义SSE处理的标准流程
   *
   * 参数：
   *   response - Fetch API的Response对象
   *   callbacks - 事件回调集合
   *
   * 返回值：Promise<void> - 处理完成后resolve
   *
   * @throws 当HTTP状态非2xx时抛出错误
   */
  static async processStream<TChunk = string, TSources = any>(
    response: Response,
    callbacks: SSECallbacks<TChunk, TSources>
  ): Promise<void> {
    // Guard Clauses：检查HTTP状态
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    // 内部变量：获取流式读取器
    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('Response body is not readable');
    }

    // 内部变量：文本解码器，用于将Uint8Array转换为字符串
    const decoder = new TextDecoder();
    // 内部变量：buffer用于存储跨chunk的未完成数据行
    let buffer = '';

    try {
      // 内部逻辑：持续读取流式数据直到完成
      while (true) {
        // 内部变量：读取下一个数据块
        const { done, value } = await reader.read();

        // 内部逻辑：流式传输完成时退出循环
        if (done) {
          break;
        }

        // 内部变量：解码当前chunk为字符串（stream模式保留编码状态）
        const chunk = decoder.decode(value, { stream: true });
        // 内部逻辑：将新数据追加到buffer
        buffer += chunk;

        // 内部逻辑：按行分割buffer处理完整的SSE事件
        const lines = buffer.split('\n');
        // 内部逻辑：保留最后一个可能未完成的行
        buffer = lines.pop() || '';

        // 内部逻辑：遍历每一行SSE数据
        for (const line of lines) {
          this.processLine(line, callbacks);
        }
      }

      // 内部逻辑：处理buffer中剩余的最后数据
      if (buffer.trim()) {
        this.processLine(buffer, callbacks);
      }
    } finally {
      // 内部逻辑：确保释放reader资源
      reader.releaseLock();
    }
  }

  /**
   * 函数级注释：处理单行SSE数据
   * 内部逻辑：解析SSE格式的单行数据，根据内容类型分发回调
   *
   * 参数：
   *   line - SSE单行数据
   *   callbacks - 事件回调集合
   *
   * 返回值：void
   *
   * @private
   */
  private static processLine<TChunk = string, TSources = any>(
    line: string,
    callbacks: SSECallbacks<TChunk, TSources>
  ): void {
    // 内部变量：去除首尾空白字符
    const trimmedLine = line.trim();

    // Guard Clauses：跳过空行和SSE注释行（以:开头）
    if (!trimmedLine || trimmedLine.startsWith(':')) {
      return;
    }

    // Guard Clauses：只处理data:开头的SSE数据行
    if (!trimmedLine.startsWith(this.SSE_DATA_PREFIX)) {
      return;
    }

    // 内部变量：提取data:后面的JSON字符串
    const dataStr = trimmedLine.slice(this.SSE_DATA_PREFIX.length);

    try {
      // 内部变量：解析JSON数据
      const data: SSEData = JSON.parse(dataStr);

      // 内部逻辑：优先处理错误回调
      if (data.error && callbacks.onError) {
        callbacks.onError(data.error);
        return;
      }

      // 内部逻辑：处理内容分块
      if (data.answer && callbacks.onChunk) {
        callbacks.onChunk(data.answer as TChunk);
      }

      // 内部逻辑：处理来源数据
      if (data.sources && callbacks.onSources) {
        callbacks.onSources(data.sources as TSources[]);
      }

      // 内部逻辑：处理完成标志
      if (data.done && callbacks.onDone) {
        callbacks.onDone();
      }
    } catch (error) {
      // 内部逻辑：JSON解析失败时输出警告，不中断流处理
      console.warn('[SSEHandler] Failed to parse SSE data:', dataStr, error);
    }
  }

  /**
   * 函数级注释：发起流式请求并处理响应
   * 内部逻辑：封装fetch请求和SSE处理流程，提供便捷的一站式接口
   * 设计模式：模板方法模式 + 外观模式
   *
   * 参数：
   *   url - 请求URL
   *   request - 请求体数据
   *   callbacks - 事件回调集合
   *   options - 可选的fetch配置
   *
   * 返回值：Promise<void> - 处理完成后resolve
   */
  static async fetchWithStream<TRequest = any, TChunk = string, TSources = any>(
    url: string,
    request: TRequest,
    callbacks: SSECallbacks<TChunk, TSources>,
    options?: RequestInit
  ): Promise<void> {
    // 内部变量：合并fetch配置
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      body: JSON.stringify({ ...request, stream: true }),
      ...options,
    });

    // 内部逻辑：使用processStream处理响应
    await this.processStream(response, callbacks);
  }
}

/**
 * 类型定义：SSE事件类型枚举
 * 内部逻辑：定义SSE处理器支持的事件类型
 */
export enum SSEEventType {
  /** 内容分块事件 */
  CHUNK = 'chunk',
  /** 来源数据事件 */
  SOURCES = 'sources',
  /** 完成事件 */
  DONE = 'done',
  /** 错误事件 */
  ERROR = 'error',
}

/**
 * 类型定义：事件监听器类型
 * 内部逻辑：定义事件监听器的函数签名
 */
type EventListener<T> = (data: T) => void;

/**
 * 类：SSE事件发射器
 * 设计模式：观察者模式
 * 职责：提供事件订阅和发布机制，支持多个监听器监听同一事件
 */
export class SSEEventEmitter {
  /**
   * 内部变量：事件监听器映射表
   * 内部逻辑：存储各事件类型对应的监听器列表
   */
  private listeners: Map<SSEEventType, Set<EventListener<any>>> = new Map();

  /**
   * 函数级注释：订阅事件
   * 内部逻辑：为指定事件类型添加监听器
   *
   * 参数：
   *   event - 事件类型
   *   listener - 事件监听器函数
   *
   * 返回值：取消订阅的函数
   */
  on<T = any>(event: SSEEventType, listener: EventListener<T>): () => void {
    // 内部逻辑：获取或创建事件类型的监听器集合
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    const eventListeners = this.listeners.get(event)!;

    // 内部逻辑：添加监听器
    eventListeners.add(listener);

    // 内部逻辑：返回取消订阅函数
    return () => {
      eventListeners.delete(listener);
    };
  }

  /**
   * 函数级注释：发射事件
   * 内部逻辑：触发指定事件的所有监听器
   *
   * 参数：
   *   event - 事件类型
   *   data - 事件数据
   *
   * 返回值：void
   */
  emit<T = any>(event: SSEEventType, data: T): void {
    // 内部变量：获取事件的监听器集合
    const eventListeners = this.listeners.get(event);

    // Guard Clauses：无监听器时直接返回
    if (!eventListeners) {
      return;
    }

    // 内部逻辑：通知所有监听器
    for (const listener of eventListeners) {
      listener(data);
    }
  }

  /**
   * 函数级注释：移除事件的所有监听器
   * 内部逻辑：清空指定事件类型的监听器集合
   *
   * 参数：
   *   event - 事件类型（可选，不传则清空所有事件）
   *
   * 返回值：void
   */
  clear(event?: SSEEventType): void {
    if (event) {
      this.listeners.delete(event);
    } else {
      this.listeners.clear();
    }
  }

  /**
   * 函数级注释：获取事件的监听器数量
   * 内部逻辑：返回指定事件类型的监听器数量
   *
   * 参数：
   *   event - 事件类型
   *
   * 返回值：监听器数量
   */
  listenerCount(event: SSEEventType): number {
    return this.listeners.get(event)?.size || 0;
  }
}
