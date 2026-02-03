# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：config_mediator模块完整测试集
内部逻辑：针对app/core/config_mediator.py编写全面测试
设计模式：中介者模式测试、优先级测试、超时处理测试
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, Any

# ============================================================================
# 测试 app.core.config_mediator 模块 (覆盖率 0%)
# ============================================================================
from app.core.config_mediator import (
    MediatorPriority,
    ColleagueConfig,
    Colleague,
    ConfigMediator,
    LLMFactoryColleague,
    EmbeddingFactoryColleague,
    CacheColleague,
    AuditColleague,
    ConfigMediatorFactory,
    config_mediator_factory
)
from app.core.config_manager import ConfigEventType


# ============================================================================
# 测试 MediatorPriority 枚举
# ============================================================================
class TestMediatorPriority:
    """类级注释：中介者优先级枚举测试"""

    def test_enum_values(self):
        """函数级注释：验证所有优先级枚举值"""
        assert MediatorPriority.HIGHEST.value == 0
        assert MediatorPriority.HIGH.value == 1
        assert MediatorPriority.NORMAL.value == 2
        assert MediatorPriority.LOW.value == 3
        assert MediatorPriority.LOWEST.value == 4

    def test_enum_ordering(self):
        """函数级注释：验证优先级顺序正确"""
        assert MediatorPriority.HIGHEST.value < MediatorPriority.HIGH.value
        assert MediatorPriority.HIGH.value < MediatorPriority.NORMAL.value
        assert MediatorPriority.NORMAL.value < MediatorPriority.LOW.value
        assert MediatorPriority.LOW.value < MediatorPriority.LOWEST.value


# ============================================================================
# 测试 ColleagueConfig 数据类
# ============================================================================
class TestColleagueConfig:
    """类级注释：同事组件配置测试"""

    def test_init_defaults(self):
        """函数级注释：测试默认初始化值"""
        config = ColleagueConfig(name="test_component")
        assert config.name == "test_component"
        assert config.priority == MediatorPriority.NORMAL
        assert config.async_mode is True
        assert config.timeout == 5.0
        assert config.continue_on_failure is False
        assert config.interested_events == set()

    def test_init_with_values(self):
        """函数级注释：测试带值的初始化"""
        config = ColleagueConfig(
            name="test",
            priority=MediatorPriority.HIGH,
            async_mode=False,
            timeout=10.0,
            continue_on_failure=True,
            interested_events={ConfigEventType.LLM_CHANGED}
        )
        assert config.name == "test"
        assert config.priority == MediatorPriority.HIGH
        assert config.async_mode is False
        assert config.timeout == 10.0
        assert config.continue_on_failure is True
        assert ConfigEventType.LLM_CHANGED in config.interested_events


# ============================================================================
# 测试 Colleague 抽象基类
# ============================================================================
class TestColleague:
    """类级注释：同事组件基类测试"""

    def test_init(self):
        """函数级注释：测试初始化"""
        colleague = TestableColleague("test_colleague")
        assert colleague.name == "test_colleague"
        assert colleague._mediator is None

    def test_name_property(self):
        """函数级注释：测试名称属性"""
        colleague = TestableColleague("my_name")
        assert colleague.name == "my_name"

    def test_set_mediator(self):
        """函数级注释：测试设置中介者"""
        colleague = TestableColleague("test")
        mediator = Mock()
        colleague.set_mediator(mediator)
        assert colleague._mediator is mediator

    def test_get_config(self):
        """函数级注释：测试获取配置"""
        colleague = TestableColleague("test")
        config = colleague.get_config()
        assert isinstance(config, ColleagueConfig)
        assert config.name == "test"

    @pytest.mark.asyncio
    async def test_notify_mediator(self):
        """函数级注释：测试通过中介者通知"""
        colleague = TestableColleague("sender")
        mediator = AsyncMock()
        colleague.set_mediator(mediator)

        config_data = {"key": "value"}
        await colleague.notify_mediator(ConfigEventType.LLM_CHANGED, config_data)

        mediator.notify.assert_called_once_with(
            "sender", ConfigEventType.LLM_CHANGED, config_data
        )

    @pytest.mark.asyncio
    async def test_notify_mediator_without_mediator(self):
        """函数级注释：测试无中介者时不崩溃"""
        colleague = TestableColleague("test")
        # 不应该抛出异常
        await colleague.notify_mediator(ConfigEventType.LLM_CHANGED, {})

    @pytest.mark.asyncio
    async def test_on_config_changed_abstract(self):
        """函数级注释：测试抽象方法被实现"""
        colleague = TestableColleague("test")
        # TestableColleague实现了on_config_changed
        await colleague.on_config_changed(ConfigEventType.LLM_CHANGED, {})
        assert colleague.last_event_type == ConfigEventType.LLM_CHANGED


