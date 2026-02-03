# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：对话服务门面模块
内部逻辑：提供统一简单的接口，隐藏内部复杂性
设计模式：门面模式（Facade Pattern）
设计原则：最少知识原则（Principle of Least Knowledge）

实现说明：
    - 提供统一的对话接口
    - 隐藏复杂的初始化和配置
    - 简化客户端调用
"""

from typing import List, AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.schemas.chat import ChatRequest, ChatResponse, SourceDetail
from app.services.chat_service import ChatService
from app.core.config import settings


class ChatServiceFacade:
    """
    类级注释：对话服务门面
    设计模式：门面模式
    职责：
        1. 提供统一的对话接口
        2. 隐藏复杂的初始化和配置
        3. 简化客户端调用
    """

    def __init__(self):
        """函数级注释：初始化门面"""
        # 内部变量：延迟初始化编排器
        self._orchestrator = None

    def _get_orchestrator(self):
        """
        函数级注释：获取编排器实例（延迟初始化）
        返回值：ChatOrchestrator实例
        """
        if self._orchestrator is None:
            from app.services.chat.orchestrator import ChatOrchestrator
            self._orchestrator = ChatOrchestrator()
        return self._orchestrator

    async def chat(
        self,
        message: str,
        db: AsyncSession,
        use_agent: bool = False,
        history: Optional[List] = None
    ) -> ChatResponse:
        """
        函数级注释：执行对话（简化的接口）
        设计模式：门面模式 - 简化调用
        参数：
            message - 用户消息
            db - 数据库会话
            use_agent - 是否使用Agent模式
            history - 对话历史
        返回值：对话响应
        """
        from app.schemas.chat import ChatRequest

        # 内部逻辑：构建请求
        request = ChatRequest(
            message=message,
            use_agent=use_agent,
            history=history or []
        )

        # 内部逻辑：委托给编排器
        orchestrator = self._get_orchestrator()
        return await orchestrator.chat(db, request)

    async def stream_chat(
        self,
        message: str,
        db: AsyncSession,
        use_agent: bool = False,
        history: Optional[List] = None
    ) -> AsyncGenerator[str, None]:
        """
        函数级注释：执行流式对话（简化的接口）
        设计模式：门面模式 - 简化调用
        参数：
            message - 用户消息
            db - 数据库会话
            use_agent - 是否使用Agent模式
            history - 对话历史
        生成值：SSE格式的数据块
        """
        from app.schemas.chat import ChatRequest

        request = ChatRequest(
            message=message,
            use_agent=use_agent,
            history=history or []
        )

        orchestrator = self._get_orchestrator()
        async for chunk in orchestrator.stream_chat(db, request):
            yield chunk

    async def get_sources(
        self,
        db: AsyncSession,
        doc_id: Optional[int] = None
    ) -> List[SourceDetail]:
        """
        函数级注释：获取来源详情（简化的接口）
        设计模式：门面模式 - 简化调用
        参数：
            db - 数据库会话
            doc_id - 可选的文档ID
        返回值：来源详情列表
        """
        orchestrator = self._get_orchestrator()
        return await orchestrator.get_sources(db, doc_id)

    async def summarize_document(
        self,
        db: AsyncSession,
        doc_id: int
    ) -> str:
        """
        函数级注释：总结文档（简化的接口）
        设计模式：门面模式 - 简化调用
        参数：
            db - 数据库会话
            doc_id - 文档ID
        返回值：总结结果
        """
        orchestrator = self._get_orchestrator()
        return await orchestrator.summarize_document(db, doc_id)

    async def compare_documents(
        self,
        db: AsyncSession,
        doc_ids: List[int]
    ) -> str:
        """
        函数级注释：对比文档（简化的接口）
        设计模式：门面模式 - 简化调用
        参数：
            db - 数据库会话
            doc_ids - 文档ID列表
        返回值：对比结果
        """
        orchestrator = self._get_orchestrator()
        return await orchestrator.compare_documents(db, doc_ids)

    async def quick_chat(
        self,
        message: str,
        db: AsyncSession,
        use_agent: bool = False
    ) -> str:
        """
        函数级注释：快速对话（只返回回答文本）
        设计模式：门面模式 - 最简接口
        参数：
            message - 用户消息
            db - 数据库会话
            use_agent - 是否使用Agent模式
        返回值：回答文本
        """
        response = await self.chat(message, db, use_agent)
        return response.answer


# 内部变量：全局门面实例
chat_facade = ChatServiceFacade()


# 内部变量：导出所有公共接口
__all__ = [
    'ChatServiceFacade',
    'chat_facade',
]
