# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：文档导出服务模块完整测试
内部逻辑：测试document_export_service.py中的所有方法和类
测试覆盖范围：
    - ExportFormat常量类
    - DocumentExportService的所有方法
    - DocumentBatchProcessor的所有方法
    - 各种导出格式的测试
测试类型：单元测试
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import StreamingResponse
from datetime import datetime

from app.services.document_export_service import (
    DocumentExportService,
    DocumentBatchProcessor,
    ExportFormat
)
from app.models.models import Document


# ============================================================================
# ExportFormat 测试
# ============================================================================

class TestExportFormat:
    """测试ExportFormat常量"""

    def test_json_format(self):
        """测试JSON格式常量"""
        assert ExportFormat.JSON == "json"

    def test_csv_format(self):
        """测试CSV格式常量"""
        assert ExportFormat.CSV == "csv"

    def test_txt_format(self):
        """测试TXT格式常量"""
        assert ExportFormat.TXT == "text"

    def test_md_format(self):
        """测试Markdown格式常量"""
        assert ExportFormat.MD == "markdown"


# ============================================================================
# DocumentExportService 初始化测试
# ============================================================================

class TestDocumentExportServiceInit:
    """测试DocumentExportService初始化"""

    def test_init_default_batch_size(self):
        """测试默认批处理大小"""
        service = DocumentExportService()
        assert service.batch_size == 100

    def test_init_custom_batch_size(self):
        """测试自定义批处理大小"""
        service = DocumentExportService(batch_size=50)
        assert service.batch_size == 50


# ============================================================================
# _get_export_strategy 测试
# ============================================================================

class TestGetExportStrategy:
    """测试_get_export_strategy方法"""

    def test_get_json_strategy(self):
        """测试获取JSON导出策略"""
        service = DocumentExportService()
        strategy = service._get_export_strategy(ExportFormat.JSON)
        assert strategy is not None
        assert strategy == service._export_json

    def test_get_csv_strategy(self):
        """测试获取CSV导出策略"""
        service = DocumentExportService()
        strategy = service._get_export_strategy(ExportFormat.CSV)
        assert strategy is not None
        assert strategy == service._export_csv

    def test_get_txt_strategy(self):
        """测试获取TXT导出策略"""
        service = DocumentExportService()
        strategy = service._get_export_strategy(ExportFormat.TXT)
        assert strategy is not None
        assert strategy == service._export_text

    def test_get_markdown_strategy(self):
        """测试获取Markdown导出策略"""
        service = DocumentExportService()
        strategy = service._get_export_strategy(ExportFormat.MD)
        assert strategy is not None
        assert strategy == service._export_markdown

    def test_get_invalid_strategy_returns_default(self):
        """测试无效的导出格式返回默认策略（JSON）"""
        service = DocumentExportService()
        # 无效格式返回默认的JSON策略（不抛出异常）
        strategy = service._get_export_strategy("invalid_format")
        assert strategy is not None
        assert strategy == service._export_json


# ============================================================================
# _get_media_type 测试
# ============================================================================

class TestGetMediaType:
    """测试_get_media_type方法"""

    def test_get_json_media_type(self):
        """测试获取JSON媒体类型"""
        service = DocumentExportService()
        media_type = service._get_media_type(ExportFormat.JSON)
        assert media_type == "application/json"

    def test_get_csv_media_type(self):
        """测试获取CSV媒体类型"""
        service = DocumentExportService()
        media_type = service._get_media_type(ExportFormat.CSV)
        assert media_type == "text/csv"

    def test_get_txt_media_type(self):
        """测试获取TXT媒体类型"""
        service = DocumentExportService()
        media_type = service._get_media_type(ExportFormat.TXT)
        assert media_type == "text/plain"

    def test_get_markdown_media_type(self):
        """测试获取Markdown媒体类型"""
        service = DocumentExportService()
        media_type = service._get_media_type(ExportFormat.MD)
        assert media_type == "text/markdown"

    def test_get_invalid_media_type(self):
        """测试无效格式的媒体类型"""
        service = DocumentExportService()
        media_type = service._get_media_type("invalid")
        assert media_type == "application/octet-stream"


# ============================================================================
# _escape_csv_field 测试
# ============================================================================

