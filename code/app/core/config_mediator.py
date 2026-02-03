# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：配置中介者模块
内部逻辑：解耦配置变更时各组件之间的通信，统一协调处理顺序
设计模式：中介者模式（Mediator Pattern）
设计原则：迪米特法则、单一职责原则
参考：从观察者模式升级，解决组件间隐式依赖问题
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Callable, Optional, Set
from enum import Enum
from loguru import logger
import asyncio
from dataclasses import dataclass, field
from datetime import datetime

# 内部变量：导入配置事件类型
from app.core.config_manager import ConfigEventType


class MediatorPriority(Enum):
    """
    类级注释：中介者优先级枚举
    内部逻辑：定义同事组件的处理优先级
    """
    # 最高优先级（先处理）
    HIGHEST = 0
    # 高优先级
    HIGH = 1
    # 正常优先级
    NORMAL = 2
    # 低优先级
    LOW = 3
    # 最低优先级（最后处理）
    LOWEST = 4


@dataclass
class ColleagueConfig:
    """
    类级注释：同事组件配置
    内部逻辑：封装同事组件的元数据
    """
    # 属性：组件名称
    name: str
    # 属性：优先级
    priority: MediatorPriority = MediatorPriority.NORMAL
    # 属性：是否异步处理
    async_mode: bool = True
    # 属性：超时时间（秒）
    timeout: float = 5.0
    # 属性：是否允许失败继续
    continue_on_failure: bool = False
    # 属性：感兴趣的事件类型
    interested_events: Set[ConfigEventType] = field(default_factory=set)


class Colleague(ABC):
    """
    类级注释：同事组件抽象基类
    内部逻辑：定义参与中介者通信的组件接口
    设计模式：中介者模式 - 同事接口
    """

    def __init__(self, name: str):
        """
        函数级注释：初始化同事组件
        参数：
            name - 组件名称
        """
        # 内部变量：组件名称
        self._name = name
        # 内部变量：中介者引用
        self._mediator: Optional['ConfigMediator'] = None

    @property
    def name(self) -> str:
        """
        函数级注释：获取组件名称
        返回值：组件名称
        """
        return self._name

    def set_mediator(self, mediator: 'ConfigMediator') -> None:
        """
        函数级注释：设置中介者
        参数：
            mediator - 中介者实例
        """
        self._mediator = mediator

    def get_config(self) -> ColleagueConfig:
        """
        函数级注释：获取同事组件配置
        返回值：同事组件配置
        """
        return ColleagueConfig(name=self._name)

    @abstractmethod
    async def on_config_changed(
        self,
        event_type: ConfigEventType,
        config: Dict[str, Any]
    ) -> None:
        """
        函数级注释：处理配置变更事件
        参数：
            event_type - 事件类型
            config - 配置数据
        """
        pass

    async def notify_mediator(
        self,
        event_type: ConfigEventType,
        config: Dict[str, Any]
    ) -> None:
        """
        函数级注释：通过中介者通知其他组件
        参数：
            event_type - 事件类型
            config - 配置数据
        """
        if self._mediator:
            await self._mediator.notify(self._name, event_type, config)


