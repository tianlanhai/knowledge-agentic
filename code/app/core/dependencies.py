# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：FastAPI依赖注入模块
内部逻辑：提供FastAPI依赖函数，从服务容器中获取服务实例
设计模式：依赖注入模式 - FastAPI Depends与ServiceContainer集成
设计原则：依赖倒置原则（DIP）
"""

from typing import TypeVar, Type, Optional, get_type_hints
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.di.service_container import get_container, ServiceContainer, ServiceLifetime
from app.db.session import get_db

# 内部变量：泛型类型 T，表示服务类型
T = TypeVar('T')


def get_service(service_type: Type[T]) -> callable:
    """
    函数级注释：创建FastAPI依赖函数，从容器中获取服务
    设计模式：工厂模式 - 动态创建依赖函数
    参数：
        service_type - 服务类型
    返回值：FastAPI依赖函数

    @example
    ```python
    @router.get("/chat")
    async def chat(
        request: ChatRequest,
        chat_service: ChatService = Depends(get_service(ChatService))
    ):
        return await chat_service.chat_completion(request)
    ```
    """
    # 内部逻辑：定义依赖函数
    async def _dependency(
        db: AsyncSession = Depends(get_db)
    ) -> T:
        """
        函数级注释：内部依赖函数
        内部逻辑：从容器中获取服务实例，并注入数据库会话
        参数：
            db - 数据库会话
        返回值：服务实例
        """
        # 内部变量：获取服务容器
        container = get_container()

        # 内部逻辑：从容器获取服务
        service = container.get_service(service_type)

        # 内部逻辑：如果服务有db属性，注入数据库会话
        if hasattr(service, 'db'):
            service.db = db

        return service

    # 内部逻辑：设置依赖函数的名称（便于调试）
    _dependency.__name__ = f"get_{service_type.__name__.lower()}"

    return _dependency


def get_optional_service(service_type: Type[T]) -> callable:
    """
    函数级注释：创建可选的FastAPI依赖函数
    内部逻辑：如果服务未注册，返回None而不是抛出异常
    参数：
        service_type - 服务类型
    返回值：FastAPI依赖函数

    @example
    ```python
    @router.get("/chat")
    async def chat(
        request: ChatRequest,
        chat_service: Optional[ChatService] = Depends(get_optional_service(ChatService))
    ):
        if chat_service:
            return await chat_service.chat_completion(request)
        return {"message": "Service not available"}
    ```
    """
    # 内部逻辑：定义依赖函数
    async def _dependency(
        db: AsyncSession = Depends(get_db)
    ) -> Optional[T]:
        """
        函数级注释：内部依赖函数
        内部逻辑：尝试从容器获取服务，未注册则返回None
        参数：
            db - 数据库会话
        返回值：服务实例或None
        """
        # 内部变量：获取服务容器
        container = get_container()

        # 内部逻辑：检查服务是否已注册
        if not container.is_registered(service_type):
            return None

        # 内部逻辑：从容器获取服务
        service = container.get_service(service_type)

        # 内部逻辑：如果服务有db属性，注入数据库会话
        if hasattr(service, 'db') and service is not None:
            service.db = db

        return service

    _dependency.__name__ = f"get_optional_{service_type.__name__.lower()}"

    return _dependency


class ServiceDepends:
    """
    类级注释：服务依赖注入工具类
    设计模式：静态工厂模式 - 提供便捷的服务依赖获取方法
    用途：简化API端点中的服务依赖注入

    @example
    ```python
    from app.core.dependencies import ServiceDepends
    from app.services.chat_service import ChatService

    @router.post("/chat")
    async def chat(
        request: ChatRequest,
        chat_service: ChatService = ServiceDepends.chat()
    ):
        return await chat_service.chat_completion(request)
    ```
    """

    @staticmethod
    def chat() -> callable:
        """
        函数级注释：获取ChatService依赖
        返回值：FastAPI依赖函数
        """
        from app.services.chat_service import ChatService
        return Depends(get_service(ChatService))

    @staticmethod
    def ingest() -> callable:
        """
        函数级注释：获取IngestService依赖
        返回值：FastAPI依赖函数
        """
        from app.services.ingest_service import IngestService
        return Depends(get_service(IngestService))

    @staticmethod
    def search() -> callable:
        """
        函数级注释：获取SearchService依赖
        返回值：FastAPI依赖函数
        """
        from app.services.search_service import SearchService
        return Depends(get_service(SearchService))


# 内部变量：导出所有公共接口
__all__ = [
    'get_service',
    'get_optional_service',
    'ServiceDepends',
]
