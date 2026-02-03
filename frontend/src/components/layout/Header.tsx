/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 顶部导航栏组件
 * Flat Design 风格 - 干净、专业、易维护
 */
import { Layout, Dropdown, Avatar, Button, Badge } from 'antd';
import { useLocation } from 'react-router-dom';
import {
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  SunOutlined,
  MoonOutlined,
} from '@ant-design/icons';
import { useUIStore } from '../../stores/uiStore';
import './Header.css';

const { Header } = Layout;

/**
 * 文件级注释：用户下拉菜单配置
 * 包含个人中心、系统设置和退出登录选项
 */
const userMenuItems = [
  {
    key: 'profile',
    icon: <UserOutlined />,
    label: '个人中心',
  },
  {
    key: 'settings',
    icon: <SettingOutlined />,
    label: '系统设置',
  },
  {
    type: 'divider' as const,
  },
  {
    key: 'logout',
    icon: <LogoutOutlined />,
    label: '退出登录',
    danger: true,
  },
];

/**
 * 页面标题映射
 * 根据路由路径返回对应的页面标题
 */
const PAGE_TITLE_MAP: Record<string, string> = {
  '/knowledge': '知识管理',
  '/chat': '智能问答',
  '/analysis': '文档分析',
  '/search': '语义搜索',
};

/**
 * 函数级注释：获取页面标题
 * 参数说明：pathname - 当前路由路径
 * 返回值：页面标题字符串
 */
const getPageTitle = (pathname: string): string => {
  return PAGE_TITLE_MAP[pathname] || '知识库智能体';
};

/**
 * 主题切换按钮组件
 * 内部变量：theme - 当前主题状态
 * 内部逻辑：点击时切换主题
 * 返回值：JSX.Element
 */
const ThemeToggle = () => {
  // 内部变量：从 store 获取主题状态和切换函数
  const { theme, toggleTheme } = useUIStore();

  return (
    <Button
      type="text"
      icon={theme === 'dark' ? <SunOutlined /> : <MoonOutlined />}
      onClick={toggleTheme}
      className="header-action-btn"
    >
      {theme === 'dark' ? '浅色' : '深色'}
    </Button>
  );
};

/**
 * 应用顶部导航栏组件
 * 包含 Logo、页面标题、系统状态和用户菜单
 */
export const AppHeader = () => {
  // 内部变量：获取当前路由位置
  const location = useLocation();
  // 内部变量：计算当前页面标题
  const pageTitle = getPageTitle(location.pathname);

  return (
    <Header className="app-header">
      {/* 左侧：Logo 和页面标题 */}
      <div className="header-left">
        {/* Logo 图标 */}
        <div className="logo-icon">
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M12 2L2 7l10 5 10-5-10-5z" />
            <path d="M2 17l10 5 10-5" />
            <path d="M2 12l10 5 10-5" />
          </svg>
        </div>

        {/* 应用名称 */}
        <h1 className="app-title">知识库智能体</h1>

        {/* 分隔线 */}
        <div className="header-divider" />

        {/* 页面标题 */}
        <h2 className="page-title">{pageTitle}</h2>
      </div>

      {/* 右侧：状态、主题切换和用户菜单 */}
      <div className="header-right">
        {/* 系统状态指示器 */}
        <div className="status-indicator">
          <span className="status-dot" />
          <span className="status-text">系统运行中</span>
        </div>

        {/* 主题切换按钮 */}
        <ThemeToggle />

        {/* 用户下拉菜单 */}
        <Dropdown
          menu={{ items: userMenuItems }}
          placement="bottomRight"
          arrow
        >
          <Avatar
            icon={<UserOutlined />}
            className="user-avatar cursor-pointer"
            size={40}
          />
        </Dropdown>
      </div>
    </Header>
  );
};
