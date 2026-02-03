# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：OpenAI提供商工厂模块
设计模式：抽象工厂模式 + 模板方法模式 - 具体工厂
设计原则：单一职责原则、DRY原则
"""

from typing import Any
from loguru import logger

from app.core.ai_provider.base import AIProviderType
from app.core.ai_provider.base_factory import BaseAIProviderFactory
from app.core.ai_provider.config import AIProviderConfig


class OpenAIProviderFactory(BaseAIProviderFactory):
    """
    类级注释：OpenAI 提供商工厂
    设计模式：模板方法模式 - 具体实现
    职责：
        1. 创建 OpenAI LLM 实例
        2. 创建 OpenAI Embeddings 实例
        3. 定义默认模型名称
    """

    provider_type = AIProviderType.OPENAI

    # 内部变量：默认模型配置
    DEFAULT_LLM_MODEL = "gpt-3.5-turbo"
    DEFAULT_EMBEDDING_MODEL = "text-embedding-ada-002"

    # 内部变量：OpenAI需要api_key
    REQUIRES_API_KEY = True

    def _get_llm_class(self) -> type:
        """函数级注释：获取OpenAI LLM类"""
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            from langchain.chat_models import ChatOpenAI
        return ChatOpenAI

    def _get_embedding_class(self) -> type:
        """函数级注释：获取OpenAI Embedding类"""
        try:
            from langchain_openai import OpenAIEmbeddings
        except ImportError:
            from langchain.embeddings import OpenAIEmbeddings
        return OpenAIEmbeddings


__all__ = ['OpenAIProviderFactory']
