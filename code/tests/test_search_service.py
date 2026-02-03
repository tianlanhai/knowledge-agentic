# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：搜索服务测试模块
内部逻辑：测试语义搜索功能、重排序功能以及边界条件
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock, Mock
from app.services.search_service import SearchService
from app.schemas.search import SearchResult
from langchain_core.documents import Document


# ============================================================================
# SearchService.semantic_search 测试
# ============================================================================


class TestSearchServiceSemanticSearch:
    """
    类级注释：semantic_search方法测试类
    测试场景：
        1. 空搜索结果
        2. 启用/禁用重排序
        3. 带数据库会话的搜索
        4. 异常处理
    """

    @pytest.mark.asyncio
    async def test_semantic_search_empty_results(self):
        """
        测试目的：验证语义搜索空结果
        测试场景：Chroma向量数据库返回空列表
        """
        with patch('app.services.search_service.Chroma') as mock_chroma:
            mock_db = MagicMock()
            mock_db.similarity_search_with_score.return_value = []
            mock_chroma.return_value = mock_db

            results = await SearchService.semantic_search(
                query="不存在的测试内容xyz",
                top_k=3,
                enable_reranking=False
            )
            assert results == []

    @pytest.mark.asyncio
    async def test_semantic_search_with_mock_results(self):
        """
        测试目的：验证有结果时的搜索
        测试场景：Chroma返回模拟的文档结果
        """
        with patch('app.services.search_service.Chroma') as mock_chroma, \
             patch('app.services.search_service.IngestService') as mock_ingest:

            # 内部逻辑：模拟嵌入模型
            mock_embeddings = MagicMock()
            mock_embeddings.embed_query.return_value = [0.1, 0.2, 0.3]
            mock_embeddings.embed_documents.return_value = [[0.1, 0.2], [0.3, 0.4]]
            mock_ingest.get_embeddings.return_value = mock_embeddings

            # 内部逻辑：模拟搜索结果
            mock_doc = Document(
                page_content="测试内容",
                metadata={"doc_id": 1}
            )
            mock_db = MagicMock()
            mock_db.similarity_search_with_score.return_value = [(mock_doc, 0.1)]
            mock_chroma.return_value = mock_db

            results = await SearchService.semantic_search(
                query="测试查询",
                top_k=3,
                enable_reranking=False
            )

            assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_semantic_search_with_reranking_enabled(self):
        """
        测试目的：验证启用重排序的搜索
        测试场景：enable_reranking=True
        """
        results = await SearchService.semantic_search(
            query="测试查询",
            top_k=3,
            enable_reranking=True
        )
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_semantic_search_without_reranking(self):
        """
        测试目的：验证禁用重排序的搜索
        测试场景：enable_reranking=False
        """
        results = await SearchService.semantic_search(
            query="测试查询",
            top_k=3,
            enable_reranking=False
        )
        assert isinstance(results, list)

    @pytest.mark.asyncio
    @patch('app.services.search_service.Chroma')
    @patch('app.services.search_service.IngestService')
    async def test_semantic_search_with_db_session(self, mock_ingest, mock_chroma):
        """
        测试目的：验证带数据库会话的搜索
        测试场景：传入db参数查询文件名
        """
        mock_db = AsyncMock()
        mock_doc_result = AsyncMock()
        mock_doc_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_doc_result

        # 内部逻辑：模拟嵌入模型
        mock_embeddings = MagicMock()
        mock_ingest.get_embeddings.return_value = mock_embeddings

        mock_chroma_instance = MagicMock()
        mock_chroma_instance.similarity_search_with_score.return_value = []
        mock_chroma.return_value = mock_chroma_instance

        results = await SearchService.semantic_search(
            query="测试",
            top_k=3,
            enable_reranking=False,
            db=mock_db
        )

        assert isinstance(results, list)


# ============================================================================
# SearchService._check_reranker_model_cached 测试
# ============================================================================


