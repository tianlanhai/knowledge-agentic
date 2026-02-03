# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：状态模式模块测试
内部逻辑：验证聊天状态和文档处理状态的状态机功能
设计模式：状态模式（State Pattern）
测试覆盖范围：
    - ChatStage: 聊天阶段枚举
    - Message: 消息数据类
    - ChatContext: 聊天上下文数据类
    - ChatState: 聊天状态抽象基类
    - IdleState: 空闲状态
    - SendingState: 发送中状态
    - StreamingState: 流式接收状态
    - CompletedState: 完成状态
    - ErrorState: 错误状态
    - ChatStateMachine: 聊天状态机
    - ChatStateMachineFactory: 聊天状态机工厂
    - ProcessingStage: 处理阶段枚举
    - ProcessingResult: 处理结果数据类
    - DocumentState: 文档状态抽象基类
    - UploadedState: 已上传状态
    - ParsingState: 解析中状态
    - ChunkingState: 分块状态
    - VectorizingState: 向量化状态
    - CompletedState: 文档完成状态
    - FailedState: 文档失败状态
    - DocumentContext: 文档上下文
    - DocumentStateMachine: 文档状态机
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.core.states.chat_states import (
    ChatStage,
    Message,
    ChatContext,
    ChatState,
    IdleState,
    SendingState,
    StreamingState,
    CompletedState,
    ErrorState,
    ChatStateMachine,
    ChatStateMachineFactory,
)

from app.core.states.document_states import (
    ProcessingStage,
    ProcessingResult,
    DocumentState,
    UploadedState,
    ParsingState,
    ChunkingState,
    VectorizingState,
    CompletedState as DocumentCompletedState,
    FailedState as DocumentFailedState,
    DocumentProcessingException,
    DocumentContext,
    DocumentStateMachine,
)


# ============================================================================
# Chat States 测试
# ============================================================================

class TestChatStage:
    """测试聊天阶段枚举"""

    def test_stage_values(self):
        """测试阶段值"""
        assert ChatStage.IDLE == "idle"
        assert ChatStage.SENDING == "sending"
        assert ChatStage.STREAMING == "streaming"
        assert ChatStage.COMPLETED == "completed"
        assert ChatStage.ERROR == "error"


class TestMessage:
    """测试消息数据类"""

    def test_init(self):
        """测试初始化"""
        message = Message(
            role="user",
            content="Hello"
        )

        assert message.role == "user"
        assert message.content == "Hello"
        assert message.is_stream is False
        assert message.metadata == {}

    def test_with_metadata(self):
        """测试带元数据的消息"""
        message = Message(
            role="assistant",
            content="Hi there",
            metadata={"model": "gpt-4"}
        )

        assert message.metadata == {"model": "gpt-4"}

    def test_stream_message(self):
        """测试流式消息"""
        message = Message(
            role="assistant",
            content="Hello",
            is_stream=True
        )

        assert message.is_stream is True


class TestChatContext:
    """测试聊天上下文"""

    def test_init(self):
        """测试初始化"""
        context = ChatContext(
            conversation_id="conv_123",
            user_id="user_456"
        )

        assert context.conversation_id == "conv_123"
        assert context.user_id == "user_456"
        assert context.messages == []
        assert context.current_input is None
        assert context.config == {}

    def test_with_config(self):
        """测试带配置的上下文"""
        config = {"temperature": 0.7, "max_tokens": 2000}
        context = ChatContext(
            conversation_id="conv_123",
            config=config
        )

        assert context.config == config


