/**
 * 上海宇羲伏天智能科技有限公司出品
 */

import React from 'react';
import type { FormattingOptions } from '../../../types/chat';

/**
 * 文件级注释：结构化内容组件
 * 内部逻辑：专门处理结构化内容的展示，使用同步渲染确保测试兼容性
 * 属性：
 *   content - 结构化内容
 *   options - 展示选项
 *   onDisplay - 展示完成回调
 */
interface StructuredContentProps {
  content: string;
  options?: FormattingOptions;
  onDisplay?: (displayedContent: string) => void;
}

/**
 * 函数级注释：格式化结构化内容
 * 内部逻辑：识别并格式化表格、列表、引用等结构化内容
 * 参数：content - 原始文本内容
 * 返回值：格式化后的HTML内容
 */
const formatStructuredContent = (content: string): string => {
  try {
    // 内部逻辑：检查 DOMParser 是否可用（在 happy-dom 中可能不可用）
    if (typeof DOMParser === 'undefined' || !DOMParser) {
      console.warn('DOMParser 不可用，返回原始内容');
      return content;
    }

    // 内部逻辑：使用DOMParser解析HTML
    const parser = new DOMParser();
    const doc = parser.parseFromString(content, 'text/html');

    // 内部逻辑：检查是否能够成功解析（happy-dom 可能返回空结果）
    if (!doc || !doc.body) {
      return content;
    }

    // 处理表格
    const tables = doc.querySelectorAll('table');
    tables.forEach(table => {
      try {
        table.classList.add('table', 'table-bordered', 'table-striped', 'structured-table');
        const caption = table.querySelector('caption');
        if (caption) {
          caption.classList.add('table-caption');
        }
      } catch (e) {
        // 跳过无法处理的表格
      }
    });

    // 处理列表
    const lists = doc.querySelectorAll('ul, ol');
    lists.forEach(lst => {
      try {
        lst.classList.add('list-group', 'structured-list');
        const items = lst.querySelectorAll('li');
        items.forEach(item => {
          item.classList.add('list-group-item', 'structured-list-item');
        });
      } catch (e) {
        // 跳过无法处理的列表
      }
    });

    // 处理引用块
    const blockquotes = doc.querySelectorAll('blockquote');
    blockquotes.forEach(blockquote => {
      try {
        blockquote.classList.add('blockquote', 'structured-blockquote');
        const cite = blockquote.querySelector('cite');
        if (cite) {
          cite.classList.add('blockquote-footer');
        }
      } catch (e) {
        // 跳过无法处理的引用块
      }
    });

    // 处理代码块
    const codeBlocks = doc.querySelectorAll('pre code');
    codeBlocks.forEach(code => {
      try {
        code.classList.add('structured-code');
        const pre = code.parentElement;
        if (pre) {
          pre.classList.add('structured-code-block');
        }
      } catch (e) {
        // 跳过无法处理的代码块
      }
    });

    // 处理标题
    const headings = doc.querySelectorAll('h1, h2, h3, h4, h5, h6');
    headings.forEach(heading => {
      try {
        heading.classList.add('structured-heading');
        const id = heading.id || `heading-${Math.random().toString(36).substr(2, 9)}`;
        heading.id = id;
      } catch (e) {
        // 跳过无法处理的标题
      }
    });

    return doc.body.innerHTML;
  } catch (error) {
    console.warn('结构化内容格式化失败:', error);
    return content;
  }
};

/**
 * 结构化内容组件
 * 内部变量：displayedContent - 展示后的内容
 * 内部逻辑：同步渲染结构化内容，避免异步操作导致的测试问题
 * 返回值：JSX.Element
 */
export const StructuredContent: React.FC<StructuredContentProps> = ({
  content,
  options = {},
  onDisplay
}) => {
  // 内部变量：使用 useMemo 缓存格式化结果，避免重复计算
  const displayedContent = React.useMemo(() => {
    return formatStructuredContent(content);
  }, [content]);

  // 内部逻辑：调用回调函数通知展示完成
  React.useEffect(() => {
    onDisplay?.(displayedContent);
  }, [displayedContent, onDisplay]);

  return (
    <div className="structured-content">
      <div
        className="displayed-content"
        dangerouslySetInnerHTML={{ __html: displayedContent }}
      />
    </div>
  );
};

/**
 * 结构化内容选项
 * 内部变量：结构化内容配置
 */
export const structuredContentOptions: FormattingOptions = {
  enable_markdown: false,
  enable_structured: true,
  highlight_keywords: [],
  max_content_length: 5000,
  table_styling: true,
  list_styling: true,
  quote_styling: true,
  heading_styling: true
};
