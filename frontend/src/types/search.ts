/**
 * 上海宇羲伏天智能科技有限公司出品
 *
/**
 * 文件级注释：语义搜索相关类型定义
 */

/**
 * 搜索结果接口
 * 属性说明：
 *   doc_id: 文档 ID
 *   file_name: 文件名（可能为空）
 *   source_type: 来源类型（FILE/WEB/DB，可能为空）
 *   content: 匹配的文本内容
 *   score: 相关度评分
 */
export interface SearchResult {
  doc_id: number;
  file_name?: string | null;
  source_type?: string | null;
  content: string;
  score: number;
}