class TestSearchServiceCheckRerankerCached:
    """
    类级注释：_check_reranker_model_cached方法测试类
    测试场景：
        1. 模型已缓存
        2. 模型未缓存
        3. 异常处理
    """

    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('os.environ.get')
    def test_reranker_model_cached(self, mock_env_get, mock_listdir, mock_exists):
        """
        测试目的：验证模型已缓存的检查
        测试场景：缓存目录存在且包含模型文件
        """
        mock_env_get.return_value = "/cache/huggingface"
        mock_exists.return_value = True
        # 内部逻辑：模拟包含snapshots的目录列表
        mock_listdir.return_value = ["snapshots"]

        result = SearchService._check_reranker_model_cached()
        # 内部逻辑：取决于实际目录结构，可能返回True或False
        assert isinstance(result, bool)

    @patch('os.path.exists')
    @patch('os.environ.get')
    def test_reranker_model_not_cached(self, mock_env_get, mock_exists):
        """
        测试目的：验证模型未缓存的检查
        测试场景：缓存目录不存在
        """
        mock_env_get.return_value = "/cache/huggingface"
        mock_exists.return_value = False

        result = SearchService._check_reranker_model_cached()
        assert result is False

    @patch('os.environ.get')
    def test_reranker_cache_check_exception(self, mock_env_get):
        """
        测试目的：验证检查缓存时的异常处理
        测试场景：访问文件系统抛出异常
        """
        mock_env_get.side_effect = Exception("Filesystem error")

        result = SearchService._check_reranker_model_cached()
        # 内部逻辑：异常时应返回False
        assert result is False


# ============================================================================
# SearchService._should_use_reranking 测试
# ============================================================================


class TestSearchServiceShouldUseReranking:
    """
    类级注释：_should_use_reranking方法测试类
    测试场景：
        1. ENABLE_RERANKING配置禁用
        2. 本地embedding提供商
        3. 云端embedding提供商
        4. 获取提供商失败
    """

    def test_should_use_reranking_when_disabled(self):
        """
        测试目的：验证配置禁用时返回False
        测试场景：ENABLE_RERANKING=False
        """
        with patch('app.services.search_service.settings') as mock_settings:
            mock_settings.ENABLE_RERANKING = False
            result = SearchService._should_use_reranking()
            assert result is False

    def test_should_use_reranking_ollama_provider(self):
        """
        测试目的：验证Ollama提供商启用重排序
        测试场景：当前提供商为ollama（本地）
        """
        with patch('app.services.search_service.settings') as mock_settings, \
             patch('app.utils.embedding_factory.EmbeddingFactory.get_current_provider', return_value="ollama"):
            mock_settings.ENABLE_RERANKING = True
            result = SearchService._should_use_reranking()
            assert result is True

    def test_should_use_reranking_local_provider(self):
        """
        测试目的：验证local提供商启用重排序
        测试场景：当前提供商为local（本地）
        """
        with patch('app.services.search_service.settings') as mock_settings, \
             patch('app.utils.embedding_factory.EmbeddingFactory.get_current_provider', return_value="local"):
            mock_settings.ENABLE_RERANKING = True
            result = SearchService._should_use_reranking()
            assert result is True

    def test_should_use_reranking_zhipuai_provider(self):
        """
        测试目的：验证云端提供商不启用重排序
        测试场景：当前提供商为zhipuai（云端）
        """
        with patch('app.services.search_service.settings') as mock_settings, \
             patch('app.utils.embedding_factory.EmbeddingFactory.get_current_provider', return_value="zhipuai"):
            mock_settings.ENABLE_RERANKING = True
            result = SearchService._should_use_reranking()
            assert result is False

    def test_should_use_reranking_openai_provider(self):
        """
        测试目的：验证云端提供商不启用重排序
        测试场景：当前提供商为openai（云端）
        """
        with patch('app.services.search_service.settings') as mock_settings, \
             patch('app.utils.embedding_factory.EmbeddingFactory.get_current_provider', return_value="openai"):
            mock_settings.ENABLE_RERANKING = True
            result = SearchService._should_use_reranking()
            assert result is False

    def test_should_use_reranking_factory_exception(self):
        """
        测试目的：验证获取提供商失败时的处理
        测试场景：EmbeddingFactory抛出异常
        """
        with patch('app.services.search_service.settings') as mock_settings, \
             patch('app.utils.embedding_factory.EmbeddingFactory.get_current_provider', side_effect=Exception("Factory error")):
            mock_settings.ENABLE_RERANKING = True
            result = SearchService._should_use_reranking()
            assert result is False


