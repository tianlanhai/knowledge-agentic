# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：访问者模式导出服务模块
内部逻辑：集成访问者模式实现文档导出功能
设计模式：访问者模式（Visitor Pattern）+ 工厂模式
设计原则：单一职责原则、开闭原则

使用场景：
    - 文档导出为多种格式（JSON、CSV、Markdown、TXT）
    - 批量文档导出
    - 自定义导出格式扩展
"""

from typing import List, Dict, Any, Optional, AsyncIterator
from datetime import datetime
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.responses import StreamingResponse

from app.core.visitors.document_visitor import (
    DocumentVisitor,
    Document,
    DocumentChunk,
    DocumentCollection,
    ExportResult,
    VisitorRegistry
)
from app.core.visitors.export_visitors import (
    JSONExportVisitor,
    CSVExportVisitor,
    MarkdownExportVisitor,
    TextExportVisitor
)
from app.models.models import Document as DocumentModel, VectorMapping


class ExportFormat:
    """
    类级注释：导出格式常量类
    职责：定义支持的导出格式
    """
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "md"
    TEXT = "txt"

    @classmethod
    def all_formats(cls) -> List[str]:
        """获取所有支持的格式"""
        return [cls.JSON, cls.CSV, cls.MARKDOWN, cls.TEXT]

    @classmethod
    def is_supported(cls, format_name: str) -> bool:
        """检查格式是否支持"""
        return format_name.lower() in cls.all_formats()


class VisitorExportService:
    """
    类级注释：访问者导出服务
    设计模式：访问者模式 + 门面模式
    职责：
        1. 统一文档导出接口
        2. 使用访问者模式实现多格式导出
        3. 支持流式导出

    使用场景：
        - 文档批量导出
        - 多格式数据交换
        - 数据备份
    """

    def __init__(self):
        """初始化导出服务"""
        # 内部变量：确保访问者已注册
        self._ensure_visitors_registered()
        logger.info("访问者导出服务初始化完成")

    def _ensure_visitors_registered(self) -> None:
        """
        函数级注释：确保所有访问者已注册
        内部逻辑：检查并注册默认访问者
        @private
        """
        formats = VisitorRegistry.get_supported_formats()
        if not formats:
            VisitorRegistry.register("json", JSONExportVisitor)
            VisitorRegistry.register("csv", CSVExportVisitor)
            VisitorRegistry.register("md", MarkdownExportVisitor)
            VisitorRegistry.register("markdown", MarkdownExportVisitor)
            VisitorRegistry.register("txt", TextExportVisitor)
            VisitorRegistry.register("text", TextExportVisitor)
            logger.info("注册默认导出访问者")

    async def export_document(
        self,
        db: AsyncSession,
        document_id: int,
        format_type: str = ExportFormat.JSON,
        **visitor_kwargs
    ) -> ExportResult:
        """
        函数级注释：导出单个文档
        内部逻辑：查询文档 -> 创建可访问对象 -> 使用访问者导出
        参数：
            db - 数据库会话
            document_id - 文档ID
            format_type - 导出格式
            **visitor_kwargs - 访问者参数
        返回值：导出结果
        """
        # 内部逻辑：查询文档
        query = select(DocumentModel).where(DocumentModel.id == document_id)
        result = await db.execute(query)
        doc_model = result.scalar_one_or_none()

        if not doc_model:
            return ExportResult(
                content="",
                format=format_type,
                size=0
            )

        # 内部逻辑：创建可访问的文档对象
        document = Document(
            id=doc_model.id,
            title=doc_model.file_name,
            content=doc_model.file_path,  # 使用路径作为内容
            file_name=doc_model.file_name,
            file_type=doc_model.source_type,
            created_at=doc_model.created_at,
            updated_at=doc_model.updated_at,
            metadata={"file_hash": doc_model.file_hash}
        )

        # 内部逻辑：获取访问者并导出
        visitor = VisitorRegistry.get_visitor(format_type, **visitor_kwargs)
        if not visitor:
            logger.error(f"不支持的导出格式: {format_type}")
            return ExportResult(
                content="",
                format=format_type,
                size=0
            )

        export_result = document.accept(visitor)
        logger.info(f"导出文档 {document_id} 为 {format_type} 格式")
        return export_result

    async def export_documents(
        self,
        db: AsyncSession,
        document_ids: List[int],
        format_type: str = ExportFormat.JSON,
        collection_name: str = "导出文档集合",
        **visitor_kwargs
    ) -> ExportResult:
        """
        函数级注释：批量导出文档
        内部逻辑：查询文档列表 -> 创建文档集合 -> 使用访问者导出
        参数：
            db - 数据库会话
            document_ids - 文档ID列表
            format_type - 导出格式
            collection_name - 集合名称
            **visitor_kwargs - 访问者参数
        返回值：导出结果
        """
        # 内部逻辑：查询文档
        query = select(DocumentModel).where(DocumentModel.id.in_(document_ids))
        result = await db.execute(query)
        doc_models = result.scalars().all()

        # 内部逻辑：创建文档集合
        collection = DocumentCollection(
            name=collection_name,
            documents=[],
            metadata={"exported_at": datetime.now().isoformat()}
        )

        # 内部逻辑：填充文档
        for doc_model in doc_models:
            document = Document(
                id=doc_model.id,
                title=doc_model.file_name,
                content=doc_model.file_path,
                file_name=doc_model.file_name,
                file_type=doc_model.source_type,
                created_at=doc_model.created_at,
                updated_at=doc_model.updated_at,
                metadata={"file_hash": doc_model.file_hash}
            )
            collection.add_document(document)

        # 内部逻辑：获取访问者并导出
        visitor = VisitorRegistry.get_visitor(format_type, **visitor_kwargs)
        if not visitor:
            logger.error(f"不支持的导出格式: {format_type}")
            return ExportResult(
                content="",
                format=format_type,
                size=0
            )

        export_result = collection.accept(visitor)
        logger.info(f"批量导出 {len(doc_models)} 个文档为 {format_type} 格式")
        return export_result

    async def export_all_documents(
        self,
        db: AsyncSession,
        format_type: str = ExportFormat.JSON,
        tags: Optional[List[str]] = None,
        **visitor_kwargs
    ) -> ExportResult:
        """
        函数级注释：导出所有文档
        内部逻辑：查询所有文档 -> 创建文档集合 -> 导出
        参数：
            db - 数据库会话
            format_type - 导出格式
            tags - 标签过滤
            **visitor_kwargs - 访问者参数
        返回值：导出结果
        """
        # 内部逻辑：构建查询
        query = select(DocumentModel)
        result = await db.execute(query)
        doc_models = result.scalars().all()

        # 内部逻辑：标签过滤
        if tags:
            filtered_models = []
            for doc in doc_models:
                if doc.tags:
                    import json
                    try:
                        doc_tags = json.loads(doc.tags) if isinstance(doc.tags, str) else doc.tags
                        if any(tag in doc_tags for tag in tags):
                            filtered_models.append(doc)
                    except:
                        pass
            doc_models = filtered_models

        # 内部逻辑：获取所有文档ID
        document_ids = [doc.id for doc in doc_models]

        return await self.export_documents(
            db=db,
            document_ids=document_ids,
            format_type=format_type,
            collection_name="全部文档",
            **visitor_kwargs
        )

    async def export_document_chunks(
        self,
        db: AsyncSession,
        document_id: int,
        format_type: str = ExportFormat.JSON,
        **visitor_kwargs
    ) -> ExportResult:
        """
        函数级注释：导出文档片段
        内部逻辑：查询文档片段 -> 创建片段集合 -> 导出
        参数：
            db - 数据库会话
            document_id - 文档ID
            format_type - 导出格式
            **visitor_kwargs - 访问者参数
        返回值：导出结果
        """
        # 内部逻辑：查询文档片段
        query = select(VectorMapping).where(VectorMapping.document_id == document_id)
        result = await db.execute(query)
        mappings = result.scalars().all()

        if not mappings:
            return ExportResult(
                content="",
                format=format_type,
                size=0
            )

        # 内部逻辑：创建片段集合
        chunks = []
        for mapping in mappings:
            chunk = DocumentChunk(
                chunk_id=mapping.chunk_id,
                document_id=document_id,
                content=mapping.chunk_content,
                chunk_index=mapping.id,
                metadata={"mapping_id": mapping.id}
            )
            chunks.append(chunk)

        # 内部逻辑：使用第一个片段的访问者导出
        visitor = VisitorRegistry.get_visitor(format_type, **visitor_kwargs)
        if not visitor:
            return ExportResult(
                content="",
                format=format_type,
                size=0
            )

        # 内部逻辑：逐个导出片段并合并
        contents = []
        for chunk in chunks:
            result = chunk.accept(visitor)
            contents.append(result.content)

        combined_content = "\n\n".join(contents)
        return ExportResult(
            content=combined_content,
            format=format_type,
            size=len(combined_content.encode('utf-8'))
        )

    async def export_streaming(
        self,
        db: AsyncSession,
        format_type: str = ExportFormat.JSON,
        tags: Optional[List[str]] = None
    ) -> StreamingResponse:
        """
        函数级注释：流式导出文档
        内部逻辑：异步生成文档 -> 流式响应
        参数：
            db - 数据库会话
            format_type - 导出格式
            tags - 标签过滤
        返回值：流式响应对象
        """
        async def generate() -> AsyncIterator[str]:
            """生成流式内容"""
            query = select(DocumentModel)
            result = await db.execute(query)
            doc_models = result.scalars().all()

            if format_type == ExportFormat.JSON:
                yield "[\n"
                for i, doc_model in enumerate(doc_models):
                    document = Document(
                        id=doc_model.id,
                        title=doc_model.file_name,
                        content=doc_model.file_path,
                        file_name=doc_model.file_name,
                        file_type=doc_model.source_type,
                        created_at=doc_model.created_at,
                        updated_at=doc_model.updated_at
                    )
                    visitor = JSONExportVisitor(indent=2)
                    result = document.accept(visitor)
                    yield result.content
                    if i < len(doc_models) - 1:
                        yield ",\n"
                yield "\n]"

            elif format_type == ExportFormat.CSV:
                visitor = CSVExportVisitor()
                # 内部逻辑：输出表头
                yield "ID,标题,文件名,文件类型,创建时间,更新时间\n"
                for doc_model in doc_models:
                    document = Document(
                        id=doc_model.id,
                        title=doc_model.file_name,
                        content=doc_model.file_path,
                        file_name=doc_model.file_name,
                        file_type=doc_model.source_type,
                        created_at=doc_model.created_at,
                        updated_at=doc_model.updated_at
                    )
                    result = document.accept(visitor)
                    yield result.content + "\n"

            elif format_type == ExportFormat.MARKDOWN:
                visitor = MarkdownExportVisitor()
                for doc_model in doc_models:
                    document = Document(
                        id=doc_model.id,
                        title=doc_model.file_name,
                        content=doc_model.file_path,
                        file_name=doc_model.file_name,
                        file_type=doc_model.source_type,
                        created_at=doc_model.created_at,
                        updated_at=doc_model.updated_at
                    )
                    result = document.accept(visitor)
                    yield result.content + "\n\n---\n\n"

            else:  # TEXT
                visitor = TextExportVisitor()
                for doc_model in doc_models:
                    document = Document(
                        id=doc_model.id,
                        title=doc_model.file_name,
                        content=doc_model.file_path,
                        file_name=doc_model.file_name,
                        file_type=doc_model.source_type,
                        created_at=doc_model.created_at,
                        updated_at=doc_model.updated_at
                    )
                    result = document.accept(visitor)
                    yield result.content + "\n\n"

        # 内部逻辑：确定媒体类型
        media_types = {
            ExportFormat.JSON: "application/json",
            ExportFormat.CSV: "text/csv",
            ExportFormat.MARKDOWN: "text/markdown",
            ExportFormat.TEXT: "text/plain"
        }

        return StreamingResponse(
            generate(),
            media_type=media_types.get(format_type, "text/plain"),
            headers={
                "Content-Disposition": f"attachment; filename=export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}"
            }
        )

    def get_supported_formats(self) -> List[str]:
        """
        函数级注释：获取支持的导出格式
        返回值：格式名称列表
        """
        return VisitorRegistry.get_supported_formats()

    def register_custom_visitor(self, format_name: str, visitor_class: type) -> None:
        """
        函数级注释：注册自定义访问者
        内部逻辑：扩展支持的导出格式
        参数：
            format_name - 格式名称
            visitor_class - 访问者类
        """
        VisitorRegistry.register(format_name, visitor_class)
        logger.info(f"注册自定义导出访问者: {format_name}")

    def create_export_visitor(self, format_type: str, **kwargs) -> Optional[DocumentVisitor]:
        """
        函数级注释：创建导出访问者实例
        参数：
            format_type - 导出格式
            **kwargs - 访问者参数
        返回值：访问者实例或None
        """
        return VisitorRegistry.get_visitor(format_type, **kwargs)


# 内部变量：导出公共接口
__all__ = [
    'VisitorExportService',
    'ExportFormat',
]
