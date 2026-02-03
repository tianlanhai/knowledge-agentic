# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：AI提供商工厂注册表模块
内部逻辑：管理所有提供商工厂的注册和获取
设计模式：工厂模式 + 注册表模式
设计原则：开闭原则、单一职责原则
"""

from typing import Dict, Type, List
from loguru import logger

from app.core.ai_provider.base import AIProviderType, AIProviderFactory


class AIProviderFactoryRegistry:
    """
    类级注释：AI 提供商工厂注册表
    内部逻辑：管理所有提供商工厂的注册和获取
    设计模式：工厂模式 + 注册表模式
    职责：
        1. 注册提供商工厂
        2. 获取工厂实例
        3. 列出支持的提供商

    使用场景：
        - 动态注册新的提供商
        - 获取指定提供商的工厂
        - 查询所有支持的提供商
    """

    # 内部变量：工厂注册表
    _factories: Dict[AIProviderType, Type[AIProviderFactory]] = {}

    @classmethod
    def register(
        cls,
        provider_type: AIProviderType,
        factory_class: Type[AIProviderFactory]
    ) -> None:
        """
        函数级注释：注册提供商工厂
        参数：
            provider_type - 提供商类型
            factory_class - 工厂类
        """
        cls._factories[provider_type] = factory_class
        logger.info(f"注册提供商工厂: {provider_type.value}")

    @classmethod
    def unregister(cls, provider_type: AIProviderType) -> None:
        """
        函数级注释：注销提供商工厂
        参数：
            provider_type - 提供商类型
        """
        cls._factories.pop(provider_type, None)
        logger.info(f"注销提供商工厂: {provider_type.value}")

    @classmethod
    def get_factory(cls, provider_type: AIProviderType) -> AIProviderFactory:
        """
        函数级注释：获取提供商工厂实例
        参数：
            provider_type - 提供商类型
        返回值：工厂实例
        异常：ValueError - 提供商不支持时抛出
        """
        factory_class = cls._factories.get(provider_type)

        if not factory_class:
            supported = [pt.value for pt in cls._factories.keys()]
            raise ValueError(
                f"不支持的提供商: {provider_type.value}. "
                f"支持的提供商: {supported}"
            )

        return factory_class()

    @classmethod
    def supported_providers(cls) -> List[AIProviderType]:
        """
        函数级注释：获取所有支持的提供商
        返回值：提供商类型列表
        """
        return list(cls._factories.keys())


# 内部变量：导出所有公共接口
__all__ = [
    'AIProviderFactoryRegistry',
]
