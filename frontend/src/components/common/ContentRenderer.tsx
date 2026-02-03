/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：统一内容渲染器组件
 * 内部逻辑：整合 Markdown 和结构化内容渲染功能，提供统一的接口
 * 设计模式：策略模式 + 组合模式
 * 职责：根据内容类型选择合适的渲染策略
 */

import React from 'react';
import type { FormattingOptions } from '../../types/chat';

/**
 * 类型定义：渲染策略类型
 * 内部逻辑：定义支持的渲染模式
 */
export type RenderStrategy = 'markdown' | 'structured' | 'plain' | 'auto';

/**
 * 接口：渲染器接口
 * 内部逻辑：定义渲染器的统一接口
 * 设计模式：策略模式 - 渲染器策略接口
 */
interface RendererStrategy {
  /**
   * 渲染名称
   */
  readonly name: string;

  /**
   * 渲染内容
   * 参数：content - 原始内容
   * 返回值：渲染后的HTML内容
   */
  render(content: string): string;
}

/**
 * 类：Markdown渲染策略
 * 内部逻辑：专门处理Markdown内容的渲染
 * 设计模式：策略模式 - 具体策略实现
 */
class MarkdownRendererStrategy implements RendererStrategy {
  readonly name = 'markdown';

  render(content: string): string {
    try {
      // Guard Clauses：检查 markdownit 是否可用
      if (typeof window.markdownit === 'undefined' || !window.markdownit) {
        console.warn('markdownit 不可用，返回原始内容');
        return this.escapeHtml(content);
      }

      // 内部逻辑：使用markdown-it解析Markdown
      const markdownIt = new window.markdownit({
        html: true,
        linkify: true,
        typographer: true
      });

      // 内部逻辑：添加自定义渲染规则
      this.setupCustomRules(markdownIt);

      return markdownIt.render(content);
    } catch (error) {
      console.warn('Markdown渲染失败:', error);
      return this.escapeHtml(content);
    }
  }

  /**
   * 函数级注释：设置自定义渲染规则
   * 内部逻辑：配置markdown-it的渲染规则
   * @private
   */
  private setupCustomRules(markdownIt: any): void {
    // 标题样式
    markdownIt.renderer.rules.heading_open = (_tokens: any, _idx: any) => {
      const token = _tokens[_idx];
      return `<${token.tag} class="markdown-heading ${token.tag}">`;
    };

    // 段落样式
    markdownIt.renderer.rules.paragraph_open = () => {
      return '<p class="markdown-paragraph">';
    };

    // 代码块样式
    markdownIt.renderer.rules.code_block = (tokens: any, idx: any, _options: any, _env: any, self: any) => {
      const token = tokens[idx];
      return `<pre class="markdown-code-block"><code class="language-${token.info || ''}">${self.renderToken(tokens, idx, _options)}</code></pre>`;
    };

    // 行内代码样式
    markdownIt.renderer.rules.code_inline = (tokens: any, idx: any, _options: any, _env: any, self: any) => {
      return `<code class="markdown-code-inline">${self.renderToken(tokens, idx, _options)}</code>`;
    };

    // 表格样式
    markdownIt.renderer.rules.table_open = () => {
      return '<table class="markdown-table table table-bordered table-striped">';
    };
  }

  /**
   * 函数级注释：转义HTML特殊字符
   * 内部逻辑：防止XSS攻击
   * @private
   */
  private escapeHtml(content: string): string {
    const div = document.createElement('div');
    div.textContent = content;
    return div.innerHTML;
  }
}

/**
 * 类：结构化内容渲染策略
 * 内部逻辑：处理表格、列表、引用等结构化内容
 * 设计模式：策略模式 - 具体策略实现
 */
class StructuredContentRendererStrategy implements RendererStrategy {
  readonly name = 'structured';

