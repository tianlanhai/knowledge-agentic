# 知识库智能体 - 前端项目

## 项目概述

这是知识库智能体项目的前端界面，基于 React + Vite + pnpm 技术栈开发。

## 技术栈

- **前端框架**: React 18+
- **构建工具**: Vite 5+
- **包管理器**: pnpm
- **路由管理**: React Router v6
- **状态管理**: Zustand
- **UI 组件库**: Ant Design 5+
- **HTTP 客户端**: axios
- **样式方案**: Tailwind CSS
- **类型检查**: TypeScript 5+

## 功能模块

### 1. 知识管理模块
- 文件上传（支持 PDF、Markdown、Word、TXT、Excel）
- 网页抓取
- 文档列表（支持查看、删除）

### 2. 智能问答模块
- 对话界面（支持流式输出）
- 智能体模式开关
- 来源引用展示
- 多轮对话支持

### 3. 文档分析模块
- 文档总结（开发中）
- 文档对比（开发中）

### 4. 语义搜索模块
- 语义搜索（开发中）

## 项目结构

```
src/
├── assets/              # 静态资源
├── components/          # 组件
│   ├── common/         # 通用组件
│   ├── layout/         # 布局组件
│   └── features/      # 功能组件
│       ├── KnowledgeManagement/
│       ├── Chat/
│       ├── DocumentAnalysis/
│       └── Search/
├── hooks/              # 自定义 Hooks
├── stores/             # 状态管理
├── services/           # API 服务
├── types/              # TypeScript 类型定义
├── utils/              # 工具函数
├── App.tsx             # 根组件
├── main.tsx            # 入口文件
└── router.tsx          # 路由配置
```

## 快速开始

### 前置要求

- Node.js 20.14.0+
- pnpm 10.21.0+

### 安装依赖

```bash
cd frontend
pnpm install
```

### 启动开发服务器

```bash
pnpm dev
```

前端服务将在 `http://localhost:3000` 启动。

### 构建生产版本

```bash
pnpm build
```

### 预览生产版本

```bash
pnpm preview
```

## API 配置

前端通过 Vite 代理与后端 API 通信：

- **前端地址**: `http://localhost:3000`
- **后端地址**: `http://127.0.0.1:8010`
- **API 基础路径**: `/v1`

代理配置在 `vite.config.ts` 中：

```typescript
server: {
  port: 3000,
  proxy: {
    '/v1': {
      target: 'http://127.0.0.1:8010',
      changeOrigin: true,
    }
  }
}
```

## 开发指南

### 代码规范

- 使用 TypeScript 进行类型检查
- 遵循 ESLint 规则
- 使用函数式组件和 Hooks
- 组件命名使用 PascalCase
- 文件命名使用 PascalCase（组件）或 camelCase（工具、服务）

### 状态管理

使用 Zustand 进行状态管理，Store 定义在 `src/stores/` 目录：

- `chatStore.ts`: 对话状态
- `documentStore.ts`: 文档状态

### API 集成

所有 API 调用通过 `src/services/` 目录下的服务层封装：

- `api.ts`: axios 实例配置
- `chatService.ts`: 对话相关 API
- `ingestService.ts`: 知识摄入相关 API
- `documentService.ts`: 文档管理相关 API
- `searchService.ts`: 搜索相关 API

### 自定义 Hooks

自定义 Hooks 定义在 `src/hooks/` 目录：

- `useChat.ts`: 对话功能 Hook
- `useDocuments.ts`: 文档管理 Hook

## 常见问题

### Q: 如何修改后端 API 地址？

A: 修改 `vite.config.ts` 中的 `proxy.target` 配置。

### Q: 如何添加新的页面？

A: 在 `src/components/features/` 下创建新组件，然后在 `src/router.tsx` 中添加路由。

### Q: 如何添加新的 API 接口？

A: 在 `src/services/` 下创建对应的服务文件，使用 `api` 实例发起请求。

### Q: 如何添加新的状态管理？

A: 在 `src/stores/` 下创建新的 Store 文件，使用 `create` 函数定义状态。

## 浏览器支持

- Chrome (推荐)
- Firefox
- Edge
- Safari

## 许可证

MIT
