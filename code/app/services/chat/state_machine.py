# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：聊天状态机模块
内部逻辑：实现清晰的对话状态转换，支持复杂对话流程管理
设计模式：状态模式（State Pattern）+ 状态机模式
设计原则：开闭原则、单一职责原则
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable, Type
from enum import Enum
from loguru import logger
from dataclasses import dataclass, field
from datetime import datetime
import asyncio


class ChatStateType(Enum):
    """
    类级注释：聊天状态类型枚举
    内部逻辑：定义所有可能的对话状态
    """
    # 空闲状态（等待用户输入）
    IDLE = "idle"
    # 处理中（正在生成回复）
    PROCESSING = "processing"
    # 流式输出中
    STREAMING = "streaming"
    # 等待用户确认
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    # 错误状态
    ERROR = "error"
    # 已完成
    COMPLETED = "completed"
    # 已取消
    CANCELLED = "cancelled"


class StateTransitionEvent(Enum):
    """
    类级注释：状态转换事件枚举
    内部逻辑：定义触发状态转换的事件
    """
    # 用户发送消息
    USER_MESSAGE = "user_message"
    # 开始生成回复
    START_GENERATION = "start_generation"
    # 开始流式输出
    START_STREAMING = "start_streaming"
    # 流式输出完成
    STREAM_COMPLETE = "stream_complete"
    # 生成完成
    GENERATION_COMPLETE = "generation_complete"
    # 发生错误
    ERROR_OCCURRED = "error_occurred"
    # 用户取消
    USER_CANCEL = "user_cancel"
    # 重置对话
    RESET = "reset"
    # 需要用户确认
    REQUEST_CONFIRMATION = "request_confirmation"
    # 用户确认
    USER_CONFIRMED = "user_confirmed"
    # 用户拒绝
    USER_DECLINED = "user_declined"


@dataclass
class StateTransition:
    """
    类级注释：状态转换记录
    内部逻辑：封装状态转换的信息
    """
    # 属性：源状态
    from_state: ChatStateType
    # 属性：目标状态
    to_state: ChatStateType
    # 属性：触发事件
    event: StateTransitionEvent
    # 属性：转换时间
    timestamp: datetime = field(default_factory=datetime.now)
    # 属性：额外数据
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatContext:
    """
    类级注释：聊天上下文
    内部逻辑：在状态机中传递的上下文数据
    设计模式：上下文对象模式
    """
    # 属性：会话 ID
    conversation_id: Optional[str] = None
    # 属性：用户消息
    user_message: Optional[str] = None
    # 属性：助手回复
    assistant_response: Optional[str] = None
    # 属性：历史消息
    history: List[Dict[str, Any]] = field(default_factory=list)
    # 属性：额外参数
    params: Dict[str, Any] = field(default_factory=dict)
    # 属性：错误信息
    error: Optional[str] = None
    # 属性：流式内容累积器
    stream_buffer: List[str] = field(default_factory=list)

    def add_stream_chunk(self, chunk: str) -> None:
        """
        函数级注释：添加流式内容块
        参数：
            chunk - 内容块
        """
        self.stream_buffer.append(chunk)

    def get_stream_content(self) -> str:
        """
        函数级注释：获取累积的流式内容
        返回值：拼接后的内容
        """
        return "".join(self.stream_buffer)

    def clear_stream_buffer(self) -> None:
        """
        函数级注释：清空流式缓冲区
        """
        self.stream_buffer.clear()


