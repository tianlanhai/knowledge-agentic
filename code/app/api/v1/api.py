"""
上海宇羲伏天智能科技有限公司出品

文件级注释：API 路由聚合文件
内部逻辑：集成所有子路由模块并统一导出
"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    ingest,
    chat,
    search,
    documents,
    conversations,
    model_config,
    version,
    vector_repair,
)
# 内部变量：直接导入 health 模块，避免通过 __init__.py 的潜在问题
from app.api.v1.endpoints import health

api_router = APIRouter()

# 内部逻辑：注册知识摄入相关接口
api_router.include_router(ingest.router, prefix="/ingest", tags=["Knowledge Ingestion"])

# 内部逻辑：注册文档管理相关接口
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])

# 内部逻辑：注册对话问答相关接口
api_router.include_router(chat.router, prefix="/chat", tags=["Chat & QA"])

# 内部逻辑：注册搜索相关接口
api_router.include_router(search.router, prefix="/search", tags=["Search"])

# 内部逻辑：注册对话持久化相关接口
api_router.include_router(
    conversations.router, prefix="/conversations", tags=["Conversations"]
)

# 内部逻辑：注册模型配置相关接口
api_router.include_router(
    model_config.router, prefix="/model-config", tags=["Model Config"]
)

# 内部逻辑：注册版本信息相关接口
api_router.include_router(version.router, prefix="/version", tags=["Version"])

# 内部逻辑：注册向量库修复相关接口
api_router.include_router(
    vector_repair.router, prefix="/vector-repair", tags=["Vector Repair"]
)

# 内部逻辑：注册健康检查相关接口
api_router.include_router(health.router, prefix="/health", tags=["Health Check"])

