# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：观察者模式实现模块
内部逻辑：定义观察者模式的核心接口
设计模式：观察者模式（Observer Pattern）
设计原则：SOLID - 依赖倒置原则、开闭原则

使用场景：
    - 配置变更通知
    - 任务状态更新
    - 事件驱动的业务流程
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from loguru import logger
import threading
import asyncio


class EventType(str, Enum):
    """
    类级注释：事件类型枚举
    职责：定义系统中的事件类型
    """
    # 配置事件
    CONFIG_CHANGED = "config_changed"
    CONFIG_RELOADED = "config_reloaded"

    # 文档事件
    DOCUMENT_ADDED = "document_added"
    DOCUMENT_UPDATED = "document_updated"
    DOCUMENT_DELETED = "document_deleted"

    # 任务事件
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"

    # 聊天事件
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    CONVERSATION_STARTED = "conversation_started"
    CONVERSATION_ENDED = "conversation_ended"

    # 系统事件
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    ERROR_OCCURRED = "error_occurred"


@dataclass
class Event:
    """
    类级注释：事件数据类
    职责：封装事件携带的数据
    """
    type: EventType  # 事件类型
    source: str  # 事件源
    data: Dict[str, Any] = field(default_factory=dict)  # 事件数据
    timestamp: datetime = field(default_factory=datetime.now)  # 事件时间
    event_id: Optional[str] = None  # 事件ID

    def __post_init__(self):
        """初始化后生成事件ID"""
        if not self.event_id:
            self.event_id = f"{self.type.value}_{self.timestamp.timestamp()}"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "event_id": self.event_id,
            "type": self.type.value,
            "source": self.source,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        }


class Observer(ABC):
    """
    类级注释：观察者抽象基类
    设计模式：观察者模式（Observer Pattern）- 观察者接口
    职责：定义观察者的更新接口

    设计优势：
        - 解耦主题和观察者
        - 支持多个观察者
        - 易于扩展新的观察者
    """

    @abstractmethod
    def update(self, event: Event) -> None:
        """
        函数级注释：接收事件通知
        参数：
            event: 事件对象
        """
        pass

    @abstractmethod
    def get_interests(self) -> List[EventType]:
        """
        函数级注释：获取感兴趣的事件类型
        返回值：事件类型列表
        """
        pass


class Subject(ABC):
    """
    类级注释：主题抽象基类
    设计模式：观察者模式（Observer Pattern）- 主题接口
    职责：定义注册、移除、通知观察者的接口
    """

    @abstractmethod
    def attach(self, observer: Observer) -> None:
        """
        函数级注释：附加观察者
        参数：
            observer: 观察者对象
        """
        pass

    @abstractmethod
    def detach(self, observer: Observer) -> None:
        """
        函数级注释：分离观察者
        参数：
            observer: 观察者对象
        """
        pass

    @abstractmethod
    def notify(self, event: Event) -> None:
        """
        函数级注释：通知所有观察者
        参数：
            event: 事件对象
        """
        pass


