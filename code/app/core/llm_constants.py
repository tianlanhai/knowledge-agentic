# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：LLM提供商常量配置
内部逻辑：定义支持的LLM和Embedding提供商及其默认配置
参考项目：easy-dataset-file
"""

from typing import List, Dict, Any

# 支持的LLM提供商列表
LLM_PROVIDERS: List[Dict[str, Any]] = [
    {
        "id": "ollama",
        "name": "Ollama",
        "default_endpoint": "http://127.0.0.1:11434/api",
        "default_models": ["deepseek-r1:8b", "llama3:8b", "qwen2:7b", "gemma2:9b"],
        "type": "text"
    },
    {
        "id": "zhipuai",
        "name": "智谱AI",
        "default_endpoint": "https://open.bigmodel.cn/api/paas/v4/",
        "default_models": ["glm-4.5-air", "glm-4", "glm-3-turbo", "glm-4-flash"],
        "type": "text"
    },
    {
        "id": "openai",
        "name": "OpenAI",
        "default_endpoint": "https://api.openai.com/v1/",
        "default_models": ["gpt-4o", "gpt-4o-mini", "o1-mini", "gpt-4-turbo"],
        "type": "text"
    },
    {
        "id": "minimax",
        "name": "MiniMax",
        "default_endpoint": "https://api.minimax.chat/v1/",
        "default_models": ["abab5.5-chat", "abab5.5s-chat"],
        "type": "text"
    },
    {
        "id": "moonshot",
        "name": "月之暗面",
        "default_endpoint": "https://api.moonshot.cn/v1",
        "default_models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
        "type": "text"
    },
    {
        "id": "deepseek",
        "name": "DeepSeek",
        "default_endpoint": "https://api.deepseek.com/v1",
        "default_models": ["deepseek-chat", "deepseek-coder"],
        "type": "text"
    },
]

# Embedding提供商列表
EMBEDDING_PROVIDERS: List[Dict[str, Any]] = [
    {
        "id": "ollama",
        "name": "Ollama",
        "default_endpoint": "http://127.0.0.1:11434/api",
        "default_models": ["mxbai-embed-large:latest", "nomic-embed-text", "all-minilm"],
        "type": "embedding"
    },
    {
        "id": "zhipuai",
        "name": "智谱AI",
        "default_endpoint": "https://open.bigmodel.cn/api/paas/v4/",
        "default_models": ["embedding-3", "embedding-2"],
        "type": "embedding"
    },
    {
        "id": "local",
        "name": "本地模型",
        "default_endpoint": "",
        "default_models": ["BAAI/bge-large-zh-v1.5", "BAAI/bge-small-zh-v1.5"],
        "type": "embedding"
    },
    {
        "id": "openai",
        "name": "OpenAI",
        "default_endpoint": "https://api.openai.com/v1/",
        "default_models": ["text-embedding-3-small", "text-embedding-3-large", "text-embedding-ada-002"],
        "type": "embedding"
    },
]

# 默认模型设置参数
DEFAULT_MODEL_SETTINGS: Dict[str, Any] = {
    "temperature": 0.7,
    "max_tokens": 8192,
    "top_p": 0.9,
    "top_k": 0
}

# 提供商ID到名称的映射（用于快速查找）
PROVIDER_ID_MAP: Dict[str, str] = {
    provider["id"]: provider["name"] for provider in LLM_PROVIDERS + EMBEDDING_PROVIDERS
}

# 内部变量：支持本地Embedding的提供商列表
LOCAL_EMBEDDING_PROVIDERS: List[str] = ["local"]

# 内部变量：支持云端API的提供商列表
CLOUD_API_PROVIDERS: List[str] = ["zhipuai", "openai", "minimax", "moonshot", "deepseek"]


def get_provider_by_id(provider_id: str) -> Dict[str, Any] | None:
    """
    函数级注释：根据提供商ID获取提供商信息
    参数：
        provider_id: 提供商ID
    返回值：提供商配置字典，未找到返回None
    """
    # 内部逻辑：先在LLM提供商中查找
    for provider in LLM_PROVIDERS:
        if provider["id"] == provider_id:
            return provider

    # 内部逻辑：再在Embedding提供商中查找
    for provider in EMBEDDING_PROVIDERS:
        if provider["id"] == provider_id:
            return provider

    return None


def is_local_embedding(provider_id: str) -> bool:
    """
    函数级注释：判断是否为本地Embedding提供商
    参数：
        provider_id: 提供商ID
    返回值：是否为本地Embedding
    """
    return provider_id in LOCAL_EMBEDDING_PROVIDERS


def is_cloud_provider(provider_id: str) -> bool:
    """
    函数级注释：判断是否为云端API提供商
    参数：
        provider_id: 提供商ID
    返回值：是否为云端提供商
    """
    return provider_id in CLOUD_API_PROVIDERS


def get_default_model(provider_id: str, provider_type: str = "llm") -> str:
    """
    函数级注释：获取提供商的默认模型
    参数：
        provider_id: 提供商ID
        provider_type: 提供商类型（llm或embedding）
    返回值：默认模型名称，未找到返回空字符串
    """
    providers = LLM_PROVIDERS if provider_type == "llm" else EMBEDDING_PROVIDERS

    for provider in providers:
        if provider["id"] == provider_id:
            models = provider.get("default_models", [])
            return models[0] if models else ""

    return ""