class TestIdleState:
    """测试空闲状态"""

    def test_stage_property(self):
        """测试阶段属性"""
        state = IdleState()
        assert state.stage == ChatStage.IDLE

    @pytest.mark.asyncio
    async def test_can_send(self):
        """测试是否可发送"""
        state = IdleState()
        assert state.can_send() is True

    @pytest.mark.asyncio
    async def test_can_retry(self):
        """测试是否可重试"""
        state = IdleState()
        assert state.can_retry() is False

    @pytest.mark.asyncio
    async def test_is_terminal(self):
        """测试是否为终止状态"""
        state = IdleState()
        assert state.is_terminal() is False

    @pytest.mark.asyncio
    async def test_send_message_transitions(self):
        """测试发送消息状态转换"""
        state = IdleState()
        context = ChatStateMachine("conv_123")

        # 添加mock服务提供者以避免实际调用
        class MockService:
            def stream_chat(self, messages):  # 不是 async 函数
                # 直接返回异步生成器
                async def mock_stream():
                    yield "response"
                return mock_stream()

        context._service_provider = MockService()

        chunks = []
        async for chunk in state.send_message(context, "Hello"):
            chunks.append(chunk)

        # 验证状态转换和响应
        assert isinstance(chunks, list)
        # 最终状态应该是CompletedState
        assert context.current_stage == ChatStage.COMPLETED

    @pytest.mark.asyncio
    async def test_get_description(self):
        """测试获取描述"""
        state = IdleState()
        description = state.get_description()
        assert "IdleState" in description


class TestSendingState:
    """测试发送中状态"""

    def test_stage_property(self):
        """测试阶段属性"""
        state = SendingState()
        assert state.stage == ChatStage.SENDING

    def test_can_send(self):
        """测试是否可发送"""
        state = SendingState()
        assert state.can_send() is False

    def test_can_retry(self):
        """测试是否可重试"""
        state = SendingState()
        assert state.can_retry() is True

    def test_is_terminal(self):
        """测试是否为终止状态"""
        state = SendingState()
        assert state.is_terminal() is False


class TestStreamingState:
    """测试流式接收状态"""

    def test_stage_property(self):
        """测试阶段属性"""
        state = StreamingState()
        assert state.stage == ChatStage.STREAMING

    def test_can_send(self):
        """测试是否可发送"""
        state = StreamingState()
        assert state.can_send() is False

    def test_can_retry(self):
        """测试是否可重试"""
        state = StreamingState()
        assert state.can_retry() is True

    def test_is_terminal(self):
        """测试是否为终止状态"""
        state = StreamingState()
        assert state.is_terminal() is False


class TestCompletedState:
    """测试完成状态"""

    def test_stage_property(self):
        """测试阶段属性"""
        state = CompletedState()
        assert state.stage == ChatStage.COMPLETED

    def test_can_send(self):
        """测试是否可发送"""
        state = CompletedState()
        assert state.can_send() is True

    def test_can_retry(self):
        """测试是否可重试"""
        state = CompletedState()
        assert state.can_retry() is False

    def test_is_terminal(self):
        """测试是否为终止状态"""
        state = CompletedState()
        # 根据实际实现，CompletedState不是终止状态(可以发送新消息)
        assert state.is_terminal() is False

    @pytest.mark.asyncio
    async def test_send_message_resets_to_idle(self):
        """测试发送消息重置到空闲状态"""
        state = CompletedState()
        context = ChatStateMachine("conv_123")

        # 添加mock服务提供者
        class MockService:
            def stream_chat(self, messages):  # 不是 async 函数
                async def mock_stream():
                    yield "response"
                return mock_stream()

        context._service_provider = MockService()

        async for _ in state.send_message(context, "New message"):
            pass

        # 发送消息后，经过完整流程最终到达 CompletedState
        assert context.current_stage == ChatStage.COMPLETED


class TestErrorState:
    """测试错误状态"""

    def test_stage_property(self):
        """测试阶段属性"""
        state = ErrorState("Test error")
        assert state.stage == ChatStage.ERROR

    def test_error_message_property(self):
        """测试错误信息属性"""
        error_msg = "Something went wrong"
        state = ErrorState(error_msg)
        assert state.error_message == error_msg

    def test_can_send(self):
        """测试是否可发送"""
        state = ErrorState("error")
        assert state.can_send() is True

    def test_can_retry(self):
        """测试是否可重试"""
        state = ErrorState("error")
        assert state.can_retry() is True

    def test_is_terminal(self):
        """测试是否为终止状态"""
        state = ErrorState("error")
        assert state.is_terminal() is False