# ============================================================================
# 测试具体同事实现（用于测试）
# ============================================================================
class TestableColleague(Colleague):
    """类级注释：可测试的同事实现"""

    def __init__(self, name: str):
        """函数级注释：初始化"""
        super().__init__(name)
        self.last_event_type = None
        self.last_config = None

    async def on_config_changed(
        self,
        event_type: ConfigEventType,
        config: Dict[str, Any]
    ) -> None:
        """函数级注释：记录配置变更"""
        self.last_event_type = event_type
        self.last_config = config


# ============================================================================
# 测试 ConfigMediator 中介者
# ============================================================================
class TestConfigMediator:
    """类级注释：配置中介者测试"""

    def test_init(self):
        """函数级注释：测试初始化"""
        mediator = ConfigMediator()
        assert mediator._colleagues == {}
        assert mediator._event_log == []
        assert mediator._max_log_size == 1000
        assert mediator._stats["total_notifications"] == 0

    def test_register(self):
        """函数级注释：测试注册同事组件"""
        mediator = ConfigMediator()
        colleague = TestableColleague("test_component")

        mediator.register(colleague)

        assert "test_component" in mediator._colleagues
        assert colleague._mediator is mediator

    def test_register_multiple(self):
        """函数级注释：测试注册多个组件"""
        mediator = ConfigMediator()
        c1 = TestableColleague("comp1")
        c2 = TestableColleague("comp2")

        mediator.register(c1)
        mediator.register(c2)

        assert len(mediator._colleagues) == 2
        assert c1._mediator is mediator
        assert c2._mediator is mediator

    def test_unregister(self):
        """函数级注释：测试注销同事组件"""
        mediator = ConfigMediator()
        colleague = TestableColleague("test")
        mediator.register(colleague)

        mediator.unregister("test")

        assert "test" not in mediator._colleagues
        assert colleague._mediator is None

    def test_unregister_nonexistent(self):
        """函数级注释：测试注销不存在的组件不崩溃"""
        mediator = ConfigMediator()
        # 不应该抛出异常
        mediator.unregister("nonexistent")

    def test_get_colleague(self):
        """函数级注释：测试获取同事组件"""
        mediator = ConfigMediator()
        colleague = TestableColleague("test")
        mediator.register(colleague)

        result = mediator.get_colleague("test")
        assert result is colleague

    def test_get_colleague_not_found(self):
        """函数级注释：测试获取不存在的组件返回None"""
        mediator = ConfigMediator()
        result = mediator.get_colleague("nonexistent")
        assert result is None

    def test_get_colleagues_by_priority_empty(self):
        """函数级注释：测试无组件时返回空列表"""
        mediator = ConfigMediator()
        result = mediator.get_colleagues_by_priority(ConfigEventType.LLM_CHANGED)
        assert result == []

    def test_get_colleagues_by_priority(self):
        """函数级注释：测试按优先级排序"""
        mediator = ConfigMediator()

        # 创建不同优先级的组件
        c1 = TestableColleague("low_priority")
        c2 = TestableColleague("high_priority")
        c3 = TestableColleague("normal_priority")

        # 设置不同的优先级配置
        def make_config(name, priority):
            class CustomColleague(TestableColleague):
                def __init__(self, n, p):
                    super().__init__(n)
                    self._priority = p

                def get_config(self):
                    return ColleagueConfig(
                        name=self._name,
                        priority=self._priority
                    )
            return CustomColleague(name, priority)

        low = make_config("low", MediatorPriority.LOW)
        high = make_config("high", MediatorPriority.HIGH)
        normal = make_config("normal", MediatorPriority.NORMAL)

        mediator.register(low)
        mediator.register(high)
        mediator.register(normal)

        result = mediator.get_colleagues_by_priority(ConfigEventType.LLM_CHANGED)

        # 验证顺序: HIGH (1) -> NORMAL (2) -> LOW (3)
        assert result[0].name == "high"
        assert result[1].name == "normal"
        assert result[2].name == "low"

    def test_get_colleagues_by_priority_with_interested_events(self):
        """函数级注释：测试筛选感兴趣事件的组件"""
        mediator = ConfigMediator()

        class FilteredColleague(TestableColleague):
            def __init__(self, name, events):
                super().__init__(name)
                self._events = events

            def get_config(self):
                return ColleagueConfig(
                    name=self._name,
                    interested_events=self._events
                )

        c1 = FilteredColleague("llm_only", {ConfigEventType.LLM_CHANGED})
        c2 = FilteredColleague("all_events", set())
        c3 = FilteredColleague("embedding_only", {ConfigEventType.EMBEDDING_CHANGED})

        mediator.register(c1)
        mediator.register(c2)
        mediator.register(c3)

        result = mediator.get_colleagues_by_priority(ConfigEventType.LLM_CHANGED)

        # llm_only 和 all_events 应该返回，embedding_only 不应该
        names = [c.name for c in result]
        assert "llm_only" in names
        assert "all_events" in names
        assert "embedding_only" not in names

    @pytest.mark.asyncio
    async def test_notify_empty(self):
        """函数级注释：测试无组件时的通知"""
        mediator = ConfigMediator()
        result = await mediator.notify("sender", ConfigEventType.LLM_CHANGED, {})
        assert result["success"] == []
        assert result["failed"] == []
        assert result["timeout"] == []

    @pytest.mark.asyncio
    async def test_notify_single_colleague(self):
        """函数级注释：测试通知单个组件"""
        mediator = ConfigMediator()
        colleague = TestableColleague("receiver")
        mediator.register(colleague)

        config = {"provider": "ollama"}
        result = await mediator.notify("sender", ConfigEventType.LLM_CHANGED, config)

        assert "receiver" in result["success"]
        assert colleague.last_event_type == ConfigEventType.LLM_CHANGED
        assert colleague.last_config == config

    @pytest.mark.asyncio
    async def test_notify_skip_sender(self):
        """函数级注释：测试跳过发送者自己"""
        mediator = ConfigMediator()
        colleague = TestableColleague("sender")
        mediator.register(colleague)

        result = await mediator.notify("sender", ConfigEventType.LLM_CHANGED, {})

        assert "sender" in result["skipped"]
        assert colleague.last_event_type is None

    @pytest.mark.asyncio
    async def test_notify_multiple_colleagues(self):
        """函数级注释：测试通知多个组件"""
        mediator = ConfigMediator()
        c1 = TestableColleague("c1")
        c2 = TestableColleague("c2")
        c3 = TestableColleague("c3")

        mediator.register(c1)
        mediator.register(c2)
        mediator.register(c3)

        result = await mediator.notify("sender", ConfigEventType.LLM_CHANGED, {})

        assert len(result["success"]) == 3
        assert "c1" in result["success"]
        assert "c2" in result["success"]
        assert "c3" in result["success"]

    @pytest.mark.asyncio
    async def test_notify_by_priority_order(self):
        """函数级注释：测试按优先级顺序通知"""
        mediator = ConfigMediator()

        call_order = []

        class OrderedColleague(TestableColleague):
            def __init__(self, name):
                super().__init__(name)

            async def on_config_changed(self, event_type, config):
                call_order.append(self.name)
                await super().on_config_changed(event_type, config)

        # 创建不同优先级的组件
        class PriorityColleague(OrderedColleague):
            def __init__(self, name, priority):
                super().__init__(name)
                self._priority = priority

            def get_config(self):
                return ColleagueConfig(name=self._name, priority=self._priority)

        high = PriorityColleague("high", MediatorPriority.HIGH)
        low = PriorityColleague("low", MediatorPriority.LOW)
        normal = PriorityColleague("normal", MediatorPriority.NORMAL)

        mediator.register(low)
        mediator.register(high)
        mediator.register(normal)

        await mediator.notify("sender", ConfigEventType.LLM_CHANGED, {})

        # 验证执行顺序
        assert call_order == ["high", "normal", "low"]

    @pytest.mark.asyncio
    async def test_notify_with_exception(self):
        """函数级注释：测试处理异常"""
        mediator = ConfigMediator()

        class FailingColleague(TestableColleague):
            async def on_config_changed(self, event_type, config):
                raise ValueError("Test error")

        colleague = FailingColleague("failing")
        mediator.register(colleague)

        result = await mediator.notify("sender", ConfigEventType.LLM_CHANGED, {})

        assert len(result["failed"]) == 1
        assert result["failed"][0]["name"] == "failing"
        assert "Test error" in result["failed"][0]["error"]

    @pytest.mark.asyncio
    async def test_notify_stop_on_failure(self):
        """函数级注释：测试失败时停止（continue_on_failure=False）"""
        mediator = ConfigMediator()

        # 创建一个自定义的同事类，可以设置优先级
        class PriorityColleague(TestableColleague):
            def __init__(self, name, priority, continue_on_failure=False):
                super().__init__(name)
                self._priority = priority
                self._continue = continue_on_failure
                self.call_count = 0

            def get_config(self):
                return ColleagueConfig(
                    name=self._name,
                    priority=self._priority,
                    continue_on_failure=self._continue
                )

            async def on_config_changed(self, event_type, config):
                self.call_count += 1
                if self._name == "failing":
                    raise ValueError("Stop here")

        # failing优先级高，会先执行
        failing = PriorityColleague("failing", MediatorPriority.HIGH, continue_on_failure=False)
        after = PriorityColleague("after", MediatorPriority.LOW, continue_on_failure=False)

        mediator.register(failing)
        mediator.register(after)

        # 通知时，failing先执行并失败，after不应该被执行
        result = await mediator.notify("sender", ConfigEventType.LLM_CHANGED, {})

        # failing应该失败
        assert "failing" in [f["name"] for f in result["failed"]]
        # after不应该被调用
        assert after.call_count == 0

    @pytest.mark.asyncio
    async def test_notify_continue_on_failure(self):
        """函数级注释：测试失败时继续（continue_on_failure=True）"""
        mediator = ConfigMediator()

        class FailingColleague(TestableColleague):
            def get_config(self):
                return ColleagueConfig(
                    name=self._name,
                    continue_on_failure=True
                )

            async def on_config_changed(self, event_type, config):
                raise ValueError("Continue anyway")

        c1 = FailingColleague("c1")
        c2 = TestableColleague("c2")

        mediator.register(c1)
        mediator.register(c2)

        result = await mediator.notify("sender", ConfigEventType.LLM_CHANGED, {})

        assert "c1" in [f["name"] for f in result["failed"]]
        assert "c2" in result["success"]
        # c2应该仍然被调用
        assert c2.last_event_type == ConfigEventType.LLM_CHANGED

    @pytest.mark.asyncio
    async def test_notify_timeout(self):
        """函数级注释：测试超时处理"""
        mediator = ConfigMediator()

        class SlowColleague(TestableColleague):
            def get_config(self):
                return ColleagueConfig(
                    name=self._name,
                    timeout=0.1  # 100ms超时
                )

            async def on_config_changed(self, event_type, config):
                await asyncio.sleep(1)  # 超过超时时间

        colleague = SlowColleague("slow")
        mediator.register(colleague)

        result = await mediator.notify("sender", ConfigEventType.LLM_CHANGED, {})

        assert "slow" in result["timeout"]

    @pytest.mark.asyncio
    async def test_notify_sync_mode(self):
        """函数级注释：测试同步模式（async_mode=False）"""
        mediator = ConfigMediator()

        class SyncColleague(TestableColleague):
            def get_config(self):
                return ColleagueConfig(
                    name=self._name,
                    async_mode=False
                )

            async def on_config_changed(self, event_type, config):
                # 同步执行，不设置超时
                self.last_event_type = event_type

        colleague = SyncColleague("sync")
        mediator.register(colleague)

        result = await mediator.notify("sender", ConfigEventType.LLM_CHANGED, {})

        assert "sync" in result["success"]
        assert colleague.last_event_type == ConfigEventType.LLM_CHANGED

    def test_log_event(self):
        """函数级注释：测试记录事件日志"""
        mediator = ConfigMediator()
        config = {"key": "value", "another": "data"}

        mediator._log_event("sender", ConfigEventType.LLM_CHANGED, config)

        assert len(mediator._event_log) == 1
        log = mediator._event_log[0]
        assert log["sender"] == "sender"
        assert log["event_type"] == "llm_changed"
        assert log["config_keys"] == ["key", "another"]

    def test_log_event_max_size(self):
        """函数级注释：测试日志大小限制"""
        mediator = ConfigMediator()
        mediator._max_log_size = 10

        # 添加超过限制的日志
        for i in range(15):
            mediator._log_event(f"sender{i}", ConfigEventType.LLM_CHANGED, {})

        # 日志应该被限制在max_log_size
        assert len(mediator._event_log) == 10

    def test_get_event_log(self):
        """函数级注释：测试获取事件日志"""
        mediator = ConfigMediator()
        mediator._log_event("s1", ConfigEventType.LLM_CHANGED, {})
        mediator._log_event("s2", ConfigEventType.EMBEDDING_CHANGED, {})

        logs = mediator.get_event_log()

        # 应该倒序返回
        assert len(logs) == 2
        assert logs[0]["sender"] == "s2"  # 最新的在前

    def test_get_event_log_with_limit(self):
        """函数级注释：测试限制日志数量"""
        mediator = ConfigMediator()
        for i in range(10):
            mediator._log_event(f"s{i}", ConfigEventType.LLM_CHANGED, {})

        logs = mediator.get_event_log(limit=5)

        assert len(logs) == 5

    def test_get_event_log_with_sender_filter(self):
        """函数级注释：测试按发送者过滤"""
        mediator = ConfigMediator()
        mediator._log_event("alice", ConfigEventType.LLM_CHANGED, {})
        mediator._log_event("bob", ConfigEventType.LLM_CHANGED, {})
        mediator._log_event("alice", ConfigEventType.EMBEDDING_CHANGED, {})

        logs = mediator.get_event_log(sender="alice")

        assert len(logs) == 2
        assert all(log["sender"] == "alice" for log in logs)

    def test_get_event_log_with_event_type_filter(self):
        """函数级注释：测试按事件类型过滤"""
        mediator = ConfigMediator()
        mediator._log_event("s1", ConfigEventType.LLM_CHANGED, {})
        mediator._log_event("s2", ConfigEventType.EMBEDDING_CHANGED, {})
        mediator._log_event("s3", ConfigEventType.LLM_CHANGED, {})

        logs = mediator.get_event_log(event_type=ConfigEventType.LLM_CHANGED)

        assert len(logs) == 2
        assert all(log["event_type"] == "llm_changed" for log in logs)

    def test_get_stats(self):
        """函数级注释：测试获取统计信息"""
        mediator = ConfigMediator()
        mediator.register(TestableColleague("c1"))
        mediator.register(TestableColleague("c2"))
        mediator._log_event("s1", ConfigEventType.LLM_CHANGED, {})

        stats = mediator.get_stats()

        assert stats["total_notifications"] == 0
        assert stats["registered_colleagues"] == 2
        assert stats["event_log_size"] == 1

    def test_clear_logs(self):
        """函数级注释：测试清空日志"""
        mediator = ConfigMediator()
        mediator._log_event("s1", ConfigEventType.LLM_CHANGED, {})
        mediator._log_event("s2", ConfigEventType.LLM_CHANGED, {})

        mediator.clear_logs()

        assert len(mediator._event_log) == 0

    def test_reset_stats(self):
        """函数级注释：测试重置统计"""
        mediator = ConfigMediator()
        mediator._stats["total_notifications"] = 10
        mediator._stats["successful_notifications"] = 5

        mediator.reset_stats()

        assert mediator._stats["total_notifications"] == 0
        assert mediator._stats["successful_notifications"] == 0


