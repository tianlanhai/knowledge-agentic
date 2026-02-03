# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：智谱AI Embeddings 实现
内部逻辑：使用智谱AI的 Embedding API 进行文本向量化
说明：轻量级方案，无需本地模型，适合生产环境使用
"""

from typing import List
from langchain_core.embeddings import Embeddings
from loguru import logger

# 导入配置以获取 API 基础地址
from app.core.config import settings


class ZhipuAIEmbeddings(Embeddings):
    """
    类级注释：智谱AI Embeddings 包装类
    使用智谱AI的 Embedding-2/Embedding-3 模型进行文本向量化
    """

    def __init__(
        self,
        api_key: str = "",
        model: str = "embedding-3",
        api_base: str = ""
    ):
        """
        函数级注释：初始化智谱AI Embeddings
        内部逻辑：优先使用传入参数，否则从配置中读取独立配置或通用配置
        参数：
            api_key: 智谱AI API密钥（可选）
            model: 模型名称，默认 embedding-3
            api_base: API基础URL（可选）
        """
        # 内部逻辑：优先使用传入参数，否则从配置中读取（支持独立配置）
        self.api_key = api_key or settings.zhipuai_embedding_api_key
        if not self.api_key:
            raise ValueError(
                "ZHIPUAI_EMBEDDING_API_KEY 或 ZHIPUAI_API_KEY 未设置。"
                "请在.env文件中设置ZHIPUAI_EMBEDDING_API_KEY。"
            )

        self.model = model
        # 内部逻辑：规范化 api_base，确保以 /embeddings 结尾
        # 支持传入完整路径或仅 base URL
        if api_base:
            # 内部逻辑：如果传入的 api_base 不包含 /embeddings，自动添加
            if not api_base.endswith("/embeddings"):
                api_base = api_base.rstrip("/") + "/embeddings"
            self.api_base = api_base
        else:
            # 内部逻辑：从配置中读取独立配置，并确保包含 /embeddings
            base_url = settings.zhipuai_embedding_base_url
            if not base_url.endswith("/embeddings"):
                base_url = base_url.rstrip("/") + "/embeddings"
            self.api_base = base_url

    def _embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        函数级注释：批量将文档转换为向量
        参数：texts - 文本列表
        返回值：向量列表
        """
        import requests

        # 内部逻辑：调用智谱AI Embeddings API
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 内部逻辑：批量请求（智谱AI支持批量）
        embeddings = []
        for text in texts:
            response = requests.post(
                self.api_base,
                headers=headers,
                json={
                    "model": self.model,
                    "input": text
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()

            # 内部逻辑：提取向量数据
            if "data" in result and len(result["data"]) > 0:
                embeddings.append(result["data"][0]["embedding"])
            else:
                raise ValueError(f"智谱AI API 返回格式错误: {result}")

        return embeddings

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        函数级注释：LangChain Embeddings 接口实现 - 文档向量化
        参数：texts - 文本列表
        返回值：向量列表
        """
        try:
            return self._embed_documents(texts)
        except Exception as e:
            logger.error(f"智谱AI Embeddings API 调用失败: {str(e)}")
            raise

    def embed_query(self, text: str) -> List[float]:
        """
        函数级注释：LangChain Embeddings 接口实现 - 查询向量化
        参数：text - 查询文本
        返回值：向量
        """
        return self._embed_documents([text])[0]


class LocalAIEmbeddings(Embeddings):
    """
    类级注释：本地 AI Embeddings 包装类
    内部逻辑：封装 HuggingFaceEmbeddings，统一处理设备配置和 "auto" 转换
    设计原则：单一职责原则 - 专门处理本地模型设备配置
    职责：
        1. 处理 "auto" 设备类型，转换为实际可用设备（cuda/cpu/mps）
        2. 封装 HuggingFaceEmbeddings，提供统一的初始化接口
        3. 设置离线模式，避免从网络下载模型
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-large-zh-v1.5",
        device: str = "auto",
        model_kwargs: dict = None,
        encode_kwargs: dict = None
    ):
        """
        函数级注释：初始化本地 Embeddings
        内部逻辑：处理 "auto" 设备类型，转换为 cuda/cpu
        设计说明：使用环境变量 TRANSFORMERS_OFFLINE=1 控制离线模式，替代 local_files_only 参数
        参数：
            model_name: 模型名称
            device: 设备类型（支持 "auto", "cuda", "cpu", "mps"）
            model_kwargs: 额外模型参数
            encode_kwargs: 编码参数
        """
        from langchain_community.embeddings import HuggingFaceEmbeddings

        # 内部逻辑：解析实际设备类型
        actual_device = self._resolve_device(device)

        # 内部逻辑：合并 model_kwargs
        if model_kwargs is None:
            model_kwargs = {}
        model_kwargs['device'] = actual_device

        # 内部逻辑：设置离线模式，防止尝试从网上下载模型
        # 设计说明：使用环境变量替代 local_files_only 参数（新版本 HuggingFaceEmbeddings 已不支持该参数）
        import os
        os.environ['TRANSFORMERS_OFFLINE'] = '1'

        # 内部变量：创建底层 HuggingFaceEmbeddings 实例（移除 local_files_only 参数）
        self._embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs or {'normalize_embeddings': True}
        )

        logger.info(f"LocalAIEmbeddings 初始化完成: model={model_name}, device={actual_device}")

    @staticmethod
    def _resolve_device(device: str) -> str:
        """
        函数级注释：解析设备类型，将 "auto" 转换为实际设备
        内部逻辑：
            - "auto" 自动选择：优先 cuda > mps > cpu
            - 其他值直接返回
        参数：
            device: 设备字符串
        返回值：实际设备类型（cuda/mps/cpu）
        """
        # 内部逻辑：Guard Clauses - 非 auto 类型直接返回
        if device != "auto":
            return device

        try:
            import torch
            # 内部逻辑：优先使用 CUDA（NVIDIA GPU）
            if torch.cuda.is_available():
                return "cuda"
            # 内部逻辑：支持 Apple Silicon (MPS)
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            pass

        # 内部逻辑：默认使用 CPU
        return "cpu"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        函数级注释：LangChain Embeddings 接口实现 - 文档向量化
        参数：texts - 文本列表
        返回值：向量列表
        """
        return self._embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        """
        函数级注释：LangChain Embeddings 接口实现 - 查询向量化
        参数：text - 查询文本
        返回值：向量
        """
        return self._embeddings.embed_query(text)
