"""
上海宇羲伏天智能科技有限公司出品

文件级注释：对话服务层实现
内部逻辑：处理 RAG 流程、Agent 调度及来源追踪
设计模式：外观模式 - 使用ChatOrchestrator简化接口
重构说明：将原有722行代码拆分为多个模块，本文件保留兼容接口
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.chat import ChatRequest, ChatResponse, SourceInfo, SourceDetail, SummaryResponse

# 内部逻辑：导入重构后的组件
from app.services.chat import ChatOrchestrator
from app.services.chat.sources_processor import SourcesProcessor
from app.services.chat.document_formatter import DocumentFormatter

# 内部变量：全局编排器实例（单例模式）
_orchestrator: ChatOrchestrator = None


def get_orchestrator() -> ChatOrchestrator:
    """
    函数级注释：获取对话编排器实例
    内部逻辑：单例模式，确保全局只有一个编排器实例
    设计模式：单例模式 - 延迟初始化
    返回值：ChatOrchestrator - 编排器实例

    注意：这里手动创建依赖，不使用DI容器，以保持向后兼容性
    """
    global _orchestrator
    if _orchestrator is None:
        # 内部逻辑：手动注入依赖，创建编排器实例
        sources_processor = SourcesProcessor()
        document_formatter = DocumentFormatter()
        _orchestrator = ChatOrchestrator(
            sources_processor=sources_processor,
            document_formatter=document_formatter,
            agent_service=None  # 将在需要时创建
        )
    return _orchestrator


class ChatService:
    """
    类级注释：对话服务类（兼容接口）
    内部逻辑：委托给ChatOrchestrator处理具体逻辑
    设计模式：外观模式 - 提供简单接口，隐藏复杂性
    重构说明：原有722行代码简化为约150行，职责更清晰
    """

    @staticmethod
    async def chat_completion(
        db: AsyncSession,
        request: ChatRequest
    ) -> ChatResponse:
        """
        函数级注释：执行智能对话逻辑
        内部逻辑：委托给ChatOrchestrator处理
        参数：
            db: 数据库异步会话
            request: 对话请求对象
        返回值：ChatResponse
        """
        # 内部逻辑：委托给编排器处理
        orchestrator = get_orchestrator()
        return await orchestrator.chat(db, request)

    @staticmethod
    async def stream_chat_completion(
        db: AsyncSession,
        request: ChatRequest
    ):
        """
        函数级注释：异步生成器，执行流式对话逻辑
        内部逻辑：委托给ChatOrchestrator处理
        参数：
            db: 数据库异步会话
            request: 对话请求对象
        生成值：JSON 字符串块，包含 answer 段落或 sources 信息
        """
        # 内部逻辑：委托给编排器处理
        orchestrator = get_orchestrator()
        async for chunk in orchestrator.stream_chat(db, request):
            yield chunk

    @staticmethod
    async def get_sources(
        db: AsyncSession,
        doc_id: Optional[int] = None
    ) -> List[SourceDetail]:
        """
        函数级注释：获取来源详情逻辑
        内部逻辑：委托给ChatOrchestrator处理
        参数：doc_id - 文档唯一标识
        返回值：List[SourceDetail]
        """
        # 内部逻辑：委托给编排器处理
        orchestrator = get_orchestrator()
        return await orchestrator.get_sources(db, doc_id)

    @staticmethod
    async def summarize_document(
        db: AsyncSession,
        doc_id: int
    ) -> SummaryResponse:
        """
        函数级注释：对单个文档进行智能总结
        内部逻辑：委托给ChatOrchestrator处理
        参数：
            db: 数据库异步会话
            doc_id: 文档 ID
        返回值：SummaryResponse
        """
        # 内部逻辑：委托给编排器处理
        orchestrator = get_orchestrator()
        result = await orchestrator.summarize_document(db, doc_id)
        return SummaryResponse(result=result)

    @staticmethod
    async def compare_documents(
        db: AsyncSession,
        doc_ids: List[int]
    ) -> SummaryResponse:
        """
        函数级注释：对多个文档进行对比分析
        内部逻辑：委托给ChatOrchestrator处理
        参数：
            db: 数据库异步会话
            doc_ids: 文档 ID 列表
        返回值：SummaryResponse
        """
        # 内部逻辑：委托给编排器处理
        orchestrator = get_orchestrator()
        result = await orchestrator.compare_documents(db, doc_ids)
        return SummaryResponse(result=result)
