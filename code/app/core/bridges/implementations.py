# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：Embedding桥接具体实现类
内部逻辑：实现各个Embedding提供商的具体创建逻辑
设计模式：桥接模式（Bridge Pattern）- 实现部分
设计原则：SOLID - 单一职责原则、开闭原则
"""

from typing import Dict, Any, List
from langchain_community.embeddings import OllamaEmbeddings, HuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings
from loguru import logger

from app.core.bridges.embedding_bridge import EmbeddingBridge, EmbeddingBridgeFactory
from app.core.config import settings
from app.core.endpoint_utils import EndpointUtils


class OllamaEmbeddingImpl(EmbeddingBridge):
    """
    类级注释：Ollama Embedding桥接实现
    设计模式：桥接模式 - 具体实现类
    职责：创建和管理Ollama Embedding实例
    """

    provider_id = "ollama"
    provider_name = "Ollama本地模型"

    def create_embeddings(self, config: Dict[str, Any]) -> Embeddings:
        """
        函数级注释：创建Ollama Embedding实例
        内部逻辑：规范化endpoint -> 创建OllamaEmbeddings -> 返回
        参数：
            config: 配置字典，包含endpoint、model等
        返回值：OllamaEmbeddings实例
        """
        actual_endpoint = config.get("endpoint", settings.OLLAMA_BASE_URL)
        normalized_endpoint = EndpointUtils.normalize_ollama_endpoint(actual_endpoint)
        actual_model = config.get("model", settings.EMBEDDING_MODEL)

        logger.info(f"[Embedding] 创建 Ollama Embeddings - endpoint: {normalized_endpoint}, model: {actual_model}")

        return OllamaEmbeddings(
            base_url=normalized_endpoint,
            model=actual_model
        )

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        函数级注释：验证Ollama配置
        内部逻辑：检查model是否存在
        参数：
            config: 配置字典
        返回值：配置是否有效
        """
        model = config.get("model", settings.EMBEDDING_MODEL)
        return bool(model)

    def get_default_model(self) -> str:
        """获取默认模型名称"""
        return settings.EMBEDDING_MODEL

    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表"""
        return [
            "nomic-embed-text",
            "mxbai-embed-large",
            "all-minilm",
            "bge-large-zh-v1.5"
        ]


class ZhipuAIEmbeddingImpl(EmbeddingBridge):
    """
    类级注释：智谱AI Embedding桥接实现
    设计模式：桥接模式 - 具体实现类
    职责：创建和管理智谱AI Embedding实例
    """

    provider_id = "zhipuai"
    provider_name = "智谱AI"

    def create_embeddings(self, config: Dict[str, Any]) -> Embeddings:
        """
        函数级注释：创建智谱AI Embedding实例
        内部逻辑：规范化endpoint -> 创建ZhipuAIEmbeddings -> 返回
        参数：
            config: 配置字典，包含api_key、model、endpoint等
        返回值：ZhipuAIEmbeddings实例
        """
        from app.utils.zhipuai_embeddings import ZhipuAIEmbeddings

        endpoint = config.get("endpoint", settings.zhipuai_embedding_base_url)
        normalized_endpoint = EndpointUtils.normalize_zhipuai_endpoint(endpoint, "/embeddings")

        return ZhipuAIEmbeddings(
            api_key=config.get("api_key", settings.ZHIPUAI_API_KEY),
            model=config.get("model", settings.ZHIPUAI_EMBEDDING_MODEL),
            api_base=normalized_endpoint
        )

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        函数级注释：验证智谱AI配置
        内部逻辑：检查api_key和model是否存在
        参数：
            config: 配置字典
        返回值：配置是否有效
        """
        api_key = config.get("api_key", settings.ZHIPUAI_API_KEY)
        model = config.get("model", settings.ZHIPUAI_EMBEDDING_MODEL)
        return bool(api_key and model)

    def get_default_model(self) -> str:
        """获取默认模型名称"""
        return settings.ZHIPUAI_EMBEDDING_MODEL

    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表"""
        return ["embedding-2", "embedding-3"]


class LocalEmbeddingImpl(EmbeddingBridge):
    """
    类级注释：本地HuggingFace Embedding桥接实现
    设计模式：桥接模式 - 具体实现类
    职责：创建和管理本地HuggingFace Embedding实例
    """

    provider_id = "local"
    provider_name = "本地HuggingFace模型"

    def create_embeddings(self, config: Dict[str, Any]) -> Embeddings:
        """
        函数级注释：创建本地HuggingFace Embedding实例
        内部逻辑：确定设备 -> 解析模型路径 -> 创建HuggingFaceEmbeddings -> 返回
        参数：
            config: 配置字典，包含model、device等
        返回值：HuggingFaceEmbeddings实例
        """
        device = config.get("device", settings.DEVICE)
        if device == "auto":
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "cpu"

        model_kwargs = {'device': device}
        model_path = config.get("model", settings.LOCAL_EMBEDDING_MODEL_PATH)

        # 内部逻辑：解析模型路径，支持相对路径或绝对路径
        if "/" in model_path and not model_path.startswith(("./", "/", "\\\\")):
            import os
            local_dir = settings.LOCAL_MODEL_DIR
            if local_dir and os.path.exists(local_dir):
                model_dir_name = model_path.split("/")[-1]
                potential_path = os.path.join(local_dir, model_dir_name)
                if os.path.exists(potential_path):
                    model_path = potential_path
                    logger.info(f"使用本地模型目录: {model_path}")

        # 内部逻辑：设置离线模式环境变量，替代 local_files_only 参数
        import os
        os.environ['TRANSFORMERS_OFFLINE'] = '1'

        return HuggingFaceEmbeddings(
            model_name=model_path,
            model_kwargs=model_kwargs,
            encode_kwargs={
                'normalize_embeddings': True
            }
        )

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        函数级注释：验证本地模型配置
        内部逻辑：检查model路径是否存在
        参数：
            config: 配置字典
        返回值：配置是否有效
        """
        import os
        model_path = config.get("model", settings.LOCAL_EMBEDDING_MODEL_PATH)
        return os.path.exists(model_path) if model_path else False

    def get_default_model(self) -> str:
        """获取默认模型名称"""
        return settings.LOCAL_EMBEDDING_MODEL_PATH

    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表"""
        return ["BAAI/bge-large-zh-v1.5", "BAAI/bge-small-zh-v1.5"]


class OpenAIEmbeddingImpl(EmbeddingBridge):
    """
    类级注释：OpenAI Embedding桥接实现
    设计模式：桥接模式 - 具体实现类
    职责：创建和管理OpenAI Embedding实例
    """

    provider_id = "openai"
    provider_name = "OpenAI"

    def create_embeddings(self, config: Dict[str, Any]) -> Embeddings:
        """
        函数级注释：创建OpenAI Embedding实例
        参数：
            config: 配置字典，包含api_key、model、endpoint等
        返回值：OpenAI Embeddings实例
        """
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(
            api_key=config.get("api_key", ""),
            model=config.get("model", "text-embedding-3-small"),
            base_url=config.get("endpoint", "https://api.openai.com/v1")
        )

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        函数级注释：验证OpenAI配置
        内部逻辑：检查api_key是否存在
        参数：
            config: 配置字典
        返回值：配置是否有效
        """
        api_key = config.get("api_key", "")
        return bool(api_key)

    def get_default_model(self) -> str:
        """获取默认模型名称"""
        return "text-embedding-3-small"

    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表"""
        return [
            "text-embedding-3-small",
            "text-embedding-3-large",
            "text-embedding-ada-002"
        ]


# 内部逻辑：自动注册所有实现类
def register_all_implementations() -> None:
    """
    函数级注释：注册所有Embedding桥接实现
    内部逻辑：遍历所有实现类并注册到工厂
    设计优势：新增实现类只需在此添加注册代码
    """
    implementations = [
        OllamaEmbeddingImpl,
        ZhipuAIEmbeddingImpl,
        LocalEmbeddingImpl,
        OpenAIEmbeddingImpl,
    ]

    for impl in implementations:
        EmbeddingBridgeFactory.register(impl)

    logger.info(f"已自动注册 {len(implementations)} 个Embedding提供商")


# 内部逻辑：模块导入时自动注册
register_all_implementations()
