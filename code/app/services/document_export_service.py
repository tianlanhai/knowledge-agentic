# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：文档导出服务模块
内部逻辑：使用迭代器模式实现大文档的流式导出
设计模式：迭代器模式 + 策略模式 + 外观模式
设计原则：SOLID - 单一职责原则、接口隔离原则
"""

from typing import List, Optional, AsyncIterator, Iterator, Any
from pathlib import Path
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger
import json
import csv
import io

from app.core.iterators.document_iterator import DatabaseDocumentIterator, AsyncDocumentIterator
from app.core.iterators.batch_iterator import BatchIterator, LazyBatchIterator
from app.models.models import Document


class ExportFormat:
    """
    类级注释：导出格式常量
    属性：支持的导出格式类型
    """
    # JSON格式
    JSON = "json"
    # CSV格式
    CSV = "csv"
    # 文本格式
    TXT = "text"
    # Markdown格式
    MD = "markdown"


class DocumentExportService:
    """
    类级注释：文档导出服务
    设计模式：外观模式 - 提供简化的导出接口
    设计模式：迭代器模式 - 使用迭代器流式处理大数据
    职责：
        1. 从数据库读取文档
        2. 使用迭代器批量处理
        3. 流式导出为不同格式

    使用场景：
        - 大量文档导出
        - 内存受限环境
        - 需要实时反馈的导出
    """

    def __init__(self, batch_size: int = 100):
        """
        函数级注释：初始化文档导出服务
        参数：
            batch_size - 批处理大小
        """
        self.batch_size = batch_size

    async def export_documents(
        self,
        db: AsyncSession,
        format_type: str = ExportFormat.JSON,
        filters: Optional[dict] = None,
        batch_size: Optional[int] = None
    ) -> StreamingResponse:
        """
        函数级注释：导出文档为流式响应
        设计模式：策略模式 - 根据格式选择不同的导出策略
        设计模式：迭代器模式 - 使用迭代器流式处理
        参数：
            db - 数据库会话
            format_type - 导出格式类型
            filters - 过滤条件
            batch_size - 批处理大小
        返回值：流式响应对象

        @example
        ```python
        response = await export_service.export_documents(
            db,
            format_type=ExportFormat.JSON,
            filters={"status": "active"}
        )
        ```
        """
        # 内部逻辑：使用批处理大小
        batch_size = batch_size or self.batch_size

        # 内部逻辑：获取导出策略
        export_strategy = self._get_export_strategy(format_type)

        # 内部逻辑：创建数据获取函数
        async def data_fetcher(offset: int, limit: int) -> List[Document]:
            """内部函数：分页获取文档"""
            query = select(Document).offset(offset).limit(limit)
            if filters:
                for key, value in filters.items():
                    query = query.where(getattr(Document, key) == value)
            result = await db.execute(query)
            return result.scalars().all()

        # 内部逻辑：创建异步生成器
        async def generate_export() -> AsyncIterator[str]:
            """内部函数：生成导出内容"""
            async for chunk in export_strategy(data_fetcher, batch_size):
                yield chunk

        # 内部逻辑：确定媒体类型
        media_type = self._get_media_type(format_type)

        # 内部逻辑：返回流式响应
        return StreamingResponse(
            generate_export(),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename=documents.{format_type}",
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no"
            }
        )

    def _get_export_strategy(self, format_type: str) -> callable:
        """
        函数级注释：获取导出策略函数（内部方法）
        设计模式：策略模式 - 根据格式选择策略
        参数：
            format_type - 格式类型
        返回值：导出策略函数
        @private
        """
        strategies = {
            ExportFormat.JSON: self._export_json,
            ExportFormat.CSV: self._export_csv,
            ExportFormat.TXT: self._export_text,
            ExportFormat.MD: self._export_markdown,
        }
        return strategies.get(format_type, self._export_json)

    def _get_media_type(self, format_type: str) -> str:
        """
        函数级注释：获取媒体类型（内部方法）
        参数：
            format_type - 格式类型
        返回值：MIME类型
        @private
        """
        media_types = {
            ExportFormat.JSON: "application/json",
            ExportFormat.CSV: "text/csv",
            ExportFormat.TXT: "text/plain",
            ExportFormat.MD: "text/markdown",
        }
        return media_types.get(format_type, "application/octet-stream")

    async def _export_json(
        self,
        data_fetcher: callable,
        batch_size: int
    ) -> AsyncIterator[str]:
        """
        函数级注释：导出为JSON格式（内部方法）
        设计模式：迭代器模式 - 流式生成JSON
        参数：
            data_fetcher - 数据获取函数
            batch_size - 批处理大小
        生成值：JSON字符串块
        @private
        """
        # 内部逻辑：输出JSON数组开始
        yield "["

        offset = 0
        is_first = True

        while True:
            # 内部逻辑：获取一批数据
            documents = await data_fetcher(offset, batch_size)
            if not documents:
                break

            for doc in documents:
                # 内部逻辑：构建文档JSON对象
                doc_json = {
                    "id": doc.id,
                    "title": doc.title or "",
                    "content": doc.content or "",
                    "file_name": doc.file_name or "",
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                }

                # 内部逻辑：添加逗号分隔
                if not is_first:
                    yield ","
                else:
                    is_first = False

                # 内部逻辑：输出JSON对象
                yield json.dumps(doc_json, ensure_ascii=False)

            offset += len(documents)

            # 内部逻辑：如果获取的数据少于批大小，说明已是最后一批
            if len(documents) < batch_size:
                break

        # 内部逻辑：输出JSON数组结束
        yield "]"

    async def _export_csv(
        self,
        data_fetcher: callable,
        batch_size: int
    ) -> AsyncIterator[str]:
        """
        函数级注释：导出为CSV格式（内部方法）
        设计模式：迭代器模式 - 流式生成CSV
        参数：
            data_fetcher - 数据获取函数
            batch_size - 批处理大小
        生成值：CSV字符串行
        @private
        """
        # 内部逻辑：输出CSV表头
        headers = ["id", "title", "content", "file_name", "created_at"]
        yield ",".join(headers) + "\n"

        offset = 0

        while True:
            documents = await data_fetcher(offset, batch_size)
            if not documents:
                break

            for doc in documents:
                # 内部逻辑：转义CSV特殊字符
                row = [
                    str(doc.id or ""),
                    self._escape_csv_field(doc.title or ""),
                    self._escape_csv_field(doc.content or ""),
                    self._escape_csv_field(doc.file_name or ""),
                    str(doc.created_at.isoformat() if doc.created_at else ""),
                ]
                yield ",".join(row) + "\n"

            offset += len(documents)
            if len(documents) < batch_size:
                break

    def _escape_csv_field(self, value: str) -> str:
        """
        函数级注释：转义CSV字段（内部方法）
        参数：
            value - 原始值
        返回值：转义后的值
        @private
        """
        # 内部逻辑：如果包含逗号、引号或换行，需要用引号包裹并转义
        if any(char in value for char in [',', '"', '\n', '\r']):
            value = value.replace('"', '""')
            return f'"{value}"'
        return value

    async def _export_text(
        self,
        data_fetcher: callable,
        batch_size: int
    ) -> AsyncIterator[str]:
        """
        函数级注释：导出为纯文本格式（内部方法）
        设计模式：迭代器模式 - 流式生成文本
        参数：
            data_fetcher - 数据获取函数
            batch_size - 批处理大小
        生成值：文本字符串行
        @private
        """
        offset = 0

        while True:
            documents = await data_fetcher(offset, batch_size)
            if not documents:
                break

            for doc in documents:
                # 内部逻辑：输出文档分隔符
                yield "=" * 80 + "\n"
                yield f"ID: {doc.id}\n"
                yield f"标题: {doc.title or '无标题'}\n"
                yield f"文件: {doc.file_name or '未知'}\n"
                yield f"时间: {doc.created_at or '未知'}\n"
                yield "-" * 80 + "\n"
                yield f"{doc.content or ''}\n"
                yield "\n"

            offset += len(documents)
            if len(documents) < batch_size:
                break

    async def _export_markdown(
        self,
        data_fetcher: callable,
        batch_size: int
    ) -> AsyncIterator[str]:
        """
        函数级注释：导出为Markdown格式（内部方法）
        设计模式：迭代器模式 - 流式生成Markdown
        参数：
            data_fetcher - 数据获取函数
            batch_size - 批处理大小
        生成值：Markdown字符串行
        @private
        """
        offset = 0
        doc_index = 1

        while True:
            documents = await data_fetcher(offset, batch_size)
            if not documents:
                break

            for doc in documents:
                # 内部逻辑：输出Markdown格式的文档
                yield f"# {doc.title or '无标题'}\n\n"
                yield f"**ID:** {doc.id}  \n"
                yield f"**文件:** {doc.file_name or '未知'}  \n"
                yield f"**时间:** {doc.created_at or '未知'}  \n\n"
                yield "---\n\n"
                yield f"{doc.content or ''}\n\n"
                yield "\n"

                doc_index += 1

            offset += len(documents)
            if len(documents) < batch_size:
                break


class DocumentBatchProcessor:
    """
    类级注释：文档批量处理器
    设计模式：模板方法模式
    职责：提供批量处理的通用框架

    使用场景：
        - 批量更新文档
        - 批量删除文档
        - 批量转换文档
    """

    def __init__(self, batch_size: int = 100):
        """
        函数级注释：初始化批量处理器
        参数：
            batch_size - 批处理大小
        """
        self.batch_size = batch_size

    async def process_batches(
        self,
        db: AsyncSession,
        processor: callable,
        filters: Optional[dict] = None,
        progress_callback: Optional[callable] = None
    ) -> dict:
        """
        函数级注释：批量处理文档
        设计模式：模板方法模式 - 定义处理流程
        设计模式：迭代器模式 - 使用迭代器分批处理
        参数：
            db - 数据库会话
            processor - 处理函数 (batch) -> result
            filters - 过滤条件
            progress_callback - 进度回调
        返回值：处理结果统计
        """
        # 内部变量：统计信息
        stats = {
            "total_processed": 0,
            "total_batches": 0,
            "errors": []
        }

        offset = 0

        try:
            while True:
                # 内部逻辑：获取一批数据
                query = select(Document).offset(offset).limit(self.batch_size)
                if filters:
                    for key, value in filters.items():
                        query = query.where(getattr(Document, key) == value)
                result = await db.execute(query)
                documents = result.scalars().all()

                if not documents:
                    break

                # 内部逻辑：处理当前批次
                try:
                    batch_result = await processor(documents)
                    stats["total_processed"] += len(documents)
                    stats["total_batches"] += 1

                    # 内部逻辑：报告进度
                    if progress_callback:
                        await progress_callback(stats["total_processed"], stats["total_batches"])

                except Exception as e:
                    error_msg = f"批次处理失败 (offset={offset}): {str(e)}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)

                offset += len(documents)

                # 内部逻辑：如果获取的数据少于批大小，说明已是最后一批
                if len(documents) < self.batch_size:
                    break

        except Exception as e:
            logger.error(f"批量处理过程中发生错误: {str(e)}")
            stats["errors"].append(f"处理过程中发生错误: {str(e)}")

        return stats


# 内部变量：导出所有公共接口
__all__ = [
    'DocumentExportService',
    'DocumentBatchProcessor',
    'ExportFormat',
]
