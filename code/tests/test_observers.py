# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：观察者模式模块测试
内部逻辑：验证事件总线、观察者、发布订阅等功能
设计模式：观察者模式（Observer Pattern）
测试覆盖范围：
    - EventType: 事件类型枚举
    - Event: 事件数据类
    - Observer: 观察者抽象基类
    - Subject: 主题抽象基类
    - EventBus: 事件总线（单例模式）
    - FunctionObserver: 函数观察者
    - AsyncFunctionObserver: 异步函数观察者
    - FilterObserver: 过滤观察者
    - subscribe/unsubscribe: 订阅/取消订阅函数
    - publish/publish_async: 发布函数
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from datetime import datetime
from typing import List

from app.core.observers.observer import (
    EventType,
    Event,
    Observer,
    Subject,
    EventBus,
    FunctionObserver,
    AsyncFunctionObserver,
    FilterObserver,
    event_bus,
    subscribe,
    unsubscribe,
    publish,
    publish_async,
)


# ============================================================================
# 测试固件
# ============================================================================

@pytest.fixture(autouse=True)
def reset_event_bus():
    """每个测试前重置事件总线"""
    # 重置单例并清空全局实例的观察者
    EventBus.reset()
    # 重新初始化全局 event_bus
    global event_bus
    from app.core.observers.observer import event_bus as global_event_bus
    global_event_bus._observers.clear()
    global_event_bus._event_history.clear()
    yield
    # 测试后再次清理
    EventBus.reset()
    global event_bus
    from app.core.observers.observer import event_bus as global_event_bus
    global_event_bus._observers.clear()
    global_event_bus._event_history.clear()


class ConcreteObserver(Observer):
    """具体观察者实现（用于测试）"""

    def __init__(self, interests: List[EventType]):
        self._interests = interests
        self.received_events = []

    def update(self, event: Event) -> None:
        self.received_events.append(event)

    def get_interests(self) -> List[EventType]:
        return self._interests


# ============================================================================
# EventType 测试
# ============================================================================

class TestEventType:
    """测试事件类型枚举"""

    def test_config_events(self):
        """测试配置事件类型"""
        assert EventType.CONFIG_CHANGED == "config_changed"
        assert EventType.CONFIG_RELOADED == "config_reloaded"

    def test_document_events(self):
        """测试文档事件类型"""
        assert EventType.DOCUMENT_ADDED == "document_added"
        assert EventType.DOCUMENT_UPDATED == "document_updated"
        assert EventType.DOCUMENT_DELETED == "document_deleted"

    def test_task_events(self):
        """测试任务事件类型"""
        assert EventType.TASK_CREATED == "task_created"
        assert EventType.TASK_STARTED == "task_started"
        assert EventType.TASK_PROGRESS == "task_progress"
        assert EventType.TASK_COMPLETED == "task_completed"
        assert EventType.TASK_FAILED == "task_failed"

    def test_chat_events(self):
        """测试聊天事件类型"""
        assert EventType.MESSAGE_SENT == "message_sent"
        assert EventType.MESSAGE_RECEIVED == "message_received"
        assert EventType.CONVERSATION_STARTED == "conversation_started"
        assert EventType.CONVERSATION_ENDED == "conversation_ended"

    def test_system_events(self):
        """测试系统事件类型"""
        assert EventType.SYSTEM_STARTUP == "system_startup"
        assert EventType.SYSTEM_SHUTDOWN == "system_shutdown"
        assert EventType.ERROR_OCCURRED == "error_occurred"


# ============================================================================
# Event 测试
# ============================================================================

