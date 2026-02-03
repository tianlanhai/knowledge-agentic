/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：useKeyboardShortcuts Hook单元测试
 * 内部逻辑：测试键盘快捷键的功能
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useKeyboardShortcuts, SHORTCUTS } from './useKeyboardShortcuts';

  /**
   * 内部函数：解析快捷键
   * 参数：shortcut - 快捷键字符串
   * 返回值：测试匹配器函数
   */
  function parseShortcut(shortcut: string) {
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
  }

describe('useKeyboardShortcuts Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  /**
   * 测试Ctrl+K快捷键
   */
  it('应该匹配Ctrl+K', () => {
    const mockAction = vi.fn();
    const shortcuts = [
      { key: 'ctrl+k', action: mockAction },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts));

    const event = new KeyboardEvent('keydown', {
      key: 'k',
      ctrlKey: true,
      metaKey: false,
      altKey: false,
      shiftKey: false,
    } as any);

    act(() => {
      document.dispatchEvent(event);
    });

    expect(mockAction).toHaveBeenCalled();
  });

  /**
   * 测试Ctrl+/快捷键
   */
  it('应该匹配Ctrl+/', () => {
    const mockAction = vi.fn();
    const shortcuts = [
      { key: 'ctrl+/', action: mockAction },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts));

    const event = new KeyboardEvent('keydown', {
      key: '/',
      ctrlKey: true,
      metaKey: false,
      altKey: false,
      shiftKey: false,
    } as any);

    act(() => {
      document.dispatchEvent(event);
    });

    expect(mockAction).toHaveBeenCalled();
  });

  /**
   * 测试Ctrl+Shift+T快捷键
   */
  it('应该匹配Ctrl+Shift+T', () => {
    const mockAction = vi.fn();
    const shortcuts = [
      { key: 'ctrl+shift+t', action: mockAction },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts));

    const event = new KeyboardEvent('keydown', {
      key: 't',
      ctrlKey: true,
      metaKey: false,
      altKey: false,
      shiftKey: true,
    } as any);

    act(() => {
      document.dispatchEvent(event);
    });

    expect(mockAction).toHaveBeenCalled();
  });

  /**
   * 测试Ctrl+B快捷键
   */
  it('应该匹配Ctrl+B', () => {
    const mockAction = vi.fn();
    const shortcuts = [
      { key: 'ctrl+b', action: mockAction },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts));

    const event = new KeyboardEvent('keydown', {
      key: 'b',
      ctrlKey: true,
      metaKey: false,
      altKey: false,
      shiftKey: false,
    } as any);

    act(() => {
      document.dispatchEvent(event);
    });

    expect(mockAction).toHaveBeenCalled();
  });

  /**
   * 测试Ctrl+Shift+L快捷键
   */
  it('应该匹配Ctrl+Shift+L', () => {
    const mockAction = vi.fn();
    const shortcuts = [
      { key: 'ctrl+shift+l', action: mockAction },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts));

    const event = new KeyboardEvent('keydown', {
      key: 'l',
      ctrlKey: true,
      metaKey: false,
      altKey: false,
      shiftKey: true,
    } as any);

    act(() => {
      document.dispatchEvent(event);
    });

    expect(mockAction).toHaveBeenCalled();
  });

  /**
   * 测试不匹配的快捷键
   */
  it('应该不匹配不正确的快捷键', () => {
    const mockAction = vi.fn();
    const shortcuts = [
      { key: 'ctrl+k', action: mockAction },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts));

    const event = new KeyboardEvent('keydown', {
      key: 'k',
      ctrlKey: false, // 没有Ctrl键
      metaKey: false,
      altKey: false,
      shiftKey: false,
    } as any);

    act(() => {
      document.dispatchEvent(event);
    });

    expect(mockAction).not.toHaveBeenCalled();
  });

  /**
   * 测试多个快捷键
   */
  it('应该支持多个快捷键', () => {
    const mockSearch = vi.fn();
    const mockHelp = vi.fn();
    const shortcuts = [
      { key: 'ctrl+k', action: mockSearch },
      { key: 'ctrl+/', action: mockHelp },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts));

    // 触发搜索快捷键
    const searchEvent = new KeyboardEvent('keydown', {
      key: 'k',
      ctrlKey: true,
      metaKey: false,
    altKey: false,
      shiftKey: false,
    } as any);

    act(() => {
      document.dispatchEvent(searchEvent);
    });

    expect(mockSearch).toHaveBeenCalled();
    expect(mockHelp).not.toHaveBeenCalled();

    // 重置mock
    vi.clearAllMocks();
    mockSearch.mockImplementation(() => {});
    mockHelp.mockImplementation(() => {});

    // 触发帮助快捷键
    const helpEvent = new KeyboardEvent('keydown', {
      key: '/',
      ctrlKey: true,
      metaKey: false,
      altKey: false,
      shiftKey: false,
    } as any);

    act(() => {
      document.dispatchEvent(helpEvent);
    });

    expect(mockHelp).toHaveBeenCalled();
  });

  /**
   * 测试preventDefault选项
   */
  it('应该阻止默认行为', () => {
    const mockAction = vi.fn();
    const mockPreventDefault = vi.fn();
    const shortcuts = [
      {
        key: 'ctrl+k',
        action: mockAction,
        preventDefault: true,
      },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts));

    const event = new KeyboardEvent('keydown', {
      key: 'k',
      ctrlKey: true,
      metaKey: false,
      altKey: false,
      shiftKey: false,
    } as any);

    // 覆盖preventDefault方法
    event.preventDefault = mockPreventDefault;

    act(() => {
      document.dispatchEvent(event);
    });

    expect(mockPreventDefault).toHaveBeenCalled();
  });

  /**
   * 测试不阻止默认行为
   */
  it('应该不阻止默认行为', () => {
    const mockAction = vi.fn();
    const mockPreventDefault = vi.fn();
    const shortcuts = [
      {
        key: 'ctrl+k',
        action: mockAction,
        preventDefault: false,
      },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts));

    const event = new KeyboardEvent('keydown', {
      key: 'k',
      ctrlKey: true,
      metaKey: false,
      altKey: false,
      shiftKey: false,
    } as any);

    // 覆盖preventDefault方法
    event.preventDefault = mockPreventDefault;

    act(() => {
      document.dispatchEvent(event);
    });

    expect(mockPreventDefault).not.toHaveBeenCalled();
  });

  /**
   * 测试预定义快捷键常量
   */
  it('应该导出预定义快捷键常量', () => {
    expect(SHORTCUTS.SEARCH).toBe('ctrl+k');
    expect(SHORTCUTS.HELP).toBe('ctrl+/');
    expect(SHORTCUTS.TOGGLE_THEME).toBe('ctrl+shift+t');
    expect(SHORTCUTS.TOGGLE_SIDEBAR).toBe('ctrl+b');
    expect(SHORTCUTS.CLEAR_CHAT).toBe('ctrl+shift+l');
  });

  /**
   * 测试大小写不敏感
   */
  it('应该支持大小写不敏感', () => {
    const mockAction = vi.fn();
    const shortcuts = [
      { key: 'ctrl+k', action: mockAction },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts));

    const event = new KeyboardEvent('keydown', {
      key: 'K', // 大写K
      ctrlKey: true,
      metaKey: false,
      altKey: false,
      shiftKey: false,
    } as any);

    act(() => {
      document.dispatchEvent(event);
    });

    expect(mockAction).toHaveBeenCalled();
  });

  /**
   * 测试Meta键（Mac的Command键）
   * 内部逻辑：验证Mac系统的Command键可以作为Ctrl键使用
   */
  it('应该匹配Meta键（Mac Command键）', () => {
    const mockAction = vi.fn();
    const shortcuts = [
      { key: 'ctrl+k', action: mockAction },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts));

    const event = new KeyboardEvent('keydown', {
      key: 'k',
      ctrlKey: false,
      metaKey: true, // Mac的Command键
      altKey: false,
      shiftKey: false,
    } as any);

    act(() => {
      document.dispatchEvent(event);
    });

    expect(mockAction).toHaveBeenCalled();
  });

  /**
   * 测试Alt修饰键
   * 内部逻辑：验证Alt键修饰符能正确识别
   */
  it('应该匹配Alt+K快捷键', () => {
    const mockAction = vi.fn();
    const shortcuts = [
      { key: 'alt+k', action: mockAction },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts));

    const event = new KeyboardEvent('keydown', {
      key: 'k',
      ctrlKey: false,
      metaKey: false,
      altKey: true,
      shiftKey: false,
    } as any);

    act(() => {
      document.dispatchEvent(event);
    });

    expect(mockAction).toHaveBeenCalled();
  });

  /**
   * 测试不匹配Alt键
   * 内部逻辑：验证Alt键修饰符检查
   */
  it('应该不匹配缺少Alt键的快捷键', () => {
    const mockAction = vi.fn();
    const shortcuts = [
      { key: 'alt+k', action: mockAction },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts));

    const event = new KeyboardEvent('keydown', {
      key: 'k',
      ctrlKey: false,
      metaKey: false,
      altKey: false, // 缺少Alt键
      shiftKey: false,
    } as any);

    act(() => {
      document.dispatchEvent(event);
    });

    expect(mockAction).not.toHaveBeenCalled();
  });

  /**
   * 测试Shift修饰键
   * 内部逻辑：验证Shift键修饰符能正确识别
   */
  it('应该匹配Shift+K快捷键', () => {
    const mockAction = vi.fn();
    const shortcuts = [
      { key: 'shift+k', action: mockAction },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts));

    const event = new KeyboardEvent('keydown', {
      key: 'k',
      ctrlKey: false,
      metaKey: false,
      altKey: false,
      shiftKey: true,
    } as any);

    act(() => {
      document.dispatchEvent(event);
    });

    expect(mockAction).toHaveBeenCalled();
  });

  /**
   * 测试不匹配Shift键
   * 内部逻辑：验证Shift键修饰符检查
   */
  it('应该不匹配缺少Shift键的快捷键', () => {
    const mockAction = vi.fn();
    const shortcuts = [
      { key: 'shift+k', action: mockAction },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts));

    const event = new KeyboardEvent('keydown', {
      key: 'k',
      ctrlKey: false,
      metaKey: false,
      altKey: false,
      shiftKey: false, // 缺少Shift键
    } as any);

    act(() => {
      document.dispatchEvent(event);
    });

    expect(mockAction).not.toHaveBeenCalled();
  });

  /**
   * 测试组合修饰键
   * 内部逻辑：验证Ctrl+Shift+K组合键
   */
  it('应该匹配Ctrl+Shift+K组合键', () => {
    const mockAction = vi.fn();
    const shortcuts = [
      { key: 'ctrl+shift+k', action: mockAction },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts));

    const event = new KeyboardEvent('keydown', {
      key: 'k',
      ctrlKey: true,
      metaKey: false,
      altKey: false,
      shiftKey: true,
    } as any);

    act(() => {
      document.dispatchEvent(event);
    });

    expect(mockAction).toHaveBeenCalled();
  });

  /**
   * 测试组合修饰键不完整时不匹配
   * 内部逻辑：验证必须满足所有修饰键
   */
  it('应该不匹配部分修饰键', () => {
    const mockAction = vi.fn();
    const shortcuts = [
      { key: 'ctrl+shift+k', action: mockAction },
    ];

    renderHook(() => useKeyboardShortcuts(shortcuts));

    // 只有Ctrl没有Shift
    const event = new KeyboardEvent('keydown', {
      key: 'k',
      ctrlKey: true,
      metaKey: false,
      altKey: false,
      shiftKey: false,
    } as any);

    act(() => {
      document.dispatchEvent(event);
    });

    expect(mockAction).not.toHaveBeenCalled();
  });

  /**
   * 测试清理函数
   * 内部逻辑：验证组件卸载时移除事件监听器
   */
  it('应该在卸载时清理事件监听器', () => {
    const removeEventListenerSpy = vi.spyOn(document, 'removeEventListener');
    const mockAction = vi.fn();
    const shortcuts = [
      { key: 'ctrl+k', action: mockAction },
    ];

    const { unmount } = renderHook(() => useKeyboardShortcuts(shortcuts));

    unmount();

    // 验证removeEventListener被调用
    expect(removeEventListenerSpy).toHaveBeenCalledWith('keydown', expect.any(Function));
    removeEventListenerSpy.mockRestore();
  });
});
