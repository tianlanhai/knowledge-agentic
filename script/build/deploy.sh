#!/bin/bash
# ============================================================================
# 知识库智能体 - Linux部署脚本（优化版）
# File    : deploy.sh
# Purpose : 在Linux系统上部署Docker容器
#           支持版本：v1(云LLM+本地向量) v2(云LLM+云端向量) v3(本地LLM+本地向量) v4(本地LLM+云端向量)
# Usage   : ./deploy.sh <version> [provider]
# Example : ./deploy.sh v1 zhipuai  # 部署v1版本，使用智谱AI
# ============================================================================

set -euo pipefail

# ============================================================================
# 1. 加载通用函数库
# ============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# 引入函数库（如果存在则加载）
[[ -f "${SCRIPT_DIR}/common.sh" ]] && source "${SCRIPT_DIR}/common.sh"
[[ -f "${SCRIPT_DIR}/lib/logger.sh" ]] && source "${SCRIPT_DIR}/lib/logger.sh"
[[ -f "${SCRIPT_DIR}/lib/version.sh" ]] && source "${SCRIPT_DIR}/lib/version.sh"

# ============================================================================
# 2. 内部变量定义
# ============================================================================
# 容器配置
NETWORK_NAME="knowledge-agent-network"
BACKEND_CONTAINER="knowledge-agent-backend"
FRONTEND_CONTAINER="knowledge-agent-frontend"
BACKEND_PORT="${BACKEND_PORT:-8010}"
FRONTEND_PORT="${FRONTEND_PORT:-8011}"

# 镜像配置
REGISTRY="registry.cn-shanghai.aliyuncs.com/tianlanhai/test"
IMAGE_NAME="knowagent-back"

# 数据持久化目录
DATA_DIR="${DATA_DIR:-/tianlanhai/knowledge-agent}"

# 版本描述映射（内部变量）
declare -A VERSION_DESCRIPTIONS=(
    ["v1"]="云LLM + 本地向量"
    ["v2"]="云LLM + 云端向量"
    ["v3"]="本地LLM + 本地向量"
    ["v4"]="本地LLM + 云端向量"
)

# ============================================================================
# 2. 辅助函数
# ==============================================================================

# 函数级注释：显示使用说明
show_usage() {
    cat << EOF
用法: $0 <version> [provider]

版本说明:
  v1  云LLM + 本地向量（需要挂载本地向量模型）
  v2  云LLM + 云端向量（轻量版）
  v3  本地LLM + 本地向量（需要挂载本地向量模型和Ollama服务）
  v4  本地LLM + 云端向量（需要Ollama服务）

云LLM提供商:
  zhipuai   智谱AI（默认）
  minimax   MiniMax
  moonshot  月之暗面
  openai    OpenAI

环境变量:
  BACKEND_PORT        后端端口（默认: 8010）
  FRONTEND_PORT       前端端口（默认: 8011）
  DATA_DIR            数据目录（默认: /tianlanhai/knowledge-agent）

  云LLM密钥配置:
  ZHIPUAI_API_KEY         智谱AI密钥
  MINIMAX_API_KEY         MiniMax密钥
  MINIMAX_GROUP_ID        MiniMax Group ID
  MOONSHOT_API_KEY        月之暗面密钥
  OPENAI_API_KEY          OpenAI密钥

  数据库配置:
  DB_HOST            数据库主机（默认: host.docker.internal）
  DB_PORT            数据库端口（默认: 15432）
  DB_NAME            数据库名称（默认: knowledge_db）
  DB_USER            数据库用户（默认: postgres）
  DB_PASSWORD        数据库密码（默认: test）

示例:
  $0 v1                              # 部署v1版本
  ZHIPUAI_API_KEY=xxx $0 v2 zhipuai   # 部署v2版本，使用智谱AI
  $0 v3                              # 部署v3版本（本地LLM）

EOF
}

# 函数级注释：日志输出
log_info() {
    echo -e "\033[32m[INFO]\033[0m $1"
}

# 函数级注释：错误输出
log_error() {
    echo -e "\033[31m[ERROR]\033[0m $1" >&2
}

# 函数级注释：警告输出
log_warn() {
    echo -e "\33[33m[WARN]\033[0m $1"
}

# ============================================================================
# 3. 参数解析
# ==============================================================================