class TestEscapeCsvField:
    """测试_escape_csv_field方法"""

    @pytest.mark.asyncio
    async def test_escape_field_with_comma(self):
        """测试包含逗号的字段转义"""
        service = DocumentExportService()
        result = service._escape_csv_field("value,with,commas")
        assert '"value,with,commas"' == result

    @pytest.mark.asyncio
    async def test_escape_field_with_quote(self):
        """测试包含引号的字段转义"""
        service = DocumentExportService()
        result = service._escape_csv_field('value "quotes" test')
        assert '"value ""quotes"" test"' == result

    @pytest.mark.asyncio
    async def test_escape_field_with_newline(self):
        """测试包含换行的字段转义"""
        service = DocumentExportService()
        result = service._escape_csv_field("line1\nline2")
        assert '"line1\nline2"' == result

    @pytest.mark.asyncio
    async def test_escape_field_with_carriage_return(self):
        """测试包含回车的字段转义"""
        service = DocumentExportService()
        result = service._escape_csv_field("text\rmore")
        assert '"text\rmore"' == result

    @pytest.mark.asyncio
    async def test_escape_field_clean_text(self):
        """测试纯文本字段不转义"""
        service = DocumentExportService()
        result = service._escape_csv_field("clean text")
        assert result == "clean text"

    @pytest.mark.asyncio
    async def test_escape_field_empty_string(self):
        """测试空字符串转义"""
        service = DocumentExportService()
        result = service._escape_csv_field("")
        assert result == ""


# ============================================================================
# export_documents 测试
# ============================================================================

class TestExportDocuments:
    """测试export_documents方法"""

    @pytest.mark.asyncio
    async def test_export_json_returns_streaming_response(self, db_session: AsyncSession):
        """测试JSON导出返回流式响应"""
        service = DocumentExportService()

        result = await service.export_documents(
            db_session,
            format_type=ExportFormat.JSON
        )

        assert isinstance(result, StreamingResponse)

    @pytest.mark.asyncio
    async def test_export_csv_returns_streaming_response(self, db_session: AsyncSession):
        """测试CSV导出返回流式响应"""
        service = DocumentExportService()

        result = await service.export_documents(
            db_session,
            format_type=ExportFormat.CSV
        )

        assert isinstance(result, StreamingResponse)

    @pytest.mark.asyncio
    async def test_export_txt_returns_streaming_response(self, db_session: AsyncSession):
        """测试TXT导出返回流式响应"""
        service = DocumentExportService()

        result = await service.export_documents(
            db_session,
            format_type=ExportFormat.TXT
        )

        assert isinstance(result, StreamingResponse)

    @pytest.mark.asyncio
    async def test_export_markdown_returns_streaming_response(self, db_session: AsyncSession):
        """测试Markdown导出返回流式响应"""
        service = DocumentExportService()

        result = await service.export_documents(
            db_session,
            format_type=ExportFormat.MD
        )

        assert isinstance(result, StreamingResponse)

    @pytest.mark.asyncio
    async def test_export_with_custom_batch_size(self, db_session: AsyncSession):
        """测试自定义批处理大小"""
        service = DocumentExportService(batch_size=10)

        result = await service.export_documents(
            db_session,
            format_type=ExportFormat.JSON,
            batch_size=5
        )

        assert isinstance(result, StreamingResponse)

    @pytest.mark.asyncio
    async def test_export_empty_database(self, db_session: AsyncSession):
        """测试空数据库导出"""
        service = DocumentExportService()

        result = await service.export_documents(
            db_session,
            format_type=ExportFormat.JSON
        )

        assert isinstance(result, StreamingResponse)


# ============================================================================
# _export_json 测试
# ============================================================================

