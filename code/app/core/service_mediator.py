# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：服务中介者模块
内部逻辑：解耦服务间的直接依赖，提供统一的服务协调接口
设计模式：中介者模式（Mediator Pattern）+ 外观模式（Facade Pattern）
设计原则：迪米特法则、单一职责原则、依赖倒置原则

使用场景：
    - ChatOrchestrator 与其他服务的协调
    - 统一的服务调用入口
    - 服务间的松耦合通信
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, List
from loguru import logger
from enum import Enum
from dataclasses import dataclass


class ServiceEventType(Enum):
    """
    类级注释：服务事件类型枚举
    属性：定义所有支持的服务事件
    """
    # 聊天相关事件
    CHAT_STARTED = "chat_started"
    CHAT_COMPLETED = "chat_completed"
    CHAT_FAILED = "chat_failed"
    # 文档相关事件
    DOCUMENT_PROCESSING = "document_processing"
    DOCUMENT_PROCESSED = "document_processed"
    DOCUMENT_FAILED = "document_failed"
    # 向量相关事件
    VECTOR_SEARCH = "vector_search"
    VECTOR_SEARCH_COMPLETED = "vector_search_completed"
    # Agent 相关事件
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"


@dataclass
class ServiceRequest:
    """
    类级注释：服务请求数据类
    内部逻辑：封装服务请求的数据
    """
    # 属性：请求类型
    request_type: str
    # 属性：请求数据
    data: Dict[str, Any]
    # 属性：请求ID（用于追踪）
    request_id: Optional[str] = None
    # 属性：元数据
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ServiceResponse:
    """
    类级注释：服务响应数据类
    内部逻辑：封装服务响应的数据
    """
    # 属性：是否成功
    success: bool
    # 属性：响应数据
    data: Any
    # 属性：错误信息
    error: Optional[str] = None
    # 属性：请求ID
    request_id: Optional[str] = None


class ServiceColleague(ABC):
    """
    类级注释：服务同事组件抽象基类
    设计模式：中介者模式 - 同事接口
    职责：
        1. 定义服务组件的统一接口
        2. 允许服务通过中介者通信
    """

    def __init__(self, name: str):
        """
        函数级注释：初始化服务同事组件
        参数：
            name: 组件名称
        """
        # 属性：组件名称
        self._name = name
        # 属性：中介者引用
        self._mediator: Optional['ServiceMediator'] = None

    @property
    def name(self) -> str:
        """获取组件名称"""
        return self._name

    def set_mediator(self, mediator: 'ServiceMediator') -> None:
        """
        函数级注释：设置中介者
        参数：
            mediator: 中介者实例
        """
        self._mediator = mediator

    @abstractmethod
    async def handle_request(self, request: ServiceRequest) -> ServiceResponse:
        """
        函数级注释：处理服务请求（抽象方法）
        参数：
            request: 服务请求
        返回值：服务响应
        """
        pass

    async def send_request(
        self,
        target_service: str,
        request_type: str,
        data: Dict[str, Any]
    ) -> ServiceResponse:
        """
        函数级注释：通过中介者发送请求给其他服务
        参数：
            target_service: 目标服务名称
            request_type: 请求类型
            data: 请求数据
        返回值：服务响应
        """
        if self._mediator:
            request = ServiceRequest(
                request_type=request_type,
                data=data,
                metadata={"sender": self._name}
            )
            return await self._mediator.send_request(target_service, request)

        # 内部逻辑：中介者未设置时返回错误响应
        return ServiceResponse(
            success=False,
            data=None,
            error="中介者未设置"
        )


