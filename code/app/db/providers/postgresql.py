"""
上海宇羲伏天智能科技有限公司出品

文件级注释：PostgreSQL 数据库适配器
设计原则：单一职责原则 - 仅处理 PostgreSQL 相关逻辑
"""

from typing import Dict, Any
from loguru import logger
from app.db.providers.base import DatabaseProvider


class PostgreSQLProvider(DatabaseProvider):
    """
    类级注释：PostgreSQL 数据库提供商实现
    属性：
        config: 包含 host, port, name, user, password 的配置字典
    """

    # 类常量：支持的驱动类型
    DRIVER = "asyncpg"

    def get_connection_url(self) -> str:
        """
        函数级注释：构建 PostgreSQL 异步连接 URL
        返回值：str - 格式：postgresql+asyncpg://user:pass@host:port/name
        """
        # 内部变量：从配置中提取参数
        host = self.config.get("host", "localhost")
        port = self.config.get("port", 5432)
        name = self.config.get("name", "knowledge_db")
        user = self.config.get("user", "postgres")
        password = self.config.get("password", "")

        # 内部逻辑：构建连接 URL
        return f"postgresql+{self.DRIVER}://{user}:{password}@{host}:{port}/{name}"

    def get_engine_options(self) -> Dict[str, Any]:
        """
        函数级注释：获取 PostgreSQL 引擎配置选项
        内部变量：pool_timeout - 获取连接的超时时间，timeout - 连接建立超时，command_timeout - SQL命令执行超时
        内部逻辑：配置连接池参数和超时参数，防止请求长时间卡住
        返回值：dict - 引擎配置
        """
        return {
            "echo": False,
            "pool_size": 5,
            "max_overflow": 10,
            "pool_pre_ping": True,  # 连接健康检查
            "pool_recycle": 3600,   # 1小时回收连接
            # 内部变量：获取连接的超时时间（秒），防止连接池耗尽时长时间等待
            "pool_timeout": 30,
            # 内部逻辑：设置连接时区，确保服务器端也使用配置的时区
            "connect_args": {
                "server_settings": {"timezone": "Asia/Shanghai"},
                # 内部变量：asyncpg 连接超时参数
                "timeout": 10,              # 内部变量：连接建立超时（秒）
                "command_timeout": 25,      # 内部变量：SQL命令执行超时（秒）
            }
        }

    async def ensure_database_exists(self) -> None:
        """
        函数级注释：确保 PostgreSQL 数据库存在
        内部逻辑：连接到 postgres 默认库 -> 检查目标库是否存在 -> 不存在则创建
        """
        # 内部变量：提取配置
        host = self.config.get("host", "localhost")
        port = self.config.get("port", 5432)
        user = self.config.get("user", "postgres")
        password = self.config.get("password", "")
        db_name = self.config.get("name", "knowledge_db")

        try:
            # 导入 asyncpg
            import asyncpg

            # 内部逻辑：连接到默认 postgres 库
            conn = await asyncpg.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database="postgres"
            )

            try:
                # 内部逻辑：检查数据库是否存在
                exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = $1)",
                    db_name
                )

                # 内部逻辑：不存在则创建
                if not exists:
                    await conn.execute(f'CREATE DATABASE "{db_name}" ENCODING \'utf8\'')
                    logger.info(f"已创建 PostgreSQL 数据库: {db_name}")
                else:
                    logger.info(f"PostgreSQL 数据库已存在: {db_name}")
            finally:
                await conn.close()

        except Exception as e:
            logger.error(f"确保 PostgreSQL 数据库存在失败: {str(e)}")
            # 如果数据库已存在或其他问题，不阻断启动
            logger.info("继续启动，假设数据库已存在")

    def get_provider_name(self) -> str:
        """
        函数级注释：获取提供商名称
        返回值：str - "PostgreSQL"
        """
        return "PostgreSQL"
