# -*- coding: utf-8 -*-
# 知识库智能体系统 - Docker镜像构建文件
#
# 功能说明：
# - 基于python:3.11官方镜像构建应用镜像
# - 安装系统依赖和Python依赖
# - 配置Gunicorn作为WSGI服务器
# - 暴露8010端口
#
# 构建参数：
#   IMAGE_VERSION: 镜像版本标识（v1/v2/v3/v4）
#                  - v1: 云LLM + 本地向量
#                  - v2: 云LLM + 云端向量
#                  - v3: 本地LLM + 本地向量
#                  - v4: 本地LLM + 云端向量
#   INSTALL_LOCAL_EMB: 是否安装本地Embedding依赖（torch、sentence-transformers）
#                      - true: 安装本地Embedding（用于v1/v3版本，约 3.5GB）
#                      - false: 不安装本地Embedding（用于v2/v4版本，约 800MB）
#   默认值：v1版本，false（生产环境优先，使用云端/Ollama Embedding）

# 构建参数：镜像版本标识
ARG IMAGE_VERSION=v1

# 构建参数：是否安装本地Embedding依赖（torch、sentence-transformers）
ARG INSTALL_LOCAL_EMB=false

# 使用Python 3.11-slim官方镜像作为基础镜像（减小镜像体积）
# slim版本比完整版小约700MB，仅包含运行Python所需的最小依赖
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
# PYTHONUNBUFFERED: 确保Python输出直接显示在容器日志中
# DEPLOYMENT_MODE: 标识部署环境，docker表示Docker容器环境
# IMAGE_VERSION: 镜像版本标识，用于版本配置限制
# PORT: 应用服务端口
# APP_ENV: 运行环境，prod表示使用.env.prod配置
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEPLOYMENT_MODE=docker \
    IMAGE_VERSION=v1 \
    PORT=8010 \
    APP_ENV=prod

# 重新设置IMAGE_VERSION为构建参数的值（如果构建时指定）
ARG IMAGE_VERSION
ENV IMAGE_VERSION=${IMAGE_VERSION}

# 安装系统依赖
# curl: 用于健康检查
# gcc, g++, make: 仅在安装本地依赖时需要（编译 torch）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# 安装UV包管理器
RUN pip install --no-cache-dir uv

# 复制依赖文件
# 注意：生产环境不使用 uv.lock，避免自动安装 [local-emb] 可选依赖
COPY pyproject.toml ./
COPY README.md ./

# 使用UV安装Python依赖
# 根据 INSTALL_LOCAL_EMB 参数决定是否安装本地Embedding依赖（torch、sentence-transformers）
# v1/v3版本（本地Embedding）：INSTALL_LOCAL_EMB=true
# v2/v4版本（云端/Ollama Embedding）：INSTALL_LOCAL_EMB=false（默认）
RUN if [ "$INSTALL_LOCAL_EMB" = "true" ]; then \
      uv pip install --system --no-cache -e ".[local-emb]"; \
    else \
      uv pip install --system --no-cache -e .; \
    fi

# 安装Gunicorn（生产环境WSGI服务器）
RUN uv pip install --system gunicorn

# 清理构建工具和缓存以减小镜像体积
# 依赖安装完成后，删除编译工具和apt缓存
RUN apt-get remove -y gcc g++ make && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# 复制应用代码
COPY app ./app

# 复制环境配置文件到镜像
# .env: 基础配置（本地开发用，也作为Docker的基础配置）
# .env.prod: 生产环境覆盖配置（PostgreSQL + 占位符）
COPY .env .env.prod ./

# 创建数据目录（数据持久化挂载点）
RUN mkdir -p /app/data && \
    mkdir -p /app/models && \
    mkdir -p /app/logs && \
    chown -R nobody:nogroup /app

# 切换到非root用户（安全最佳实践）
USER nobody

# 暴露应用端口（与配置文件 PORT=8010 一致）
EXPOSE 8010

# 健康检查配置
# 使用根路径健康检查端点
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8010/ || exit 1

# 使用Gunicorn启动应用
# -w: worker进程数
# -k: worker类型（sync同步worker，兼容性好）
# -b: 绑定地址
# --access-logfile: 访问日志
# --error-logfile: 错误日志
# --timeout: 请求超时时间
CMD ["gunicorn", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", \
     "-b", "0.0.0.0:8010", \
     "--access-logfile", "-", "--error-logfile", "-", \
     "--timeout", "120", \
     "app.main:app"]
















