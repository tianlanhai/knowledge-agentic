# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：Embedding桥接模式模块
内部逻辑：将Embedding抽象与实现解耦，支持独立扩展
设计模式：桥接模式（Bridge Pattern）
设计原则：SOLID - 依赖倒置原则、开闭原则
"""

from .embedding_bridge import EmbeddingBridge, EmbeddingBridgeFactory
from .implementations import (
    OllamaEmbeddingImpl,
    ZhipuAIEmbeddingImpl,
    LocalEmbeddingImpl,
    OpenAIEmbeddingImpl,
)

__all__ = [
    "EmbeddingBridge",
    "EmbeddingBridgeFactory",
    "OllamaEmbeddingImpl",
    "ZhipuAIEmbeddingImpl",
    "LocalEmbeddingImpl",
    "OpenAIEmbeddingImpl",
]