class ServiceMediator:
    """
    类级注释：服务中介者
    设计模式：中介者模式 - 具体中介者
    职责：
        1. 管理所有服务组件的注册
        2. 协调服务间的通信
        3. 提供统一的服务调用入口
        4. 处理服务调用失败和重试
    """

    def __init__(self):
        """
        函数级注释：初始化服务中介者
        """
        # 内部变量：服务注册表 {name: service}
        self._services: Dict[str, ServiceColleague] = {}

        # 内部变量：事件监听器 {event_type: [listeners]}
        self._event_listeners: Dict[ServiceEventType, List[Callable]] = {}

        # 内部变量：调用统计
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "service_calls": {}
        }

        logger.info("服务中介者初始化完成")

    def register_service(self, service: ServiceColleague) -> None:
        """
        函数级注释：注册服务组件
        内部逻辑：添加到注册表 -> 设置中介者引用 -> 初始化统计
        参数：
            service: 服务组件实例
        """
        self._services[service.name] = service
        service.set_mediator(self)
        self._stats["service_calls"][service.name] = 0
        logger.info(f"已注册服务: {service.name}")

    def unregister_service(self, name: str) -> None:
        """
        函数级注释：注销服务组件
        参数：
            name: 服务名称
        """
        if name in self._services:
            service = self._services.pop(name)
            service.set_mediator(None)
            self._stats["service_calls"].pop(name, None)
            logger.info(f"已注销服务: {name}")

    def get_service(self, name: str) -> Optional[ServiceColleague]:
        """
        函数级注释：获取服务组件
        参数：
            name: 服务名称
        返回值：服务组件或 None
        """
        return self._services.get(name)

    def has_service(self, name: str) -> bool:
        """
        函数级注释：检查服务是否已注册
        参数：
            name: 服务名称
        返回值：是否已注册
        """
        return name in self._services

    async def send_request(
        self,
        target_service: str,
        request: ServiceRequest
    ) -> ServiceResponse:
        """
        函数级注释：发送请求给目标服务
        内部逻辑：验证服务存在 -> 调用服务 -> 记录统计 -> 返回结果
        参数：
            target_service: 目标服务名称
            request: 服务请求
        返回值：服务响应
        """
        self._stats["total_requests"] += 1

        # 内部逻辑：验证服务是否存在
        service = self._services.get(target_service)
        if not service:
            self._stats["failed_requests"] += 1
            return ServiceResponse(
                success=False,
                data=None,
                error=f"服务不存在: {target_service}"
            )

        try:
            # 内部逻辑：调用服务处理请求
            response = await service.handle_request(request)

            # 内部逻辑：更新统计
            if response.success:
                self._stats["successful_requests"] += 1
            else:
                self._stats["failed_requests"] += 1

            self._stats["service_calls"][target_service] += 1

            return response

        except Exception as e:
            self._stats["failed_requests"] += 1
            logger.error(f"服务 {target_service} 处理请求失败: {str(e)}")
            return ServiceResponse(
                success=False,
                data=None,
                error=f"服务调用失败: {str(e)}"
            )

    def add_event_listener(
        self,
        event_type: ServiceEventType,
        listener: Callable
    ) -> None:
        """
        函数级注释：添加事件监听器
        参数：
            event_type: 事件类型
            listener: 监听器函数
        """
        if event_type not in self._event_listeners:
            self._event_listeners[event_type] = []
        self._event_listeners[event_type].append(listener)
        logger.debug(f"已添加事件监听器: {event_type.value}")

    def remove_event_listener(
        self,
        event_type: ServiceEventType,
        listener: Callable
    ) -> None:
        """
        函数级注释：移除事件监听器
        参数：
            event_type: 事件类型
            listener: 监听器函数
        """
        if event_type in self._event_listeners:
            try:
                self._event_listeners[event_type].remove(listener)
                logger.debug(f"已移除事件监听器: {event_type.value}")
            except ValueError:
                pass

    async def emit_event(
        self,
        event_type: ServiceEventType,
        data: Dict[str, Any]
    ) -> None:
        """
        函数级注释：触发事件
        内部逻辑：通知所有监听该事件的监听器
        参数：
            event_type: 事件类型
            data: 事件数据
        """
        listeners = self._event_listeners.get(event_type, [])
        for listener in listeners:
            try:
                if isinstance(listener, Callable):
                    await listener(data)
            except Exception as e:
                logger.error(f"事件监听器执行失败: {str(e)}")

    def get_stats(self) -> Dict[str, Any]:
        """
        函数级注释：获取统计信息
        返回值：统计信息字典
        """
        return self._stats.copy()

    def reset_stats(self) -> None:
        """
        函数级注释：重置统计信息
        """
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "service_calls": {name: 0 for name in self._services.keys()}
        }
        logger.info("服务中介者统计信息已重置")


# ============================================================================
# 具体服务同事组件实现（示例）
# ============================================================================

class ChatServiceColleague(ServiceColleague):
    """
    类级注释：聊天服务同事组件
    设计模式：中介者模式 - 具体同事
    职责：
        1. 处理聊天请求
        2. 协调文档搜索和 Agent 调用
    """

    def __init__(self, chat_service=None):
        """
        函数级注释：初始化聊天服务同事
        参数：
            chat_service: 聊天服务实例
        """
        super().__init__("chat_service")
        self._chat_service = chat_service

    async def handle_request(self, request: ServiceRequest) -> ServiceResponse:
        """
        函数级注释：处理聊天请求
        参数：
            request: 服务请求
        返回值：服务响应
        """
        if request.request_type == "chat":
            # 内部逻辑：处理聊天请求
            try:
                # 这里可以调用实际的聊天服务
                result = {"message": "聊天处理结果"}
                return ServiceResponse(success=True, data=result)
            except Exception as e:
                return ServiceResponse(success=False, data=None, error=str(e))

        return ServiceResponse(
            success=False,
            data=None,
            error=f"未知的请求类型: {request.request_type}"
        )