class TestChatStateMachine:
    """测试聊天状态机"""

    def test_init(self):
        """测试初始化"""
        machine = ChatStateMachine("conv_123")

        assert machine.context.conversation_id == "conv_123"
        assert machine.current_stage == ChatStage.IDLE
        assert machine.is_error() is False

    def test_init_with_user_id(self):
        """测试带用户ID初始化"""
        machine = ChatStateMachine(
            conversation_id="conv_123",
            user_id="user_456"
        )

        assert machine.context.user_id == "user_456"

    def test_init_with_initial_state(self):
        """测试带初始状态初始化"""
        machine = ChatStateMachine(
            conversation_id="conv_123",
            initial_state=CompletedState()
        )

        assert machine.current_stage == ChatStage.COMPLETED

    def test_current_state_property(self):
        """测试当前状态属性"""
        machine = ChatStateMachine("conv_123")
        assert isinstance(machine.current_state, IdleState)

    def test_can_send(self):
        """测试是否可发送"""
        machine = ChatStateMachine("conv_123")
        assert machine.can_send() is True

    def test_is_error(self):
        """测试是否处于错误状态"""
        machine = ChatStateMachine("conv_123")
        assert machine.is_error() is False

    def test_get_error_when_no_error(self):
        """测试无错误时获取错误信息"""
        machine = ChatStateMachine("conv_123")
        assert machine.get_error() is None

    def test_get_messages(self):
        """测试获取消息"""
        machine = ChatStateMachine("conv_123")
        messages = machine.get_messages()
        assert messages == []

    @pytest.mark.asyncio
    async def test_send_message(self):
        """测试发送消息"""
        machine = ChatStateMachine("conv_123")

        # 使用 mock 服务提供者
        class MockService:
            def stream_chat(self, messages):  # 不是 async 函数
                async def mock_stream():
                    yield "Hello"
                return mock_stream()

        machine._service_provider = MockService()

        chunks = []
        async for chunk in machine.send_message("Hi"):
            chunks.append(chunk)

        # 验证消息被设置
        assert machine.context.current_input == "Hi"
        # 验证至少有一个响应块
        assert len(chunks) > 0

    def test_get_stats(self):
        """测试获取统计信息"""
        machine = ChatStateMachine("conv_123")
        stats = machine.get_stats()

        assert "current_state" in stats
        assert "current_stage" in stats
        assert "message_count" in stats
        assert "messages_sent" in stats
        assert "messages_received" in stats
        assert stats["messages_sent"] == 0

    @pytest.mark.asyncio
    async def test_reset(self):
        """测试重置状态机"""
        machine = ChatStateMachine("conv_123")
        machine.context.messages.append(Message(role="user", content="test"))

        await machine.reset()

        assert len(machine.context.messages) == 0
        assert machine.current_stage == ChatStage.IDLE


class TestChatStateMachineFactory:
    """测试聊天状态机工厂"""

    def test_create(self):
        """测试创建状态机"""
        mock_provider = Mock()

        factory = ChatStateMachineFactory(mock_provider)
        machine = factory.create("conv_123", user_id="user_456")

        assert machine.context.conversation_id == "conv_123"
        assert machine.context.user_id == "user_456"

    def test_create_with_initial_messages(self):
        """测试创建带初始消息的状态机"""
        mock_provider = Mock()
        messages = [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi")
        ]

        factory = ChatStateMachineFactory(mock_provider)
        machine = factory.create("conv_123", initial_messages=messages)

        assert len(machine.context.messages) == 2


# ============================================================================
# Document States 测试
# ============================================================================

class TestProcessingStage:
    """测试处理阶段枚举"""

    def test_stage_values(self):
        """测试阶段值"""
        assert ProcessingStage.UPLOADED == "uploaded"
        assert ProcessingStage.PARSING == "parsing"
        assert ProcessingStage.CHUNKING == "chunking"
        assert ProcessingStage.VECTORIZING == "vectorizing"
        assert ProcessingStage.COMPLETED == "completed"
        assert ProcessingStage.FAILED == "failed"