class ConfigMediator:
    """
    类级注释：配置变更中介者
    内部逻辑：协调各组件的配置变更处理，解耦组件间依赖
    设计模式：中介者模式 - 具体中介者
    职责：
        1. 管理同事组件的注册和注销
        2. 按优先级协调配置变更通知
        3. 处理组件通信的异常和超时
        4. 记录通信日志和审计信息
    """

    def __init__(self):
        """
        函数级注释：初始化中介者
        """
        # 内部变量：同事组件注册表 {name: colleague}
        self._colleagues: Dict[str, Colleague] = {}

        # 内部变量：事件日志
        self._event_log: List[Dict[str, Any]] = []

        # 内部变量：最大日志条数
        self._max_log_size = 1000

        # 内部变量：通信统计
        self._stats = {
            "total_notifications": 0,
            "successful_notifications": 0,
            "failed_notifications": 0,
            "timeout_notifications": 0
        }

        logger.info("配置中介者初始化完成")

    def register(self, colleague: Colleague) -> None:
        """
        函数级注释：注册同事组件
        内部逻辑：添加到注册表 -> 设置中介者引用
        参数：
            colleague - 同事组件实例
        """
        self._colleagues[colleague.name] = colleague
        colleague.set_mediator(self)
        logger.info(f"注册同事组件: {colleague.name}")

    def unregister(self, name: str) -> None:
        """
        函数级注释：注销同事组件
        参数：
            name - 组件名称
        """
        if name in self._colleagues:
            colleague = self._colleagues.pop(name)
            colleague.set_mediator(None)
            logger.info(f"注销同事组件: {name}")

    def get_colleague(self, name: str) -> Optional[Colleague]:
        """
        函数级注释：获取同事组件
        参数：
            name - 组件名称
        返回值：同事组件或 None
        """
        return self._colleagues.get(name)

    def get_colleagues_by_priority(
        self,
        event_type: ConfigEventType
    ) -> List[Colleague]:
        """
        函数级注释：按优先级获取感兴趣的同事组件
        内部逻辑：筛选感兴趣的组件 -> 按优先级排序
        参数：
            event_type - 事件类型
        返回值：排序后的同事组件列表
        """
        interested = []

        for colleague in self._colleagues.values():
            config = colleague.get_config()

            # 内部逻辑：检查组件是否对该事件感兴趣
            if not config.interested_events or event_type in config.interested_events:
                interested.append((colleague, config.priority.value))

        # 内部逻辑：按优先级排序（值越小优先级越高）
        interested.sort(key=lambda x: x[1])

        return [c for c, _ in interested]

    async def notify(
        self,
        sender_name: str,
        event_type: ConfigEventType,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        函数级注释：通知所有感兴趣的同事组件
        内部逻辑：按优先级顺序通知 -> 处理超时和异常 -> 收集结果
        参数：
            sender_name - 发送者名称
            event_type - 事件类型
            config - 配置数据
        返回值：通知结果汇总
        """
        self._stats["total_notifications"] += 1

        # 内部逻辑：记录事件
        self._log_event(sender_name, event_type, config)

        # 内部逻辑：获取按优先级排序的同事组件
        colleagues = self.get_colleagues_by_priority(event_type)

        logger.info(
            f"中介者开始通知: 发送者={sender_name}, "
            f"事件={event_type.value}, 感兴趣的组件数={len(colleagues)}"
        )

        # 内部变量：收集结果
        results = {
            "success": [],
            "failed": [],
            "timeout": [],
            "skipped": []
        }

        for colleague in colleagues:
            # 内部逻辑：跳过发送者自己
            if colleague.name == sender_name:
                results["skipped"].append(colleague.name)
                continue

            colleague_config = colleague.get_config()

            try:
                # 内部逻辑：根据配置选择处理方式
                if colleague_config.async_mode:
                    # 内部逻辑：带超时的异步处理
                    await asyncio.wait_for(
                        colleague.on_config_changed(event_type, config),
                        timeout=colleague_config.timeout
                    )
                else:
                    # 内部逻辑：同步处理
                    await colleague.on_config_changed(event_type, config)

                results["success"].append(colleague.name)
                self._stats["successful_notifications"] += 1
                logger.debug(f"组件 {colleague.name} 处理成功")

            except asyncio.TimeoutError:
                results["timeout"].append(colleague.name)
                self._stats["timeout_notifications"] += 1
                logger.warning(f"组件 {colleague.name} 处理超时")

                # 内部逻辑：检查是否继续
                if not colleague_config.continue_on_failure:
                    logger.warning(f"组件 {colleague.name} 超时且不允许继续，停止通知")
                    break

            except Exception as e:
                results["failed"].append({
                    "name": colleague.name,
                    "error": str(e)
                })
                self._stats["failed_notifications"] += 1
                logger.error(f"组件 {colleague.name} 处理失败: {str(e)}")

                # 内部逻辑：检查是否继续
                if not colleague_config.continue_on_failure:
                    logger.warning(f"组件 {colleague.name} 失败且不允许继续，停止通知")
                    break

        logger.info(
            f"中介者通知完成: 成功={len(results['success'])}, "
            f"失败={len(results['failed'])}, 超时={len(results['timeout'])}"
        )

        return results

    def _log_event(
        self,
        sender: str,
        event_type: ConfigEventType,
        config: Dict[str, Any]
    ) -> None:
        """
        函数级注释：记录事件日志
        参数：
            sender - 发送者
            event_type - 事件类型
            config - 配置数据
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "sender": sender,
            "event_type": event_type.value,
            "config_keys": list(config.keys()) if config else []
        }

        self._event_log.append(log_entry)

        # 内部逻辑：保持日志大小
        if len(self._event_log) > self._max_log_size:
            self._event_log = self._event_log[-self._max_log_size:]

    def get_event_log(
        self,
        limit: int = 100,
        sender: Optional[str] = None,
        event_type: Optional[ConfigEventType] = None
    ) -> List[Dict[str, Any]]:
        """
        函数级注释：获取事件日志
        内部逻辑：可选过滤 -> 限制数量
        参数：
            limit - 最大返回条数
            sender - 过滤发送者
            event_type - 过滤事件类型
        返回值：日志条目列表
        """
        logs = self._event_log

        # 内部逻辑：应用过滤
        if sender:
            logs = [log for log in logs if log["sender"] == sender]
        if event_type:
            logs = [log for log in logs if log["event_type"] == event_type.value]

        # 内部逻辑：限制数量并倒序返回
        return logs[-limit:][::-1]

    def get_stats(self) -> Dict[str, Any]:
        """
        函数级注释：获取统计信息
        返回值：统计信息字典
        """
        stats = self._stats.copy()
        stats["registered_colleagues"] = len(self._colleagues)
        stats["event_log_size"] = len(self._event_log)
        return stats

    def clear_logs(self) -> None:
        """
        函数级注释：清空事件日志
        """
        self._event_log.clear()
        logger.info("中介者事件日志已清空")

    def reset_stats(self) -> None:
        """
        函数级注释：重置统计信息
        """
        self._stats = {
            "total_notifications": 0,
            "successful_notifications": 0,
            "failed_notifications": 0,
            "timeout_notifications": 0
        }
        logger.info("中介者统计信息已重置")


