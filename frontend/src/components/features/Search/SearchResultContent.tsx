/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：搜索结果内容渲染组件
 * 功能：将 Markdown 内容渲染为 HTML，并在其中高亮搜索关键词
 * 内部逻辑：使用简单 Markdown 解析（无需额外依赖），然后在 HTML 中高亮关键词
 */

import React from 'react';

/**
 * 组件属性接口
 */
interface SearchResultContentProps {
  /** 原始 Markdown 内容 */
  content: string;
  /** 搜索关键词 */
  query: string;
}

/**
 * 搜索结果内容渲染组件
 * 内部变量：renderedHtml - 渲染后的 HTML 内容
 * 内部逻辑：
 *   1. 使用正则表达式将 Markdown 转换为 HTML
 *   2. 在 HTML 中使用 DOMParser 和 TreeWalker 高亮关键词
 * 返回值：JSX.Element
 */
export const SearchResultContent: React.FC<SearchResultContentProps> = ({
  content,
  query
}) => {
  // 内部变量：渲染后的 HTML 内容
  const [renderedHtml, setRenderedHtml] = React.useState<string>('');
  // 内部变量：渲染状态
  const [isRendering, setIsRendering] = React.useState<boolean>(false);

  /**
   * 函数级注释：转义正则表达式特殊字符
   * 内部逻辑：将正则表达式中的特殊字符转义，避免匹配错误
   * 参数：str - 需要转义的字符串
   * 返回值：转义后的字符串
   */
  const escapeRegExp = (str: string): string => {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  };

  /**
   * 函数级注释：转义 HTML 特殊字符
   * 内部逻辑：将 HTML 特殊字符转义，防止 XSS 攻击
   * 参数：str - 需要转义的字符串
   * 返回值：转义后的字符串
   */
  const escapeHtml = (str: string): string => {
    const htmlEntities: Record<string, string> = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    };
    return str.replace(/[&<>"']/g, (char) => htmlEntities[char]);
  };

  /**
   * 函数级注释：渲染 Markdown 内容为 HTML
   * 内部逻辑：使用正则表达式将 Markdown 语法转换为 HTML
   * 参数：markdown - Markdown 格式的文本
   * 返回值：HTML 字符串
   */
  const renderMarkdown = (markdown: string): string => {
    try {
      // Guard Clause：空内容直接返回
      if (!markdown || markdown.trim() === '') {
        return '';
      }

      // 内部变量：先转义 HTML 特殊字符
      let html = escapeHtml(markdown);

      // 内部逻辑：按顺序处理 Markdown 语法（注意顺序很重要）
      // 1. 代码块（必须先处理，避免内部内容被其他规则匹配）
      html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
        return `<pre class="markdown-code-block"><code>${code}</code></pre>`;
      });

      // 2. 行内代码（必须先处理，避免内部内容被其他规则匹配）
      html = html.replace(/`([^`]+)`/g, (match, code) => {
        return `<code class="markdown-code-inline">${code}</code>`;
      });

      // 3. 标题（# ## ### #### ##### ######）
      html = html.replace(/^######\s+(.*)$/gm, '<h6 class="markdown-heading h6">$1</h6>');
      html = html.replace(/^#####\s+(.*)$/gm, '<h5 class="markdown-heading h5">$1</h5>');
      html = html.replace(/^####\s+(.*)$/gm, '<h4 class="markdown-heading h4">$1</h4>');
      html = html.replace(/^###\s+(.*)$/gm, '<h3 class="markdown-heading h3">$1</h3>');
      html = html.replace(/^##\s+(.*)$/gm, '<h2 class="markdown-heading h2">$1</h2>');
      html = html.replace(/^#\s+(.*)$/gm, '<h1 class="markdown-heading h1">$1</h1>');

      // 4. 粗体（**text** 或 __text__）
      html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
      html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
      html = html.replace(/___(.+?)___/g, '<strong><em>$1</em></strong>');
      html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');

      // 5. 斜体（*text* 或 _text_）
      html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
      html = html.replace(/_(.+?)_/g, '<em>$1</em>');

      // 6. 删除线（~~text~~）
      html = html.replace(/~~(.+?)~~/g, '<del>$1</del>');

      // 7. 链接（[text](url)）
      html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');

      // 8. 图片（![alt](url)）
      html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" />');

      // 9. 无序列表（- item 或 * item）
      html = html.replace(/^[\s]*[-*]\s+(.*)$/gm, '<li class="markdown-list-item">$1</li>');
      // 将连续的 li 包装在 ul 中
      html = html.replace(/(<li class="markdown-list-item">.*<\/li>\n?)+/g, (match) => {
        return `<ul>${match}</ul>`;
      });

      // 10. 有序列表（1. item）
      html = html.replace(/^[\s]*\d+\.\s+(.*)$/gm, '<li class="markdown-list-item">$1</li>');
      // 将连续的 li 包装在 ol 中（如果前面没有 ul）
      html = html.replace(/(?<!<ul>)(<li class="markdown-list-item">.*<\/li>\n?)+(?![<\s]*\/ul>)/g, (match) => {
        return `<ol>${match}</ol>`;
      });

      // 11. 引用块（> text）
      html = html.replace(/^>\s+(.*)$/gm, '<blockquote>$1</blockquote>');
      // 合并连续的 blockquote
      html = html.replace(/(<blockquote>.*<\/blockquote>\n?)+/g, (match) => {
        return `<blockquote>${match.replace(/<\/blockquote>\n?<blockquote>/g, '<br>').replace(/<\/blockquote><blockquote>/g, '<br>').replace(/<blockquote>|<\/blockquote>/g, '')}</blockquote>`;
      });

      // 12. 水平线（--- 或 *** 或 ___）
      html = html.replace(/^(-{3,}|_{3,}|\*{3,})$/gm, '<hr />');

      // 13. 段落（双换行）
      html = html.replace(/\n\n+/g, '</p><p class="markdown-paragraph">');

      // 14. 单换行转换为 <br>
      html = html.replace(/\n/g, '<br />');

      // 15. 包装在段落标签中（如果还没有被其他标签包装）
      if (!html.startsWith('<')) {
        html = `<p class="markdown-paragraph">${html}</p>`;
      }

      return html;
    } catch (error) {
      console.warn('Markdown 渲染失败:', error);
      return escapeHtml(markdown);
    }
  };

  /**
   * 函数级注释：在 HTML 中高亮关键词
   * 内部逻辑：
   *   1. 使用 DOMParser 解析 HTML
   *   2. 使用 TreeWalker 遍历文本节点
   *   3. 对匹配的关键词用 <mark class="search-highlight"> 包裹
   * 参数：
   *   html - HTML 字符串
   *   keywords - 关键词数组
   * 返回值：高亮后的 HTML 字符串
   */
  const highlightKeywords = (html: string, keywords: string[]): string => {
    // Guard Clause：没有关键词时直接返回原 HTML
    if (!keywords || keywords.length === 0) {
      return html;
    }

    try {
      // 内部变量：使用 DOMParser 解析 HTML
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, 'text/html');

      // 内部逻辑：遍历每个关键词
      keywords.forEach(keyword => {
        if (!keyword.trim()) return;

        // 内部逻辑：创建 TreeWalker 遍历文本节点
        const walker = document.createTreeWalker(
          doc.body,
          NodeFilter.SHOW_TEXT,
          {
            // 内部逻辑：跳过代码块中的文本
            acceptNode: (node: Node) => {
              // 检查是否在代码块内
              const parent = node.parentElement;
              if (parent && (
                parent.tagName === 'CODE' ||
                parent.tagName === 'PRE' ||
                parent.classList.contains('markdown-code-block') ||
                parent.classList.contains('markdown-code-inline')
              )) {
                return NodeFilter.FILTER_REJECT;
              }
              return NodeFilter.FILTER_ACCEPT;
            }
          }
        );

        // 内部变量：存储需要替换的节点
        const nodesToReplace: Array<{ parent: ChildNode | null; node: ChildNode; text: string }> = [];

        let node: ChildNode | null;
        while (node = walker.nextNode()) {
          const text = node.nodeValue || '';
          // 内部逻辑：检查文本是否包含关键词（不区分大小写）
          if (text.toLowerCase().includes(keyword.toLowerCase())) {
            nodesToReplace.push({
              parent: node.parentNode,
              node,
              text
            });
          }
        }

        // 内部逻辑：替换匹配的文本节点
        nodesToReplace.forEach(({ parent, node, text }) => {
          if (!parent) return;

          // 内部变量：构建正则表达式（不区分大小写，全局匹配）
          const regex = new RegExp(`(${escapeRegExp(keyword)})`, 'gi');

          // 内部逻辑：分割文本并创建带高亮的片段
          const fragment = document.createDocumentFragment();
          let lastIndex = 0;
          let match: RegExpExecArray | null;

          while ((match = regex.exec(text)) !== null) {
            // 内部逻辑：添加匹配前的文本
            if (match.index > lastIndex) {
              fragment.appendChild(document.createTextNode(text.slice(lastIndex, match.index)));
            }

            // 内部逻辑：创建高亮元素
            const mark = document.createElement('mark');
            mark.className = 'search-highlight';
            mark.textContent = match[1];
            fragment.appendChild(mark);

            lastIndex = regex.lastIndex;
          }

          // 内部逻辑：添加剩余文本
          if (lastIndex < text.length) {
            fragment.appendChild(document.createTextNode(text.slice(lastIndex)));
          }

          // 内部逻辑：替换原节点
          parent.replaceChild(fragment, node);
        });
      });

      return doc.body.innerHTML;
    } catch (error) {
      console.warn('关键词高亮失败:', error);
      return html;
    }
  };

  /**
   * 函数级注释：处理内容渲染
   * 内部逻辑：先渲染 Markdown，再高亮关键词
   * 返回值：Promise<void>
   */
  const processContent = async (): Promise<void> => {
    setIsRendering(true);

    try {
      // 内部逻辑：使用 setTimeout 让 UI 有机会显示加载状态
      await new Promise(resolve => setTimeout(resolve, 0));

      // 内部变量：解析搜索关键词（按空格分割）
      const keywords = query.trim().split(/\s+/).filter(Boolean);

      // 内部逻辑：先渲染 Markdown
      let html = renderMarkdown(content);

      // 内部逻辑：再高亮关键词
      if (keywords.length > 0) {
        html = highlightKeywords(html, keywords);
      }

      setRenderedHtml(html);
      setIsRendering(false);
    } catch (error) {
      console.error('内容处理失败:', error);
      setIsRendering(false);
    }
  };

  // 内部逻辑：当内容或查询变化时重新处理
  React.useEffect(() => {
    processContent();
  }, [content, query]);

  // 内部逻辑：渲染中显示加载状态
  if (isRendering) {
    return (
      <div className="search-content-loading">
        <span>渲染中...</span>
      </div>
    );
  }

  // 内部逻辑：使用 dangerouslySetInnerHTML 渲染 HTML
  return (
    <div
      className="search-result-rendered-content"
      dangerouslySetInnerHTML={{ __html: renderedHtml }}
    />
  );
};