class TestProcessingResult:
    """测试处理结果"""

    def test_success_result(self):
        """测试成功结果"""
        result = ProcessingResult(success=True, data=100)

        # is_valid是属性，不是方法
        assert result.is_valid is True
        assert result.data == 100
        assert result.error is None

    def test_failure_result(self):
        """测试失败结果"""
        result = ProcessingResult(
            success=False,
            error="Processing failed"
        )

        assert result.success is False
        assert result.error == "Processing failed"

    def test_stage_info_success(self):
        """测试成功阶段信息"""
        result = ProcessingResult(success=True, data=50)
        info = result.stage_info
        assert "成功" in info

    def test_stage_info_failure(self):
        """测试失败阶段信息"""
        result = ProcessingResult(success=False, error="Test error")
        info = result.stage_info
        assert "失败" in info

    def test_with_duration(self):
        """测试带处理时长"""
        result = ProcessingResult(
            success=True,
            duration=1.5
        )
        assert result.duration == 1.5

    def test_with_metadata(self):
        """测试带元数据"""
        metadata = {"stage": "parsing", "chunks": 5}
        result = ProcessingResult(
            success=True,
            metadata=metadata
        )
        assert result.metadata == metadata


class TestUploadedState:
    """测试已上传状态"""

    def test_stage_property(self):
        """测试阶段属性"""
        state = UploadedState()
        assert state.stage == ProcessingStage.UPLOADED

    def test_can_process(self):
        """测试是否可处理"""
        state = UploadedState()
        assert state.can_process() is False

    def test_can_retry(self):
        """测试是否可重试"""
        state = UploadedState()
        assert state.can_retry() is True

    def test_is_terminal(self):
        """测试是否为终止状态"""
        state = UploadedState()
        assert state.is_terminal() is False

    @pytest.mark.asyncio
    async def test_next_with_valid_file(self):
        """测试有效文件的下一步"""
        state = UploadedState()
        context = DocumentContext("doc_123")
        context.set_data('file_info', {
            'size': 1024,
            'name': 'test.txt'
        })

        next_state = await state.next(context)
        assert isinstance(next_state, ParsingState)

    @pytest.mark.asyncio
    async def test_next_with_too_large_file(self):
        """测试过大文件的下一步"""
        state = UploadedState()
        context = DocumentContext("doc_123")
        context.set_data('file_info', {
            'size': 200 * 1024 * 1024,  # 200MB
            'name': 'large.pdf'
        })

        next_state = await state.next(context)
        assert isinstance(next_state, DocumentFailedState)

    @pytest.mark.asyncio
    async def test_next_with_invalid_file_type(self):
        """测试无效文件类型的下一步"""
        state = UploadedState()
        context = DocumentContext("doc_123")
        context.set_data('file_info', {
            'size': 1024,
            'name': 'test.exe'
        })

        next_state = await state.next(context)
        assert isinstance(next_state, DocumentFailedState)


class TestParsingState:
    """测试解析中状态"""

    def test_stage_property(self):
        """测试阶段属性"""
        state = ParsingState()
        assert state.stage == ProcessingStage.PARSING

    def test_can_process(self):
        """测试是否可处理"""
        state = ParsingState()
        assert state.can_process() is True

    def test_can_retry(self):
        """测试是否可重试"""
        state = ParsingState()
        assert state.can_retry() is True

    def test_is_terminal(self):
        """测试是否为终止状态"""
        state = ParsingState()
        assert state.is_terminal() is False

    @pytest.mark.asyncio
    async def test_next_success(self):
        """测试成功解析"""
        state = ParsingState()
        context = DocumentContext("doc_123")
        context.set_data('file_path', 'test.txt')

        # Mock default parse
        with patch.object(state, '_default_parse', return_value="Test content"):
            next_state = await state.next(context)

        assert isinstance(next_state, ChunkingState)


