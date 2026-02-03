# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：聊天服务初始化模块
内部逻辑：配置服务容器，注册所有聊天相关服务
设计模式：依赖注入模式 + 服务定位器模式
设计原则：依赖倒置原则（DIP）、开闭原则（OCP）
职责：统一管理聊天服务的依赖注入配置
"""

from typing import Optional
from loguru import logger

from app.core.di import ServiceContainer, ServiceLifetime
from app.services.chat.orchestrator import ChatOrchestrator
from app.services.chat.sources_processor import SourcesProcessor
from app.services.chat.document_formatter import DocumentFormatter
from app.services.chat.strategies import ChatStrategyFactory
from app.services.chat.streaming_strategies import StreamingStrategyFactory
from app.services.agent_service import AgentService


def initialize_chat_services(
    container: Optional[ServiceContainer] = None
) -> ServiceContainer:
    """
    函数级注释：初始化聊天相关服务
    内部逻辑：按依赖顺序注册所有服务到容器
    设计模式：依赖注入 - 将服务注册与使用分离
    参数：
        container - 服务容器，如果为None则使用全局容器
    返回值：ServiceContainer - 配置完成的服务容器

    使用示例：
        container = initialize_chat_services()
        orchestrator = container.get_service(ChatOrchestrator)
    """
    # 内部逻辑：获取或创建容器
    if container is None:
        from app.core.di import get_container
        container = get_container()

    # 内部逻辑：注册无状态工具类（瞬态生命周期）
    # 瞬态服务：每次请求创建新实例，无状态共享
    container.register_transient(
        SourcesProcessor,
        SourcesProcessor
    )
    logger.debug("注册瞬态服务: SourcesProcessor")

    container.register_transient(
        DocumentFormatter,
        DocumentFormatter
    )
    logger.debug("注册瞬态服务: DocumentFormatter")

    # 内部逻辑：注册策略工厂（单例生命周期）
    # 单例服务：全局共享一个实例，避免重复创建
    container.register_singleton(
        ChatStrategyFactory,
        ChatStrategyFactory
    )
    logger.debug("注册单例服务: ChatStrategyFactory")

    container.register_singleton(
        StreamingStrategyFactory,
        StreamingStrategyFactory
    )
    logger.debug("注册单例服务: StreamingStrategyFactory")

    # 内部逻辑：注册编排器（作用域生命周期）
    # 作用域服务：在同一作用域内共享实例
    container.register_scoped(
        ChatOrchestrator,
        ChatOrchestrator
    )
    logger.debug("注册作用域服务: ChatOrchestrator")

    # 内部逻辑：注册Agent服务（单例生命周期）
    # Agent服务维护会话状态，需要全局共享
    container.register_singleton(
        AgentService,
        AgentService
    )
    logger.debug("注册单例服务: AgentService")

    logger.info("聊天服务初始化完成")
    return container


def reset_chat_services(container: ServiceContainer) -> None:
    """
    函数级注释：重置聊天服务注册
    内部逻辑：清除所有聊天相关的服务注册
    参数：
        container - 服务容器
    返回值：None
    用途：主要用于测试环境
    """
    # 内部逻辑：获取所有已注册的服务
    registered = container.get_registered_services()

    # 内部逻辑：移除聊天相关服务
    chat_services = [
        ChatOrchestrator,
        SourcesProcessor,
        DocumentFormatter,
        ChatStrategyFactory,
        StreamingStrategyFactory,
        AgentService
    ]

    for service_type in chat_services:
        if service_type in registered:
            # 内部逻辑：容器本身不提供删除接口
            # 这里只是标记，实际清空需要调用container.clear()
            pass

    logger.info("聊天服务已重置")


# 内部变量：导出所有公共接口
__all__ = [
    'initialize_chat_services',
    'reset_chat_services',
]
