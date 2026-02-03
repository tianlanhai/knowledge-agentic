# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：访问者模式模块
内部逻辑：分离数据结构与操作，支持灵活的数据导出
设计模式：访问者模式（Visitor Pattern）
设计原则：SOLID - 开闭原则、单一职责原则
"""

from .document_visitor import (
    Visitable,
    DocumentVisitor,
    Document,
    DocumentCollection,
    ExportResult,
)

from .export_visitors import (
    JSONExportVisitor,
    CSVExportVisitor,
    MarkdownExportVisitor,
)

__all__ = [
    "Visitable",
    "DocumentVisitor",
    "Document",
    "DocumentCollection",
    "ExportResult",
    "JSONExportVisitor",
    "CSVExportVisitor",
    "MarkdownExportVisitor",
]
