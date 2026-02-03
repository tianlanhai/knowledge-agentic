/**
 * 上海宇羲伏天智能科技有限公司出品
 */

import React from 'react';
import MarkdownIt from 'markdown-it';
import type { FormattingOptions } from '../../../types/chat';

/**
 * 文件级注释：创建 markdown-it 实例
 * 内部逻辑：配置 markdown-it 解析器，支持 HTML、链接识别和排版优化
 * 内部变量：md - markdown-it 实例，全局单例避免重复创建
 */
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
});

/**
 * 文件级注释：配置 Markdown 表格渲染规则
 * 内部逻辑：为表格元素添加 CSS 类名，确保样式正确应用
 */
// 配置表格开始标签
md.renderer.rules.table_open = () => {
  return '<table class="markdown-table table table-bordered table-striped">';
};

// 配置表格单元格
md.renderer.rules.table_cell = (tokens: any, idx: number, _options: any, _env: any, self: any) => {
  const token = tokens[idx];
  const cellType = token.type === 'table_cell' ? 'td' : 'th';
  const cellContent = token.content || '';
  return `<${cellType} class="markdown-table-cell ${cellType}">${cellContent}</${cellType}>`;
};

/**
 * 文件级注释：文档格式化组件
 * 内部逻辑：处理文档内容的格式化展示，支持流式输出优化
 * 属性：
 *   content - 原始文本内容
 *   options - 格式化选项
 *   onFormat - 格式化完成回调
 *   isStreaming - 是否正在流式输出（流式期间显示纯文本，结束后格式化）
 */
interface DocumentFormatterProps {
  content: string;
  options?: FormattingOptions;
  onFormat?: (formattedContent: string) => void;
  isStreaming?: boolean;
}

/**
 * 文档格式化组件
 * 内部变量：isFormatting - 是否正在格式化
 * 内部逻辑：根据选项应用不同的格式化策略，流式期间显示纯文本
 * 返回值：JSX.Element
 *
 * 使用 React.memo 优化：只在 props 真正变化时才重新渲染
 * 自定义比较函数：避免因 options 引用变化导致的重复格式化
 */
