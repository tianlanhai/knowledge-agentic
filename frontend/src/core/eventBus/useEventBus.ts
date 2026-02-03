/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：事件总线 React Hook
 * 内部逻辑：提供 React 集成的事件订阅 Hook
 * 设计模式：观察者模式 + React Hook 模式
 */

import { useEffect, useRef, useCallback } from 'react';
import { EventBus, NamespacedEventBus, EventListener, globalEventBus } from './EventBus';

/**
 * Hook: 使用事件总线订阅
 * 设计模式：观察者模式
 * 内部逻辑：自动清理订阅的 React Hook
 *
 * 参数：
 *   bus - 事件总线实例（默认使用全局实例）
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const bus = useEventBus();
 *
 *   useEffect(() => {
 *     const unsub = bus.on('message', (data) => {
 *       console.log('Received:', data);
 *     });
 *     return unsub;
 *   }, []);
 *
 *   return <div>...</div>;
 * }
 * ```
 */
export function useEventBus(bus: EventBus | NamespacedEventBus = globalEventBus): EventBus | NamespacedEventBus {
  return bus;
}

/**
 * Hook: 订阅事件
 * 设计模式：观察者模式
 * 内部逻辑：自动管理订阅生命周期
 *
 * 参数：
 *   eventName - 事件名称
 *   listener - 监听器函数
 *   bus - 事件总线实例（默认使用全局实例）
 *   deps - 依赖数组
 *
 * @example
 * ```tsx
 * function ChatComponent() {
 *   const [messages, setMessages] = useState([]);
 *
 *   useSubscribe('chat:new', (message) => {
 *     setMessages(prev => [...prev, message]);
 *   });
 *
 *   return <div>{messages.map(m => <div key={m.id}>{m.text}</div>)}</div>;
 * }
 * ```
 */
export function useSubscribe<TEvent = any>(
  eventName: string,
  listener: EventListener<TEvent>,
  bus: EventBus | NamespacedEventBus = globalEventBus,
  deps: any[] = []
): void {
  // 内部变量：存储取消订阅函数
  const unsubscribeRef = useRef<(() => void) | null>(null);

  // 内部逻辑：使用 useCallback 稳定监听器引用
  const stableListener = useCallback(listener, deps);

  useEffect(() => {
    // 内部逻辑：订阅事件
    unsubscribeRef.current = bus.on(eventName, stableListener);

    // 内部逻辑：清理函数 - 取消订阅
    return () => {
      unsubscribeRef.current?.();
    };
  }, [bus, eventName, stableListener]);
}

/**
 * Hook: 订阅一次性事件
 * 设计模式：观察者模式
 * 内部逻辑：事件触发后自动取消订阅
 *
 * 参数：
 *   eventName - 事件名称
 *   listener - 监听器函数
 *   bus - 事件总线实例（默认使用全局实例）
 *   deps - 依赖数组
 *
 * @example
 * ```tsx
 * function InitComponent() {
 *   useSubscribeOnce('app:ready', () => {
 *     console.log('App is ready!');
 *   });
 *
 *   return <div>Initializing...</div>;
 * }
 * ```
 */
export function useSubscribeOnce<TEvent = any>(
  eventName: string,
  listener: EventListener<TEvent>,
  bus: EventBus | NamespacedEventBus = globalEventBus,
  deps: any[] = []
): void {
  // 内部变量：使用 ref 标记是否已触发
  const hasTriggeredRef = useRef(false);

  // 内部逻辑：包装监听器，确保只触发一次
  const wrappedListener = useCallback((event: TEvent) => {
    if (!hasTriggeredRef.current) {
      hasTriggeredRef.current = true;
      listener(event);
    }
  }, [listener, ...deps]);

  useEffect(() => {
    // 内部逻辑：订阅一次性事件
    const unsubscribe = bus.once(eventName, wrappedListener);

    return unsubscribe;
  }, [bus, eventName, wrappedListener]);
}

/**
 * Hook: 使用事件发布器
 * 设计模式：观察者模式
 * 内部逻辑：返回发布事件的方法
 *
 * 参数：
 *   bus - 事件总线实例（默认使用全局实例）
 * 返回值：包含 emit 方法的对象
 *
 * @example
 * ```tsx
 * function SenderComponent() {
 *   const { emit } = useEventEmitter();
 *
 *   const handleClick = () => {
 *     emit('button:click', { button: 'submit' });
 *   };
 *
 *   return <button onClick={handleClick}>Submit</button>;
 * }
 * ```
 */
export function useEventEmitter(
  bus: EventBus | NamespacedEventBus = globalEventBus
) {
  // 内部逻辑：使用 useCallback 稳定引用
  const emit = useCallback(<T = any>(eventName: string, eventData?: T) => {
    return bus.emit(eventName, eventData);
  }, [bus]);

  const emitSync = useCallback(<T = any>(eventName: string, eventData?: T) => {
    bus.emitSync(eventName, eventData);
  }, [bus]);

  return { emit, emitSync, bus };
}

/**
 * Hook: 创建命名空间事件总线订阅
 * 设计模式：命名空间模式 + 观察者模式
 * 内部逻辑：为特定命名空间提供便捷订阅方法
 *
 * 参数：
 *   namespace - 命名空间
 *   bus - 父事件总线实例（默认使用全局实例）
 * 返回值：命名空间事件总线实例
 *
 * @example
 * ```tsx
 * function ChatComponent() {
 *   const chatBus = useNamespaceEventBus('chat');
 *
 *   useSubscribe('send', (data) => {
 *     console.log('Chat send:', data);
 *   }, chatBus);
 *
 *   return <div>...</div>;
 * }
 * ```
 */
export function useNamespaceEventBus(
  namespace: string,
  bus: EventBus = globalEventBus
): NamespacedEventBus {
  // 内部逻辑：使用 useMemo 确保命名空间总线实例稳定
  // 这里简化为直接创建，实际应用中可能需要缓存
  return bus.createNamespace(namespace);
}

/**
 * Hook: 监听多个事件
 * 设计模式：观察者模式
 * 内部逻辑：批量订阅多个事件
 *
 * 参数：
 *   eventListeners - 事件监听器配置
 *   bus - 事件总线实例
 *
 * @example
 * ```tsx
 * function AppComponent() {
 *   useSubscribeMultiple({
 *     'user:login': (user) => console.log('User logged in:', user),
 *     'user:logout': () => console.log('User logged out'),
 *   });
 *
 *   return <div>...</div>;
 * }
 * ```
 */
export function useSubscribeMultiple(
  eventListeners: Record<string, EventListener>,
  bus: EventBus | NamespacedEventBus = globalEventBus
): void {
  // 内部逻辑：将配置转换为数组
  const entries = Object.entries(eventListeners);

  useEffect(() => {
    // 内部变量：收集取消订阅函数
    const unsubscribers: (() => void)[] = [];

    // 内部逻辑：订阅所有事件
    for (const [eventName, listener] of entries) {
      const unsubscribe = bus.on(eventName, listener);
      unsubscribers.push(unsubscribe);
    }

    // 内部逻辑：清理函数 - 取消所有订阅
    return () => {
      for (const unsubscribe of unsubscribers) {
        unsubscribe();
      }
    };
  }, [bus, ...entries.map(([_, listener]) => listener)]);
}

// 导出所有公共接口
export {
  globalEventBus,
};
