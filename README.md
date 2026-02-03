<div align="center">

# 知识库智能体 (Knowledge Agent)

**基于大语言模型的企业级知识库智能体系统**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-18.3.1-blue.svg)](https://reactjs.org/)

[**English**](./README_EN.md) | **简体中文**

</div>

---

## 📖 简介

**知识库智能体** 是一个基于大语言模型的企业级知识库智能体系统，致力于将企业文档、知识库转化为智能问答系统，助力企业实现 AI 驱动的数字化转型。

### 核心特性

- **私有化部署** - 数据不出域，保障企业核心数据安全与隐私
- **多源知识摄入** - 支持文件、网页、数据库等多种数据源
- **语义检索与溯源** - 基于向量嵌入的智能搜索，可追溯答案来源
- **智能问答与对话** - 多轮对话支持，流式响应体验
- **多模型支持** - 兼容 Ollama、智谱AI、MiniMax、月之暗面等多种 LLM

### 在线体验

👉 **[产品演示 / 在线体验](http://www.tianyufuxi.com:8011/chat?intro=true)**

---

## 🚀 快速开始

### Docker 部署（推荐）

```bash
# 克隆项目
git clone https://github.com/your-org/knowledge-agentic.git
cd knowledge-agentic

# 使用 Docker 一键启动
docker-compose up -d
```

### 本地开发

```bash
# 后端启动
cd code
pip install -e .
uvicorn app.main:app --reload

# 前端启动
cd frontend
pnpm install
pnpm dev
```

> 📖 详细部署指南请参考 [部署说明文档](./docs/deployment-guide.md)

---

## ✨ 核心功能

### 多源知识摄入

| 数据源 | 支持格式 | 说明 |
|--------|----------|------|
| **文件上传** | PDF、Word、Excel、PPT、TXT、Markdown | 支持批量上传，自动解析 |
| **网页采集** | HTML/网页 | 自动提取正文内容 |
| **数据库同步** | PostgreSQL、MySQL | 定时同步业务数据 |
| **增量更新** | - | 智能去重，避免重复处理 |

### 语义检索与溯源

- 基于向量嵌入的语义搜索
- 相似度计算与排序
- 答案溯源引用，确保可解释性
- 高亮显示相关文档片段

### 智能问答与对话

- 多轮对话上下文管理
- 流式响应，实时反馈
- 支持多语言
- 会话历史记录

### 文档智能分析

- 一键文档总结
- 文档对比分析
- 关键信息提取
- 智能体任务执行

### 敏感信息过滤

- 手机号自动脱敏
- 邮箱地址脱敏
- 自定义过滤规则
- 数据安全保护

### 多模型支持

| 提供商 | 模型示例 |
|--------|----------|
| **Ollama** | Llama 3、DeepSeek-R1、Qwen2 |
| **智谱AI** | glm-4、glm-3-turbo |
| **MiniMax** | abab5.5-chat、abab6-chat |
| **月之暗面** | moonshot-v1-8k、moonshot-v1-32k |

---

## 🛠️ 技术栈

### 后端技术

| 组件 | 技术选型 |
|------|----------|
| **Web 框架** | FastAPI 0.109.0 |
| **AI 编排** | LangChain + LangGraph |
| **向量数据库** | ChromaDB 0.4.22 |
| **文档解析** | pdfplumber、python-docx、python-pptx |
| **数据库** | SQLite / PostgreSQL（异步驱动） |
| **测试框架** | pytest + pytest-asyncio |

### 前端技术

| 组件 | 技术选型 |
|------|----------|
| **框架** | React 18.3.1 + TypeScript |
| **构建工具** | Vite 7+ |
| **包管理** | pnpm |
| **UI 组件库** | Ant Design 6.1.4 |
| **状态管理** | Zustand 5.0.9 |
| **HTTP 客户端** | TanStack React Query 5.0.0 |
| **路由** | React Router DOM 7.12.0 |
| **测试框架** | Vitest 4.0.16 |

---

## 🎨 界面设计

本项目采用 **UI/UX Pro Max** 设计理念，融合现代 UI/UX 最佳实践：

- **玻璃拟态（Glassmorphism）** - 半透明、模糊背景和边框光效
- **深色模式（Dark Mode）** - 高对比度，舒适的视觉体验
- **Bento Grid 布局** - 网格化卡片布局，响应式排列
- **渐变美学** - 蓝紫渐变主色调，传递专业和创新感
- **无障碍设计** - 符合 WCAG 2.1 标准

---

## 💡 使用场景

### 企业知识管理

将企业文档、SOP、知识库转化为智能问答系统，让知识触手可及。

### 智能客服系统

基于企业知识库的 7×24 小时智能客服，提升服务效率。

### 文档智能处理

自动总结、对比、分析大量文档，提取关键信息。

### 个人知识库

构建个人专属的 AI 助手，处理各类文档和知识管理。

### 研究分析工具

快速检索和分析研究资料，辅助决策和报告撰写。

---

## 📁 项目结构

```
knowledge-agentic/
├── code/                    # 后端代码（Python FastAPI）
│   ├── app/                # 应用核心代码
│   ├── tests/              # 测试代码
│   └── pyproject.toml      # 项目配置
├── frontend/               # 前端代码（React + TypeScript）
│   ├── src/
│   │   ├── components/     # React 组件
│   │   ├── services/       # API 服务
│   │   └── stores/         # 状态管理
│   └── package.json        # 前端项目配置
├── docs/                   # 项目文档
└── script/                 # 构建和部署脚本
```

---

## 🏢 关于我们

### 上海宇羲伏天智能科技有限公司

我们是一家专注于 **AI 智能助手开发** 与 **企业 AI 赋能** 的创新型企业，致力于将前沿 AI 技术转化为实际生产力，为企业提供可 **私有化部署** 的 AI 助手解决方案。

**公司愿景**：让 AI 助手赋能每一个业务场景，助力企业完成智能化改造

**核心优势**：
- ✅ 十年架构经验，确保系统高可用、可扩展
- ✅ 2018 年深耕 AI 领域，紧跟前沿技术发展
- ✅ 支持私有化部署和云端 SaaS 两种模式
- ✅ 深入理解业务，提供量身定制的 AI 解决方案

---

## 📞 联系我们

| 方式 | 信息 |
|------|------|
| **在线体验** | [http://www.tianyufuxi.com:8011/chat?intro=true](http://www.tianyufuxi.com/chat?intro=true) |

---

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

---

<div align="center">

**让 AI 赋能每一个业务场景** 💪

[产品演示](http://www.tianyufuxi.com:8011/chat?intro=true) | [文档中心](./docs/README.md)

</div>
