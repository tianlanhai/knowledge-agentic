/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：Store 中介者模式
 * 内部逻辑：协调多个 Store 之间的通信，解耦 Store 之间的直接依赖
 * 设计模式：中介者模式、观察者模式
 * 设计原则：迪米特法则、单一职责原则
 *
 * 问题背景：
 *   - chatStore 直接依赖 messageStore，通过 useMessageStore.getState() 获取状态
 *   - conversationStore 和 chatStore 有重复的消息管理逻辑
 *   - Store 之间缺乏统一的通信机制
 *
 * 解决方案：
 *   - 使用中介者模式管理 Store 之间的通信
 *   - 使用事件总线实现发布-订阅机制
 *   - 提供统一的 Store 注册和通知接口
 */

/**
 * 类型：Store 事件类型
 */
export enum StoreEventType {
  /** 消息添加 */
  MESSAGE_ADDED = 'message:added',
  /** 消息更新 */
  MESSAGE_UPDATED = 'message:updated',
  /** 消息清空 */
  MESSAGE_CLEARED = 'message:cleared',
  /** 流式状态变化 */
  STREAMING_CHANGED = 'streaming:changed',
  /** 来源更新 */
  SOURCES_UPDATED = 'sources:updated',
  /** 会话切换 */
  CONVERSATION_CHANGED = 'conversation:changed',
  /** 聊天状态变化 */
  CHAT_STATE_CHANGED = 'chat_state:changed',
  /** 错误发生 */
  ERROR_OCCURRED = 'error:occurred',
}

/**
 * 类型：Store 事件数据
 */
export interface StoreEventData {
  /** 事件类型 */
  type: StoreEventType;
  /** 事件源 Store 名称 */
  source: string;
  /** 事件数据 */
  data?: any;
  /** 时间戳 */
  timestamp: number;
}

/**
 * 类型：事件监听器
 */
type EventListener = (event: StoreEventData) => void | Promise<void>;

/**
 * 类型：Store 实例接口
 */
export interface StoreInstance {
  /** Store 名称 */
  name: string;
  /** Store 状态 */
  getState: () => any;
  /** 订阅事件（可选，Zustand 支持） */
  subscribe?: (listener: (state: any) => void) => () => void;
  /** 处理事件的方法 */
  onEvent?: (fromStore: string, event: StoreEventData) => void | Promise<void>;
}

/**
 * 类：Store 中介者
 * 设计模式：中介者模式 - 管理 Store 之间的通信
 * 职责：
 *   1. 注册和管理 Store 实例
 *   2. 广播事件到所有 Store
 *   3. 提供事件订阅机制
 *   4. 维护事件历史（用于调试）
 */
export class StoreMediator {
  /** 内部变量：注册的 Store 映射 */
  private stores: Map<string, StoreInstance> = new Map();

  /** 内部变量：事件监听器映射 */
  private listeners: Map<StoreEventType, Set<EventListener>> = new Map();

  /** 内部变量：事件历史（最多保存 100 条） */
  private eventHistory: StoreEventData[] = [];

  /** 内部变量：最大历史记录数 */
  private readonly maxHistorySize = 100;

  /** 内部变量：是否启用调试日志 */
  private debugEnabled = false;

  /**
   * 函数级注释：注册 Store
   * 参数：store - Store 实例
   */
  registerStore(store: StoreInstance): void {
    if (this.stores.has(store.name)) {
      console.warn(`[StoreMediator] Store "${store.name}" 已存在，将被覆盖`);
    }

    this.stores.set(store.name, store);
    this.log('debug', `Store "${store.name}" 已注册`);

    // 内部逻辑：如果 Store 有 subscribe 方法，自动监听状态变化
    if (store.subscribe) {
      store.subscribe((state) => {
        // 内部逻辑：状态变化时通知其他 Store
        this.notifyStores(store.name, {
          type: StoreEventType.CHAT_STATE_CHANGED,
          source: store.name,
          data: state,
          timestamp: Date.now(),
        });
      });
    }
  }

  /**
   * 函数级注释：注销 Store
   * 参数：name - Store 名称
   */
  unregisterStore(name: string): void {
    const removed = this.stores.delete(name);
    if (removed) {
      this.log('debug', `Store "${name}" 已注销`);
    }
  }

