"""
上海宇羲伏天智能科技有限公司出品

文件级注释：配置管理模块
内部逻辑：统一管理应用配置，支持配置变更通知
设计模式：单例模式 + 观察者模式
职责：集中管理配置，支持热重载和变更通知
"""

from typing import Dict, Any, Callable, List, Optional
from enum import Enum
from loguru import logger
import asyncio


class ConfigEventType(Enum):
    """
    类级注释：配置事件类型枚举
    内部逻辑：定义各种配置变更事件
    """
    # LLM配置变更
    LLM_CHANGED = "llm_changed"
    # 嵌入模型配置变更
    EMBEDDING_CHANGED = "embedding_changed"
    # 数据库配置变更
    DATABASE_CHANGED = "database_changed"
    # 向量库配置变更
    VECTOR_DB_CHANGED = "vector_db_changed"
    # 全局配置变更
    GLOBAL_CHANGED = "global_changed"


class ConfigManager:
    """
    类级注释：配置管理器
    内部逻辑：统一管理应用配置，支持配置变更通知
    设计模式：单例模式 + 观察者模式

    使用示例：
        # 获取单例实例
        config_manager = ConfigManager()

        # 订阅配置变更
        def on_llm_change(config):
            LLMFactory.update_config(config)

        config_manager.subscribe(ConfigEventType.LLM_CHANGED, on_llm_change)

        # 更新配置
        await config_manager.update_config(new_llm_config, ConfigEventType.LLM_CHANGED)
    """

    # 内部变量：类级别的单例实例
    _instance: Optional['ConfigManager'] = None

    # 内部变量：类级别的锁，用于线程安全
    _lock = asyncio.Lock()

    def __new__(cls) -> 'ConfigManager':
        """
        函数级注释：实现单例模式
        内部逻辑：确保全局只有一个配置管理器实例
        设计模式：单例模式 - 延迟初始化
        返回值：ConfigManager实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """
        函数级注释：初始化配置管理器
        内部逻辑：初始化监听器列表和配置存储
        """
        # Guard Clauses：避免重复初始化
        if self._initialized:
            return

        # 内部变量：事件监听器映射表
        self._listeners: Dict[ConfigEventType, List[Callable]] = {
            event_type: []
            for event_type in ConfigEventType
        }

        # 内部变量：配置存储
        self._config: Dict[str, Any] = {}

        # 内部变量：配置版本号，用于检测变更
        self._config_versions: Dict[ConfigEventType, int] = {
            event_type: 0
            for event_type in ConfigEventType
        }

        self._initialized = True
        logger.info("配置管理器初始化完成")

    async def subscribe(
        self,
        event_type: ConfigEventType,
        callback: Callable[[Dict[str, Any]], Any]
    ) -> Callable[[], None]:
        """
        函数级注释：订阅配置变更事件
        内部逻辑：将回调函数注册到指定事件类型
        设计模式：观察者模式 - 订阅主题
        参数：
            event_type - 事件类型
            callback - 回调函数，接收配置字典
        返回值：取消订阅的函数

        使用示例：
            unsubscribe = await config_manager.subscribe(
                ConfigEventType.LLM_CHANGED,
                lambda config: update_llm(config)
            )
            # 取消订阅
            unsubscribe()
        """
        # 内部逻辑：添加监听器
        self._listeners[event_type].append(callback)

        logger.debug(f"订阅事件: {event_type.value}, 当前监听器数量: {len(self._listeners[event_type])}")

        # 内部逻辑：返回取消订阅函数
        def unsubscribe() -> None:
            """内部函数：取消订阅"""
            if callback in self._listeners[event_type]:
                self._listeners[event_type].remove(callback)
                logger.debug(f"取消订阅事件: {event_type.value}")

        return unsubscribe

    def unsubscribe(
        self,
        event_type: ConfigEventType,
        callback: Callable[[Dict[str, Any]], Any]
    ) -> None:
        """
        函数级注释：取消订阅配置变更事件
        内部逻辑：从指定事件类型的监听器列表中移除回调
        参数：
            event_type - 事件类型
            callback - 要取消的回调函数
        返回值：None
        """
        if callback in self._listeners[event_type]:
            self._listeners[event_type].remove(callback)
            logger.debug(f"取消订阅事件: {event_type.value}")

    async def update_config(
        self,
        config: Dict[str, Any],
        event_type: ConfigEventType
    ) -> None:
        """
        函数级注释：更新配置并通知订阅者
        内部逻辑：更新配置存储 -> 增加版本号 -> 通知所有监听器
        设计模式：观察者模式 - 发布通知
        参数：
            config - 新的配置字典
            event_type - 配置变更事件类型
        返回值：None

        使用示例：
            await config_manager.update_config(
                {"provider": "openai", "model": "gpt-4"},
                ConfigEventType.LLM_CHANGED
            )
        """
        # 内部逻辑：更新配置存储
        self._config.update(config)

        # 内部逻辑：增加版本号
        self._config_versions[event_type] += 1

        logger.info(f"配置已更新: {event_type.value}, 版本: {self._config_versions[event_type]}")

        # 内部逻辑：通知所有订阅者
        await self._notify_listeners(event_type, config)

    async def _notify_listeners(
        self,
        event_type: ConfigEventType,
        config: Dict[str, Any]
    ) -> None:
        """
        函数级注释：通知事件的所有监听器
        内部逻辑：遍历监听器列表，异步执行回调
        参数：
            event_type - 事件类型
            config - 配置字典
        返回值：None
        @private
        """
        listeners = self._listeners[event_type]

        if not listeners:
            logger.debug(f"事件 {event_type.value} 没有监听器")
            return

        # 内部逻辑：异步执行所有监听器
        for callback in listeners:
            try:
                # 内部逻辑：检查是否为协程函数
                if asyncio.iscoroutinefunction(callback):
                    await callback(config)
                else:
                    callback(config)
            except Exception as e:
                logger.error(f"监听器执行失败 ({event_type.value}): {str(e)}", exc_info=True)

    def get(self, key: str, default: Any = None) -> Any:
        """
        函数级注释：获取配置值
        内部逻辑：从配置存储中获取指定键的值
        参数：
            key - 配置键
            default - 默认值
        返回值：配置值或默认值

        使用示例：
            api_key = config_manager.get("openai_api_key", "")
        """
        return self._config.get(key, default)

    def get_all(self) -> Dict[str, Any]:
        """
        函数级注释：获取所有配置
        内部逻辑：返回完整的配置字典副本
        返回值：配置字典副本

        使用示例：
            all_config = config_manager.get_all()
        """
        return self._config.copy()

    def set(self, key: str, value: Any) -> None:
        """
        函数级注释：设置配置值（不触发通知）
        内部逻辑：直接设置配置值，不通知监听器
        参数：
            key - 配置键
            value - 配置值
        返回值：None

        注意：此方法不会触发配置变更通知，如需通知请使用 update_config
        """
        self._config[key] = value

    def get_version(self, event_type: ConfigEventType) -> int:
        """
        函数级注释：获取配置版本号
        内部逻辑：返回指定事件类型的配置版本
        参数：
            event_type - 事件类型
        返回值：版本号
        """
        return self._config_versions.get(event_type, 0)

    async def refresh_config(self, event_type: ConfigEventType) -> None:
        """
        函数级注释：刷新配置
        内部逻辑：重新加载配置并触发变更事件
        参数：
            event_type - 要刷新的配置类型
        返回值：None
        """
        # 内部逻辑：这里可以添加从数据库或文件加载配置的逻辑
        # 目前只是触发版本号更新
        self._config_versions[event_type] += 1
        await self._notify_listeners(event_type, self._config)

    def clear(self) -> None:
        """
        函数级注释：清空所有配置
        内部逻辑：重置配置存储和版本号
        返回值：None
        """
        self._config.clear()
        for event_type in ConfigEventType:
            self._config_versions[event_type] = 0
        logger.info("配置已清空")

    def listener_count(self, event_type: ConfigEventType) -> int:
        """
        函数级注释：获取监听器数量
        参数：event_type - 事件类型
        返回值：监听器数量
        """
        return len(self._listeners[event_type])


# 内部变量：全局配置管理器实例（便捷访问）
config_manager = ConfigManager()


# 内部变量：导出所有公共接口
__all__ = [
    'ConfigManager',
    'ConfigEventType',
    'config_manager',
]