# ==================== 具体同事组件实现 ====================

class LLMFactoryColleague(Colleague):
    """
    类级注释：LLM 工厂同事组件
    内部逻辑：监听 LLM 配置变更，更新工厂实例
    设计模式：中介者模式 - 具体同事
    """

    def __init__(self, llm_factory):
        """
        函数级注释：初始化 LLM 工厂同事
        参数：
            llm_factory - LLM 工厂实例
        """
        super().__init__("llm_factory")
        # 内部变量：LLM 工厂引用
        self._factory = llm_factory

    def get_config(self) -> ColleagueConfig:
        """
        函数级注释：获取组件配置
        返回值：组件配置
        """
        return ColleagueConfig(
            name=self._name,
            priority=MediatorPriority.HIGHEST,  # 最高优先级
            interested_events={ConfigEventType.LLM_CHANGED}
        )

    async def on_config_changed(
        self,
        event_type: ConfigEventType,
        config: Dict[str, Any]
    ) -> None:
        """
        函数级注释：处理 LLM 配置变更
        内部逻辑：更新运行时配置 -> 清除缓存
        参数：
            event_type - 事件类型
            config - 新配置
        """
        if event_type == ConfigEventType.LLM_CHANGED:
            self._factory.set_runtime_config(config)
            self._factory.clear_cache()
            logger.info(f"LLM 工厂已更新配置: provider={config.get('provider')}")


class EmbeddingFactoryColleague(Colleague):
    """
    类级注释：Embedding 工厂同事组件
    内部逻辑：监听 Embedding 配置变更
    设计模式：中介者模式 - 具体同事
    """

    def __init__(self, embedding_factory):
        """
        函数级注释：初始化 Embedding 工厂同事
        参数：
            embedding_factory - Embedding 工厂实例
        """
        super().__init__("embedding_factory")
        # 内部变量：Embedding 工厂引用
        self._factory = embedding_factory

    def get_config(self) -> ColleagueConfig:
        """
        函数级注释：获取组件配置
        返回值：组件配置
        """
        return ColleagueConfig(
            name=self._name,
            priority=MediatorPriority.HIGH,
            interested_events={ConfigEventType.EMBEDDING_CHANGED}
        )

    async def on_config_changed(
        self,
        event_type: ConfigEventType,
        config: Dict[str, Any]
    ) -> None:
        """
        函数级注释：处理 Embedding 配置变更
        参数：
            event_type - 事件类型
            config - 新配置
        """
        if event_type == ConfigEventType.EMBEDDING_CHANGED:
            self._factory.set_runtime_config(config)
            self._factory.clear_cache()
            logger.info(f"Embedding 工厂已更新配置: provider={config.get('provider')}")


