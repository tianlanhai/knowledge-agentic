# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：DeepSeek提供商工厂模块
设计模式：抽象工厂模式 + 模板方法模式 - 具体工厂
设计原则：单一职责原则、DRY原则
"""

from typing import Any
from loguru import logger

from app.core.ai_provider.base import AIProviderType, AIComponentType
from app.core.ai_provider.base_factory import BaseAIProviderFactory
from app.core.ai_provider.config import AIProviderConfig


class DeepSeekProviderFactory(BaseAIProviderFactory):
    """
    类级注释：DeepSeek 提供商工厂
    设计模式：模板方法模式 - 具体实现
    职责：
        1. 创建 DeepSeek LLM 实例
        2. 创建 DeepSeek Embeddings 实例
        3. 定义默认模型名称
    """

    provider_type = AIProviderType.DEEPSEEK

    # 内部变量：默认模型配置
    DEFAULT_LLM_MODEL = "deepseek-chat"
    DEFAULT_EMBEDDING_MODEL = "deepseek-embedding"

    # 内部变量：DeepSeek需要api_key
    REQUIRES_API_KEY = True

    # 内部变量：默认base_url
    DEFAULT_BASE_URL = "https://api.deepseek.com/v1"

    def _get_llm_class(self) -> type:
        """函数级注释：获取DeepSeek LLM类（使用OpenAI兼容接口）"""
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            from langchain.chat_models import ChatOpenAI
        return ChatOpenAI

    def _get_embedding_class(self) -> type:
        """函数级注释：获取DeepSeek Embedding类（使用OpenAI兼容接口）"""
        try:
            from langchain_openai import OpenAIEmbeddings
        except ImportError:
            from langchain.embeddings import OpenAIEmbeddings
        return OpenAIEmbeddings

    def _customize_llm_params(self, params: dict, config: AIProviderConfig) -> dict:
        """函数级注释：自定义LLM参数"""
        if "base_url" not in params:
            params["base_url"] = config.base_url or self.DEFAULT_BASE_URL
        return params

    def _customize_embedding_params(self, params: dict, config: AIProviderConfig) -> dict:
        """函数级注释：自定义Embedding参数"""
        if "base_url" not in params:
            params["base_url"] = config.base_url or self.DEFAULT_BASE_URL
        return params

    def supports_component(self, component_type: AIComponentType) -> bool:
        """
        函数级注释：检查组件支持
        内部逻辑：DeepSeek 主要用于对话，嵌入模型可能不支持
        """
        return component_type == AIComponentType.LLM


__all__ = ['DeepSeekProviderFactory']