  render(content: string): string {
    try {
      // Guard Clauses：检查 DOMParser 是否可用
      if (typeof DOMParser === 'undefined' || !DOMParser) {
        console.warn('DOMParser 不可用，返回原始内容');
        return content;
      }

      // 内部逻辑：使用DOMParser解析HTML
      const parser = new DOMParser();
      const doc = parser.parseFromString(content, 'text/html');

      // Guard Clauses：检查解析结果
      if (!doc || !doc.body) {
        return content;
      }

      // 内部逻辑：应用结构化样式
      this.applyStructuredStyles(doc);

      return doc.body.innerHTML;
    } catch (error) {
      console.warn('结构化内容格式化失败:', error);
      return content;
    }
  }

  /**
   * 函数级注释：应用结构化样式
   * 内部逻辑：为各种HTML元素添加Bootstrap样式类
   * @private
   */
  private applyStructuredStyles(doc: Document): void {
    // 处理表格
    const tables = doc.querySelectorAll('table');
    tables.forEach(table => {
      table.classList.add('table', 'table-bordered', 'table-striped', 'structured-table');
    });

    // 处理列表
    const lists = doc.querySelectorAll('ul, ol');
    lists.forEach(lst => {
      lst.classList.add('list-group', 'structured-list');
      lst.querySelectorAll('li').forEach(item => {
        item.classList.add('list-group-item', 'structured-list-item');
      });
    });

    // 处理引用块
    const blockquotes = doc.querySelectorAll('blockquote');
    blockquotes.forEach(blockquote => {
      blockquote.classList.add('blockquote', 'structured-blockquote');
    });

    // 处理代码块
    const codeBlocks = doc.querySelectorAll('pre code');
    codeBlocks.forEach(code => {
      code.classList.add('structured-code');
      const pre = code.parentElement;
      if (pre) {
        pre.classList.add('structured-code-block');
      }
    });
  }
}

/**
 * 类：纯文本渲染策略
 * 内部逻辑：不做任何处理，直接返回原内容
 * 设计模式：策略模式 - 默认策略实现
 */
class PlainTextRendererStrategy implements RendererStrategy {
  readonly name = 'plain';

  render(content: string): string {
    return content;
  }
}

/**
 * 类：自动检测渲染策略
 * 内部逻辑：自动判断内容类型并选择合适的渲染方式
 * 设计模式：策略模式 + 工厂模式
 */
class AutoDetectRendererStrategy implements RendererStrategy {
  readonly name = 'auto';

  // 内部变量：策略实例
  private markdownStrategy = new MarkdownRendererStrategy();
  private structuredStrategy = new StructuredContentRendererStrategy();
  private plainStrategy = new PlainTextRendererStrategy();

  render(content: string): string {
    // 内部逻辑：检测内容类型并选择策略
    if (this.isMarkdownContent(content)) {
      return this.markdownStrategy.render(content);
    }
    if (this.isStructuredContent(content)) {
      return this.structuredStrategy.render(content);
    }
    return this.plainStrategy.render(content);
  }

