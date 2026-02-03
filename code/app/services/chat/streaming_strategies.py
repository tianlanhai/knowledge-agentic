# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：流式对话策略模块
内部逻辑：定义不同模式的流式对话策略，消除条件分支
设计模式：策略模式（Strategy Pattern）
设计原则：开闭原则、单一职责原则

实现说明：
    - 抽象策略接口定义统一的流式对话接口
    - 具体策略实现 RAG 和 Agent 两种流式对话模式
    - 使用工厂模式管理策略实例
"""

import json
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.chat import ChatRequest, SourceDetail
from app.services.chat.sources_processor import SourcesProcessor
from app.core.config import settings
from app.utils.sensitive_data_filter import get_filter, StreamingSensitiveFilter


class StreamingStrategy(ABC):
    """
    类级注释：流式对话策略抽象基类
    设计模式：策略模式 - 抽象策略接口
    职责：定义流式对话的统一接口
    """

    @abstractmethod
    async def execute(
        self,
        request: ChatRequest,
        db: AsyncSession
    ) -> AsyncGenerator[str, None]:
        """
        函数级注释：执行流式对话
        内部逻辑：由具体策略实现各自的流式对话流程
        参数：
            request - 对话请求
            db - 数据库会话
        生成值：str - SSE格式的数据块
        """
        pass


class RAGStreamingStrategy(StreamingStrategy):
    """
    类级注释：RAG模式流式策略
    设计模式：策略模式 - 具体策略实现
    职责：实现检索增强生成的流式对话
    """

    # 内部变量：策略名称
    name = "rag"

    def __init__(
        self,
        vector_db,
        llm,
        sources_processor: SourcesProcessor
    ):
        """
        函数级注释：初始化RAG流式策略
        参数：
            vector_db - 向量数据库
            llm - 大语言模型
            sources_processor - 来源处理器
        """
        # 内部变量：向量数据库
        self.vector_db = vector_db
        # 内部变量：大语言模型
        self.llm = llm
        # 内部变量：来源处理器
        self.sources_processor = sources_processor

    async def execute(
        self,
        request: ChatRequest,
        db: AsyncSession
    ) -> AsyncGenerator[str, None]:
        """
        函数级注释：执行RAG流式对话
        内部逻辑：检索 -> 发送来源 -> 流式生成回答
        """
        # 内部逻辑：检索相关文档
        docs = self.vector_db.similarity_search(request.message, k=3)
        context = "\n\n".join([doc.page_content for doc in docs])

        # 内部逻辑：构建Prompt
        prompt_template = """帅哥，请基于以下提供的参考资料回答用户的问题。

【重要约束】
在回答中绝对不要包含以下信息：
- 任何手机号码（11位数字）
- 任何邮箱地址

如果需要引用联系方式，请使用"联系方式"、"电话"等替代表述。

参考资料:
{context}

用户问题: {question}

