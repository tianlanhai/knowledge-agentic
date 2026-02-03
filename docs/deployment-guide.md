# 知识库智能体 - 部署说明文档

## 1. 运行环境要求

帅哥，为了保证智能体能流畅运行，请确保您的 Windows 环境满足以下条件：

### 1.1 硬件要求

| 组件 | 最低配置 | 推荐配置 | 说明 |
|-----|---------|---------|------|
| **操作系统** | Windows 10/11 | Windows 11 专业版 | 建议专业版，以支持 Docker |
| **处理器** | 4 核 | 8 核+ | 多核提升并发处理能力 |
| **内存** | 16GB | 32GB | 本地模型和向量库共用内存 |
| **显卡** | 8GB 显存（可选） | 12GB+ 显存（推荐） | NVIDIA 显卡，支持 CUDA 加速 |
| **存储** | 20GB 可用空间 | 50GB+ | 模型+向量库+数据存储 |

### 1.2 软件依赖

| 软件 | 版本要求 | 用途说明 |
|-----|---------|---------|
| **Ollama** | Latest | 本地模型推理 |
| **Python** | 3.10+ | 后端环境 |
| **UV** | Latest | Python 包管理器 |
| **Node.js** | 18+ | 前端环境 |
| **pnpm** | Latest | 前端包管理器 |
| **Docker** | Latest（可选） | 一键部署向量库或前端 |

### 1.3 浏览器要求

**前端界面支持的浏览器：**

| 浏览器 | 最低版本 | 推荐版本 | 说明 |
|-------|---------|---------|------|
| **Chrome** | 90+ | Latest（推荐） | 最佳兼容性和性能 |
| **Firefox** | 88+ | Latest | 良好兼容性 |
| **Safari** | 14+ | Latest | macOS 和 iOS |
| **Edge** | 90+ | Latest | Windows 原生浏览器 |
| **Opera** | 76+ | Latest | 基于 Chromium |

**浏览器兼容性说明：**
- **推荐使用 Chrome 90+**：最佳兼容性和性能表现
- **不支持 IE 浏览器**：界面使用现代 Web 标准，不支持旧版 IE
- **移动端支持**：支持 iOS Safari 14+、Android Chrome 90+
- **功能降级**：旧版浏览器可能缺少某些高级功能

## 2. 核心依赖安装步骤

### 2.1 安装 Ollama

**Ollama 是本地大模型推理的核心组件。**

