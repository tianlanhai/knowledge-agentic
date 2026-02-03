# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：导出访问者实现类
内部逻辑：实现各种格式的数据导出访问者
设计模式：访问者模式（Visitor Pattern）- 具体访问者
设计原则：SOLID - 单一职责原则
"""

import json
import csv
import io
from typing import Any, List, Dict
from datetime import datetime
from loguru import logger

from app.core.visitors.document_visitor import (
    DocumentVisitor,
    Document,
    DocumentChunk,
    DocumentCollection,
    ExportResult,
    VisitorRegistry,
)


class JSONExportVisitor(DocumentVisitor):
    """
    类级注释：JSON导出访问者
    设计模式：访问者模式（Visitor Pattern）- 具体访问者
    职责：将文档导出为JSON格式
    """

    def __init__(self, indent: int = 2, ensure_ascii: bool = False):
        """
        函数级注释：初始化JSON导出访问者
        参数：
            indent: 缩进空格数
            ensure_ascii: 是否确保ASCII编码
        """
        self.indent = indent
        self.ensure_ascii = ensure_ascii

    def visit_document(self, document: Document) -> ExportResult:
        """
        函数级注释：导出单个文档为JSON
        """
        data = {
            "id": document.id,
            "title": document.title,
            "content": document.content,
            "file_name": document.file_name,
            "file_type": document.file_type,
            "created_at": document.created_at.isoformat() if document.created_at else None,
            "updated_at": document.updated_at.isoformat() if document.updated_at else None,
            "metadata": document.metadata
        }

        content = json.dumps(data, indent=self.indent, ensure_ascii=self.ensure_ascii)
        return ExportResult(
            content=content,
            format="json",
            size=len(content.encode('utf-8'))
        )

    def visit_chunk(self, chunk: DocumentChunk) -> ExportResult:
        """
        函数级注释：导出文档片段为JSON
        """
        data = {
            "chunk_id": chunk.chunk_id,
            "document_id": chunk.document_id,
            "content": chunk.content,
            "chunk_index": chunk.chunk_index,
            "metadata": chunk.metadata
        }

        content = json.dumps(data, indent=self.indent, ensure_ascii=self.ensure_ascii)
        return ExportResult(
            content=content,
            format="json",
            size=len(content.encode('utf-8'))
        )

    def visit_collection(self, collection: DocumentCollection) -> ExportResult:
        """
        函数级注释：导出文档集合为JSON
        """
        data = {
            "name": collection.name,
            "count": len(collection.documents),
            "metadata": collection.metadata,
            "documents": [
                {
                    "id": doc.id,
                    "title": doc.title,
                    "content": doc.content,
                    "file_name": doc.file_name,
                    "file_type": doc.file_type,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
                    "metadata": doc.metadata
                }
                for doc in collection.documents
            ]
        }

        content = json.dumps(data, indent=self.indent, ensure_ascii=self.ensure_ascii)
        return ExportResult(
            content=content,
            format="json",
            size=len(content.encode('utf-8'))
        )


class CSVExportVisitor(DocumentVisitor):
    """
    类级注释：CSV导出访问者
    设计模式：访问者模式（Visitor Pattern）- 具体访问者
    职责：将文档导出为CSV格式
    """

    def __init__(self, delimiter: str = ",", encoding: str = "utf-8-sig"):
        """
        函数级注释：初始化CSV导出访问者
        参数：
            delimiter: 分隔符
            encoding: 编码格式
        """
        self.delimiter = delimiter
        self.encoding = encoding

    def visit_document(self, document: Document) -> ExportResult:
        """
        函数级注释：导出单个文档为CSV
        """
        output = io.StringIO()
        writer = csv.writer(output, delimiter=self.delimiter)

        # 内部逻辑：写入表头
        writer.writerow(["ID", "标题", "内容", "文件名", "文件类型", "创建时间", "更新时间"])

        # 内部逻辑：写入数据
        writer.writerow([
            document.id,
            document.title,
            document.content,
            document.file_name,
            document.file_type,
            document.created_at.isoformat() if document.created_at else "",
            document.updated_at.isoformat() if document.updated_at else ""
        ])

        content = output.getvalue()
        return ExportResult(
            content=content,
            format="csv",
            size=len(content.encode(self.encoding))
        )

    def visit_chunk(self, chunk: DocumentChunk) -> ExportResult:
        """
        函数级注释：导出文档片段为CSV
        """
        output = io.StringIO()
        writer = csv.writer(output, delimiter=self.delimiter)

        writer.writerow(["片段ID", "文档ID", "内容", "片段索引"])
        writer.writerow([
            chunk.chunk_id,
            chunk.document_id,
            chunk.content,
            chunk.chunk_index
        ])

        content = output.getvalue()
        return ExportResult(
            content=content,
            format="csv",
            size=len(content.encode(self.encoding))
        )

    def visit_collection(self, collection: DocumentCollection) -> ExportResult:
        """
        函数级注释：导出文档集合为CSV
        """
        output = io.StringIO()
        writer = csv.writer(output, delimiter=self.delimiter)

        # 内部逻辑：写入表头
        writer.writerow(["ID", "标题", "内容", "文件名", "文件类型", "创建时间", "更新时间"])

        # 内部逻辑：写入所有文档
        for doc in collection.documents:
            writer.writerow([
                doc.id,
                doc.title,
                doc.content,
                doc.file_name,
                doc.file_type,
                doc.created_at.isoformat() if doc.created_at else "",
                doc.updated_at.isoformat() if doc.updated_at else ""
            ])

        content = output.getvalue()
        return ExportResult(
            content=content,
            format="csv",
            size=len(content.encode(self.encoding))
        )


class MarkdownExportVisitor(DocumentVisitor):
    """
    类级注释：Markdown导出访问者
    设计模式：访问者模式（Visitor Pattern）- 具体访问者
    职责：将文档导出为Markdown格式
    """

    def __init__(self, include_metadata: bool = True):
        """
        函数级注释：初始化Markdown导出访问者
        参数：
            include_metadata: 是否包含元数据
        """
        self.include_metadata = include_metadata

    def visit_document(self, document: Document) -> ExportResult:
        """
        函数级注释：导出单个文档为Markdown
        """
        lines = []

        # 内部逻辑：添加标题
        lines.append(f"# {document.title}\n")

        # 内部逻辑：添加元数据
        if self.include_metadata:
            lines.append("## 元数据\n")
            lines.append(f"- **文件名**: {document.file_name}")
            lines.append(f"- **文件类型**: {document.file_type}")
            if document.created_at:
                lines.append(f"- **创建时间**: {document.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            if document.updated_at:
                lines.append(f"- **更新时间**: {document.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append("")

        # 内部逻辑：添加内容
        lines.append("## 内容\n")
        lines.append(document.content)

        content = "\n".join(lines)
        return ExportResult(
            content=content,
            format="md",
            size=len(content.encode('utf-8'))
        )

    def visit_chunk(self, chunk: DocumentChunk) -> ExportResult:
        """
        函数级注释：导出文档片段为Markdown
        """
        lines = [
            f"## 片段 {chunk.chunk_index}\n",
            chunk.content,
            ""
        ]

        if self.include_metadata and chunk.metadata:
            lines.append("### 元数据")
            for key, value in chunk.metadata.items():
                lines.append(f"- **{key}**: {value}")
            lines.append("")

        content = "\n".join(lines)
        return ExportResult(
            content=content,
            format="md",
            size=len(content.encode('utf-8'))
        )

    def visit_collection(self, collection: DocumentCollection) -> ExportResult:
        """
        函数级注释：导出文档集合为Markdown
        """
        lines = [
            f"# {collection.name}\n",
            f"**文档数量**: {len(collection.documents)}\n"
        ]

        # 内部逻辑：添加目录
        lines.append("## 目录\n")
        for doc in collection.documents:
            lines.append(f"- [{doc.title}](#document-{doc.id})")
        lines.append("")

        # 内部逻辑：添加所有文档
        for doc in collection.documents:
            lines.append(f"---\n")
            doc_result = self.visit_document(doc)
            lines.append(doc_result.content)

        content = "\n".join(lines)
        return ExportResult(
            content=content,
            format="md",
            size=len(content.encode('utf-8'))
        )


class TextExportVisitor(DocumentVisitor):
    """
    类级注释：纯文本导出访问者
    设计模式：访问者模式（Visitor Pattern）- 具体访问者
    职责：将文档导出为纯文本格式
    """

    def __init__(self, include_header: bool = True):
        """
        函数级注释：初始化文本导出访问者
        参数：
            include_header: 是否包含标题头
        """
        self.include_header = include_header

    def visit_document(self, document: Document) -> ExportResult:
        """
        函数级注释：导出单个文档为纯文本
        """
        lines = []

        if self.include_header:
            lines.append(f"{'='*60}")
            lines.append(f"标题: {document.title}")
            lines.append(f"文件: {document.file_name}")
            lines.append(f"{'='*60}")
            lines.append("")

        lines.append(document.content)

        content = "\n".join(lines)
        return ExportResult(
            content=content,
            format="txt",
            size=len(content.encode('utf-8'))
        )

    def visit_chunk(self, chunk: DocumentChunk) -> ExportResult:
        """
        函数级注释：导出文档片段为纯文本
        """
        content = f"[片段 {chunk.chunk_index}]\n{chunk.content}"
        return ExportResult(
            content=content,
            format="txt",
            size=len(content.encode('utf-8'))
        )

    def visit_collection(self, collection: DocumentCollection) -> ExportResult:
        """
        函数级注释：导出文档集合为纯文本
        """
        lines = [
            f"集合: {collection.name}",
            f"文档数量: {len(collection.documents)}",
            ""
        ]

        for doc in collection.documents:
            lines.append(f"\n{'-'*60}")
            doc_result = self.visit_document(doc)
            lines.append(doc_result.content)

        content = "\n".join(lines)
        return ExportResult(
            content=content,
            format="txt",
            size=len(content.encode('utf-8'))
        )


# 内部逻辑：自动注册所有导出访问者
VisitorRegistry.register("json", JSONExportVisitor)
VisitorRegistry.register("csv", CSVExportVisitor)
VisitorRegistry.register("md", MarkdownExportVisitor)
VisitorRegistry.register("markdown", MarkdownExportVisitor)
VisitorRegistry.register("txt", TextExportVisitor)
VisitorRegistry.register("text", TextExportVisitor)
