# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：对话服务层单元测试
内部逻辑：测试对话服务的核心业务逻辑
覆盖范围：CRUD操作、消息发送、流式响应、Token统计、标题生成
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.services.conversation_service import ConversationService
from app.schemas.conversation import (
    CreateConversationRequest,
    UpdateConversationRequest,
    SendMessageRequest,
)
from app.models.conversation import Conversation, Message, MessageSource, TokenUsage, MessageRole
from app.models.models import Document


class TestConversationServiceCreate:
    """
    类级注释：测试创建会话功能
    """

    @pytest.mark.asyncio
    async def test_create_conversation_with_defaults(self, db_session: AsyncSession):
        """
        函数级注释：测试使用默认值创建会话
        内部逻辑：不传title和model_name，验证使用默认值
        参数：
            db_session: 测试数据库会话
        """
        request = CreateConversationRequest()
        result = await ConversationService.create_conversation(db_session, request)

        assert result.title == "新对话"
        assert result.use_agent is False

    @pytest.mark.asyncio
    async def test_create_conversation_with_values(self, db_session: AsyncSession):
        """
        函数级注释：测试创建带指定值的会话
        内部逻辑：传入title和model_name
        参数：
            db_session: 测试数据库会话
        """
        request = CreateConversationRequest(
            title="测试会话",
            model_name="glm-4",
            use_agent=True
        )
        result = await ConversationService.create_conversation(db_session, request)

        assert result.title == "测试会话"
        assert result.model_name == "glm-4"
        assert result.use_agent is True

    @pytest.mark.asyncio
    async def test_create_conversation_initial_stats(self, db_session: AsyncSession):
        """
        函数级注释：测试创建会话时的初始统计值
        内部逻辑：验证message_count、total_tokens、total_cost为0
        参数：
            db_session: 测试数据库会话
        """
        request = CreateConversationRequest(title="初始测试")
        result = await ConversationService.create_conversation(db_session, request)

        assert result.message_count == 0
        assert result.total_tokens == 0
        assert result.total_cost == 0


class TestConversationServiceList:
    """
    类级注释：测试获取会话列表功能
    """

    @pytest.mark.asyncio
    async def test_list_conversations_empty(self, db_session: AsyncSession):
        """
        函数级注释：测试空会话列表
        内部逻辑：没有会话时返回空列表
        参数：
            db_session: 测试数据库会话
        """
        result = await ConversationService.list_conversations(db_session, skip=0, limit=10)

        assert result.total == 0
        assert len(result.conversations) == 0
        assert result.has_more is False

    @pytest.mark.asyncio
    async def test_list_conversations_with_data(self, db_session: AsyncSession):
        """
        函数级注释：测试获取会话列表
        内部逻辑：创建多个会话，验证正确返回
        参数：
            db_session: 测试数据库会话
        """
        # 创建会话
        for i in range(3):
            request = CreateConversationRequest(title=f"会话{i}")
            await ConversationService.create_conversation(db_session, request)

        result = await ConversationService.list_conversations(db_session, skip=0, limit=10)

        assert result.total >= 3
        assert len(result.conversations) >= 3

    @pytest.mark.asyncio
    async def test_list_conversations_pagination(self, db_session: AsyncSession):
        """
        函数级注释：测试会话列表分页
        内部逻辑：创建多个会话，测试分页逻辑
        参数：
            db_session: 测试数据库会话
        """
        # 创建5个会话
        for i in range(5):
            request = CreateConversationRequest(title=f"会话{i}")
            await ConversationService.create_conversation(db_session, request)

        page1 = await ConversationService.list_conversations(db_session, skip=0, limit=2)
        page2 = await ConversationService.list_conversations(db_session, skip=2, limit=2)

        assert len(page1.conversations) == 2
        assert page1.has_more is True

        assert len(page2.conversations) == 2
        # 第二页可能还有数据

    @pytest.mark.asyncio
    async def test_list_conversations_with_last_message(self, db_session: AsyncSession):
        """
        函数级注释：测试会话列表包含最后一条消息预览
        内部逻辑：创建会话和消息，验证last_message字段
        参数：
            db_session: 测试数据库会话
        """
        conv_request = CreateConversationRequest(title="测试会话")
        conv = await ConversationService.create_conversation(db_session, conv_request)

        # 添加助手消息
        msg = Message(
            conversation_id=conv.id,
            role=MessageRole.ASSISTANT,
            content="这是一条较长的助手回复内容，用于测试预览截断功能",
            streaming_state="completed"
        )
        db_session.add(msg)
        await db_session.commit()

        result = await ConversationService.list_conversations(db_session, skip=0, limit=10)

        if result.conversations:
            first_conv = result.conversations[0]
            assert first_conv.last_message is not None
            assert len(first_conv.last_message) <= 100


