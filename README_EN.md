<div align="center">

# Knowledge Agent

**Enterprise-Level Knowledge Base Agent System Powered by LLM**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-18.3.1-blue.svg)](https://reactjs.org/)

**English** | [简体中文](./README.md)

</div>

---

## 📖 Introduction

**Knowledge Agent** is an enterprise-level knowledge base agent system powered by Large Language Models (LLM). It is dedicated to transforming enterprise documents and knowledge bases into intelligent Q&A systems, helping enterprises achieve AI-driven digital transformation.

### Core Features

- **Private Deployment** - Data stays within your domain, ensuring enterprise data security and privacy
- **Multi-Source Knowledge Ingestion** - Support for files, web pages, databases, and more
- **Semantic Retrieval with Source Tracing** - Intelligent search based on vector embeddings with traceable answer sources
- **Intelligent Q&A and Conversation** - Multi-turn dialogue support with streaming response experience
- **Multi-Model Support** - Compatible with Ollama, Zhipu AI, MiniMax, Moonshot, and more

### Live Demo

👉 **[Product Demo / Live Experience](http://www.tianyufuxi.com:8011/chat?intro=true)**

---

## 🚀 Quick Start

### Docker Deployment (Recommended)

```bash
# Clone the project
git clone https://github.com/your-org/knowledge-agentic.git
cd knowledge-agentic

# Start with Docker
docker-compose up -d
```

### Local Development

```bash
# Backend
cd code
pip install -e .
uvicorn app.main:app --reload

# Frontend
cd frontend
pnpm install
pnpm dev
```

> 📖 For detailed deployment guide, please refer to [Deployment Documentation](./docs/deployment-guide.md)

---

## ✨ Core Features

### Multi-Source Knowledge Ingestion

| Data Source | Supported Formats | Description |
|-------------|-------------------|-------------|
| **File Upload** | PDF, Word, Excel, PPT, TXT, Markdown | Batch upload with automatic parsing |
| **Web Crawling** | HTML/Web Pages | Automatic content extraction |
| **Database Sync** | PostgreSQL, MySQL | Scheduled business data sync |
| **Incremental Updates** | - | Intelligent deduplication to avoid reprocessing |

### Semantic Retrieval with Source Tracing

- Semantic search based on vector embeddings
- Similarity calculation and ranking
- Answer source citation for explainability
- Highlighted relevant document fragments

### Intelligent Q&A and Conversation

- Multi-turn dialogue context management
- Streaming responses with real-time feedback
- Multi-language support
- Conversation history records

### Document Intelligence Analysis

- One-click document summarization
- Document comparison and analysis
- Key information extraction
- Agent task execution

### Sensitive Information Filtering

- Automatic phone number masking
- Email address masking
- Custom filtering rules
- Data security protection

### Multi-Model Support

| Provider | Model Examples |
|----------|----------------|
| **Ollama** | Llama 3, DeepSeek-R1, Qwen2 |
| **Zhipu AI** | glm-4, glm-3-turbo |
| **MiniMax** | abab5.5-chat, abab6-chat |
| **Moonshot** | moonshot-v1-8k, moonshot-v1-32k |

---

## 🛠️ Tech Stack

### Backend Technologies

| Component | Technology |
|-----------|------------|
| **Web Framework** | FastAPI 0.109.0 |
| **AI Orchestration** | LangChain + LangGraph |
| **Vector Database** | ChromaDB 0.4.22 |
| **Document Parsing** | pdfplumber, python-docx, python-pptx |
| **Database** | SQLite / PostgreSQL (async driver) |
| **Testing Framework** | pytest + pytest-asyncio |

### Frontend Technologies

| Component | Technology |
|-----------|------------|
| **Framework** | React 18.3.1 + TypeScript |
| **Build Tool** | Vite 7+ |
| **Package Manager** | pnpm |
| **UI Component Library** | Ant Design 6.1.4 |
| **State Management** | Zustand 5.0.9 |
| **HTTP Client** | TanStack React Query 5.0.0 |
| **Routing** | React Router DOM 7.12.0 |
| **Testing Framework** | Vitest 4.0.16 |

---

## 🎨 UI/UX Design

This project adopts the **UI/UX Pro Max** design philosophy, incorporating modern UI/UX best practices:

- **Glassmorphism** - Semi-transparent, blurred backgrounds with glowing borders
- **Dark Mode** - High contrast for comfortable visual experience
- **Bento Grid Layout** - Grid-based card layout with responsive arrangement
- **Gradient Aesthetics** - Blue-purple gradient theme conveying professionalism and innovation
- **Accessibility Design** - WCAG 2.1 compliant

---

## 💡 Use Cases

### Enterprise Knowledge Management

Transform enterprise documents, SOPs, and knowledge bases into intelligent Q&A systems, making knowledge accessible at your fingertips.

### Intelligent Customer Service

7×24-hour intelligent customer service based on enterprise knowledge base, improving service efficiency.

### Document Intelligence Processing

Automatically summarize, compare, and analyze large volumes of documents, extracting key information.

### Personal Knowledge Base

Build your personal AI assistant to handle various documents and knowledge management tasks.

### Research and Analysis Tool

Quickly retrieve and analyze research materials, assisting in decision-making and report writing.

---

## 📁 Project Structure

```
knowledge-agentic/
├── code/                    # Backend code (Python FastAPI)
│   ├── app/                # Application core code
│   ├── tests/              # Test code
│   └── pyproject.toml      # Project configuration
├── frontend/               # Frontend code (React + TypeScript)
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API services
│   │   └── stores/         # State management
│   └── package.json        # Frontend project configuration
├── docs/                   # Project documentation
└── script/                 # Build and deployment scripts
```

---

## 🏢 About Us

### Shanghai Yuxi Futian Intelligent Technology Co., Ltd.

We are an innovative company focused on **AI Assistant Development** and **Enterprise AI Empowerment**, dedicated to transforming cutting-edge AI technology into practical productivity and providing **privately deployable** AI assistant solutions for enterprises.

**Company Vision**: Empower every business scenario with AI assistants, helping enterprises complete intelligent transformation

**Core Advantages**:
- ✅ 10 years of architecture experience, ensuring high availability and scalability
- ✅ Deep engagement in AI since 2018, keeping up with frontier technology
- ✅ Supporting both private deployment and cloud SaaS models
- ✅ Deep understanding of business, providing customized AI solutions

---

## 📞 Contact

| Method | Information |
|--------|-------------|
| **Live Demo** | [http://www.tianyufuxi.com:8011/chat?intro=true](http://www.tianyufuxi.com/chat?intro=true) |

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

**Empower Every Business Scenario with AI** 💪

[Product Demo](http://www.tianyufuxi.com:8011/chat?intro=true) | [Documentation](./docs/README.md)

</div>