class EventBus(Subject):
    """
    类级注释：事件总线
    设计模式：观察者模式 + 单例模式
    职责：
        1. 管理所有观察者
        2. 分发事件到感兴趣的观察者
        3. 支持同步和异步通知

    设计优势：
        - 集中式事件管理
        - 观察者自动过滤事件
        - 线程安全
    """

    _instance: Optional["EventBus"] = None
    _lock = threading.Lock()

    def __new__(cls):
        """实现线程安全的单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初始化事件总线"""
        if self._initialized:
            return

        self._initialized = True
        # 内部变量：观察者列表
        self._observers: List[Observer] = []
        # 内部变量：事件历史（可选）
        self._event_history: List[Event] = []
        self._max_history = 1000

        logger.info("事件总线初始化完成")

    def attach(self, observer: Observer) -> None:
        """
        函数级注释：附加观察者
        参数：
            observer: 观察者对象
        """
        if observer not in self._observers:
            self._observers.append(observer)
            logger.debug(f"附加观察者: {observer.__class__.__name__}")

    def detach(self, observer: Observer) -> None:
        """
        函数级注释：分离观察者
        参数：
            observer: 观察者对象
        """
        if observer in self._observers:
            self._observers.remove(observer)
            logger.debug(f"分离观察者: {observer.__class__.__name__}")

    def notify(self, event: Event) -> None:
        """
        函数级注释：同步通知所有观察者
        参数：
            event: 事件对象
        """
        # 内部逻辑：记录事件历史
        self._add_to_history(event)

        # 内部逻辑：通知感兴趣的观察者
        for observer in self._observers:
            interests = observer.get_interests()
            if event.type in interests:
                try:
                    observer.update(event)
                except Exception as e:
                    logger.error(f"观察者 {observer.__class__.__name__} 处理事件失败: {e}")

    async def notify_async(self, event: Event) -> None:
        """
        函数级注释：异步通知所有观察者
        参数：
            event: 事件对象
        """
        # 内部逻辑：记录事件历史
        self._add_to_history(event)

        # 内部逻辑：创建异步任务
        tasks = []
        for observer in self._observers:
            interests = observer.get_interests()
            if event.type in interests:
                tasks.append(self._notify_observer_async(observer, event))

        # 内部逻辑：并发执行
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _notify_observer_async(self, observer: Observer, event: Event) -> None:
        """
        函数级注释：异步通知单个观察者
        参数：
            observer: 观察者
            event: 事件
        @private
        """
        try:
            # 内部逻辑：检查是否有异步更新方法
            if hasattr(observer, 'update_async'):
                await observer.update_async(event)
            else:
                observer.update(event)
        except Exception as e:
            logger.error(f"观察者 {observer.__class__.__name__} 异步处理事件失败: {e}")

    def _add_to_history(self, event: Event) -> None:
        """
        函数级注释：添加事件到历史记录
        参数：
            event: 事件对象
        @private
        """
        self._event_history.append(event)
        # 内部逻辑：限制历史记录大小
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]

    def get_event_history(
        self,
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[Event]:
        """
        函数级注释：获取事件历史
        参数：
            event_type: 事件类型过滤
            limit: 返回数量限制
        返回值：事件列表
        """
        history = self._event_history

        # 内部逻辑：类型过滤
        if event_type:
            history = [e for e in history if e.type == event_type]

        # 内部逻辑：限制数量
        return history[-limit:]

    def clear_history(self) -> None:
        """清空事件历史"""
        self._event_history.clear()
        logger.debug("事件历史已清空")

    def get_observer_count(self) -> int:
        """
        函数级注释：获取观察者数量
        返回值：观察者数量
        """
        return len(self._observers)

    def clear_observers(self) -> None:
        """
        函数级注释：清空所有观察者
        内部逻辑：主要用于测试环境
        """
        self._observers.clear()
        logger.debug("已清空所有观察者")

    @classmethod
    def reset(cls) -> None:
        """
        函数级注释：重置单例
        内部逻辑：主要用于测试环境，清除单例实例
        """
        cls._instance = None
        logger.debug("事件总线单例已重置")


class FunctionObserver(Observer):
    """
    类级注释：函数观察者
    设计模式：观察者模式 - 适配器模式
    职责：将函数包装为观察者

    设计优势：
        - 快速创建观察者
        - 无需定义类
        - 灵活的回调机制
    """

    def __init__(
        self,
        callback: Callable[[Event], None],
        interests: List[EventType],
        name: str = "FunctionObserver"
    ):
        """
        函数级注释：初始化函数观察者
        参数：
            callback: 回调函数
            interests: 感兴趣的事件类型
            name: 观察者名称
        """
        self._callback = callback
        self._interests = interests
        self._name = name

    def update(self, event: Event) -> None:
        """接收事件通知"""
        self._callback(event)

    def get_interests(self) -> List[EventType]:
        """获取感兴趣的事件类型"""
        return self._interests

    @property
    def name(self) -> str:
        """获取观察者名称"""
        return self._name


class AsyncFunctionObserver(Observer):
    """
    类级注释：异步函数观察者
    设计模式：观察者模式 - 适配器模式
    职责：将异步函数包装为观察者
    """

    def __init__(
        self,
        callback: Callable[[Event], Any],  # 可以是协程函数
        interests: List[EventType],
        name: str = "AsyncFunctionObserver"
    ):
        """
        函数级注释：初始化异步函数观察者
        参数：
            callback: 回调函数（协程或普通函数）
            interests: 感兴趣的事件类型
            name: 观察者名称
        """
        self._callback = callback
        self._interests = interests
        self._name = name

    def update(self, event: Event) -> None:
        """接收事件通知（同步调用）"""
        result = self._callback(event)
        # 内部逻辑：如果是协程，尝试在当前循环中创建任务
        if asyncio.iscoroutine(result):
            try:
                loop = asyncio.get_running_loop()
                asyncio.create_task(result)
            except RuntimeError:
                # 内部逻辑：没有运行中的事件循环，忽略异步回调
                logger.debug("无事件循环，跳过异步回调执行")

    async def update_async(self, event: Event) -> None:
        """异步接收事件通知"""
        result = self._callback(event)
        if asyncio.iscoroutine(result):
            await result

    async def update_async(self, event: Event) -> None:
        """异步接收事件通知"""
        result = self._callback(event)
        if asyncio.iscoroutine(result):
            await result

    def get_interests(self) -> List[EventType]:
        """获取感兴趣的事件类型"""
        return self._interests

    @property
    def name(self) -> str:
        """获取观察者名称"""
        return self._name


class FilterObserver(Observer):
    """
    类级注释：过滤观察者装饰器
    设计模式：装饰器模式 + 观察者模式
    职责：根据条件过滤事件

    设计优势：
        - 灵活的事件过滤
        - 组合多个条件
        - 不修改原观察者
    """

    def __init__(
        self,
        wrapped_observer: Observer,
        predicate: Callable[[Event], bool]
    ):
        """
        函数级注释：初始化过滤观察者
        参数：
            wrapped_observer: 被装饰的观察者
            predicate: 谓词函数，返回True则传递事件
        """
        self._wrapped = wrapped_observer
        self._predicate = predicate

    def update(self, event: Event) -> None:
        """接收事件通知（带过滤）"""
        if self._predicate(event):
            self._wrapped.update(event)

    def get_interests(self) -> List[EventType]:
        """获取感兴趣的事件类型"""
        return self._wrapped.get_interests()


# 内部变量：全局事件总线实例
event_bus = EventBus()


# 便捷函数
def subscribe(
    interests: List[EventType],
    callback: Callable[[Event], None],
    async_mode: bool = False,
    name: str = "Subscriber"
) -> Observer:
    """
    函数级注释：订阅事件
    参数：
        interests: 感兴趣的事件类型
        callback: 回调函数
        async_mode: 是否为异步模式
        name: 订阅者名称
    返回值：观察者对象
    """
    if async_mode:
        observer = AsyncFunctionObserver(callback, interests, name)
    else:
        observer = FunctionObserver(callback, interests, name)

    event_bus.attach(observer)
    return observer


def unsubscribe(observer: Observer) -> None:
    """
    函数级注释：取消订阅
    参数：
        observer: 观察者对象
    """
    event_bus.detach(observer)


def publish(event_type: EventType, source: str, data: Dict[str, Any]) -> None:
    """
    函数级注释：发布事件
    参数：
        event_type: 事件类型
        source: 事件源
        data: 事件数据
    """
    event = Event(type=event_type, source=source, data=data)
    event_bus.notify(event)


async def publish_async(event_type: EventType, source: str, data: Dict[str, Any]) -> None:
    """
    函数级注释：异步发布事件
    参数：
        event_type: 事件类型
        source: 事件源
        data: 事件数据
    """
    event = Event(type=event_type, source=source, data=data)
    await event_bus.notify_async(event)


# 内部变量：导出公共接口
__all__ = [
    'EventType',
    'Event',
    'Observer',
    'Subject',
    'EventBus',
    'FunctionObserver',
    'AsyncFunctionObserver',
    'FilterObserver',
    'event_bus',
    'subscribe',
    'unsubscribe',
    'publish',
    'publish_async',
]