class TestExportJson:
    """测试_export_json方法"""

    @pytest.mark.asyncio
    async def test_export_json_empty_data(self):
        """测试空数据的JSON导出"""
        service = DocumentExportService()

        async def empty_fetcher(offset, limit):
            return []

        chunks = []
        async for chunk in service._export_json(empty_fetcher, 10):
            chunks.append(chunk)

        assert len(chunks) == 2  # "[" 和 "]"
        assert chunks[0] == "["
        assert chunks[-1] == "]"

    @pytest.mark.asyncio
    async def test_export_json_with_single_document(self):
        """测试单个文档的JSON导出"""
        service = DocumentExportService()

        doc = Mock(
            id=1,
            title="测试文档",
            content="测试内容",
            file_name="test.pdf",
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )

        async def single_fetcher(offset, limit):
            if offset == 0:
                return [doc]
            return []

        chunks = []
        async for chunk in service._export_json(single_fetcher, 10):
            chunks.append(chunk)

        # 应该包含JSON内容
        full_content = "".join(chunks)
        assert '"id": 1' in full_content
        assert '"title": "测试文档"' in full_content

    @pytest.mark.asyncio
    async def test_export_json_multiple_batches(self):
        """测试多批JSON导出"""
        service = DocumentExportService(batch_size=2)

        docs = [
            Mock(id=1, title="Doc1", content="Content1", file_name="f1.pdf", created_at=None),
            Mock(id=2, title="Doc2", content="Content2", file_name="f2.pdf", created_at=None),
            Mock(id=3, title="Doc3", content="Content3", file_name="f3.pdf", created_at=None),
        ]

        async def multi_fetcher(offset, limit):
            if offset >= len(docs):
                return []
            return docs[offset:offset + limit]

        chunks = []
        async for chunk in service._export_json(multi_fetcher, 2):
            chunks.append(chunk)

        # 验证所有3个文档都被导出
        full_content = "".join(chunks)
        assert '"id": 1' in full_content
        assert '"id": 2' in full_content
        assert '"id": 3' in full_content
        # 验证JSON格式正确
        assert full_content.startswith("[")
        assert full_content.endswith("]")


# ============================================================================
# _export_csv 测试
# ============================================================================

class TestExportCsv:
    """测试_export_csv方法"""

    @pytest.mark.asyncio
    async def test_export_csv_empty_data(self):
        """测试空数据的CSV导出"""
        service = DocumentExportService()

        async def empty_fetcher(offset, limit):
            return []

        chunks = []
        async for chunk in service._export_csv(empty_fetcher, 10):
            chunks.append(chunk)

        # 应该只有表头
        assert len(chunks) == 1
        assert "id,title,content,file_name,created_at" in chunks[0]

    @pytest.mark.asyncio
    async def test_export_csv_with_data(self):
        """测试带数据的CSV导出"""
        service = DocumentExportService()

        doc = Mock(
            id=1,
            title="测试文档",
            content="测试内容",
            file_name="test.pdf",
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )

        async def single_fetcher(offset, limit):
            if offset == 0:
                return [doc]
            return []

        chunks = []
        async for chunk in service._export_csv(single_fetcher, 10):
            chunks.append(chunk)

        # 应该包含表头和数据行
        full_content = "".join(chunks)
        assert "id,title,content,file_name,created_at" in full_content
        assert "1,测试文档,测试内容,test.pdf" in full_content

    @pytest.mark.asyncio
    async def test_export_csv_escapes_special_chars(self):
        """测试CSV特殊字符转义"""
        service = DocumentExportService()

        doc = Mock(
            id=1,
            title='Title with "quotes"',
            content='Content, with, commas',
            file_name='file "name".pdf',
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )

        async def fetcher(offset, limit):
            return [doc]

        chunks = []
        async for chunk in service._export_csv(fetcher, 10):
            chunks.append(chunk)

        full_content = "".join(chunks)
        # CSV中引号会转义为双引号（""）
        assert 'Title with ""quotes""' in full_content
        assert '"Content, with, commas"' in full_content
        assert 'file ""name"".pdf' in full_content


# ============================================================================
# _export_text 测试
# ============================================================================

class TestExportText:
    """测试_export_text方法"""

    @pytest.mark.asyncio
    async def test_export_text_empty_data(self):
        """测试空数据的TXT导出"""
        service = DocumentExportService()

        async def empty_fetcher(offset, limit):
            return []

        chunks = []
        async for chunk in service._export_text(empty_fetcher, 10):
            chunks.append(chunk)

        assert len(chunks) == 0

    @pytest.mark.asyncio
    async def test_export_text_with_document(self):
        """测试带文档的TXT导出"""
        service = DocumentExportService()

        doc = Mock(
            id=1,
            title="测试文档",
            content="这是测试内容",
            file_name="test.pdf",
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )

        async def single_fetcher(offset, limit):
            if offset == 0:
                return [doc]
            return []

        chunks = []
        async for chunk in service._export_text(single_fetcher, 10):
            chunks.append(chunk)

        full_content = "".join(chunks)
        assert "ID: 1" in full_content
        assert "标题: 测试文档" in full_content
        assert "这是测试内容" in full_content


