#!/bin/bash
# ============================================================================
# 知识库智能体 - Linux通用函数库
# File    : common.sh
# Purpose : 提供共享的环境变量和通用函数
# ============================================================================

# ============================================================================
# 全局变量定义
# ============================================================================
readonly REGISTRY="registry.cn-shanghai.aliyuncs.com/tianlanhai/test"
readonly IMAGE_NAME="knowagent-back"
readonly FRONTEND_IMAGE_NAME="knowagent-front"
readonly NETWORK_NAME="knowledge-agent-network"
readonly BACKEND_CONTAINER="knowledge-agent-backend"
readonly FRONTEND_CONTAINER="knowledge-agent-frontend"
readonly BACKEND_PORT="${BACKEND_PORT:-8010}"
readonly FRONTEND_PORT="${FRONTEND_PORT:-8011}"
readonly DATA_DIR="${DATA_DIR:-/tianlanhai/knowledge-agent}"

# ============================================================================
# check_docker - 检查Docker是否运行
# 返回: 0=运行中, 1=未运行
# ============================================================================
check_docker() {
    if ! command -v docker >/dev/null 2>&1; then
        return 1
    fi
    if ! docker info >/dev/null 2>&1; then
        return 1
    fi
    return 0
}

# ============================================================================
# pull_image - 拉取镜像
# 参数: $1 = 镜像名称
# 返回: 0=成功, 1=失败
# ============================================================================
pull_image() {
    local image="$1"
    if [[ -z "$image" ]]; then
        echo "[ERROR] 镜像名称不能为空"
        return 1
    fi
    echo "[PULL] 拉取镜像: $image"
    docker pull "$image"
    return $?
}

# ============================================================================
# print_separator - 打印分隔线
# 参数: $1 = 标题（可选）
# ============================================================================
print_separator() {
    echo ""
    echo "========================================"
    if [[ -n "$1" ]]; then
        echo "  $1"
        echo "========================================"
    fi
}

# ============================================================================
# show_deployment_summary - 显示部署摘要
# ============================================================================
show_deployment_summary() {
    echo ""
    echo "后端服务:"
    echo "  - 容器名   : ${BACKEND_CONTAINER}"
    echo "  - 镜像     : ${IMAGE_TAG}"
    echo "  - 版本     : ${VERSION}"
    echo "  - URL      : http://<服务器IP>:${BACKEND_PORT}"
    echo ""
    echo "前端服务:"
    echo "  - 容器名   : ${FRONTEND_CONTAINER}"
    echo "  - URL      : http://<服务器IP>:${FRONTEND_PORT}"
    echo ""
    echo "管理命令:"
    echo "  - 查看日志 : docker logs -f ${BACKEND_CONTAINER}"
    echo "  - 停止服务 : docker stop ${BACKEND_CONTAINER} ${FRONTEND_CONTAINER}"
    echo "  - 重启服务 : docker restart ${BACKEND_CONTAINER} ${FRONTEND_CONTAINER}"
}

# ============================================================================
# End of file
# ============================================================================
