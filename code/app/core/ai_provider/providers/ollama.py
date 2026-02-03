# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：Ollama提供商工厂模块
内部逻辑：创建 Ollama 的 LLM 和 Embedding 实例
设计模式：抽象工厂模式 + 模板方法模式 - 具体工厂
设计原则：单一职责原则、DRY原则
"""

from typing import Any
from loguru import logger

from app.core.ai_provider.base import AIProviderType, AIComponentType
from app.core.ai_provider.base_factory import BaseAIProviderFactory
from app.core.ai_provider.config import AIProviderConfig
from app.core.endpoint_utils import EndpointUtils


class OllamaProviderFactory(BaseAIProviderFactory):
    """
    类级注释：Ollama 提供商工厂
    设计模式：模板方法模式 - 具体实现
    职责：
        1. 创建 Ollama LLM 实例
        2. 创建 Ollama Embeddings 实例
        3. 定义默认模型名称
    """

    provider_type = AIProviderType.OLLAMA

    # 内部变量：默认模型配置
    DEFAULT_LLM_MODEL = "llama2"
    DEFAULT_EMBEDDING_MODEL = "llama2"

    # 内部变量：Ollama需要base_url
    REQUIRES_BASE_URL = True

    def _get_llm_class(self) -> type:
        """
        函数级注释：获取Ollama LLM类
        返回值：ChatOllama类
        """
        try:
            from langchain_community.chat_models import ChatOllama
        except ImportError:
            from langchain_community.chat_models import ChatOllama as ChatOllamaImport
            ChatOllama = ChatOllamaImport
        return ChatOllama

    def _get_embedding_class(self) -> type:
        """
        函数级注释：获取Ollama Embedding类
        返回值：OllamaEmbeddings类
        """
        try:
            from langchain_community.embeddings import OllamaEmbeddings
        except ImportError:
            from langchain_community.embeddings import OllamaEmbeddings as OllamaEmbeddingsImport
            OllamaEmbeddings = OllamaEmbeddingsImport
        return OllamaEmbeddings

    def _customize_llm_params(self, params: dict, config: AIProviderConfig) -> dict:
        """
        函数级注释：自定义LLM参数
        内部逻辑：Ollama必须有base_url，且需要规范化endpoint（移除/api后缀）
        参数：
            params - 参数字典
            config - 提供商配置
        返回值：定制后的参数
        """
        # 内部逻辑：确保base_url存在并规范化
        if config.base_url:
            # 内部逻辑：规范化Ollama端点，移除末尾的/api或/
            # Ollama API格式：http://host:port/api/chat，所以base应该是http://host:port
            normalized_url = EndpointUtils.normalize_ollama_endpoint(config.base_url)
            params["base_url"] = normalized_url
        return params

    def _customize_embedding_params(self, params: dict, config: AIProviderConfig) -> dict:
        """
        函数级注释：自定义Embedding参数
        内部逻辑：Ollama embeddings也需要规范化endpoint
        参数：
            params - 参数字典
            config - 提供商配置
        返回值：定制后的参数
        """
        # 内部逻辑：确保base_url存在并规范化
        if config.base_url:
            normalized_url = EndpointUtils.normalize_ollama_endpoint(config.base_url)
            params["base_url"] = normalized_url
        return params


# 内部变量：导出所有公共接口
__all__ = [
    'OllamaProviderFactory',
]
