/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：事件总线工具模块
 * 内部逻辑：实现发布-订阅模式，用于组件间解耦通信
 * 设计模式：观察者模式（发布-订阅模式）
 * 设计原则：SOLID - 单一职责原则、开闭原则
 */

/**
 * 内部类型：事件回调函数类型
 */
type EventCallback = (...args: any[]) => void;

/**
 * 内部类型：事件取消订阅函数类型
 */
type UnsubscribeFunction = () => void;

/**
 * 内部类型：事件监听器包装（包含一次性标志）
 */
interface EventListener {
  callback: EventCallback;
  once: boolean;
}

/**
 * 类级注释：事件总线类
 * 设计模式：发布-订阅模式（观察者模式）
 * 职责：
 *   1. 管理事件的订阅和取消订阅
 *   2. 触发事件并通知所有订阅者
 *   3. 支持一次性订阅
 *
 * 设计优势：
 *   - 组件间松耦合通信
 *   - 支持跨层级组件通信
 *   - 避免props drilling
 */
class EventBus {
  /**
   * 内部变量：事件名称到监听器列表的映射
   * 格式：Map<事件名称, Set<监听器包装>>
   */
  private events: Map<string, Set<EventListener>> = new Map();

  /**
   * 内部变量：是否启用调试日志
   */
  private debugMode: boolean = false;

  /**
   * 函数级注释：订阅事件
   * 内部逻辑：获取事件监听器集合 -> 添加监听器 -> 返回取消订阅函数
   *
   * @param event - 事件名称
   * @param callback - 事件回调函数
   * @param once - 是否为一次性订阅（默认false）
   * @returns 取消订阅函数
   */
  on(event: string, callback: EventCallback, once: boolean = false): UnsubscribeFunction {
    // 内部逻辑：获取或创建事件监听器集合
    if (!this.events.has(event)) {
      this.events.set(event, new Set());
    }
    const listeners = this.events.get(event)!;

    // 内部逻辑：创建监听器包装
    const listener: EventListener = { callback, once };
    listeners.add(listener);

    if (this.debugMode) {
      console.log(`[EventBus] 订阅事件: ${event}, 当前监听器数量: ${listeners.size}`);
    }

    // 内部逻辑：返回取消订阅函数
    return () => this.off(event, callback);
  }

  /**
   * 函数级注释：订阅一次性事件
   * 内部逻辑：事件触发后自动取消订阅
   *
   * @param event - 事件名称
   * @param callback - 事件回调函数
   * @returns 取消订阅函数
   */
  once(event: string, callback: EventCallback): UnsubscribeFunction {
    return this.on(event, callback, true);
  }

  /**
   * 函数级注释：取消订阅事件
   * 内部逻辑：查找并移除指定的监听器
   *
   * @param event - 事件名称
   * @param callback - 要取消的回调函数（可选，不传则移除所有）
   */
  off(event: string, callback?: EventCallback): void {
    const listeners = this.events.get(event);

    // Guard Clauses：事件不存在或无监听器
    if (!listeners || listeners.size === 0) {
      return;
    }

    // 内部逻辑：移除指定的回调
    if (callback) {
      for (const listener of listeners) {
        if (listener.callback === callback) {
          listeners.delete(listener);
          break;
        }
      }
    } else {
      // 内部逻辑：移除所有监听器
      listeners.clear();
    }

    if (this.debugMode) {
      console.log(`[EventBus] 取消订阅事件: ${event}, 剩余监听器数量: ${listeners.size}`);
    }

    // 内部逻辑：如果没有监听器了，删除事件
    if (listeners.size === 0) {
      this.events.delete(event);
    }
  }

