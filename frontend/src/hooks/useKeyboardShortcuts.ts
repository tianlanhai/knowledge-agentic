/**
 * 上海宇羲伏天智能科技有限公司出品
 *
/**
 * 文件级注释：键盘快捷钩子
 * 内部逻辑：提供全局键盘快捷键支持，如 Ctrl+K 搜索
 */

import { useEffect } from 'react';

/**
 * 接口级注释：快捷键配置接口
 * 属性：
 *   key: 快捷键组合（如 'ctrl+k'）
 *   action: 触发函数
 *   preventDefault: 是否阻止默认行为
 */
interface KeyboardShortcut {
  key: string;
  action: () => void;
  preventDefault?: boolean;
}

/**
 * 函数级注释：使用键盘快捷键
 * 内部逻辑：监听键盘事件，匹配快捷键并触发对应的动作
 * 参数：shortcuts - 快捷键配置数组
 * 返回值：void
 */
export const useKeyboardShortcuts = (shortcuts: KeyboardShortcut[]) => {
  /**
   * 解析快捷键
   * 将字符串格式的快捷键转换为按键对象
   * 参数：shortcut - 快捷键字符串（如 'ctrl+k'）
   * 返回值：event - 匹配的按键事件
   */
  const parseShortcut = (shortcut: string) => {
    return (event: KeyboardEvent): boolean => {
      const parts = shortcut.toLowerCase().split('+');
      const [modifiers, key] = [parts.slice(0, -1), parts[parts.length - 1]];

      // 检查修饰键
      if (modifiers.includes('ctrl') && !event.ctrlKey && !event.metaKey) {
        return false;
      }
      if (modifiers.includes('alt') && !event.altKey) {
        return false;
      }
      if (modifiers.includes('shift') && !event.shiftKey) {
        return false;
      }

      // 检查主键
      return event.key.toLowerCase() === key;
    };
  };

  // 内部逻辑：添加键盘事件监听器
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // 内部变量：遍历所有快捷键配置
      for (const shortcut of shortcuts) {
        // 内部变量：解析当前快捷键
        const matcher = parseShortcut(shortcut.key);

        // 内部逻辑：如果匹配成功，执行对应动作
        if (matcher(event)) {
          // 内部逻辑：如果需要阻止默认行为
          if (shortcut.preventDefault !== false) {
            event.preventDefault();
          }

          // 内部逻辑：执行动作
          shortcut.action();
          break;
        }
      }
    };

    // 内部逻辑：添加键盘事件监听
    document.addEventListener('keydown', handleKeyDown);

    // 内部逻辑：清理函数 - 移除监听器
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [shortcuts]);
};

/**
 * 预定义快捷键集合
 */
export const SHORTCUTS = {
  // 搜索快捷键
  SEARCH: 'ctrl+k',

  // 帮助快捷键
  HELP: 'ctrl+/',

  // 主题切换快捷键
  TOGGLE_THEME: 'ctrl+shift+t',

  // 侧边栏切换快捷键
  TOGGLE_SIDEBAR: 'ctrl+b',

  // 清除对话框快捷键
  CLEAR_CHAT: 'ctrl+shift+l',
};
