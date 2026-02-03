/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 侧边栏导航组件
 * Flat Design 风格 - 干净、专业
 */
import { Layout, Tooltip } from 'antd';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  BookOutlined,
  MessageOutlined,
  FileTextOutlined,
  SearchOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  InfoCircleOutlined,
  UnorderedListOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import './Sidebar.css';

const { Sider } = Layout;

/**
 * 侧边栏属性接口
 */
interface AppSidebarProps {
  /** 侧边栏是否折叠 */
  collapsed: boolean;
  /** 切换折叠状态的回调函数 */
  onToggle: () => void;
}

/**
 * 菜单项配置
 * 包含路由路径、图标、标题和提示信息
 */
const menuItems = [
  {
    key: '/knowledge',
    icon: <BookOutlined />,
    label: '知识管理',
    tooltip: '管理文档和知识库',
  },
  {
    key: '/tasks',
    icon: <UnorderedListOutlined />,
    label: '任务列表',
    tooltip: '查看所有处理任务',
  },
  {
    key: '/documents',
    icon: <FileTextOutlined />,
    label: '文档列表',
    tooltip: '查看所有已处理的文档',
  },
  {
    key: '/chat',
    icon: <MessageOutlined />,
    label: '智能问答',
    tooltip: '与AI助手对话',
  },
  {
    key: '/analysis',
    icon: <MenuFoldOutlined />,
    label: '文档分析',
    tooltip: '总结和对比文档',
  },
  {
    key: '/search',
    icon: <SearchOutlined />,
    label: '语义搜索',
    tooltip: '搜索知识库内容',
  },
  {
    key: '/model-config',
    icon: <SettingOutlined />,
    label: '模型配置',
    tooltip: '管理LLM和Embedding配置',
  },
] as const;

/**
 * 菜单项组件属性接口
 */
interface MenuItemProps {
  /** 菜单项数据 */
  item: typeof menuItems[number];
  /** 是否激活 */
  isActive: boolean;
  /** 侧边栏是否折叠 */
  collapsed: boolean;
  /** 点击回调函数 */
  onClick: () => void;
}

/**
 * 菜单项组件
 * 内部变量：item - 菜单项配置，isActive - 激活状态，collapsed - 折叠状态
 * 内部逻辑：根据激活状态应用不同样式
 * 返回值：JSX.Element
 */
const MenuItem = ({ item, isActive, collapsed, onClick }: MenuItemProps) => {
  const content = (
    <div
      role="menuitem"
      tabIndex={0}
      aria-label={item.label}
      aria-current={isActive ? 'page' : undefined}
      className={`sidebar-menu-item ${isActive ? 'active' : ''}`}
      onClick={onClick}
      onKeyDown={(e) => {
        // 内部逻辑：支持键盘操作（Enter或空格键触发）
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      }}
    >
      <span className="menu-icon">{item.icon}</span>
      {!collapsed && <span className="menu-label">{item.label}</span>}
    </div>
  );

  return collapsed ? (
    <Tooltip title={item.tooltip} placement="right" arrow={false}>
      {content}
    </Tooltip>
  ) : (
    content
  );
};

/**
 * 应用侧边栏组件
 * 内部变量：collapsed - 折叠状态
 * 内部逻辑：渲染菜单项并处理导航
 * 返回值：JSX.Element
 */
export const AppSidebar = ({ collapsed, onToggle }: AppSidebarProps) => {
  // 内部变量：获取当前路由位置
  const location = useLocation();
  // 内部变量：获取导航函数
  const navigate = useNavigate();

  /**
   * 处理菜单项点击
   * 导航到对应路由
   */
  const handleMenuClick = (path: string) => {
    navigate(path);
  };

  return (
    <div className="sidebar">
      {/* 侧边栏头部 */}
      <div className="sidebar-header">
        {!collapsed ? (
          <div className="sidebar-header-content">
            <div className="sidebar-logo">
              <svg
                width="18"
                height="18"
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
            <span className="sidebar-title">导航菜单</span>
            <button
              className="collapse-btn"
              onClick={onToggle}
              aria-label="折叠侧边栏"
            >
              <MenuFoldOutlined />
            </button>
          </div>
        ) : (
          <div className="sidebar-header-collapsed">
            <div className="sidebar-logo">
              <svg
                width="18"
                height="18"
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
          </div>
        )}
      </div>

      {/* 菜单项列表 */}
      <nav className="sidebar-nav" role="navigation">
        {menuItems.map((item) => (
          <MenuItem
            key={item.key}
            item={item}
            isActive={location.pathname === item.key}
            collapsed={collapsed}
            onClick={() => handleMenuClick(item.key)}
          />
        ))}
      </nav>

      {/* 侧边栏底部 */}
      <div className="sidebar-footer">
        {!collapsed ? (
          <div className="sidebar-footer-content">
            <div className="sidebar-version">
              <span className="version-text">知识库智能体</span>
              <span className="version-number">v1.0.0</span>
            </div>
          </div>
        ) : (
          <Tooltip title="知识库智能体 v1.0.0" placement="right" arrow={false}>
            <div className="sidebar-footer-collapsed">
              <InfoCircleOutlined />
            </div>
          </Tooltip>
        )}
      </div>
    </div>
  );
};
