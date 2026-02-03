/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：事件总线模块
 * 内部逻辑：实现类型安全的发布-订阅模式，支持命名空间和自动清理
 * 设计模式：观察者模式（Observer Pattern）+ 中介者模式（Mediator Pattern）
 * 设计原则：开闭原则（OCP）、单一职责原则（SRP）
 */

/**
 * 类级注释：事件监听器函数类型
 * 参数：
 *   TEvent - 事件数据类型
 */
export type EventListener<TEvent = any> = (event: TEvent) => void | Promise<void>;

/**
 * 类级注释：事件订阅信息接口
 * 属性：监听器函数、是否只执行一次、优先级
 */
export interface EventSubscription<TEvent = any> {
  /** 内部属性：监听器函数 */
  listener: EventListener<TEvent>;
  /** 内部属性：是否只执行一次 */
  once: boolean;
  /** 内部属性：优先级（数字越大优先级越高） */
  priority: number;
  /** 内部属性：订阅 ID（用于取消订阅） */
  id: string;
}

/**
 * 类级注释：事件配置接口
 * 属性：最大监听器数量、是否按优先级排序
 */
export interface EventBusConfig {
  /** 内部属性：每个事件的最大监听器数量 */
  maxListeners?: number;
  /** 内部属性：是否按优先级执行 */
  enablePriority?: boolean;
  /** 内部属性：错误处理函数 */
  errorHandler?: (error: Error, event: any, listener: EventListener) => void;
}

/**
 * 类级注释：事件总线类
 * 设计模式：观察者模式 + 中介者模式
 * 职责：
 *   1. 管理事件订阅
 *   2. 发布事件到订阅者
 *   3. 支持命名空间
 *   4. 自动清理订阅
 *
 * @example
 * ```typescript
 * const bus = new EventBus();
 * bus.on('chat:send', (data) => console.log(data));
 * bus.emit('chat:send', { message: 'Hello' });
 * ```
 */
export class EventBus {
  /** 内部变量：事件订阅映射 {eventName: subscriptions[]} */
  private _subscriptions: Map<string, EventSubscription[]>;

  /** 内部变量：命名空间分隔符 */
  private _separator: string;

  /** 内部变量：配置选项 */
  private _config: Required<EventBusConfig>;

  /** 内部变量：订阅 ID 计数器 */
  private _subscriptionIdCounter: number;

  /** 内部变量：全局订阅（监听所有事件） */
  private _wildcardSubscriptions: EventSubscription[];

  /**
   * 函数级注释：构造函数
   * 参数：
   *   config - 事件总线配置
   */
  constructor(config: EventBusConfig = {}) {
    this._subscriptions = new Map();
    this._wildcardSubscriptions = [];
    this._separator = ':';
    this._subscriptionIdCounter = 0;
    this._config = {
      maxListeners: config.maxListeners ?? 100,
      enablePriority: config.enablePriority ?? true,
      errorHandler: config.errorHandler ?? this._defaultErrorHandler,
    };
  }

  /**
   * 函数级注释：订阅事件
   * 参数：
   *   eventName - 事件名称（支持命名空间，如 'chat:message'）
   *   listener - 监听器函数
   *   options - 订阅选项
   * 返回值：取消订阅的函数
   *
   * @example
   * ```typescript
   * const unsubscribe = bus.on('chat:send', (data) => {
   *   console.log('Message sent:', data);
   * });
   * // 取消订阅
   * unsubscribe();
   * ```
   */
  on<TEvent = any>(
    eventName: string,
    listener: EventListener<TEvent>,
    options: {
      /** 是否只执行一次 */
      once?: boolean;
      /** 优先级（数字越大优先级越高） */
      priority?: number;
    } = {}
  ): () => void {
    // 内部逻辑：创建订阅信息
    const subscription: EventSubscription<TEvent> = {
      listener,
      once: options.once ?? false,
      priority: options.priority ?? 0,
      id: `sub_${++this._subscriptionIdCounter}`,
    };

    // 内部逻辑：获取或创建订阅列表
    let subscriptions = this._subscriptions.get(eventName);
    if (!subscriptions) {
      subscriptions = [];
      this._subscriptions.set(eventName, subscriptions);
    }

    // 内部逻辑：检查监听器数量限制
    if (subscriptions.length >= this._config.maxListeners) {
      console.warn(
        `[EventBus] 事件 "${eventName}" 的监听器数量超过限制 ` +
        `(${this._config.maxListeners})，可能导致内存泄漏`
      );
    }

    // 内部逻辑：添加订阅
    subscriptions.push(subscription);

    // 内部逻辑：按优先级排序
    if (this._config.enablePriority) {
      subscriptions.sort((a, b) => b.priority - a.priority);
    }

    // 内部逻辑：返回取消订阅函数
    return () => this.off(eventName, subscription.id);
  }

