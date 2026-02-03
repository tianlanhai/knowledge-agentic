# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：Embedding工厂类（使用抽象工厂模式重构）
内部逻辑：统一管理不同提供商的Embedding实例，支持运行时热切换
设计模式：抽象工厂模式 + 桥接模式（桥接到 ai_provider 模块）
设计原则：SOLID - 依赖倒置原则、开闭原则、单一职责原则
参考项目：easy-dataset-file
重构说明：使用 ai_provider 模块统一管理 LLM 和 Embedding
"""

from typing import Dict, Any
from langchain_core.embeddings import Embeddings
from loguru import logger

from app.core.config import settings
from app.core.base_factory import BaseFactory
from app.core.ai_provider import (
    AIProviderType,
    AIProviderConfig,
    AIProviderFactoryRegistry,
    AIComponentType,
)


class EmbeddingFactory(BaseFactory[Embeddings]):
    """
    类级注释：Embedding工厂类，使用抽象工厂模式重构
    设计模式：抽象工厂模式 + 桥接模式（桥接到 ai_provider）
    职责：
        1. 根据提供商创建对应的Embedding实例
        2. 支持运行时配置切换（继承自 BaseFactory）
        3. 实例缓存优化性能（继承自 BaseFactory）

    重构优势：
        - 统一 LLM 和 Embedding 的创建接口
        - 使用注册表模式消除 if-else 分支
        - 与 ai_provider 模块共享提供商实现
    """

    # 内部常量：支持的Embedding提供商列表
    SUPPORTED_PROVIDERS = {
        "ollama": "Ollama本地模型",
        "zhipuai": "智谱AI",
        "openai": "OpenAI",
        "moonshot": "月之暗面",
        "deepseek": "DeepSeek",
        "local": "本地模型"
    }

    # 内部常量：提供商到枚举的映射
    _PROVIDER_ENUM_MAP = {
        "ollama": AIProviderType.OLLAMA,
        "zhipuai": AIProviderType.ZHIPUAI,
        "openai": AIProviderType.OPENAI,
        "moonshot": AIProviderType.MOONSHOT,
        "deepseek": AIProviderType.DEEPSEEK,
        "minimax": AIProviderType.MINIMAX,
    }

    # ========================================================================
    # 实现基类抽象方法
    # ========================================================================

    @classmethod
    def _get_default_config(cls) -> Dict[str, Any]:
        """
        函数级注释：获取默认配置（实现基类抽象方法）
        内部逻辑：从环境变量 settings 获取默认配置
        返回值：默认配置字典
        """
        return {
            "provider": settings.EMBEDDING_PROVIDER,
            "model": settings.EMBEDDING_MODEL,
            "endpoint": settings.OLLAMA_BASE_URL,
            "device": settings.DEVICE
        }

    @classmethod
    def _create_by_provider(cls, provider: str, config: Dict[str, Any], **kwargs) -> Embeddings:
        """
        函数级注释：根据提供商创建对应的Embedding实例（实现基类抽象方法）
        内部逻辑：使用 ai_provider 模块的注册表获取工厂，消除 if-else 分支
        设计模式：抽象工厂模式 + 注册表模式
        参数：
            provider: 提供商ID
            config: 配置字典
            **kwargs: 额外参数
        返回值：Embeddings实例
        """
        # 内部逻辑：特殊处理本地模型提供商
        if provider == "local":
            return cls._create_local_embedding(config)

        # 内部逻辑：将提供商字符串转换为枚举类型
        provider_enum = cls._get_provider_enum(provider)

        # 内部逻辑：构建 AIProviderConfig
        ai_config = AIProviderConfig(
            provider_type=provider_enum,
            api_key=config.get("api_key"),
            base_url=config.get("endpoint"),
            model=config.get("model"),
            **config.get("extra_params", {})
        )

        # 内部逻辑：从注册表获取工厂并创建实例（替代 if-else 分支）
        factory = AIProviderFactoryRegistry.get_factory(provider_enum)

        # 内部逻辑：检查工厂是否支持 Embedding
        if not factory.supports_component(AIComponentType.EMBEDDING):
            raise ValueError(
                f"提供商 {provider} 不支持 Embedding 组件"
            )

        embeddings = factory.create_embeddings(ai_config)
        return embeddings

    @classmethod
    def _get_provider_enum(cls, provider: str) -> AIProviderType:
        """
        函数级注释：将提供商字符串转换为枚举类型
        内部逻辑：使用映射表，避免 if-else 分支
        参数：
            provider: 提供商ID字符串
        返回值：AIProviderType 枚举
        """
        provider_lower = provider.lower()
        if provider_lower not in cls._PROVIDER_ENUM_MAP:
            supported_list = list(cls.SUPPORTED_PROVIDERS.keys())
            raise ValueError(
                f"不支持的Embedding提供商: {provider}。"
                f"支持的提供商: {supported_list}"
            )
        return cls._PROVIDER_ENUM_MAP[provider_lower]

    @classmethod
    def _create_local_embedding(cls, config: Dict[str, Any]) -> Embeddings:
        """
        函数级注释：创建本地Embedding实例
        内部逻辑：使用本地的transformers模型，处理设备自动检测
        设计原则：KISS 原则 - 在入口处统一处理设备类型转换
        参数：
            config: 配置字典
        返回值：Embeddings实例
        """
        # 内部逻辑：添加诊断日志 - 追踪 device 参数的传递过程
        logger.info(f"[诊断] _create_local_embedding 接收到的完整config: {config}")

        try:
            from app.utils.zhipuai_embeddings import LocalAIEmbeddings
        except ImportError:
            from langchain_community.embeddings import HuggingFaceEmbeddings as LocalAIEmbeddings

        # 内部变量：解析配置参数
        model_name = config.get("model", settings.EMBEDDING_MODEL)
        device_raw = config.get("device", settings.DEVICE)

        # 内部逻辑：在传递给 Embeddings 之前，先将 "auto" 转换为实际设备
        # 设计原则：防御性编程 - 在边界处处理数据转换
        device_resolved = cls._resolve_device_auto(device_raw)

        logger.info(f"[诊断] device解析: {repr(device_raw)} -> {repr(device_resolved)}")

        # 内部逻辑：构建模型参数（确保 device 不包含 "auto"）
        model_kwargs = {'device': device_resolved}
        encode_kwargs = {'normalize_embeddings': True}

        # 内部逻辑：设置离线模式环境变量，防止尝试从网上下载模型
        # 设计说明：使用环境变量替代 local_files_only 参数（新版本 HuggingFaceEmbeddings 已不支持该参数）
        import os
        os.environ['TRANSFORMERS_OFFLINE'] = '1'

        embeddings = LocalAIEmbeddings(
            model_name=model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs
        )

        logger.info(f"已创建本地Embedding实例，模型: {model_name}, 设备: {device_resolved}")
        return embeddings

    @staticmethod
    def _resolve_device_auto(device: str) -> str:
        """
        函数级注释：解析设备类型，将 "auto" 转换为实际可用设备
        内部逻辑：
            - "auto" 自动选择：优先 cuda > mps > cpu
            - 其他值直接返回
        设计原则：单一职责原则 - 仅处理设备类型转换
        说明：系统中 "auto" 表示自动选择设备（有 GPU 用 GPU，无 GPU 用 CPU）
        参数：
            device: 设备字符串（可能为 "auto"）
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

    # ========================================================================
    # 公共接口方法
    # ========================================================================

    @classmethod
    def create_embeddings(cls, config: Dict[str, Any] = None) -> Embeddings:
        """
        函数级注释：创建Embedding实例（支持热切换）
        内部逻辑：解析配置 -> 检查缓存 -> 创建/返回实例
        参数：
            config: 可选的配置字典，不传则使用运行时配置或环境变量
        返回值：Embeddings实例
        异常：ValueError - 当配置的提供商不支持时
        """
        # 内部逻辑：添加诊断日志 - 追踪方法调用
        logger.info(f"[诊断] >>> EmbeddingFactory.create_embeddings 被调用")

        # 内部逻辑：解析配置优先级：传入 > 运行时 > 默认
        embedding_config = cls._resolve_config(config)
        provider = embedding_config.get("provider", "ollama")

        # 内部逻辑：记录解析后的配置
        logger.info(f"[诊断] 解析后的embedding_config: {embedding_config}")
        logger.info(f"[诊断] provider: {provider}")

        # 内部逻辑：Guard Clauses - 验证提供商是否支持
        if not cls._is_supported_provider(provider):
            supported_list = list(cls.SUPPORTED_PROVIDERS.keys())
            raise ValueError(
                f"不支持的Embedding提供商: {provider}。"
                f"支持的提供商: {supported_list}"
            )

        # 内部逻辑：生成缓存键
        cache_key = cls._get_cache_key(embedding_config)
        logger.info(f"[诊断] cache_key: {cache_key}")

        # 内部逻辑：检查缓存
        if cache_key in cls._instance_cache:
            logger.debug(f"使用缓存的Embedding实例: {cache_key}")
            return cls._instance_cache[cache_key]

        # 内部逻辑：创建新实例前记录日志
        logger.info(f"[诊断] 准备创建新的 Embedding 实例，provider={provider}")

        # 内部逻辑：创建新实例
        embeddings = cls._create_by_provider(provider, embedding_config)
        cls._instance_cache[cache_key] = embeddings

        logger.info(f"已创建 {cls.SUPPORTED_PROVIDERS.get(provider, provider)} Embedding实例，模型: {embedding_config.get('model')}")
        return embeddings

    @classmethod
    def get_current_provider(cls) -> str:
        """
        函数级注释：获取当前配置的提供商
        返回值：提供商ID
        """
        config = cls._resolve_config()
        return config.get("provider", "ollama")

    @classmethod
    def get_current_model(cls) -> str:
        """
        函数级注释：获取当前配置的模型名称
        返回值：模型名称
        """
        config = cls._resolve_config()
        return config.get("model", settings.EMBEDDING_MODEL)

    @classmethod
    def validate_provider_config(cls, provider: str, config: Dict[str, Any]) -> bool:
        """
        函数级注释：验证提供商配置
        参数：
            provider: 提供商ID
            config: 配置字典
        返回值：配置是否有效
        """
        # 内部逻辑：检查提供商是否支持
        if not cls._is_supported_provider(provider):
            return False

        # 内部逻辑：本地模型需要特殊处理
        if provider == "local":
            try:
                import torch
                return True
            except ImportError:
                return False

        # 内部逻辑：云端提供商需要 API 密钥
        cloud_providers = ["zhipuai", "openai", "moonshot", "deepseek"]
        if provider in cloud_providers:
            return bool(config.get("api_key"))

        return True