class ChatState(ABC):
    """
    类级注释：聊天状态抽象基类
    内部逻辑：定义状态的行为接口
    设计模式：状态模式 - 抽象状态
    """

    # 内部变量：状态类型
    state_type: ChatStateType = ChatStateType.IDLE

    def __init__(self, state_machine: 'ChatStateMachine'):
        """
        函数级注释：初始化状态
        参数：
            state_machine - 状态机引用
        """
        # 内部变量：状态机引用
        self._state_machine = state_machine

    @property
    def name(self) -> str:
        """
        函数级注释：获取状态名称
        返回值：状态名称
        """
        return self.state_type.value

    async def enter(self, context: ChatContext) -> None:
        """
        函数级注释：进入状态时调用
        参数：
            context - 聊天上下文
        """
        logger.debug(f"进入状态: {self.name}")

    async def exit(self, context: ChatContext) -> None:
        """
        函数级注释：离开状态时调用
        参数：
            context - 聊天上下文
        """
        logger.debug(f"离开状态: {self.name}")

    async def handle_event(
        self,
        event: StateTransitionEvent,
        context: ChatContext
    ) -> Optional[ChatStateType]:
        """
        函数级注释：处理事件
        内部逻辑：根据事件决定是否转换状态
        参数：
            event - 转换事件
            context - 聊天上下文
        返回值：目标状态类型，None 表示不转换
        """
        logger.debug(f"状态 {self.name} 处理事件: {event.value}")
        return None

    async def on_message(self, context: ChatContext, message: str) -> None:
        """
        函数级注释：处理用户消息
        参数：
            context - 聊天上下文
            message - 用户消息
        """
        logger.debug(f"状态 {self.name} 收到消息: {message[:50]}...")

    async def on_stream_chunk(self, context: ChatContext, chunk: str) -> None:
        """
        函数级注释：处理流式内容块
        参数：
            context - 聊天上下文
            chunk - 内容块
        """
        context.add_stream_chunk(chunk)

    async def on_error(self, context: ChatContext, error: Exception) -> None:
        """
        函数级注释：处理错误
        参数：
            context - 聊天上下文
            error - 错误对象
        """
        context.error = str(error)
        logger.error(f"状态 {self.name} 发生错误: {str(error)}")


class IdleState(ChatState):
    """
    类级注释：空闲状态
    内部逻辑：等待用户输入的初始状态
    设计模式：状态模式 - 具体状态
    """

    state_type = ChatStateType.IDLE

    async def handle_event(
        self,
        event: StateTransitionEvent,
        context: ChatContext
    ) -> Optional[ChatStateType]:
        """
        函数级注释：处理事件
        内部逻辑：用户消息 -> 处理中
        """
        if event == StateTransitionEvent.USER_MESSAGE:
            return ChatStateType.PROCESSING
        elif event == StateTransitionEvent.REQUEST_CONFIRMATION:
            return ChatStateType.AWAITING_CONFIRMATION
        return None


class ProcessingState(ChatState):
    """
    类级注释：处理中状态
    内部逻辑：正在生成回复
    设计模式：状态模式 - 具体状态
    """

    state_type = ChatStateType.PROCESSING

    async def handle_event(
        self,
        event: StateTransitionEvent,
        context: ChatContext
    ) -> Optional[ChatStateType]:
        """
        函数级注释：处理事件
        内部逻辑：开始流式 -> 流式中 / 完成 -> 已完成 / 错误 -> 错误
        """
        if event == StateTransitionEvent.START_STREAMING:
            return ChatStateType.STREAMING
        elif event == StateTransitionEvent.GENERATION_COMPLETE:
            return ChatStateType.COMPLETED
        elif event == StateTransitionEvent.ERROR_OCCURRED:
            return ChatStateType.ERROR
        elif event == StateTransitionEvent.USER_CANCEL:
            return ChatStateType.CANCELLED
        return None


class StreamingState(ChatState):
    """
    类级注释：流式输出状态
    内部逻辑：正在流式输出回复内容
    设计模式：状态模式 - 具体状态
    """

    state_type = ChatStateType.STREAMING

    async def handle_event(
        self,
        event: StateTransitionEvent,
        context: ChatContext
    ) -> Optional[ChatStateType]:
        """
        函数级注释：处理事件
        内部逻辑：流式完成 -> 已完成 / 错误 -> 错误 / 取消 -> 已取消
        """
        if event == StateTransitionEvent.STREAM_COMPLETE:
            # 内部逻辑：设置累积的内容
            context.assistant_response = context.get_stream_content()
            return ChatStateType.COMPLETED
        elif event == StateTransitionEvent.ERROR_OCCURRED:
            return ChatStateType.ERROR
        elif event == StateTransitionEvent.USER_CANCEL:
            return ChatStateType.CANCELLED
        return None


