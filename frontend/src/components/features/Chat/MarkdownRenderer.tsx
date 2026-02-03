/**
 * 上海宇羲伏天智能科技有限公司出品
 */

import React from 'react';
import type { FormattingOptions } from '../../../types/chat';

/**
 * 文件级注释：Markdown渲染器组件
 * 内部逻辑：专门处理Markdown内容的渲染，使用同步渲染确保测试兼容性
 * 属性：
 *   content - Markdown内容
 *   options - 渲染选项
 *   onRender - 渲染完成回调
 */
interface MarkdownRendererProps {
  content: string;
  options?: FormattingOptions;
  onRender?: (renderedContent: string) => void;
}

/**
 * 函数级注释：渲染Markdown内容
 * 内部逻辑：使用markdown-it解析Markdown内容
 * 参数：content - Markdown内容
 * 返回值：渲染后的HTML内容
 */
const renderMarkdown = (content: string): string => {
  try {
    // 内部逻辑：检查 markdownit 是否可用
    if (typeof window.markdownit === 'undefined' || !window.markdownit) {
      console.warn('markdownit 不可用，返回原始内容');
      return content;
    }

    // 内部逻辑：使用markdown-it解析Markdown
    const markdownIt = new window.markdownit({
      html: true,
      linkify: true,
      typographer: true
    });

    // 内部逻辑：添加自定义渲染器
    markdownIt.renderer.rules.heading_open = (_tokens: any, _idx: any, _options: any, _env: any, _self: any) => {
      const token = _tokens[_idx];
      const level = token.tag;
      return `<${level} class="markdown-heading ${level}">`;
    };

    markdownIt.renderer.rules.paragraph_open = (_tokens: any, _idx: any, _options: any, _env: any, _self: any) => {
      return '<p class="markdown-paragraph">';
    };

    markdownIt.renderer.rules.code_block = (tokens: any, idx: any, _options: any, _env: any, self: any) => {
      const token = tokens[idx];
      return `<pre class="markdown-code-block"><code class="language-${token.info || ''}">${self.renderToken(tokens, idx, _options)}</code></pre>`;
    };

    markdownIt.renderer.rules.code_inline = (tokens: any, idx: any, _options: any, _env: any, self: any) => {
      const token = tokens[idx];
      return `<code class="markdown-code-inline">${self.renderToken(tokens, idx, _options)}</code>`;
    };

    markdownIt.renderer.rules.list_item_open = (_tokens: any, _idx: any, _options: any, _env: any, _self: any) => {
      return '<li class="markdown-list-item">';
    };

    markdownIt.renderer.rules.table_open = (_tokens: any, _idx: any, _options: any, _env: any, _self: any) => {
      return '<table class="markdown-table table table-bordered table-striped">';
    };

    markdownIt.renderer.rules.table_cell = (tokens: any, idx: any, _options: any, _env: any, _self: any) => {
      const token = tokens[idx];
      const cellType = token.type === 'table_cell' ? 'td' : 'th';
      const cellContent = token.content || '';
      return `<${cellType} class="markdown-table-cell ${cellType}">${cellContent}</${cellType}>`;
    };

    return markdownIt.render(content);
  } catch (error) {
    console.warn('Markdown渲染失败:', error);
    return content;
  }
};

/**
 * Markdown渲染器组件
 * 内部变量：renderedContent - 渲染后的内容
 * 内部逻辑：同步渲染Markdown内容，避免异步操作导致的测试问题
 * 返回值：JSX.Element
 */
export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
  content,
  options = {},
  onRender
}) => {
  // 内部变量：使用 useMemo 缓存渲染结果，避免重复计算
  const renderedContent = React.useMemo(() => {
    return renderMarkdown(content);
  }, [content]);

  // 内部逻辑：调用回调函数通知渲染完成
  React.useEffect(() => {
    onRender?.(renderedContent);
  }, [renderedContent, onRender]);

  return (
    <div className="markdown-renderer">
      <div
        className="rendered-content"
        dangerouslySetInnerHTML={{ __html: renderedContent }}
      />
    </div>
  );
};

/**
 * Markdown渲染选项
 * 内部变量：Markdown渲染配置
 */
export const markdownRenderingOptions: FormattingOptions = {
  enable_markdown: true,
  enable_structured: false,
  highlight_keywords: [],
  max_content_length: 10000,
  code_highlighting: true,
  link_target: '_blank'
};