"""
上海宇羲伏天智能科技有限公司出品

文件级注释：数据库模型导出模块
内部逻辑：统一导出所有数据库模型，方便其他模块导入
"""

# 内部逻辑：导入基础配置
from app.models.models import Base, TaskStatus

# 内部逻辑：导入文档相关模型
from app.models.models import Document, VectorMapping, IngestTask

# 内部逻辑：导入对话持久化相关模型
from app.models.conversation import (
    Conversation,
    Message,
    MessageSource,
    TokenUsage,
    MessageRole,
)

# 内部逻辑：导入模型配置相关模型
from app.models.model_config import ModelConfig, EmbeddingConfig

# 内部变量：导出所有模型
__all__ = [
    # 基础配置
    "Base",
    "TaskStatus",
    # 文档相关
    "Document",
    "VectorMapping",
    "IngestTask",
    # 对话持久化相关
    "Conversation",
    "Message",
    "MessageSource",
    "TokenUsage",
    "MessageRole",
    # 模型配置相关
    "ModelConfig",
    "EmbeddingConfig",
]