# ============================================================================
# 测试 LLMFactoryColleague
# ============================================================================
class TestLLMFactoryColleague:
    """类级注释：LLM工厂同事组件测试"""

    def test_init(self):
        """函数级注释：测试初始化"""
        mock_factory = Mock()
        colleague = LLMFactoryColleague(mock_factory)
        assert colleague.name == "llm_factory"
        assert colleague._factory is mock_factory

    def test_get_config(self):
        """函数级注释：测试获取配置"""
        mock_factory = Mock()
        colleague = LLMFactoryColleague(mock_factory)
        config = colleague.get_config()

        assert config.name == "llm_factory"
        assert config.priority == MediatorPriority.HIGHEST
        assert ConfigEventType.LLM_CHANGED in config.interested_events

    @pytest.mark.asyncio
    async def test_on_config_changed(self):
        """函数级注释：测试处理LLM配置变更"""
        mock_factory = Mock()
        colleague = LLMFactoryColleague(mock_factory)

        config = {"provider": "ollama", "model": "llama2"}
        await colleague.on_config_changed(ConfigEventType.LLM_CHANGED, config)

        mock_factory.set_runtime_config.assert_called_once_with(config)
        mock_factory.clear_cache.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_config_changed_ignores_other_events(self):
        """函数级注释：测试忽略其他事件"""
        mock_factory = Mock()
        colleague = LLMFactoryColleague(mock_factory)

        await colleague.on_config_changed(ConfigEventType.EMBEDDING_CHANGED, {})

        # 不应该调用factory方法
        mock_factory.set_runtime_config.assert_not_called()