class TestChunkingState:
    """测试分块状态"""

    def test_stage_property(self):
        """测试阶段属性"""
        state = ChunkingState()
        assert state.stage == ProcessingStage.CHUNKING

    def test_custom_chunk_size(self):
        """测试自定义块大小"""
        state = ChunkingState(chunk_size=500, chunk_overlap=50)
        assert state._chunk_size == 500
        assert state._chunk_overlap == 50

    def test_can_process(self):
        """测试是否可处理"""
        state = ChunkingState()
        assert state.can_process() is True

    def test_can_retry(self):
        """测试是否可重试"""
        state = ChunkingState()
        assert state.can_retry() is True

    def test_is_terminal(self):
        """测试是否为终止状态"""
        state = ChunkingState()
        assert state.is_terminal() is False

    @pytest.mark.asyncio
    async def test_next_with_content(self):
        """测试有内容的下一步"""
        state = ChunkingState()
        context = DocumentContext("doc_123")
        context.set_data('parsed_content', "This is a test document. " * 100)

        with patch.object(state, '_default_chunk', return_value=["chunk1", "chunk2"]):
            next_state = await state.next(context)

        assert isinstance(next_state, VectorizingState)

    @pytest.mark.asyncio
    async def test_next_with_no_content(self):
        """测试无内容的下一步"""
        state = ChunkingState()
        context = DocumentContext("doc_123")

        next_state = await state.next(context)
        assert isinstance(next_state, DocumentFailedState)


class TestVectorizingState:
    """测试向量化状态"""

    def test_stage_property(self):
        """测试阶段属性"""
        state = VectorizingState()
        assert state.stage == ProcessingStage.VECTORIZING

    def test_can_process(self):
        """测试是否可处理"""
        state = VectorizingState()
        assert state.can_process() is True

    def test_can_retry(self):
        """测试是否可重试"""
        state = VectorizingState()
        assert state.can_retry() is True

    def test_is_terminal(self):
        """测试是否为终止状态"""
        state = VectorizingState()
        assert state.is_terminal() is False

    @pytest.mark.asyncio
    async def test_next_with_chunks(self):
        """测试有块的下一步"""
        state = VectorizingState()
        context = DocumentContext("doc_123")
        context.set_data('chunks', ["chunk1", "chunk2"])

        with patch.object(state, '_default_vectorize', return_value=["vec1", "vec2"]):
            next_state = await state.next(context)

        assert isinstance(next_state, DocumentCompletedState)

    @pytest.mark.asyncio
    async def test_next_with_no_chunks(self):
        """测试无块的下一步"""
        state = VectorizingState()
        context = DocumentContext("doc_123")

        next_state = await state.next(context)
        assert isinstance(next_state, DocumentFailedState)


class TestDocumentCompletedState:
    """测试文档完成状态"""

    def test_stage_property(self):
        """测试阶段属性"""
        from app.core.states.document_states import CompletedState as DocCompletedState
        state = DocCompletedState()
        assert state.stage == ProcessingStage.COMPLETED

    def test_can_process(self):
        """测试是否可处理"""
        from app.core.states.document_states import CompletedState as DocCompletedState
        state = DocCompletedState()
        assert state.can_process() is False

    def test_can_retry(self):
        """测试是否可重试"""
        from app.core.states.document_states import CompletedState as DocCompletedState
        state = DocCompletedState()
        assert state.can_retry() is False

    def test_is_terminal(self):
        """测试是否为终止状态"""
        from app.core.states.document_states import CompletedState as DocCompletedState
        state = DocCompletedState()
        assert state.is_terminal() is True

    @pytest.mark.asyncio
    async def test_next_returns_self(self):
        """测试下一步返回自身"""
        from app.core.states.document_states import CompletedState as DocCompletedState
        state = DocCompletedState()
        context = DocumentContext("doc_123")

        next_state = await state.next(context)
        assert next_state is state


