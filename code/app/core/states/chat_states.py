# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：聊天状态模式模块
内部逻辑：使用状态模式管理聊天对话流程
设计模式：状态模式（State Pattern）
设计原则：开闭原则、单一职责原则

状态转换图：
    IdleState → SendingState → StreamingState → CompletedState
       ↑                                        ↓
       └────────────────────────────────────────┘
                  (继续对话)

    任何状态 → ErrorState (发生错误)
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
import time


class ChatStage(str, Enum):
    """
    类级注释：聊天阶段枚举
    内部逻辑：定义聊天的所有阶段
    """
    # 空闲
    IDLE = "idle"
    # 发送中
    SENDING = "sending"
    # 流式接收中
    STREAMING = "streaming"
    # 已完成
    COMPLETED = "completed"
    # 错误
    ERROR = "error"


@dataclass
class Message:
    """
    类级注释：消息数据类
    内部逻辑：封装聊天消息
    """
    # 属性：消息角色
    role: str
    # 属性：消息内容
    content: str
    # 属性：时间戳
    timestamp: float = field(default_factory=time.time)
    # 属性：是否为流式消息
    is_stream: bool = False
    # 属性：额外元数据
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatContext:
    """
    类级注释：聊天上下文数据类
    内部逻辑：封装聊天的上下文信息
    """
    # 属性：对话 ID
    conversation_id: str
    # 属性：用户 ID
    user_id: Optional[str] = None
    # 属性：消息历史
    messages: List[Message] = field(default_factory=list)
    # 属性：当前输入
    current_input: Optional[str] = None
    # 属性：配置参数
    config: Dict[str, Any] = field(default_factory=dict)


class ChatState(ABC):
    """
    类级注释：聊天状态抽象基类
    内部逻辑：定义所有聊天状态的统一接口
    设计模式：状态模式 - 抽象状态
    """

    @property
    def stage(self) -> ChatStage:
        """
        函数级注释：获取当前聊天阶段
        返回值：聊天阶段枚举
        """
        return ChatStage.IDLE

    @abstractmethod
    async def send_message(
        self,
        context: 'ChatStateMachine',
        message: str
    ) -> AsyncIterator[str]:
        """
        函数级注释：发送消息并获取响应
        内部逻辑：由子类实现具体的发送逻辑
        参数：
            context - 聊天状态机
            message - 用户消息
        生成值：响应内容块
        """
        pass

    @abstractmethod
    def can_send(self) -> bool:
        """
        函数级注释：检查是否可以发送消息
        返回值：是否可以发送
        """
        pass

    @abstractmethod
    def can_retry(self) -> bool:
        """
        函数级注释：检查是否可以重试
        返回值：是否可以重试
        """
        pass

    @abstractmethod
    def is_terminal(self) -> bool:
        """
        函数级注释：检查是否为终止状态
        返回值：是否为终止状态
        """
        pass

    def get_description(self) -> str:
        """
        函数级注释：获取状态描述
        返回值：状态描述字符串
        """
        return f"{self.__class__.__name__}"


class IdleState(ChatState):
    """
    类级注释：空闲状态
    内部逻辑：聊天等待输入的初始状态
    设计模式：状态模式 - 具体状态
    """

    @property
    def stage(self) -> ChatStage:
        return ChatStage.IDLE

    async def send_message(
        self,
        context: 'ChatStateMachine',
        message: str
    ) -> AsyncIterator[str]:
        """
        函数级注释：发送消息
        内部逻辑：转换到发送状态 -> 发送消息
        """
        logger.info(f"[对话 {context.context.conversation_id}] 发送消息")

        # 内部逻辑：转换状态
        context._transition_to(SendingState())

        # 内部逻辑：发送消息
        async for chunk in context._current_state.send_message(context, message):
            yield chunk

    def can_send(self) -> bool:
        return True

    def can_retry(self) -> bool:
        return False

    def is_terminal(self) -> bool:
        return False


class SendingState(ChatState):
    """
    类级注释：发送中状态
    内部逻辑：正在发送请求到 AI 服务
    设计模式：状态模式 - 具体状态
    """

    def __init__(self):
        # 内部变量：发送开始时间
        self._start_time: Optional[float] = None

    @property
    def stage(self) -> ChatStage:
        return ChatStage.SENDING

    async def send_message(
        self,
        context: 'ChatStateMachine',
        message: str
    ) -> AsyncIterator[str]:
        """
        函数级注释：发送消息到 AI 服务
        内部逻辑：构建请求 -> 调用服务 -> 处理响应
        """
        self._start_time = time.time()
        logger.info(f"[对话 {context.context.conversation_id}] 正在发送请求到 AI 服务")

        try:
            # 内部逻辑：添加用户消息到历史
            user_message = Message(role="user", content=message)
            context.context.messages.append(user_message)

            # 内部逻辑：转换到流式状态
            context._transition_to(StreamingState())

            # 内部逻辑：发送并获取响应
            async for chunk in context._current_state.send_message(context, message):
                yield chunk

        except Exception as e:
            logger.error(f"[对话 {context.context.conversation_id}] 发送失败: {str(e)}")
            context._transition_to(ErrorState(str(e)))
            raise

    def can_send(self) -> bool:
        return False

    def can_retry(self) -> bool:
        return True

    def is_terminal(self) -> bool:
        return False


