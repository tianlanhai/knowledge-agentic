# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：服务装饰器模块
内部逻辑：提供依赖注入相关的装饰器
设计模式：装饰器模式（Decorator Pattern）
设计原则：开闭原则（OCP）
"""

from functools import wraps
from typing import Callable, TypeVar, Type, Any, Optional, get_type_hints
from enum import Enum
from loguru import logger

from .service_container import (
    ServiceContainer,
    ServiceLifetime,
    get_container
)

# 内部变量：泛型类型
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])


class InjectMode(Enum):
    """
    类级注释：注入模式枚举
    属性：
        POSITIONAL: 位置参数注入
        KEYWORD: 关键字参数注入
    """
    # 位置参数注入
    POSITIONAL = "positional"
    # 关键字参数注入
    KEYWORD = "keyword"


def injectable(
    lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
    as_interface: Optional[Type] = None
):
    """
    函数级注释：服务类装饰器
    设计模式：装饰器模式
    内部逻辑：自动将类注册到服务容器

    参数：
        lifetime - 服务生命周期
        as_interface - 注册为接口类型

    @example
    ```python
    @injectable(ServiceLifetime.SCOPED)
    class ChatService:
        def __init__(self, db: Database):
            self.db = db
    ```
    """
    def decorator(cls: Type[T]) -> Type[T]:
        # 内部逻辑：获取容器并注册
        container = get_container()
        container.register(cls, cls, lifetime, as_interface)

        # 内部逻辑：保留原始类
        cls._injectable_lifetime = lifetime
        cls._injectable_interface = as_interface

        return cls

    return decorator


def inject(func: F) -> F:
    """
    函数级注释：依赖注入装饰器
    设计模式：装饰器模式
    内部逻辑：自动注入函数参数中的依赖

    @example
    ```python
    @inject
    def handle_chat(request: ChatRequest, service: ChatService):
        return service.chat(request)
    ```

    注意：需要配合 FastAPI 依赖注入使用，或在容器作用域中调用
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 内部逻辑：获取容器
        container = get_container()

        # 内部逻辑：获取函数签名
        import inspect
        sig = inspect.signature(func)

        # 内部逻辑：解析并注入依赖
        for param_name, param in sig.parameters.items():
            if param_name in kwargs:
                continue  # 已提供参数，跳过

            # 内部逻辑：获取参数类型
            param_type = param.annotation
            if param_type == inspect.Parameter.empty:
                continue

            # 内部逻辑：从容器获取服务
            try:
                service = container.get_service(param_type)
                kwargs[param_name] = service
            except ValueError:
                # 内部逻辑：服务未注册，跳过
                logger.debug(
                    f"服务 {param_type.__name__} 未注册，"
                    f"无法注入到 {func.__name__}"
                )

        return func(*args, **kwargs)

    return wrapper


def inject_method(method: F) -> F:
    """
    函数级注释：方法依赖注入装饰器
    设计模式：装饰器模式
    内部逻辑：自动注入类方法中的依赖

    @example
    ```python
    class ChatHandler:
        @inject_method
        async def handle(self, request: ChatRequest, service: ChatService):
            return await service.process(request)
    ```
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        # 内部逻辑：获取容器
        container = get_container()

        # 内部逻辑：获取方法签名
        import inspect
        sig = inspect.signature(method)

        # 内部逻辑：解析并注入依赖（跳过 self 参数）
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            if param_name in kwargs:
                continue

            param_type = param.annotation
            if param_type == inspect.Parameter.empty:
                continue

            try:
                service = container.get_service(param_type)
                kwargs[param_name] = service
            except ValueError:
                logger.debug(
                    f"服务 {param_type.__name__} 未注册，"
                    f"无法注入到 {method.__name__}"
                )

        return method(self, *args, **kwargs)

    return wrapper


def inject_property(service_type: Type[T]) -> property:
    """
    函数级注释：属性依赖注入装饰器
    设计模式：装饰器模式 + 代理模式
    内部逻辑：创建一个延迟加载的属性

    @example
    ```python
    class ChatHandler:
        service: ChatService = inject_property(ChatService)
    ```
    """
    # 内部变量：缓存属性名
    cache_name = f'_{service_type.__name__}_cached'

    def getter(self) -> T:
        # 内部逻辑：检查缓存
        if hasattr(self, cache_name):
            return getattr(self, cache_name)

        # 内部逻辑：从容器获取服务
        container = get_container()
        service = container.get_service(service_type)

        # 内部逻辑：缓存实例
        setattr(self, cache_name, service)
        return service

    return property(getter)


def singleton(cls: Type[T]) -> Type[T]:
    """
    函数级注释：单例装饰器（便捷方法）
    设计模式：单例模式 + 装饰器模式
    内部逻辑：将类注册为单例服务

    @example
    ```python
    @singleton
    class Database:
        def __init__(self):
            self.connection = connect()
    ```
    """
    return injectable(ServiceLifetime.SINGLETON)(cls)


def scoped(cls: Type[T]) -> Type[T]:
    """
    函数级注释：作用域装饰器（便捷方法）
    设计模式：装饰器模式
    内部逻辑：将类注册为作用域服务

    @example
    ```python
    @scoped
    class ChatService:
        def __init__(self, db: Database):
            self.db = db
    ```
    """
    return injectable(ServiceLifetime.SCOPED)(cls)


def transient(cls: Type[T]) -> Type[T]:
    """
    函数级注释：瞬态装饰器（便捷方法）
    设计模式：装饰器模式
    内部逻辑：将类注册为瞬态服务

    @example
    ```python
    @transient
    class ChatRequest:
        def __init__(self):
            self.timestamp = datetime.now()
    ```
    """
    return injectable(ServiceLifetime.TRANSIENT)(cls)


# 内部变量：导出所有公共接口
__all__ = [
    'InjectMode',
    'injectable',
    'inject',
    'inject_method',
    'inject_property',
    'singleton',
    'scoped',
    'transient',
]
