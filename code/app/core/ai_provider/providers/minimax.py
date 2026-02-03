# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：MiniMax提供商工厂模块
设计模式：抽象工厂模式 + 模板方法模式 - 具体工厂
设计原则：单一职责原则、DRY原则
"""

from typing import Any
from loguru import logger

from app.core.ai_provider.base import AIProviderType
from app.core.ai_provider.base_factory import BaseAIProviderFactory
from app.core.ai_provider.config import AIProviderConfig


class MiniMaxProviderFactory(BaseAIProviderFactory):
    """
    类级注释：MiniMax 提供商工厂
    设计模式：模板方法模式 - 具体实现
    职责：
        1. 创建 MiniMax LLM 实例
        2. 创建 MiniMax Embeddings 实例
        3. 定义默认模型名称
    """

    provider_type = AIProviderType.MINIMAX

    # 内部变量：默认模型配置
    DEFAULT_LLM_MODEL = "abab5.5-chat"
    DEFAULT_EMBEDDING_MODEL = "embedding-v1"

    # 内部变量：MiniMax需要api_key
    REQUIRES_API_KEY = True

    def _get_llm_class(self) -> type:
        """
        函数级注释：获取MiniMax LLM类
        内部逻辑：返回模拟类（需要根据实际SDK实现）
        """
        # 内部逻辑：返回模拟实例（需要根据实际SDK实现）
        return type("MiniMaxLLM", (), {})

    def _get_embedding_class(self) -> type:
        """
        函数级注释：获取MiniMax Embedding类
        内部逻辑：返回模拟类（需要根据实际SDK实现）
        """
        # 内部逻辑：返回模拟实例（需要根据实际SDK实现）
        return type("MiniMaxEmbeddings", (), {})

    def create_llm(self, config: AIProviderConfig) -> Any:
        """
        函数级注释：创建 MiniMax LLM 实例（覆盖基类方法）
        内部逻辑：MiniMax需要特殊处理，返回模拟实例
        """
        params = self._build_llm_params(config)
        logger.info(f"创建 MiniMax LLM: model={params.get('model')}")
        return type("MiniMaxLLM", (), params)()

    def create_embeddings(self, config: AIProviderConfig) -> Any:
        """
        函数级注释：创建 MiniMax Embeddings 实例（覆盖基类方法）
        内部逻辑：MiniMax需要特殊处理，返回模拟实例
        """
        params = self._build_embedding_params(config)
        logger.info(f"创建 MiniMax Embeddings: model={params.get('model')}")
        return type("MiniMaxEmbeddings", (), params)()


__all__ = ['MiniMaxProviderFactory']