class AwaitingConfirmationState(ChatState):
    """
    类级注释：等待确认状态
    内部逻辑：等待用户确认某项操作
    设计模式：状态模式 - 具体状态
    """

    state_type = ChatStateType.AWAITING_CONFIRMATION

    async def handle_event(
        self,
        event: StateTransitionEvent,
        context: ChatContext
    ) -> Optional[ChatStateType]:
        """
        函数级注释：处理事件
        内部逻辑：用户确认 -> 处理中 / 拒绝 -> 空闲
        """
        if event == StateTransitionEvent.USER_CONFIRMED:
            return ChatStateType.PROCESSING
        elif event == StateTransitionEvent.USER_DECLINED:
            return ChatStateType.IDLE
        elif event == StateTransitionEvent.RESET:
            return ChatStateType.IDLE
        return None


class ErrorState(ChatState):
    """
    类级注释：错误状态
    内部逻辑：处理错误情况
    设计模式：状态模式 - 具体状态
    """

    state_type = ChatStateType.ERROR

    async def enter(self, context: ChatContext) -> None:
        """
        函数级注释：进入错误状态
        内部逻辑：记录错误日志
        """
        await super().enter(context)
        logger.error(f"进入错误状态: {context.error}")

    async def handle_event(
        self,
        event: StateTransitionEvent,
        context: ChatContext
    ) -> Optional[ChatStateType]:
        """
        函数级注释：处理事件
        内部逻辑：重置 -> 空闲 / 用户消息 -> 处理中（重试）
        """
        if event == StateTransitionEvent.RESET:
            context.error = None
            return ChatStateType.IDLE
        elif event == StateTransitionEvent.USER_MESSAGE:
            # 内部逻辑：清除错误，重试
            context.error = None
            return ChatStateType.PROCESSING
        return None


class CompletedState(ChatState):
    """
    类级注释：已完成状态
    内部逻辑：对话回合完成
    设计模式：状态模式 - 具体状态
    """

    state_type = ChatStateType.COMPLETED

    async def handle_event(
        self,
        event: StateTransitionEvent,
        context: ChatContext
    ) -> Optional[ChatStateType]:
        """
        函数级注释：处理事件
        内部逻辑：用户消息 -> 处理中 / 重置 -> 空闲
        """
        if event == StateTransitionEvent.USER_MESSAGE:
            return ChatStateType.PROCESSING
        elif event == StateTransitionEvent.RESET:
            return ChatStateType.IDLE
        return None


class CancelledState(ChatState):
    """
    类级注释：已取消状态
    内部逻辑：用户取消了当前操作
    设计模式：状态模式 - 具体状态
    """

    state_type = ChatStateType.CANCELLED

    async def handle_event(
        self,
        event: StateTransitionEvent,
        context: ChatContext
    ) -> Optional[ChatStateType]:
        """
        函数级注释：处理事件
        内部逻辑：用户消息 -> 处理中 / 重置 -> 空闲
        """
        if event == StateTransitionEvent.USER_MESSAGE:
            return ChatStateType.PROCESSING
        elif event == StateTransitionEvent.RESET:
            return ChatStateType.IDLE
        return None


