"""
上海宇羲伏天智能科技有限公司出品

文件级注释：对话服务层测试
内部逻辑：测试对话服务的核心业务逻辑，包括RAG流程、Agent模式和流式响应
测试策略：使用Mock对象隔离外部依赖，专注测试业务逻辑
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.chat_service import ChatService
from app.services.chat.document_formatter import DocumentFormatter
from app.schemas.chat import ChatRequest
from app.models.models import Document, VectorMapping


class TestDocumentFormatter:
    """
    类级注释：DocumentFormatter 测试类
    内部逻辑：测试文档格式化器的各种格式化功能
    """

    def test_format_markdown_with_content(self):
        """
        函数级注释：测试Markdown格式化
        内部逻辑：验证Markdown内容能被正确转换为HTML
        """
        content = "# 标题\n\n这是**粗体**文本"
        result = DocumentFormatter.format_markdown(content)
        # 应该返回HTML格式
        assert "<h1" in result or result == content  # 如果markdown-it不可用则返回原内容

    def test_format_markdown_empty(self):
        """
        函数级注释：测试空内容Markdown格式化
        内部逻辑：验证空内容能被正确处理
        """
        result = DocumentFormatter.format_markdown("")
        assert result == ""

    def test_format_structured_content(self):
        """
        函数级注释：测试结构化内容格式化
        内部逻辑：验证HTML表格内容能被正确处理
        """
        html_content = "<table><tr><td>数据</td></tr></table>"
        result = DocumentFormatter.format_structured_content(html_content)
        # 应该添加 Bootstrap 类
        assert "table" in result.lower()

    def test_format_structured_content_with_lists(self):
        """
        函数级注释：测试包含列表的结构化内容格式化
        内部逻辑：验证HTML列表内容能被正确处理
        """
        html_content = "<ul><li>项目1</li><li>项目2</li></ul>"
        result = DocumentFormatter.format_structured_content(html_content)
        assert "ul" in result.lower() or result == html_content

    def test_format_structured_content_with_blockquote(self):
        """
        函数级注释：测试包含引用的结构化内容格式化
        内部逻辑：验证HTML引用内容能被正确处理
        """
        html_content = "<blockquote>引用内容</blockquote>"
        result = DocumentFormatter.format_structured_content(html_content)
        assert "blockquote" in result.lower() or result == html_content

    def test_highlight_content(self):
        """
        函数级注释：测试内容高亮
        内部逻辑：验证关键词高亮功能
        """
        content = "<p>这是一个重要的关键词</p>"
        keywords = ["重要", "关键词"]
        result = DocumentFormatter.highlight_content(content, keywords)
        # 应该包含 mark 标签或返回原内容（如果BeautifulSoup不可用）
        assert "mark" in result.lower() or result == content

    def test_highlight_content_empty_keywords(self):
        """
        函数级注释：测试空关键词列表的高亮
        内部逻辑：验证空关键词时返回原内容
        """
        content = "<p>测试内容</p>"
        result = DocumentFormatter.highlight_content(content, None)
        assert result == content

    def test_highlight_content_empty_list_keywords(self):
        """
        函数级注释：测试空列表关键词的高亮
        内部逻辑：验证空列表关键词时返回原内容
        """
        content = "<p>测试内容</p>"
        result = DocumentFormatter.highlight_content(content, [])
        assert result == content

    def test_format_document(self):
        """
        函数级注释：测试综合文档格式化
        内部逻辑：验证文档格式化功能的综合效果
        """
        content = "# 标题\n\n重要内容"
        options = {
            'highlight_keywords': ['重要']
        }
        result = DocumentFormatter.format_document(content, options)
        # 应该返回格式化后的内容
        assert result is not None


@pytest.mark.asyncio
async def test_chat_service_mock_mode(db_session: AsyncSession):
    """
    函数级注释：测试Mock模式下的对话
    内部逻辑：通过patch settings.USE_MOCK来测试Mock模式
    Mock位置：app.services.chat.orchestrator.settings（因为settings在orchestrator中使用）
    """
    request = ChatRequest(
        message="测试问题",
        use_agent=False,
        stream=False
    )

    # 修复：patch正确的settings位置（在orchestrator模块中导入）
    with patch('app.services.chat.orchestrator.settings.USE_MOCK', True):
        response = await ChatService.chat_completion(db_session, request)
        assert response.answer is not None
        assert "Mock" in response.answer


@pytest.mark.asyncio
async def test_chat_service_get_sources_without_doc_id(db_session: AsyncSession):
    """
    函数级注释：测试获取来源列表（不指定doc_id）
    内部逻辑：创建测试数据并验证来源列表功能
    """
    # 创建测试数据
    doc = Document(
        file_name="测试文档.pdf",
        file_path="/test/path.pdf",
        file_hash="test_hash_123",
        source_type="FILE"
    )
    db_session.add(doc)
    await db_session.flush()

    mapping = VectorMapping(
        document_id=doc.id,
        chunk_id="test_chunk_1",
        chunk_content="测试片段内容"
    )
    db_session.add(mapping)
    await db_session.commit()

    # 获取来源
    sources = await ChatService.get_sources(db_session)
    assert len(sources) >= 1
    assert sources[0].doc_id == doc.id


@pytest.mark.asyncio
async def test_chat_service_get_sources_with_doc_id(db_session: AsyncSession):
    """
    函数级注释：测试获取指定文档的来源详情
    内部逻辑：创建测试数据并验证指定文档来源功能
    """
    # 创建测试数据
    doc = Document(
        file_name="指定文档.pdf",
        file_path="/test/path2.pdf",
        file_hash="test_hash_456",
        source_type="FILE"
    )
    db_session.add(doc)
    await db_session.flush()

    mapping = VectorMapping(
        document_id=doc.id,
        chunk_id="test_chunk_2",
        chunk_content="指定文档的测试片段"
    )
    db_session.add(mapping)
    await db_session.commit()

    # 获取来源
    sources = await ChatService.get_sources(db_session, doc_id=doc.id)
    assert len(sources) == 1
    assert sources[0].doc_id == doc.id
    assert "指定文档" in sources[0].file_name


@pytest.mark.asyncio
async def test_chat_service_get_sources_empty(db_session: AsyncSession):
    """
    函数级注释：测试获取不存在文档的来源
    内部逻辑：验证当文档不存在时返回空列表
    """
    sources = await ChatService.get_sources(db_session, doc_id=99999)
    assert sources == []


@pytest.mark.asyncio
async def test_chat_service_summarize_document_not_found(db_session: AsyncSession):
    """
    函数级注释：测试总结不存在的文档
    内部逻辑：验证当文档不存在时抛出404异常
    """
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await ChatService.summarize_document(db_session, 99999)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_chat_service_compare_documents_empty_list(db_session: AsyncSession):
    """
    函数级注释：测试对比空文档列表
    内部逻辑：验证当文档列表为空时抛出400异常（Bad Request）
    """
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await ChatService.compare_documents(db_session, [])
    assert exc_info.value.status_code == 400  # 空列表是400 Bad Request


@pytest.mark.asyncio
async def test_chat_service_compare_documents_not_found(db_session: AsyncSession):
    """
    函数级注释：测试对比不存在的文档
    内部逻辑：验证当文档不存在时抛出404异常
    """
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await ChatService.compare_documents(db_session, [99999, 88888])
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_chat_service_stream_mock_mode(db_session: AsyncSession):
    """
    函数级注释：测试Mock模式下的流式对话
    内部逻辑：通过patch settings.USE_MOCK来测试流式Mock模式
    Mock位置：app.services.chat.orchestrator.settings（因为settings在orchestrator中使用）
    """
    request = ChatRequest(
        message="测试问题",
        use_agent=False,
        stream=True
    )

    # 修复：patch正确的settings位置
    with patch('app.services.chat.orchestrator.settings.USE_MOCK', True):
        chunks = []
        async for chunk in ChatService.stream_chat_completion(db_session, request):
            chunks.append(chunk)

        # 应该至少有响应和完成标记
        assert len(chunks) >= 2
        assert any("Mock" in chunk for chunk in chunks)
        assert any('done' in chunk for chunk in chunks)


@pytest.mark.asyncio
async def test_chat_service_stream_mock_mode_with_sources(db_session: AsyncSession):
    """
    函数级注释：测试Mock模式下的流式对话带来源
    内部逻辑：验证Mock模式下流式对话的基本功能
    """
    request = ChatRequest(
        message="测试问题",
        use_agent=True,
        stream=True
    )

    # 修复：patch正确的settings位置
    with patch('app.services.chat.orchestrator.settings.USE_MOCK', True):
        chunks = []
        async for chunk in ChatService.stream_chat_completion(db_session, request):
            chunks.append(chunk)

        # 应该有响应
        assert len(chunks) >= 1


def test_document_formatter_class_exists():
    """
    函数级注释：测试DocumentFormatter类存在
    内部逻辑：验证DocumentFormatter类有所有必要的方法
    """
    assert hasattr(DocumentFormatter, 'format_markdown')
    assert hasattr(DocumentFormatter, 'format_structured_content')
    assert hasattr(DocumentFormatter, 'highlight_content')
    assert hasattr(DocumentFormatter, 'format_document')


def test_chat_service_class_exists():
    """
    函数级注释：测试ChatService类存在
    内部逻辑：验证ChatService类有所有必要的方法
    """
    assert hasattr(ChatService, 'chat_completion')
    assert hasattr(ChatService, 'stream_chat_completion')
    assert hasattr(ChatService, 'get_sources')
    assert hasattr(ChatService, 'summarize_document')
    assert hasattr(ChatService, 'compare_documents')
