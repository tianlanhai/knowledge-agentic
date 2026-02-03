# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：Endpoint规范化工具类
内部逻辑：提供统一的endpoint规范化方法，消除重复代码
设计模式：工具类模式（静态方法）
设计原则：DRY（不重复）、单一职责原则
"""

from typing import Optional
from loguru import logger


class EndpointUtils:
    """
    类级注释：Endpoint规范化工具类
    职责：
        1. 统一处理不同提供商的endpoint规范化逻辑
        2. 消除在工厂类中重复的规范化代码
        3. 提供类型安全的规范化方法
    """

    @staticmethod
    def normalize_ollama_endpoint(endpoint: str) -> str:
        """
        函数级注释：规范化Ollama endpoint
        内部逻辑：移除末尾的 /api 或 /，确保正确拼接API路径
                 Ollama API 格式：http://host:port/api/tags，所以 base 应该是 http://host:port
        参数：
            endpoint: 原始endpoint地址
        返回值：规范化后的endpoint
        示例：
            "http://localhost:11434/api" -> "http://localhost:11434"
            "http://localhost:11434/" -> "http://localhost:11434"
        """
        return endpoint.rstrip('/').rstrip('/api')

    @staticmethod
    def normalize_zhipuai_endpoint(
        endpoint: str,
        suffix: str = "/chat/completions"
    ) -> str:
        """
        函数级注释：规范化智谱AI endpoint
        内部逻辑：确保endpoint以指定后缀结尾，自动补全路径
                 支持用户只配置 base URL（如 https://open.bigmodel.cn/api/coding/paas/v4）
                 或完整路径（如 https://open.bigmodel.cn/api/paas/v4/chat/completions）
        参数：
            endpoint: 原始endpoint地址
            suffix: 期望的后缀路径（默认/chat/completions，Embedding用/embeddings）
        返回值：规范化后的endpoint
        示例：
            "https://open.bigmodel.cn/api/paas/v4" -> "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        """
        if not endpoint.endswith(suffix):
            # 移除末尾的斜杠
            endpoint = endpoint.rstrip("/")
            # 添加指定后缀
            endpoint = f"{endpoint}{suffix}"
            logger.info(f"自动补全智谱AI端点路径: {endpoint}")
        return endpoint

    @staticmethod
    def ensure_trailing_slash(endpoint: str) -> str:
        """
        函数级注释：确保endpoint以斜杠结尾
        内部逻辑：如果endpoint不以/结尾，则添加/
        参数：
            endpoint: 原始endpoint地址
        返回值：确保以/结尾的endpoint
        """
        return endpoint if endpoint.endswith('/') else f"{endpoint}/"

    @staticmethod
    def remove_trailing_slash(endpoint: str) -> str:
        """
        函数级注释：移除endpoint末尾的斜杠
        内部逻辑：如果endpoint以/结尾，则移除
        参数：
            endpoint: 原始endpoint地址
        返回值：移除末尾斜杠的endpoint
        """
        return endpoint.rstrip('/')

    @staticmethod
    def validate_endpoint(endpoint: Optional[str], provider_name: str = "") -> str:
        """
        函数级注释：验证并返回endpoint
        内部逻辑：Guard Clauses - 验证endpoint非空
        参数：
            endpoint: 待验证的endpoint
            provider_name: 提供商名称（用于错误消息）
        返回值：验证后的endpoint
        异常：ValueError - 当endpoint为空时
        """
        if not endpoint:
            raise ValueError(
                f"{provider_name}需要配置端点地址" if provider_name else "端点地址不能为空"
            )
        return endpoint
