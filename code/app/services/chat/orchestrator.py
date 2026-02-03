"""
上海宇羲伏天智能科技有限公司出品

文件级注释：对话编排器模块
内部逻辑：协调各组件完成对话流程，提供统一的对话接口
设计模式：外观模式 + 模板方法模式 + 策略模式 + 依赖注入模式
职责：编排对话流程，协调策略、来源处理器和格式化器
设计原则：依赖倒置原则（DIP）、单一职责原则（SRP）
"""

import json
from typing import List, AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.schemas.chat import ChatRequest, ChatResponse, SourceDetail
from app.services.chat.strategies import (
    ChatStrategyFactory,
    RAGStrategy,
    AgentStrategy,
    ChatAnswer
)
from app.services.chat.streaming_strategies import StreamingStrategyFactory
from app.services.chat.sources_processor import SourcesProcessor
from app.services.chat.document_formatter import DocumentFormatter, DocumentFormatterBuilder
from app.models.models import Document, VectorMapping
from sqlalchemy.future import select

# 内部逻辑：导入依赖服务
from app.services.ingest_service import IngestService
from app.services.agent_service import AgentService
from app.services.llm_provider import llm_provider
from app.core.config import settings
from app.utils.sensitive_data_filter import get_filter, StreamingSensitiveFilter