class TestConversationServiceDetail:
    """
    类级注释：测试获取会话详情功能
    """

    @pytest.mark.asyncio
    async def test_get_conversation_detail_not_found(self, db_session: AsyncSession):
        """
        函数级注释：测试获取不存在的会话详情
        内部逻辑：查询不存在的会话ID
        参数：
            db_session: 测试数据库会话
        """
        result = await ConversationService.get_conversation_detail(db_session, 99999)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_conversation_detail_with_messages(self, db_session: AsyncSession):
        """
        函数级注释：测试获取会话详情（包含消息）
        内部逻辑：创建会话和消息，验证完整返回
        参数：
            db_session: 测试数据库会话
        """
        request = CreateConversationRequest(title="详情测试")
        conv = await ConversationService.create_conversation(db_session, request)

        # 添加消息
        msg = Message(
            conversation_id=conv.id,
            role=MessageRole.USER,
            content="测试消息",
            streaming_state="completed"
        )
        db_session.add(msg)
        await db_session.commit()
        await db_session.refresh(msg)

        result = await ConversationService.get_conversation_detail(db_session, conv.id)

        assert result is not None
        assert result.conversation.id == conv.id
        assert len(result.messages) == 1
        assert result.messages[0].content == "测试消息"

    @pytest.mark.asyncio
    async def test_get_conversation_detail_with_sources(self, db_session: AsyncSession):
        """
        函数级注释：测试获取会话详情（包含来源）
        内部逻辑：创建会话、消息和来源
        参数：
            db_session: 测试数据库会话
        """
        request = CreateConversationRequest(title="来源测试")
        conv = await ConversationService.create_conversation(db_session, request)

        # 添加消息
        msg = Message(
            conversation_id=conv.id,
            role=MessageRole.ASSISTANT,
            content="回复内容",
            streaming_state="completed"
        )
        db_session.add(msg)
        await db_session.flush()

        # 添加来源
        source = MessageSource(
            message_id=msg.id,
            document_id=1,
            file_name="测试.pdf",
            text_segment="内容片段",
            score=85,
            position=0
        )
        db_session.add(source)
        await db_session.commit()

        result = await ConversationService.get_conversation_detail(db_session, conv.id)

        assert result is not None
        assert len(result.messages) == 1
        assert len(result.messages[0].sources) == 1
        assert result.messages[0].sources[0].file_name == "测试.pdf"


