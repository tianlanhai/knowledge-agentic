/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：状态机模块导出文件
 * 内部逻辑：统一导出所有状态机相关的类型和类
 */

// 导出泛型状态机
export {
  StateMachine,
  StateMachineHelper
} from './StateMachine';

// 导出类型定义
export type {
  Transition,
  StateConfig,
  StateChangeEvent
} from './StateMachine';

// 导出聊天状态机
export {
  ChatStateMachine,
  ChatStateMachineFactory,
  ChatStateMachineHookHelper
} from './ChatStateMachine';

// 导出聊天相关类型
export type {
  ChatState,
  ChatEvent,
  ChatStateContext
} from './ChatStateMachine';