class ChatOrchestrator:
    """
    类级注释：对话编排器（优化后）
    内部逻辑：协调各组件完成对话流程
    设计模式：外观模式 + 依赖注入模式
    职责：
        1. 通过依赖注入获取各组件
        2. 执行对话流程
        3. 处理流式响应
    设计原则：依赖倒置原则（DIP）- 依赖抽象而非具体实现
    """

    def __init__(
        self,
        sources_processor: SourcesProcessor,
        document_formatter: DocumentFormatter,
        agent_service: Optional[AgentService] = None
    ):
        """
        函数级注释：初始化编排器（构造函数注入）
        设计模式：依赖注入模式 - 通过构造函数注入依赖
        参数：
            sources_processor - 来源处理器（注入）
            document_formatter - 文档格式化器（注入）
            agent_service - Agent服务（可选注入）
        返回值：None

        使用示例：
            # 通过依赖注入容器自动创建
            orchestrator = container.get_service(ChatOrchestrator)

            # 手动创建（用于测试）
            orchestrator = ChatOrchestrator(
                sources_processor=SourcesProcessor(),
                document_formatter=DocumentFormatter()
            )
        """
        # 内部变量：来源处理器（通过依赖注入）
        self.sources_processor = sources_processor
        # 内部变量：文档格式化器（通过依赖注入）
        self.document_formatter = document_formatter
        # 内部变量：Agent服务（可选依赖）
        self._agent_service = agent_service

    async def chat(
        self,
        db: AsyncSession,
        request: ChatRequest
    ) -> ChatResponse:
        """
        函数级注释：执行非流式对话
        内部逻辑：选择策略 -> 执行对话 -> 处理来源 -> 返回响应
        设计模式：模板方法模式 - 定义对话流程骨架
        参数：
            db - 数据库异步会话
            request - 对话请求对象
        返回值：ChatResponse - 对话响应
        """
        # Guard Clauses：Mock模式处理
        if settings.USE_MOCK:
            return ChatResponse(
                answer="帅哥，这是 Mock 模式下的模拟回答。开启 USE_MOCK=True 时，系统不会调用真实模型。",
                sources=[]
            )

        # 内部逻辑：初始化向量库和模型
        embeddings = IngestService.get_embeddings()
        from langchain_community.vectorstores import Chroma
        vector_db = Chroma(
            persist_directory=settings.CHROMA_DB_PATH,
            embedding_function=embeddings,
            collection_name=settings.CHROMA_COLLECTION_NAME
        )

        # 内部变量：获取非流式LLM实例
        llm = await llm_provider.get_llm(db, streaming=False)

        # 内部逻辑：注册策略
        # 内部变量：AgentService（延迟初始化，避免在RAG模式下创建）
        agent_svc = None
        if request.use_agent:
            # 内部逻辑：只在 Agent 模式下创建 AgentService
            # 原因：某些 LLM 不支持 bind_tools()，会导致 NotImplementedError
            try:
                agent_svc = self._agent_service if self._agent_service else AgentService()
            except NotImplementedError:
                # 内部逻辑：LLM 不支持 bind_tools()，无法使用 Agent 模式
                logger.warning("当前 LLM 不支持 bind_tools()，无法使用 Agent 模式，将回退到 RAG 模式")
                request.use_agent = False

        ChatStrategyFactory.clear()
        ChatStrategyFactory.register("rag", RAGStrategy(vector_db, llm))
        if agent_svc:
            ChatStrategyFactory.register("agent", AgentStrategy(agent_svc))

        # 内部逻辑：选择并执行策略
        strategy = ChatStrategyFactory.get_strategy(request.use_agent)
        answer: ChatAnswer = await strategy.execute(request, db)

        # 内部逻辑：处理来源信息
        sources = await self.sources_processor.process(
            answer.sources_data,
            db
        )

        return ChatResponse(
            answer=answer.text,
            sources=sources
        )

    async def stream_chat(
        self,
        db: AsyncSession,
        request: ChatRequest
    ) -> AsyncGenerator[str, None]:
        """
        函数级注释：执行流式对话
        内部逻辑：初始化 -> 获取策略 -> 委托执行 -> 发送完成标记
        设计模式：策略模式 - 消除条件分支
        参数：
            db - 数据库异步会话
            request - 对话请求对象
        生成值：str - SSE格式的数据块
        """
        try:
            # 内部变量：调试日志
            logger.debug(f"开始流式对话: use_agent={request.use_agent}, message={request.message[:50]}...")

            # Guard Clauses：Mock模式处理
            if settings.USE_MOCK:
                yield "data: " + ChatResponse(
                    answer="帅哥，这是 Mock 模式下的流式回答。",
                    sources=[]
                ).model_dump_json() + "\n\n"
                return

            # 内部逻辑：初始化向量库和模型
            logger.debug("初始化向量库和LLM...")
            embeddings = IngestService.get_embeddings()
            from langchain_community.vectorstores import Chroma
            vector_db = Chroma(
                persist_directory=settings.CHROMA_DB_PATH,
                embedding_function=embeddings,
                collection_name=settings.CHROMA_COLLECTION_NAME
            )

            # 内部变量：获取流式LLM实例
            logger.debug("获取流式LLM实例...")
            llm = await llm_provider.get_llm(db, streaming=True)
            logger.debug(f"LLM实例类型: {type(llm).__name__}")

            # 内部逻辑：设置流式策略依赖
            # 内部变量：AgentService（延迟初始化，避免在RAG模式下创建）
            agent_svc = None
            if request.use_agent:
                # 内部逻辑：只在 Agent 模式下创建 AgentService
                # 原因：某些 LLM 不支持 bind_tools()，会导致 NotImplementedError
                try:
                    agent_svc = self._agent_service if self._agent_service else AgentService()
                    logger.debug(f"AgentService已创建: {type(agent_svc).__name__}")
                except NotImplementedError:
                    # 内部逻辑：LLM 不支持 bind_tools()，无法使用 Agent 模式
                    logger.warning("当前 LLM 不支持 bind_tools()，无法使用 Agent 模式，将回退到 RAG 模式")
                    request.use_agent = False

            StreamingStrategyFactory.set_dependencies(
                vector_db=vector_db,
                llm=llm,
                sources_processor=self.sources_processor,
                agent_service=agent_svc,
                llm_provider=llm_provider
            )
            logger.debug("流式策略依赖已设置")

            # 内部逻辑：获取流式策略（关键：使用策略模式消除if-else）
            logger.debug(f"获取流式策略: use_agent={request.use_agent}")
            strategy = StreamingStrategyFactory.get_strategy(use_agent=request.use_agent)
            logger.debug(f"策略实例类型: {type(strategy).__name__}")

            # 内部逻辑：委托给策略执行
            logger.debug("开始执行流式策略...")
            async for chunk in strategy.execute(request, db):
                yield chunk
            logger.debug("流式策略执行完成")

        except Exception as e:
            """
            异常处理：捕获流式对话过程中的所有异常
            内部逻辑：记录详细错误信息和堆栈跟踪
            """
            import traceback
            error_msg = str(e) or "流式对话失败（无详细错误信息）"
            logger.error(f"流式对话异常: {error_msg}")
            logger.error(f"异常类型: {type(e).__name__}")
            logger.error(f"异常堆栈: {traceback.format_exc()}")
            yield f"data: {json.dumps({'error': error_msg}, ensure_ascii=False)}\n\n"

        finally:
            # 内部逻辑：确保发送完成标记
            yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"

    async def get_sources(
        self,
        db: AsyncSession,
        doc_id: Optional[int] = None
    ) -> List[SourceDetail]:
        """
        函数级注释：获取来源详情
        内部逻辑：查询文档元数据及片段备份
        参数：
            db - 数据库会话
            doc_id - 文档ID（可选）
        返回值：List[SourceDetail] - 来源详情列表
        """
        from app.models.models import VectorMapping

        # 内部逻辑：构建查询
        if doc_id:
            result = await db.execute(
                select(VectorMapping, Document)
                .join(Document, VectorMapping.document_id == Document.id)
                .where(Document.id == doc_id)
            )
        else:
            result = await db.execute(
                select(VectorMapping, Document)
                .join(Document, VectorMapping.document_id == Document.id)
                .limit(10)
            )

        rows = result.all()

        # Guard Clauses：无数据时返回空列表
        if not rows:
            return []

        # 内部逻辑：格式化文档内容
        formatted_rows = []
        for mapping, doc in rows:
            # 内部逻辑：使用建造者模式构建格式化选项
            formatting_options = (DocumentFormatterBuilder()
                .with_highlight(['重要', '关键', '注意'])
                .build())

            formatted_content = self.document_formatter.format_document(
                mapping.chunk_content,
                formatting_options
            )

            formatted_rows.append(SourceDetail(
                doc_id=doc.id,
                file_name=doc.file_name,
                content=formatted_content,
                score=None
            ))

        return formatted_rows

    async def summarize_document(
        self,
        db: AsyncSession,
        doc_id: int
    ) -> str:
        """
        函数级注释：文档总结
        内部逻辑：获取文档内容 -> 调用LLM生成总结
        参数：
            db - 数据库会话
            doc_id - 文档ID
        返回值：str - 总结结果
        """
        from app.models.models import VectorMapping
        from fastapi import HTTPException

        # 内部逻辑：获取文档内容
        result = await db.execute(
            select(VectorMapping.chunk_content).where(
                VectorMapping.document_id == doc_id
            )
        )
        chunks = result.scalars().all()

        # Guard Clauses：无内容时抛出异常
        if not chunks:
            raise HTTPException(status_code=404, detail="未找到文档内容")

        full_text = "\n".join(chunks)

        # 内部变量：获取LLM实例
        llm = await llm_provider.get_llm(db, streaming=False)

        # 内部逻辑：构造总结Prompt
        prompt = f"帅哥，请帮我总结下面这段文档的核心内容：\n\n{full_text[:4000]}"

        # 内部逻辑：调用模型
        response = await llm.ainvoke(prompt)
        return response.content

    async def compare_documents(
        self,
        db: AsyncSession,
        doc_ids: List[int]
    ) -> str:
        """
        函数级注释：文档对比
        内部逻辑：获取多文档内容 -> 调用LLM生成对比
        优化：使用单次查询替代循环查询（N+1问题优化）
        参数：
            db - 数据库会话
            doc_ids - 文档ID列表
        返回值：str - 对比结果
        """
        from app.models.models import VectorMapping
        from fastapi import HTTPException

        # Guard Clauses：文档ID列表为空时抛出异常
        if not doc_ids:
            raise HTTPException(status_code=400, detail="文档ID列表不能为空")

        # 内部逻辑：一次性查询所有文档内容（优化 N+1 查询问题）
        result = await db.execute(
            select(
                Document.id,
                Document.file_name,
                VectorMapping.chunk_content
            )
            .join(VectorMapping, Document.id == VectorMapping.document_id)
            .where(Document.id.in_(doc_ids))
            .order_by(Document.id)
        )

        rows = result.all()

        # Guard Clauses：无内容时抛出异常
        if not rows:
            raise HTTPException(status_code=404, detail="未找到对比文档的内容")

        # 内部逻辑：按文档ID分组并格式化内容
        from collections import defaultdict
        doc_chunks = defaultdict(list)
        for row in rows:
            doc_chunks[row[0]].append((row[1], row[2]))  # (file_name, chunk_content)

        # 内部逻辑：构造对比内容
        contents = []
        for doc_id in doc_ids:
            if doc_id in doc_chunks:
                file_name = doc_chunks[doc_id][0][0]  # 获取文件名
                text = "\n".join([chunk[1] for chunk in doc_chunks[doc_id]])
                contents.append(f"文档名: {file_name}\n内容: {text[:2000]}")

        # 内部逻辑：构造对比Prompt
        comparison_text = "\n\n---\n\n".join(contents)
        prompt = f"帅哥，请帮我对比分析以下几份文档的异同：\n\n{comparison_text}"

        # 内部变量：获取LLM实例
        llm = await llm_provider.get_llm(db, streaming=False)

        # 内部逻辑：调用模型
        response = await llm.ainvoke(prompt)
        return response.content
