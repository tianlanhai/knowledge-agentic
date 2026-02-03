"""
上海宇羲伏天智能科技有限公司出品

文件级注释：Pytest 配置与 Fixture 定义
内部逻辑：提供 FastAPI 客户端、异步数据库会话及通用 Mock 对象
"""

import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.main import create_app
from app.models.models import Base
from app.core.config import settings
from unittest.mock import MagicMock, AsyncMock, patch
import builtins
import os
import sys
import threading

# 内部变量：设置生产模式环境变量，确保版本配置测试正确
# 说明：开发模式下会绕过版本限制，影响测试结果
os.environ["ENVIRONMENT"] = "prod"
os.environ["DEVELOPMENT_MODE"] = "false"

# 内部变量：使用内存 SQLite 进行测试，确保测试隔离且快速
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# ============================================================================
# Mock Fixtures - 原本在 mock_fixtures.py 中，现合并到此处避免 pytest_plugins 问题
# ============================================================================

# 说明：移除了 patch_isinstance fixture
# 原因：全局 patch builtins.isinstance 会导致无限递归
# unittest.mock 内部会调用 isinstance，patch 后会触发自身，形成死循环
# 这是导致系统死机重启的根本原因


@pytest.fixture(autouse=True)
def disable_use_mock_logic():
    """
    函数级注释：在测试期间禁用业务逻辑中的 USE_MOCK 早返

    内部逻辑：修改 settings.USE_MOCK 为 False，确保测试时不走早返逻辑
    注意：autouse=True 确保所有测试自动应用此 mock
    """
    with patch.object(settings, "USE_MOCK", False):
        yield


@pytest.fixture(autouse=True)
def mock_embeddings():
    """
    函数级注释：全局 Mock Embedding 模型

    内部逻辑：返回预定义的模拟向量，避免加载真实模型消耗内存
    注意：autouse=True 确保所有测试自动应用此 mock
    """
    # 内部变量：创建 Embedding Mock 实例
    instance = MagicMock()
    instance.embed_documents.return_value = [[0.1] * 128]
    instance.embed_query.return_value = [0.1] * 128

    from langchain_community.embeddings import OllamaEmbeddings, HuggingFaceEmbeddings
    instance._mock_type_hint = OllamaEmbeddings  # 兼容旧逻辑

    # 内部变量：Mock 目标路径列表
    targets = [
        "langchain_community.embeddings.OllamaEmbeddings",
        "langchain_community.embeddings.HuggingFaceEmbeddings",
        "app.services.chat_service.OllamaEmbeddings",
        "app.services.ingest_service.OllamaEmbeddings",
        "app.services.ingest_service.HuggingFaceEmbeddings",
        "app.services.search_service.OllamaEmbeddings",
        "app.services.agent_service.OllamaEmbeddings"
    ]

    mocks = []
    for target in targets:
        try:
            p = patch(target, return_value=instance)
            p.start()
            mocks.append(p)
        except (ImportError, AttributeError):
            continue

    yield instance

    for p in mocks:
        p.stop()


