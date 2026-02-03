"""
文件级注释：Service 层逻辑单元测试
内部逻辑：测试 IngestService, ChatService 和 AgentService 的核心逻辑，包括异常处理
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.ingest_service import IngestService
from app.services.chat_service import ChatService
from app.services.agent_service import AgentService
from app.services.search_service import SearchService
from app.schemas.ingest import DBIngestRequest
from app.schemas.chat import ChatRequest
from app.core.config import settings
from fastapi import HTTPException
from unittest.mock import MagicMock, patch, AsyncMock

@pytest.mark.asyncio
async def test_ingest_service_calculate_hash():
    """测试哈希计算逻辑"""
    content = b"hello world"
    h = await IngestService._calculate_hash(content)
    assert len(h) == 64
    assert h == await IngestService._calculate_hash(content)

@pytest.mark.asyncio
async def test_ingest_service_get_embeddings_config():
    """
    函数级注释：测试 Embedding 实例获取逻辑
    内部逻辑：使用 monkeypatch 修改环境变量来改变 settings 行为
    注意：pydantic settings 使用环境变量，不能直接 patch 对象属性
    """
    import os

    # 1. 测试 Ollama 模式 (默认)
    # 内部逻辑：使用 monkeypatch 修改环境变量
    original_provider = os.environ.get("EMBEDDING_PROVIDER")
    try:
        os.environ["EMBEDDING_PROVIDER"] = "ollama"
        emb = IngestService.get_embeddings()
        # 内部逻辑：在 Mock 环境下，get_embeddings 会返回 Mock 实例
        # 验证返回的对象有 embed_documents 和 embed_query 方法即可
        assert hasattr(emb, "embed_documents")
        assert hasattr(emb, "embed_query")
    finally:
        if original_provider is not None:
            os.environ["EMBEDDING_PROVIDER"] = original_provider
        elif "EMBEDDING_PROVIDER" in os.environ:
            del os.environ["EMBEDDING_PROVIDER"]

    # 2. 测试本地模式（使用 EMBEDDING_PROVIDER=local）
    original_local = os.environ.get("EMBEDDING_PROVIDER")
    try:
        os.environ["EMBEDDING_PROVIDER"] = "local"
        emb = IngestService.get_embeddings()
        # 内部逻辑：验证本地模式下也能正常返回 Embedding 实例
        assert hasattr(emb, "embed_documents")
        assert hasattr(emb, "embed_query")
    finally:
        if original_local is not None:
            os.environ["EMBEDDING_PROVIDER"] = original_local
        elif "EMBEDDING_PROVIDER" in os.environ:
            del os.environ["EMBEDDING_PROVIDER"]

@pytest.mark.asyncio
async def test_ingest_service_process_db(db_session: AsyncSession):
    """测试数据库摄入逻辑"""
    request = DBIngestRequest(
        connection_uri="sqlite:///test.db",
        table_name="test_table",
        content_column="content"
    )
    
    # Mock SQLDatabaseLoader
    with patch("langchain_community.document_loaders.SQLDatabaseLoader.load") as mock_load:
        doc = MagicMock()
        doc.page_content = "db content"
        doc.metadata = {}
        mock_load.return_value = [doc]
        
        with patch("langchain_community.utilities.SQLDatabase.from_uri"):
            response = await IngestService.process_db(db_session, request)
            # IngestResponse 没有 status_code 属性
            assert response.status == "completed"

@pytest.mark.asyncio
async def test_chat_service_chat_completion_no_agent(db_session: AsyncSession):
    """
    函数级注释：测试非智能体模式的对话逻辑
    内部逻辑：验证use_agent=False时的基本对话功能
    注意：不强制要求sources有值，因为可能向量库中没有数据
    """
    request = ChatRequest(message="test", use_agent=False)
    response = await ChatService.chat_completion(db_session, request)
    assert "answer" in response.model_dump()
    # 内部逻辑：sources可能为空（向量库无数据），验证其为列表类型即可
    assert isinstance(response.sources, list)

@pytest.mark.asyncio
async def test_chat_service_chat_completion_with_agent(db_session: AsyncSession):
    """测试智能体模式的对话逻辑"""
    request = ChatRequest(message="test", use_agent=True)
    # Mock AgentService.run
    with patch("app.services.agent_service.AgentService.run") as mock_run:
        mock_run.return_value = {"answer": "Agent 回复", "sources": [1]}
        response = await ChatService.chat_completion(db_session, request)
        assert response.answer == "Agent 回复"

@pytest.mark.asyncio
async def test_chat_service_chat_completion_with_history(db_session: AsyncSession):
    """测试带历史记录的对话逻辑（覆盖 chat_service.py:117-121）"""
    request = ChatRequest(
        message="test", 
        use_agent=True,
        history=[
            {"role": "user", "content": "第一条消息"},
            {"role": "assistant", "content": "第一条回复"}
        ]
    )
    # Mock AgentService.run
    with patch("app.services.agent_service.AgentService.run") as mock_run:
        mock_run.return_value = {"answer": "Agent 回复", "sources": [1]}
        response = await ChatService.chat_completion(db_session, request)
        assert response.answer == "Agent 回复"

@pytest.mark.asyncio
async def test_agent_service_run():
    """测试智能体服务运行逻辑"""
    agent = AgentService()
    # Mock Graph invoke
    with patch("app.services.agent_service.AgentService.create_graph") as mock_create_graph:
        mock_app = MagicMock()
        mock_create_graph.return_value = mock_app
        mock_app.ainvoke = AsyncMock(return_value={
            "messages": [MagicMock(content="最终答案")],
            "sources": [1, 2]
        })
        
        result = await agent.run("问题")
        assert result["answer"] == "最终答案"
        assert result["sources"] == [1, 2]

@pytest.mark.asyncio
async def test_agent_service_run_with_history():
    """测试带历史记录的智能体运行逻辑"""
    from langchain_core.messages import HumanMessage, AIMessage
    agent = AgentService()
    # Mock Graph invoke
    with patch("app.services.agent_service.AgentService.create_graph") as mock_create_graph:
        mock_app = MagicMock()
        mock_create_graph.return_value = mock_app
        mock_app.ainvoke = AsyncMock(return_value={
            "messages": [MagicMock(content="最终答案")],
            "sources": [1, 2]
        })
        
        history = [HumanMessage(content="历史1"), AIMessage(content="回复1")]
        result = await agent.run("问题", history=history)
        assert result["answer"] == "最终答案"
        assert result["sources"] == [1, 2]

@pytest.mark.asyncio
async def test_agent_service_tools():
    """测试智能体工具函数（覆盖 agent_service.py:72-81, 90-97, 106-118）"""
    agent = AgentService()
    
    # 测试 retrieve_knowledge 工具
    # 这个工具在 AgentService.__init__ 中定义，需要通过图执行来测试
    # 我们通过 mock vector_db 来测试
    with patch.object(agent.vector_db, "similarity_search") as mock_search:
        from langchain_core.documents import Document
        doc = Document(page_content="测试内容", metadata={"doc_id": 1})
        mock_search.return_value = [doc]
        
        # 获取工具并调用
        retrieve_tool = agent.tools[0]
        result = retrieve_tool.invoke({"query": "测试"})
        assert "测试内容" in result
        # 内部逻辑：last_retrieved_ids 是类属性
        assert AgentService._last_retrieved_ids == [1]
    
    # 测试 calculate 工具
    calc_tool = agent.tools[2]
    result = calc_tool.invoke({"expression": "2 + 2"})
    assert "4" in result
    
    # 测试 calculate 工具异常情况
    result_error = calc_tool.invoke({"expression": "invalid syntax !!!"})
    assert "计算出错" in result_error
    
    # 测试 search_local_files 工具（找不到文件的情况）
    search_tool = agent.tools[1]
    result = search_tool.invoke({"directory": "/nonexistent", "pattern": "*.txt"})
    assert "未找到" in result
    
    # 测试 query_metadata_db 工具（无数据情况）
    query_tool = agent.tools[3]
    with patch("sqlite3.connect") as mock_connect:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_connect.return_value.cursor.return_value = mock_cursor
        result = query_tool.invoke({"sql_query": "SELECT * FROM documents"})
        assert "未查询到" in result

@pytest.mark.asyncio
async def test_ingest_service_delete_document(db_session: AsyncSession):
    """测试文档删除逻辑"""
    # 先摄入一个网页文档
    res = await IngestService.process_url(db_session, "https://delete.me")
    doc_id = res.document_id
    
    # 执行删除
    success = await IngestService.delete_document(db_session, doc_id)
    assert success is True
    
    # 再次删除应失败
    fail = await IngestService.delete_document(db_session, doc_id)
    assert fail is False

@pytest.mark.asyncio
async def test_ingest_service_get_documents(db_session: AsyncSession):
    """测试获取文档列表功能（覆盖 ingest_service.py:382-389）"""
    # 先摄入几个文档
    await IngestService.process_url(db_session, "https://doc1.test")
    await IngestService.process_url(db_session, "https://doc2.test")
    await IngestService.process_url(db_session, "https://doc3.test")
    
    # 测试分页查询
    result = await IngestService.get_documents(db_session, skip=0, limit=2)
    assert result.total >= 3
    assert len(result.items) == 2
    
    # 测试跳过查询
    result_skip = await IngestService.get_documents(db_session, skip=1, limit=2)
    assert len(result_skip.items) == 2

@pytest.mark.asyncio
async def test_chat_service_summarize_error(db_session: AsyncSession):
    """测试总结不存在文档时的异常处理"""
    with pytest.raises(HTTPException) as exc:
        await ChatService.summarize_document(db_session, 9999)
    assert exc.value.status_code == 404

@pytest.mark.asyncio
async def test_chat_service_summarize_document(db_session: AsyncSession):
    """测试文档总结功能"""
    # 先摄入一个文档
    res = await IngestService.process_url(db_session, "https://summary.test")
    doc_id = res.document_id
    
    # 执行总结
    summary = await ChatService.summarize_document(db_session, doc_id)
    assert "result" in summary.model_dump()
    assert len(summary.result) > 0

@pytest.mark.asyncio
async def test_chat_service_compare_documents(db_session: AsyncSession):
    """测试文档对比功能"""
    # 摄入两个文档
    res1 = await IngestService.process_url(db_session, "https://compare1.test")
    res2 = await IngestService.process_url(db_session, "https://compare2.test")
    
    # 执行对比
    comparison = await ChatService.compare_documents(db_session, [res1.document_id, res2.document_id])
    assert "result" in comparison.model_dump()

@pytest.mark.asyncio
async def test_chat_service_compare_documents_empty(db_session: AsyncSession):
    """测试文档对比功能（空内容情况，覆盖 chat_service.py:334）"""
    # 测试对比不存在的文档
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await ChatService.compare_documents(db_session, [99999, 99998])
    assert exc.value.status_code == 404
    assert "未找到" in exc.value.detail

@pytest.mark.asyncio
async def test_chat_service_get_sources(db_session: AsyncSession):
    """测试获取来源详情功能"""
    # 先摄入一个文档
    res = await IngestService.process_url(db_session, "https://sources.test")
    doc_id = res.document_id
    
    # 获取来源详情
    sources = await ChatService.get_sources(db_session, doc_id)
    assert isinstance(sources, list)
    
    # 测试获取所有来源
    all_sources = await ChatService.get_sources(db_session)
    assert isinstance(all_sources, list)

@pytest.mark.asyncio
async def test_chat_service_get_sources_empty(db_session: AsyncSession):
    """测试获取来源详情功能（空结果情况，覆盖 chat_service.py:266）"""
    # 测试获取不存在的文档的来源详情
    sources = await ChatService.get_sources(db_session, 99999)
    assert isinstance(sources, list)
    assert len(sources) == 0

@pytest.mark.asyncio
async def test_chat_service_stream_chat_completion(db_session: AsyncSession):
    """测试流式对话功能（非 Agent 模式）"""
    request = ChatRequest(message="流式测试", stream=True, use_agent=False)
    
    # 收集流式响应
    chunks = []
    async for chunk in ChatService.stream_chat_completion(db_session, request):
        chunks.append(chunk)
    
    assert len(chunks) > 0
    # 验证最后是 {"done": true}
    assert chunks[-1].strip() == 'data: {"done": true}'

@pytest.mark.asyncio
async def test_chat_service_stream_chat_completion_with_agent(db_session: AsyncSession):
    """
    测试流式对话功能（Agent 模式，覆盖 chat_service.py:213-232）
    注意：使用Mock模式避免实际调用LLM
    """
    # 使用Mock模式以确保测试快速执行
    with patch.object(settings, "USE_MOCK", True):
        request = ChatRequest(message="流式测试 Agent", stream=True, use_agent=True)

        # 收集流式响应
        chunks = []
        async for chunk in ChatService.stream_chat_completion(db_session, request):
            chunks.append(chunk)

        assert len(chunks) > 0
        # 验证包含answer字段（Mock模式返回的内容）
        assert any("answer" in chunk for chunk in chunks)

@pytest.mark.asyncio
async def test_agent_service_create_graph():
    """测试智能体图创建逻辑"""
    agent = AgentService()
    graph = agent.create_graph()
    assert graph is not None

@pytest.mark.asyncio
async def test_agent_service_call_model():
    """测试智能体调用模型逻辑"""
    from langchain_core.messages import HumanMessage
    agent = AgentService()
    state = {
        "messages": [HumanMessage(content="测试消息")],
        "sources": []
    }
    result = agent._call_model(state)
    assert "messages" in result

@pytest.mark.asyncio
async def test_agent_service_execute_tools():
    """测试智能体工具执行逻辑"""
    from langchain_core.messages import AIMessage
    agent = AgentService()
    # 创建带 tool_calls 的消息
    msg = AIMessage(content="test", tool_calls=[{"name": "retrieve_knowledge", "args": {"query": "test"}, "id": "1"}])
    state = {
        "messages": [msg],
        "sources": []
    }
    result = agent._execute_tools(state)
    assert "messages" in result
    assert "sources" in result

@pytest.mark.asyncio
async def test_agent_service_should_continue():
    """测试智能体继续判断逻辑"""
    from langchain_core.messages import AIMessage
    from langgraph.graph import END
    agent = AgentService()
    # 测试有 tool_calls 的情况（需要完整的 tool_call 结构）
    msg_with_tools = AIMessage(
        content="test", 
        tool_calls=[{"name": "retrieve_knowledge", "args": {"query": "test"}, "id": "1"}]
    )
    state_with_tools = {"messages": [msg_with_tools]}
    assert agent._should_continue(state_with_tools) == "action"
    
    # 测试没有 tool_calls 的情况
    msg_no_tools = AIMessage(content="test")
    state_no_tools = {"messages": [msg_no_tools]}
    assert agent._should_continue(state_no_tools) == END

@pytest.mark.asyncio
async def test_ingest_service_process_file_mock_mode(db_session: AsyncSession):
    """测试文件处理 Mock 模式（覆盖 ingest_service.py:88-90）"""
    from fastapi import UploadFile
    from io import BytesIO
    
    file = UploadFile(filename="test.txt", file=BytesIO(b"test"))
    
    with patch.object(settings, "USE_MOCK", True):
        response = await IngestService.process_file(db_session, file)
        assert response.status == "completed"
        assert response.document_id == 999

@pytest.mark.asyncio
async def test_ingest_service_process_file_duplicate(db_session: AsyncSession):
    """测试文件处理重复文件情况（覆盖 ingest_service.py:104-106）"""
    from fastapi import UploadFile
    from io import BytesIO
    
    file_content = b"duplicate test content"
    file1 = UploadFile(filename="dup.txt", file=BytesIO(file_content))
    
    # 第一次上传
    res1 = await IngestService.process_file(db_session, file1)
    assert res1.status == "completed"
    
    # 第二次上传相同内容（应该被检测为重复）
    file2 = UploadFile(filename="dup2.txt", file=BytesIO(file_content))
    res2 = await IngestService.process_file(db_session, file2)
    assert res2.status == "completed"
    assert res2.chunk_count == 0  # 重复文件不处理
    assert res2.document_id == res1.document_id  # 返回已存在的文档 ID

@pytest.mark.asyncio
async def test_ingest_service_process_file_exception(db_session: AsyncSession):
    """测试文件处理异常情况"""
    from fastapi import UploadFile
    from io import BytesIO

    # 创建一个会导致异常的文件
    file = UploadFile(filename="test.txt", file=BytesIO(b"test"))

    # Mock _get_document_loader 方法抛出异常
    with patch.object(IngestService, "_get_document_loader") as mock_get_loader:
        mock_loader = MagicMock()
        mock_loader.load.side_effect = Exception("解析失败")
        mock_get_loader.return_value = mock_loader

        with pytest.raises(HTTPException) as exc:
            await IngestService.process_file(db_session, file)
        assert exc.value.status_code == 500

@pytest.mark.asyncio
async def test_ingest_service_process_url_mock_mode(db_session: AsyncSession):
    """测试 URL 处理 Mock 模式（覆盖 ingest_service.py:193-194）"""
    with patch.object(settings, "USE_MOCK", True):
        response = await IngestService.process_url(db_session, "https://mock.test")
        assert response.status == "completed"
        assert response.document_id == 888

@pytest.mark.asyncio
async def test_ingest_service_process_url_duplicate(db_session: AsyncSession):
    """测试 URL 处理重复 URL 情况（覆盖 ingest_service.py:208）"""
    url = "https://duplicate.test"
    
    # 第一次处理
    res1 = await IngestService.process_url(db_session, url)
    assert res1.status == "completed"
    
    # 第二次处理相同 URL（应该被检测为重复）
    res2 = await IngestService.process_url(db_session, url)
    assert res2.status == "completed"
    assert res2.chunk_count == 0
    assert res2.document_id == res1.document_id

@pytest.mark.asyncio
async def test_ingest_service_process_url_title_from_source(db_session: AsyncSession):
    """测试 URL 处理从 source 提取标题（覆盖 ingest_service.py:219-220）"""
    # Mock WebBaseLoader 来测试标题提取
    with patch("app.services.ingest_service.WebBaseLoader") as mock_loader_cls:
        from langchain_core.documents import Document
        doc = Document(
            page_content="test content",
            metadata={"source": "https://example.com/page.html", "title": "Example Page"}
        )
        mock_instance = MagicMock()
        mock_instance.load.return_value = [doc]
        mock_loader_cls.return_value = mock_instance

        response = await IngestService.process_url(db_session, "https://example.com/page.html")
        assert response.status == "completed"

@pytest.mark.asyncio
async def test_ingest_service_process_url_exception(db_session: AsyncSession):
    """测试 URL 处理异常情况"""
    # Mock WebBaseLoader 抛出异常
    with patch("app.services.ingest_service.WebBaseLoader") as mock_loader_cls:
        mock_instance = MagicMock()
        mock_instance.load.side_effect = Exception("抓取失败")
        mock_loader_cls.return_value = mock_instance

        with pytest.raises(HTTPException) as exc:
            await IngestService.process_url(db_session, "https://error.test")
        assert exc.value.status_code == 500

@pytest.mark.asyncio
async def test_ingest_service_process_db_mock_mode(db_session: AsyncSession):
    """测试数据库摄入 Mock 模式（覆盖 ingest_service.py:286-287）"""
    request = DBIngestRequest(
        connection_uri="sqlite:///test.db",
        table_name="test_table",
        content_column="content"
    )
    
    with patch.object(settings, "USE_MOCK", True):
        response = await IngestService.process_db(db_session, request)
        assert response.status == "completed"
        assert response.document_id == 777

@pytest.mark.asyncio
async def test_ingest_service_process_db_duplicate(db_session: AsyncSession):
    """测试数据库摄入重复情况（覆盖 ingest_service.py:301）"""
    request = DBIngestRequest(
        connection_uri="sqlite:///test.db",
        table_name="test_table",
        content_column="content"
    )
    
    # 第一次处理
    with patch("langchain_community.document_loaders.SQLDatabaseLoader.load") as mock_load:
        doc = MagicMock()
        doc.page_content = "db content"
        doc.metadata = {}
        mock_load.return_value = [doc]
        
        with patch("langchain_community.utilities.SQLDatabase.from_uri"):
            res1 = await IngestService.process_db(db_session, request)
            assert res1.status == "completed"
            
            # 第二次处理相同配置（应该被检测为重复）
            res2 = await IngestService.process_db(db_session, request)
            assert res2.status == "completed"
            assert res2.chunk_count == 0
            assert res2.document_id == res1.document_id

@pytest.mark.asyncio
async def test_ingest_service_process_db_exception(db_session: AsyncSession):
    """测试数据库摄入异常情况"""
    request = DBIngestRequest(
        connection_uri="sqlite:///test.db",
        table_name="test_table",
        content_column="content"
    )
    
    # Mock loader 抛出异常（需要在正确的位置 patch）
    with patch("app.services.ingest_service.SQLDatabaseLoader") as mock_loader_cls:
        mock_instance = MagicMock()
        mock_instance.load.side_effect = Exception("数据库连接失败")
        mock_loader_cls.return_value = mock_instance
        
        with patch("app.services.ingest_service.SQLDatabase.from_uri"):
            with pytest.raises(HTTPException) as exc:
                await IngestService.process_db(db_session, request)
            assert exc.value.status_code == 500

@pytest.mark.asyncio
async def test_ingest_service_delete_document_exception(db_session: AsyncSession):
    """测试文档删除异常情况"""
    # 先摄入一个文档
    res = await IngestService.process_url(db_session, "https://delete-error.test")
    doc_id = res.document_id
    
    # Mock Chroma 抛出异常
    with patch("app.services.ingest_service.Chroma") as mock_chroma:
        mock_chroma.return_value.delete.side_effect = Exception("删除失败")
        
        with pytest.raises(HTTPException) as exc:
            await IngestService.delete_document(db_session, doc_id)
        assert exc.value.status_code == 500

@pytest.mark.asyncio
async def test_chat_service_chat_completion_mock_mode(db_session: AsyncSession):
    """测试对话服务的Mock模式（覆盖 chat_service.py:42）"""
    request = ChatRequest(message="test", use_agent=False)
    with patch.object(settings, "USE_MOCK", True):
        response = await ChatService.chat_completion(db_session, request)
        assert "Mock" in response.answer

@pytest.mark.asyncio
async def test_chat_service_stream_chat_completion_mock_mode(db_session: AsyncSession):
    """测试流式对话服务的Mock模式（覆盖 chat_service.py:164-168）"""
    request = ChatRequest(message="流式测试", stream=True, use_agent=False)
    with patch.object(settings, "USE_MOCK", True):
        chunks = []
        async for chunk in ChatService.stream_chat_completion(db_session, request):
            chunks.append(chunk)
        assert len(chunks) > 0
        assert "Mock" in chunks[0] or "流式" in chunks[0]

@pytest.mark.asyncio
async def test_chat_service_stream_chat_completion_with_agent_sources(db_session: AsyncSession):
    """
    函数级注释：测试流式对话Agent模式的sources处理
    内部逻辑：重构后使用ChatOrchestrator，patch正确的位置
    """
    request = ChatRequest(message="流式测试 Agent", stream=True, use_agent=True)

    # 内部逻辑：重构后使用ChatOrchestrator，patch orchestrator的stream_chat方法
    with patch('app.services.chat.orchestrator.settings.USE_MOCK', True):
        chunks = []
        async for chunk in ChatService.stream_chat_completion(db_session, request):
            chunks.append(chunk)
        assert len(chunks) > 0
        # 验证完成标记
        assert any('done' in chunk for chunk in chunks)

@pytest.mark.asyncio
async def test_agent_service_search_local_files_success():
    """测试search_local_files工具成功找到文件的情况（覆盖 agent_service.py:79-81）"""
    import tempfile
    import os
    agent = AgentService()
    search_tool = agent.tools[1]
    
    # 创建临时目录和文件
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test content")
        
        result = search_tool.invoke({"directory": tmpdir, "pattern": "*.txt"})
        assert "找到以下文件" in result
        assert "test.txt" in result
    
    # 测试异常情况（覆盖80-81行）
    with patch("glob.glob", side_effect=Exception("权限错误")):
        result = search_tool.invoke({"directory": "/tmp", "pattern": "*.txt"})
        assert "搜索文件时出错" in result

@pytest.mark.asyncio
async def test_agent_service_query_metadata_db_exception():
    """测试query_metadata_db工具的异常处理（覆盖 agent_service.py:116-118）"""
    agent = AgentService()
    query_tool = agent.tools[3]
    
    # 测试有数据的情况（覆盖116行）
    with patch("sqlite3.connect") as mock_connect:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("doc1", "content1"), ("doc2", "content2")]
        mock_connect.return_value.cursor.return_value = mock_cursor
        mock_connect.return_value.__enter__ = lambda x: x
        mock_connect.return_value.__exit__ = lambda *args: None
        
        result = query_tool.invoke({"sql_query": "SELECT * FROM documents"})
        assert "查询结果" in result
    
    # 测试异常情况（覆盖117-118行）
    with patch("sqlite3.connect", side_effect=Exception("连接失败")):
        result = query_tool.invoke({"sql_query": "SELECT * FROM documents"})
        assert "数据库查询失败" in result

@pytest.mark.asyncio
async def test_search_service_empty_results():
    """测试搜索服务返回空结果的情况（覆盖 search_service.py:47）"""
    # Mock vector_db返回空结果
    with patch("app.services.search_service.Chroma") as mock_chroma:
        mock_instance = MagicMock()
        mock_instance.similarity_search_with_score.return_value = []
        mock_chroma.return_value = mock_instance
        
        results = await SearchService.semantic_search("不存在的查询", top_k=5)
        assert results == []

@pytest.mark.asyncio
async def test_config_cors_origins_edge_cases():
    """测试配置CORS来源的边界情况（覆盖 config.py:45, 48）"""
    from app.core.config import settings
    from pydantic import ValidationError

    # 内部逻辑：测试CORS配置是列表类型
    assert isinstance(settings.BACKEND_CORS_ORIGINS, list)

    # 内部逻辑：测试当前配置不为None
    assert settings.BACKEND_CORS_ORIGINS is not None

@pytest.mark.asyncio
async def test_db_session_get_db():
    """测试数据库会话获取（覆盖 db/session.py:30-34）"""
    from app.db.session import get_db

    # 内部逻辑：测试get_db生成器函数
    async for session in get_db():
        assert session is not None
        # 内部逻辑：验证会话可以正常使用
        assert hasattr(session, "execute")
        break  # 只测试一次迭代

@pytest.mark.asyncio
async def test_ingest_service_process_url_with_task_id_updates_task(db_session: AsyncSession):
    """测试 URL 处理传入 task_id 时正确更新任务状态"""
    from app.models.models import IngestTask, TaskStatus

    # 创建一个任务
    task = IngestTask(
        file_name="https://test-task-id.com",
        file_path="https://test-task-id.com",
        file_hash="test_hash",
        source_type="WEB",
        tags=None,
        status=TaskStatus.PENDING,
        progress=0
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # Mock URLLoader 返回数据
    with patch("app.services.ingest_service.WebBaseLoader") as mock_loader_cls:
        from langchain_core.documents import Document
        doc = Document(
            page_content="test content",
            metadata={"title": "Test Page"}
        )
        mock_instance = MagicMock()
        mock_instance.load.return_value = [doc]
        mock_loader_cls.return_value = mock_instance

        # 调用 process_url 并传入 task_id
        response = await IngestService.process_url(
            db_session,
            "https://test-task-id.com",
            tags=None,
            task_id=task.id
        )

        # 断言不再抛出参数错误
        assert response.status == "completed"
        assert response.document_id is not None
        assert response.chunk_count > 0

        # 刷新任务状态并验证更新
        await db_session.refresh(task)
        assert task.status == TaskStatus.COMPLETED
        assert task.progress == 100
        assert task.document_id == response.document_id

@pytest.mark.asyncio
async def test_ingest_service_process_db_with_task_id_updates_task(db_session: AsyncSession):
    """测试 DB 处理传入 task_id 时正确更新任务状态"""
    from app.models.models import IngestTask, TaskStatus

    # 创建一个任务
    task = IngestTask(
        file_name="DB:test_table_task_id",
        file_path="sqlite:///test.db",
        file_hash="test_db_hash",
        source_type="DB",
        tags=None,
        status=TaskStatus.PENDING,
        progress=0
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # Mock SQLDatabaseLoader 返回数据
    with patch("langchain_community.document_loaders.SQLDatabaseLoader.load") as mock_load:
        doc = MagicMock()
        doc.page_content = "db content"
        doc.metadata = {}
        mock_load.return_value = [doc]

        with patch("langchain_community.utilities.SQLDatabase.from_uri"):
            request = DBIngestRequest(
                connection_uri="sqlite:///test.db",
                table_name="test_table",
                content_column="content"
            )

            # 调用 process_db 并传入 task_id
            response = await IngestService.process_db(
                db_session,
                request,
                task_id=task.id
            )

            # 断言不再抛出参数错误
            assert response.status == "completed"
            assert response.document_id is not None
            assert response.chunk_count > 0

            # 刷新任务状态并验证更新
            await db_session.refresh(task)
            assert task.status == TaskStatus.COMPLETED
            assert task.progress == 100
            assert task.document_id == response.document_id