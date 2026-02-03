/**
 * 上海宇羲伏天智能科技有限公司出品
 *
/**
 * 文件级注释：文档类型定义
 * 内部逻辑：定义文档相关的TypeScript类型，确保类型安全
 */

/**
 * 接口级注释：文档数据模型
 * 属性：
 *   id: 文档唯一标识
 *   file_name: 文件名或网页标题
 *   source_type: 来源类型(file/url/db)
 *   tags: 标签列表
 *   created_at: 创建时间
 *   chunk_count: 切分出的片段数量
 */
export interface Document {
  id: number;
  file_name: string;
  source_type: string;
  tags: string[];
  created_at: string;
  chunk_count?: number;
}

/**
 * 接口级注释：文档列表响应模型
 * 属性：
 *   items: 文档对象列表
 *   total: 总记录数
 *   skip: 跳过数量
 *   limit: 返回限制
 */
export interface DocumentListResponse {
  items: Document[];
  total: number;
  skip: number;
  limit: number;
}
