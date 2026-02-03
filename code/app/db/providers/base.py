"""
上海宇羲伏天智能科技有限公司出品

文件级注释：数据库提供商抽象基类
设计原则：遵循 SOLID 中的开闭原则和依赖倒置原则
设计模式：抽象工厂模式
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class DatabaseProvider(ABC):
    """
    类级注释：数据库提供商抽象基类
    设计模式：策略模式 - 定义数据库连接的统一接口
    属性：
        config: 数据库配置字典
    """

    def __init__(self, config: Dict[str, Any]):
        """
        函数级注释：构造函数
        参数：
            config: 数据库配置字典
        """
        self.config = config

    @abstractmethod
    def get_connection_url(self) -> str:
        """
        函数级注释：获取数据库连接URL（抽象方法）
        返回值：str - SQLAlchemy连接字符串
        """
        pass

    @abstractmethod
    def get_engine_options(self) -> Dict[str, Any]:
        """
        函数级注释：获取引擎配置选项（抽象方法）
        返回值：dict - 引擎配置字典
        """
        pass

    @abstractmethod
    async def ensure_database_exists(self) -> None:
        """
        函数级注释：确保数据库存在（抽象方法）
        内部逻辑：对于PostgreSQL，创建数据库；对于SQLite，创建目录
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        函数级注释：获取提供商名称（抽象方法）
        返回值：str - 提供商显示名称
        """
        pass