  /**
   * 函数级注释：获取 Store
   * 参数：name - Store 名称
   * 返回值：Store 实例或 undefined
   */
  getStore<T extends StoreInstance>(name: string): T | undefined {
    return this.stores.get(name) as T;
  }

  /**
   * 函数级注释：广播事件到所有 Store
   * 参数：event - 事件数据
   */
  broadcast(event: StoreEventData): void {
    this.addToHistory(event);
    this.notifyStores('*', event);
  }

  /**
   * 函数级注释：发送事件到指定 Store
   * 参数：targetStoreName - 目标 Store 名称，event - 事件数据
   */
  sendTo(targetStoreName: string, event: StoreEventData): void {
    const targetStore = this.stores.get(targetStoreName);
    if (!targetStore) {
      this.log('warn', `目标 Store "${targetStoreName}" 不存在`);
      return;
    }

    this.addToHistory(event);

    // 内部逻辑：调用目标 Store 的 onEvent 方法
    if (targetStore.onEvent) {
      try {
        targetStore.onEvent(event.source, event);
      } catch (error) {
        this.log('error', `Store "${targetStoreName}" 处理事件时出错:`, error);
      }
    }
  }

  /**
   * 函数级注释：通知所有 Store（除了来源 Store）
   * 参数：sourceStoreName - 来源 Store 名称，event - 事件数据
   */
  private notifyStores(sourceStoreName: string, event: StoreEventData): void {
    for (const [name, store] of this.stores.entries()) {
      // 内部逻辑：跳过来源 Store 和广播通配符
      if (name === sourceStoreName || sourceStoreName === '*') {
        continue;
      }

      // 内部逻辑：调用 Store 的 onEvent 方法
      if (store.onEvent) {
        try {
          store.onEvent(sourceStoreName, event);
        } catch (error) {
          this.log('error', `Store "${name}" 处理事件时出错:`, error);
        }
      }
    }

    // 内部逻辑：触发全局监听器
    this.triggerListeners(event);
  }

  /**
   * 函数级注释：订阅事件
   * 参数：eventType - 事件类型，listener - 监听器函数
   * 返回值：取消订阅的函数
   */
  subscribe(eventType: StoreEventType, listener: EventListener): () => void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }

    this.listeners.get(eventType)!.add(listener);
    this.log('debug', `监听器已订阅事件 "${eventType}"`);

    // 内部逻辑：返回取消订阅函数
    return () => {
      const listeners = this.listeners.get(eventType);
      if (listeners) {
        listeners.delete(listener);
        this.log('debug', `监听器已取消订阅事件 "${eventType}"`);
      }
    };
  }

  /**
   * 函数级注释：触发事件监听器
   * 参数：event - 事件数据
   */
  private triggerListeners(event: StoreEventData): void {
    const listeners = this.listeners.get(event.type);
    if (listeners) {
      for (const listener of listeners) {
        try {
          listener(event);
        } catch (error) {
          this.log('error', `事件监听器出错 (${event.type}):`, error);
        }
      }
    }
  }

  /**
   * 函数级注释：添加事件到历史记录
   * 参数：event - 事件数据
   */
  private addToHistory(event: StoreEventData): void {
    this.eventHistory.push(event);

    // 内部逻辑：限制历史记录大小
    if (this.eventHistory.length > this.maxHistorySize) {
      this.eventHistory.shift();
    }
  }

  /**
   * 函数级注释：获取事件历史
   * 参数：limit - 最大返回条数，source - 过滤来源 Store，type - 过滤事件类型
   * 返回值：事件历史数组
   */
  getHistory(limit: number = 50, source?: string, type?: StoreEventType): StoreEventData[] {
    let history = [...this.eventHistory];

    // 内部逻辑：按来源过滤
    if (source) {
      history = history.filter(e => e.source === source);
    }

    // 内部逻辑：按类型过滤
    if (type) {
      history = history.filter(e => e.type === type);
    }

    // 内部逻辑：按时间倒序，限制条数
    return history.reverse().slice(0, limit);
  }

  /**
   * 函数级注释：清除事件历史
   */
  clearHistory(): void {
    this.eventHistory = [];
  }

  /**
   * 函数级注释：启用调试日志
   * 参数：enabled - 是否启用
   */
  setDebug(enabled: boolean): void {
    this.debugEnabled = enabled;
  }

  /**
   * 函数级注释：记录日志
   * 参数：level - 日志级别，message - 日志消息，data - 附加数据
   */
  private log(level: 'debug' | 'info' | 'warn' | 'error', message: string, data?: any): void {
    if (!this.debugEnabled && level === 'debug') {
      return;
    }

    const timestamp = new Date().toISOString();
    const prefix = `[StoreMediator ${timestamp}]`;

    switch (level) {
      case 'debug':
        console.debug(prefix, message, data ?? '');
        break;
      case 'info':
        console.info(prefix, message, data ?? '');
        break;
      case 'warn':
        console.warn(prefix, message, data ?? '');
        break;
      case 'error':
        console.error(prefix, message, data ?? '');
        break;
    }
  }

  /**
   * 函数级注释：获取中介者状态
   * 返回值：状态信息对象
   */
  getStatus() {
    return {
      registeredStores: Array.from(this.stores.keys()),
      listenerCount: Array.from(this.listeners.entries()).map(([type, listeners]) => ({
        type,
        count: listeners.size,
      })),
      eventHistorySize: this.eventHistory.length,
      debugEnabled: this.debugEnabled,
    };
  }

  /**
   * 函数级注释：清空所有状态
   */
  clear(): void {
    this.stores.clear();
    this.listeners.clear();
    this.eventHistory = [];
    this.log('info', '中介者已清空');
  }
}