# ============================================================================
# 测试 EmbeddingFactoryColleague
# ============================================================================
class TestEmbeddingFactoryColleague:
    """类级注释：Embedding工厂同事组件测试"""

    def test_init(self):
        """函数级注释：测试初始化"""
        mock_factory = Mock()
        colleague = EmbeddingFactoryColleague(mock_factory)
        assert colleague.name == "embedding_factory"
        assert colleague._factory is mock_factory

    def test_get_config(self):
        """函数级注释：测试获取配置"""
        mock_factory = Mock()
        colleague = EmbeddingFactoryColleague(mock_factory)
        config = colleague.get_config()

        assert config.name == "embedding_factory"
        assert config.priority == MediatorPriority.HIGH
        assert ConfigEventType.EMBEDDING_CHANGED in config.interested_events

    @pytest.mark.asyncio
    async def test_on_config_changed(self):
        """函数级注释：测试处理Embedding配置变更"""
        mock_factory = Mock()
        colleague = EmbeddingFactoryColleague(mock_factory)

        config = {"provider": "zhipuai", "model": "embedding-2"}
        await colleague.on_config_changed(ConfigEventType.EMBEDDING_CHANGED, config)

        mock_factory.set_runtime_config.assert_called_once_with(config)
        mock_factory.clear_cache.assert_called_once()


