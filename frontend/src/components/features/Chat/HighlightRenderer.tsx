/**
 * 上海宇羲伏天智能科技有限公司出品
 */

import React from 'react';
import type { FormattingOptions } from '../../../types/chat';

/**
 * 文件级注释：高亮渲染器组件
 * 内部逻辑：专门处理内容高亮显示，使用同步渲染确保测试兼容性
 * 属性：
 *   content - 原始内容
 *   options - 高亮选项
 *   onHighlight - 高亮完成回调
 */
interface HighlightRendererProps {
  content: string;
  options?: FormattingOptions;
  onHighlight?: (highlightedContent: string) => void;
}

/**
 * 函数级注释：应用内容高亮
 * 内部逻辑：根据关键词对重要内容进行高亮显示
 * 参数：
 *   content - 原始文本内容
 *   keywords - 需要高亮的关键词列表
 * 返回值：高亮后的HTML内容
 */
const applyHighlighting = (content: string, keywords: string[]): string => {
  if (!keywords || keywords.length === 0) {
    return content;
  }

  try {
    // 内部逻辑：使用字符串替换进行简单高亮，避免在 happy-dom 中的 DOM 操作问题
    let result = content;
    keywords.forEach(keyword => {
      if (!keyword) return;
      // 内部逻辑：使用正则表达式直接替换
      const escapedKeyword = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const regex = new RegExp(`(${escapedKeyword})`, 'gi');
      result = result.replace(regex, '<mark class="highlight">$1</mark>');
    });
    return result;
  } catch (error) {
    console.warn('内容高亮失败:', error);
    return content;
  }
};

/**
 * 高亮渲染器组件
 * 内部变量：highlightedContent - 高亮后的内容
 * 内部逻辑：同步渲染高亮内容，避免异步操作导致的测试问题
 * 返回值：JSX.Element
 */
export const HighlightRenderer: React.FC<HighlightRendererProps> = ({
  content,
  options = {},
  onHighlight
}) => {
  // 内部变量：使用 useMemo 缓存高亮结果，避免重复计算
  const highlightedContent = React.useMemo(() => {
    return applyHighlighting(content, options.highlight_keywords || []);
  }, [content, options.highlight_keywords]);

  // 内部逻辑：调用回调函数通知高亮完成
  React.useEffect(() => {
    onHighlight?.(highlightedContent);
  }, [highlightedContent, onHighlight]);

  return (
    <div className="highlight-renderer">
      <div
        className="highlighted-content"
        dangerouslySetInnerHTML={{ __html: highlightedContent }}
      />
    </div>
  );
};

/**
 * 高亮选项
 * 内部变量：高亮配置
 */
export const highlightOptions: FormattingOptions = {
  enable_markdown: false,
  enable_structured: false,
  highlight_keywords: ['重要', '关键', '注意', '核心', '重点', '必须', '建议', '警告', '错误', '成功', '失败'],
  max_content_length: 5000,
  highlight_style: 'background',
  case_sensitive: false,
  whole_word: false,
};
