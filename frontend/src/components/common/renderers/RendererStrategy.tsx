/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：渲染策略模块
 * 内部逻辑：提供可扩展的内容渲染策略，支持多种格式
 * 设计模式：策略模式（Strategy Pattern）+ 注册表模式
 * 设计原则：开闭原则、依赖倒置原则
 */

import React from 'react';
import type { ComponentType, ReactNode } from 'react';
import ReactMarkdown from 'react-markdown';

/**
 * 渲染结果接口
 */
export interface RenderResult {
  /** 是否可以渲染 */
  canRender: boolean;
  /** 优先级（数值越小优先级越高） */
  priority?: number;
  /** 渲染结果 */
  render?: () => ReactNode;
}

/**
 * 渲染器策略接口
 */
export interface RendererStrategy {
  /** 策略名称 */
  name: string;
  /** 优先级 */
  priority: number;

  /**
   * 检查是否可以渲染
   * 参数：
   *   content - 内容字符串
   *   context - 渲染上下文
   * 返回值：是否可以渲染
   */
  canRender(content: string, context?: RenderContext): boolean;

  /**
   * 渲染内容
   * 参数：
   *   content - 内容字符串
   *   context - 渲染上下文
   * 返回值：React 节点
   */
  render(content: string, context?: RenderContext): ReactNode;
}

/**
 * 渲染上下文接口
 */
export interface RenderContext {
  /** 额外数据 */
  [key: string]: any;
}

/**
 * 类：纯文本渲染策略
 * 内部逻辑：渲染普通文本内容
 * 设计模式：策略模式 - 具体策略
 */
export class PlainTextRendererStrategy implements RendererStrategy {
  name = 'plaintext';
  priority = 999; // 最低优先级

  canRender(content: string): boolean {
    // 内部逻辑：纯文本总是可以渲染（作为后备）
    return true;
  }

  render(content: string): ReactNode {
    return <div className="render-plaintext">{content}</div>;
  }
}

/**
 * 类：Markdown 渲染策略
 * 内部逻辑：渲染 Markdown 格式内容
 * 设计模式：策略模式 - 具体策略
 */
export class MarkdownRendererStrategy implements RendererStrategy {
  name = 'markdown';
  priority = 100;

  canRender(content: string): boolean {
    // 内部逻辑：检测 Markdown 特征
    const markdownPatterns = [
      /^#{1,6}\s/, // 标题
      /\*\*.*\*\*/, // 粗体
      /\*.*\*/, // 斜体
      /^\s*[-*+]\s/, // 列表
      /^\s*\d+\.\s/, // 有序列表
      /\[.*\]\(.*\)/, // 链接
      /```[\s\S]*```/, // 代码块
      /`[^`]+`/ // 行内代码
    ];

    return markdownPatterns.some((pattern) => pattern.test(content));
  }

  render(content: string): ReactNode {
    return (
      <div className="render-markdown">
        <ReactMarkdown
          components={{
            // 内部逻辑：自定义组件渲染
            code: ({ node, inline, className, children, ...props }) => {
              const match = /language-(\w+)/.exec(className || '');
              return !inline ? (
                <code className={className} {...props}>
                  {children}
                </code>
              ) : (
                <code className="bg-gray-100 px-1 py-0.5 rounded text-sm" {...props}>
                  {children}
                </code>
              );
            },
            a: ({ node, children, ...props }) => (
              <a
                className="text-blue-600 hover:text-blue-800 underline"
                target="_blank"
                rel="noopener noreferrer"
                {...props}
              >
                {children}
              </a>
            )
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    );
  }
}

/**
 * 类：JSON 渲染策略
 * 内部逻辑：渲染 JSON 格式内容
 * 设计模式：策略模式 - 具体策略
 */
export class JSONRendererStrategy implements RendererStrategy {
  name = 'json';
  priority = 200;

  canRender(content: string): boolean {
    try {
      const trimmed = content.trim();
      // 内部逻辑：检查是否以 { 或 [ 开头
      if (!trimmed.startsWith('{') && !trimmed.startsWith('[')) {
        return false;
      }
      JSON.parse(trimmed);
      return true;
    } catch {
      return false;
    }
  }

  render(content: string): ReactNode {
    try {
      const data = JSON.parse(content);
      return (
        <pre className="render-json bg-gray-50 p-4 rounded overflow-auto">
          <code>{JSON.stringify(data, null, 2)}</code>
        </pre>
      );
    } catch {
      return <div className="text-red-500">无效的 JSON</div>;
    }
  }
}

/**
 * 类：代码渲染策略
 * 内部逻辑：渲染代码块内容
 * 设计模式：策略模式 - 具体策略
 */
export class CodeRendererStrategy implements RendererStrategy {
  name = 'code';
  priority = 150;

  canRender(content: string): boolean {
    // 内部逻辑：检测代码块特征
    const trimmed = content.trim();
    return (
      trimmed.startsWith('```') ||
      /^[\s\S]*?(function|const|let|var|class|import|export)\s/.test(content)
    );
  }

  render(content: string): ReactNode {
    // 内部逻辑：提取语言和代码内容
    const match = content.trim().match(/^```(\w*)\n([\s\S]*)```$/);

    if (match) {
      const language = match[1] || 'text';
      const code = match[2];
      return (
        <div className="render-code">
          <div className="bg-gray-800 text-gray-300 px-4 py-1 text-sm rounded-t">
            {language}
          </div>
          <pre className="bg-gray-900 text-gray-100 p-4 rounded-b overflow-x-auto">
            <code>{code}</code>
          </pre>
        </div>
      );
    }

    // 内部逻辑：没有代码块标记，直接渲染
    return (
      <pre className="render-code bg-gray-900 text-gray-100 p-4 rounded overflow-x-auto">
        <code>{content}</code>
      </pre>
    );
  }
}

