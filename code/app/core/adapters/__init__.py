# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：向量存储适配器模块
内部逻辑：将不同的向量存储实现统一为同一接口，支持灵活切换
设计模式：适配器模式（Adapter Pattern）
设计原则：SOLID - 开闭原则、依赖倒置原则
"""

from .vector_store_adapter import (
    VectorStoreAdapter,
    VectorStoreConfig,
    SearchQuery,
    SearchResult,
    VectorStoreAdapterFactory,
)

from .chroma_adapter import ChromaAdapter

__all__ = [
    "VectorStoreAdapter",
    "VectorStoreConfig",
    "SearchQuery",
    "SearchResult",
    "VectorStoreAdapterFactory",
    "ChromaAdapter",
]
