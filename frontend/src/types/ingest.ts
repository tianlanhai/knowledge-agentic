/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：文档导入相关类型定义
 */

export interface IngestResponse {
  document_id: number;
  status: string;
  chunk_count: number;
}

export interface DBIngestRequest {
  connection_uri: string;
  table_name: string;
  content_column: string;
  metadata_columns?: string[];
}

export interface URLIngestRequest {
  url: string;
  tags?: string[];
}

/**
 * 函数级注释：任务状态类型
 * 内部逻辑：定义任务状态的联合类型
 */
export type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed';

/**
 * 函数级注释：任务状态常量对象
 * 内部逻辑：提供任务状态的常量引用，便于代码中使用
 */
export const TaskStatus = {
  PENDING: 'pending' as const,
  PROCESSING: 'processing' as const,
  COMPLETED: 'completed' as const,
  FAILED: 'failed' as const
} as const;

export interface TaskResponse {
  id: number;
  file_name: string;
  status: TaskStatus;
  progress: number;
  error_message?: string;
  document_id?: number;
  created_at: string;
  updated_at: string;
}

export interface TaskListResponse {
  items: TaskResponse[];
  total: number;
}
