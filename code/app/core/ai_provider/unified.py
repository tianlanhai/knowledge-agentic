# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：统一AI工厂模块
内部逻辑：提供统一的入口创建AI组件
设计模式：外观模式 + 工厂模式 + 单例模式
设计原则：迪米特法则、单一职责原则
"""

from typing import Dict, Any, Optional, Tuple
from loguru import logger

from app.core.ai_provider.base import (
    AIProviderType,
    AIComponentType,
    AIProviderFactory,
)
from app.core.ai_provider.config import AIProviderConfig
from app.core.ai_provider.registry import AIProviderFactoryRegistry


class UnifiedAIFactory:
    """
    类级注释：统一 AI 工厂
    内部逻辑：提供统一的入口创建 AI 组件
    设计模式：外观模式 + 工厂模式
    职责：
        1. 管理当前配置
        2. 缓存创建的实例
        3. 提供统一的创建接口

    使用场景：
        - 应用全局的AI组件创建入口
        - 统一管理AI提供商配置
        - 实例复用和缓存
    """

    def __init__(self):
        """
        函数级注释：初始化统一工厂
        """
        # 内部变量：当前配置
        self._current_config: Optional[AIProviderConfig] = None

        # 内部变量：组件缓存
        self._llm_cache: Dict[str, Any] = {}
        self._embedding_cache: Dict[str, Any] = {}

    def set_config(self, config: AIProviderConfig) -> None:
        """
        函数级注释：设置当前配置
        内部逻辑：更新配置 -> 清空缓存
        参数：
            config - 提供商配置
        """
        self._current_config = config
        self._llm_cache.clear()
        self._embedding_cache.clear()
        logger.info(f"设置 AI 配置: provider={config.provider_type.value}")

    def create_llm(
        self,
        config: Optional[AIProviderConfig] = None,
        **kwargs
    ) -> Any:
        """
        函数级注释：创建 LLM 实例
        内部逻辑：使用传入配置或当前配置 -> 获取工厂 -> 创建实例
        参数：
            config - 提供商配置（可选）
            **kwargs - 额外参数
        返回值：LLM 实例
        """
        # 内部逻辑：确定配置
        provider_config = config or self._current_config

        if not provider_config:
            raise ValueError("未设置 AI 提供商配置")

        # 内部逻辑：生成缓存键
        cache_key = f"{provider_config.provider_type.value}_{provider_config.model or 'default'}"

        # 内部逻辑：检查缓存
        if cache_key in self._llm_cache:
            logger.debug(f"从缓存获取 LLM: {cache_key}")
            return self._llm_cache[cache_key]

        # 内部逻辑：获取工厂并创建
        factory = AIProviderFactoryRegistry.get_factory(provider_config.provider_type)
        llm = factory.create_llm(provider_config)

        # 内部逻辑：缓存实例
        self._llm_cache[cache_key] = llm

        return llm

    def create_embeddings(
        self,
        config: Optional[AIProviderConfig] = None,
        **kwargs
    ) -> Any:
        """
        函数级注释：创建 Embeddings 实例
        内部逻辑：使用传入配置或当前配置 -> 获取工厂 -> 创建实例
        参数：
            config - 提供商配置（可选）
            **kwargs - 额外参数
        返回值：Embeddings 实例
        """
        # 内部逻辑：确定配置
        provider_config = config or self._current_config

        if not provider_config:
            raise ValueError("未设置 AI 提供商配置")

        # 内部逻辑：生成缓存键
        cache_key = f"{provider_config.provider_type.value}_embedding_{provider_config.model or 'default'}"

        # 内部逻辑：检查缓存
        if cache_key in self._embedding_cache:
            logger.debug(f"从缓存获取 Embeddings: {cache_key}")
            return self._embedding_cache[cache_key]

        # 内部逻辑：获取工厂并创建
        factory = AIProviderFactoryRegistry.get_factory(provider_config.provider_type)

        # 内部逻辑：检查是否支持
        if not factory.supports_component(AIComponentType.EMBEDDING):
            raise ValueError(
                f"提供商 {provider_config.provider_type.value} "
                f"不支持 Embeddings"
            )

        embeddings = factory.create_embeddings(provider_config)

        # 内部逻辑：缓存实例
        self._embedding_cache[cache_key] = embeddings

        return embeddings

    def create_all(
        self,
        config: Optional[AIProviderConfig] = None
    ) -> Tuple[Any, Any]:
        """
        函数级注释：创建所有组件
        内部逻辑：同时创建 LLM 和 Embeddings
        参数：
            config - 提供商配置（可选）
        返回值：(LLM, Embeddings) 元组
        """
        llm = self.create_llm(config)
        embeddings = self.create_embeddings(config)
        return llm, embeddings

    def clear_cache(self) -> None:
        """
        函数级注释：清空所有缓存
        """
        self._llm_cache.clear()
        self._embedding_cache.clear()
        logger.info("统一 AI 工厂缓存已清空")


# 内部变量：全局统一工厂实例（单例模式）
unified_ai_factory = UnifiedAIFactory()


def create_ai_provider(
    provider_type: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs
) -> AIProviderConfig:
    """
    函数级注释：创建提供商配置的便捷函数
    参数：
        provider_type - 提供商类型字符串
        api_key - API 密钥
        base_url - 基础 URL
        model - 模型名称
        **kwargs - 额外参数
    返回值：提供商配置对象

    @example
    ```python
    config = create_ai_provider(
        provider_type="openai",
        api_key="sk-xxx",
        model="gpt-4"
    )
    ```
    """
    try:
        provider_enum = AIProviderType(provider_type)
    except ValueError:
        logger.warning(f"未知的提供商: {provider_type}, 使用 ollama")
        provider_enum = AIProviderType.OLLAMA

    return AIProviderConfig(
        provider_type=provider_enum,
        api_key=api_key,
        base_url=base_url,
        model=model,
        **kwargs
    )


# 内部变量：导出所有公共接口
__all__ = [
    'UnifiedAIFactory',
    'unified_ai_factory',
    'create_ai_provider',
]