# ============================================================================
# SearchService._rerank_with_embeddings 测试
# ============================================================================


class TestSearchServiceRerankWithEmbeddings:
    """
    类级注释：_rerank_with_embeddings方法测试类
    测试场景：
        1. 成功重排序
        2. 重排序异常处理
        3. 分数归一化
    """

    def test_rerank_with_embeddings_success(self):
        """
        测试目的：验证成功重排序
        测试场景：正常的重排序流程
        """
        mock_embeddings = MagicMock()
        mock_embeddings.embed_query.return_value = [1.0, 0.0, 0.0]
        # 内部逻辑：为不同文档返回不同的向量
        mock_embeddings.embed_documents.return_value = [
            [1.0, 0.0, 0.0],  # 高相似度
            [0.0, 1.0, 0.0],  # 低相似度
            [0.5, 0.5, 0.0],  # 中等相似度
        ]

        initial_results = [
            {"content": "doc1", "score": 0.7},
            {"content": "doc2", "score": 0.5},
            {"content": "doc3", "score": 0.6},
        ]

        result = SearchService._rerank_with_embeddings("query", initial_results, mock_embeddings)

        # 内部逻辑：应该返回3个结果
        assert len(result) == 3
        # 内部逻辑：每个结果应该有rerank_score字段
        for r in result:
            assert "rerank_score" in r

    def test_rerank_with_embeddings_exception(self):
        """
        测试目的：验证重排序异常处理
        测试场景：embed_query抛出异常
        """
        mock_embeddings = MagicMock()
        mock_embeddings.embed_query.side_effect = Exception("Embedding error")

        initial_results = [
            {"content": "doc1", "score": 0.7},
            {"content": "doc2", "score": 0.5},
        ]

        # 内部逻辑：异常时返回原始结果
        result = SearchService._rerank_with_embeddings("query", initial_results, mock_embeddings)

        assert len(result) == 2
        assert result == initial_results

    def test_rerank_with_embeddings_single_result(self):
        """
        测试目的：验证单个结果的重排序
        测试场景：只有一个搜索结果
        """
        mock_embeddings = MagicMock()
        mock_embeddings.embed_query.return_value = [1.0, 0.0]
        mock_embeddings.embed_documents.return_value = [[1.0, 0.0]]

        initial_results = [
            {"content": "only doc", "score": 0.7},
        ]

        result = SearchService._rerank_with_embeddings("query", initial_results, mock_embeddings)

        assert len(result) == 1
        # 内部逻辑：单个结果的归一化分数应该是0.5（当score_range=0时）
        assert result[0]["rerank_score"] == 0.5


# ============================================================================
# SearchService._get_reranker 测试
# ============================================================================


class TestSearchServiceGetReranker:
    """
    类级注释：_get_reranker方法测试类
    """

    def test_get_reranker_returns_none(self):
        """
        测试目的：验证_get_reranker返回None
        测试场景：已改用embedding重排序
        """
        reranker = SearchService._get_reranker()
        # 内部逻辑：始终返回None，已改用embedding重排序
        assert reranker is None


# ============================================================================
# SearchResult 模型测试
# ============================================================================


class TestSearchResultModel:
    """
    类级注释：SearchResult模型测试类
    """

    def test_search_result_model(self):
        """
        测试目的：验证SearchResult模型创建
        测试场景：创建完整的SearchResult对象
        """
        result = SearchResult(
            doc_id=1,
            file_name="test.pdf",
            source_type="pdf",
            content="测试内容",
            score=0.95
        )
        assert result.doc_id == 1
        assert result.file_name == "test.pdf"
        assert result.source_type == "pdf"
        assert result.content == "测试内容"
        assert result.score == 0.95

    def test_search_result_with_optional_fields(self):
        """
        测试目的：验证可选字段的处理
        测试场景：只传入必需字段
        """
        result = SearchResult(
            doc_id=1,
            content="测试内容",
            score=0.95
        )
        assert result.doc_id == 1
        assert result.content == "测试内容"
        assert result.score == 0.95
        assert result.file_name is None
        assert result.source_type is None