@pytest.fixture(autouse=True)
def mock_chroma():
    """
    函数级注释：全局 Mock Chroma 向量库

    内部逻辑：创建真正的 BaseRetriever 子类实例以通过 Pydantic 校验
    注意：autouse=True 确保所有测试自动应用此 mock
    """
    from langchain_core.documents import Document
    from langchain_core.retrievers import BaseRetriever
    from langchain_community.vectorstores import Chroma

    class MockRetriever(BaseRetriever):
        """
        类级注释：Mock Retriever 实现，继承自 BaseRetriever 以通过类型校验
        """
        def _get_relevant_documents(self, query: str):
            """
            函数级注释：同步检索方法实现

            参数：
                query: 查询字符串

            返回值：
                Document 列表
            """
            doc = Document(
                page_content="这是模拟的文档内容",
                metadata={"doc_id": 1}
            )
            return [doc]

        async def _aget_relevant_documents(self, query: str):
            """
            函数级注释：异步检索方法实现

            参数：
                query: 查询字符串

            返回值：
                Document 列表
            """
            doc = Document(
                page_content="这是模拟的文档内容",
                metadata={"doc_id": 1}
            )
            return [doc]

    # 内部变量：创建真正的 Retriever 实例
    retriever_instance = MockRetriever()

    # 内部变量：创建文档 Mock 对象
    doc_mock = MagicMock()
    doc_mock.page_content = "这是模拟的文档内容"
    doc_mock.metadata = {"doc_id": 1}

    # 内部变量：创建 Chroma 实例 Mock
    instance = MagicMock()
    instance.persist.return_value = None
    instance.similarity_search.return_value = [doc_mock]
    instance.similarity_search_with_score.return_value = [(doc_mock, 0.1)]
    instance.as_retriever.return_value = retriever_instance  # 返回真正的 BaseRetriever 实例
    instance._mock_type_hint = Chroma

    targets = [
        "langchain_community.vectorstores.Chroma",
        "app.services.chat_service.Chroma",
        "app.services.ingest_service.Chroma",
        "app.services.search_service.Chroma",
        "app.services.agent_service.Chroma"
    ]

    mocks = []
    for target in targets:
        try:
            p = patch(target)
            mock_cls = p.start()
            mock_cls.return_value = instance
            mock_cls.from_documents.return_value = instance
            mocks.append(p)
        except (ImportError, AttributeError):
            continue

    yield instance

    for p in mocks:
        p.stop()


@pytest.fixture(autouse=True)
def mock_llm_factory(request):
    """
    函数级注释：全局 Mock LLMFactory，支持多模型提供商

    内部逻辑：使用 LangChain 提供的 FakeChatModel，Mock所有LLM提供商
    注意：LLM工厂测试需要真实的LLMFactory行为，所以跳过mock
    注意：autouse=True 确保所有测试自动应用此 mock
    """
    # 内部逻辑：LLM工厂和模型配置测试需要真实行为，跳过mock
    path_str = str(request.node.path).lower()
    skip_mock_patterns = [
        "test_llm_factory",  # 匹配 test_llm_factory.py, test_llm_factory_full.py, test_llm_factory_complete.py 等
        "test_embedding_factory",
        "test_model_config",
        "test_coverage_final",  # 内部逻辑：test_coverage_final也包含LLMFactory测试，需要跳过mock
        "test_coverage_deep"  # 内部逻辑：test_coverage_deep也包含LLMFactory测试，需要跳过mock
    ]
    if any(pattern in path_str for pattern in skip_mock_patterns):
        yield None
        return

    # 内部逻辑：使用 LangChain 官方提供的 FakeChatModel，满足 BaseLanguageModel 接口要求
    from langchain_core.language_models.fake_chat_models import FakeChatModel

    class MockChatModel(FakeChatModel):
        """
        类级注释：扩展 FakeChatModel，支持 bind_tools 方法（AgentService 需要）
        """
        def bind_tools(self, tools, **kwargs):
            """
            函数级注释：绑定工具到模型，返回自身以兼容 AgentService 调用

            参数：
                tools: 工具列表
                kwargs: 其他参数

            返回值：
                Runnable - 返回 self，因为 FakeChatModel 本身就是 Runnable
            """
            return self

    # 内部变量：创建 MockChatModel 实例，它会返回固定的 "fake response" 内容
    # FakeChatModel 已经返回 AIMessage，业务代码可以通过 .content 访问
    instance = MockChatModel()

    # 内部逻辑：Mock所有LLM提供商和LLMFactory
    targets = [
        "langchain_community.chat_models.ChatOllama",
        "langchain_community.chat_models.ChatZhipuAI",
        "langchain_community.chat_models.ChatOpenAI",
        "app.services.chat_service.ChatOllama",
        "app.services.agent_service.ChatOllama",
        "app.utils.llm_factory.LLMFactory.create_llm"
    ]

    mocks = []
    for target in targets:
        try:
            # 内部逻辑：LLMFactory.create_llm 需要返回Mock实例
            p = patch(target, return_value=instance)
            p.start()
            mocks.append(p)
        except (ImportError, AttributeError):
            continue

    yield instance

    for p in mocks:
        p.stop()