  /**
   * 函数级注释：检测是否为Markdown内容
   * 内部逻辑：检查Markdown特征标记
   * @private
   */
  private isMarkdownContent(content: string): boolean {
    const markdownPatterns = [
      /^#{1,6}\s/m,  // 标题
      /\*\*.*\*\*/,  // 粗体
      /\*.*\*/,      // 斜体
      /```/,         // 代码块
      /^\s*[-*+]\s/m, // 列表
      /\[.*\]\(.*\)/, // 链接
    ];
    return markdownPatterns.some(pattern => pattern.test(content));
  }

  /**
   * 函数级注释：检测是否为结构化内容
   * 内部逻辑：检查HTML标签
   * @private
   */
  private isStructuredContent(content: string): boolean {
    const htmlTags = ['<table', '<ul>', '<ol>', '<blockquote', '<div', '<span'];
    return htmlTags.some(tag => content.includes(tag));
  }
}

/**
 * 类：渲染器工厂
 * 内部逻辑：管理渲染策略的创建和获取
 * 设计模式：工厂模式 + 注册表模式
 */
export class RendererFactory {
  // 内部变量：策略注册表
  private static strategies: Map<RenderStrategy, RendererStrategy> = new Map<RenderStrategy, RendererStrategy>([
    ['markdown', new MarkdownRendererStrategy()],
    ['structured', new StructuredContentRendererStrategy()],
    ['plain', new PlainTextRendererStrategy()],
    ['auto', new AutoDetectRendererStrategy()],
  ] as Array<[RenderStrategy, RendererStrategy]>);

  /**
   * 函数级注释：获取渲染策略
   * 内部逻辑：根据策略类型返回对应的渲染器
   */
  static getStrategy(strategy: RenderStrategy): RendererStrategy {
    return this.strategies.get(strategy) || new PlainTextRendererStrategy();
  }

  /**
   * 函数级注释：注册自定义策略
   * 内部逻辑：支持扩展新的渲染策略
   */
  static registerStrategy(
    strategyType: RenderStrategy,
    strategy: RendererStrategy
  ): void {
    this.strategies.set(strategyType, strategy);
  }
}

/**
 * 接口：内容渲染器属性
 */
export interface ContentRendererProps {
  /** 要渲染的内容 */
  content: string;
  /** 渲染策略 */
  strategy?: RenderStrategy;
  /** 格式化选项 */
  options?: FormattingOptions;
  /** 自定义类名 */
  className?: string;
  /** 渲染完成回调 */
  onRender?: (renderedContent: string) => void;
}

/**
 * 组件：统一内容渲染器
 * 内部逻辑：根据策略选择合适的渲染方式渲染内容
 * 设计模式：策略模式 + 组合模式
 *
 * 使用示例：
 * ```tsx
 * // Markdown渲染
 * <ContentRenderer content="# 标题" strategy="markdown" />
 *
 * // 结构化内容渲染
 * <ContentRenderer content="<table>...</table>" strategy="structured" />
 *
 * // 自动检测
 * <ContentRenderer content={content} strategy="auto" />
 * ```
 */
export const ContentRenderer: React.FC<ContentRendererProps> = ({
  content,
  strategy = 'auto',
  options = {},
  className = '',
  onRender
}) => {
  // 内部变量：获取渲染策略
  const rendererStrategy = React.useMemo(
    () => RendererFactory.getStrategy(strategy),
    [strategy]
  );

  // 内部变量：渲染内容
  const renderedContent = React.useMemo(() => {
    // Guard Clauses：空内容处理
    if (!content) {
      return '';
    }

    // 内部逻辑：应用内容长度限制
    const maxLength = options.max_content_length || Infinity;
    const processedContent = content.length > maxLength
      ? content.slice(0, maxLength) + '...'
      : content;

    // 内部逻辑：使用策略渲染内容
    return rendererStrategy.render(processedContent);
  }, [content, rendererStrategy, options.max_content_length]);

  // 内部逻辑：通知渲染完成
  React.useEffect(() => {
    onRender?.(renderedContent);
  }, [renderedContent, onRender]);

  // 内部变量：生成类名
  const containerClassName = [
    'content-renderer',
    `content-renderer--${strategy}`,
    className
  ].filter(Boolean).join(' ');

  return (
    <div className={containerClassName}>
      <div
        className="rendered-content"
        dangerouslySetInnerHTML={{ __html: renderedContent }}
      />
    </div>
  );
};

/**
 * 默认导出
 */
export default ContentRenderer;

// 内部变量：导出预定义的渲染选项
export const defaultRenderingOptions: FormattingOptions = {
  enable_markdown: true,
  enable_structured: true,
  highlight_keywords: [],
  max_content_length: 10000,
  code_highlighting: true,
  link_target: '_blank'
};
