# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：对话处理管道模块
内部逻辑：使用责任链模式拆分ChatOrchestrator的多重职责
设计模式：责任链模式（Chain of Responsibility Pattern）+ 建造者模式（Builder Pattern）
设计原则：单一职责原则（SRP）、开闭原则（OCP）

实现说明：
    - 将ChatOrchestrator的多重职责拆分为独立的处理器
    - 每个处理器只负责一个特定的处理步骤
    - 支持处理器链的动态组合
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger


class PipelineContext:
    """
    类级注释：管道上下文
    设计模式：上下文对象模式
    职责：在管道处理器间传递数据
    """

    def __init__(self, request: Any, db: AsyncSession):
        """
        函数级注释：初始化管道上下文
        参数：
            request - 对话请求
            db - 数据库会话
        """
        # 内部变量：对话请求
        self.request = request
        # 内部变量：数据库会话
        self.db = db
        # 内部变量：上下文数据
        self.data: Dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        函数级注释：获取上下文数据
        参数：
            key - 数据键
            default - 默认值
        返回值：数据值
        """
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        函数级注释：设置上下文数据
        参数：
            key - 数据键
            value - 数据值
        """
        self.data[key] = value

    def has(self, key: str) -> bool:
        """
        函数级注释：检查是否存在数据
        参数：
            key - 数据键
        返回值：是否存在
        """
        return key in self.data


class PipelineHandler(ABC):
    """
    类级注释：管道处理器抽象基类
    设计模式：责任链模式 - 处理器接口
    职责：定义处理器的统一接口
    """

    # 内部变量：下一个处理器
    _next: Optional['PipelineHandler'] = None

    def set_next(self, handler: 'PipelineHandler') -> 'PipelineHandler':
        """
        函数级注释：设置下一个处理器
        参数：
            handler - 下一个处理器
        返回值：下一个处理器（支持链式调用）
        """
        self._next = handler
        return handler

    async def handle(self, context: PipelineContext) -> Any:
        """
        函数级注释：处理请求（模板方法）
        内部逻辑：执行当前处理 -> 传递给下一个处理器
        参数：
            context - 管道上下文
        返回值：处理结果
        """
        # 内部逻辑：执行当前处理
        result = await self._process(context)

        # 内部逻辑：传递给下一个处理器
        if self._next:
            return await self._next.handle(context)

        return result

    @abstractmethod
    async def _process(self, context: PipelineContext) -> Any:
        """
        函数级注释：执行具体处理逻辑（抽象方法）
        参数：
            context - 管道上下文
        返回值：处理结果
        """
        pass


class LLMInitializationHandler(PipelineHandler):
    """
    类级注释：LLM初始化处理器
    设计模式：责任链模式 - 具体处理器
    职责：初始化LLM和向量库
    """

    def __init__(self, streaming: bool = False):
        """
        函数级注释：初始化处理器
        参数：
            streaming - 是否使用流式模式
        """
        # 内部变量：是否流式
        self.streaming = streaming

    async def _process(self, context: PipelineContext) -> Any:
        """
        函数级注释：初始化LLM和向量库
        参数：
            context - 管道上下文
        """
        from app.services.ingest_service import IngestService
        from app.services.llm_provider import llm_provider
        from langchain_community.vectorstores import Chroma
        from app.core.config import settings

        # 内部逻辑：初始化向量库
        embeddings = IngestService.get_embeddings()
        vector_db = Chroma(
            persist_directory=settings.CHROMA_DB_PATH,
            embedding_function=embeddings,
            collection_name=settings.CHROMA_COLLECTION_NAME
        )

        # 内部逻辑：获取LLM实例
        llm = await llm_provider.get_llm(context.db, streaming=self.streaming)

        # 内部逻辑：存储到上下文
        context.set('vector_db', vector_db)
        context.set('llm', llm)

        logger.debug(f"LLM初始化完成: streaming={self.streaming}")


class SourceProcessingHandler(PipelineHandler):
    """
    类级注释：来源处理处理器
    设计模式：责任链模式 - 具体处理器
    职责：处理文档来源信息
    """

    def __init__(self, sources_processor):
        """
        函数级注释：初始化来源处理器
        参数：
            sources_processor - 来源处理器实例
        """
        # 内部变量：来源处理器
        self.sources_processor = sources_processor

    async def _process(self, context: PipelineContext) -> Any:
        """
        函数级注释：处理来源信息
        参数：
            context - 管道上下文
        """
        doc_ids = context.get('doc_ids', [])
        sources = await self.sources_processor.process(doc_ids, context.db)

        context.set('sources', sources)
        logger.debug(f"来源处理完成: {len(sources)}个来源")


