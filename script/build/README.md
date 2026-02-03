# 知识库智能体 - 多版本镜像构建部署指南

## 一、版本说明

本项目提供4个不同的镜像版本，以满足不同客户的需求：

| 版本 | LLM | Embedding | 镜像大小 | 适用场景 |
|------|-----|-----------|----------|----------|
| **v1** | 云LLM | 本地向量 | ~3.5GB | 有GPU、追求隐私 |
| **v2** | 云LLM | 云端向量 | ~800MB | 无GPU、快速部署 |
| **v3** | 本地LLM | 本地向量 | ~3.5GB | 完全离线、高隐私 |
| **v4** | 本地LLM | 云端向量 | ~800MB | 本地推理、云端向量 |

### 支持的云LLM提供商

所有云LLM版本（v1、v2）支持以下提供商（运行时可切换）：

- **智谱AI (ZhipuAI)** - 国内推荐
- **MiniMax** - 高性价比
- **月之暗面 (Moonshot)** - 长文本支持
- **OpenAI** - 海外客户

## 二、目录结构

```
script/build/
├── dockerbuild.bat           # Windows构建脚本（主入口）
├── common.bat                # Windows通用函数库
├── deploy.sh                 # Linux部署脚本（统一入口）
├── common.sh                 # Linux通用函数库
├── lib/                      # 函数库目录
│   ├── version.bat           # Windows版本配置
│   ├── version.sh            # Linux版本配置
│   ├── logger.bat            # Windows日志函数
│   └── logger.sh             # Linux日志函数
├── configs/                  # 配置模板目录（简化版）
│   ├── base.env              # 基础配置
│   ├── cloud-llm.env         # 云LLM配置片段
│   ├── local-llm.env         # 本地LLM配置片段
│   ├── local-emb.env         # 本地向量配置片段
│   └── cloud-emb.env         # 云端向量配置片段
└── README.md                 # 本文档
```

## 三、构建镜像（Windows）

### 3.1 准备工作

1. 确保已安装Docker Desktop
2. 确保有阿里云容器镜像服务访问权限
3. 确保代码仓库已更新到最新版本

### 3.2 构建命令

#### 交互式构建（推荐）

```cmd
cd script\build
dockerbuild.bat
```

无参数运行将显示交互式菜单，可选择构建版本并设置选项。

#### 命令行构建

```cmd
cd script\build

# 构建v1版本（云LLM + 本地向量）
dockerbuild.bat v1

# 构建v2版本（云LLM + 云端向量）
dockerbuild.bat v2

# 构建v3版本（本地LLM + 本地向量）
dockerbuild.bat v3

# 构建v4版本（本地LLM + 云端向量）
dockerbuild.bat v4

# 构建并推送到仓库
dockerbuild.bat v1 --push

# 不使用缓存构建
dockerbuild.bat v1 --no-cache
```

### 3.3 验证构建

```cmd
REM 查看镜像大小
docker images | findstr knowagent-back

REM 预期结果
REM v1/v3: 约 3.5GB（含torch）
REM v2/v4: 约 800MB（不含torch）
```

## 四、部署镜像（Linux）

### 4.1 环境变量配置

#### 云LLM密钥配置

```bash
# 智谱AI
export ZHIPUAI_API_KEY="your_api_key_here"

# MiniMax
export MINIMAX_API_KEY="your_api_key_here"
export MINIMAX_GROUP_ID="your_group_id_here"

# 月之暗面
export MOONSHOT_API_KEY="your_api_key_here"

# OpenAI
export OPENAI_API_KEY="your_api_key_here"
```

#### 数据库配置

```bash
export DB_HOST="host.docker.internal"  # 或实际数据库地址
export DB_PORT="15432"
export DB_NAME="knowledge_db"
export DB_USER="postgres"
export DB_PASSWORD="your_password"
```

### 4.2 部署命令

#### 使用统一部署脚本

```bash
cd script/build

# 部署v1版本（云LLM + 本地向量）
./deploy.sh v1 zhipuai

# 部署v2版本（云LLM + 云端向量）
ZHIPUAI_API_KEY=xxx ./deploy.sh v2 zhipuai

# 部署v3版本（本地LLM + 本地向量）
./deploy.sh v3

# 部署v4版本（本地LLM + 云端向量）
ZHIPUAI_API_KEY=xxx ./deploy.sh v4
```

### 4.3 部署后验证

```bash
# 检查容器状态
docker ps | grep knowledge-agent

# 查看后端日志
docker logs -f knowledge-agent-backend

# 健康检查
curl http://localhost:8010/

# 检查版本信息
curl http://localhost:8010/api/v1/version/info
```

## 五、客户使用示例

### 客户A：使用智谱AI + 本地向量

```bash
cd script/build

# 部署v1版本
ZHIPUAI_API_KEY=xxx ./deploy.sh v1 zhipuai

# 确保本地向量模型已挂载到 /tianlanhai/knowledge-agent/models/bge-large-zh-v1.5
```

### 客户B：使用MiniMax + 云端向量

```bash
cd script/build

# 部署v2版本
MINIMAX_API_KEY=xxx MINIMAX_GROUP_ID=xxx ./deploy.sh v2 minimax
```

### 客户C：完全离线环境（本地LLM + 本地向量）

```bash
cd script/build

# 部署v3版本
./deploy.sh v3

# 前提条件：
# 1. Ollama服务已启动并下载了模型
# 2. 本地向量模型已挂载到 /tianlanhai/knowledge-agent/models/
```

## 六、Volume挂载说明

### v1和v3版本（本地向量）

需要挂载本地向量模型目录：

```bash
docker run -d \
  -v /path/to/models:/app/models \
  # ... 其他配置
```

客户需要自行准备向量模型文件：

```
/path/to/models/
└── bge-large-zh-v1.5/
    ├── config.json
    ├── model.safetensors
    └── ...
```

### 所有版本的数据持久化

```bash
-v /path/to/data:/app/data         # 向量库、上传文件
-v /path/to/logs:/app/logs         # 日志文件
```

## 七、常见问题

### Q1: 构建失败怎么办？

A: 检查以下几点：
- Docker是否正常运行
- 网络是否可以访问阿里云容器镜像服务
- 代码是否完整

### Q2: 镜像大小不对？

A:
- v1/v3应该约3.5GB（含torch）
- v2/v4应该约800MB（不含torch）

### Q3: 如何切换云LLM提供商？

A: 部署时指定不同的提供商：
```bash
./deploy.sh v1 minimax      # 使用MiniMax
./deploy.sh v1 moonshot     # 使用月之暗面
./deploy.sh v1 openai       # 使用OpenAI
```

### Q4: 本地向量模型如何准备？

A: 从HuggingFace下载模型文件：
```bash
git clone https://huggingface.co/BAAI/bge-large-zh-v1.5 /path/to/models/bge-large-zh-v1.5
```

## 八、管理命令

```bash
# 查看日志
docker logs -f knowledge-agent-backend
docker logs -f knowledge-agent-frontend

# 停止服务
docker stop knowledge-agent-backend knowledge-agent-frontend

# 重启服务
docker restart knowledge-agent-backend knowledge-agent-frontend

# 删除容器
docker rm -f knowledge-agent-backend knowledge-agent-frontend

# 查看资源使用
docker stats knowledge-agent-backend
```