  /**
   * 函数级注释：订阅一次性事件
   * 参数：
   *   eventName - 事件名称
   *   listener - 监听器函数
   * 返回值：取消订阅的函数
   */
  once<TEvent = any>(
    eventName: string,
    listener: EventListener<TEvent>
  ): () => void {
    return this.on(eventName, listener, { once: true });
  }

  /**
   * 函数级注释：取消订阅
   * 参数：
   *   eventName - 事件名称
   *   subscriptionId - 订阅 ID（可选，不传则取消所有）
   * 返回值：void
   */
  off(eventName: string, subscriptionId?: string): void {
    const subscriptions = this._subscriptions.get(eventName);
    if (!subscriptions) return;

    if (subscriptionId) {
      // 内部逻辑：移除指定订阅
      const index = subscriptions.findIndex(sub => sub.id === subscriptionId);
      if (index !== -1) {
        subscriptions.splice(index, 1);
      }

      // 内部逻辑：如果没有订阅了，删除事件
      if (subscriptions.length === 0) {
        this._subscriptions.delete(eventName);
      }
    } else {
      // 内部逻辑：移除所有订阅
      this._subscriptions.delete(eventName);
    }
  }

  /**
   * 函数级注释：发布事件
   * 参数：
   *   eventName - 事件名称
   *   eventData - 事件数据
   * 返回值：Promise<void>（等待所有异步监听器完成）
   */
  async emit<TEvent = any>(eventName: string, eventData?: TEvent): Promise<void> {
    const subscriptions = this._subscriptions.get(eventName) ?? [];
    const toRemove: string[] = [];

    // 内部逻辑：执行事件订阅
    for (const subscription of subscriptions) {
      try {
        const result = subscription.listener(eventData);

        // 内部逻辑：处理异步监听器
        if (result instanceof Promise) {
          await result;
        }

        // 内部逻辑：标记一次性订阅待删除
        if (subscription.once) {
          toRemove.push(subscription.id);
        }
      } catch (error) {
        this._config.errorHandler(error as Error, eventData, subscription.listener);
      }
    }

    // 内部逻辑：移除一次性订阅
    for (const id of toRemove) {
      this.off(eventName, id);
    }

    // 内部逻辑：触发通配符订阅
    await this._emitWildcard(eventName, eventData);
  }

  /**
   * 函数级注释：发布同步事件（不等待异步完成）
   * 参数：
   *   eventName - 事件名称
   *   eventData - 事件数据
   * 返回值：void
   */
  emitSync<TEvent = any>(eventName: string, eventData?: TEvent): void {
    // 内部逻辑：不等待异步完成
    this.emit(eventName, eventData).catch(error => {
      console.error(`[EventBus] 事件 "${eventName}" 异步处理失败:`, error);
    });
  }