回答:"""
        full_prompt = prompt_template.format(
            context=context,
            question=request.message
        )

        # 内部逻辑：处理来源信息
        doc_ids = [doc.metadata.get("doc_id", 0) for doc in docs if doc.metadata.get("doc_id")]
        sources = await self.sources_processor.process(doc_ids, db, docs)

        # 内部逻辑：先发送来源信息
        yield f"data: {json.dumps({'sources': [s.model_dump() for s in sources]}, ensure_ascii=False)}\n\n"

        # 内部逻辑：初始化流式敏感信息过滤器
        streaming_filter = None
        if settings.ENABLE_SENSITIVE_DATA_FILTER:
            filter_instance = get_filter()
            streaming_filter = StreamingSensitiveFilter(filter_instance, window_size=20)

        # 内部逻辑：流式生成回答（带降级处理）
        try:
            async for chunk in self.llm.astream(full_prompt):
                content = chunk.content

                # 内部逻辑：应用敏感信息过滤
                if streaming_filter:
                    content = streaming_filter.process(content)

                if content:
                    yield f"data: {json.dumps({'answer': content}, ensure_ascii=False)}\n\n"

        except Exception as e:
            """
            异常处理：捕获 LLM 流式调用过程中的所有异常
            内部逻辑：检测错误类型，尝试降级为非流式调用
            设计原则：防御性编程 - 优先保证服务可用性
            """
            import traceback
            error_msg = str(e) or "LLM流式调用失败（无详细错误信息）"
            logger.error(f"LLM流式调用异常: {error_msg}")
            logger.error(f"异常类型: {type(e).__name__}")
            logger.error(f"异常堆栈: {traceback.format_exc()}")

            # 内部逻辑：检测是否为流式响应格式错误，尝试降级为非流式调用
            # 常见场景：
            #   1. API返回JSON而非SSE（认证失败、限流、端点不支持流式等）
            #   2. 网络问题导致流式连接中断
            is_stream_format_error = (
                "text/event-stream" in error_msg and "application/json" in error_msg
            ) or (
                "Content-Type" in error_msg
            )
            is_sse_error = "SSEError" in type(e).__name__ or "event-source" in error_msg.lower()

            if is_stream_format_error or is_sse_error:
                logger.warning("检测到流式响应格式错误，尝试降级为非流式调用...")
                yield f"data: {json.dumps({'warning': '正在切换为非流式模式...'}, ensure_ascii=False)}\n\n"

                try:
                    # 内部逻辑：降级为非流式调用（invoke）
                    response = self.llm.invoke(full_prompt)
                    content = response.content

                    # 内部逻辑：应用敏感信息过滤
                    if streaming_filter:
                        content = streaming_filter.process(content)
                        # 内部逻辑：降级调用后也需要刷新过滤器
                        remaining = streaming_filter.flush()
                        if remaining:
                            content = content + remaining

                    if content:
                        yield f"data: {json.dumps({'answer': content}, ensure_ascii=False)}\n\n"

                    logger.info("非流式降级调用成功")

                except Exception as fallback_error:
                    """
                    异常处理：非流式调用也失败时的最终错误处理
                    内部逻辑：记录降级调用失败信息，返回友好错误消息
                    """
                    fallback_msg = str(fallback_error)
                    logger.error(f"非流式降级调用也失败: {fallback_msg}")
                    yield f"data: {json.dumps({'error': f'LLM调用失败（流式和非流式均失败）: {fallback_msg}'}, ensure_ascii=False)}\n\n"
            else:
                # 内部逻辑：其他类型的错误直接返回，不尝试降级
                yield f"data: {json.dumps({'error': f'LLM调用失败: {error_msg}'}, ensure_ascii=False)}\n\n"

        # 内部逻辑：刷新过滤器缓冲区
        if streaming_filter:
            remaining = streaming_filter.flush()
            if remaining:
                yield f"data: {json.dumps({'answer': remaining}, ensure_ascii=False)}\n\n"


class AgentStreamingStrategy(StreamingStrategy):
    """
    类级注释：Agent模式流式策略
    设计模式：策略模式 - 具体策略实现
    职责：实现智能体的流式对话
    """

    # 内部变量：策略名称
    name = "agent"

    def __init__(
        self,
        agent_service,
        sources_processor: SourcesProcessor,
        llm_provider
    ):
        """
        函数级注释：初始化Agent流式策略
        参数：
            agent_service - 智能体服务
            sources_processor - 来源处理器
            llm_provider - LLM提供商
        """
        # 内部变量：智能体服务
        self.agent_service = agent_service
        # 内部变量：来源处理器
        self.sources_processor = sources_processor
        # 内部变量：LLM提供商
        self.llm_provider = llm_provider

    async def execute(
        self,
        request: ChatRequest,
        db: AsyncSession
    ) -> AsyncGenerator[str, None]:
        """
        函数级注释：执行Agent流式对话
        内部逻辑：调用Agent服务 -> 处理来源 -> 发送完整回答
        """
        # 内部逻辑：确保Agent使用正确的LLM配置
        await self.llm_provider.refresh_config(db)

        # 内部逻辑：运行Agent
        agent = self.agent_service
        result = await agent.run(request.message)

        # 内部逻辑：处理来源信息
        doc_ids = result.get("sources", [])
        sources = await self.sources_processor.process(doc_ids, db)

        # 内部逻辑：应用敏感信息过滤（Guard Clause - 防止answer键缺失）
        filtered_answer = result.get("answer", "")
        if settings.ENABLE_SENSITIVE_DATA_FILTER and filtered_answer:
            filter_instance = get_filter()
            filtered_answer, _ = filter_instance.filter_all(filtered_answer)

        # 内部逻辑：Agent模式一次性发送完整回答
        yield f"data: {json.dumps({'answer': filtered_answer, 'sources': [s.model_dump() for s in sources]}, ensure_ascii=False)}\n\n"


class StreamingStrategyFactory:
    """
    类级注释：流式策略工厂
    设计模式：工厂模式 + 策略模式
    职责：管理流式策略的创建和获取
    """

    # 内部变量：策略缓存
    _strategies = {}

    # 内部变量：依赖注入容器
    _dependencies = {}

    @classmethod
    def set_dependencies(cls, **kwargs) -> None:
        """
        函数级注释：设置依赖项
        内部逻辑：注入策略需要的依赖
        参数：
            **kwargs - 依赖项字典
        """
        cls._dependencies = kwargs
        # 内部逻辑：清空缓存，强制重新创建策略
        cls._strategies.clear()

    @classmethod
    def get_strategy(cls, use_agent: bool) -> StreamingStrategy:
        """
        函数级注释：获取流式策略
        内部逻辑：验证依赖注入 -> 根据参数返回对应的策略
        参数：
            use_agent - 是否使用Agent模式
        返回值：StreamingStrategy - 流式策略实例
        异常：
            ValueError - 依赖项未注入时抛出
        """
        cache_key = f"{'agent' if use_agent else 'rag'}_streaming"

        # 内部逻辑：验证依赖是否已注入（Guard Clauses - 早期验证）
        if use_agent:
            # Agent 模式需要的依赖
            required_deps = {
                'agent_service': 'Agent服务',
                'sources_processor': '来源处理器',
                'llm_provider': 'LLM提供者'
            }
        else:
            # RAG 模式需要的依赖
            required_deps = {
                'vector_db': '向量数据库',
                'llm': '大语言模型',
                'sources_processor': '来源处理器'
            }

        # 内部逻辑：检查缺失的依赖
        missing_deps = [
            f"{name}({desc})" for name, desc in required_deps.items()
            if name not in cls._dependencies or cls._dependencies[name] is None
        ]

        # Guard Clauses：依赖缺失时抛出明确异常
        if missing_deps:
            missing_str = ", ".join(missing_deps)
            error_msg = f"流式策略依赖项未注入或为空: [{missing_str}]"
            logger.error(error_msg)
            logger.error(f"当前已注入的依赖: {list(cls._dependencies.keys())}")
            raise ValueError(error_msg)

        # 内部逻辑：检查缓存
        if cache_key not in cls._strategies:
            if use_agent:
                cls._strategies[cache_key] = AgentStreamingStrategy(
                    agent_service=cls._dependencies.get('agent_service'),
                    sources_processor=cls._dependencies.get('sources_processor'),
                    llm_provider=cls._dependencies.get('llm_provider')
                )
            else:
                cls._strategies[cache_key] = RAGStreamingStrategy(
                    vector_db=cls._dependencies.get('vector_db'),
                    llm=cls._dependencies.get('llm'),
                    sources_processor=cls._dependencies.get('sources_processor')
                )

        return cls._strategies[cache_key]

    @classmethod
    def clear(cls) -> None:
        """
        函数级注释：清空策略缓存
        内部逻辑：主要用于测试场景
        """
        cls._strategies.clear()
        cls._dependencies.clear()


# 内部变量：导出所有公共接口
__all__ = [
    'StreamingStrategy',
    'RAGStreamingStrategy',
    'AgentStreamingStrategy',
    'StreamingStrategyFactory',
]
