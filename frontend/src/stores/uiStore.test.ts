/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：uiStore单元测试
 * 内部逻辑：测试UI状态管理
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { useUIStore } from './uiStore';
import type { Theme } from './uiStore';

/**
 * 内部变量：mock的localStorage
 */
const mockLocalStorage: Record<string, string> = {};

/**
 * 内部函数：mock localStorage
 */
const createMockLocalStorage = () => ({
  getItem: (key: string) => mockLocalStorage[key] || null,
  setItem: (key: string, value: string) => {
    mockLocalStorage[key] = value;
  },
  removeItem: (key: string) => {
    delete mockLocalStorage[key];
  },
  clear: () => {
    Object.keys(mockLocalStorage).forEach((key) => delete mockLocalStorage[key]);
  },
});

describe('uiStore', () => {
  /**
   * 测试初始状态
   */
  it('应该有初始状态', () => {
    const state = useUIStore.getState();

    expect(state.theme).toBeDefined();
    expect(typeof state.sidebarCollapsed).toBe('boolean');
  });

  /**
   * 测试setTheme功能
   */
  it('应该设置主题', () => {
    useUIStore.getState().setTheme('light');

    const state = useUIStore.getState();

    expect(state.theme).toBe('light');
  });

  /**
   * 测试toggleTheme功能
   */
  it('应该切换主题', () => {
    // 设置初始主题
    useUIStore.getState().setTheme('dark');
    expect(useUIStore.getState().theme).toBe('dark');

    // 切换到light
    useUIStore.getState().toggleTheme();

    const state1 = useUIStore.getState();
    expect(state1.theme).toBe('light');

    // 切换回dark
    useUIStore.getState().toggleTheme();

    const state2 = useUIStore.getState();
    expect(state2.theme).toBe('dark');
  });

  /**
   * 测试setSidebarCollapsed功能
   */
  it('应该设置侧边栏折叠状态', () => {
    useUIStore.getState().setSidebarCollapsed(true);

    const state1 = useUIStore.getState();
    expect(state1.sidebarCollapsed).toBe(true);

    useUIStore.getState().setSidebarCollapsed(false);

    const state2 = useUIStore.getState();
    expect(state2.sidebarCollapsed).toBe(false);
  });

  /**
   * 测试toggleSidebar功能
   */
  it('应该切换侧边栏状态', () => {
    // 初始状态是展开的
    expect(useUIStore.getState().sidebarCollapsed).toBe(false);

    // 折叠侧边栏
    useUIStore.getState().toggleSidebar();

    const state1 = useUIStore.getState();
    expect(state1.sidebarCollapsed).toBe(true);

    // 展开侧边栏
    useUIStore.getState().toggleSidebar();

    const state2 = useUIStore.getState();
    expect(state2.sidebarCollapsed).toBe(false);
  });

  /**
   * 测试多次切换主题
   */
  it('应该支持多次切换主题', () => {
    const themes: Theme[] = ['dark', 'light', 'dark', 'light'];

    themes.forEach((theme, index) => {
      useUIStore.getState().setTheme(theme);
      expect(useUIStore.getState().theme).toBe(theme);
    });
  });

  /**
   * 测试多次切换侧边栏
   */
  it('应该支持多次切换侧边栏', () => {
    const states = [true, false, true, false, true];

    states.forEach((collapsed, index) => {
      useUIStore.getState().toggleSidebar();
      expect(useUIStore.getState().sidebarCollapsed).toBe(collapsed);
    });
  });
});