# 内部逻辑：检查参数数量
if [ $# -lt 1 ]; then
    show_usage
    exit 1
fi

VERSION="$1"
PROVIDER="${2:-zhipuai}"
VERSION_DESC="${VERSION_DESCRIPTIONS[$VERSION]}"
IMAGE_TAG="${REGISTRY}:${IMAGE_NAME}-${VERSION}"

# ============================================================================
# 4. Guard: 验证版本参数
# ============================================================================

if [[ ! "$VERSION" =~ ^v[1-4]$ ]]; then
    log_error "无效的版本: $VERSION"
    log_info "支持的版本: v1, v2, v3, v4"
    exit 1
fi

# ============================================================================
# 5. Guard: 检查Docker环境
# ============================================================================

if ! command -v docker >/dev/null 2>&1; then
    log_error "docker命令未找到，请先安装Docker"
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    log_error "Docker守护进程未运行"
    exit 1
fi

# ============================================================================
# 6. 准备数据目录
# ==============================================================================

log_info "=========================================="
log_info "  知识库智能体 - 部署脚本"
log_info "=========================================="
log_info ""
log_info "配置信息:"
log_info "  - 版本     : $VERSION ($VERSION_DESC)"
log_info "  - 镜像     : $IMAGE_TAG"
log_info "  - 云LLM    : $PROVIDER"
log_info "  - 数据目录 : $DATA_DIR"
log_info ""

# 内部逻辑：创建数据目录
log_info "[INIT] 创建数据目录..."
mkdir -p "${DATA_DIR}/data"
mkdir -p "${DATA_DIR}/models"
mkdir -p "${DATA_DIR}/logs/backend"
mkdir -p "${DATA_DIR}/logs/frontend"

# 内部逻辑：设置目录权限
chmod -R 777 "${DATA_DIR}/data" "${DATA_DIR}/models" "${DATA_DIR}/logs"

# ============================================================================
# 7. 准备Docker网络
# ============================================================================

log_info "[NETWORK] 创建Docker网络: ${NETWORK_NAME}"
docker network create "${NETWORK_NAME}" >/dev/null 2>&1 || true

# ============================================================================
# 8. 拉取镜像
# ==============================================================================

log_info "[PULL] 拉取镜像: ${IMAGE_TAG}"
if ! docker pull "${IMAGE_TAG}"; then
    log_error "镜像拉取失败: ${IMAGE_TAG}"
    log_info "请先运行构建脚本: ./build-${VERSION}.sh"
    exit 1
fi

# ============================================================================
# 9. 停止旧容器
# ==============================================================================

log_info "[CLEAN] 停止旧容器..."
docker stop "${BACKEND_CONTAINER}" "${FRONTEND_CONTAINER}" >/dev/null 2>&1 || true
docker rm "${BACKEND_CONTAINER}" "${FRONTEND_CONTAINER}" >/dev/null 2>&1 || true

# ============================================================================
# 10. 启动后端容器
# ============================================================================

log_info "[RUN] 启动后端容器..."

# 内部逻辑：构建环境变量列表
ENV_ARGS=(
    -e APP_ENV=prod
    -e TIMEZONE="Asia/Shanghai"
    -e DB_HOST="${DB_HOST:-host.docker.internal}"
    -e DB_PORT="${DB_PORT:-15432}"
    -e DB_NAME="${DB_NAME:-knowledge_db}"
    -e DB_USER="${DB_USER:-postgres}"
    -e DB_PASSWORD="${DB_PASSWORD:-test}"
)

# 内部逻辑：根据版本添加环境变量
case "$VERSION" in
    v1|v2)
        # 云LLM版本：添加云LLM密钥配置
        case "$PROVIDER" in
            zhipuai)
                ENV_ARGS+=(
                    -e LLM_PROVIDER=zhipuai
                    -e EMBEDDING_PROVIDER="$([ "$VERSION" = "v1" ] && echo "local" || echo "zhipuai")"
                    -e ZHIPUAI_API_KEY="${ZHIPUAI_API_KEY:-}"
                    -e ZHIPUAI_LLM_API_KEY="${ZHIPUAI_LLM_API_KEY:-${ZHIPUAI_API_KEY:-}}"
                    -e ZHIPUAI_EMBEDDING_API_KEY="${ZHIPUAI_EMBEDDING_API_KEY:-${ZHIPUAI_API_KEY:-}}"
                )
                ;;
            minimax)
                ENV_ARGS+=(
                    -e LLM_PROVIDER=minimax
                    -e EMBEDDING_PROVIDER="$([ "$VERSION" = "v1" ] && echo "local" || echo "zhipuai")"
                    -e MINIMAX_API_KEY="${MINIMAX_API_KEY:-}"
                    -e MINIMAX_GROUP_ID="${MINIMAX_GROUP_ID:-}"
                )
                ;;
            moonshot)
                ENV_ARGS+=(
                    -e LLM_PROVIDER=moonshot
                    -e EMBEDDING_PROVIDER="$([ "$VERSION" = "v1" ] && echo "local" || echo "zhipuai")"
                    -e MOONSHOT_API_KEY="${MOONSHOT_API_KEY:-}"
                )
                ;;
            openai)
                ENV_ARGS+=(
                    -e LLM_PROVIDER=openai
                    -e EMBEDDING_PROVIDER="$([ "$VERSION" = "v1" ] && echo "local" || echo "openai")"
                    -e OPENAI_API_KEY="${OPENAI_API_KEY:-}"
                )
                ;;
        esac
        ;;
    v3|v4)
        # 本地LLM版本：配置Ollama连接
        ENV_ARGS+=(
            -e LLM_PROVIDER=ollama
            -e EMBEDDING_PROVIDER="$([ "$VERSION" = "v3" ] && echo "local" || echo "zhipuai")"
            -e OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://host.docker.internal:11434}"
            -e ZHIPUAI_EMBEDDING_API_KEY="${ZHIPUAI_EMBEDDING_API_KEY:-${ZHIPUAI_API_KEY:-}}"
        )
        ;;