class TestEvent:
    """测试事件数据类"""

    def test_init_with_all_params(self):
        """测试完整参数初始化"""
        event = Event(
            type=EventType.CONFIG_CHANGED,
            source="test_source",
            data={"key": "value"}
        )

        assert event.type == EventType.CONFIG_CHANGED
        assert event.source == "test_source"
        assert event.data == {"key": "value"}

    def test_event_id_generation(self):
        """测试事件ID自动生成"""
        event = Event(
            type=EventType.DOCUMENT_ADDED,
            source="test"
        )

        assert event.event_id is not None
        assert EventType.DOCUMENT_ADDED.value in event.event_id

    def test_custom_event_id(self):
        """测试自定义事件ID"""
        custom_id = "custom_event_123"
        event = Event(
            type=EventType.TASK_COMPLETED,
            source="test",
            event_id=custom_id
        )

        assert event.event_id == custom_id

    def test_to_dict(self):
        """测试转换为字典"""
        event = Event(
            type=EventType.MESSAGE_SENT,
            source="chat_service",
            data={"message": "hello"}
        )

        result = event.to_dict()
        assert "event_id" in result
        assert result["type"] == "message_sent"
        assert result["source"] == "chat_service"
        assert result["data"] == {"message": "hello"}
        assert "timestamp" in result

    def test_timestamp_auto_generation(self):
        """测试时间戳自动生成"""
        before = datetime.now()
        event = Event(type=EventType.ERROR_OCCURRED, source="test")
        after = datetime.now()

        assert event.timestamp >= before
        assert event.timestamp <= after


# ============================================================================
# EventBus 测试
# ============================================================================

