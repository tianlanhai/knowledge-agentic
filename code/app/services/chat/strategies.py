"""
上海宇羲伏天智能科技有限公司出品

文件级注释：对话策略模块
内部逻辑：定义不同对话模式的策略实现，支持RAG和Agent两种模式
设计模式：策略模式 + 工厂模式
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.schemas.chat import ChatRequest, SourceInfo
from app.models.models import Document, VectorMapping
from sqlalchemy.future import select


class ChatAnswer:
    """
    类级注释：对话回答结果封装
    内部逻辑：封装回答文本和来源数据，供编排器统一处理
    """

    def __init__(
        self,
        text: str,
        sources_data: List[int] = None
    ):
        """
        函数级注释：初始化回答结果
        参数：
            text - 回答文本内容
            sources_data - 来源文档ID列表
        """
        # 内部变量：回答文本
        self.text = text
        # 内部变量：来源文档ID列表
        self.sources_data = sources_data or []


class ChatStrategy(ABC):
    """
    类级注释：对话策略抽象基类
    内部逻辑：定义对话策略的统一接口
    设计模式：策略模式 - 抽象策略接口
    """

    @abstractmethod
    async def execute(
        self,
        request: ChatRequest,
        db: AsyncSession
    ) -> ChatAnswer:
        """
        函数级注释：执行对话策略
        内部逻辑：由具体策略实现各自的对话流程
        参数：
            request - 对话请求对象
            db - 数据库异步会话
        返回值：ChatAnswer - 对话回答结果
        """
        pass


class RAGStrategy(ChatStrategy):
    """
    类级注释：RAG对话策略实现
    内部逻辑：实现检索增强生成(RAG)流程
    设计模式：策略模式 - 具体策略实现
    """

    def __init__(self, vector_db, llm):
        """
        函数级注释：初始化RAG策略
        参数：
            vector_db - 向量数据库实例
            llm - 大语言模型实例
        """
        # 内部变量：向量数据库
        self.vector_db = vector_db
        # 内部变量：大语言模型
        self.llm = llm

    async def execute(
        self,
        request: ChatRequest,
        db: AsyncSession
    ) -> ChatAnswer:
        """
        函数级注释：执行RAG对话策略
        内部逻辑：检索相关文档 -> 构建上下文 -> 生成回答
        参数：
            request - 对话请求对象
            db - 数据库异步会话
        返回值：ChatAnswer - 对话回答结果
        """
        # 内部逻辑：检索相关文档
        retrieved_docs = self.vector_db.as_retriever(
            search_kwargs={"k": 3}
        ).invoke(request.message)

        # 内部逻辑：构建上下文
        def format_docs(docs):
            """内部函数：格式化文档为上下文字符串"""
            return "\n\n".join(doc.page_content for doc in docs)

        context = format_docs(retrieved_docs)

        # 内部逻辑：构建Prompt
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.runnables import RunnablePassthrough

        prompt = ChatPromptTemplate.from_template(
            """帅哥，请基于以下提供的参考资料回答用户的问题。
如果你在资料中找不到答案，就直接说你不知道，不要尝试胡编乱造。

【重要约束】
在回答中绝对不要包含以下信息：
- 任何手机号码（11位数字）
- 任何邮箱地址

如果需要引用联系方式，请使用"联系方式"、"电话"等替代表述。

参考资料:
{context}

用户问题: {question}

回答:"""
        )

        # 内部逻辑：构建RAG链
        rag_chain = (
            {
                "context": self.vector_db.as_retriever(search_kwargs={"k": 3}) | format_docs,
                "question": RunnablePassthrough()
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )

        # 内部逻辑：执行查询获取回答
        answer = rag_chain.invoke(request.message)

        # 内部逻辑：提取来源文档ID
        doc_ids = [
            doc.metadata.get("doc_id", 0)
            for doc in retrieved_docs
            if doc.metadata.get("doc_id")
        ]

        # 内部逻辑：应用敏感信息过滤
        from app.core.config import settings
        from app.utils.sensitive_data_filter import get_filter

        if settings.ENABLE_SENSITIVE_DATA_FILTER:
            filter_instance = get_filter()
            answer, _ = filter_instance.filter_all(answer)

        return ChatAnswer(text=answer, sources_data=doc_ids)


class AgentStrategy(ChatStrategy):
    """
    类级注释：Agent对话策略实现
    内部逻辑：实现智能体对话流程
    设计模式：策略模式 - 具体策略实现
    """

    def __init__(self, agent_service):
        """
        函数级注释：初始化Agent策略
        参数：
            agent_service - 智能体服务实例
        """
        # 内部变量：智能体服务
        self.agent_service = agent_service

    async def execute(
        self,
        request: ChatRequest,
        db: AsyncSession
    ) -> ChatAnswer:
        """
        函数级注释：执行Agent对话策略
        内部逻辑：调用智能体服务生成回答
        参数：
            request - 对话请求对象
            db - 数据库异步会话
        返回值：ChatAnswer - 对话回答结果
        """
        # 内部逻辑：转换历史记录为LangChain格式
        from langchain_core.messages import HumanMessage, AIMessage

        history = []
        if request.history:
            for msg in request.history:
                if msg.role == "user":
                    history.append(HumanMessage(content=msg.content))
                else:
                    history.append(AIMessage(content=msg.content))

        # 内部逻辑：运行智能体
        result = await self.agent_service.run(request.message, history=history)

        # 内部逻辑：应用敏感信息过滤
        from app.core.config import settings
        from app.utils.sensitive_data_filter import get_filter

        filtered_answer = result["answer"]
        if settings.ENABLE_SENSITIVE_DATA_FILTER:
            filter_instance = get_filter()
            filtered_answer, _ = filter_instance.filter_all(filtered_answer)

        # 内部逻辑：提取来源文档ID
        doc_ids = result.get("sources", [])

        return ChatAnswer(text=filtered_answer, sources_data=doc_ids)


class ChatStrategyFactory:
    """
    类级注释：对话策略工厂
    内部逻辑：管理对话策略的注册和创建
    设计模式：工厂模式 + 注册表模式
    """

    # 内部变量：策略注册表
    _strategies: Dict[str, ChatStrategy] = {}

    @classmethod
    def register(cls, name: str, strategy: ChatStrategy) -> None:
        """
        函数级注释：注册策略
        内部逻辑：将策略实例注册到工厂
        参数：
            name - 策略名称
            strategy - 策略实例
        返回值：None
        """
        cls._strategies[name] = strategy

    @classmethod
    def get_strategy(cls, use_agent: bool = False) -> ChatStrategy:
        """
        函数级注释：获取策略实例
        内部逻辑：根据参数返回对应的策略
        参数：
            use_agent - 是否使用Agent模式
        返回值：ChatStrategy - 策略实例
        @raises ValueError - 当策略不存在时抛出
        """
        strategy_name = "agent" if use_agent else "rag"
        strategy = cls._strategies.get(strategy_name)

        if not strategy:
            raise ValueError(f"未知的对话策略: {strategy_name}")

        return strategy

    @classmethod
    def clear(cls) -> None:
        """
        函数级注释：清空策略注册表
        内部逻辑：主要用于测试场景
        返回值：None
        """
        cls._strategies.clear()
