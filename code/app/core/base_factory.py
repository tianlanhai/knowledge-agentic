# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：工厂基类模块
内部逻辑：提供统一的配置解析和实例缓存机制，使用模板方法模式消除重复代码
设计模式：模板方法模式、单例模式（实例缓存）、泛型设计
设计原则：DRY（不重复）、开闭原则（对扩展开放）、SOLID（依赖倒置）
参考项目：easy-dataset-file
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TypeVar, Generic, Set
from loguru import logger

# 内部变量：泛型类型 T，表示 LLM 或 Embedding 实例类型
T = TypeVar('T')


class BaseFactory(ABC, Generic[T]):
    """
    类级注释：工厂基类，定义所有工厂类的通用行为
    设计模式：模板方法模式
    职责：
        1. 定义配置解析的模板方法（子类实现具体配置获取）
        2. 提供统一的实例缓存机制
        3. 提供统一的运行时配置管理
        4. 提供统一的缓存键生成逻辑

    泛型参数：
        T: 工厂创建的实例类型（如 BaseChatModel、Embeddings）

    抽象方法（子类必须实现）：
        - _get_default_config(): 获取默认配置
        - _create_by_provider(): 根据提供商创建实例
        - SUPPORTED_PROVIDERS: 支持的提供商列表
    """

    # 抽象类变量：子类必须定义支持的提供商
    SUPPORTED_PROVIDERS: Dict[str, str] = {}

    # 内部类变量：运行时配置缓存（支持热切换）
    _runtime_config: Optional[Dict[str, Any]] = None

    # 内部类变量：实例缓存（避免重复创建，单例模式的变体）
    _instance_cache: Dict[str, T] = {}

    @classmethod
    def set_runtime_config(cls, config: Dict[str, Any]) -> None:
        """
        函数级注释：设置运行时配置并清除实例缓存

        配置优先级说明：
            运行时配置（数据库注入）是最高优先级配置来源。
            通过此方法设置的配置将覆盖所有其他配置来源。

        内部逻辑：更新配置 -> 清除所有缓存的实例 -> 记录日志
        参数：
            config: 配置字典，包含 provider、model、endpoint、api_key 等
                   来源：数据库模型配置（ModelConfig 或 EmbeddingConfig）
        """
        cls._runtime_config = config
        cls._instance_cache.clear()
        provider = config.get('provider', 'unknown')
        # 内部逻辑：添加诊断日志 - 记录完整的运行时配置
        logger.info(f"[配置优先级] 运行时配置已更新（优先级: ★★★★★ 数据库模型配置）")
        logger.info(f"[诊断] {cls.__name__}运行时配置详情: {config}")
        logger.info(f"{cls.__name__}运行时配置已更新: {provider}")

    @classmethod
    def _resolve_config(cls, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        函数级注释：解析配置优先级（模板方法）

        配置优先级（从高到低）：
            1. 传入配置（方法参数）- 临时配置，一次性使用
            2. 运行时配置（set_runtime_config）- 数据库模型配置注入
            3. 默认配置（_get_default_config）- 环境变量/配置文件/代码默认值

        参数：
            config: 可选的传入配置（最高优先级，一次性使用）
        返回值：合并后的配置字典
        """
        if config:
            logger.debug(f"[配置优先级] 使用传入配置（优先级: ★★★★★ 临时配置）")
            return config

        if cls._runtime_config:
            logger.debug(f"[配置优先级] 使用运行时配置（优先级: ★★★★★ 数据库模型配置）")
            return cls._runtime_config

        # 内部逻辑：调用子类实现的默认配置获取方法
        # 默认配置从 settings 读取，已包含环境变量 > .env文件 > 代码默认值的优先级
        default_config = cls._get_default_config()
        logger.debug(f"[配置优先级] 使用默认配置（优先级: ★★★☆☆ 环境变量/配置文件/代码默认值）")
        return default_config

    @classmethod
    @abstractmethod
    def _get_default_config(cls) -> Dict[str, Any]:
        """
        函数级注释：获取默认配置（抽象方法，子类必须实现）
        内部逻辑：从环境变量或 settings 获取默认配置
        返回值：默认配置字典
        """
        pass

    @classmethod
    def create_with_config(cls, config: Optional[Dict[str, Any]] = None, **kwargs) -> T:
        """
        函数级注释：使用配置创建实例（模板方法）
        内部逻辑：解析配置 -> 检查提供商支持 -> 创建实例
        参数：
            config: 可选的配置字典
            **kwargs: 额外的参数（如 streaming）
        返回值：实例
        异常：ValueError - 当提供商不支持时
        """
        resolved_config = cls._resolve_config(config)
        provider = resolved_config.get("provider", "unknown")

        if not cls._is_supported_provider(provider):
            supported_list = list(cls.SUPPORTED_PROVIDERS.keys())
            raise ValueError(
                f"不支持的提供商: {provider}。"
                f"支持的提供商: {supported_list}"
            )

        return cls._create_by_provider(provider, resolved_config, **kwargs)

    @classmethod
    @abstractmethod
    def _create_by_provider(cls, provider: str, config: Dict[str, Any], **kwargs) -> T:
        """
        函数级注释：根据提供商创建实例（抽象方法，子类必须实现）
        内部逻辑：根据 provider 类型分发到具体的创建方法
        参数：
            provider: 提供商 ID（如 ollama、zhipuai）
            config: 配置字典
            **kwargs: 额外的参数（如 streaming）
        返回值：提供商实例
        """
        pass

    @classmethod
    def _get_cache_key(cls, config: Dict[str, Any]) -> str:
        """
        函数级注释：生成缓存键（模板方法，可被子类覆盖）
        内部逻辑：provider_model 格式的字符串
        参数：
            config: 配置字典
        返回值：缓存键字符串
        """
        provider = config.get("provider", "unknown")
        model = config.get("model", "unknown")
        return f"{provider}_{model}"

    @classmethod
    def _is_supported_provider(cls, provider: str) -> bool:
        """
        函数级注释：检查提供商是否支持
        内部逻辑：检查 provider 是否在 SUPPORTED_PROVIDERS 中
        参数：
            provider: 提供商 ID
        返回值：是否支持
        """
        return provider.lower() in cls.SUPPORTED_PROVIDERS

    @classmethod
    def get_supported_providers(cls) -> Set[str]:
        """
        函数级注释：获取所有支持的提供商
        返回值：支持的提供商名称集合
        """
        return set(cls.SUPPORTED_PROVIDERS.keys())

    @classmethod
    def clear_cache(cls) -> None:
        """
        函数级注释：清除所有实例缓存
        内部逻辑：清空缓存字典 -> 记录日志 -> 用于强制重新创建实例
        """
        cls._instance_cache.clear()
        logger.info(f"{cls.__name__}实例缓存已清除")