class TestEventBus:
    """测试事件总线"""

    def test_singleton_pattern(self):
        """测试单例模式"""
        bus1 = EventBus()
        bus2 = EventBus()
        assert bus1 is bus2

    def test_attach_observer(self):
        """测试附加观察者"""
        bus = EventBus()
        observer = ConcreteObserver([EventType.CONFIG_CHANGED])

        bus.attach(observer)

        assert bus.get_observer_count() == 1

    def test_detach_observer(self):
        """测试分离观察者"""
        bus = EventBus()
        observer = ConcreteObserver([EventType.CONFIG_CHANGED])

        bus.attach(observer)
        assert bus.get_observer_count() == 1

        bus.detach(observer)
        assert bus.get_observer_count() == 0

    def test_detach_non_attached_observer(self):
        """测试分离未附加的观察者"""
        bus = EventBus()
        observer = ConcreteObserver([EventType.CONFIG_CHANGED])

        # 不应抛出异常
        bus.detach(observer)
        assert bus.get_observer_count() == 0

    def test_notify_interested_observers(self):
        """测试通知感兴趣的观察者"""
        bus = EventBus()
        observer1 = ConcreteObserver([EventType.CONFIG_CHANGED])
        observer2 = ConcreteObserver([EventType.DOCUMENT_ADDED])

        bus.attach(observer1)
        bus.attach(observer2)

        event = Event(type=EventType.CONFIG_CHANGED, source="test")
        bus.notify(event)

        assert len(observer1.received_events) == 1
        assert len(observer2.received_events) == 0

    def test_notify_all_observers(self):
        """测试通知所有观察者（通用兴趣）"""
        bus = EventBus()
        observer1 = ConcreteObserver([EventType.CONFIG_CHANGED, EventType.DOCUMENT_ADDED])
        observer2 = ConcreteObserver([EventType.DOCUMENT_ADDED])

        bus.attach(observer1)
        bus.attach(observer2)

        event = Event(type=EventType.DOCUMENT_ADDED, source="test")
        bus.notify(event)

        assert len(observer1.received_events) == 1
        assert len(observer2.received_events) == 1

    def test_notify_with_observer_exception(self):
        """测试观察者异常处理"""
        bus = EventBus()

        class BrokenObserver(Observer):
            def get_interests(self):
                return [EventType.CONFIG_CHANGED]

            def update(self, event):
                raise ValueError("测试错误")

        observer = BrokenObserver()
        bus.attach(observer)

        # 不应抛出异常
        event = Event(type=EventType.CONFIG_CHANGED, source="test")
        bus.notify(event)

    def test_event_history_recording(self):
        """测试事件历史记录"""
        bus = EventBus()
        observer = ConcreteObserver([EventType.CONFIG_CHANGED])
        bus.attach(observer)

        event1 = Event(type=EventType.CONFIG_CHANGED, source="test1")
        event2 = Event(type=EventType.DOCUMENT_ADDED, source="test2")

        bus.notify(event1)
        bus.notify(event2)

        history = bus.get_event_history()
        assert len(history) == 2

    def test_event_history_with_type_filter(self):
        """测试按类型过滤事件历史"""
        bus = EventBus()
        observer = ConcreteObserver([EventType.CONFIG_CHANGED])
        bus.attach(observer)

        bus.notify(Event(type=EventType.CONFIG_CHANGED, source="test1"))
        bus.notify(Event(type=EventType.DOCUMENT_ADDED, source="test2"))
        bus.notify(Event(type=EventType.CONFIG_CHANGED, source="test3"))

        config_history = bus.get_event_history(event_type=EventType.CONFIG_CHANGED)
        assert len(config_history) == 2

    def test_event_history_limit(self):
        """测试事件历史数量限制"""
        bus = EventBus()
        observer = ConcreteObserver([EventType.CONFIG_CHANGED])
        bus.attach(observer)

        for i in range(10):
            bus.notify(Event(type=EventType.CONFIG_CHANGED, source=f"test{i}"))

        history = bus.get_event_history(limit=5)
        assert len(history) == 5

    def test_clear_history(self):
        """测试清空事件历史"""
        bus = EventBus()
        observer = ConcreteObserver([EventType.CONFIG_CHANGED])
        bus.attach(observer)

        bus.notify(Event(type=EventType.CONFIG_CHANGED, source="test"))
        assert len(bus.get_event_history()) == 1

        bus.clear_history()
        assert len(bus.get_event_history()) == 0

    def test_max_history_limit(self):
        """测试最大历史记录限制"""
        bus = EventBus()
        observer = ConcreteObserver([EventType.CONFIG_CHANGED])
        bus.attach(observer)

        # 超过最大历史记录（1000）- 减少循环次数避免资源消耗过大
        for i in range(1050):
            bus.notify(Event(type=EventType.CONFIG_CHANGED, source=f"test{i}"))

        history = bus.get_event_history()
        # 应该被限制在1000以内
        assert len(history) <= 1000

    @pytest.mark.asyncio
    async def test_async_notify(self):
        """测试异步通知"""
        bus = EventBus()

        class AsyncObserver(Observer):
            def __init__(self):
                self.received_events = []

            def get_interests(self):
                return [EventType.CONFIG_CHANGED]

            def update(self, event):
                self.received_events.append(event)

            async def update_async(self, event):
                self.received_events.append(event)
                await asyncio.sleep(0.01)

        observer = AsyncObserver()
        bus.attach(observer)

        event = Event(type=EventType.CONFIG_CHANGED, source="test")
        await bus.notify_async(event)

        assert len(observer.received_events) == 1

    @pytest.mark.asyncio
    async def test_async_notify_with_sync_observer(self):
        """测试异步通知同步观察者"""
        bus = EventBus()
        observer = ConcreteObserver([EventType.CONFIG_CHANGED])
        bus.attach(observer)

        event = Event(type=EventType.CONFIG_CHANGED, source="test")
        await bus.notify_async(event)

        assert len(observer.received_events) == 1


# ============================================================================
# FunctionObserver 测试
# ============================================================================

class TestFunctionObserver:
    """测试函数观察者"""

    def test_init(self):
        """测试初始化"""
        callback = Mock()
        interests = [EventType.CONFIG_CHANGED]

        observer = FunctionObserver(callback, interests, "TestObserver")

        assert observer._callback is callback
        assert observer.get_interests() == interests
        assert observer.name == "TestObserver"

    def test_default_name(self):
        """测试默认名称"""
        observer = FunctionObserver(Mock(), [])
        assert observer.name == "FunctionObserver"

    def test_update_calls_callback(self):
        """测试更新调用回调"""
        callback = Mock()
        observer = FunctionObserver(
            callback,
            [EventType.CONFIG_CHANGED],
            "TestObserver"
        )

        event = Event(type=EventType.CONFIG_CHANGED, source="test")
        observer.update(event)

        callback.assert_called_once_with(event)

    def test_get_interests(self):
        """测试获取感兴趣的事件"""
        interests = [EventType.CONFIG_CHANGED, EventType.DOCUMENT_ADDED]
        observer = FunctionObserver(Mock(), interests)

        assert observer.get_interests() == interests