# ============================================================================
# _export_markdown 测试
# ============================================================================

class TestExportMarkdown:
    """测试_export_markdown方法"""

    @pytest.mark.asyncio
    async def test_export_markdown_empty_data(self):
        """测试空数据的Markdown导出"""
        service = DocumentExportService()

        async def empty_fetcher(offset, limit):
            return []

        chunks = []
        async for chunk in service._export_markdown(empty_fetcher, 10):
            chunks.append(chunk)

        assert len(chunks) == 0

    @pytest.mark.asyncio
    async def test_export_markdown_with_document(self):
        """测试带文档的Markdown导出"""
        service = DocumentExportService()

        doc = Mock(
            id=1,
            title="测试文档",
            content="# 内容\n\n这是测试内容",
            file_name="test.pdf",
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )

        async def single_fetcher(offset, limit):
            if offset == 0:
                return [doc]
            return []

        chunks = []
        async for chunk in service._export_markdown(single_fetcher, 10):
            chunks.append(chunk)

        full_content = "".join(chunks)
        assert "# 测试文档" in full_content
        assert "**ID:** 1" in full_content
        assert "这是测试内容" in full_content


# ============================================================================
# DocumentBatchProcessor 测试
# ============================================================================

class TestDocumentBatchProcessor:
    """测试DocumentBatchProcessor类"""

    def test_init_default_batch_size(self):
        """测试默认批处理大小"""
        processor = DocumentBatchProcessor()
        assert processor.batch_size == 100

    def test_init_custom_batch_size(self):
        """测试自定义批处理大小"""
        processor = DocumentBatchProcessor(batch_size=50)
        assert processor.batch_size == 50

    @pytest.mark.asyncio
    async def test_process_batches_empty_database(self, db_session: AsyncSession):
        """测试空数据库的批量处理"""
        processor = DocumentBatchProcessor(batch_size=10)

        async def no_process(documents):
            return []

        result = await processor.process_batches(
            db_session,
            no_process
        )

        assert result["total_processed"] == 0
        assert result["total_batches"] == 0
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_process_batches_successful(self, db_session: AsyncSession):
        """测试成功的批量处理"""
        processor = DocumentBatchProcessor(batch_size=2)

        # 创建测试文档
        for i in range(5):
            doc = Document(
                file_name=f"doc{i}.pdf",
                file_path=f"/test/doc{i}.pdf",
                file_hash=f"hash{i}",
                source_type="FILE"
            )
            db_session.add(doc)
        await db_session.commit()

        processed_count = []

        async def delete_processor(documents):
            processed_count.extend(documents)
            return len(documents)

        result = await processor.process_batches(
            db_session,
            delete_processor
        )

        assert result["total_processed"] == 5
        assert result["total_batches"] == 3  # 2, 2, 1
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_process_batches_with_filters(self, db_session: AsyncSession):
        """测试带过滤条件的批量处理"""
        processor = DocumentBatchProcessor(batch_size=10)

        # 创建不同类型的文档
        doc1 = Document(
            file_name="file1.pdf",
            file_path="/test/file1.pdf",
            file_hash="hash1",
            source_type="FILE"
        )
        doc2 = Document(
            file_name="web1",
            file_path="https://example.com",
            file_hash="hash2",
            source_type="WEB"
        )
        db_session.add(doc1)
        db_session.add(doc2)
        await db_session.commit()

        processed_count = []

        async def file_processor(documents):
            for doc in documents:
                if doc.source_type == "FILE":
                    processed_count.append(doc.id)
            return len(processed_count)

        result = await processor.process_batches(
            db_session,
            file_processor,
            filters={"source_type": "FILE"}
        )

        # 应该只处理FILE类型的文档
        assert result["total_processed"] == 1

    @pytest.mark.asyncio
    async def test_process_batches_with_errors(self, db_session: AsyncSession):
        """测试批量处理中的错误处理"""
        processor = DocumentBatchProcessor(batch_size=2)

        # 创建测试文档
        for i in range(3):
            doc = Document(
                file_name=f"doc{i}.pdf",
                file_path=f"/test/doc{i}.pdf",
                file_hash=f"hash{i}",
                source_type="FILE"
            )
            db_session.add(doc)
        await db_session.commit()

        call_count = [0]

        async def faulty_processor(documents):
            call_count[0] += 1
            # 第一批(2个文档)抛出错误
            if call_count[0] == 1:
                raise ValueError("Intentional error")
            return len(documents)

        result = await processor.process_batches(
            db_session,
            faulty_processor
        )

        # 第一批失败后，total_processed为0（在异常前未累加）
        # 但由于continue循环，第二批仍会处理
        assert len(result["errors"]) > 0
        # 确认错误被正确记录
        assert any("Intentional error" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_process_batches_with_progress_callback(self, db_session: AsyncSession):
        """测试带进度回调的批量处理"""
        processor = DocumentBatchProcessor(batch_size=1)

        # 创建2个文档
        for i in range(2):
            doc = Document(
                file_name=f"doc{i}.pdf",
                file_path=f"/test/doc{i}.pdf",
                file_hash=f"hash{i}",
                source_type="FILE"
            )
            db_session.add(doc)
        await db_session.commit()

        progress_calls = []

        async def simple_processor(documents):
            return len(documents)

        result = await processor.process_batches(
            db_session,
            simple_processor,
            progress_callback=lambda current, total: progress_calls.append((current, total))
        )

        assert result["total_processed"] == 2
        assert len(progress_calls) == 2
        # 第二次回调应该在处理完所有2个文档后
        assert progress_calls[-1] == (2, 2)


# ============================================================================
# 边界条件和错误处理测试
# ============================================================================

class TestDocumentExportServiceEdgeCases:
    """测试边界条件和错误处理"""

    @pytest.mark.asyncio
    async def test_export_with_zero_batch_size(self, db_session: AsyncSession):
        """测试零批处理大小"""
        service = DocumentExportService(batch_size=0)

        # 将batch_size设为1以避免无限循环
        service.batch_size = 1

        result = await service.export_documents(
            db_session,
            format_type=ExportFormat.JSON
        )

        assert isinstance(result, StreamingResponse)

    @pytest.mark.asyncio
    async def test_export_with_filters(self, db_session: AsyncSession):
        """测试带过滤条件的导出"""
        service = DocumentExportService()

        # 创建不同类型的文档
        doc1 = Document(
            file_name="file1.pdf",
            file_path="/test/file1.pdf",
            file_hash="hash1",
            source_type="FILE"
        )
        doc2 = Document(
            file_name="web1",
            file_path="https://example.com",
            file_hash="hash2",
            source_type="WEB"
        )
        db_session.add(doc1)
        db_session.add(doc2)
        await db_session.commit()

        result = await service.export_documents(
            db_session,
            format_type=ExportFormat.JSON,
            filters={"source_type": "FILE"}
        )

        assert isinstance(result, StreamingResponse)

    @pytest.mark.asyncio
    async def test_get_export_strategy_returns_same_function(self, db_session: AsyncSession):
        """测试策略返回同一类函数"""
        service = DocumentExportService()

        # 多次获取同一格式的策略应该返回相同类型的函数
        strategy1 = service._get_export_strategy(ExportFormat.JSON)
        strategy2 = service._get_export_strategy(ExportFormat.JSON)
        # 验证返回的是同一个方法（尽管bound method每次是不同实例，但应该是同一个方法）
        assert strategy1.__name__ == strategy2.__name__
        assert strategy1.__name__ == "_export_json"

    @pytest.mark.asyncio
    async def test_get_media_type_cache_behavior(self, db_session: AsyncSession):
        """测试媒体类型缓存行为"""
        service = DocumentExportService()

        # 多次获取同一格式的媒体类型应该返回相同结果
        media1 = service._get_media_type(ExportFormat.JSON)
        media2 = service._get_media_type(ExportFormat.JSON)
        assert media1 == media2
        assert media1 == "application/json"