# ============================================================================
# 测试 CacheColleague
# ============================================================================
class TestCacheColleague:
    """类级注释：缓存同事组件测试"""

    def test_init(self):
        """函数级注释：测试初始化"""
        mock_manager = Mock()
        colleague = CacheColleague(mock_manager)
        assert colleague.name == "cache_manager"
        assert colleague._cache_manager is mock_manager

    def test_get_config(self):
        """函数级注释：测试获取配置"""
        mock_manager = Mock()
        colleague = CacheColleague(mock_manager)
        config = colleague.get_config()

        assert config.name == "cache_manager"
        assert config.priority == MediatorPriority.LOW
        assert ConfigEventType.LLM_CHANGED in config.interested_events
        assert ConfigEventType.EMBEDDING_CHANGED in config.interested_events
        assert ConfigEventType.DATABASE_CHANGED in config.interested_events

    @pytest.mark.asyncio
    async def test_on_config_changed_llm(self):
        """函数级注释：测试处理LLM配置变更"""
        mock_manager = Mock()
        colleague = CacheColleague(mock_manager)

        await colleague.on_config_changed(ConfigEventType.LLM_CHANGED, {})

        mock_manager.clear_llm_cache.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_config_changed_embedding(self):
        """函数级注释：测试处理Embedding配置变更"""
        mock_manager = Mock()
        colleague = CacheColleague(mock_manager)

        await colleague.on_config_changed(ConfigEventType.EMBEDDING_CHANGED, {})

        mock_manager.clear_embedding_cache.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_config_changed_database(self):
        """函数级注释：测试处理数据库配置变更"""
        mock_manager = Mock()
        colleague = CacheColleague(mock_manager)

        await colleague.on_config_changed(ConfigEventType.DATABASE_CHANGED, {})

        mock_manager.clear_all.assert_called_once()


