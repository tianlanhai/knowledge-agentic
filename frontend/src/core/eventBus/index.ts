/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：事件总线模块导出文件
 * 内部逻辑：统一导出所有事件总线相关的类型和函数
 */

// 导出核心类
export {
  EventBus,
  NamespacedEventBus,
  globalEventBus,
  EventBusHelper,
} from './EventBus';

// 导出类型定义
export type {
  EventListener,
  EventSubscription,
  EventBusConfig,
} from './EventBus';

// 导出 React Hook
export {
  useEventBus,
  useSubscribe,
  useSubscribeOnce,
  useEventEmitter,
  useNamespaceEventBus,
  useSubscribeMultiple,
} from './useEventBus';
