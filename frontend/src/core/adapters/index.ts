/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：适配器模块入口
 * 内部逻辑：导出所有适配器
 */

export { ChatServiceAdapter, chatAdapter } from './ChatAdapter';
export type {
  IChatServicePort,
  StreamCallbacks,
  ChatRequest as ChatAdapterRequest,
  ChatResponse as ChatAdapterResponse,
} from './ChatAdapter';
