"""
上海宇羲伏天智能科技有限公司出品

文件级注释：对话与问答接口实现
内部逻辑：提供基于知识库的智能对话接口及来源查询接口
设计模式：装饰器模式 - 统一错误处理和日志记录
设计模式：依赖注入模式 - 通过ServiceContainer获取服务实例
"""

from fastapi import APIRouter, Body, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse, SourceDetail, SummaryRequest, ComparisonRequest, SummaryResponse
from app.schemas.response import SuccessResponse, ErrorResponse, ErrorDetail
from app.services.chat_service import ChatService
from app.core.decorators import api_error_handler, log_execution
from app.core.dependencies import get_service, ServiceDepends

# 变量：创建路由实例
router = APIRouter()

@router.post("/completions", response_model=SuccessResponse[ChatResponse])
@log_execution(log_args=True, log_result=False)
async def chat_completions(
    request: ChatRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    # 设计模式：依赖注入模式 - 从容器获取ChatService实例
    chat_service: ChatService = ServiceDepends.chat()
):
    """
    函数级注释：智能问答接口
    内部逻辑：校验请求 -> 判断是否流式 -> 调用相应服务
    设计模式：
        - 装饰器模式 - 统一错误处理和日志记录
        - 依赖注入模式 - 通过ServiceContainer获取服务实例
    参数：
        request: 对话请求参数，包含消息和历史记录
        db: 数据库异步会话，用于追踪来源
        chat_service: 注入的聊天服务实例（通过依赖注入获取）
    返回值：SuccessResponse[ChatResponse] 或 StreamingResponse
    """
    # 内部逻辑：判断是否启用流式返回
    if request.stream:
        # 内部逻辑：流式返回保持原有格式,使用SSE
        # 内部变量：添加关键响应头，禁用Nginx缓冲，支持流式传输
        return StreamingResponse(
            chat_service.stream_chat_completion(db, request),
            media_type="text/event-stream",
            headers={
                # 内部变量：禁用缓存
                "Cache-Control": "no-cache",
                # 内部变量：保持长连接
                "Connection": "keep-alive",
                # 内部变量：告诉Nginx不要使用加速缓冲（关键配置）
                "X-Accel-Buffering": "no"
            }
        )

    # 内部逻辑：将业务逻辑委派给注入的 ChatService
    # 设计模式：依赖注入模式 + 装饰器自动处理异常，无需try-catch
    result = await chat_service.chat_completion(db, request)

    # 内部逻辑：返回统一格式的成功响应
    return SuccessResponse[ChatResponse](
        success=True,
        data=result,
        message="对话完成"
    )

@router.get("/sources", response_model=SuccessResponse[List[SourceDetail]])
async def get_sources_detail(
    doc_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    # 设计模式：依赖注入模式 - 从容器获取ChatService实例
    chat_service: ChatService = ServiceDepends.chat()
):
    """
    函数级注释：查询特定回答的引用来源详情
    内部逻辑：根据文档 ID 查询详细的片段内容和相关度评分
    设计模式：依赖注入模式 - 通过ServiceContainer获取服务实例
    参数：
        doc_id: 可选的文档 ID
        db: 数据库异步会话
        chat_service: 注入的聊天服务实例（通过依赖注入获取）
    返回值：SuccessResponse[List[SourceDetail]] - 统一格式响应
    """
    # 内部变量：调用注入的服务层获取详情
    details = await chat_service.get_sources(db, doc_id)

    # 内部逻辑：返回统一格式的成功响应
    return SuccessResponse[List[SourceDetail]](
        success=True,
        data=details,
        message="查询来源详情成功"
    )

@router.post("/summary", response_model=SuccessResponse[SummaryResponse])
@api_error_handler("文档总结失败")
@log_execution()
async def summarize_document(
    request: SummaryRequest,
    db: AsyncSession = Depends(get_db),
    # 设计模式：依赖注入模式 - 从容器获取ChatService实例
    chat_service: ChatService = ServiceDepends.chat()
):
    """
    函数级注释：文档智能总结接口
    内部逻辑：接收文档 ID -> 提取文本 -> 模型生成总结
    设计模式：
        - 装饰器模式 - 统一错误处理
        - 依赖注入模式 - 通过ServiceContainer获取服务实例
    参数：
        request: 总结请求对象
        db: 数据库异步会话
        chat_service: 注入的聊天服务实例（通过依赖注入获取）
    返回值：SuccessResponse[SummaryResponse] - 统一格式响应
    """
    # 内部逻辑：装饰器自动处理异常，无需try-catch
    result = await chat_service.summarize_document(db, request.doc_id)

    # 内部逻辑：返回统一格式的成功响应
    return SuccessResponse[SummaryResponse](
        success=True,
        data=result,
        message="文档总结成功"
    )

@router.post("/compare", response_model=SuccessResponse[SummaryResponse])
@api_error_handler("文档对比失败")
@log_execution()
async def compare_documents(
    request: ComparisonRequest,
    db: AsyncSession = Depends(get_db),
    # 设计模式：依赖注入模式 - 从容器获取ChatService实例
    chat_service: ChatService = ServiceDepends.chat()
):
    """
    函数级注释：多文档对比分析接口
    内部逻辑：接收多个文档 ID -> 提取文本 -> 模型生成对比分析
    设计模式：
        - 装饰器模式 - 统一错误处理
        - 依赖注入模式 - 通过ServiceContainer获取服务实例
    参数：
        request: 对比请求对象
        db: 数据库异步会话
        chat_service: 注入的聊天服务实例（通过依赖注入获取）
    返回值：SuccessResponse[SummaryResponse] - 统一格式响应
    """
    # 内部逻辑：装饰器自动处理异常，无需try-catch
    result = await chat_service.compare_documents(db, request.doc_ids)

    # 内部逻辑：返回统一格式的成功响应
    return SuccessResponse[SummaryResponse](
        success=True,
        data=result,
        message="文档对比成功"
    )