class SensitiveDataFilterHandler(PipelineHandler):
    """
    类级注释：敏感信息过滤处理器
    设计模式：责任链模式 - 具体处理器
    职责：过滤回答中的敏感信息
    """

    def __init__(self, enabled: bool = True):
        """
        函数级注释：初始化过滤处理器
        参数：
            enabled - 是否启用过滤
        """
        # 内部变量：是否启用
        self.enabled = enabled

    async def _process(self, context: PipelineContext) -> Any:
        """
        函数级注释：过滤敏感信息
        参数：
            context - 管道上下文
        """
        from app.core.config import settings
        from app.utils.sensitive_data_filter import get_filter

        if not self.enabled or not settings.ENABLE_SENSITIVE_DATA_FILTER:
            return

        answer = context.get('answer', '')
        if not answer:
            return

        filter_instance = get_filter()
        filtered_answer, _ = filter_instance.filter_all(answer)
        context.set('answer', filtered_answer)

        logger.debug("敏感信息过滤完成")


class ResponseBuildingHandler(PipelineHandler):
    """
    类级注释：响应构建处理器
    设计模式：责任链模式 - 具体处理器
    职责：构建最终的响应对象
    """

    async def _process(self, context: PipelineContext) -> Any:
        """
        函数级注释：构建响应对象
        参数：
            context - 管道上下文
        返回值：响应对象
        """
        from app.schemas.chat import ChatResponse

        answer = context.get('answer', '')
        sources = context.get('sources', [])

        response = ChatResponse(answer=answer, sources=sources)
        context.set('response', response)

        logger.debug("响应构建完成")
        return response


class ChatPipeline:
    """
    类级注释：对话处理管道
    设计模式：责任链模式 + 建造者模式
    职责：管理和执行处理器链
    """

    def __init__(self):
        """函数级注释：初始化管道"""
        # 内部变量：链头
        self._head: Optional[PipelineHandler] = None
        # 内部变量：链尾
        self._tail: Optional[PipelineHandler] = None

    def add_handler(self, handler: PipelineHandler) -> 'ChatPipeline':
        """
        函数级注释：添加处理器
        参数：
            handler - 管道处理器
        返回值：管道自身（支持链式调用）
        """
        if self._head is None:
            self._head = handler
            self._tail = handler
        else:
            self._tail.set_next(handler)
            self._tail = handler
        return self

    async def execute(self, context: PipelineContext) -> Any:
        """
        函数级注释：执行管道
        参数：
            context - 管道上下文
        返回值：处理结果
        """
        if self._head is None:
            logger.warning("管道为空，没有处理器执行")
            return None
        return await self._head.handle(context)


class ChatPipelineBuilder:
    """
    类级注释：对话管道建造者
    设计模式：建造者模式
    职责：构建对话处理管道
    """

    def __init__(self):
        """函数级注释：初始化建造者"""
        # 内部变量：处理器工厂列表
        self._handler_factories: List[callable] = []
        # 内部变量：配置
        self._config: Dict[str, Any] = {}

    def with_streaming(self, streaming: bool = True) -> 'ChatPipelineBuilder':
        """
        函数级注释：设置流式模式
        参数：
            streaming - 是否流式
        返回值：建造者自身
        """
        self._config['streaming'] = streaming
        return self

    def with_llm_init(self) -> 'ChatPipelineBuilder':
        """
        函数级注释：添加LLM初始化处理器
        返回值：建造者自身
        """
        def factory():
            streaming = self._config.get('streaming', False)
            return LLMInitializationHandler(streaming=streaming)
        self._handler_factories.append(factory)
        return self

    def with_source_processing(self, sources_processor) -> 'ChatPipelineBuilder':
        """
        函数级注释：添加来源处理处理器
        参数：
            sources_processor - 来源处理器
        返回值：建造者自身
        """
        def factory():
            return SourceProcessingHandler(sources_processor)
        self._handler_factories.append(factory)
        return self

    def with_sensitive_filter(self, enabled: bool = True) -> 'ChatPipelineBuilder':
        """
        函数级注释：添加敏感信息过滤处理器
        参数：
            enabled - 是否启用
        返回值：建造者自身
        """
        def factory():
            return SensitiveDataFilterHandler(enabled=enabled)
        self._handler_factories.append(factory)
        return self

    def with_response_building(self) -> 'ChatPipelineBuilder':
        """
        函数级注释：添加响应构建处理器
        返回值：建造者自身
        """
        def factory():
            return ResponseBuildingHandler()
        self._handler_factories.append(factory)
        return self

    def build(self) -> ChatPipeline:
        """
        函数级注释：构建管道
        返回值：新的管道实例
        内部逻辑：每次构建创建新的管道实例
        """
        pipeline = ChatPipeline()
        for factory in self._handler_factories:
            pipeline.add_handler(factory())
        return pipeline


# 内部变量：导出所有公共接口
__all__ = [
    'PipelineContext',
    'PipelineHandler',
    'ChatPipeline',
    'ChatPipelineBuilder',
    'LLMInitializationHandler',
    'SourceProcessingHandler',
    'SensitiveDataFilterHandler',
    'ResponseBuildingHandler',
]