class DocumentServiceColleague(ServiceColleague):
    """
    类级注释：文档服务同事组件
    设计模式：中介者模式 - 具体同事
    职责：
        1. 处理文档搜索请求
        2. 处理文档处理请求
    """

    def __init__(self, document_service=None):
        """
        函数级注释：初始化文档服务同事
        参数：
            document_service: 文档服务实例
        """
        super().__init__("document_service")
        self._document_service = document_service

    async def handle_request(self, request: ServiceRequest) -> ServiceResponse:
        """
        函数级注释：处理文档请求
        参数：
            request: 服务请求
        返回值：服务响应
        """
        if request.request_type == "search":
            # 内部逻辑：处理搜索请求
            try:
                result = {"documents": []}
                return ServiceResponse(success=True, data=result)
            except Exception as e:
                return ServiceResponse(success=False, data=None, error=str(e))

        return ServiceResponse(
            success=False,
            data=None,
            error=f"未知的请求类型: {request.request_type}"
        )


class AgentServiceColleague(ServiceColleague):
    """
    类级注释：Agent 服务同事组件
    设计模式：中介者模式 - 具体同事
    职责：
        1. 处理 Agent 执行请求
        2. 协调工具调用
    """

    def __init__(self, agent_service=None):
        """
        函数级注释：初始化 Agent 服务同事
        参数：
            agent_service: Agent 服务实例
        """
        super().__init__("agent_service")
        self._agent_service = agent_service

    async def handle_request(self, request: ServiceRequest) -> ServiceResponse:
        """
        函数级注释：处理 Agent 请求
        参数：
            request: 服务请求
        返回值：服务响应
        """
        if request.request_type == "execute":
            # 内部逻辑：处理 Agent 执行请求
            try:
                result = {"result": "Agent 执行结果"}
                return ServiceResponse(success=True, data=result)
            except Exception as e:
                return ServiceResponse(success=False, data=None, error=str(e))

        return ServiceResponse(
            success=False,
            data=None,
            error=f"未知的请求类型: {request.request_type}"
        )


# ============================================================================
# 服务中介者工厂
# ============================================================================

class ServiceMediatorFactory:
    """
    类级注释：服务中介者工厂
    设计模式：工厂模式 + 单例模式
    职责：
        1. 创建和配置服务中介者
        2. 提供全局访问点
    """

    # 内部变量：单例实例
    _instance: Optional['ServiceMediatorFactory'] = None
    # 内部变量：中介者实例
    _mediator: Optional[ServiceMediator] = None

    def __new__(cls) -> 'ServiceMediatorFactory':
        """实现单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def create_standard_mediator(
        self,
        chat_service=None,
        document_service=None,
        agent_service=None
    ) -> ServiceMediator:
        """
        函数级注释：创建标准服务中介者
        内部逻辑：创建中介者 -> 注册标准服务
        参数：
            chat_service: 聊天服务实例
            document_service: 文档服务实例
            agent_service: Agent 服务实例
        返回值：配置好的服务中介者
        """
        mediator = ServiceMediator()

        # 内部逻辑：注册服务组件
        if chat_service:
            mediator.register_service(ChatServiceColleague(chat_service))

        if document_service:
            mediator.register_service(DocumentServiceColleague(document_service))

        if agent_service:
            mediator.register_service(AgentServiceColleague(agent_service))

        self._mediator = mediator
        logger.info("标准服务中介者创建完成")
        return mediator

    def get_mediator(self) -> Optional[ServiceMediator]:
        """
        函数级注释：获取已创建的中介者实例
        返回值：服务中介者实例或 None
        """
        return self._mediator


# 内部变量：导出所有公共接口
__all__ = [
    # 核心类
    'ServiceEventType',
    'ServiceRequest',
    'ServiceResponse',
    'ServiceColleague',
    'ServiceMediator',
    'ServiceMediatorFactory',
    # 具体同事组件
    'ChatServiceColleague',
    'DocumentServiceColleague',
    'AgentServiceColleague',
]