# ============================================================================
# AsyncFunctionObserver 测试
# ============================================================================

class TestAsyncFunctionObserver:
    """测试异步函数观察者"""

    def test_init(self):
        """测试初始化"""
        callback = Mock()
        interests = [EventType.CONFIG_CHANGED]

        observer = AsyncFunctionObserver(callback, interests, "AsyncTestObserver")

        assert observer._callback is callback
        assert observer.get_interests() == interests
        assert observer.name == "AsyncTestObserver"

    def test_update_with_sync_callback(self):
        """测试同步回调更新"""
        callback = Mock()
        observer = AsyncFunctionObserver(callback, [EventType.CONFIG_CHANGED])

        event = Event(type=EventType.CONFIG_CHANGED, source="test")
        observer.update(event)

        callback.assert_called_once_with(event)

    def test_update_with_async_callback(self):
        """测试异步回调更新"""
        async_callback = AsyncMock()
        observer = AsyncFunctionObserver(async_callback, [EventType.CONFIG_CHANGED])

        event = Event(type=EventType.CONFIG_CHANGED, source="test")
        observer.update(event)

        async_callback.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_update_async_with_coroutine(self):
        """测试异步更新协程"""
        call_count = [0]

        async def callback(event):
            call_count[0] += 1
            await asyncio.sleep(0.01)

        observer = AsyncFunctionObserver(callback, [EventType.CONFIG_CHANGED])

        event = Event(type=EventType.CONFIG_CHANGED, source="test")
        await observer.update_async(event)

        assert call_count[0] == 1

    @pytest.mark.asyncio
    async def test_update_async_with_sync_callback(self):
        """测试异步更新使用同步回调"""
        callback = Mock()
        observer = AsyncFunctionObserver(callback, [EventType.CONFIG_CHANGED])

        event = Event(type=EventType.CONFIG_CHANGED, source="test")
        await observer.update_async(event)

        callback.assert_called_once()


# ============================================================================
# FilterObserver 测试
# ============================================================================

class TestFilterObserver:
    """测试过滤观察者"""

    def test_init(self):
        """测试初始化"""
        wrapped = ConcreteObserver([EventType.CONFIG_CHANGED])
        predicate = Mock(return_value=True)

        observer = FilterObserver(wrapped, predicate)

        assert observer._wrapped is wrapped
        assert observer._predicate is predicate

    def test_update_with_passing_predicate(self):
        """测试通过谓词的更新"""
        wrapped = ConcreteObserver([EventType.CONFIG_CHANGED])
        predicate = lambda e: e.source == "allowed_source"
        observer = FilterObserver(wrapped, predicate)

        event = Event(type=EventType.CONFIG_CHANGED, source="allowed_source")
        observer.update(event)

        assert len(wrapped.received_events) == 1

    def test_update_with_failing_predicate(self):
        """测试未通过谓词的更新"""
        wrapped = ConcreteObserver([EventType.CONFIG_CHANGED])
        predicate = lambda e: e.source == "allowed_source"
        observer = FilterObserver(wrapped, predicate)

        event = Event(type=EventType.CONFIG_CHANGED, source="blocked_source")
        observer.update(event)

        assert len(wrapped.received_events) == 0

    def test_get_interests_delegation(self):
        """测试获取兴趣委托"""
        wrapped = ConcreteObserver([EventType.CONFIG_CHANGED])
        observer = FilterObserver(wrapped, lambda e: True)

        assert observer.get_interests() == [EventType.CONFIG_CHANGED]


# ============================================================================
# 便捷函数测试
# ============================================================================