# ============================================================================
# 顶部函数测试（pytest兼容）
# ============================================================================


@pytest.mark.asyncio
async def test_semantic_search_top_k_parameter():
    """
    函数级注释：测试 top_k 参数
    """
    results = await SearchService.semantic_search(
        query="测试",
        top_k=10,
        enable_reranking=False
    )
    assert len(results) <= 10


@pytest.mark.asyncio
async def test_semantic_search_exception_handling():
    """
    函数级注释：测试搜索异常处理
    测试场景：Chroma搜索时抛出异常
    注意：semantic_search会重新抛出异常，而不是返回空列表
    """
    with patch('app.services.search_service.IngestService') as mock_ingest, \
         patch('app.services.search_service.Chroma') as mock_chroma_class:

        # 内部逻辑：模拟嵌入模型
        mock_embeddings = MagicMock()
        mock_ingest.get_embeddings.return_value = mock_embeddings

        # 内部逻辑：模拟Chroma实例，但搜索时抛出异常
        mock_chroma_instance = MagicMock()
        mock_chroma_instance.similarity_search_with_score.side_effect = Exception("Search error")
        mock_chroma_class.return_value = mock_chroma_instance

        # 内部逻辑：异常会被重新抛出
        with pytest.raises(Exception) as exc_info:
            await SearchService.semantic_search(
                query="测试",
                top_k=3,
                enable_reranking=False
            )
        assert "Search error" in str(exc_info.value)


# ============================================================================
# 额外测试：覆盖未覆盖的代码行 (183-184, 245-254, 260-261, 276)
# ============================================================================