class StreamingState(ChatState):
    """
    类级注释：流式接收状态
    内部逻辑：正在接收 AI 的流式响应
    设计模式：状态模式 - 具体状态
    """

    def __init__(self):
        # 内部变量：响应内容缓冲区
        self._buffer: List[str] = []
        # 内部变量：是否开始接收
        self._has_started = False

    @property
    def stage(self) -> ChatStage:
        return ChatStage.STREAMING

    async def send_message(
        self,
        context: 'ChatStateMachine',
        message: str
    ) -> AsyncIterator[str]:
        """
        函数级注释：接收流式响应
        内部逻辑：调用聊天服务 -> 流式输出 -> 完成后转换状态
        """
        if not self._has_started:
            logger.info(f"[对话 {context.context.conversation_id}] 开始接收流式响应")
            self._has_started = True

        try:
            # 内部逻辑：调用聊天服务
            chat_service = context._service_provider
            if chat_service is None:
                raise RuntimeError("聊天服务未配置")

            # 内部逻辑：构建消息历史
            messages = [
                {"role": msg.role, "content": msg.content}
                for msg in context.context.messages
            ]

            # 内部逻辑：流式调用
            full_response = ""
            async for chunk in chat_service.stream_chat(messages):
                self._buffer.append(chunk)
                full_response += chunk
                yield chunk

            # 内部逻辑：添加助手消息到历史
            assistant_message = Message(
                role="assistant",
                content=full_response,
                is_stream=True
            )
            context.context.messages.append(assistant_message)

            # 内部逻辑：转换到完成状态
            context._transition_to(CompletedState())

            logger.info(f"[对话 {context.context.conversation_id}] 流式响应完成，长度: {len(full_response)}")

        except Exception as e:
            logger.error(f"[对话 {context.context.conversation_id}] 流式接收失败: {str(e)}")
            context._transition_to(ErrorState(str(e)))
            raise

    def can_send(self) -> bool:
        return False

    def can_retry(self) -> bool:
        return True

    def is_terminal(self) -> bool:
        return False


class CompletedState(ChatState):
    """
    类级注释：完成状态
    内部逻辑：消息处理完成的终止状态
    设计模式：状态模式 - 终止状态
    """

    @property
    def stage(self) -> ChatStage:
        return ChatStage.COMPLETED

    async def send_message(
        self,
        context: 'ChatStateMachine',
        message: str
    ) -> AsyncIterator[str]:
        """
        函数级注释：发送下一条消息
        内部逻辑：转换到空闲状态 -> 重新发送
        """
        # 内部逻辑：转换回空闲状态
        context._transition_to(IdleState())

        # 内部逻辑：重新发送
        async for chunk in context._current_state.send_message(context, message):
            yield chunk

    def can_send(self) -> bool:
        return True

    def can_retry(self) -> bool:
        return False

    def is_terminal(self) -> bool:
        return False


class ErrorState(ChatState):
    """
    类级注释：错误状态
    内部逻辑：处理失败的终止状态
    设计模式：状态模式 - 终止状态
    """

    def __init__(self, error_message: str):
        """
        函数级注释：初始化错误状态
        参数：
            error_message - 错误信息
        """
        self._error_message = error_message

    @property
    def stage(self) -> ChatStage:
        return ChatStage.ERROR

    @property
    def error_message(self) -> str:
        """获取错误信息"""
        return self._error_message

    async def send_message(
        self,
        context: 'ChatStateMachine',
        message: str
    ) -> AsyncIterator[str]:
        """
        函数级注释：错误状态下尝试重试
        内部逻辑：转换到空闲状态 -> 重新发送
        """
        logger.warning(f"[对话 {context.context.conversation_id}] 从错误状态恢复: {self._error_message}")

        # 内部逻辑：转换到空闲状态
        context._transition_to(IdleState())

        # 内部逻辑：重新发送
        async for chunk in context._current_state.send_message(context, message):
            yield chunk

    def can_send(self) -> bool:
        return True

    def can_retry(self) -> bool:
        return True

    def is_terminal(self) -> bool:
        return False


