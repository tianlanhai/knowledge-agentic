"""
上海宇羲伏天智能科技有限公司出品

文件级注释：数据库工厂类
设计原则：遵循工厂模式，参考 LLMFactory 的设计风格
设计模式：工厂模式 + 单例模式
"""

from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from loguru import logger

from app.db.providers.base import DatabaseProvider
from app.db.providers.postgresql import PostgreSQLProvider
from app.db.providers.sqlite import SQLiteProvider
from app.core.config import settings


class DatabaseFactory:
    """
    类级注释：数据库工厂类，负责根据配置创建不同类型的数据库引擎
    设计模式：工厂模式 + 单例模式
    """

    # 类常量：支持的数据库提供商列表
    SUPPORTED_PROVIDERS = {
        "postgresql": "PostgreSQL",
        "sqlite": "SQLite",
    }

    # 类变量：单例引擎实例
    _engine: AsyncEngine = None
    _provider: DatabaseProvider = None

    @classmethod
    def create_provider(cls) -> DatabaseProvider:
        """
        函数级注释：根据配置创建数据库提供商实例
        内部逻辑：读取配置 -> 验证配置 -> 创建对应提供商实例 -> 返回实例
        返回值：DatabaseProvider - 数据库提供商实例
        异常：ValueError - 当配置的提供商不支持时
        """
        # 内部变量：获取当前配置的提供商（转小写）
        provider = settings.DATABASE_PROVIDER.lower()

        # 内部逻辑：Guard Clauses - 验证提供商是否支持
        if provider not in cls.SUPPORTED_PROVIDERS:
            supported_list = list(cls.SUPPORTED_PROVIDERS.keys())
            raise ValueError(
                f"不支持的数据库提供商: {provider}。"
                f"支持的提供商: {supported_list}"
            )

        # 内部逻辑：根据提供商创建对应的配置字典
        config = cls._get_provider_config(provider)

        # 内部逻辑：根据提供商创建对应的实例
        try:
            if provider == "postgresql":
                return PostgreSQLProvider(config)
            elif provider == "sqlite":
                return SQLiteProvider(config)
        except Exception as e:
            logger.error(f"创建 {provider} 数据库提供商失败: {str(e)}")
            raise

    @classmethod
    def _get_provider_config(cls, provider: str) -> Dict[str, Any]:
        """
        函数级注释：根据提供商类型获取配置字典
        参数：
            provider: 提供商名称
        返回值：dict - 配置字典
        """
        if provider == "postgresql":
            return {
                "host": settings.DB_HOST,
                "port": settings.DB_PORT,
                "name": settings.DB_NAME,
                "user": settings.DB_USER,
                "password": settings.DB_PASSWORD,
            }
        elif provider == "sqlite":
            return {
                "path": settings.SQLITE_DB_PATH,
            }
        return {}

    @classmethod
    async def get_engine(cls) -> AsyncEngine:
        """
        函数级注释：获取数据库引擎（单例模式）
        内部逻辑：检查是否已创建 -> 未创建则创建新引擎 -> 返回引擎
        返回值：AsyncEngine - 数据库异步引擎
        """
        # 内部逻辑：单例检查
        if cls._engine is None:
            # 内部变量：创建提供商实例
            provider = cls.create_provider()
            cls._provider = provider

            # 内部逻辑：确保数据库存在
            await provider.ensure_database_exists()

            # 内部逻辑：创建引擎
            url = provider.get_connection_url()
            options = provider.get_engine_options()
            cls._engine = create_async_engine(url, **options)

            logger.info(
                f"已创建数据库引擎，提供商: {provider.get_provider_name()}, "
                f"地址: {settings.DB_HOST if isinstance(provider, PostgreSQLProvider) else settings.SQLITE_DB_PATH}"
            )

        return cls._engine

    @classmethod
    async def dispose_engine(cls) -> None:
        """
        函数级注释：关闭数据库引擎
        内部逻辑：检查引擎是否存在 -> 存在则关闭并置空
        返回值：无
        """
        # 内部逻辑：单例检查
        if cls._engine is not None:
            await cls._engine.dispose()
            cls._engine = None
            cls._provider = None
            logger.info("数据库引擎已关闭")

    @classmethod
    def get_current_provider(cls) -> str:
        """
        函数级注释：获取当前配置的数据库提供商
        返回值：str - 提供商名称
        """
        return settings.DATABASE_PROVIDER.lower()

    @classmethod
    def get_current_provider_name(cls) -> str:
        """
        函数级注释：获取当前提供商的显示名称
        返回值：str - 提供商显示名称
        """
        provider = cls.get_current_provider()
        return cls.SUPPORTED_PROVIDERS.get(provider, "Unknown")
