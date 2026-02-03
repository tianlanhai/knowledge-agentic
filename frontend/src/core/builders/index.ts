/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：建造者模块导出文件
 * 内部逻辑：统一导出所有建造者相关的类型和类
 */

// 导出聊天消息建造者
export {
  ChatMessageBuilder,
  ChatRequestBuilder,
  SearchQueryBuilder,
} from './ChatMessageBuilder';

// 导出类型定义
export type {
  MessageRole,
  ChatMessage,
  ToolCall,
  BuildResult,
} from './ChatMessageBuilder';