# ============================================================================
# 测试 AuditColleague
# ============================================================================
class TestAuditColleague:
    """类级注释：审计同事组件测试"""

    def test_init(self):
        """函数级注释：测试初始化"""
        colleague = AuditColleague()
        assert colleague.name == "audit_logger"
        assert colleague._audit_logs == []

    def test_get_config(self):
        """函数级注释：测试获取配置"""
        colleague = AuditColleague()
        config = colleague.get_config()

        assert config.name == "audit_logger"
        assert config.priority == MediatorPriority.LOWEST
        assert config.continue_on_failure is True
        # 应该关心所有事件
        assert len(config.interested_events) > 0

    @pytest.mark.asyncio
    async def test_on_config_changed(self):
        """函数级注释：测试记录审计日志"""
        colleague = AuditColleague()

        config = {"provider": "ollama", "api_key": "secret123"}
        await colleague.on_config_changed(ConfigEventType.LLM_CHANGED, config)

        logs = colleague.get_audit_logs()
        assert len(logs) == 1
        assert logs[0]["event_type"] == "llm_changed"
        # api_key应该被过滤掉
        assert "api_key" not in logs[0]["config_summary"]
        assert "provider" in logs[0]["config_summary"]

    @pytest.mark.asyncio
    async def test_on_config_changed_multiple(self):
        """函数级注释：测试记录多条审计日志"""
        colleague = AuditColleague()

        await colleague.on_config_changed(ConfigEventType.LLM_CHANGED, {})
        await colleague.on_config_changed(ConfigEventType.EMBEDDING_CHANGED, {})

        logs = colleague.get_audit_logs()
        assert len(logs) == 2

    def test_get_audit_logs_limit(self):
        """函数级注释：测试限制审计日志数量"""
        colleague = AuditColleague()

        # 手动添加日志
        for i in range(10):
            colleague._audit_logs.append({"id": i})

        logs = colleague.get_audit_logs(limit=5)

        assert len(logs) == 5

    @pytest.mark.asyncio
    async def test_audit_log_max_size(self):
        """函数级注释：测试日志大小限制"""
        colleague = AuditColleague()

        # 添加超过限制的日志（限制1000）
        for i in range(1100):
            await colleague.on_config_changed(ConfigEventType.LLM_CHANGED, {"id": i})

        # 日志应该被限制
        assert len(colleague._audit_logs) <= 1000