class ChatStateMachine:
    """
    类级注释：聊天状态机
    内部逻辑：维护聊天对话的状态和上下文
    设计模式：状态模式 - 上下文角色
    职责：
        1. 维护当前状态
        2. 存储聊天上下文
        3. 提供状态转换接口
        4. 管理消息流

    使用场景：
        - 聊天 API 端点
        - WebSocket 聊天连接
        - 流式响应处理
    """

    def __init__(
        self,
        conversation_id: str,
        service_provider: Optional[Any] = None,
        user_id: Optional[str] = None,
        initial_state: Optional[ChatState] = None
    ):
        """
        函数级注释：初始化聊天状态机
        参数：
            conversation_id - 对话 ID
            service_provider - 聊天服务提供者
            user_id - 用户 ID
            initial_state - 初始状态
        """
        # 内部变量：聊天上下文
        self.context = ChatContext(
            conversation_id=conversation_id,
            user_id=user_id
        )

        # 内部变量：当前状态
        self._current_state = initial_state or IdleState()

        # 内部变量：状态历史
        self._state_history: List[ChatState] = [self._current_state]

        # 内部变量：服务提供者
        self._service_provider = service_provider

        # 内部变量：统计信息
        self._stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "errors": 0,
            "total_duration": 0.0
        }

        logger.info(f"[对话 {conversation_id}] 聊天状态机初始化完成")

    @property
    def current_state(self) -> ChatState:
        """获取当前状态"""
        return self._current_state

    @property
    def current_stage(self) -> ChatStage:
        """获取当前聊天阶段"""
        return self._current_state.stage

    def _transition_to(self, new_state: ChatState) -> None:
        """
        函数级注释：转换到新状态
        内部逻辑：更新当前状态 -> 记录历史
        参数：
            new_state - 新状态
        """
        old_state = self._current_state
        self._current_state = new_state
        self._state_history.append(new_state)

        logger.debug(
            f"[对话 {self.context.conversation_id}] 状态转换: "
            f"{old_state.get_description()} -> {new_state.get_description()}"
        )

    async def send_message(self, message: str) -> AsyncIterator[str]:
        """
        函数级注释：发送消息并获取响应
        内部逻辑：调用当前状态的 send_message -> 流式输出响应
        参数：
            message - 用户消息
        生成值：响应内容块

        @example
        ```python
        state_machine = ChatStateMachine("conv_123", chat_service)
        async for chunk in state_machine.send_message("你好"):
            print(chunk, end="")
        ```
        """
        start_time = time.time()

        try:
            self._stats["messages_sent"] += 1
            self.context.current_input = message

            async for chunk in self._current_state.send_message(self, message):
                yield chunk

            duration = time.time() - start_time
            self._stats["total_duration"] += duration
            self._stats["messages_received"] += 1

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"[对话 {self.context.conversation_id}] 发送消息异常: {str(e)}")
            raise

    async def reset(self) -> None:
        """
        函数级注释：重置状态机
        内部逻辑：清空消息历史 -> 重置到空闲状态
        """
        logger.info(f"[对话 {self.context.conversation_id}] 重置状态机")

        self.context.messages.clear()
        self.context.current_input = None
        self._transition_to(IdleState())

    def get_messages(self) -> List[Message]:
        """获取所有消息"""
        return self.context.messages.copy()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self._stats.copy()
        stats["current_state"] = self._current_state.get_description()
        stats["current_stage"] = self._current_state.stage.value
        stats["message_count"] = len(self.context.messages)
        stats["state_history"] = [s.get_description() for s in self._state_history]
        return stats

    def can_send(self) -> bool:
        """检查是否可以发送消息"""
        return self._current_state.can_send()

    def is_error(self) -> bool:
        """检查是否处于错误状态"""
        return isinstance(self._current_state, ErrorState)

    def get_error(self) -> Optional[str]:
        """获取错误信息"""
        if self.is_error():
            return self._current_state.error_message
        return None


class ChatStateMachineFactory:
    """
    类级注释：聊天状态机工厂
    内部逻辑：统一创建聊天状态机
    设计模式：工厂模式
    """

    def __init__(self, service_provider: Any):
        """
        函数级注释：初始化工厂
        参数：
            service_provider - 聊天服务提供者
        """
        self._service_provider = service_provider

    def create(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
        initial_messages: Optional[List[Message]] = None
    ) -> ChatStateMachine:
        """
        函数级注释：创建聊天状态机
        参数：
            conversation_id - 对话 ID
            user_id - 用户 ID
            initial_messages - 初始消息列表
        返回值：聊天状态机实例
        """
        state_machine = ChatStateMachine(
            conversation_id=conversation_id,
            service_provider=self._service_provider,
            user_id=user_id
        )

        # 内部逻辑：添加初始消息
        if initial_messages:
            state_machine.context.messages.extend(initial_messages)

        return state_machine


# 内部变量：导出所有公共接口
__all__ = [
    # 基础类
    'ChatState',
    'ChatStateMachine',
    'ChatStateMachineFactory',
    # 数据类
    'Message',
    'ChatContext',
    # 枚举
    'ChatStage',
    # 具体状态
    'IdleState',
    'SendingState',
    'StreamingState',
    'CompletedState',
    'ErrorState',
]
