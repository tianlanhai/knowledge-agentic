/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 全局布局组件
 * Flat Design 风格 - 干净、专业的页面布局
 */
import { Layout } from 'antd';
import { Outlet } from 'react-router-dom';
import { AppHeader } from './Header';
import { AppSidebar } from './Sidebar';
import { AppFooter } from './Footer';
import { useState, useEffect } from 'react';
import './Layout.css';

const { Content, Sider } = Layout;

/**
 * 应用主布局组件
 * 内部变量：collapsed - 侧边栏折叠状态，isMobile - 移动端标识
 * 内部逻辑：响应式处理侧边栏显示
 * 返回值：JSX.Element
 */
export const AppLayout = () => {
  // 内部变量：侧边栏折叠状态
  const [collapsed, setCollapsed] = useState(false);
  // 内部变量：是否为移动端
  const [isMobile, setIsMobile] = useState(false);

  /**
   * 响应式处理：移动端自动收起侧边栏
   * 内部逻辑：监听窗口大小变化，自动调整侧边栏状态
   */
  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (mobile) {
        setCollapsed(true);
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  /**
   * 切换侧边栏折叠状态
   * 内部逻辑：反转折叠状态
   */
  const toggleCollapsed = () => {
    setCollapsed(!collapsed);
  };

  return (
    <Layout className="app-layout">
      {/* 侧边栏 */}
      {!isMobile && (
        <Sider
          collapsible
          collapsed={collapsed}
          onCollapse={toggleCollapsed}
          width={240}
          collapsedWidth={72}
          className="app-sider"
          style={{
            overflow: 'hidden',
          }}
        >
          <AppSidebar collapsed={collapsed} onToggle={toggleCollapsed} />
        </Sider>
      )}

      {/* 主内容区域 */}
      <Layout className="app-main-layout">
        {/* 顶部导航栏 */}
        <AppHeader />

        {/* 内容区 */}
        <Content className="app-content">
          <Outlet />
        </Content>

        {/* 页脚 */}
        <AppFooter />
      </Layout>
    </Layout>
  );
};