# ============================================================================
# 测试 ConfigMediatorFactory 工厂
# ============================================================================
class TestConfigMediatorFactory:
    """类级注释：配置中介者工厂测试"""

    def test_singleton(self):
        """函数级注释：测试单例模式"""
        factory1 = ConfigMediatorFactory()
        factory2 = ConfigMediatorFactory()

        assert factory1 is factory2

    def test_create_standard_mediator_empty(self):
        """函数级注释：测试创建空标准中介者"""
        factory = ConfigMediatorFactory()
        mediator = factory.create_standard_mediator()

        assert isinstance(mediator, ConfigMediator)
        # 至少应该有audit_logger
        assert mediator.get_colleague("audit_logger") is not None

    def test_create_standard_mediator_with_llm(self):
        """函数级注释：测试创建带LLM工厂的中介者"""
        factory = ConfigMediatorFactory()
        mock_llm_factory = Mock()

        mediator = factory.create_standard_mediator(llm_factory=mock_llm_factory)

        assert mediator.get_colleague("llm_factory") is not None
        assert mediator.get_colleague("audit_logger") is not None

    def test_create_standard_mediator_with_embedding(self):
        """函数级注释：测试创建带Embedding工厂的中介者"""
        factory = ConfigMediatorFactory()
        mock_embedding_factory = Mock()

        mediator = factory.create_standard_mediator(embedding_factory=mock_embedding_factory)

        assert mediator.get_colleague("embedding_factory") is not None

    def test_create_standard_mediator_with_cache(self):
        """函数级注释：测试创建带缓存管理器的中介者"""
        factory = ConfigMediatorFactory()
        mock_cache_manager = Mock()

        mediator = factory.create_standard_mediator(cache_manager=mock_cache_manager)

        assert mediator.get_colleague("cache_manager") is not None

    def test_create_standard_mediator_with_all(self):
        """函数级注释：测试创建完整配置的中介者"""
        factory = ConfigMediatorFactory()

        mock_llm = Mock()
        mock_embedding = Mock()
        mock_cache = Mock()

        mediator = factory.create_standard_mediator(
            llm_factory=mock_llm,
            embedding_factory=mock_embedding,
            cache_manager=mock_cache
        )

        assert mediator.get_colleague("llm_factory") is not None
        assert mediator.get_colleague("embedding_factory") is not None
        assert mediator.get_colleague("cache_manager") is not None
        assert mediator.get_colleague("audit_logger") is not None


