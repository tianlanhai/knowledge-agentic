# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：迭代器模式模块
内部逻辑：实现大批量数据的惰性加载和批量处理
设计模式：迭代器模式（Iterator Pattern）
设计原则：SOLID - 单一职责原则
"""

from .batch_iterator import BatchIterator, BatchIteratorFactory
from .document_iterator import DocumentIterator, AsyncDocumentIterator

__all__ = [
    "BatchIterator",
    "BatchIteratorFactory",
    "DocumentIterator",
    "AsyncDocumentIterator",
]