class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_subscribe(self):
        """测试订阅函数"""
        callback = Mock()
        interests = [EventType.CONFIG_CHANGED]

        observer = subscribe(interests, callback, name="TestSubscriber")

        assert isinstance(observer, FunctionObserver)
        assert event_bus.get_observer_count() == 1

    def test_subscribe_async_mode(self):
        """测试异步模式订阅"""
        callback = Mock()
        interests = [EventType.CONFIG_CHANGED]

        observer = subscribe(interests, callback, async_mode=True, name="AsyncSubscriber")

        assert isinstance(observer, AsyncFunctionObserver)

    def test_unsubscribe(self):
        """测试取消订阅"""
        callback = Mock()
        interests = [EventType.CONFIG_CHANGED]

        observer = subscribe(interests, callback)
        assert event_bus.get_observer_count() == 1

        unsubscribe(observer)
        assert event_bus.get_observer_count() == 0

    def test_publish(self):
        """测试发布事件"""
        observer = ConcreteObserver([EventType.CONFIG_CHANGED])
        event_bus.attach(observer)

        publish(EventType.CONFIG_CHANGED, "test_source", {"key": "value"})

        assert len(observer.received_events) == 1
        assert observer.received_events[0].source == "test_source"
        assert observer.received_events[0].data == {"key": "value"}

    @pytest.mark.asyncio
    async def test_publish_async(self):
        """测试异步发布事件"""
        observer = ConcreteObserver([EventType.CONFIG_CHANGED])
        event_bus.attach(observer)

        await publish_async(EventType.CONFIG_CHANGED, "test_source", {"key": "value"})

        assert len(observer.received_events) == 1
        assert observer.received_events[0].source == "test_source"


# ============================================================================
# 集成测试
# ============================================================================

class TestEventBusIntegration:
    """事件总线集成测试"""

    def test_multiple_observers_multiple_events(self):
        """测试多观察者多事件场景"""
        bus = EventBus()

        config_observers = [
            ConcreteObserver([EventType.CONFIG_CHANGED]) for _ in range(3)
        ]
        doc_observers = [
            ConcreteObserver([EventType.DOCUMENT_ADDED]) for _ in range(2)
        ]

        for obs in config_observers + doc_observers:
            bus.attach(obs)

        # 发布配置变更事件
        config_event = Event(type=EventType.CONFIG_CHANGED, source="test")
        bus.notify(config_event)

        # 发布文档添加事件
        doc_event = Event(type=EventType.DOCUMENT_ADDED, source="test")
        bus.notify(doc_event)

        # 验证
        for obs in config_observers:
            assert len(obs.received_events) == 1
            assert obs.received_events[0].type == EventType.CONFIG_CHANGED

        for obs in doc_observers:
            assert len(obs.received_events) == 1
            assert obs.received_events[0].type == EventType.DOCUMENT_ADDED

    def test_observer_with_multiple_interests(self):
        """测试多兴趣观察者"""
        bus = EventBus()
        observer = ConcreteObserver([
            EventType.CONFIG_CHANGED,
            EventType.DOCUMENT_ADDED,
            EventType.TASK_COMPLETED
        ])
        bus.attach(observer)

        bus.notify(Event(type=EventType.CONFIG_CHANGED, source="test"))
        bus.notify(Event(type=EventType.DOCUMENT_ADDED, source="test"))
        bus.notify(Event(type=EventType.TASK_STARTED, source="test"))
        bus.notify(Event(type=EventType.TASK_COMPLETED, source="test"))

        assert len(observer.received_events) == 3

    @pytest.mark.asyncio
    async def test_async_concurrent_notifications(self):
        """测试异步并发通知"""
        bus = EventBus()

        notification_counts = {"count": 0}

        class CountingObserver(Observer):
            def __init__(self):
                self.notifications = 0

            def get_interests(self):
                return [EventType.CONFIG_CHANGED]

            def update(self, event):
                self.notifications += 1

            async def update_async(self, event):
                await asyncio.sleep(0.01)
                self.notifications += 1

        observers = [CountingObserver() for _ in range(5)]
        for obs in observers:
            bus.attach(obs)

        event = Event(type=EventType.CONFIG_CHANGED, source="test")
        await bus.notify_async(event)

        # 所有观察者都应该收到通知
        for obs in observers:
            assert obs.notifications == 1