  /**
   * 函数级注释：订阅通配符事件（监听所有事件）
   * 参数：
   *   listener - 监听器函数
   *   pattern - 事件名称模式过滤（可选）
   * 返回值：取消订阅的函数
   */
  onAny(listener: EventListener<{ name: string; data: any }>, pattern?: RegExp): () => void {
    const subscription: EventSubscription = {
      listener: (event) => {
        if (pattern && !pattern.test(event.name)) return;
        listener(event);
      },
      once: false,
      priority: 0,
      id: `wildcard_${++this._subscriptionIdCounter}`,
    };

    this._wildcardSubscriptions.push(subscription);

    return () => {
      const index = this._wildcardSubscriptions.indexOf(subscription);
      if (index !== -1) {
        this._wildcardSubscriptions.splice(index, 1);
      }
    };
  }

  /**
   * 函数级注释：移除所有事件订阅
   * 返回值：void
   */
  removeAllListeners(): void {
    this._subscriptions.clear();
    this._wildcardSubscriptions = [];
  }

  /**
   * 函数级注释：移除指定事件的所有订阅
   * 参数：
   *   eventName - 事件名称
   * 返回值：void
   */
  removeAllListenersFor(eventName: string): void {
    this._subscriptions.delete(eventName);
  }

  /**
   * 函数级注释：获取事件的监听器数量
   * 参数：
   *   eventName - 事件名称
   * 返回值：监听器数量
   */
  listenerCount(eventName: string): number {
    return this._subscriptions.get(eventName)?.length ?? 0;
  }

  /**
   * 函数级注释：获取所有事件名称
   * 返回值：事件名称列表
   */
  eventNames(): string[] {
    return Array.from(this._subscriptions.keys());
  }

  /**
   * 函数级注释：获取事件名称的命名空间
   * 参数：
   *   eventName - 事件名称
   * 返回值：命名空间数组
   *
   * @example
   * ```typescript
   * getNamespaces('chat:message:send') // ['chat', 'message', 'send']
   * ```
   */
  getNamespaces(eventName: string): string[] {
    return eventName.split(this._separator);
  }

  /**
   * 函数级注释：创建命名空间事件总线
   * 参数：
   *   namespace - 命名空间前缀
   * 返回值：命名空间事件总线
   *
   * @example
   * ```typescript
   * const chatBus = bus.createNamespace('chat');
   * chatBus.on('send', (data) => console.log(data)); // 实际事件名: 'chat:send'
   * ```
   */
  createNamespace(namespace: string): NamespacedEventBus {
    return new NamespacedEventBus(this, namespace);
  }

  /**
   * 函数级注释：执行通配符订阅（内部方法）
   * 参数：
   *   eventName - 事件名称
   *   eventData - 事件数据
   * 返回值：Promise<void>
   */
  private async _emitWildcard(eventName: string, eventData: any): Promise<void> {
    const toRemove: number[] = [];

    for (let i = 0; i < this._wildcardSubscriptions.length; i++) {
      const subscription = this._wildcardSubscriptions[i];
      try {
        const result = subscription.listener({ name: eventName, data: eventData });

        if (result instanceof Promise) {
          await result;
        }

        if (subscription.once) {
          toRemove.push(i);
        }
      } catch (error) {
        this._config.errorHandler(error as Error, { name: eventName, data: eventData }, subscription.listener);
      }
    }

    // 内部逻辑：从后往前删除，避免索引问题
    for (const index of toRemove.reverse()) {
      this._wildcardSubscriptions.splice(index, 1);
    }
  }

  /**
   * 函数级注释：默认错误处理器（内部方法）
   * 参数：
   *   error - 错误对象
   * 返回值：void
   */
  private _defaultErrorHandler(error: Error): void {
    console.error('[EventBus] 监听器执行失败:', error);
  }
}

/**
 * 类级注释：命名空间事件总线
 * 设计模式：装饰器模式 + 外观模式
 * 职责：为特定命名空间提供便捷的事件操作接口
 */
export class NamespacedEventBus {
  /** 内部变量：父事件总线 */
  private _bus: EventBus;

  /** 内部变量：命名空间前缀 */
  private _namespace: string;

