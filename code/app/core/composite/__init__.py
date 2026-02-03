# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：组合模式模块
内部逻辑：统一处理单个文档和文档集合，实现树形结构管理
设计模式：组合模式（Composite Pattern）
设计原则：SOLID - 开闭原则、里氏替换原则
"""

from .document_node import (
    DocumentNode,
    FileNode,
    FolderNode,
    NodeType,
    NodeFilter,
)

__all__ = [
    "DocumentNode",
    "FileNode",
    "FolderNode",
    "NodeType",
    "NodeFilter",
]