class CacheColleague(Colleague):
    """
    类级注释：缓存同事组件
    内部逻辑：配置变更时清除相关缓存
    设计模式：中介者模式 - 具体同事
    """

    def __init__(self, cache_manager):
        """
        函数级注释：初始化缓存同事
        参数：
            cache_manager - 缓存管理器实例
        """
        super().__init__("cache_manager")
        # 内部变量：缓存管理器引用
        self._cache_manager = cache_manager

    def get_config(self) -> ColleagueConfig:
        """
        函数级注释：获取组件配置
        返回值：组件配置
        """
        return ColleagueConfig(
            name=self._name,
            priority=MediatorPriority.LOW,  # 低优先级，最后处理
            interested_events={
                ConfigEventType.LLM_CHANGED,
                ConfigEventType.EMBEDDING_CHANGED,
                ConfigEventType.DATABASE_CHANGED
            }
        )

    async def on_config_changed(
        self,
        event_type: ConfigEventType,
        config: Dict[str, Any]
    ) -> None:
        """
        函数级注释：处理配置变更，清除缓存
        参数：
            event_type - 事件类型
            config - 配置数据
        """
        # 内部逻辑：清除相关缓存
        if event_type == ConfigEventType.LLM_CHANGED:
            self._cache_manager.clear_llm_cache()
        elif event_type == ConfigEventType.EMBEDDING_CHANGED:
            self._cache_manager.clear_embedding_cache()
        elif event_type == ConfigEventType.DATABASE_CHANGED:
            self._cache_manager.clear_all()

        logger.info(f"缓存管理器已清除: {event_type.value}")


class AuditColleague(Colleague):
    """
    类级注释：审计同事组件
    内部逻辑：记录配置变更审计日志
    设计模式：中介者模式 - 具体同事
    """

    def __init__(self):
        """
        函数级注释：初始化审计同事
        """
        super().__init__("audit_logger")
        # 内部变量：审计日志存储
        self._audit_logs: List[Dict[str, Any]] = []

    def get_config(self) -> ColleagueConfig:
        """
        函数级注释：获取组件配置
        返回值：组件配置
        """
        return ColleagueConfig(
            name=self._name,
            priority=MediatorPriority.LOWEST,  # 最低优先级，确保在最后执行
            continue_on_failure=True,  # 审计失败不影响其他组件
            interested_events=set(ConfigEventType)  # 关心所有事件
        )

    async def on_config_changed(
        self,
        event_type: ConfigEventType,
        config: Dict[str, Any]
    ) -> None:
        """
        函数级注释：记录审计日志
        参数：
            event_type - 事件类型
            config - 配置数据
        """
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type.value,
            "config_summary": {k: f"{v}" for k, v in config.items() if k not in ['api_key', 'secret']},
            "config_hash": hash(str(sorted(config.items())))
        }

        self._audit_logs.append(audit_entry)

        # 内部逻辑：限制日志大小
        if len(self._audit_logs) > 1000:
            self._audit_logs = self._audit_logs[-1000:]

        logger.debug(f"审计日志已记录: {event_type.value}")

    def get_audit_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        函数级注释：获取审计日志
        参数：
            limit - 最大返回条数
        返回值：审计日志列表
        """
        return self._audit_logs[-limit:][::-1]


# ==================== 中介者工厂 ====================

class ConfigMediatorFactory:
    """
    类级注释：配置中介者工厂
    内部逻辑：创建预配置的中介者和同事组件
    设计模式：工厂模式
    """

    # 内部变量：单例实例
    _instance: Optional['ConfigMediatorFactory'] = None

    def __new__(cls) -> 'ConfigMediatorFactory':
        """
        函数级注释：实现单例模式
        返回值：单例实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def create_standard_mediator(
        self,
        llm_factory=None,
        embedding_factory=None,
        cache_manager=None
    ) -> ConfigMediator:
        """
        函数级注释：创建标准配置中介者
        内部逻辑：创建中介者 -> 注册标准同事组件
        参数：
            llm_factory - LLM 工厂实例
            embedding_factory - Embedding 工厂实例
            cache_manager - 缓存管理器实例
        返回值：配置好的中介者
        """
        mediator = ConfigMediator()

        # 内部逻辑：注册审计组件（总是注册）
        mediator.register(AuditColleague())

        # 内部逻辑：按条件注册其他组件
        if llm_factory:
            mediator.register(LLMFactoryColleague(llm_factory))

        if embedding_factory:
            mediator.register(EmbeddingFactoryColleague(embedding_factory))

        if cache_manager:
            mediator.register(CacheColleague(cache_manager))

        logger.info("标准配置中介者创建完成")
        return mediator


# 内部变量：全局中介者实例
config_mediator_factory = ConfigMediatorFactory()


# 内部变量：导出所有公共接口
__all__ = [
    'ConfigMediator',
    'Colleague',
    'ColleagueConfig',
    'MediatorPriority',
    'ConfigMediatorFactory',
    'config_mediator_factory',
    'LLMFactoryColleague',
    'EmbeddingFactoryColleague',
    'CacheColleague',
    'AuditColleague',
]