# ============================================================================
# 测试全局工厂实例
# ============================================================================
class TestGlobalFactory:
    """类级注释：全局工厂实例测试"""

    def test_global_factory_exists(self):
        """函数级注释：测试全局工厂实例存在"""
        assert config_mediator_factory is not None
        assert isinstance(config_mediator_factory, ConfigMediatorFactory)

    def test_global_factory_singleton(self):
        """函数级注释：测试全局工厂是单例"""
        # 直接使用模块导入的实例
        from app.core.config_mediator import config_mediator_factory as factory2
        assert config_mediator_factory is factory2


# ============================================================================
# 测试集成场景
# ============================================================================
class TestConfigMediatorIntegration:
    """类级注释：集成场景测试"""

    @pytest.mark.asyncio
    async def test_end_to_end_notification_flow(self):
        """函数级注释：测试端到端通知流程"""
        # 创建工厂和中介者
        factory = ConfigMediatorFactory()

        mock_llm = Mock()
        mock_embedding = Mock()
        mock_cache = Mock()

        mediator = factory.create_standard_mediator(
            llm_factory=mock_llm,
            embedding_factory=mock_embedding,
            cache_manager=mock_cache
        )

        # 发送LLM配置变更通知
        llm_config = {"provider": "ollama", "model": "llama2"}
        result = await mediator.notify(
            "system",
            ConfigEventType.LLM_CHANGED,
            llm_config
        )

        # 验证结果
        assert len(result["success"]) >= 1  # 至少audit_logger成功
        mock_llm.set_runtime_config.assert_called_once()
        mock_llm.clear_cache.assert_called_once()
        mock_cache.clear_llm_cache.assert_called_once()

    @pytest.mark.asyncio
    async def test_colleague_notify_mediator_flow(self):
        """函数级注释：测试同事组件通过中介者通知流程"""
        mediator = ConfigMediator()

        # 创建发送者
        sender = TestableColleague("sender")
        mediator.register(sender)

        # 创建接收者
        receiver = TestableColleague("receiver")
        mediator.register(receiver)

        # 发送者通过中介者通知，sender自己会被跳过，receiver会收到
        config = {"key": "value"}
        await sender.notify_mediator(ConfigEventType.LLM_CHANGED, config)

        # receiver应该收到通知（sender被跳过）
        assert receiver.last_config == config
        assert receiver.last_event_type == ConfigEventType.LLM_CHANGED
        # sender自己不应该收到通知
        assert sender.last_config is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
