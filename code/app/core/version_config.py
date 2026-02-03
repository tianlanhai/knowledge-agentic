# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：镜像版本配置限制模块
内部逻辑：根据环境变量 IMAGE_VERSION 确定当前镜像支持的配置项，实现版本与配置的联动限制

设计原则：
- 第一性原理：镜像版本决定了系统能力，配置不能超出镜像能力范围
- 单一职责：只负责版本配置的验证和限制逻辑
- 开闭原则：新增版本时只需添加枚举和映射，无需修改验证逻辑
"""

from enum import Enum
from typing import List, Set, Tuple, Dict, Any


class ImageVersion(str, Enum):
    """
    类级注释：镜像版本枚举
    属性：
        V1: 云LLM + 本地向量版本
        V2: 云LLM + 云端向量版本
        V3: 本地LLM + 本地向量版本
        V4: 本地LLM + 云端向量版本
    """
    V1 = "v1"  # 云LLM + 本地向量
    V2 = "v2"  # 云LLM + 云端向量
    V3 = "v3"  # 本地LLM + 本地向量
    V4 = "v4"  # 本地LLM + 云端向量

    @classmethod
    def from_string(cls, value: str) -> "ImageVersion":
        """
        函数级注释：从字符串获取镜像版本枚举值
        参数：value - 版本字符串
        返回值：ImageVersion枚举值
        """
        try:
            return cls(value.lower())
        except ValueError:
            return cls.V1  # 默认返回v1版本


class VersionCapability:
    """
    类级注释：版本能力类，定义各镜像版本的能力和限制
    属性：
        version: 镜像版本
        description: 版本描述
        supported_llm_providers: 支持的LLM提供商列表
        supported_embedding_providers: 支持的Embedding提供商列表
        supports_local_embedding: 是否支持本地Embedding
    """

    def __init__(
        self,
        version: ImageVersion,
        description: str,
        supported_llm_providers: Set[str],
        supported_embedding_providers: Set[str],
        supports_local_embedding: bool,
    ):
        """
        函数级注释：初始化版本能力对象
        参数：
            version: 镜像版本
            description: 版本描述
            supported_llm_providers: 支持的LLM提供商集合
            supported_embedding_providers: 支持的Embedding提供商集合
            supports_local_embedding: 是否支持本地Embedding
        """
        self.version = version
        self.description = description
        self.supported_llm_providers = supported_llm_providers
        self.supported_embedding_providers = supported_embedding_providers
        self.supports_local_embedding = supports_local_embedding

    def to_dict(self) -> Dict[str, Any]:
        """
        函数级注释：将版本能力转换为字典格式
        返回值：包含版本信息的字典
        """
        return {
            "version": self.version.value,
            "description": self.description,
            "supported_llm_providers": sorted(self.supported_llm_providers),
            "supported_embedding_providers": sorted(self.supported_embedding_providers),
            "supports_local_embedding": self.supports_local_embedding,
        }


class VersionConfig:
    """
    类级注释：版本配置管理类，提供版本相关的验证和查询功能
    内部逻辑：使用类变量存储各版本的能力配置，提供静态方法进行验证和查询
    """

    # 各版本支持的LLM提供商（内部变量）
    VERSION_LLM_PROVIDERS: Dict[ImageVersion, Set[str]] = {
        ImageVersion.V1: {"zhipuai", "minimax", "moonshot", "openai"},  # 云LLM
        ImageVersion.V2: {"zhipuai", "minimax", "moonshot", "openai"},  # 云LLM
        ImageVersion.V3: {"ollama"},                                      # 本地LLM
        ImageVersion.V4: {"ollama"},                                      # 本地LLM
    }

    # 各版本支持的Embedding提供商（内部变量）
    VERSION_EMBEDDING_PROVIDERS: Dict[ImageVersion, Set[str]] = {
        ImageVersion.V1: {"local"},                                       # 本地向量
        ImageVersion.V2: {"zhipuai", "openai"},                          # 云端向量
        ImageVersion.V3: {"local"},                                       # 本地向量
        ImageVersion.V4: {"zhipuai", "openai"},                          # 云端向量
    }

    # 版本描述信息（内部变量）
    VERSION_DESCRIPTIONS: Dict[ImageVersion, str] = {
        ImageVersion.V1: "云LLM + 本地向量",
        ImageVersion.V2: "云LLM + 云端向量",
        ImageVersion.V3: "本地LLM + 本地向量",
        ImageVersion.V4: "本地LLM + 云端向量",
    }

    @classmethod
    def get_current_version(cls) -> ImageVersion:
        """
        函数级注释：获取当前镜像版本
        内部逻辑：从环境变量 IMAGE_VERSION 读取版本信息，不存在则默认为 v1
        返回值：ImageVersion枚举值
        """
        import os

        version_str = os.getenv("IMAGE_VERSION", "v1")
        return ImageVersion.from_string(version_str)

    @classmethod
    def get_version_capability(cls, version: ImageVersion = None) -> VersionCapability:
        """
        函数级注释：获取指定版本的能力信息
        参数：version - 镜像版本，为None时使用当前版本
        返回值：VersionCapability版本能力对象
        """
        if version is None:
            version = cls.get_current_version()

        return VersionCapability(
            version=version,
            description=cls.VERSION_DESCRIPTIONS[version],
            supported_llm_providers=cls.VERSION_LLM_PROVIDERS[version],
            supported_embedding_providers=cls.VERSION_EMBEDDING_PROVIDERS[version],
            supports_local_embedding="local" in cls.VERSION_EMBEDDING_PROVIDERS[version],
        )

    @classmethod
    def is_development_mode(cls) -> bool:
        """
        函数级注释：检测是否为开发模式
        内部逻辑：检查环境变量 DEVELOPMENT_MODE 或 ENVIRONMENT
        返回值：是否为开发模式
        """
        import os

        return (
            os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"
            or os.getenv("ENVIRONMENT", "prod").lower() == "development"
        )

    # ========================================================================
    # 模板方法模式辅助方法（消除重复代码）
    # ========================================================================

    @classmethod
    def _get_all_providers(cls, provider_dict: Dict[ImageVersion, Set[str]]) -> Set[str]:
        """
        函数级注释：获取所有提供商列表（辅助方法）
        内部逻辑：合并所有版本的提供商集合
        参数：
            provider_dict: 提供商字典
        返回值：排序后的提供商列表
        """
        all_providers = set()
        for providers in provider_dict.values():
            all_providers.update(providers)
        return all_providers

    @classmethod
    def _execute_with_development_fallback(
        cls,
        development_func,
        production_func,
        *args,
        **kwargs
    ):
        """
        函数级注释：根据开发模式执行不同逻辑（模板方法）
        内部逻辑：开发模式执行 development_func，生产模式执行 production_func
        参数：
            development_func: 开发模式下的函数
            production_func: 生产模式下的函数
            *args, **kwargs: 传递给函数的参数
        返回值：函数执行结果
        """
        if cls.is_development_mode():
            return development_func(*args, **kwargs)
        return production_func(*args, **kwargs)

    # ========================================================================
    # 提供商支持检查方法（使用模板方法）
    # ========================================================================

    @classmethod
    def is_llm_provider_supported(cls, provider: str) -> bool:
        """
        函数级注释：检查LLM提供商是否被当前镜像版本支持
        内部逻辑：开发模式下支持所有提供商，生产模式下检查版本限制（使用模板方法）
        参数：provider - LLM提供商名称
        返回值：是否支持
        """
        def dev_mode():
            all_providers = cls._get_all_providers(cls.VERSION_LLM_PROVIDERS)
            return provider.lower() in all_providers

        def prod_mode():
            version = cls.get_current_version()
            return provider.lower() in cls.VERSION_LLM_PROVIDERS.get(version, set())

        return cls._execute_with_development_fallback(dev_mode, prod_mode)

    @classmethod
    def is_embedding_provider_supported(cls, provider: str) -> bool:
        """
        函数级注释：检查Embedding提供商是否被当前镜像版本支持
        内部逻辑：开发模式下支持所有提供商，生产模式下检查版本限制（使用模板方法）
        参数：provider - Embedding提供商名称
        返回值：是否支持
        """
        def dev_mode():
            all_providers = cls._get_all_providers(cls.VERSION_EMBEDDING_PROVIDERS)
            return provider.lower() in all_providers

        def prod_mode():
            version = cls.get_current_version()
            return provider.lower() in cls.VERSION_EMBEDDING_PROVIDERS.get(version, set())

        return cls._execute_with_development_fallback(dev_mode, prod_mode)

    @classmethod
    def get_supported_llm_providers(cls) -> List[str]:
        """
        函数级注释：获取当前镜像版本支持的LLM提供商列表
        内部逻辑：开发模式下返回所有提供商，生产模式下返回当前版本支持的提供商（使用模板方法）
        返回值：LLM提供商名称列表
        """
        def dev_mode():
            all_providers = cls._get_all_providers(cls.VERSION_LLM_PROVIDERS)
            return sorted(all_providers)

        def prod_mode():
            version = cls.get_current_version()
            return list(cls.VERSION_LLM_PROVIDERS.get(version, set()))

        return cls._execute_with_development_fallback(dev_mode, prod_mode)

    @classmethod
    def get_supported_embedding_providers(cls) -> List[str]:
        """
        函数级注释：获取当前镜像版本支持的Embedding提供商列表
        内部逻辑：开发模式下返回所有提供商，生产模式下返回当前版本支持的提供商（使用模板方法）
        返回值：Embedding提供商名称列表
        """
        def dev_mode():
            all_providers = cls._get_all_providers(cls.VERSION_EMBEDDING_PROVIDERS)
            return sorted(all_providers)

        def prod_mode():
            version = cls.get_current_version()
            return list(cls.VERSION_EMBEDDING_PROVIDERS.get(version, set()))

        return cls._execute_with_development_fallback(dev_mode, prod_mode)

    @classmethod
    def validate_config(cls, llm_provider: str, embedding_provider: str) -> Tuple[bool, str]:
        """
        函数级注释：验证配置是否与当前镜像版本匹配
        内部逻辑：分别检查LLM和Embedding提供商是否在支持列表中，返回验证结果和错误信息
        参数：
            llm_provider: LLM提供商名称
            embedding_provider: Embedding提供商名称
        返回值：(是否有效, 错误信息)元组
        """
        # 检查LLM提供商
        if not cls.is_llm_provider_supported(llm_provider):
            supported = ", ".join(cls.get_supported_llm_providers())
            current_version = cls.get_current_version().value
            return False, (
                f"当前镜像版本({current_version})不支持 {llm_provider}，"
                f"支持的LLM提供商: {supported}"
            )

        # 检查Embedding提供商
        if not cls.is_embedding_provider_supported(embedding_provider):
            supported = ", ".join(cls.get_supported_embedding_providers())
            current_version = cls.get_current_version().value
            return False, (
                f"当前镜像版本({current_version})不支持 {embedding_provider}，"
                f"支持的Embedding提供商: {supported}"
            )

        return True, ""

    @classmethod
    def supports_local_embedding(cls) -> bool:
        """
        函数级注释：检查当前镜像版本是否支持本地Embedding
        返回值：是否支持本地Embedding
        """
        return "local" in cls.get_supported_embedding_providers()

    @classmethod
    def is_cloud_llm_version(cls) -> bool:
        """
        函数级注释：检查当前镜像版本是否为云LLM版本
        返回值：是否为云LLM版本
        """
        version = cls.get_current_version()
        return version in {ImageVersion.V1, ImageVersion.V2}

    @classmethod
    def is_local_llm_version(cls) -> bool:
        """
        函数级注释：检查当前镜像版本是否为本地LLM版本
        返回值：是否为本地LLM版本
        """
        version = cls.get_current_version()
        return version in {ImageVersion.V3, ImageVersion.V4}


# 变量：导出模块级别的版本配置实例
version_config = VersionConfig
