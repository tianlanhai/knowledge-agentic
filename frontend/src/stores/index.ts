/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：Store 统一导出模块
 * 内部逻辑：统一导出所有 Zustand stores，提供清晰的访问入口
 * 设计原则：单一职责原则、DRY
 *
 * 说明：此文件仅作为统一导出入口，不创建额外的组合 store
 *       推荐直接使用各功能模块的独立 store，以获得更好的类型提示和性能
 */

// ============================================================================
// 导出类型定义
// ============================================================================
export type { ChatState } from './chatStore';
export type { UIState, Theme } from './uiStore';
export type { TaskState } from './taskStore';
export type { ConversationState } from './conversationStore';
export type { DocumentState } from './documentStore';
export type { HistoryState } from './historyStore';

// ============================================================================
// 导出各功能模块的独立 Store（推荐使用）
// ============================================================================
/**
 * 聊天状态管理
 * 用途：管理聊天消息、来源引用、流式输出状态
 */
export { useChatStore } from './chatStore';

/**
 * 对话管理
 * 用途：管理对话列表、当前选中对话
 */
export { useConversationStore } from './conversationStore';

/**
 * 文档管理
 * 用途：管理知识库文档列表、分页、加载状态
 */
export { useDocumentStore } from './documentStore';

/**
 * 任务管理
 * 用途：管理文档导入任务的进度和状态
 */
export { useTaskStore } from './taskStore';

/**
 * UI 状态管理
 * 用途：管理主题、侧边栏状态等 UI 相关状态
 */
export { useUIStore } from './uiStore';

/**
 * 历史记录管理
 * 用途：管理对话历史记录
 */
export { useHistoryStore } from './historyStore';
