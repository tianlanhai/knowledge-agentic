# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：Embedding桥接抽象与工厂
内部逻辑：定义Embedding桥接接口，管理所有Embedding实现
设计模式：桥接模式（Bridge Pattern）+ 工厂模式
设计原则：SOLID - 依赖倒置原则、开闭原则、单一职责原则
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type
from langchain_core.embeddings import Embeddings
from loguru import logger


class EmbeddingBridge(ABC):
    """
    类级注释：Embedding桥接抽象类
    设计模式：桥接模式（Bridge Pattern）- 抽象部分
    职责：
        1. 定义Embedding实现的统一接口
        2. 解耦抽象（Embedding接口）与实现（具体提供商）
        3. 允许两者独立变化

    设计优势：
        - 新增提供商无需修改现有代码（开闭原则）
        - 抽象与实现可以独立扩展
        - 运行时可以动态切换实现
    """

    # 类变量：提供商标识符（子类必须覆盖）
    provider_id: str = "base"

    # 类变量：提供商显示名称
    provider_name: str = "Base Embedding"

    @abstractmethod
    def create_embeddings(self, config: Dict[str, Any]) -> Embeddings:
        """
        函数级注释：创建Embedding实例（抽象方法）
        内部逻辑：由具体实现类创建对应的Embedding实例
        参数：
            config: 配置字典，包含model、endpoint、api_key等
        返回值：Embeddings实例
        """
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        函数级注释：验证配置是否有效
        内部逻辑：检查必需的配置项是否存在且有效
        参数：
            config: 配置字典
        返回值：配置是否有效
        """
        pass

    @abstractmethod
    def get_default_model(self) -> str:
        """
        函数级注释：获取默认模型名称
        返回值：默认模型名称
        """
        pass

    def get_supported_models(self) -> list[str]:
        """
        函数级注释：获取支持的模型列表
        返回值：模型名称列表（默认返回包含默认模型的列表）
        """
        return [self.get_default_model()]


class EmbeddingBridgeFactory:
    """
    类级注释：Embedding桥接工厂
    设计模式：工厂模式 + 注册表模式
    职责：
        1. 管理所有Embedding实现（注册表）
        2. 根据提供商ID创建对应的桥接实例
        3. 支持动态注册新的实现

    设计优势：
        - 新增提供商只需注册，无需修改工厂代码（开闭原则）
        - 集中管理所有实现
        - 支持运行时动态扩展
    """

    # 内部类变量：实现注册表（provider_id -> 桥接类）
    _registry: Dict[str, Type[EmbeddingBridge]] = {}

    # 内部类变量：单例实例缓存
    _instances: Dict[str, EmbeddingBridge] = {}

    @classmethod
    def register(cls, bridge_class: Type[EmbeddingBridge]) -> None:
        """
        函数级注释：注册Embedding桥接实现
        内部逻辑：将桥接类添加到注册表中
        参数：
            bridge_class: 桥接类（继承自EmbeddingBridge）
        异常：ValueError - 当provider_id已存在时
        """
        provider_id = bridge_class.provider_id

        # 内部逻辑：检查是否已注册
        if provider_id in cls._registry:
            logger.warning(f"提供商 {provider_id} 已注册，将被覆盖")

        # 内部逻辑：注册桥接类
        cls._registry[provider_id] = bridge_class
        logger.info(f"已注册Embedding提供商: {provider_id} ({bridge_class.provider_name})")

    @classmethod
    def unregister(cls, provider_id: str) -> None:
        """
        函数级注释：注销Embedding桥接实现
        内部逻辑：从注册表中移除指定的提供商
        参数：
            provider_id: 提供商ID
        """
        if provider_id in cls._registry:
            del cls._registry[provider_id]
            # 内部逻辑：同时清除实例缓存
            if provider_id in cls._instances:
                del cls._instances[provider_id]
            logger.info(f"已注销Embedding提供商: {provider_id}")

    @classmethod
    def get_bridge(cls, provider_id: str) -> EmbeddingBridge:
        """
        函数级注释：获取指定提供商的桥接实例
        内部逻辑：检查注册表 -> 获取或创建实例 -> 返回
        参数：
            provider_id: 提供商ID
        返回值：EmbeddingBridge实例
        异常：ValueError - 当提供商未注册时
        """
        # 内部逻辑：Guard Clauses - 检查提供商是否已注册
        if provider_id not in cls._registry:
            supported = list(cls._registry.keys())
            raise ValueError(
                f"未注册的Embedding提供商: {provider_id}。"
                f"已注册的提供商: {supported}"
            )

        # 内部逻辑：检查实例缓存
        if provider_id not in cls._instances:
            bridge_class = cls._registry[provider_id]
            cls._instances[provider_id] = bridge_class()
            logger.debug(f"创建Embedding桥接实例: {provider_id}")

        return cls._instances[provider_id]

    @classmethod
    def create_embeddings(cls, provider_id: str, config: Dict[str, Any]) -> Embeddings:
        """
        函数级注释：创建Embedding实例（工厂方法）
        内部逻辑：获取桥接实例 -> 调用create_embeddings -> 返回
        参数：
            provider_id: 提供商ID
            config: 配置字典
        返回值：Embeddings实例
        """
        bridge = cls.get_bridge(provider_id)
        return bridge.create_embeddings(config)

    @classmethod
    def validate_provider_config(cls, provider_id: str, config: Dict[str, Any]) -> bool:
        """
        函数级注释：验证提供商配置
        内部逻辑：获取桥接实例 -> 调用validate_config -> 返回
        参数：
            provider_id: 提供商ID
            config: 配置字典
        返回值：配置是否有效
        """
        bridge = cls.get_bridge(provider_id)
        return bridge.validate_config(config)

    @classmethod
    def get_supported_providers(cls) -> Dict[str, str]:
        """
        函数级注释：获取所有已注册的提供商
        返回值：提供商ID到名称的映射字典
        """
        return {
            provider_id: bridge_class.provider_name
            for provider_id, bridge_class in cls._registry.items()
        }

    @classmethod
    def get_provider_models(cls, provider_id: str) -> list[str]:
        """
        函数级注释：获取指定提供商支持的模型列表
        内部逻辑：获取桥接实例 -> 调用get_supported_models -> 返回
        参数：
            provider_id: 提供商ID
        返回值：模型名称列表
        """
        bridge = cls.get_bridge(provider_id)
        return bridge.get_supported_models()

    @classmethod
    def is_registered(cls, provider_id: str) -> bool:
        """
        函数级注释：检查提供商是否已注册
        参数：
            provider_id: 提供商ID
        返回值：是否已注册
        """
        return provider_id in cls._registry

    @classmethod
    def clear_instances(cls) -> None:
        """
        函数级注释：清除所有实例缓存
        内部逻辑：清空实例缓存字典 -> 记录日志
        """
        cls._instances.clear()
        logger.info("Embedding桥接实例缓存已清除")