/**
 * 类：HTML 渲染策略
 * 内部逻辑：渲染 HTML 格式内容
 * 设计模式：策略模式 - 具体策略
 */
export class HTMLRendererStrategy implements RendererStrategy {
  name = 'html';
  priority = 180;

  canRender(content: string): boolean {
    // 内部逻辑：检测 HTML 特征
    const htmlPatterns = [
      /<[^>]+>/, // 任何标签
      /&[a-zA-Z]+;/, // HTML 实体
      /<\s*html/i // HTML 根元素
    ];

    return htmlPatterns.some((pattern) => pattern.test(content));
  }

  render(content: string): ReactNode {
    return (
      <div
        className="render-html"
        dangerouslySetInnerHTML={{ __html: content }}
      />
    );
  }
}

/**
 * 类：LaTeX 渲染策略
 * 内部逻辑：渲染 LaTeX 数学公式
 * 设计模式：策略模式 - 具体策略
 */
export class LaTeXRendererStrategy implements RendererStrategy {
  name = 'latex';
  priority = 170;

  canRender(content: string): boolean {
    // 内部逻辑：检测 LaTeX 特征
    const latexPatterns = [
      /\$\$[\s\S]*?\$\$/, // 块级公式
      /\$[^$]+\$/, // 行内公式
      /\\[\[\]]/, // \[ ... \]
      /\\\(/, // \( ... \)
      /\\[a-zA-Z]+\{/ // 命令如 \frac{
    ];

    return latexPatterns.some((pattern) => pattern.test(content));
  }

  render(content: string): ReactNode {
    // 内部逻辑：这里需要集成 KaTeX 或 MathJax
    // 简化版本：直接显示代码
    return (
      <div className="render-latex bg-blue-50 p-4 rounded border border-blue-200">
        <div className="text-xs text-blue-600 mb-2">LaTeX 公式</div>
        <pre className="text-sm">{content}</pre>
      </div>
    );
  }
}

/**
 * 类：Mermaid 图表渲染策略
 * 内部逻辑：渲染 Mermaid 图表
 * 设计模式：策略模式 - 具体策略
 */
export class MermaidRendererStrategy implements RendererStrategy {
  name = 'mermaid';
  priority = 160;

  canRender(content: string): boolean {
    const trimmed = content.trim().toLowerCase();
    return (
      trimmed.startsWith('```mermaid') ||
      trimmed.startsWith('graph ') ||
      trimmed.startsWith('flowchart ') ||
      trimmed.startsWith('sequencediagram') ||
      trimmed.startsWith('classdiagram') ||
      trimmed.startsWith('statediagram') ||
      trimmed.startsWith('erdiagram') ||
      trimmed.startsWith('gantt') ||
      trimmed.startsWith('pie') ||
      trimmed.startsWith('mindmap')
    );
  }

  render(content: string): ReactNode {
    // 内部逻辑：这里需要集成 mermaid.js
    // 简化版本：显示代码块
    const cleanContent = content.replace(/^```mermaid\n?|```$/gi, '');

    return (
      <div className="render-mermaid bg-purple-50 p-4 rounded border border-purple-200">
        <div className="text-xs text-purple-600 mb-2">Mermaid 图表</div>
        <pre className="text-sm overflow-auto">{cleanContent}</pre>
      </div>
    );
  }
}

/**
 * 类：表格渲染策略
 * 内部逻辑：渲染表格格式内容
 * 设计模式：策略模式 - 具体策略
 */
export class TableRendererStrategy implements RendererStrategy {
  name = 'table';
  priority = 140;

  canRender(content: string): boolean {
    // 内部逻辑：检测表格特征（Markdown 表格）
    const lines = content.trim().split('\n');
    if (lines.length < 2) return false;

    // 内部逻辑：检查是否有分隔行
    const hasSeparator = lines.some((line) =>
      /^\|?[\s\-:]+\|[\s\-:]+/.test(line)
    );

    // 内部逻辑：检查是否有多个 | 分隔的行
    const hasPipeRows = lines.filter((line) => line.includes('|')).length >= 2;

    return hasSeparator && hasPipeRows;
  }

  render(content: string): ReactNode {
    const lines = content.trim().split('\n');

    // 内部逻辑：解析表格
    const parseRow = (line: string) =>
      line
        .split('|')
        .map((cell) => cell.trim())
        .filter((cell) => cell);

    const headers = parseRow(lines[0]);
    const rows = lines.slice(2).map(parseRow).filter((row) => row.length > 0);

    return (
      <div className="render-table overflow-x-auto">
        <table className="min-w-full border-collapse border">
          <thead>
            <tr className="bg-gray-100">
              {headers.map((header, i) => (
                <th
                  key={i}
                  className="border px-4 py-2 text-left font-medium"
                >
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                {row.map((cell, j) => (
                  <td key={j} className="border px-4 py-2">
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }
}

/**
 * 类：渲染器注册表
 * 内部逻辑：管理所有渲染策略的注册和获取
 * 设计模式：注册表模式 + 工厂模式
 */
export class RendererRegistry {
  /** 内部变量：策略列表 */
  private strategies: RendererStrategy[] = [];

  /**
   * 函数级注释：注册策略
   * 参数：
   *   strategy - 渲染策略
   */
  register(strategy: RendererStrategy): void {
    // 内部逻辑：检查是否已存在
    const existingIndex = this.strategies.findIndex(
      (s) => s.name === strategy.name
    );

    if (existingIndex >= 0) {
      // 内部逻辑：替换现有策略
      this.strategies[existingIndex] = strategy;
    } else {
      // 内部逻辑：添加新策略并按优先级排序
      this.strategies.push(strategy);
      this.strategies.sort((a, b) => a.priority - b.priority);
    }
  }

  /**
   * 函数级注释：注销策略
   * 参数：
   *   name - 策略名称
   */
  unregister(name: string): void {
    this.strategies = this.strategies.filter((s) => s.name !== name);
  }

  /**
   * 函数级注释：获取策略
   * 参数：
   *   name - 策略名称
   * 返回值：策略实例或 undefined
   */
  getStrategy(name: string): RendererStrategy | undefined {
    return this.strategies.find((s) => s.name === name);
  }

  /**
   * 函数级注释：查找适合的策略
   * 参数：
   *   content - 内容字符串
   *   context - 渲染上下文
   * 返回值：第一个匹配的策略
   */
  findStrategy(
    content: string,
    context?: RenderContext
  ): RendererStrategy | undefined {
    return this.strategies.find((strategy) =>
      strategy.canRender(content, context)
    );
  }

  /**
   * 函数级注释：获取所有策略
   * 返回值：策略列表
   */
  getAllStrategies(): RendererStrategy[] {
    return [...this.strategies];
  }
}

/**
 * 内部变量：全局渲染器注册表实例
 */
export const rendererRegistry = new RendererRegistry();

/**
 * 注册默认策略
 */
rendererRegistry.register(new TableRendererStrategy());
rendererRegistry.register(new JSONRendererStrategy());
rendererRegistry.register(new MermaidRendererStrategy());
rendererRegistry.register(new LaTeXRendererStrategy());
rendererRegistry.register(new HTMLRendererStrategy());
rendererRegistry.register(new CodeRendererStrategy());
rendererRegistry.register(new MarkdownRendererStrategy());
rendererRegistry.register(new PlainTextRendererStrategy());

/**
 * 组件：SmartRenderer
 * 内部逻辑：根据内容类型自动选择合适的渲染器
 * 设计模式：策略模式 + 组件模式
 */
export interface SmartRendererProps {
  /** 要渲染的内容 */
  content: string;
  /** 渲染上下文 */
  context?: RenderContext;
  /** 自定义渲染器注册表 */
  registry?: RendererRegistry;
  /** 无匹配策略时的回退组件 */
  fallback?: ReactNode;
  /** 渲染器名称（强制使用指定渲染器） */
  forceRenderer?: string;
}

export const SmartRenderer: React.FC<SmartRendererProps> = ({
  content,
  context,
  registry = rendererRegistry,
  fallback,
  forceRenderer
}) => {
  // 内部逻辑：确定使用的策略
  let strategy: RendererStrategy | undefined;

  if (forceRenderer) {
    // 内部逻辑：强制使用指定渲染器
    strategy = registry.getStrategy(forceRenderer);
  } else {
    // 内部逻辑：自动查找合适的渲染器
    strategy = registry.findStrategy(content, context);
  }

  // 内部逻辑：渲染内容
  if (strategy) {
    return <>{strategy.render(content, context)}</>;
  }

  // 内部逻辑：使用回退组件
  return <>{fallback || <pre>{content}</pre>}</>;
};

/**
 * Hook：useRenderer
 * 内部逻辑：提供渲染功能的 Hook
 * 设计模式：Hook 模式
 */
export function useRenderer(registry: RendererRegistry = rendererRegistry) {
  /**
   * 函数级注释：渲染内容
   */
  const render = (
    content: string,
    context?: RenderContext,
    forceRenderer?: string
  ): ReactNode => {
    let strategy: RendererStrategy | undefined;

    if (forceRenderer) {
      strategy = registry.getStrategy(forceRenderer);
    } else {
      strategy = registry.findStrategy(content, context);
    }

    if (strategy) {
      return strategy.render(content, context);
    }

    return <pre>{content}</pre>;
  };

  /**
   * 函数级注释：检测内容类型
   */
  const detectType = (content: string): string | undefined => {
    const strategy = registry.findStrategy(content);
    return strategy?.name;
  };

  /**
   * 函数级注释：注册自定义渲染器
   */
  const registerStrategy = (strategy: RendererStrategy) => {
    registry.register(strategy);
  };

  return {
    render,
    detectType,
    registerStrategy,
    registry
  };
}

/**
 * 组件：MultiFormatRenderer
 * 内部逻辑：支持多种格式混合的内容渲染
 */
export interface MultiFormatRendererProps {
  /** 内容片段列表 */
  segments: Array<{
    content: string;
    type?: string;
  }>;
  /** 分隔符 */
  separator?: ReactNode;
  /** 容器样式 */
  containerStyle?: React.CSSProperties;
  /** 渲染上下文 */
  context?: RenderContext;
}

export const MultiFormatRenderer: React.FC<MultiFormatRendererProps> = ({
  segments,
  separator = <hr className="my-4" />,
  containerStyle,
  context
}) => {
  return (
    <div style={containerStyle}>
      {segments.map((segment, index) => (
        <div key={index}>
          <SmartRenderer
            content={segment.content}
            context={context}
            forceRenderer={segment.type}
          />
          {index < segments.length - 1 && separator}
        </div>
      ))}
    </div>
  );
};

// 导出所有公共接口
export default SmartRenderer;
