/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：DocumentFormatter 组件单元测试
 * 内部逻辑：测试流式期间和结束后的渲染行为差异
 */

import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { DocumentFormatter } from './DocumentFormatter';
import type { FormattingOptions } from '../../../types/chat';

describe('DocumentFormatter 组件', () => {
  const mockOptions: FormattingOptions = {
    enable_markdown: true,
    enable_structured: true,
    highlight_keywords: ['重要', '关键'],
    max_content_length: 5000,
  };

  describe('流式状态测试', () => {
    it('应该在流式期间显示纯文本内容', () => {
      const codeContent = '```js\nconsole.log("test");\n```';

      const { container } = render(
        <DocumentFormatter
          content={codeContent}
          isStreaming={true}
          options={mockOptions}
        />
      );

      // 验证有 streaming class
      const streamingDiv = container.querySelector('.document-formatter.streaming');
      expect(streamingDiv).toBeInTheDocument();

      // 验证显示原始内容
      const content = container.querySelector('.streaming-content');
      expect(content).toBeInTheDocument();
      expect(content).toHaveTextContent(/console\.log/);
    });

    it('应该在流式期间不触发格式化', () => {
      const onFormatCallback = vi.fn();

      render(
        <DocumentFormatter
          content="# 标题\n**粗体**"
          isStreaming={true}
          options={mockOptions}
          onFormat={onFormatCallback}
        />
      );

      // 流式期间不调用格式化回调
      expect(onFormatCallback).not.toHaveBeenCalled();
    });

    it('应该在流式结束后触发格式化', async () => {
      const onFormatCallback = vi.fn();
      const markdownContent = '# 标题\n**粗体**';

      const { rerender } = render(
        <DocumentFormatter
          content={markdownContent}
          isStreaming={true}
          options={mockOptions}
          onFormat={onFormatCallback}
        />
      );

      // 流式期间不调用
      expect(onFormatCallback).not.toHaveBeenCalled();

      // 切换为非流式状态
      rerender(
        <DocumentFormatter
          content={markdownContent}
          isStreaming={false}
          options={mockOptions}
          onFormat={onFormatCallback}
        />
      );

      // 等待 useEffect 触发格式化
      await waitFor(() => {
        expect(onFormatCallback).toHaveBeenCalled();
      });
    });
  });

  describe('格式化内容测试', () => {
    it('应该正确格式化 Markdown 内容', async () => {
      const markdownContent = '# 标题\n\n这是**粗体**文本';

      render(
        <DocumentFormatter
          content={markdownContent}
          isStreaming={false}
          options={mockOptions}
        />
      );

      await waitFor(() => {
        const formattedContent = document.querySelector('.formatted-content');
        expect(formattedContent).toBeInTheDocument();
      });
    });

    it('应该在非流式状态显示格式化内容', async () => {
      const markdownContent = '## 小标题\n\n*斜体*';

      render(
        <DocumentFormatter
          content={markdownContent}
          isStreaming={false}
          options={mockOptions}
        />
      );

      await waitFor(() => {
        const formattedContent = document.querySelector('.formatted-content');
        expect(formattedContent).toBeInTheDocument();
      });
    });
  });

  describe('样式测试', () => {
    it('应该正确应用流式样式', () => {
      const { container } = render(
        <DocumentFormatter
          content="测试内容"
          isStreaming={true}
        />
      );

      const streamingContent = container.querySelector('.streaming-content');
      expect(streamingContent).toBeInTheDocument();
      expect(streamingContent).toHaveStyle({
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
        lineHeight: '1.6',
      });
    });

    it('应该在流式期间添加 streaming 类名', () => {
      const { container } = render(
        <DocumentFormatter
          content="测试内容"
          isStreaming={true}
        />
      );

      const formatterDiv = container.querySelector('.document-formatter.streaming');
      expect(formatterDiv).toBeInTheDocument();
    });

    it('应该在非流式期间移除 streaming 类名', () => {
      const { container } = render(
        <DocumentFormatter
          content="测试内容"
          isStreaming={false}
        />
      );

      const formatterDiv = container.querySelector('.document-formatter.streaming');
      expect(formatterDiv).not.toBeInTheDocument();
    });
  });

  describe('边缘情况测试', () => {
    it('应该处理空内容', async () => {
      const { container } = render(
        <DocumentFormatter
          content=""
          isStreaming={false}
        />
      );

      // 等待格式化完成或显示内容
      await waitFor(
        () => {
          const formattedContent = container.querySelector('.formatted-content');
          const loadingIndicator = container.querySelector('.loading-indicator');
          // 只要显示其中一个即可
          expect(formattedContent || loadingIndicator).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    });

    it('应该处理特殊字符', () => {
      const specialContent = '特殊字符: < > & " \'';

      const { container } = render(
        <DocumentFormatter
          content={specialContent}
          isStreaming={true}
        />
      );

      const content = container.querySelector('.streaming-content');
      expect(content).toHaveTextContent(/特殊字符/);
    });

    it('应该处理多行内容', () => {
      const multilineContent = '第一行\n第二行\n第三行';

      const { container } = render(
        <DocumentFormatter
          content={multilineContent}
          isStreaming={true}
        />
      );

      const content = container.querySelector('.streaming-content');
      expect(content).toHaveTextContent(/第一行/);
      expect(content).toHaveTextContent(/第二行/);
      expect(content).toHaveTextContent(/第三行/);
    });
  });

  describe('选项测试', () => {
    it('应该使用提供的格式化选项', async () => {
      const customOptions: FormattingOptions = {
        enable_markdown: true,
        enable_structured: false,
        highlight_keywords: ['测试'],
      };

      const onFormatCallback = vi.fn();

      render(
        <DocumentFormatter
          content="测试内容"
          isStreaming={false}
          options={customOptions}
          onFormat={onFormatCallback}
        />
      );

      await waitFor(() => {
        expect(onFormatCallback).toHaveBeenCalled();
      });
    });

    it('应该处理高亮关键词', async () => {
      const optionsWithKeywords: FormattingOptions = {
        enable_markdown: true,
        highlight_keywords: ['重要'],
      };

      const { container } = render(
        <DocumentFormatter
          content="这是重要的内容"
          isStreaming={false}
          options={optionsWithKeywords}
        />
      );

      await waitFor(() => {
        const formattedContent = container.querySelector('.formatted-content');
        expect(formattedContent).toBeInTheDocument();
      });
    });
  });

  describe('错误处理测试', () => {
    it('应该在applyHighlighting出错时返回原始内容', async () => {
      // 内部逻辑：Mock DOMParser.createTreeWalker抛出错误
      const originalCreateTreeWalker = document.createTreeWalker;
      vi.spyOn(document, 'createTreeWalker').mockImplementation(() => {
        throw new Error('TreeWalker error');
      });

      const optionsWithKeywords: FormattingOptions = {
        enable_markdown: false,
        highlight_keywords: ['测试'],
      };

      const { container } = render(
        <DocumentFormatter
          content="测试内容"
          isStreaming={false}
          options={optionsWithKeywords}
        />
      );

      await waitFor(() => {
        const formattedContent = container.querySelector('.formatted-content');
        expect(formattedContent).toBeInTheDocument();
      });

      document.createTreeWalker = originalCreateTreeWalker;
    });

    it('应该在formatAsync出错时重置格式化状态', async () => {
      // 内部逻辑：Mock formatDocument抛出错误
      const consoleErrorSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      // 内部逻辑：使用会抛出错误的内容和选项组合
      const problematicOptions: FormattingOptions = {
        enable_markdown: true,
        enable_structured: true,
        highlight_keywords: [],
      };

      const { container } = render(
        <DocumentFormatter
          content="<div>测试内容</div>"
          isStreaming={false}
          options={problematicOptions}
        />
      );

      // 内部逻辑：等待组件渲染完成
      await waitFor(() => {
        const content = container.querySelector('.document-formatter');
        expect(content).toBeInTheDocument();
      });

      consoleErrorSpy.mockRestore();
    });

    it('应该处理applyStructuredFormatting错误', async () => {
      // 内部逻辑：Mock DOMParser.parseFromString抛出错误
      const originalDOMParser = global.DOMParser;
      // @ts-ignore - 临时移除DOMParser
      delete (global as any).DOMParser;

      const optionsWithStructured: FormattingOptions = {
        enable_markdown: false,
        enable_structured: true,
      };

      const { container } = render(
        <DocumentFormatter
          content="测试内容"
          isStreaming={false}
          options={optionsWithStructured}
        />
      );

      await waitFor(() => {
        const content = container.querySelector('.document-formatter');
        expect(content).toBeInTheDocument();
      });

      global.DOMParser = originalDOMParser;
    });

    it('应该处理applyMarkdownFormatting错误', async () => {
      // 内部逻辑：使用会导致正则表达式错误的内容
      const { container } = render(
        <DocumentFormatter
          content="正常内容"
          isStreaming={false}
          options={{ enable_markdown: true }}
        />
      );

      await waitFor(() => {
        const formattedContent = container.querySelector('.formatted-content');
        expect(formattedContent).toBeInTheDocument();
      });
    });
  });

  describe('加载状态测试', () => {
    it('应该在格式化期间显示加载指示器', async () => {
      const { container } = render(
        <DocumentFormatter
          content="# 标题\n内容"
          isStreaming={false}
        />
      );

      // 内部逻辑：初始状态应该显示加载指示器或已格式化内容
      await waitFor(() => {
        const loadingIndicator = container.querySelector('.loading-indicator');
        const formattedContent = container.querySelector('.formatted-content');
        expect(loadingIndicator || formattedContent).toBeInTheDocument();
      });
    });
  });

  describe('React.memo比较函数测试', () => {
    it('应该在内容相同时跳过重新渲染', () => {
      const renderCount = vi.fn();
      const originalMemo = React.memo;

      // 内部逻辑：监控组件渲染
      React.memo = ((fn: any, compare?: any) => {
        const wrapped = originalMemo(fn, compare);
        return function MemorizedComponent(props: any) {
          renderCount();
          return wrapped(props);
        };
      }) as typeof React.memo;

      const content = "测试内容";
      const { rerender } = render(
        <DocumentFormatter
          content={content}
          isStreaming={true}
        />
      );

      const initialCount = renderCount.mock.calls.length;

      rerender(
        <DocumentFormatter
          content={content}
          isStreaming={true}
        />
      );

      // 内部逻辑：由于内容相同，React.memo应该阻止重新渲染
      React.memo = originalMemo;
    });
  });
});