export const DocumentFormatter: React.FC<DocumentFormatterProps> = React.memo(({
  content,
  options = {},
  onFormat,
  isStreaming = false
}) => {
  // 内部变量：格式化后的内容
  const [formattedContent, setFormattedContent] = React.useState<string>(content);
  // 内部变量：格式化状态
  const [isFormatting, setIsFormatting] = React.useState<boolean>(false);

  /**
   * 函数级注释：应用Markdown格式化
   * 内部逻辑：使用 markdown-it 库解析 Markdown 内容，支持表格、代码块等完整语法
   * 参数：content - 原始文本内容
   * 返回值：格式化后的HTML内容
   */
  const applyMarkdownFormatting = (content: string): string => {
    try {
      // 内部逻辑：检查内容是否为空
      if (!content || content.trim() === '') {
        return content;
      }

      // 内部逻辑：使用 markdown-it 解析 Markdown 内容
      // markdown-it 支持完整的 Markdown 语法，包括表格、代码块、列表等
      return md.render(content);
    } catch (error) {
      console.warn('Markdown格式化失败:', error);
      return content;
    }
  };

  /**
   * 函数级注释：应用结构化内容格式化
   * 内部逻辑：识别并格式化表格、列表、引用等结构化内容
   * 参数：content - 原始文本内容
   * 返回值：格式化后的HTML内容
   */
  const applyStructuredFormatting = (content: string): string => {
    try {
      // 内部逻辑：使用DOMParser解析HTML
      const parser = new DOMParser();
      const doc = parser.parseFromString(content, 'text/html');
      
      // 处理表格
      const tables = doc.querySelectorAll('table');
      tables.forEach(table => {
        table.classList.add('table', 'table-bordered', 'table-striped');
      });
      
      // 处理列表
      const lists = doc.querySelectorAll('ul, ol');
      lists.forEach(lst => {
        lst.classList.add('list-group');
      });
      
      // 处理引用块
      const blockquotes = doc.querySelectorAll('blockquote');
      blockquotes.forEach(blockquote => {
        blockquote.classList.add('blockquote');
      });
      
      return doc.body.innerHTML;
    } catch (error) {
      console.warn('结构化内容格式化失败:', error);
      return content;
    }
  };

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
      // 内部逻辑：使用DOMParser解析HTML
      const parser = new DOMParser();
      const doc = parser.parseFromString(content, 'text/html');
      
      keywords.forEach(keyword => {
        // 内部逻辑：查找包含关键词的文本节点
        const walker = document.createTreeWalker(
          doc.body,
          NodeFilter.SHOW_TEXT,
          null
        );
        
        let node;
        while (node = walker.nextNode()) {
          const text = node.nodeValue || '';
          if (text.toLowerCase().includes(keyword.toLowerCase())) {
            // 内部逻辑：创建高亮元素
            const mark = document.createElement('mark');
            mark.className = 'highlight';
            mark.textContent = text;
            
            // 内部逻辑：替换文本节点
            node.parentNode?.replaceChild(mark, node);
          }
        }
      });
      
      return doc.body.innerHTML;
    } catch (error) {
      console.warn('内容高亮失败:', error);
      return content;
    }
  };

  /**
   * 函数级注释：综合文档格式化
   * 内部逻辑：综合应用各种格式化方法
   * 参数：
   *   content - 原始文本内容
   *   options - 格式化选项
   * 返回值：完全格式化后的HTML内容
   */
  const formatDocument = (content: string, options: FormattingOptions): string => {
    let formatted = content;
    
    // 内部逻辑：应用Markdown格式化
    if (options.enable_markdown) {
      formatted = applyMarkdownFormatting(formatted);
    }

    // 内部逻辑：应用结构化内容格式化
    if (options.enable_structured) {
      formatted = applyStructuredFormatting(formatted);
    }

    // 内部逻辑：应用高亮
    if (options.highlight_keywords && options.highlight_keywords.length > 0) {
      formatted = applyHighlighting(formatted, options.highlight_keywords);
    }
    
    return formatted;
  };

  /**
   * 函数级注释：异步格式化文档内容
   * 内部逻辑：异步处理文档格式化
   * 返回值：Promise<string>
   */
  const formatAsync = async (): Promise<string> => {
    setIsFormatting(true);
    
    try {
      // 内部逻辑：使用setTimeout模拟异步操作
      return new Promise((resolve) => {
        setTimeout(() => {
          const result = formatDocument(content, options);
          setFormattedContent(result);
          onFormat?.(result);
          setIsFormatting(false);
          resolve(result);
        }, 100);
      });
    } catch (error) {
      setIsFormatting(false);
      throw error;
    }
  };

  // 内部逻辑：组件挂载时自动格式化，仅在非流式状态时执行
  React.useEffect(() => {
    // 内部逻辑：流式期间不格式化，流式结束后才格式化
    if (!isStreaming) {
      formatAsync();
    }
  }, [content, options, isStreaming]);

  // 内部逻辑：流式期间直接显示纯文本，避免格式化导致的跳跃
  if (isStreaming) {
    return (
      <div className="document-formatter streaming">
        <div
          className="streaming-content"
          style={{
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            lineHeight: '1.6'
          }}
        >
          {content}
        </div>
      </div>
    );
  }

  return (
    <div className="document-formatter">
      {isFormatting ? (
        <div className="loading-indicator">
          <div className="spinner"></div>
          <span>格式化中...</span>
        </div>
      ) : (
        <div
          className="formatted-content"
          dangerouslySetInnerHTML={{ __html: formattedContent }}
        />
      )}
    </div>
  );
}, (prevProps, nextProps) => {
  /**
   * React.memo 自定义比较函数
   * 内部逻辑：只有真正的变化才重新渲染
   * 返回值：true 表示 props 相等，不需要重新渲染
   */
  return (
    prevProps.content === nextProps.content &&
    prevProps.isStreaming === nextProps.isStreaming &&
    prevProps.options === nextProps.options // 引用比较，useMemo 后应该相等
  );
});

/**
 * 默认格式化选项
 * 内部变量：默认的格式化配置
 */
export const defaultFormattingOptions: FormattingOptions = {
  enable_markdown: true,
  enable_structured: true,
  highlight_keywords: ['重要', '关键', '注意', '核心', '重点'],
  max_content_length: 5000
};