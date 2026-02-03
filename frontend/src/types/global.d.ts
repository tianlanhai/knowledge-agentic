/**
 * 上海宇羲伏天智能科技有限公司出品
 *
/**
 * 文件级注释：全局类型声明
 * 内部逻辑：为window对象扩展第三方库类型
 */

declare global {
  interface Window {
    /**
     * MarkdownIt库实例
     * 内部逻辑：全局Markdown解析器实例
     */
    markdownit: any;
  }
}

export {};