esac

# 内部逻辑：构建挂载卷列表
VOLUME_ARGS=(
    -v "${DATA_DIR}/data:/app/data"
    -v "${DATA_DIR}/logs/backend:/app/logs"
)

# 内部逻辑：v1和v3版本需要挂载本地向量模型
if [ "$VERSION" = "v1" ] || [ "$VERSION" = "v3" ]; then
    VOLUME_ARGS+=(-v "${DATA_DIR}/models:/app/models")
    log_info "[INFO] 将挂载本地向量模型目录: ${DATA_DIR}/models"
fi

# 内部逻辑：启动后端容器
docker run -d \
    --name "${BACKEND_CONTAINER}" \
    --cpus="0.5" \
    --memory="1g" \
    --network "${NETWORK_NAME}" \
    --restart unless-stopped \
    --add-host=host.docker.internal:host-gateway \
    -p "${BACKEND_PORT}:8010" \
    "${VOLUME_ARGS[@]}" \
    "${ENV_ARGS[@]}" \
    "${IMAGE_TAG}"

# ============================================================================
# 11. 等待后端启动
# ============================================================================

log_info "[WAIT] 等待后端服务启动..."
sleep 10

# 内部逻辑：健康检查
log_info "[CHECK] 检查后端服务健康状态..."
if curl -sf "http://localhost:${BACKEND_PORT}/" > /dev/null; then
    log_info "[OK] 后端服务启动成功"
else
    log_warn "[WARN] 后端服务健康检查失败，请检查日志: docker logs ${BACKEND_CONTAINER}"
fi

# ============================================================================
# 12. 启动前端容器
# ==============================================================================

log_info "[RUN] 启动前端容器..."
FRONTEND_IMAGE="${REGISTRY}:knowagent-front"

# 内部逻辑：拉取前端镜像
docker pull "${FRONTEND_IMAGE}"

# 内部逻辑：启动前端容器
docker run -d \
    --name "${FRONTEND_CONTAINER}" \
    --network "${NETWORK_NAME}" \
    --link "${BACKEND_CONTAINER}:knowledge-agent-backend" \
    --restart unless-stopped \
    -p "${FRONTEND_PORT}:80" \
    -v "${DATA_DIR}/logs/frontend:/var/log/nginx" \
    "${FRONTEND_IMAGE}"

# ============================================================================
# 13. 部署摘要
# ==============================================================================

log_info ""
log_info "=========================================="
log_info "  部署完成"
log_info "=========================================="
log_info ""
log_info "后端服务:"
log_info "  - 容器名   : ${BACKEND_CONTAINER}"
log_info "  - 镜像     : ${IMAGE_TAG}"
log_info "  - 版本     : ${VERSION}"
log_info "  - URL      : http://<服务器IP>:${BACKEND_PORT}"
log_info ""
log_info "前端服务:"
log_info "  - 容器名   : ${FRONTEND_CONTAINER}"
log_info "  - 镜像     : ${FRONTEND_IMAGE}"
log_info "  - URL      : http://<服务器IP>:${FRONTEND_PORT}"
log_info ""
log_info "数据存储:"
log_info "  - 目录     : ${DATA_DIR}"
log_info "  - 数据库   : 外部PostgreSQL (${DB_HOST:-host.docker.internal}:${DB_PORT:-15432})"
log_info "  - 向量库   : ${DATA_DIR}/data/chroma_db"
log_info "  - 上传文件 : ${DATA_DIR}/data/files"
if [ "$VERSION" = "v1" ] || [ "$VERSION" = "v3" ]; then
    log_info "  - 向量模型 : ${DATA_DIR}/models/bge-large-zh-v1.5"
fi
log_info ""
log_info "管理命令:"
log_info "  - 查看日志 : docker logs -f ${BACKEND_CONTAINER}"
log_info "  - 停止服务 : docker stop ${BACKEND_CONTAINER} ${FRONTEND_CONTAINER}"
log_info "  - 重启服务 : docker restart ${BACKEND_CONTAINER} ${FRONTEND_CONTAINER}"
log_info ""
log_info "=========================================="