class ChatStateMachine:
    """
    类级注释：聊天状态机
    内部逻辑：管理对话状态的转换
    设计模式：状态模式 - 状态上下文
    职责：
        1. 管理当前状态
        2. 处理状态转换
        3. 维护转换历史
        4. 提供状态查询接口
    """

    # 内部变量：状态类型到状态类的映射
    _state_classes: Dict[ChatStateType, Type[ChatState]] = {
        ChatStateType.IDLE: IdleState,
        ChatStateType.PROCESSING: ProcessingState,
        ChatStateType.STREAMING: StreamingState,
        ChatStateType.AWAITING_CONFIRMATION: AwaitingConfirmationState,
        ChatStateType.ERROR: ErrorState,
        ChatStateType.COMPLETED: CompletedState,
        ChatStateType.CANCELLED: CancelledState,
    }

    # 内部变量：允许的状态转换 (from_state, event) -> to_state
    _allowed_transitions: Dict[tuple, ChatStateType] = {
        # 空闲状态的转换
        (ChatStateType.IDLE, StateTransitionEvent.USER_MESSAGE): ChatStateType.PROCESSING,
        (ChatStateType.IDLE, StateTransitionEvent.REQUEST_CONFIRMATION): ChatStateType.AWAITING_CONFIRMATION,

        # 处理中状态的转换
        (ChatStateType.PROCESSING, StateTransitionEvent.START_STREAMING): ChatStateType.STREAMING,
        (ChatStateType.PROCESSING, StateTransitionEvent.GENERATION_COMPLETE): ChatStateType.COMPLETED,
        (ChatStateType.PROCESSING, StateTransitionEvent.ERROR_OCCURRED): ChatStateType.ERROR,
        (ChatStateType.PROCESSING, StateTransitionEvent.USER_CANCEL): ChatStateType.CANCELLED,

        # 流式状态的转换
        (ChatStateType.STREAMING, StateTransitionEvent.STREAM_COMPLETE): ChatStateType.COMPLETED,
        (ChatStateType.STREAMING, StateTransitionEvent.ERROR_OCCURRED): ChatStateType.ERROR,
        (ChatStateType.STREAMING, StateTransitionEvent.USER_CANCEL): ChatStateType.CANCELLED,

        # 等待确认状态的转换
        (ChatStateType.AWAITING_CONFIRMATION, StateTransitionEvent.USER_CONFIRMED): ChatStateType.PROCESSING,
        (ChatStateType.AWAITING_CONFIRMATION, StateTransitionEvent.USER_DECLINED): ChatStateType.IDLE,
        (ChatStateType.AWAITING_CONFIRMATION, StateTransitionEvent.RESET): ChatStateType.IDLE,

        # 错误状态的转换
        (ChatStateType.ERROR, StateTransitionEvent.RESET): ChatStateType.IDLE,
        (ChatStateType.ERROR, StateTransitionEvent.USER_MESSAGE): ChatStateType.PROCESSING,

        # 完成状态的转换
        (ChatStateType.COMPLETED, StateTransitionEvent.USER_MESSAGE): ChatStateType.PROCESSING,
        (ChatStateType.COMPLETED, StateTransitionEvent.RESET): ChatStateType.IDLE,

        # 取消状态的转换
        (ChatStateType.CANCELLED, StateTransitionEvent.USER_MESSAGE): ChatStateType.PROCESSING,
        (ChatStateType.CANCELLED, StateTransitionEvent.RESET): ChatStateType.IDLE,
    }

    def __init__(self, conversation_id: Optional[str] = None):
        """
        函数级注释：初始化状态机
        参数：
            conversation_id - 会话 ID
        """
        # 内部变量：会话 ID
        self._conversation_id = conversation_id

        # 内部变量：当前状态
        self._current_state: ChatState = self._create_state(ChatStateType.IDLE)

        # 内部变量：上下文
        self._context = ChatContext(conversation_id=conversation_id)

        # 内部变量：转换历史
        self._transition_history: List[StateTransition] = []

        # 内部变量：状态进入/离开回调
        self._state_callbacks: Dict[str, List[Callable]] = {
            "on_enter": [],
            "on_exit": [],
            "on_transition": []
        }

        # 内部变量：统计信息
        self._stats = {
            "total_transitions": 0,
            "state_durations": {},
            "error_count": 0
        }

        # 内部变量：状态进入时间
        self._state_enter_time: Optional[datetime] = None

        logger.info(f"聊天状态机初始化完成: conversation_id={conversation_id}")

    def _create_state(self, state_type: ChatStateType) -> ChatState:
        """
        函数级注释：创建状态实例
        参数：
            state_type - 状态类型
        返回值：状态实例
        """
        state_class = self._state_classes.get(state_type, IdleState)
        return state_class(self)

    async def transition_to(
        self,
        event: StateTransitionEvent,
        context_update: Optional[Dict[str, Any]] = None
    ) -> ChatStateType:
        """
        函数级注释：执行状态转换
        内部逻辑：检查是否允许转换 -> 离开当前状态 -> 进入新状态
        参数：
            event - 触发事件
            context_update - 上下文更新
        返回值：新状态类型
        """
        old_state = self._current_state.state_type
        transition_key = (old_state, event)

        # 内部逻辑：检查是否允许转换
        if transition_key not in self._allowed_transitions:
            logger.warning(
                f"不允许的状态转换: {old_state.value} -> {event.value}"
            )
            return old_state

        new_state_type = self._allowed_transitions[transition_key]

        # 内部逻辑：更新上下文
        if context_update:
            for key, value in context_update.items():
                setattr(self._context, key, value)

        # 内部逻辑：离开当前状态
        await self._current_state.exit(self._context)
        await self._notify_callbacks("on_exit", old_state, new_state_type)

        # 内部逻辑：计算状态持续时间
        if self._state_enter_time:
            duration = (datetime.now() - self._state_enter_time).total_seconds()
            state_name = old_state.value
            if state_name not in self._stats["state_durations"]:
                self._stats["state_durations"][state_name] = []
            self._stats["state_durations"][state_name].append(duration)

        # 内部逻辑：创建并进入新状态
        self._current_state = self._create_state(new_state_type)
        self._state_enter_time = datetime.now()
        await self._current_state.enter(self._context)
        await self._notify_callbacks("on_enter", old_state, new_state_type)

        # 内部逻辑：记录转换
        transition = StateTransition(
            from_state=old_state,
            to_state=new_state_type,
            event=event
        )
        self._transition_history.append(transition)
        self._stats["total_transitions"] += 1

        # 内部逻辑：通知转换回调
        await self._notify_callbacks("on_transition", transition)

        logger.info(
            f"状态转换: {old_state.value} -> {new_state_type.value} "
            f"(事件: {event.value})"
        )

        return new_state_type

    @property
    def current_state(self) -> ChatStateType:
        """
        函数级注释：获取当前状态
        返回值：当前状态类型
        """
        return self._current_state.state_type

    @property
    def context(self) -> ChatContext:
        """
        函数级注释：获取上下文
        返回值：聊天上下文
        """
        return self._context

    async def send_event(
        self,
        event: StateTransitionEvent,
        **kwargs
    ) -> ChatStateType:
        """
        函数级注释：发送事件到当前状态
        内部逻辑：当前状态处理事件 -> 如需转换则转换
        参数：
            event - 事件
            **kwargs - 额外参数
        返回值：新状态类型
        """
        # 内部逻辑：更新上下文参数
        if kwargs:
            self._context.params.update(kwargs)

        # 内部逻辑：让当前状态处理事件
        target_state = await self._current_state.handle_event(event, self._context)

        # 内部逻辑：如果状态建议转换，执行转换
        if target_state:
            return await self.transition_to(event)

        return self._current_state.state_type

    async def send_message(self, message: str) -> ChatStateType:
        """
        函数级注释：发送用户消息
        参数：
            message - 用户消息
        返回值：新状态类型
        """
        self._context.user_message = message
        self._context.history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        return await self.send_event(StateTransitionEvent.USER_MESSAGE)

    async def send_stream_chunk(self, chunk: str) -> None:
        """
        函数级注释：发送流式内容块
        参数：
            chunk - 内容块
        """
        await self._current_state.on_stream_chunk(self._context, chunk)

    async def send_error(self, error: Exception) -> ChatStateType:
        """
        函数级注释：报告错误
        参数：
            error - 错误对象
        返回值：新状态类型
        """
        await self._current_state.on_error(self._context, error)
        self._stats["error_count"] += 1
        return await self.send_event(StateTransitionEvent.ERROR_OCCURRED)

    async def reset(self) -> ChatStateType:
        """
        函数级注释：重置状态机
        返回值：新状态类型（应该是 IDLE）
        """
        return await self.transition_to(StateTransitionEvent.RESET)

    def register_callback(
        self,
        callback_type: str,
        callback: Callable
    ) -> None:
        """
        函数级注释：注册回调函数
        参数：
            callback_type - 回调类型 (on_enter, on_exit, on_transition)
            callback - 回调函数
        """
        if callback_type in self._state_callbacks:
            self._state_callbacks[callback_type].append(callback)
            logger.debug(f"注册 {callback_type} 回调")

    async def _notify_callbacks(
        self,
        callback_type: str,
        *args
    ) -> None:
        """
        函数级注释：通知回调函数
        参数：
            callback_type - 回调类型
            *args - 回调参数
        """
        for callback in self._state_callbacks.get(callback_type, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(*args)
                else:
                    callback(*args)
            except Exception as e:
                logger.error(f"回调执行失败 ({callback_type}): {str(e)}")

    def get_transition_history(
        self,
        limit: int = 50
    ) -> List[StateTransition]:
        """
        函数级注释：获取转换历史
        参数：
            limit - 最大返回条数
        返回值：转换记录列表
        """
        return self._transition_history[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """
        函数级注释：获取统计信息
        返回值：统计信息字典
        """
        stats = self._stats.copy()

        # 内部逻辑：计算平均状态持续时间
        avg_durations = {}
        for state, durations in stats["state_durations"].items():
            if durations:
                avg_durations[state] = sum(durations) / len(durations)

        stats["average_state_durations"] = avg_durations
        stats["current_state"] = self._current_state.state_type.value
        stats["history_length"] = len(self._transition_history)

        return stats


class ChatStateMachineFactory:
    """
    类级注释：聊天状态机工厂
    内部逻辑：管理和创建状态机实例
    设计模式：工厂模式 + 对象池模式
    """

    # 内部变量：状态机池
    _machines: Dict[str, ChatStateMachine] = {}

    @classmethod
    def create(
        cls,
        conversation_id: Optional[str] = None
    ) -> ChatStateMachine:
        """
        函数级注释：创建状态机
        参数：
            conversation_id - 会话 ID
        返回值：状态机实例
        """
        machine = ChatStateMachine(conversation_id)

        if conversation_id:
            cls._machines[conversation_id] = machine
            logger.debug(f"创建并注册状态机: {conversation_id}")

        return machine

    @classmethod
    def get(cls, conversation_id: str) -> Optional[ChatStateMachine]:
        """
        函数级注释：获取已存在的状态机
        参数：
            conversation_id - 会话 ID
        返回值：状态机实例或 None
        """
        return cls._machines.get(conversation_id)

    @classmethod
    def remove(cls, conversation_id: str) -> None:
        """
        函数级注释：移除状态机
        参数：
            conversation_id - 会话 ID
        """
        cls._machines.pop(conversation_id, None)
        logger.debug(f"移除状态机: {conversation_id}")

    @classmethod
    def clear_all(cls) -> None:
        """
        函数级注释：清空所有状态机
        """
        cls._machines.clear()
        logger.info("清空所有聊天状态机")


# 内部变量：导出所有公共接口
__all__ = [
    'ChatStateType',
    'StateTransitionEvent',
    'StateTransition',
    'ChatContext',
    'ChatState',
    'ChatStateMachine',
    'ChatStateMachineFactory',
    'IdleState',
    'ProcessingState',
    'StreamingState',
    'AwaitingConfirmationState',
    'ErrorState',
    'CompletedState',
    'CancelledState',
]
