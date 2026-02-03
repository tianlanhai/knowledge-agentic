/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：UI状态管理Store
 * 内部逻辑：使用Zustand管理全局UI状态，包括主题、侧边栏等
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

/**
 * 枚举级注释：主题类型
 */
export type Theme = 'dark' | 'light';

/**
 * 接口级注释：UI状态接口
 * 属性：
 *   theme: 当前主题（深色/浅色）
 *   sidebarCollapsed: 侧边栏是否折叠
 *   setTheme: 设置主题
 *   toggleTheme: 切换主题
 *   setSidebarCollapsed: 设置侧边栏折叠状态
 *   toggleSidebar: 切换侧边栏
 */
export interface UIState {
  // 主题相关
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;

  // 侧边栏相关
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleSidebar: () => void;
}

/**
 * 变量：UI状态Store（持久化到localStorage）
 */
export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      // 初始状态
      theme: 'dark',
      sidebarCollapsed: false,

      // 主题操作
      setTheme: (theme) => set({ theme }),
      toggleTheme: () => set((state) => ({ theme: state.theme === 'dark' ? 'light' : 'dark' })),

      // 侧边栏操作
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
      toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
    }),
    {
      name: 'ui-storage', // localStorage key
      partialize: (state) => ({
        theme: state.theme,
        sidebarCollapsed: state.sidebarCollapsed,
      }),
    }
  )
);
