"""
上海宇羲伏天智能科技有限公司出品

文件级注释：对话持久化接口实现
内部逻辑：提供会话和消息的CRUD操作，支持流式对话的持久化
"""

from fastapi import APIRouter, Body, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.conversation import (
    CreateConversationRequest,
    UpdateConversationRequest,
    SendMessageRequest,
    ConversationResponse,
    ConversationDetailResponse,
    ConversationListResponse,
    MessageListResponse,
    MessageResponse,
)
from app.schemas.response import SuccessResponse, ErrorResponse, ErrorDetail
from app.services.conversation_service import ConversationService

# 变量：创建路由实例
router = APIRouter()


@router.post("", response_model=SuccessResponse[ConversationResponse])
async def create_conversation(
    request: CreateConversationRequest = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    函数级注释：创建新会话
    内部逻辑：验证请求 -> 调用服务层创建会话 -> 返回会话信息
    参数：
        request: 创建会话请求
        db: 数据库会话
    返回值：SuccessResponse[ConversationResponse]
    """
    try:
        result = await ConversationService.create_conversation(db, request)
        return SuccessResponse[ConversationResponse](
            success=True,
            data=result,
            message="会话创建成功"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                success=False,
                error=ErrorDetail(
                    code=500,
                    message="创建会话失败",
                    details=str(e)
                )
            ).model_dump()
        )


@router.get("", response_model=SuccessResponse[ConversationListResponse])
async def list_conversations(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: AsyncSession = Depends(get_db)
):
    """
    函数级注释：获取会话列表
    内部逻辑：查询会话 -> 按更新时间倒序 -> 返回列表
    参数：
        skip: 分页跳过
        limit: 分页限制
        db: 数据库会话
    返回值：SuccessResponse[ConversationListResponse]
    """
    try:
        result = await ConversationService.list_conversations(
            db,
            skip=skip,
            limit=limit
        )
        return SuccessResponse[ConversationListResponse](
            success=True,
            data=result,
            message="查询会话列表成功"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                success=False,
                error=ErrorDetail(
                    code=500,
                    message="查询会话列表失败",
                    details=str(e)
                )
            ).model_dump()
        )


@router.get("/{conversation_id}", response_model=SuccessResponse[ConversationDetailResponse])
async def get_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    函数级注释：获取会话详情（包含消息列表）
    内部逻辑：查询会话 -> 查询消息 -> 组装返回
    参数：
        conversation_id: 会话ID
        db: 数据库会话
    返回值：SuccessResponse[ConversationDetailResponse]
    """
    try:
        result = await ConversationService.get_conversation_detail(db, conversation_id)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(
                    success=False,
                    error=ErrorDetail(
                        code=404,
                        message="会话不存在"
                    )
                ).model_dump()
            )
        return SuccessResponse[ConversationDetailResponse](
            success=True,
            data=result,
            message="查询会话详情成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                success=False,
                error=ErrorDetail(
                    code=500,
                    message="查询会话详情失败",
                    details=str(e)
                )
            ).model_dump()
        )


@router.put("/{conversation_id}", response_model=SuccessResponse[ConversationResponse])
async def update_conversation(
    conversation_id: int,
    request: UpdateConversationRequest = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    函数级注释：更新会话信息
    内部逻辑：验证会话存在 -> 更新字段 -> 返回更新后信息
    参数：
        conversation_id: 会话ID
        request: 更新请求
        db: 数据库会话
    返回值：SuccessResponse[ConversationResponse]
    """
    try:
        result = await ConversationService.update_conversation(db, conversation_id, request)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(
                    success=False,
                    error=ErrorDetail(
                        code=404,
                        message="会话不存在"
                    )
                ).model_dump()
            )
        return SuccessResponse[ConversationResponse](
            success=True,
            data=result,
            message="会话更新成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                success=False,
                error=ErrorDetail(
                    code=500,
                    message="更新会话失败",
                    details=str(e)
                )
            ).model_dump()
        )


@router.delete("/{conversation_id}", response_model=SuccessResponse[dict])
async def delete_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    函数级注释：删除会话（物理删除）
    内部逻辑：物理删除会话及关联数据
    参数：
        conversation_id: 会话ID
        db: 数据库会话
    返回值：SuccessResponse[dict]
    """
    try:
        success = await ConversationService.delete_conversation(db, conversation_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(
                    success=False,
                    error=ErrorDetail(
                        code=404,
                        message="会话不存在"
                    )
                ).model_dump()
            )
        return SuccessResponse[dict](
            success=True,
            data={"deleted": True},
            message="会话删除成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                success=False,
                error=ErrorDetail(
                    code=500,
                    message="删除会话失败",
                    details=str(e)
                )
            ).model_dump()
        )


@router.post("/{conversation_id}/messages", response_model=SuccessResponse[MessageResponse])
async def send_message(
    conversation_id: int,
    request: SendMessageRequest = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    函数级注释：发送消息（非流式）
    内部逻辑：保存用户消息 -> 调用LLM -> 保存助手回复 -> 更新会话
    参数：
        conversation_id: 会话ID
        request: 消息请求
        db: 数据库会话
    返回值：SuccessResponse[MessageResponse]
    """
    try:
        # Guard Clause：流式请求应使用stream端点
        if request.stream:
            raise HTTPException(
                status_code=400,
                detail="流式请求请使用 /stream 端点"
            )

        result = await ConversationService.send_message(db, conversation_id, request)
        return SuccessResponse[MessageResponse](
            success=True,
            data=result,
            message="消息发送成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                success=False,
                error=ErrorDetail(
                    code=500,
                    message="发送消息失败",
                    details=str(e)
                )
            ).model_dump()
        )


@router.post("/{conversation_id}/stream", response_class=StreamingResponse)
async def send_message_stream(
    conversation_id: int,
    request: SendMessageRequest = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    函数级注释：发送消息（流式）
    内部逻辑：保存用户消息 -> 流式生成 -> 逐步yield -> 完成后保存
    参数：
        conversation_id: 会话ID
        request: 消息请求
        db: 数据库会话
    返回值：StreamingResponse
    """
    return StreamingResponse(
        ConversationService.send_message_stream(db, conversation_id, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/{conversation_id}/messages", response_model=SuccessResponse[MessageListResponse])
async def get_messages(
    conversation_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    函数级注释：获取会话消息列表
    内部逻辑：分页查询消息 -> 返回列表
    参数：
        conversation_id: 会话ID
        skip: 分页跳过
        limit: 分页限制
        db: 数据库会话
    返回值：SuccessResponse[MessageListResponse]
    """
    try:
        result = await ConversationService.get_messages(db, conversation_id, skip, limit)
        return SuccessResponse[MessageListResponse](
            success=True,
            data=result,
            message="查询消息列表成功"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                success=False,
                error=ErrorDetail(
                    code=500,
                    message="查询消息列表失败",
                    details=str(e)
                )
            ).model_dump()
        )