  /**
   * 函数级注释：触发事件
   * 内部逻辑：获取监听器列表 -> 遍历执行回调 -> 处理一次性监听器
   *
   * @param event - 事件名称
   * @param args - 传递给回调函数的参数
   */
  emit(event: string, ...args: any[]): void {
    const listeners = this.events.get(event);

    // Guard Clauses：没有监听器
    if (!listeners || listeners.size === 0) {
      if (this.debugMode) {
        console.log(`[EventBus] 触发事件: ${event}, 无监听器`);
      }
      return;
    }

    if (this.debugMode) {
      console.log(`[EventBus] 触发事件: ${event}, 监听器数量: ${listeners.size}`, args);
    }

    // 内部逻辑：收集需要移除的一次性监听器
    const toRemove: EventListener[] = [];

    // 内部逻辑：执行所有回调
    for (const listener of listeners) {
      try {
        listener.callback(...args);
        // 内部逻辑：标记一次性监听器待移除
        if (listener.once) {
          toRemove.push(listener);
        }
      } catch (error) {
        console.error(`[EventBus] 事件回调执行错误: ${event}`, error);
      }
    }

    // 内部逻辑：移除一次性监听器
    for (const listener of toRemove) {
      listeners.delete(listener);
    }

    // 内部逻辑：如果没有监听器了，删除事件
    if (listeners.size === 0) {
      this.events.delete(event);
    }
  }

  /**
   * 函数级注释：清除所有事件监听器
   * 内部逻辑：清空事件映射表
   */
  clear(): void {
    this.events.clear();
    if (this.debugMode) {
      console.log('[EventBus] 已清除所有事件监听器');
    }
  }

  /**
   * 函数级注释：获取事件的监听器数量
   *
   * @param event - 事件名称
   * @returns 监听器数量
   */
  listenerCount(event: string): number {
    const listeners = this.events.get(event);
    return listeners ? listeners.size : 0;
  }

  /**
   * 函数级注释：获取所有事件名称
   *
   * @returns 事件名称数组
   */
  eventNames(): string[] {
    return Array.from(this.events.keys());
  }

  /**
   * 函数级注释：启用或禁用调试日志
   *
   * @param enabled - 是否启用调试
   */
  setDebugMode(enabled: boolean): void {
    this.debugMode = enabled;
  }

  /**
   * 函数级注释：异步等待事件
   * 内部逻辑：返回一个Promise，当事件触发时resolve
   *
   * @param event - 事件名称
   * @param timeout - 超时时间（毫秒），不传则不超时
   * @returns Promise，resolve时返回事件参数
   */
  async waitFor<T = any>(event: string, timeout?: number): Promise<T[]> {
    return new Promise((resolve, reject) => {
      // 内部逻辑：设置超时
      let timer: number | undefined;
      if (timeout) {
        timer = setTimeout(() => {
          this.off(event, callback);
          reject(new Error(`等待事件超时: ${event}`));
        }, timeout);
      }

      // 内部逻辑：订阅事件
      const callback = (...args: T[]) => {
        if (timer) clearTimeout(timer);
        resolve(args);
      };

      this.once(event, callback);
    });
  }
}

/**
 * 内部变量：全局事件总线单例
 */
export const eventBus = new EventBus();

/**
 * 内部变量：预定义的事件名称常量
 * 用于避免硬编码事件名称，提供类型安全
 */
export const AppEvents = {
  // 配置相关事件
  CONFIG_CHANGED: 'config:changed',
  CONFIG_RELOADED: 'config:reloaded',

  // 聊天相关事件
  CHAT_MESSAGE_SENT: 'chat:message_sent',
  CHAT_MESSAGE_RECEIVED: 'chat:message_received',
  CHAT_STREAMING_START: 'chat:streaming_start',
  CHAT_STREAMING_END: 'chat:streaming_end',
  CHAT_ERROR: 'chat:error',

  // 文档相关事件
  DOCUMENT_UPLOADED: 'document:uploaded',
  DOCUMENT_DELETED: 'document:deleted',
  DOCUMENT_PROCESSING: 'document:processing',
  DOCUMENT_PROCESSED: 'document:processed',

  // 会话相关事件
  CONVERSATION_CREATED: 'conversation:created',
  CONVERSATION_DELETED: 'conversation:deleted',
  CONVERSATION_SWITCHED: 'conversation:switched',

  // 用户相关事件
  USER_LOGIN: 'user:login',
  USER_LOGOUT: 'user:logout',

  // 系统相关事件
  SYSTEM_ERROR: 'system:error',
  SYSTEM_READY: 'system:ready',
} as const;

/**
 * 导出类型
 */
export type { EventCallback, UnsubscribeFunction };
export default EventBus;
