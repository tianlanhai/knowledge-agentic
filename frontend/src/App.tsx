/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：应用根组件
 * 内部逻辑：初始化主题并渲染路由
 */

import { RouterProvider } from 'react-router-dom';
import { router } from './router';
import { useUIStore } from './stores/uiStore';
import { useEffect } from 'react';
import 'antd/dist/reset.css';
import './index.css';

/**
 * 函数级注释：应用根组件
 * 内部逻辑：初始化主题并应用
 * 返回值：JSX.Element
 */
function App() {
  // 内部变量：从store中获取当前主题
  const { theme } = useUIStore();

  // 内部逻辑：将主题应用到根元素上
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  return <RouterProvider router={router} />;
}

export default App;