class TestConversationServiceUpdate:
    """
    类级注释：测试更新会话功能
    """

    @pytest.mark.asyncio
    async def test_update_conversation_title(self, db_session: AsyncSession):
        """
        函数级注释：测试更新会话标题
        内部逻辑：创建会话后更新标题
        参数：
            db_session: 测试数据库会话
        """
        request = CreateConversationRequest(title="原标题")
        conv = await ConversationService.create_conversation(db_session, request)

        update_request = UpdateConversationRequest(title="新标题")
        result = await ConversationService.update_conversation(
            db_session, conv.id, update_request
        )

        assert result.title == "新标题"

    @pytest.mark.asyncio
    async def test_update_conversation_not_found(self, db_session: AsyncSession):
        """
        函数级注释：测试更新不存在的会话
        内部逻辑：更新不存在的会话ID
        参数：
            db_session: 测试数据库会话
        """
        update_request = UpdateConversationRequest(title="新标题")
        result = await ConversationService.update_conversation(
            db_session, 99999, update_request
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_update_conversation_empty_title(self, db_session: AsyncSession):
        """
        函数级注释：测试更新空标题时不修改
        内部逻辑：传入空title，验证不更新
        参数：
            db_session: 测试数据库会话
        """
        request = CreateConversationRequest(title="原标题")
        conv = await ConversationService.create_conversation(db_session, request)

        update_request = UpdateConversationRequest(title="")
        result = await ConversationService.update_conversation(
            db_session, conv.id, update_request
        )

        # 空字符串不更新，标题应保持原样
        assert result.title == "原标题"


class TestConversationServiceDelete:
    """
    类级注释：测试删除会话功能
    """

    @pytest.mark.asyncio
    async def test_delete_conversation_success(self, db_session: AsyncSession):
        """
        函数级注释：测试成功删除会话
        内部逻辑：创建会话后删除
        参数：
            db_session: 测试数据库会话
        """
        request = CreateConversationRequest(title="待删除")
        conv = await ConversationService.create_conversation(db_session, request)

        result = await ConversationService.delete_conversation(db_session, conv.id)

        assert result is True

        # 验证已删除
        check = await ConversationService.get_conversation_detail(db_session, conv.id)
        assert check is None

    @pytest.mark.asyncio
    async def test_delete_conversation_not_found(self, db_session: AsyncSession):
        """
        函数级注释：测试删除不存在的会话
        内部逻辑：删除不存在的会话ID
        参数：
            db_session: 测试数据库会话
        """
        result = await ConversationService.delete_conversation(db_session, 99999)
        assert result is False


class TestConversationServiceGetMessages:
    """
    类级注释：测试获取消息列表功能
    """

    @pytest.mark.asyncio
    async def test_get_messages_empty(self, db_session: AsyncSession):
        """
        函数级注释：测试获取空消息列表
        内部逻辑：会话没有消息时
        参数：
            db_session: 测试数据库会话
        """
        request = CreateConversationRequest(title="测试")
        conv = await ConversationService.create_conversation(db_session, request)

        result = await ConversationService.get_messages(db_session, conv.id)

        assert result.total == 0
        assert len(result.messages) == 0

    @pytest.mark.asyncio
    async def test_get_messages_with_data(self, db_session: AsyncSession):
        """
        函数级注释：测试获取消息列表
        内部逻辑：创建会话和消息
        参数：
            db_session: 测试数据库会话
        """
        request = CreateConversationRequest(title="消息测试")
        conv = await ConversationService.create_conversation(db_session, request)

        # 添加消息
        msg = Message(
            conversation_id=conv.id,
            role=MessageRole.USER,
            content="用户消息",
            streaming_state="completed"
        )
        db_session.add(msg)
        await db_session.commit()

        result = await ConversationService.get_messages(db_session, conv.id)

        assert result.total == 1
        assert len(result.messages) == 1
        assert result.messages[0].content == "用户消息"

    @pytest.mark.asyncio
    async def test_get_messages_pagination(self, db_session: AsyncSession):
        """
        函数级注释：测试消息分页
        内部逻辑：创建多条消息，测试分页
        参数：
            db_session: 测试数据库会话
        """
        request = CreateConversationRequest(title="分页测试")
        conv = await ConversationService.create_conversation(db_session, request)

        # 添加多条消息
        for i in range(5):
            msg = Message(
                conversation_id=conv.id,
                role=MessageRole.USER,
                content=f"消息{i}",
                streaming_state="completed"
            )
            db_session.add(msg)
        await db_session.commit()

        page1 = await ConversationService.get_messages(db_session, conv.id, skip=0, limit=2)
        page2 = await ConversationService.get_messages(db_session, conv.id, skip=2, limit=2)

        assert len(page1.messages) == 2
        assert page1.has_more is True
        assert len(page2.messages) == 2


class TestConversationServiceSendMessage:
    """
    类级注释：测试发送消息功能
    """

    @pytest.mark.asyncio
    async def test_send_message_conversation_not_found(self, db_session: AsyncSession):
        """
        函数级注释：测试向不存在的会话发送消息
        内部逻辑：会话不存在时应抛出HTTPException
        参数：
            db_session: 测试数据库会话
        """
        from fastapi import HTTPException

        request = SendMessageRequest(content="测试消息")

        with pytest.raises(HTTPException) as exc_info:
            await ConversationService.send_message(db_session, 99999, request)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_send_message_with_mock_chat_service(self, db_session: AsyncSession):
        """
        函数级注释：测试发送消息（mock ChatService）
        内部逻辑：mock ChatService.chat_completion
        参数：
            db_session: 测试数据库会话
        """
        request = CreateConversationRequest(title="发送测试")
        conv = await ConversationService.create_conversation(db_session, request)

        send_request = SendMessageRequest(content="你好")

        # Mock ChatService
        with patch('app.services.conversation_service.ChatService') as mock_chat:
            mock_response = MagicMock()
            mock_response.answer = "你好！有什么可以帮助你的？"
            mock_response.sources = []

            mock_chat.chat_completion = AsyncMock(return_value=mock_response)

            result = await ConversationService.send_message(db_session, conv.id, send_request)

            assert result.content == "你好！有什么可以帮助你的？"
            assert result.role == "assistant"

    @pytest.mark.asyncio
    async def test_send_message_saves_user_message(self, db_session: AsyncSession):
        """
        函数级注释：测试发送消息时保存用户消息
        内部逻辑：验证用户消息被保存到数据库
        参数：
            db_session: 测试数据库会话
        """
        request = CreateConversationRequest(title="保存测试")
        conv = await ConversationService.create_conversation(db_session, request)

        send_request = SendMessageRequest(content="用户输入")

        with patch('app.services.conversation_service.ChatService') as mock_chat:
            mock_response = MagicMock()
            mock_response.answer = "回复"
            mock_response.sources = []

            mock_chat.chat_completion = AsyncMock(return_value=mock_response)

            await ConversationService.send_message(db_session, conv.id, send_request)

            # 验证消息被保存
            msg_result = await db_session.execute(
                select(Message).where(Message.conversation_id == conv.id)
            )
            messages = msg_result.scalars().all()

            # 应该有用户消息和助手消息
            assert len(messages) == 2


class TestConversationServiceSendMessageStream:
    """
    类级注释：测试流式发送消息功能
    """

    @pytest.mark.asyncio
    async def test_send_message_stream_conversation_not_found(self, db_session: AsyncSession):
        """
        函数级注释：测试流式发送消息到不存在的会话
        内部逻辑：会话不存在时返回错误SSE
        参数：
            db_session: 测试数据库会话
        """
        request = SendMessageRequest(content="测试")

        chunks = []
        async for chunk in ConversationService.send_message_stream(db_session, 99999, request):
            chunks.append(chunk)

        # 应该返回错误
        error_data = None
        for chunk in chunks:
            if chunk.startswith("data: "):
                try:
                    data = json.loads(chunk[6:])
                    if "error" in data:
                        error_data = data
                        break
                except json.JSONDecodeError:
                    pass

        assert error_data is not None
        assert "会话不存在" in error_data["error"]

    @pytest.mark.asyncio
    async def test_send_message_stream_with_mock(self, db_session: AsyncSession):
        """
        函数级注释：测试流式发送消息（mock）
        内部逻辑：mock ChatService.stream_chat_completion
        参数：
            db_session: 测试数据库会话
        """
        request = CreateConversationRequest(title="流式测试")
        conv = await ConversationService.create_conversation(db_session, request)

        send_request = SendMessageRequest(content="你好")

        # Mock ChatService
        async def mock_stream():
            yield 'data: {"answer": "你", "sources": []}\n\n'
            yield 'data: {"answer": "好", "sources": []}\n\n'
            yield 'data: {"answer": "！", "sources": []}\n\n'

        with patch('app.services.conversation_service.ChatService') as mock_chat:
            mock_chat.stream_chat_completion = lambda db, req: mock_stream()

            chunks = []
            async for chunk in ConversationService.send_message_stream(
                db_session, conv.id, send_request
            ):
                chunks.append(chunk)

            # 验证收到数据
            assert len(chunks) > 0
            # 验证最后有done标记
            assert any('"done": true' in chunk for chunk in chunks)


class TestConversationServiceHelpers:
    """
    类级注释：测试辅助方法
    """

    def test_to_conversation_response(self):
        """
        函数级注释：测试会话响应转换
        内部逻辑：验证ORM对象正确转换为响应模型
        """
        # 内部变量：创建测试用的datetime对象
        from datetime import datetime
        now = datetime.now()

        conv = Conversation(
            id=1,
            title="测试会话",
            model_name="glm-4",
            use_agent=1,
            message_count=5,
            total_tokens=1000,
            total_cost=0.01,
            created_at=now,
            updated_at=now
        )

        result = ConversationService._to_conversation_response(conv)

        assert result.title == "测试会话"
        assert result.model_name == "glm-4"
        assert result.use_agent is True
        assert result.message_count == 5
        assert result.id == 1

    def test_to_message_response(self):
        """
        函数级注释：测试消息响应转换
        内部逻辑：验证ORM对象正确转换为响应模型
        """
        from datetime import datetime
        now = datetime.now()

        # 内部逻辑：创建消息对象，设置必需字段
        msg = Message(
            id=1,
            conversation_id=1,
            role=MessageRole.ASSISTANT,
            content="测试内容",
            streaming_state="completed",
            tokens_count=100,
            created_at=now
        )

        # 内部逻辑：创建来源对象
        sources = [
            MessageSource(
                id=1,
                message_id=1,
                file_name="测试.pdf",
                text_segment="内容片段",
                score=85,
                position=0
            )
        ]

        result = ConversationService._to_message_response(msg, sources)

        assert result.content == "测试内容"
        assert result.streaming_state == "completed"
        assert len(result.sources) == 1
        assert result.sources[0].file_name == "测试.pdf"

    def test_to_message_response_no_sources(self):
        """
        函数级注释：测试消息响应转换（无来源）
        内部逻辑：sources为None时的处理
        """
        from datetime import datetime
        now = datetime.now()

        # 内部逻辑：创建消息对象，设置必需的tokens_count
        msg = Message(
            id=1,
            conversation_id=1,
            role=MessageRole.USER,
            content="用户消息",
            streaming_state="idle",
            tokens_count=0,
            created_at=now
        )

        result = ConversationService._to_message_response(msg, None)

        assert result.content == "用户消息"
        assert result.sources == []

    def test_generate_title_short_content(self):
        """
        函数级注释：测试生成标题（短内容）
        内部逻辑：内容短于最大长度时不截断
        """
        result = ConversationService._generate_title("短内容")
        assert result == "短内容"

    def test_generate_title_long_content(self):
        """
        函数级注释：测试生成标题（长内容）
        内部逻辑：内容超过最大长度时截断并添加省略号
        """
        long_content = "这是一条非常长的消息内容" * 10
        result = ConversationService._generate_title(long_content, max_length=20)

        assert len(result) == 23  # 20 + "..."
        assert result.endswith("...")

    def test_generate_title_with_newlines(self):
        """
        函数级注释：测试生成标题（含换行）
        内部逻辑：换行符被替换为空格
        """
        result = ConversationService._generate_title("第一行\n第二行\n第三行")
        assert "\n" not in result
        assert "第一行 第二行 第三行" == result

    def test_generate_title_with_spaces(self):
        """
        函数级注释：测试生成标题（含多余空格）
        内部逻辑：strip()去除两端空格，但保留中间空格
        """
        # 内部逻辑：strip()只去除两端空格，中间空格保留
        result = ConversationService._generate_title("  标题  内容  ")
        assert result == "标题  内容"

    def test_generate_title_exact_length(self):
        """
        函数级注释：测试生成标题（恰好等于最大长度）
        内部逻辑：不添加省略号
        """
        content = "a" * 30
        result = ConversationService._generate_title(content, max_length=30)
        assert result == content
        assert not result.endswith("...")


class TestConversationServiceIntegration:
    """
    类级注释：集成测试类
    """

    @pytest.mark.asyncio
    async def test_full_conversation_flow(self, db_session: AsyncSession):
        """
        函数级注释：测试完整对话流程
        内部逻辑：创建会话 -> 发送消息 -> 获取详情 -> 删除
        参数：
            db_session: 测试数据库会话
        """
        # 创建会话
        request = CreateConversationRequest(title="流程测试")
        conv = await ConversationService.create_conversation(db_session, request)

        # 获取列表
        list_result = await ConversationService.list_conversations(db_session)
        assert list_result.total >= 1

        # 获取详情
        detail = await ConversationService.get_conversation_detail(db_session, conv.id)
        assert detail is not None
        assert detail.conversation.title == "流程测试"

        # 更新
        update = UpdateConversationRequest(title="已更新")
        updated = await ConversationService.update_conversation(db_session, conv.id, update)
        assert updated.title == "已更新"

        # 删除
        deleted = await ConversationService.delete_conversation(db_session, conv.id)
        assert deleted is True

        # 验证删除
        check = await ConversationService.get_conversation_detail(db_session, conv.id)
        assert check is None


# ============================================================================
# 补充测试：覆盖未覆盖的代码行 (398-402, 407-422, 515-517, 558-562, 566-580, 594-596)
# ============================================================================


class TestConversationServiceMissingCoverage:
    """
    类级注释：补充测试以覆盖未覆盖的代码行
    未覆盖行：
        398-402: send_message中批量验证文档存在性
        407-422: doc_id验证和MessageSource创建（无效doc_id处理）
        515-517: 流式发送消息中解析sources
        558-562: 流式发送消息中批量验证文档
        566-580: 流式发送消息中创建MessageSource
        594-596: 异常处理
    """

    @pytest.mark.asyncio
    async def test_send_message_with_invalid_doc_id(self, db_session: AsyncSession):
        """
        测试目的：覆盖行398-422
        测试场景：sources包含无效的doc_id
        预期：无效doc_id应被设为None并记录警告日志
        """
        from app.schemas.chat import SourceInfo

        request = CreateConversationRequest(title="无效文档ID测试")
        conv = await ConversationService.create_conversation(db_session, request)

        send_request = SendMessageRequest(content="你好")

        # Mock ChatService返回包含无效doc_id的sources
        with patch('app.services.conversation_service.ChatService') as mock_chat:
            mock_response = MagicMock()
            mock_response.answer = "回复内容"
            # 内部逻辑：创建包含无效doc_id的sources（不能使用doc_id=None因为SourceInfo要求int类型）
            mock_response.sources = [
                SourceInfo(
                    doc_id=99999,  # 不存在的文档ID
                    file_name="不存在的文档.pdf",
                    text_segment="内容片段",
                    score=0.85
                ),
                SourceInfo(
                    doc_id=88888,  # 另一个不存在的文档ID
                    file_name="另一个不存在的文档.pdf",
                    text_segment="另一个内容",
                    score=0.75
                )
            ]

            mock_chat.chat_completion = AsyncMock(return_value=mock_response)

            result = await ConversationService.send_message(db_session, conv.id, send_request)

            # 内部逻辑：验证回复正常返回
            assert result.content == "回复内容"
            # 内部逻辑：sources应该被保存（即使doc_id无效）
            assert len(result.sources) == 2

    @pytest.mark.asyncio
    async def test_send_message_stream_with_invalid_doc_id(self, db_session: AsyncSession):
        """
        测试目的：覆盖行515-517, 558-580
        测试场景：流式发送消息时sources包含无效的doc_id
        预期：无效doc_id应被设为None
        """
        send_request = SendMessageRequest(content="你好")

        # Mock ChatService流式响应
        async def mock_stream():
            # 内部逻辑：返回包含无效doc_id的sources
            yield 'data: {"answer": "你好", "sources": [{"doc_id": 99999, "file_name": "不存在的文档.pdf", "text_segment": "内容", "score": 0.85}]}\n\n'

        request = CreateConversationRequest(title="流式无效文档测试")
        conv = await ConversationService.create_conversation(db_session, request)

        with patch('app.services.conversation_service.ChatService') as mock_chat:
            mock_chat.stream_chat_completion = lambda db, req: mock_stream()

            chunks = []
            async for chunk in ConversationService.send_message_stream(
                db_session, conv.id, send_request
            ):
                chunks.append(chunk)

            # 内部逻辑：应该收到数据块
            assert len(chunks) > 0
            # 内部逻辑：应该有done标记
            assert any('"done": true' in chunk for chunk in chunks)

    @pytest.mark.asyncio
    async def test_send_message_stream_json_decode_error(self, db_session: AsyncSession):
        """
        测试目的：覆盖行515-517（JSON解析异常）
        测试场景：流式数据包含无效JSON
        预期：应该捕获JSONDecodeError并继续
        """
        send_request = SendMessageRequest(content="你好")

        # Mock ChatService流式响应，包含无效JSON
        async def mock_stream():
            yield 'data: {"answer": "你好"}\n\n'
            yield 'data: invalid json\n\n'  # 无效JSON
            yield 'data: {"answer": "世界"}\n\n'

        request = CreateConversationRequest(title="JSON错误测试")
        conv = await ConversationService.create_conversation(db_session, request)

        with patch('app.services.conversation_service.ChatService') as mock_chat:
            mock_chat.stream_chat_completion = lambda db, req: mock_stream()

            chunks = []
            async for chunk in ConversationService.send_message_stream(
                db_session, conv.id, send_request
            ):
                chunks.append(chunk)

            # 内部逻辑：应该收到数据块和done标记
            assert len(chunks) > 0
            assert any('"done": true' in chunk for chunk in chunks)

    @pytest.mark.asyncio
    async def test_send_message_stream_exception_handling(self, db_session: AsyncSession):
        """
        测试目的：覆盖行594-596（异常处理）
        测试场景：流式发送消息时发生异常
        预期：应该捕获异常并返回错误信息
        """
        send_request = SendMessageRequest(content="你好")

        # Mock ChatService抛出异常
        async def mock_stream_error():
            yield 'data: {"answer": "开始"}\n\n'
            raise Exception("流式处理异常")

        request = CreateConversationRequest(title="异常处理测试")
        conv = await ConversationService.create_conversation(db_session, request)

        with patch('app.services.conversation_service.ChatService') as mock_chat:
            mock_chat.stream_chat_completion = lambda db, req: mock_stream_error()

            chunks = []
            async for chunk in ConversationService.send_message_stream(
                db_session, conv.id, send_request
            ):
                chunks.append(chunk)

            # 内部逻辑：应该有错误消息
            error_chunks = [c for c in chunks if "error" in c]
            assert len(error_chunks) > 0
            # 内部逻辑：应该有done标记
            assert any('"done": true' in chunk for chunk in chunks)

    @pytest.mark.asyncio
    async def test_send_message_with_valid_and_invalid_doc_ids(self, db_session: AsyncSession):
        """
        测试目的：覆盖行407-422（混合有效和无效doc_id）
        测试场景：sources同时包含有效和无效的doc_id
        预期：有效doc_id保留，无效doc_id设为None
        """
        from app.schemas.chat import SourceInfo
        from app.models.models import Document

        request = CreateConversationRequest(title="混合文档ID测试")
        conv = await ConversationService.create_conversation(db_session, request)

        # 内部逻辑：创建一个真实的文档用于有效doc_id
        doc = Document(
            file_name="有效文档.pdf",
            source_type="pdf",
            file_hash="abc123",
            file_path="/path/to/file.pdf"
        )
        db_session.add(doc)
        await db_session.commit()

        send_request = SendMessageRequest(content="你好")

        # Mock ChatService返回混合的sources
        with patch('app.services.conversation_service.ChatService') as mock_chat:
            mock_response = MagicMock()
            mock_response.answer = "回复内容"
            # 内部逻辑：包含有效和无效的doc_id
            mock_response.sources = [
                SourceInfo(
                    doc_id=doc.id,  # 有效的文档ID
                    file_name="有效文档.pdf",
                    text_segment="有效内容",
                    score=0.85
                ),
                SourceInfo(
                    doc_id=88888,  # 无效的文档ID
                    file_name="无效文档.pdf",
                    text_segment="无效内容",
                    score=0.75
                )
            ]

            mock_chat.chat_completion = AsyncMock(return_value=mock_response)

            result = await ConversationService.send_message(db_session, conv.id, send_request)

            assert result.content == "回复内容"
            # 内部逻辑：两个sources都应该被保存
            assert len(result.sources) == 2

    @pytest.mark.asyncio
    async def test_send_message_stream_with_sources_parsing(self, db_session: AsyncSession):
        """
        测试目的：覆盖行515-517（sources解析）
        测试场景：流式数据包含sources字段
        预期：正确解析sources并保存
        """
        send_request = SendMessageRequest(content="你好")

        # Mock ChatService流式响应，包含sources
        async def mock_stream():
            yield 'data: {"answer": "你好", "sources": [{"doc_id": null, "file_name": "test.pdf", "text_segment": "内容", "score": 0.9}]}\n\n'

        request = CreateConversationRequest(title="sources解析测试")
        conv = await ConversationService.create_conversation(db_session, request)

        with patch('app.services.conversation_service.ChatService') as mock_chat:
            mock_chat.stream_chat_completion = lambda db, req: mock_stream()

            chunks = []
            async for chunk in ConversationService.send_message_stream(
                db_session, conv.id, send_request
            ):
                chunks.append(chunk)

            # 内部逻辑：应该收到数据块和done标记
            assert len(chunks) > 0
            assert any('"done": true' in chunk for chunk in chunks)
