"""
上海宇羲伏天智能科技有限公司出品

文件级注释：API v1 端点包初始化文件
内部逻辑：显式导出所有端点模块，确保路由正确注册
"""

# 显式导出所有端点模块，确保路由正确注册
from app.api.v1.endpoints import ingest
from app.api.v1.endpoints import chat
from app.api.v1.endpoints import search
from app.api.v1.endpoints import documents
from app.api.v1.endpoints import conversations
from app.api.v1.endpoints import model_config
from app.api.v1.endpoints import version
from app.api.v1.endpoints import vector_repair
from app.api.v1.endpoints import health

__all__ = [
    'ingest',
    'chat',
    'search',
    'documents',
    'conversations',
    'model_config',
    'version',
    'vector_repair',
    'health',
]