1. **下载和安装 Ollama**
   - 访问 [ollama.com](https://ollama.com) 下载 Windows 版
   - 运行安装程序，按照提示完成安装
   - 安装完成后，Ollama 服务会自动启动

2. **验证 Ollama 安装**
   ```bash
   # 检查 Ollama 版本
   ollama --version

   # 查看已安装的模型
   ollama list
   ```

3. **下载核心模型**
   ```bash
   # 下载问答模型
   ollama pull deepseek-r1:8b

   # 下载嵌入模型
   ollama pull mxbai-embed-large:latest
   ```

**Ollama 配置（可选）：**
```bash
# 设置 GPU 使用数量（1=启用GPU，0=使用CPU）
set OLLAMA_NUM_GPU=1

# 设置 GPU 内存利用率（0-1）
set OLLAMA_GPU_MEMORY_UTILIZATION=0.9
```

### 2.2 安装后端环境

**使用 UV 包管理器安装 Python 依赖。**

1. **安装 UV 包管理器**
   ```bash
   # 使用 PowerShell 安装
   irm https://astral.sh/uv/install.ps1 | iex
   ```

2. **克隆代码仓库**
   ```bash
   git clone <repository-url>
   cd knowledge-agentic
   ```

3. **安装项目依赖**
   ```bash
   # 在项目根目录下运行
   uv sync

   # UV 会自动创建虚拟环境并安装所有依赖到 .venv 目录
   ```

### 2.3 安装前端环境

**使用 pnpm 安装前端依赖。**

1. **安装 Node.js**
   ```bash
   # 访问 https://nodejs.org/ 下载 Node.js 18+ LTS 版本
   # 或使用 nvm 安装（推荐）
   nvm install 18
   nvm use 18
   ```

2. **安装 pnpm**
   ```bash
   # 使用 npm 安装 pnpm
   npm install -g pnpm
   ```

3. **安装前端依赖**
   ```bash
   # 进入前端目录
   cd frontend

   # 安装依赖
   pnpm install
   ```

## 3. 配置文件说明

系统配置文件通常位于根目录的 `.env` 中，主要包含以下内容：

### 3.1 后端配置

```bash
# Ollama 配置
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_HOST=127.0.0.1
OLLAMA_PORT=11434

# 嵌入模型配置
USE_LOCAL_EMBEDDINGS=True
DEVICE=cuda  # 或 auto 自动检测
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5

# 向量数据库配置
VECTOR_DB_PATH=./data/chroma_db
COLLECTION_NAME=knowledge_base

# 元数据库配置
METADB_PATH=./data/meta.db

# 日志配置
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
DEBUG=True  # 开发模式

# 虚拟数据配置
USE_MOCK=False  # 开发环境可启用
```

### 3.2 前端配置

**前端配置主要在 `vite.config.ts` 和环境变量中。**

```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/v1': {
        target: 'http://127.0.0.1:8010',
        changeOrigin: true,
      }
    }
  }
});
```

### 3.3 UI/UX 设计配置

**前端 UI 设计相关配置。**

**Tailwind CSS 配置（`tailwind.config.js`）：**
```javascript
export default {
  theme: {
    extend: {
      colors: {
        // 主色调
        primary: {
          500: '#667eea',
          900: '#764ba2',
        },
        // 背景色
        bg: {
          DEFAULT: '#0f172a',
          card: '#1e293b',
        },
        // 玻璃态
        glass: {
          light: 'rgba(255, 255, 255, 0.05)',
        },
      },
    },
  },
};
```

**主题配置（支持主题切换）：**
```typescript
// 在 src/config/theme.ts 中配置
export const themes = {
  dark: {
    background: '#0f172a',
    text: '#f1f5f9',
    // ...
  },
  light: {
    background: '#ffffff',
    text: '#1e293b',
    // ...
  },
};
```

## 4. 启动方式

### 4.1 本地开发模式启动

#### 4.1.1 启动后端服务

```bash
# 进入后端目录
cd code

# 方式一：使用 uvicorn 启动（推荐，支持热重载）
uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload

# 方式二：使用 uv 运行
uv run uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload
```

**后端启动成功后：**
- API 访问地址：`http://127.0.0.1:8010`
- Swagger 文档：`http://127.0.0.1:8010/docs`
- 健康检查：`http://127.0.0.1:8010/`

#### 4.1.2 启动前端服务

```bash
# 进入前端目录
cd frontend

# 启动开发服务器
pnpm dev

# 或使用其他命令
pnpm start
```

**前端启动成功后：**
- 前端访问地址：`http://localhost:3000` 或 `http://localhost:5173`
- 自动打开浏览器（如果配置）
- 支持 HMR（热模块替换）

#### 4.1.3 完整启动流程

建议使用两个终端窗口分别启动后端和前端：

**终端 1 - 启动后端：**
```bash
cd code
uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload
```

**终端 2 - 启动前端：**
```bash
cd frontend
pnpm dev
```

**验证启动状态：**
1. 访问 `http://127.0.0.1:8010/` 查看后端健康状态
2. 访问 `http://127.0.0.1:8010/docs` 测试 API 接口
3. 访问 `http://localhost:3000` 查看前端界面
4. 检查终端日志，确认无错误信息
5. 打开浏览器开发者工具，检查 Console 是否有错误

### 4.2 Docker 部署（推荐）

**Docker 部署提供了一键部署的便利性。**

#### 4.2.1 环境准备

1. **安装 Docker Desktop**
   - 下载并安装 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
   - 启动 Docker Desktop
   - 确保 Docker 服务正在运行

2. **GPU 支持（可选）**
   - 确保 NVIDIA 驱动已安装
   - 安装 NVIDIA Container Toolkit
   - Docker Desktop 设置中启用 GPU 支持

#### 4.2.2 使用 Docker 基础脚本部署

> **注意**：这是快速部署方案，适用于简单场景。如需多版本支持，请使用 [script/build/](../script/build/README.md)

在 `script/basic-docker/` 目录下运行：
```bash
# 进入 basic-docker 目录
cd script/basic-docker

# 启动所有服务（后端、前端、向量库）
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重新构建并启动
docker-compose up -d --build
```

**Docker Compose 配置示例：**
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8010:8000"
    environment:
      - OLLAMA_BASE_URL=http://host.docker.internal:11434
    volumes:
      - ./data:/app/data
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"
    volumes:
      - ./data/chroma:/chroma/chroma
```

**Docker 部署成功后：**
- 后端 API：`http://localhost:8010`
- 前端界面：`http://localhost:3000`
- 向量库：`http://localhost:8001`

### 4.3 生产环境部署

#### 4.3.1 后端部署

**使用 Gunicorn 或 Uvicorn 部署：**
```bash
# 使用 Gunicorn（生产环境推荐）
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8010

# 使用 Uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8010 --workers 4
```

#### 4.3.2 前端部署

**构建前端生产版本：**
```bash
# 进入前端目录
cd frontend

# 构建生产版本
pnpm build

# 构建产物在 dist/ 目录
```

**部署到静态服务器：**
```bash
# 使用 Nginx
# 配置 Nginx 指向 dist/ 目录

# 使用 Apache
# 配置 Apache 指向 dist/ 目录

# 使用 Vercel / Netlify
# 直接上传 dist/ 目录
```

**Nginx 配置示例：**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    root /path/to/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /v1 {
        proxy_pass http://localhost:8010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 5. 浏览器兼容性配置

### 5.1 Polyfill 配置

**为旧版浏览器提供兼容性支持。**

**安装 polyfill：**
```bash
# 在前端目录
cd frontend

# 安装 core-js 和 regenerator-runtime
pnpm add core-js regenerator-runtime
```

**在入口文件中引入：**
```typescript
// src/main.tsx
import 'core-js/stable';
import 'regenerator-runtime/runtime';
```

### 5.2 浏览器检测

**检测浏览器类型和版本。**
```typescript
// src/utils/browser.ts
export const getBrowserInfo = () => {
  const ua = navigator.userAgent;
  let browser = 'unknown';
  let version = 'unknown';

  if (ua.includes('Chrome')) {
    browser = 'chrome';
    version = ua.match(/Chrome\/(\d+)/)?.[1] || 'unknown';
  } else if (ua.includes('Firefox')) {
    browser = 'firefox';
    version = ua.match(/Firefox\/(\d+)/)?.[1] || 'unknown';
  } else if (ua.includes('Safari') && !ua.includes('Chrome')) {
    browser = 'safari';
    version = ua.match(/Version\/(\d+)/)?.[1] || 'unknown';
  }

  return { browser, version };
};

export const isBrowserSupported = () => {
  const { browser, version } = getBrowserInfo();
  const versionNum = parseInt(version, 10);

  switch (browser) {
    case 'chrome':
      return versionNum >= 90;
    case 'firefox':
      return versionNum >= 88;
    case 'safari':
      return versionNum >= 14;
    default:
      return false;
  }
};
```

### 5.3 功能降级

**为不支持的浏览器提供降级方案。**
```typescript
// 在组件中检测并降级
const Component = () => {
  const isSupported = isBrowserSupported();

  if (!isSupported) {
    return <BrowserUpgrade />;
  }

  return <MainComponent />;
};
```

## 6. 常见问题

### 6.1 安装问题

#### Q1: Ollama 安装后无法启动？
**A**: 检查以下几点：
- 确保 Ollama 服务已启动（查看任务管理器）
- 检查端口 11434 是否被占用
- 查看防火墙设置
- 重启 Ollama 服务

#### Q2: UV 安装依赖失败？
**A**: 尝试以下方法：
- 确保 Python 3.10+ 已安装
- 更新 UV 到最新版本
- 清除缓存：`uv cache clean`
- 使用 `uv sync --reinstall` 重新安装

#### Q3: pnpm install 报错？
**A**: 尝试以下方法：
- 确保 Node.js 18+ 已安装
- 清除缓存：`pnpm store prune`
- 删除 node_modules 和 pnpm-lock.yaml
- 重新运行 `pnpm install`

### 6.2 运行问题

#### Q4: 后端启动失败？
**A**: 检查以下几点：
- 确保端口 8010 未被占用
- 检查 .env 文件配置是否正确
- 查看 uvicorn 日志输出
- 检查 Ollama 服务是否正常运行

#### Q5: 前端启动失败？
**A**: 检查以下几点：
- 确保端口 3000 未被占用
- 检查依赖是否完整安装
- 查看 Vite 日志输出
- 检查后端服务是否正常运行

#### Q6: 模型响应慢？
**A**: 优化建议：
- 检查显卡驱动是否为最新版本
- 确保 Ollama 正在使用 GPU 加速
- 调整 GPU 内存利用率（设置为 0.9 或更低）
- 使用参数量较小的模型（如 phi3）

#### Q7: 内存溢出？
**A**: 解决方案：
- 如果物理内存不足，建议将 Ollama 的并发处理数调低
- 换用参数量较小的模型（如 phi3）
- 减少向量库的批次大小
- 增加系统虚拟内存

#### Q8: 文件解析失败？
**A**: 排查步骤：
- 确保已安装 `libmagic`（Windows 下可能需要额外配置 dll）
- 检查文件格式是否支持
- 查看后端日志获取详细错误信息
- 尝试将文件转换为支持的格式

### 6.3 界面问题

#### Q9: 界面样式不正确？
**A**: 排查步骤：
- 检查浏览器版本是否符合要求
- 清除浏览器缓存
- 禁用浏览器扩展（可能干扰样式）
- 检查 Tailwind CSS 是否正确加载
- 查看浏览器开发者工具的 Console 是否有错误

#### Q10: 响应式布局不工作？
**A**: 排查步骤：
- 使用浏览器开发者工具的设备工具栏测试
- 检查 viewport meta 标签是否正确
- 查看媒体查询断点是否正确
- 测试不同屏幕尺寸的布局

#### Q11: 动画不流畅？
**A**: 优化建议：
- 检查浏览器硬件加速是否启用
- 减少 DOM 元素数量
- 使用 `transform` 和 `opacity` 进行动画
- 避免引起重排的 CSS 属性

### 6.4 性能优化

#### Q12: 如何优化界面性能？
**A**: 优化方法：
- 使用代码分割和懒加载
- 长列表使用虚拟滚动
- 图片懒加载和响应式图片
- 使用 React.memo 和 useMemo 优化渲染
- 启用浏览器缓存

#### Q13: 如何优化后端性能？
**A**: 优化方法：
- 使用 GPU 加速
- 增加工作进程数量
- 优化向量检索参数
- 使用缓存减少重复计算

### 6.5 Docker 部署问题

#### Q14: Docker 容器无法启动？
**A**: 排查步骤：
- 检查 Docker Desktop 是否运行
- 查看容器日志：`docker-compose logs`
- 检查端口冲突
- 检查 Docker 镜像是否正确构建

#### Q15: Docker GPU 不工作？
**A**: 解决方案：
- 确保 NVIDIA 驱动已安装
- 安装 NVIDIA Container Toolkit
- Docker Desktop 设置中启用 GPU 支持
- 检查 docker-compose.yml 中的 GPU 配置

## 7. 维护和监控

### 7.1 日志管理

**日志位置：**
- 后端日志：`logs/` 目录
- 前端日志：浏览器 Console
- Docker 日志：`docker-compose logs`

**日志级别：**
- DEBUG：详细的调试信息
- INFO：一般信息
- WARNING：警告信息
- ERROR：错误信息

### 7.2 监控指标

**关键监控指标：**
- CPU 使用率
- 内存使用率
- GPU 使用率和显存占用
- 磁盘 I/O
- 网络流量
- API 响应时间
- 错误率

### 7.3 备份策略

**数据备份：**
- 定期备份向量数据库
- 定期备份元数据库
- 备份配置文件
- 备份用户上传的文档

**备份工具：**
- 手动复制备份
- 自动化备份脚本
- 云存储备份（可选）

## 8. 多版本镜像部署

### 8.1 版本说明

为满足不同客户的需求，本项目提供4个不同的镜像版本：

| 版本 | LLM | Embedding | 镜像大小 | 适用场景 |
|------|-----|-----------|----------|----------|
| **v1** | 云LLM | 本地向量 | ~3.5GB | 有GPU、追求隐私 |
| **v2** | 云LLM | 云端向量 | ~800MB | 无GPU、快速部署 |
| **v3** | 本地LLM | 本地向量 | ~3.5GB | 完全离线、高隐私 |
| **v4** | 本地LLM | 云端向量 | ~800MB | 本地推理、云端向量 |

### 8.2 支持的云LLM提供商

云LLM版本（v1、v2）支持以下提供商，运行时可切换：

- **智谱AI (ZhipuAI)** - 国内推荐
- **MiniMax** - 高性价比
- **月之暗面 (Moonshot)** - 长文本支持
- **OpenAI** - 海外客户

### 8.3 构建镜像

详细构建文档请参考：[构建部署指南](../script/build/README.md)

```bash
# 进入构建目录
cd script/build

# 构建指定版本
./build.sh v1    # 构建v1版本
./build.sh v2    # 构建v2版本
./build.sh v3    # 构建v3版本
./build.sh v4    # 构建v4版本

# 构建并推送
./build.sh v1 --push
```

### 8.4 部署镜像

```bash
# 进入构建目录
cd script/build

# 部署v1版本（云LLM + 本地向量）
ZHIPUAI_API_KEY=xxx ./deploy-v1.sh zhipuai

# 部署v2版本（云LLM + 云端向量）
MINIMAX_API_KEY=xxx MINIMAX_GROUP_ID=xxx ./deploy-v2.sh minimax

# 部署v3版本（本地LLM + 本地向量）
./deploy-v3.sh

# 部署v4版本（本地LLM + 云端向量）
./deploy-v4.sh
```

### 8.5 版本限制

每个镜像版本都有对应的配置限制，防止用户配置不支持的功能：

- v2版本无法配置本地Embedding
- v3版本无法配置云LLM提供商

版本限制通过后端验证和前端UI限制双重保障。

### 8.6 Volume挂载

**v1和v3版本**需要挂载本地向量模型目录：

```bash
-v /path/to/models:/app/models
```

**所有版本**都需要挂载数据目录：

```bash
-v /path/to/data:/app/data         # 向量库、上传文件
-v /path/to/logs:/app/logs         # 日志文件
```

## 9. 相关文档

- [构建部署指南](../script/build/README.md) - 多版本镜像构建和部署
- [CI/CD配置文档](./cicd-configuration.md) - 配置自动化测试和部署
- [本地调试文档](./local-debugging.md) - 了解本地开发调试
- [技术设计文档](./technical-design.md) - 了解系统架构
- [API接口文档](./api-documentation.md) - 查看接口详细说明
- [操作界面文档](./ui-interface.md) - 了解前端界面设计