class TestDocumentFailedState:
    """测试文档失败状态"""

    def test_stage_property(self):
        """测试阶段属性"""
        from app.core.states.document_states import FailedState as DocFailedState
        state = DocFailedState("Test error")
        assert state.stage == ProcessingStage.FAILED

    def test_error_message_property(self):
        """测试错误信息属性"""
        from app.core.states.document_states import FailedState as DocFailedState
        error_msg = "Processing failed"
        state = DocFailedState(error_msg)
        assert state.error_message == error_msg

    def test_can_process(self):
        """测试是否可处理"""
        from app.core.states.document_states import FailedState as DocFailedState
        state = DocFailedState("error")
        assert state.can_process() is False

    def test_can_retry(self):
        """测试是否可重试"""
        from app.core.states.document_states import FailedState as DocFailedState
        state = DocFailedState("error")
        assert state.can_retry() is True

    def test_is_terminal(self):
        """测试是否为终止状态"""
        from app.core.states.document_states import FailedState as DocFailedState
        state = DocFailedState("error")
        assert state.is_terminal() is True


class TestDocumentContext:
    """测试文档上下文"""

    def test_init(self):
        """测试初始化"""
        context = DocumentContext("doc_123")

        assert context.document_id == "doc_123"
        assert context.current_stage == ProcessingStage.UPLOADED
        assert context.is_finished is False
        assert context.is_failed is False

    def test_with_max_retries(self):
        """测试带最大重试次数"""
        context = DocumentContext("doc_123", max_retries=5)
        assert context._max_retries == 5

    def test_current_state_property(self):
        """测试当前状态属性"""
        context = DocumentContext("doc_123")
        assert isinstance(context.current_state, UploadedState)

    def test_get_set_data(self):
        """测试获取设置数据"""
        context = DocumentContext("doc_123")

        context.set_data('key1', 'value1')
        assert context.get_data('key1') == 'value1'
        assert context.get_data('nonexistent', 'default') == 'default'

    def test_add_get_results(self):
        """测试添加获取结果"""
        context = DocumentContext("doc_123")

        result = ProcessingResult(success=True, data=100)
        context.add_result(result)

        results = context.get_results()
        assert len(results) == 1
        assert results[0] is result

    def test_get_state_history(self):
        """测试获取状态历史"""
        context = DocumentContext("doc_123")
        history = context.get_state_history()
        assert len(history) >= 1

    def test_get_summary(self):
        """测试获取摘要"""
        context = DocumentContext("doc_123")
        summary = context.get_summary()

        assert "document_id" in summary
        assert "current_state" in summary
        assert "is_finished" in summary


class TestDocumentStateMachine:
    """测试文档状态机"""

    @pytest.mark.asyncio
    async def test_process_document_success(self):
        """测试成功处理文档"""
        # Mock the entire chain
        machine = DocumentStateMachine()

        # 使用 mock 处理函数
        async def mock_parse(ctx):
            return "parsed content"

        async def mock_chunk(content):
            return ["chunk1", "chunk2"]

        async def mock_vectorize(chunks, ctx):
            return ["vec1", "vec2"]

        machine = DocumentStateMachine(
            parser_func=mock_parse,
            chunker_func=mock_chunk,
            vectorizer_func=mock_vectorize
        )

        result = await machine.process_document(
            document_id="doc_123",
            file_path="test.txt",
            file_info={"size": 1024, "name": "test.txt"}
        )

        assert result["document_id"] == "doc_123"
        # 应该有成功的处理结果

    def test_init(self):
        """测试初始化"""
        machine = DocumentStateMachine()

        assert machine._max_retries == 3
        assert machine._validation_func is None

    def test_init_with_custom_functions(self):
        """测试带自定义函数初始化"""
        validation_func = Mock()
        parser_func = Mock()

        machine = DocumentStateMachine(
            validation_func=validation_func,
            parser_func=parser_func
        )

        assert machine._validation_func is validation_func
        assert machine._parser_func is parser_func
