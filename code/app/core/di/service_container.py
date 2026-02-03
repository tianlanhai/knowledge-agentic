# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：服务容器模块（依赖注入容器）
内部逻辑：实现轻量级依赖注入容器，管理服务生命周期
设计模式：单例模式（Singleton）、依赖注入模式（Dependency Injection）
设计原则：依赖倒置原则（DIP）、开闭原则（OCP）
"""

from typing import (
    Any,
    Callable,
    Dict,
    Optional,
    Type,
    TypeVar,
    Generic,
    get_type_hints
)
from enum import Enum
from dataclasses import dataclass, field
from loguru import logger
import asyncio
import inspect

# 内部变量：泛型类型 T，表示服务类型
T = TypeVar('T')


class ServiceLifetime(Enum):
    """
    类级注释：服务生命周期枚举
    属性：
        TRANSIENT: 瞬态 - 每次请求创建新实例
        SCOPED: 作用域 - 同一作用域内共享实例
        SINGLETON: 单例 - 全局唯一实例
    """
    # 瞬态服务
    TRANSIENT = "transient"
    # 作用域服务
    SCOPED = "scoped"
    # 单例服务
    SINGLETON = "singleton"


@dataclass
class ServiceDescriptor:
    """
    类级注释：服务描述符
    内部逻辑：封装服务的注册信息
    属性：工厂函数、生命周期、接口类型
    """
    # 内部属性：服务工厂函数
    factory: Callable[..., Any]
    # 内部属性：服务生命周期
    lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    # 内部属性：接口类型（用于抽象注册）
    interface: Optional[Type] = None
    # 内部属性：依赖的服务类型列表
    dependencies: list = field(default_factory=list)


class ServiceScope:
    """
    类级注释：服务作用域
    设计模式：作用域模式
    职责：管理作用域内的服务实例
    """

    def __init__(self, container: 'ServiceContainer'):
        """
        函数级注释：初始化服务作用域
        参数：
            container - 服务容器
        """
        # 内部变量：所属容器
        self._container = container
        # 内部变量：作用域内的实例缓存
        self._scoped_instances: Dict[Type, Any] = {}
        # 内部变量：是否已释放
        self._disposed = False

    def get_service(self, service_type: Type[T]) -> T:
        """
        函数级注释：获取作用域内的服务
        参数：
            service_type - 服务类型
        返回值：服务实例
        异常：ValueError - 作用域已释放时抛出
        """
        if self._disposed:
            raise ValueError("服务作用域已释放")

        # 内部逻辑：检查作用域缓存
        if service_type in self._scoped_instances:
            return self._scoped_instances[service_type]

        # 内部逻辑：从容器获取服务
        service = self._container._create_service(service_type, self)
        self._scoped_instances[service_type] = service
        return service

    def release(self):
        """
        函数级注释：释放作用域
        内部逻辑：清理作用域内的实例，调用释放方法
        """
        for service in self._scoped_instances.values():
            # 内部逻辑：调用服务的释放方法（如果有）
            if hasattr(service, 'dispose'):
                try:
                    service.dispose()
                except Exception as e:
                    logger.warning(f"释放服务失败: {e}")
            elif hasattr(service, 'close'):
                try:
                    if inspect.iscoroutinefunction(service.close):
                        asyncio.create_task(service.close())
                    else:
                        service.close()
                except Exception as e:
                    logger.warning(f"关闭服务失败: {e}")

        self._scoped_instances.clear()
        self._disposed = True


class ServiceContainer:
    """
    类级注释：服务容器（依赖注入容器）
    设计模式：单例模式 + 依赖注入模式
    职责：
        1. 管理服务注册
        2. 创建服务实例
        3. 处理依赖关系
        4. 管理服务生命周期
    """

    # 内部类变量：全局容器实例（单例）
    _instance: Optional['ServiceContainer'] = None

    def __new__(cls) -> 'ServiceContainer':
        """
        函数级注释：实现单例模式
        返回值：单例容器实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """
        函数级注释：初始化服务容器
        """
        if self._initialized:
            return

        # 内部变量：服务注册表 {服务类型: 服务描述符}
        self._services: Dict[Type, ServiceDescriptor] = {}

        # 内部变量：单例实例缓存
        self._singletons: Dict[Type, Any] = {}

        # 内部变量：当前作用域
        self._current_scope: Optional[ServiceScope] = None

        # 内部变量：初始化标记
        self._initialized = True

        logger.info("服务容器初始化完成")

    def register(
        self,
        service_type: Type[T],
        factory: Callable[..., T],
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
        as_interface: Optional[Type] = None
    ) -> 'ServiceContainer':
        """
        函数级注释：注册服务
        参数：
            service_type - 服务类型
            factory - 工厂函数或类
            lifetime - 服务生命周期
            as_interface - 注册为接口类型
        返回值：容器自身（支持链式调用）

        @example
        ```python
        container.register(ChatService, ChatService, ServiceLifetime.SCOPED)
        # 或者
        container.register(IChatService, ChatService, as_interface=IChatService)
        ```
        """
        # 内部逻辑：解析工厂函数的依赖
        dependencies = self._get_dependencies(factory)

        # 内部逻辑：创建服务描述符
        descriptor = ServiceDescriptor(
            factory=factory,
            lifetime=lifetime,
            interface=as_interface,
            dependencies=dependencies
        )

        # 内部逻辑：注册服务
        self._services[service_type] = descriptor

        # 内部逻辑：如果指定了接口，也注册到接口类型
        if as_interface:
            self._services[as_interface] = descriptor

        logger.debug(
            f"注册服务: {service_type.__name__}, "
            f"生命周期: {lifetime.value}, "
            f"依赖: {[d.__name__ for d in dependencies]}"
        )

        return self

    def register_singleton(
        self,
        service_type: Type[T],
        factory: Callable[..., T],
        as_interface: Optional[Type] = None
    ) -> 'ServiceContainer':
        """
        函数级注释：注册单例服务（便捷方法）
        参数：
            service_type - 服务类型
            factory - 工厂函数或类
            as_interface - 注册为接口类型
        返回值：容器自身
        """
        return self.register(service_type, factory, ServiceLifetime.SINGLETON, as_interface)

    def register_scoped(
        self,
        service_type: Type[T],
        factory: Callable[..., T],
        as_interface: Optional[Type] = None
    ) -> 'ServiceContainer':
        """
        函数级注释：注册作用域服务（便捷方法）
        参数：
            service_type - 服务类型
            factory - 工厂函数或类
            as_interface - 注册为接口类型
        返回值：容器自身
        """
        return self.register(service_type, factory, ServiceLifetime.SCOPED, as_interface)

    def register_transient(
        self,
        service_type: Type[T],
        factory: Callable[..., T],
        as_interface: Optional[Type] = None
    ) -> 'ServiceContainer':
        """
        函数级注释：注册瞬态服务（便捷方法）
        参数：
            service_type - 服务类型
            factory - 工厂函数或类
            as_interface - 注册为接口类型
        返回值：容器自身
        """
        return self.register(service_type, factory, ServiceLifetime.TRANSIENT, as_interface)

    def get_service(self, service_type: Type[T]) -> T:
        """
        函数级注释：获取服务实例
        参数：
            service_type - 服务类型
        返回值：服务实例
        异常：ValueError - 服务未注册时抛出
        """
        # 内部逻辑：检查服务是否已注册
        if service_type not in self._services:
            # 内部逻辑：尝试查找接口实现
            for interface, descriptor in self._services.items():
                if descriptor.interface == service_type:
                    return self._create_service(interface, None)

            raise ValueError(
                f"服务未注册: {service_type.__name__}. "
                f"请先使用 register() 方法注册该服务。"
            )

        # 内部逻辑：创建服务实例
        return self._create_service(service_type, None)

    def create_scope(self) -> ServiceScope:
        """
        函数级注释：创建新的服务作用域
        返回值：服务作用域实例
        """
        return ServiceScope(self)

    def is_registered(self, service_type: Type) -> bool:
        """
        函数级注释：检查服务是否已注册
        参数：
            service_type - 服务类型
        返回值：是否已注册
        """
        return service_type in self._services

    def get_registered_services(self) -> Dict[Type, ServiceDescriptor]:
        """
        函数级注释：获取所有已注册的服务
        返回值：服务字典
        """
        return self._services.copy()

    def clear(self):
        """
        函数级注释：清空所有注册的服务
        内部逻辑：用于测试或重置
        """
        self._services.clear()
        self._singletons.clear()
        logger.info("服务容器已清空")

    def _create_service(
        self,
        service_type: Type[T],
        scope: Optional[ServiceScope]
    ) -> T:
        """
        函数级注释：创建服务实例（内部方法）
        参数：
            service_type - 服务类型
            scope - 服务作用域
        返回值：服务实例

        内部逻辑：
        1. 获取服务描述符
        2. 根据生命周期决定是否使用缓存
        3. 解析依赖并注入
        4. 调用工厂函数创建实例
        """
        descriptor = self._services[service_type]

        # 内部逻辑：单例服务
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            if service_type in self._singletons:
                return self._singletons[service_type]
            instance = self._instantiate_service(descriptor, scope)
            self._singletons[service_type] = instance
            return instance

        # 内部逻辑：作用域服务
        # 修复递归问题：直接在scope中检查缓存和创建实例，而不是委托给scope.get_service
        if descriptor.lifetime == ServiceLifetime.SCOPED:
            if scope is None:
                scope = self._current_scope
            if scope is None:
                raise ValueError(
                    f"作用域服务 {service_type.__name__} 需要在作用域中使用。"
                    f"请使用 create_scope() 创建作用域。"
                )
            # 检查scope缓存
            if service_type in scope._scoped_instances:
                return scope._scoped_instances[service_type]
            # 创建实例并缓存到scope中
            instance = self._instantiate_service(descriptor, scope)
            scope._scoped_instances[service_type] = instance
            return instance

        # 内部逻辑：瞬态服务 - 每次创建新实例
        return self._instantiate_service(descriptor, scope)

    def _instantiate_service(
        self,
        descriptor: ServiceDescriptor,
        scope: Optional[ServiceScope]
    ) -> Any:
        """
        函数级注释：实例化服务（内部方法）
        参数：
            descriptor - 服务描述符
            scope - 服务作用域
        返回值：服务实例

        内部逻辑：
        1. 解析构造函数参数
        2. 递归解析依赖
        3. 调用工厂函数
        """
        # 内部逻辑：获取工厂函数的签名
        factory = descriptor.factory
        sig = inspect.signature(factory if inspect.isclass(factory) else factory)

        # 内部逻辑：解析依赖
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue

            # 内部逻辑：跳过有默认值的参数
            if param.default != inspect.Parameter.empty:
                continue

            # 内部逻辑：获取参数类型
            param_type = param.annotation
            if param_type == inspect.Parameter.empty:
                logger.warning(
                    f"服务 {factory.__name__} 的参数 {param_name} 缺少类型注解，"
                    f"无法自动注入依赖"
                )
                continue

            # 内部逻辑：递归获取依赖服务
            dependency = self._create_service(param_type, scope)
            kwargs[param_name] = dependency

        # 内部逻辑：调用工厂函数
        if inspect.isclass(factory):
            # 内部逻辑：如果是类，实例化
            instance = factory(**kwargs)
        else:
            # 内部逻辑：如果是函数，直接调用
            instance = factory(**kwargs)

        return instance

    def _get_dependencies(self, factory: Callable) -> list:
        """
        函数级注释：获取工厂函数的依赖类型（内部方法）
        参数：
            factory - 工厂函数
        返回值：依赖类型列表
        """
        dependencies = []

        try:
            # 内部逻辑：获取类型注解
            hints = get_type_hints(factory)

            # 内部逻辑：过滤返回值类型
            if 'return' in hints:
                del hints['return']

            # 内部逻辑：收集依赖类型
            for param_name, param_type in hints.items():
                if param_type != type(None):  # 排除 None 类型
                    dependencies.append(param_type)

        except Exception as e:
            logger.debug(f"无法解析 {factory.__name__} 的依赖: {e}")

        return dependencies


# 内部变量：全局服务容器实例
_global_container: Optional[ServiceContainer] = None


def get_container() -> ServiceContainer:
    """
    函数级注释：获取全局服务容器
    返回值：全局服务容器实例
    """
    global _global_container
    if _global_container is None:
        _global_container = ServiceContainer()
    return _global_container


def reset_container():
    """
    函数级注释：重置全局服务容器
    内部逻辑：主要用于测试
    """
    global _global_container
    _global_container = None


# 内部变量：导出所有公共接口
__all__ = [
    'ServiceContainer',
    'ServiceScope',
    'ServiceLifetime',
    'ServiceDescriptor',
    'get_container',
    'reset_container',
]
