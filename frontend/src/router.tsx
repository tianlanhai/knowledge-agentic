/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：路由配置
 * 内部逻辑：定义应用的路由结构和页面组件映射
 */

import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AppLayout } from './components/layout/Layout';
import { KnowledgeManagement } from './components/features/KnowledgeManagement';
import { ChatInterface } from './components/features/Chat';
import { TaskListPage } from './components/features/KnowledgeManagement/TaskListPage';
import { DocumentListPage } from './components/features/KnowledgeManagement/DocumentListPage';
import { DocumentAnalysis } from './components/features/DocumentAnalysis';
import { SemanticSearch } from './components/features/Search';
import { ModelConfigPage } from './components/features/ModelConfig';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <Navigate to="/knowledge" replace />,
      },
      {
        path: 'knowledge',
        element: <KnowledgeManagement />,
      },
      {
        path: 'tasks',
        element: <TaskListPage />,
      },
      {
        path: 'documents',
        element: <DocumentListPage />,
      },
      {
        path: 'chat',
        element: <ChatInterface />,
      },
      {
        path: 'analysis',
        element: <DocumentAnalysis />,
      },
      {
        path: 'search',
        element: <SemanticSearch />,
      },
      {
        path: 'model-config',
        element: <ModelConfigPage />,
      },
    ],
  },
]);