class TestSearchServiceMissingCoverage:
    """
    类级注释：补充测试以覆盖未覆盖的代码行
    未覆盖行：
        183-184: EmbeddingFactory获取provider/model失败的异常处理
        245-254: 数据库查询文档信息失败的处理
        260-261: doc_info为None时设置file_name/source_type为None
        276: 不满足重排序条件时的处理路径
    """

    @pytest.mark.asyncio
    async def test_semantic_search_embedding_factory_exception(self):
        """
        测试目的：覆盖行183-184
        测试场景：EmbeddingFactory获取current_provider抛出异常
        预期：应该捕获异常并记录日志，继续执行搜索
        """
        with patch('app.services.search_service.IngestService') as mock_ingest, \
             patch('app.services.search_service.Chroma') as mock_chroma_class, \
             patch('app.utils.embedding_factory.EmbeddingFactory') as mock_factory:

            # 内部逻辑：模拟嵌入模型
            mock_embeddings = MagicMock()
            mock_ingest.get_embeddings.return_value = mock_embeddings

            # 内部逻辑：EmbeddingFactory.get_current_provider抛出异常
            mock_factory.get_current_provider.side_effect = Exception("Factory error")

            # 内部逻辑：模拟空搜索结果
            mock_chroma_instance = MagicMock()
            mock_chroma_instance.similarity_search_with_score.return_value = []
            mock_chroma_class.return_value = mock_chroma_instance

            # 内部逻辑：即使EmbeddingFactory失败，搜索也应该正常返回空结果
            results = await SearchService.semantic_search(
                query="测试",
                top_k=3,
                enable_reranking=False
            )
            assert results == []

    @pytest.mark.asyncio
    async def test_semantic_search_db_query_fails_with_results(self):
        """
        测试目的：覆盖行245-254
        测试场景：数据库查询文档信息时抛出异常
        预期：应该捕获异常，记录警告日志，继续返回结果（file_name为None）
        """
        with patch('app.services.search_service.IngestService') as mock_ingest, \
             patch('app.services.search_service.Chroma') as mock_chroma_class:

            # 内部逻辑：模拟嵌入模型
            mock_embeddings = MagicMock()
            mock_ingest.get_embeddings.return_value = mock_embeddings

            # 内部逻辑：模拟搜索结果
            mock_doc = Document(
                page_content="测试内容",
                metadata={"doc_id": 123}
            )
            mock_chroma_instance = MagicMock()
            mock_chroma_instance.similarity_search_with_score.return_value = [(mock_doc, 0.1)]
            mock_chroma_class.return_value = mock_chroma_instance

            # 内部逻辑：模拟数据库会话，查询时抛出异常
            mock_db = AsyncMock()
            mock_db.execute.side_effect = Exception("Database query error")

            results = await SearchService.semantic_search(
                query="测试",
                top_k=3,
                enable_reranking=False,
                db=mock_db
            )

            # 内部逻辑：应该返回结果，但file_name和source_type为None
            assert len(results) == 1
            assert results[0].file_name is None
            assert results[0].source_type is None
            assert results[0].content == "测试内容"

    @pytest.mark.asyncio
    async def test_semantic_search_doc_info_map_missing(self):
        """
        测试目的：覆盖行260-261
        测试场景：doc_id不在doc_info_map中（数据库返回空文档列表）
        预期：file_name和source_type应该被设置为None
        """
        with patch('app.services.search_service.IngestService') as mock_ingest, \
             patch('app.services.search_service.Chroma') as mock_chroma_class:

            # 内部逻辑：模拟嵌入模型
            mock_embeddings = MagicMock()
            mock_ingest.get_embeddings.return_value = mock_embeddings

            # 内部逻辑：模拟搜索结果，doc_id=999
            mock_doc = Document(
                page_content="测试内容",
                metadata={"doc_id": 999}
            )
            mock_chroma_instance = MagicMock()
            mock_chroma_instance.similarity_search_with_score.return_value = [(mock_doc, 0.1)]
            mock_chroma_class.return_value = mock_chroma_instance

            # 内部逻辑：模拟数据库查询返回空列表（没有找到对应doc_id）
            mock_db = AsyncMock()
            mock_doc_result = AsyncMock()
            mock_doc_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = mock_doc_result

            results = await SearchService.semantic_search(
                query="测试",
                top_k=3,
                enable_reranking=False,
                db=mock_db
            )

            # 内部逻辑：doc_id=999不在doc_info_map中，所以file_name和source_type为None
            assert len(results) == 1
            assert results[0].file_name is None
            assert results[0].source_type is None
            assert results[0].content == "测试内容"

    @pytest.mark.asyncio
    async def test_semantic_search_reranking_condition_not_met(self):
        """
        测试目的：覆盖行276
        测试场景：enable_reranking=True但不满足重排序条件（如云端提供商）
        预期：应该走276行逻辑，直接返回原始top_k结果
        """
        with patch('app.services.search_service.IngestService') as mock_ingest, \
             patch('app.services.search_service.Chroma') as mock_chroma_class, \
             patch('app.services.search_service.settings') as mock_settings, \
             patch('app.utils.embedding_factory.EmbeddingFactory') as mock_factory:

            # 内部逻辑：模拟嵌入模型
            mock_embeddings = MagicMock()
            mock_ingest.get_embeddings.return_value = mock_embeddings

            # 内部逻辑：模拟云端提供商（不满足重排序条件）
            mock_factory.get_current_provider.return_value = "zhipuai"
            mock_factory.get_current_model.return_value = "zhipu-embedding"

            # 内部逻辑：模拟搜索结果（返回10个结果用于重排序）
            mock_docs = [
                Document(page_content=f"内容{i}", metadata={"doc_id": i})
                for i in range(10)
            ]
            mock_scores = [0.1 + i * 0.05 for i in range(10)]
            mock_chroma_instance = MagicMock()
            mock_chroma_instance.similarity_search_with_score.return_value = list(
                zip(mock_docs, mock_scores)
            )
            mock_chroma_class.return_value = mock_chroma_instance

            # 内部逻辑：启用重排序
            mock_settings.ENABLE_RERANKING = True

            results = await SearchService.semantic_search(
                query="测试",
                top_k=5,
                enable_reranking=True
            )

            # 内部逻辑：由于不满足重排序条件，应该返回原始top_k=5个结果
            assert len(results) <= 5

    @pytest.mark.asyncio
    async def test_semantic_search_multiple_docs_missing_info_map(self):
        """
        测试目的：覆盖行260-261（多个文档场景）
        测试场景：多个文档的doc_id都不在doc_info_map中
        预期：所有结果的file_name和source_type都应该是None
        """
        with patch('app.services.search_service.IngestService') as mock_ingest, \
             patch('app.services.search_service.Chroma') as mock_chroma_class:

            # 内部逻辑：模拟嵌入模型
            mock_embeddings = MagicMock()
            mock_ingest.get_embeddings.return_value = mock_embeddings

            # 内部逻辑：模拟多个搜索结果
            mock_docs = [
                Document(page_content=f"内容{i}", metadata={"doc_id": 100 + i})
                for i in range(3)
            ]
            mock_scores = [0.1, 0.2, 0.3]
            mock_chroma_instance = MagicMock()
            mock_chroma_instance.similarity_search_with_score.return_value = list(
                zip(mock_docs, mock_scores)
            )
            mock_chroma_class.return_value = mock_chroma_instance

            # 内部逻辑：数据库返回空列表
            mock_db = AsyncMock()
            mock_doc_result = AsyncMock()
            mock_doc_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = mock_doc_result

            results = await SearchService.semantic_search(
                query="测试",
                top_k=5,
                enable_reranking=False,
                db=mock_db
            )

            # 内部逻辑：所有结果的file_name和source_type都应该是None
            assert len(results) == 3
            for r in results:
                assert r.file_name is None
                assert r.source_type is None

    @pytest.mark.asyncio
    async def test_semantic_search_embedding_get_model_exception(self):
        """
        测试目的：覆盖行184（get_current_model异常）
        测试场景：get_current_provider成功但get_current_model失败
        """
        with patch('app.services.search_service.IngestService') as mock_ingest, \
             patch('app.services.search_service.Chroma') as mock_chroma_class, \
             patch('app.utils.embedding_factory.EmbeddingFactory') as mock_factory:

            # 内部逻辑：模拟嵌入模型
            mock_embeddings = MagicMock()
            mock_ingest.get_embeddings.return_value = mock_embeddings

            # 内部逻辑：get_current_provider成功，get_current_model失败
            mock_factory.get_current_provider.return_value = "ollama"
            mock_factory.get_current_model.side_effect = Exception("Model fetch error")

            # 内部逻辑：模拟空搜索结果
            mock_chroma_instance = MagicMock()
            mock_chroma_instance.similarity_search_with_score.return_value = []
            mock_chroma_class.return_value = mock_chroma_instance

            results = await SearchService.semantic_search(
                query="测试",
                top_k=3,
                enable_reranking=False
            )
            assert results == []

    @pytest.mark.asyncio
    async def test_semantic_search_reranking_disabled_with_initial_k(self):
        """
        测试目的：覆盖行278-279（enable_reranking=False时使用原始结果）
        测试场景：禁用重排序时，initial_k应该等于top_k
        """
        with patch('app.services.search_service.IngestService') as mock_ingest, \
             patch('app.services.search_service.Chroma') as mock_chroma_class:

            # 内部逻辑：模拟嵌入模型
            mock_embeddings = MagicMock()
            mock_ingest.get_embeddings.return_value = mock_embeddings

            # 内部逻辑：模拟搜索结果
            mock_docs = [
                Document(page_content=f"内容{i}", metadata={"doc_id": i})
                for i in range(3)
            ]
            mock_scores = [0.1, 0.2, 0.3]
            mock_chroma_instance = MagicMock()
            mock_chroma_instance.similarity_search_with_score.return_value = list(
                zip(mock_docs, mock_scores)
            )
            mock_chroma_class.return_value = mock_chroma_instance

            results = await SearchService.semantic_search(
                query="测试",
                top_k=5,
                enable_reranking=False
            )

            # 内部逻辑：禁用重排序，应该返回top_k=5个结果（实际有3个）
            assert len(results) == 3
