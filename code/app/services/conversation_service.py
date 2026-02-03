"""
上海宇羲伏天智能科技有限公司出品

文件级注释：对话持久化服务层实现
内部逻辑：处理会话和消息的CRUD操作，集成现有ChatService，处理Token统计
设计原则：复用现有ChatService，遵循SOLID原则，使用Guard Clauses模式
"""

import json
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, desc, func
from fastapi import HTTPException
from loguru import logger
from datetime import datetime

from app.schemas.conversation import (
    CreateConversationRequest,
    UpdateConversationRequest,
    SendMessageRequest,
    ConversationResponse,
    ConversationDetailResponse,
    ConversationListResponse,
    MessageListResponse,
    MessageResponse,
    MessageRole as SchemaMessageRole,
)
from app.models.conversation import (
    Conversation,
    Message,
    MessageSource,
    TokenUsage,
    MessageRole as DBMessageRole,
)
from app.models.models import Document
from app.services.chat_service import ChatService
from app.schemas.chat import ChatRequest
from app.core.config import settings
from app.core.token_pricing import calculate_token_cost, TokenPricingCalculator
from app.utils.timezone_helper import get_local_time


class ConversationService:
    """
    类级注释：对话服务类，处理会话和消息的持久化逻辑
    内部逻辑：复用ChatService处理RAG，专注于数据持久化和Token统计
    """

    @staticmethod
    async def create_conversation(
        db: AsyncSession,
        request: CreateConversationRequest
    ) -> ConversationResponse:
        """
        函数级注释：创建新会话
        内部逻辑：创建Conversation对象 -> 保存到数据库 -> 返回响应
        参数：
            db: 数据库会话
            request: 创建请求
        返回值：ConversationResponse
        """
        # 内部变量：创建ORM对象
        conversation = Conversation(
            title=request.title or "新对话",
            model_name=request.model_name or settings.CHAT_MODEL,
            use_agent=1 if request.use_agent else 0,
            message_count=0,
            total_tokens=0,
            total_cost=0
        )

        # 内部逻辑：保存到数据库
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)

        # 内部逻辑：转换为响应模型
        return ConversationService._to_conversation_response(conversation)

    @staticmethod
    async def list_conversations(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20
    ) -> ConversationListResponse:
        """
        函数级注释：获取会话列表
        内部逻辑：构建查询 -> 按更新时间倒序 -> 分页 -> 转换响应
        参数：
            db: 数据库会话
            skip: 分页跳过
            limit: 分页限制
        返回值：ConversationListResponse
        """
        # 内部逻辑：获取总数
        count_result = await db.execute(
            select(func.count(Conversation.id))
        )
        total = count_result.scalar()

        # 内部逻辑：构建查询并排序
        query = select(Conversation).order_by(desc(Conversation.updated_at))
        query = query.offset(skip).limit(limit)

        # 内部逻辑：执行查询
        result = await db.execute(query)
        conversations = result.scalars().all()

        # 内部逻辑：转换并附加最后一条消息
        response_list = []
        for conv in conversations:
            response = ConversationService._to_conversation_response(conv)

            # 内部逻辑：获取最后一条助手消息作为预览
            last_msg_query = select(Message.content).where(
                and_(
                    Message.conversation_id == conv.id,
                    Message.role == DBMessageRole.ASSISTANT
                )
            ).order_by(desc(Message.created_at)).limit(1)
            last_msg_result = await db.execute(last_msg_query)
            last_msg = last_msg_result.scalar()
            response.last_message = last_msg[:100] if last_msg else None

            response_list.append(response)

        return ConversationListResponse(
            conversations=response_list,
            total=total,
            has_more=skip + limit < total
        )

    @staticmethod
    async def get_conversation_detail(
        db: AsyncSession,
        conversation_id: int
    ) -> Optional[ConversationDetailResponse]:
        """
        函数级注释：获取会话详情（包含消息列表）
        内部逻辑：查询会话 -> 查询消息 -> 查询来源 -> 组装返回
        参数：
            db: 数据库会话
            conversation_id: 会话ID
        返回值：ConversationDetailResponse或None
        """
        # 内部逻辑：查询会话
        conv_result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = conv_result.scalar_one_or_none()

        # Guard Clause：会话不存在
        if conversation is None:
            return None

        # 内部逻辑：查询消息列表
        msg_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        messages = msg_result.scalars().all()

        # 内部逻辑：转换消息为响应模型
        message_responses = []
        for msg in messages:
            # 内部逻辑：查询来源引用
            source_result = await db.execute(
                select(MessageSource)
                .where(MessageSource.message_id == msg.id)
                .order_by(MessageSource.position.asc())
            )
            sources = source_result.scalars().all()

            message_responses.append(ConversationService._to_message_response(msg, list(sources)))

        # 内部逻辑：组装详情响应
        return ConversationDetailResponse(
            conversation=ConversationService._to_conversation_response(conversation),
            messages=message_responses
        )

    @staticmethod
    async def update_conversation(
        db: AsyncSession,
        conversation_id: int,
        request: UpdateConversationRequest
    ) -> Optional[ConversationResponse]:
        """
        函数级注释：更新会话信息
        内部逻辑：查询会话 -> 更新字段 -> 提交
        参数：
            db: 数据库会话
            conversation_id: 会话ID
            request: 更新请求
        返回值：ConversationResponse或None
        """
        # 内部逻辑：查询会话
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()

        # Guard Clause：会话不存在
        if conversation is None:
            return None

        # 内部逻辑：更新字段
        if request.title:
            conversation.title = request.title

        conversation.updated_at = get_local_time()

        # 内部逻辑：提交
        await db.commit()
        await db.refresh(conversation)

        return ConversationService._to_conversation_response(conversation)

    @staticmethod
    async def delete_conversation(
        db: AsyncSession,
        conversation_id: int
    ) -> bool:
        """
        函数级注释：删除会话（物理删除）
        内部逻辑：直接删除，通过CASCADE级联删除关联数据
        参数：
            db: 数据库会话
            conversation_id: 会话ID
        返回值：是否成功
        """
        # 内部逻辑：查询会话
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()

        # Guard Clause：会话不存在
        if conversation is None:
            return False

        # 内部逻辑：物理删除（级联删除关联数据）
        await db.delete(conversation)
        await db.commit()

        logger.info(f"会话 {conversation_id} 已物理删除")
        return True

    @staticmethod
    async def get_messages(
        db: AsyncSession,
        conversation_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> MessageListResponse:
        """
        函数级注释：获取消息列表
        内部逻辑：分页查询消息 -> 查询来源 -> 组装返回
        参数：
            db: 数据库会话
            conversation_id: 会话ID
            skip: 分页跳过
            limit: 分页限制
        返回值：MessageListResponse
        """
        # 内部逻辑：获取总数
        count_result = await db.execute(
            select(func.count(Message.id))
            .where(Message.conversation_id == conversation_id)
        )
        total = count_result.scalar()

        # 内部逻辑：查询消息
        msg_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        messages = msg_result.scalars().all()

        # 内部逻辑：转换并附加来源
        message_responses = []
        for msg in messages:
            source_result = await db.execute(
                select(MessageSource)
                .where(MessageSource.message_id == msg.id)
                .order_by(MessageSource.position.asc())
            )
            sources = source_result.scalars().all()
            message_responses.append(ConversationService._to_message_response(msg, list(sources)))

        return MessageListResponse(
            messages=message_responses,
            total=total,
            has_more=skip + limit < total
        )

    @staticmethod
    async def send_message(
        db: AsyncSession,
        conversation_id: int,
        request: SendMessageRequest
    ) -> MessageResponse:
        """
        函数级注释：发送消息（非流式）
        内部逻辑：保存用户消息 -> 调用ChatService -> 保存助手回复 -> 保存来源 -> 统计Token
        参数：
            db: 数据库会话
            conversation_id: 会话ID
            request: 消息请求
        返回值：MessageResponse
        """
        # 内部逻辑：验证会话存在
        conv_result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = conv_result.scalar_one_or_none()
        if conversation is None:
            raise HTTPException(status_code=404, detail="会话不存在")

        # 内部逻辑：保存用户消息
        user_message = Message(
            conversation_id=conversation_id,
            role=DBMessageRole.USER,
            content=request.content,
            streaming_state="idle",
            tokens_count=0
        )
        db.add(user_message)
        await db.flush()

        # 内部逻辑：获取历史消息作为上下文
        history_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(20)  # 内部变量：限制历史消息数量
        )
        history_messages = history_result.scalars().all()

        # 内部逻辑：转换为ChatRequest格式
        chat_history = [
            {"role": "user" if msg.role == DBMessageRole.USER else "assistant", "content": msg.content}
            for msg in history_messages[:-1]  # 内部逻辑：排除刚添加的用户消息
        ]

        # 内部逻辑：调用ChatService获取回复
        chat_request = ChatRequest(
            message=request.content,
            history=chat_history,
            use_agent=request.use_agent or conversation.use_agent == 1,
            stream=False
        )
        chat_response = await ChatService.chat_completion(db, chat_request)

        # 内部逻辑：估算并保存Token统计
        model_name = conversation.model_name or settings.CHAT_MODEL
        prompt_tokens = TokenPricingCalculator.estimate_tokens(request.content)
        completion_tokens = TokenPricingCalculator.estimate_tokens(chat_response.answer)
        cost_info = calculate_token_cost(model_name, prompt_tokens, completion_tokens)

        # 内部逻辑：保存助手回复
        assistant_message = Message(
            conversation_id=conversation_id,
            role=DBMessageRole.ASSISTANT,
            content=chat_response.answer,
            streaming_state="completed",
            tokens_count=cost_info["total_tokens"]
        )
        db.add(assistant_message)
        await db.flush()

        # 内部逻辑：保存Token使用记录
        token_usage = TokenUsage(
            conversation_id=conversation_id,
            message_id=assistant_message.id,
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=cost_info["total_tokens"],
            prompt_cost=cost_info["prompt_cost"],
            completion_cost=cost_info["completion_cost"],
            total_cost=cost_info["total_cost"]
        )
        db.add(token_usage)

        # 内部逻辑：保存来源引用（添加文档存在性验证）
        # 内部逻辑：收集所有 doc_id 进行批量验证
        source_doc_ids = [source.doc_id for source in chat_response.sources if source.doc_id]

        # 内部逻辑：批量验证文档是否存在
        valid_doc_ids = set()
        if source_doc_ids:
            from app.models.models import Document
            doc_result = await db.execute(
                select(Document.id).where(Document.id.in_(source_doc_ids))
            )
            valid_doc_ids = {row[0] for row in doc_result.all()}

        # 内部逻辑：保存来源引用（将无效的 doc_id 设为 None）
        sources = []
        for idx, source in enumerate(chat_response.sources):
            doc_id = source.doc_id
            # 内部逻辑：验证 doc_id 是否有效，无效则设为 None
            if doc_id and doc_id not in valid_doc_ids:
                doc_id = None
                logger.warning(f"文档 ID {source.doc_id} 不存在，将 document_id 设为 None")

            msg_source = MessageSource(
                message_id=assistant_message.id,
                document_id=doc_id,
                file_name=source.file_name,
                text_segment=source.text_segment,
                score=int(source.score * 100) if source.score else None,
                position=idx
            )
            db.add(msg_source)
            sources.append(msg_source)

        # 内部逻辑：更新会话信息
        conversation.message_count += 2  # 内部变量：用户消息 + 助手消息
        conversation.total_tokens += cost_info["total_tokens"]
        conversation.total_cost += cost_info["total_cost"]
        conversation.updated_at = get_local_time()

        # 内部逻辑：自动生成标题（如果是第一条消息）
        if conversation.message_count == 2:
            conversation.title = ConversationService._generate_title(request.content)

        # 内部逻辑：提交所有更改
        await db.commit()
        await db.refresh(assistant_message)

        return ConversationService._to_message_response(assistant_message, sources)

    @staticmethod
    async def send_message_stream(
        db: AsyncSession,
        conversation_id: int,
        request: SendMessageRequest
    ):
        """
        函数级注释：发送消息（流式）
        内部逻辑：保存用户消息 -> 流式生成 -> 逐步yield -> 完成后保存
        参数：
            db: 数据库会话
            conversation_id: 会话ID
            request: 消息请求
        生成值：SSE格式的JSON字符串
        """
        try:
            # 内部逻辑：验证会话存在
            conv_result = await db.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = conv_result.scalar_one_or_none()
            if conversation is None:
                yield f"data: {json.dumps({'error': '会话不存在'}, ensure_ascii=False)}\n\n"
                return

            # 内部逻辑：保存用户消息
            user_message = Message(
                conversation_id=conversation_id,
                role=DBMessageRole.USER,
                content=request.content,
                streaming_state="idle",
                tokens_count=0
            )
            db.add(user_message)
            await db.commit()

            # 内部逻辑：获取历史消息
            history_result = await db.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.asc())
                .limit(20)
            )
            history_messages = history_result.scalars().all()

            chat_history = [
                {"role": "user" if msg.role == DBMessageRole.USER else "assistant", "content": msg.content}
                for msg in history_messages[:-1]
            ]

            # 内部逻辑：调用ChatService流式接口
            chat_request = ChatRequest(
                message=request.content,
                history=chat_history,
                use_agent=request.use_agent or conversation.use_agent == 1,
                stream=True
            )

            # 内部变量：累积助手回复内容
            assistant_content = ""
            sources = []

            # 内部逻辑：处理流式响应
            async for chunk in ChatService.stream_chat_completion(db, chat_request):
                # 内部逻辑：直接转发SSE数据
                yield chunk

                # 内部逻辑：解析数据用于持久化
                if chunk.startswith("data: "):
                    data_str = chunk[6:]
                    try:
                        data = json.loads(data_str)
                        if data.get("answer"):
                            assistant_content += data["answer"]
                        if data.get("sources"):
                            sources = data["sources"]
                    except json.JSONDecodeError:
                        pass

            # 内部逻辑：流式结束后保存助手消息
            if assistant_content:
                # 内部逻辑：估算Token
                model_name = conversation.model_name or settings.CHAT_MODEL
                prompt_tokens = TokenPricingCalculator.estimate_tokens(request.content)
                completion_tokens = TokenPricingCalculator.estimate_tokens(assistant_content)
                cost_info = calculate_token_cost(model_name, prompt_tokens, completion_tokens)

                assistant_message = Message(
                    conversation_id=conversation_id,
                    role=DBMessageRole.ASSISTANT,
                    content=assistant_content,
                    streaming_state="completed",
                    tokens_count=cost_info["total_tokens"]
                )
                db.add(assistant_message)
                await db.flush()

                # 内部逻辑：保存Token使用记录
                token_usage = TokenUsage(
                    conversation_id=conversation_id,
                    message_id=assistant_message.id,
                    model_name=model_name,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=cost_info["total_tokens"],
                    prompt_cost=cost_info["prompt_cost"],
                    completion_cost=cost_info["completion_cost"],
                    total_cost=cost_info["total_cost"]
                )
                db.add(token_usage)

                # 内部逻辑：保存来源引用（添加文档存在性验证）
                # 内部逻辑：收集所有 doc_id 进行批量验证
                source_doc_ids = [source.get("doc_id") for source in sources if source.get("doc_id")]

                # 内部逻辑：批量验证文档是否存在
                valid_doc_ids = set()
                if source_doc_ids:
                    from app.models.models import Document
                    doc_result = await db.execute(
                        select(Document.id).where(Document.id.in_(source_doc_ids))
                    )
                    valid_doc_ids = {row[0] for row in doc_result.all()}

                # 内部逻辑：保存来源引用（将无效的 doc_id 设为 None）
                for idx, source in enumerate(sources):
                    doc_id = source.get("doc_id")
                    # 内部逻辑：验证 doc_id 是否有效，无效则设为 None
                    if doc_id and doc_id not in valid_doc_ids:
                        doc_id = None
                        logger.warning(f"文档 ID {source.get('doc_id')} 不存在，将 document_id 设为 None")

                    msg_source = MessageSource(
                        message_id=assistant_message.id,
                        document_id=doc_id,
                        file_name=source.get("file_name", ""),
                        text_segment=source.get("text_segment", ""),
                        score=int(source.get("score", 0) * 100) if source.get("score") else None,
                        position=idx
                    )
                    db.add(msg_source)

                # 内部逻辑：更新会话
                conversation.message_count += 2
                conversation.total_tokens += cost_info["total_tokens"]
                conversation.total_cost += cost_info["total_cost"]
                conversation.updated_at = get_local_time()

                # 内部逻辑：自动生成标题
                if conversation.message_count == 2:
                    conversation.title = ConversationService._generate_title(request.content)

                await db.commit()

        except Exception as e:
            """
            异常处理：捕获流式发送消息过程中的所有异常
            内部逻辑：记录详细错误信息和堆栈跟踪，便于问题定位
            """
            import traceback
            logger.error(f"流式发送消息异常: {str(e)}")
            logger.error(f"异常类型: {type(e).__name__}")
            logger.error(f"异常堆栈: {traceback.format_exc()}")
            yield f"data: {json.dumps({'error': str(e) or '未知错误'}, ensure_ascii=False)}\n\n"
        finally:
            # 内部逻辑：确保发送完成标记
            yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"

    @staticmethod
    def _to_conversation_response(conversation: Conversation) -> ConversationResponse:
        """
        函数级注释：将ORM对象转换为响应模型
        内部逻辑：映射字段
        参数：
            conversation: Conversation ORM对象
        返回值：ConversationResponse
        """
        return ConversationResponse(
            id=conversation.id,
            title=conversation.title,
            model_name=conversation.model_name,
            use_agent=conversation.use_agent == 1,
            total_tokens=conversation.total_tokens,
            total_cost=conversation.total_cost,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=conversation.message_count,
            last_message=None
        )

    @staticmethod
    def _to_message_response(message: Message, sources: List[MessageSource] = None) -> MessageResponse:
        """
        函数级注释：将ORM对象转换为响应模型
        内部逻辑：映射字段
        参数：
            message: Message ORM对象
            sources: 来源列表
        返回值：MessageResponse
        """
        from app.schemas.conversation import MessageSourceResponse

        source_responses = []
        if sources:
            for source in sources:
                source_responses.append(MessageSourceResponse(
                    id=source.id,
                    document_id=source.document_id,
                    chunk_id=source.chunk_id,
                    file_name=source.file_name,
                    text_segment=source.text_segment,
                    score=source.score,
                    position=source.position
                ))

        return MessageResponse(
            id=message.id,
            conversation_id=message.conversation_id,
            role=SchemaMessageRole(message.role.value),
            content=message.content,
            streaming_state=message.streaming_state,
            tokens_count=message.tokens_count,
            created_at=message.created_at,
            sources=source_responses
        )

    @staticmethod
    def _generate_title(content: str, max_length: int = 30) -> str:
        """
        函数级注释：根据消息内容生成会话标题
        内部逻辑：截取前N个字符，添加省略号
        参数：
            content: 消息内容
            max_length: 最大长度
        返回值：生成的标题
        """
        # 内部逻辑：去除换行和多余空格
        cleaned = content.strip().replace("\n", " ")

        # 内部逻辑：截断
        if len(cleaned) <= max_length:
            return cleaned
        return cleaned[:max_length] + "..."
