"""
上海宇羲伏天智能科技有限公司出品

文件级注释：SQLite 数据库适配器
设计原则：单一职责原则 - 仅处理 SQLite 相关逻辑
"""

import os
from typing import Dict, Any
from loguru import logger
from app.db.providers.base import DatabaseProvider


class SQLiteProvider(DatabaseProvider):
    """
    类级注释：SQLite 数据库提供商实现
    属性：
        config: 包含 path 的配置字典
    """

    # 类常量：驱动类型
    DRIVER = "aiosqlite"

    def get_connection_url(self) -> str:
        """
        函数级注释：构建 SQLite 异步连接 URL
        返回值：str - 格式：sqlite+aiosqlite:///path/to/db.sqlite
        """
        # 内部变量：获取数据库路径
        db_path = self.config.get("path", "./data/metadata.db")

        # 内部逻辑：规范化路径（移除前导 ./）
        normalized_path = db_path.lstrip('./')

        return f"sqlite+{self.DRIVER}:///{normalized_path}"

    def get_engine_options(self) -> Dict[str, Any]:
        """
        函数级注释：获取 SQLite 引擎配置选项
        返回值：dict - 引擎配置
        """
        return {
            "echo": False,
        }

    async def ensure_database_exists(self) -> None:
        """
        函数级注释：确保 SQLite 数据库目录存在
        内部逻辑：获取数据库文件目录 -> 创建目录（如不存在）
        """
        # 内部变量：获取数据库路径
        db_path = self.config.get("path", "./data/metadata.db")

        # 内部逻辑：获取目录路径
        db_dir = os.path.dirname(db_path.lstrip('./'))

        # 内部逻辑：创建目录（Guard Clause）
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"SQLite 数据库目录已确保存在: {db_dir}")

    def get_provider_name(self) -> str:
        """
        函数级注释：获取提供商名称
        返回值：str - "SQLite"
        """
        return "SQLite"