/**
 * 变量：全局 Store 中介者单例
 */
export const storeMediator = new StoreMediator();

/**
 * 类：增强的 Store 基类
 * 设计模式：模板方法模式
 * 职责：提供 Store 与中介者集成的基类
 */
export abstract class MediatedStore {
  /**
   * 函数级注释：获取 Store 名称（子类实现）
   * 返回值：Store 名称
   */
  protected abstract getStoreName(): string;

  /**
   * 函数级注释：初始化时自动注册到中介者
   */
  constructor() {
    // 内部逻辑：将当前实例注册到中介者
    storeMediator.registerStore({
      name: this.getStoreName(),
      getState: () => this.getState(),
      onEvent: this.handleEvent.bind(this),
    });
  }

  /**
   * 函数级注释：获取 Store 状态（子类实现）
   * 返回值：当前状态
   */
  protected abstract getState(): any;

  /**
   * 函数级注释：处理来自其他 Store 的事件（子类可覆盖）
   * 参数：fromStore - 来源 Store 名称，event - 事件数据
   */
  protected handleEvent(fromStore: string, event: StoreEventData): void {
    // 默认实现：子类可覆盖
  }

  /**
   * 函数级注释：广播事件
   * 参数：type - 事件类型，data - 事件数据
   */
  protected broadcast(type: StoreEventType, data?: any): void {
    storeMediator.broadcast({
      type,
      source: this.getStoreName(),
      data,
      timestamp: Date.now(),
    });
  }

  /**
   * 函数级注释：发送事件到指定 Store
   * 参数：targetStore - 目标 Store 名称，type - 事件类型，data - 事件数据
   */
  protected sendTo(targetStore: string, type: StoreEventType, data?: any): void {
    storeMediator.sendTo(targetStore, {
      type,
      source: this.getStoreName(),
      data,
      timestamp: Date.now(),
    });
  }

  /**
   * 函数级注释：订阅事件
   * 参数：eventType - 事件类型，listener - 监听器函数
   * 返回值：取消订阅的函数
   */
  protected subscribe(eventType: StoreEventType, listener: EventListener): () => void {
    return storeMediator.subscribe(eventType, listener);
  }
}

// 导出快捷函数
/**
 * 快捷函数：注册 Store 到中介者
 * 参数：store - Store 实例
 */
export const registerStore = (store: StoreInstance): void => {
  storeMediator.registerStore(store);
};

/**
 * 快捷函数：发送事件
 * 参数：source - 来源 Store 名称，type - 事件类型，data - 事件数据
 */
export const emitEvent = (source: string, type: StoreEventType, data?: any): void => {
  storeMediator.broadcast({
    type,
    source,
    data,
    timestamp: Date.now(),
  });
};

/**
 * 快捷函数：订阅事件
 * 参数：eventType - 事件类型，listener - 监听器函数
 * 返回值：取消订阅的函数
 */
export const onEvent = (eventType: StoreEventType, listener: EventListener): () => void => {
  return storeMediator.subscribe(eventType, listener);
};

// StoreInstance 和 StoreEventData 已在上方使用 export interface 导出，此处不再重复导出
export { type EventListener };