@pytest.fixture(autouse=True)
def mock_loaders():
    """
    函数级注释：Mock 所有文档加载器

    内部变量：mock文档对象，包含页面内容和元数据
    注意：autouse=True 确保所有测试自动应用此 mock
    """
    # 内部变量：创建Mock文档对象，包含页面内容和标题元数据
    doc = MagicMock()
    doc.page_content = "Mock 解析内容"
    doc.metadata = {"title": "Mock Title", "source": "mock_source"}

    # 内部变量：Mock加载器目标路径列表
    targets = [
        "langchain_community.document_loaders.UnstructuredFileLoader",
        "app.services.ingest_service.UnstructuredFileLoader",
        "langchain_community.document_loaders.UnstructuredURLLoader",
        "app.services.ingest_service.UnstructuredURLLoader",
        "langchain_community.document_loaders.WebBaseLoader",
        "app.services.ingest_service.WebBaseLoader",
        "langchain_community.document_loaders.SQLDatabaseLoader",
        "app.services.ingest_service.SQLDatabaseLoader"
    ]

    # 内部逻辑：启动所有Mock补丁
    mocks = []
    for target in targets:
        try:
            p = patch(target)
            mock_cls = p.start()
            # 内部逻辑：设置Mock类的load方法返回Mock文档列表
            mock_cls.return_value.load.return_value = [doc]
            mocks.append(p)
        except (ImportError, AttributeError):
            continue

    yield

    # 内部逻辑：停止所有Mock补丁
    for p in mocks:
        p.stop()


@pytest.fixture(autouse=True)
def mock_version_config(request):
    """
    函数级注释：Mock版本配置，允许所有提供商在测试中使用

    内部逻辑：绕过镜像版本限制，使ollama等所有提供商都可用于测试
    注意：version_config测试本身需要真实的版本验证，因此跳过mock
    注意：autouse=True 确保所有测试自动应用此 mock
    """
    # 内部逻辑：检测是否为version_config相关测试
    path_str = str(request.node.path).lower()
    skip_patterns = [
        "test_version_config",
        "test_simple_coverage",
        "test_version_api"
    ]
    # 内部逻辑：如果是版本配置测试，跳过mock
    if any(pattern in path_str for pattern in skip_patterns):
        yield
        return

    with patch("app.core.version_config.VersionConfig.is_llm_provider_supported", return_value=True):
        with patch("app.core.version_config.VersionConfig.is_embedding_provider_supported", return_value=True):
            with patch("app.services.model_config_service.VersionConfig.is_llm_provider_supported", return_value=True):
                yield


# ============================================================================
# 原有 conftest.py 内容
# ============================================================================

# 函数级注释：初始化全局会话工厂
# 内部逻辑：确保后台任务（如 process_url_background）可以访问 AsyncSessionLocal
async def _ensure_session_factory():
    """确保会话工厂已初始化"""
    import app.db.session as session_module
    if session_module.AsyncSessionLocal is None:
        await session_module.init_session_factory()


# 类级/全局变量：创建 FastAPI 应用实例
app = create_app()


# 内部逻辑：初始化DI容器和服务注册
# 这对于ChatOrchestrator等服务的正常运行是必需的
def _initialize_service_container():
    """
    函数级注释：初始化服务容器（依赖注入）

    内部逻辑：注册所有核心服务到容器，支持自动依赖注入
    注意：测试环境使用瞬态生命周期而不是作用域，避免作用域管理复杂性
    """
    from app.core.di.service_container import get_container
    from app.services.chat.service_initializer import initialize_chat_services
    from app.services.chat_service import ChatService
    from app.services.ingest_service import IngestService
    from app.services.search_service import SearchService

    # 内部变量：获取全局服务容器
    container = get_container()

    # 内部逻辑：注册聊天相关服务
    initialize_chat_services(container)

    # 内部逻辑：注册核心服务为瞬态服务（测试环境）
    # 瞬态服务：每次请求创建新实例，不需要作用域
    container.register_transient(ChatService, ChatService)
    container.register_transient(IngestService, IngestService)
    container.register_transient(SearchService, SearchService)