  /**
   * 函数级注释：构造函数
   * 参数：
   *   bus - 父事件总线
   *   namespace - 命名空间前缀
   */
  constructor(bus: EventBus, namespace: string) {
    this._bus = bus;
    this._namespace = namespace;
  }

  /**
   * 函数级注释：订阅事件（自动添加命名空间前缀）
   * 参数：
   *   eventName - 事件名称（不需要命名空间前缀）
   *   listener - 监听器函数
   *   options - 订阅选项
   * 返回值：取消订阅的函数
   */
  on<TEvent = any>(
    eventName: string,
    listener: EventListener<TEvent>,
    options?: { once?: boolean; priority?: number }
  ): () => void {
    return this._bus.on(`${this._namespace}:${eventName}`, listener, options);
  }

  /**
   * 函数级注释：订阅一次性事件
   */
  once<TEvent = any>(eventName: string, listener: EventListener<TEvent>): () => void {
    return this._bus.once(`${this._namespace}:${eventName}`, listener);
  }

  /**
   * 函数级注释：取消订阅
   */
  off(eventName: string, subscriptionId?: string): void {
    this._bus.off(`${this._namespace}:${eventName}`, subscriptionId);
  }

  /**
   * 函数级注释：发布事件
   */
  async emit<TEvent = any>(eventName: string, eventData?: TEvent): Promise<void> {
    return this._bus.emit(`${this._namespace}:${eventName}`, eventData);
  }

  /**
   * 函数级注释：发布同步事件
   */
  emitSync<TEvent = any>(eventName: string, eventData?: TEvent): void {
    this._bus.emitSync(`${this._namespace}:${eventName}`, eventData);
  }

  /**
   * 函数级注释：获取父事件总线
   * 返回值：父事件总线实例
   */
  getBus(): EventBus {
    return this._bus;
  }
}

/**
 * 变量：全局默认事件总线
 * 内部逻辑：提供单例事件总线，方便直接使用
 */
export const globalEventBus = new EventBus();

/**
 * 类级注释：事件总线工具类
 * 内部逻辑：提供事件总线相关的辅助方法
 */
export class EventBusHelper {
  /**
   * 函数级注释：创建 React Hook 适配器
   * 参数：
   *   bus - 事件总线实例
   * 返回值：自定义 Hook
   *
   * @example
   * ```typescript
   * const useChatEvent = createEventBusHook(chatBus);
   *
   * function MyComponent() {
   *   const [message, setMessage] = useState('');
   *   useChatEvent('message', (data) => setMessage(data));
   *   return <div>{message}</div>;
   * }
   * ```
   */
  static createEventBusHook<TEventMap extends Record<string, any>>(
    bus: EventBus | NamespacedEventBus
  ) {
    return function useEventBus<TEventName extends keyof TEventMap & string>(
      eventName: TEventName,
      listener: (event: TEventMap[TEventName]) => void,
      deps: any[] = []
    ) {
      // 内部逻辑：使用 React 的副作用钩子订阅事件
      // 注意：这里只是类型定义，实际使用需要配合 React
      return { bus, eventName, listener };
    };
  }

  /**
   * 函数级注释：批量订阅事件
   * 参数：
   *   bus - 事件总线实例
   *   subscriptions - 订阅配置映射
   * 返回值：取消所有订阅的函数
   */
  static batchSubscribe<TEventMap extends Record<string, any>>(
    bus: EventBus,
    subscriptions: {
      [K in keyof TEventMap]: {
        event: K;
        listener: (event: TEventMap[K]) => void;
        options?: { once?: boolean; priority?: number };
      }
    }[keyof TEventMap][]
  ): () => void {
    const unsubscribers: (() => void)[] = [];

    for (const sub of subscriptions) {
      const unsubscribe = bus.on(sub.event as string, sub.listener, sub.options);
      unsubscribers.push(unsubscribe);
    }

    // 内部逻辑：返回批量取消订阅函数
    return () => {
      for (const unsubscribe of unsubscribers) {
        unsubscribe();
      }
    };
  }
}