# 内部逻辑：在导入时立即初始化
_initialize_service_container()


# 函数级注释：注册所有 AI Provider 工厂
# 内部逻辑：确保测试运行时 AIProviderFactoryRegistry 有可用的工厂
def _register_ai_providers():
    """注册所有 AI Provider 工厂到注册表"""
    from app.core.ai_provider.registry import AIProviderFactoryRegistry
    from app.core.ai_provider.base import AIProviderType
    from app.core.ai_provider.providers.ollama import OllamaProviderFactory
    from app.core.ai_provider.providers.zhipuai import ZhipuAIProviderFactory
    from app.core.ai_provider.providers.openai import OpenAIProviderFactory
    from app.core.ai_provider.providers.deepseek import DeepSeekProviderFactory
    from app.core.ai_provider.providers.minimax import MiniMaxProviderFactory
    from app.core.ai_provider.providers.moonshot import MoonshotProviderFactory

    # 内部逻辑：注册所有提供商工厂
    factories = [
        (AIProviderType.OLLAMA, OllamaProviderFactory),
        (AIProviderType.ZHIPUAI, ZhipuAIProviderFactory),
        (AIProviderType.OPENAI, OpenAIProviderFactory),
        (AIProviderType.DEEPSEEK, DeepSeekProviderFactory),
        (AIProviderType.MINIMAX, MiniMaxProviderFactory),
        (AIProviderType.MOONSHOT, MoonshotProviderFactory),
    ]

    for provider_type, factory_class in factories:
        AIProviderFactoryRegistry.register(provider_type, factory_class)


# 内部逻辑：在导入时立即注册
_register_ai_providers()


@pytest.fixture(scope="session")
def event_loop():
    """
    函数级注释：创建并管理事件循环
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """
    函数级注释：创建测试数据库引擎并初始化表

    内部逻辑：创建SQLite引擎 -> 覆盖DatabaseFactory -> 初始化会话工厂
    """
    # 内部变量：创建测试专用引擎
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 内部逻辑：覆盖DatabaseFactory的引擎，使init_session_factory使用测试数据库
    from app.db import factory as db_factory
    db_factory._engine = engine

    # 内部逻辑：强制重新初始化会话工厂（现在使用测试引擎）
    import app.db.session as session_module
    session_module.AsyncSessionLocal = None  # 清除现有会话工厂
    await session_module.init_session_factory()  # 使用测试引擎重新初始化

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    函数级注释：提供干净的数据库会话 Fixture

    内部逻辑：每个测试用例开启一个事务，完成后回滚
    """
    connection = await db_engine.connect()
    transaction = await connection.begin()

    SessionLocal = sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )

    async with SessionLocal() as session:
        yield session

    await transaction.rollback()
    await connection.close()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    函数级注释：提供配置了测试数据库的 FastAPI 客户端

    内部逻辑：覆盖 get_db 依赖项
    """
    from app.db.session import get_db

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def reset_llm_factory_state():
    """
    函数级注释：重置LLMFactory状态

    内部逻辑：清除运行时配置和实例缓存，确保测试隔离
    """
    from app.utils.llm_factory import LLMFactory
    # 测试前清理
    LLMFactory._runtime_config = None
    LLMFactory._instance_cache.clear()
    yield
    # 测试后也清理
    LLMFactory._runtime_config = None
    LLMFactory._instance_cache.clear()


@pytest.fixture
def clean_llm_factory():
    """
    函数级注释：简化的LLMFactory清理fixture

    内部逻辑：只清理不返回
    """
    from app.utils.llm_factory import LLMFactory
    LLMFactory._runtime_config = None
    LLMFactory._instance_cache.clear()
