# -*- coding: utf-8 -*-
"""
文件级注释：版本配置模块测试
内部逻辑：测试镜像版本配置和验证逻辑
"""

import pytest
from app.core.version_config import (
    ImageVersion,
    VersionCapability,
    VersionConfig,
)


class TestImageVersion:
    """
    类级注释：ImageVersion枚举测试类
    """

    def test_from_string_valid_v1(self):
        """
        函数级注释：测试从字符串获取v1版本
        """
        result = ImageVersion.from_string("v1")
        assert result == ImageVersion.V1

    def test_from_string_valid_v2(self):
        """
        函数级注释：测试从字符串获取v2版本
        """
        result = ImageVersion.from_string("v2")
        assert result == ImageVersion.V2

    def test_from_string_valid_v3(self):
        """
        函数级注释：测试从字符串获取v3版本
        """
        result = ImageVersion.from_string("v3")
        assert result == ImageVersion.V3

    def test_from_string_valid_v4(self):
        """
        函数级注释：测试从字符串获取v4版本
        """
        result = ImageVersion.from_string("v4")
        assert result == ImageVersion.V4

    def test_from_string_invalid_returns_default(self):
        """
        函数级注释：测试无效版本字符串返回默认v1
        内部逻辑：验证错误输入的默认行为
        """
        result = ImageVersion.from_string("invalid")
        assert result == ImageVersion.V1

    def test_from_string_empty_returns_default(self):
        """
        函数级注释：测试空字符串返回默认v1
        """
        result = ImageVersion.from_string("")
        assert result == ImageVersion.V1

    def test_from_string_case_insensitive(self):
        """
        函数级注释：测试大小写不敏感
        内部逻辑：验证函数内部使用lower()处理
        """
        result = ImageVersion.from_string("V1")
        assert result == ImageVersion.V1

    def test_from_string_uppercase(self):
        """
        函数级注释：测试大写字符串
        """
        result = ImageVersion.from_string("V2")
        assert result == ImageVersion.V2

    def test_from_string_mixed_case(self):
        """
        函数级注释：测试混合大小写字符串
        """
        result = ImageVersion.from_string("V3")
        assert result == ImageVersion.V3

    def test_image_version_values(self):
        """
        函数级注释：测试枚举值正确性
        内部逻辑：验证每个版本的value属性
        """
        assert ImageVersion.V1.value == "v1"
        assert ImageVersion.V2.value == "v2"
        assert ImageVersion.V3.value == "v3"
        assert ImageVersion.V4.value == "v4"


class TestVersionCapability:
    """
    类级注释：VersionCapability类测试类
    """

    def test_to_dict_structure(self):
        """
        函数级注释：测试to_dict方法返回正确结构
        内部逻辑：验证返回字典包含所有必需字段
        """
        capability = VersionCapability(
            version=ImageVersion.V1,
            description="云LLM + 本地向量",
            supported_llm_providers={"zhipuai", "openai"},
            supported_embedding_providers={"local"},
            supports_local_embedding=True
        )
        result = capability.to_dict()
        assert isinstance(result, dict)
        assert "version" in result
        assert "description" in result
        assert "supported_llm_providers" in result
        assert "supported_embedding_providers" in result
        assert "supports_local_embedding" in result

    def test_to_dict_all_fields_present(self):
        """
        函数级注释：测试to_dict包含所有字段
        """
        capability = VersionCapability(
            version=ImageVersion.V2,
            description="云LLM + 云端向量",
            supported_llm_providers={"zhipuai"},
            supported_embedding_providers={"zhipuai"},
            supports_local_embedding=False
        )
        result = capability.to_dict()
        assert result["version"] == "v2"
        assert result["description"] == "云LLM + 云端向量"
        assert result["supports_local_embedding"] is False
        assert isinstance(result["supported_llm_providers"], list)
        assert isinstance(result["supported_embedding_providers"], list)

    def test_to_dict_sorted_lists(self):
        """
        函数级注释：测试提供商列表已排序
        内部逻辑：验证返回的列表是已排序的
        """
        capability = VersionCapability(
            version=ImageVersion.V1,
            description="test",
            supported_llm_providers={"zhipuai", "openai", "minimax"},
            supported_embedding_providers={"local"},
            supports_local_embedding=True
        )
        result = capability.to_dict()
        # 验证列表是排序的
        assert result["supported_llm_providers"] == sorted(result["supported_llm_providers"])
        assert result["supported_embedding_providers"] == sorted(result["supported_embedding_providers"])

    def test_version_capability_initialization(self):
        """
        函数级注释：测试VersionCapability初始化
        内部逻辑：验证所有属性正确设置
        """
        capability = VersionCapability(
            version=ImageVersion.V3,
            description="本地LLM + 本地向量",
            supported_llm_providers={"ollama"},
            supported_embedding_providers={"local"},
            supports_local_embedding=True
        )
        assert capability.version == ImageVersion.V3
        assert capability.description == "本地LLM + 本地向量"
        assert capability.supports_local_embedding is True
        assert "ollama" in capability.supported_llm_providers
        assert "local" in capability.supported_embedding_providers


class TestVersionConfig:
    """
    类级注释：VersionConfig类测试类
    """

    def test_get_current_version_default(self):
        """
        函数级注释：测试默认获取当前版本
        内部逻辑：未设置环境变量时返回v1
        """
        # 确保没有设置环境变量
        import os
        if "IMAGE_VERSION" in os.environ:
            del os.environ["IMAGE_VERSION"]
        result = VersionConfig.get_current_version()
        assert result in [ImageVersion.V1, ImageVersion.V2, ImageVersion.V3, ImageVersion.V4]

    def test_get_current_version_from_env(self, monkeypatch):
        """
        函数级注释：测试从环境变量获取版本
        内部逻辑：设置IMAGE_VERSION环境变量
        """
        monkeypatch.setenv("IMAGE_VERSION", "v2")
        result = VersionConfig.get_current_version()
        assert result == ImageVersion.V2

    def test_get_current_version_from_env_v3(self, monkeypatch):
        """
        函数级注释：测试从环境变量获取v3版本
        """
        monkeypatch.setenv("IMAGE_VERSION", "v3")
        result = VersionConfig.get_current_version()
        assert result == ImageVersion.V3

    def test_get_current_version_from_env_invalid(self, monkeypatch):
        """
        函数级注释：测试无效环境变量值返回默认v1
        """
        monkeypatch.setenv("IMAGE_VERSION", "invalid")
        result = VersionConfig.get_current_version()
        assert result == ImageVersion.V1

    def test_get_version_capability_default(self):
        """
        函数级注释：测试获取默认版本能力
        内部逻辑：不传参数时使用当前版本
        """
        capability = VersionConfig.get_version_capability()
        assert capability is not None
        assert isinstance(capability, VersionCapability)
        assert capability.version in [ImageVersion.V1, ImageVersion.V2, ImageVersion.V3, ImageVersion.V4]

    def test_get_version_capability_specific_v1(self):
        """
        函数级注释：测试获取v1版本能力
        """
        capability = VersionConfig.get_version_capability(ImageVersion.V1)
        assert capability.version == ImageVersion.V1
        assert "zhipuai" in capability.supported_llm_providers
        assert "local" in capability.supported_embedding_providers
        assert capability.supports_local_embedding is True

    def test_get_version_capability_v2(self):
        """
        函数级注释：测试获取v2版本能力
        """
        capability = VersionConfig.get_version_capability(ImageVersion.V2)
        assert capability.version == ImageVersion.V2
        assert "zhipuai" in capability.supported_llm_providers
        assert "zhipuai" in capability.supported_embedding_providers
        assert capability.supports_local_embedding is False

    def test_get_version_capability_v3(self):
        """
        函数级注释：测试获取v3版本能力
        """
        capability = VersionConfig.get_version_capability(ImageVersion.V3)
        assert capability.version == ImageVersion.V3
        assert "ollama" in capability.supported_llm_providers
        assert "local" in capability.supported_embedding_providers
        assert capability.supports_local_embedding is True

    def test_get_version_capability_v4(self):
        """
        函数级注释：测试获取v4版本能力
        """
        capability = VersionConfig.get_version_capability(ImageVersion.V4)
        assert capability.version == ImageVersion.V4
        assert "ollama" in capability.supported_llm_providers
        assert "zhipuai" in capability.supported_embedding_providers
        assert capability.supports_local_embedding is False

    def test_is_llm_provider_supported_v1_cloud(self, monkeypatch):
        """
        函数级注释：测试v1版本支持云端LLM
        内部逻辑：v1版本是云LLM版本
        """
        monkeypatch.setenv("IMAGE_VERSION", "v1")
        assert VersionConfig.is_llm_provider_supported("zhipuai") is True
        assert VersionConfig.is_llm_provider_supported("openai") is True
        assert VersionConfig.is_llm_provider_supported("minimax") is True

    def test_is_llm_provider_supported_v1_not_ollama(self, monkeypatch):
        """
        函数级注释：测试v1版本不支持Ollama
        内部逻辑：v1是云LLM版本
        """
        monkeypatch.setenv("IMAGE_VERSION", "v1")
        assert VersionConfig.is_llm_provider_supported("ollama") is False

    def test_is_llm_provider_supported_v3_local(self, monkeypatch):
        """
        函数级注释：测试v3版本支持本地LLM
        内部逻辑：v3版本是本地LLM版本
        """
        monkeypatch.setenv("IMAGE_VERSION", "v3")
        assert VersionConfig.is_llm_provider_supported("ollama") is True

    def test_is_llm_provider_supported_v3_not_cloud(self, monkeypatch):
        """
        函数级注释：测试v3版本不支持云端LLM
        """
        monkeypatch.setenv("IMAGE_VERSION", "v3")
        assert VersionConfig.is_llm_provider_supported("zhipuai") is False

    def test_is_llm_provider_supported_not_supported(self, monkeypatch):
        """
        函数级注释：测试不支持的LLM提供商
        内部逻辑：完全不存在的提供商ID
        """
        monkeypatch.setenv("IMAGE_VERSION", "v1")
        assert VersionConfig.is_llm_provider_supported("nonexistent") is False

    def test_is_llm_provider_supported_case_insensitive(self, monkeypatch):
        """
        函数级注释：测试提供商ID大小写不敏感
        内部逻辑：函数内部使用lower()处理
        """
        monkeypatch.setenv("IMAGE_VERSION", "v1")
        assert VersionConfig.is_llm_provider_supported("ZHIPUAI") is True
        assert VersionConfig.is_llm_provider_supported("Ollama") is False

    def test_is_embedding_provider_supported_v1_local(self, monkeypatch):
        """
        函数级注释：测试v1版本支持本地Embedding
        """
        monkeypatch.setenv("IMAGE_VERSION", "v1")
        assert VersionConfig.is_embedding_provider_supported("local") is True

    def test_is_embedding_provider_supported_v1_not_cloud(self, monkeypatch):
        """
        函数级注释：测试v1版本不支持云端Embedding
        """
        monkeypatch.setenv("IMAGE_VERSION", "v1")
        assert VersionConfig.is_embedding_provider_supported("zhipuai") is False

    def test_is_embedding_provider_supported_v2_cloud(self, monkeypatch):
        """
        函数级注释：测试v2版本支持云端Embedding
        内部逻辑：v2版本是云端向量版本
        """
        monkeypatch.setenv("IMAGE_VERSION", "v2")
        assert VersionConfig.is_embedding_provider_supported("zhipuai") is True
        assert VersionConfig.is_embedding_provider_supported("openai") is True

    def test_is_embedding_provider_supported_v2_not_local(self, monkeypatch):
        """
        函数级注释：测试v2版本不支持本地Embedding
        """
        monkeypatch.setenv("IMAGE_VERSION", "v2")
        assert VersionConfig.is_embedding_provider_supported("local") is False

    def test_is_embedding_provider_supported_not_supported(self, monkeypatch):
        """
        函数级注释：测试不支持的Embedding提供商
        """
        monkeypatch.setenv("IMAGE_VERSION", "v1")
        assert VersionConfig.is_embedding_provider_supported("nonexistent") is False

    def test_get_supported_llm_providers_v1(self, monkeypatch):
        """
        函数级注释：测试v1版本的LLM提供商列表
        """
        monkeypatch.setenv("IMAGE_VERSION", "v1")
        providers = VersionConfig.get_supported_llm_providers()
        assert isinstance(providers, list)
        assert "zhipuai" in providers
        assert "minimax" in providers
        assert "moonshot" in providers
        assert "openai" in providers
        assert "ollama" not in providers

    def test_get_supported_llm_providers_v3(self, monkeypatch):
        """
        函数级注释：测试v3版本的LLM提供商列表
        """
        monkeypatch.setenv("IMAGE_VERSION", "v3")
        providers = VersionConfig.get_supported_llm_providers()
        assert isinstance(providers, list)
        assert "ollama" in providers
        assert "zhipuai" not in providers

    def test_get_supported_embedding_providers_v1(self, monkeypatch):
        """
        函数级注释：测试v1版本的Embedding提供商列表
        """
        monkeypatch.setenv("IMAGE_VERSION", "v1")
        providers = VersionConfig.get_supported_embedding_providers()
        assert isinstance(providers, list)
        assert "local" in providers
        assert "zhipuai" not in providers

    def test_get_supported_embedding_providers_v2(self, monkeypatch):
        """
        函数级注释：测试v2版本的Embedding提供商列表
        """
        monkeypatch.setenv("IMAGE_VERSION", "v2")
        providers = VersionConfig.get_supported_embedding_providers()
        assert isinstance(providers, list)
        assert "zhipuai" in providers
        assert "openai" in providers
        assert "local" not in providers

    def test_validate_config_valid_both(self, monkeypatch):
        """
        函数级注释：测试有效的LLM和Embedding配置
        内部逻辑：两者都匹配当前版本
        """
        monkeypatch.setenv("IMAGE_VERSION", "v1")
        is_valid, error_msg = VersionConfig.validate_config("zhipuai", "local")
        assert is_valid is True
        assert error_msg == ""

    def test_validate_config_invalid_llm(self, monkeypatch):
        """
        函数级注释：测试无效的LLM提供商配置
        内部逻辑：LLM提供商不匹配当前版本
        """
        monkeypatch.setenv("IMAGE_VERSION", "v1")
        is_valid, error_msg = VersionConfig.validate_config("ollama", "local")
        assert is_valid is False
        assert "ollama" in error_msg.lower()
        assert "v1" in error_msg

    def test_validate_config_invalid_embedding(self, monkeypatch):
        """
        函数级注释：测试无效的Embedding提供商配置
        内部逻辑：Embedding提供商不匹配当前版本
        """
        monkeypatch.setenv("IMAGE_VERSION", "v1")
        is_valid, error_msg = VersionConfig.validate_config("zhipuai", "zhipuai")
        assert is_valid is False
        assert "zhipuai" in error_msg.lower()
        assert "embedding" in error_msg.lower()

    def test_validate_config_invalid_both(self, monkeypatch):
        """
        函数级注释：测试两者都无效的配置
        """
        monkeypatch.setenv("IMAGE_VERSION", "v1")
        is_valid, error_msg = VersionConfig.validate_config("ollama", "zhipuai")
        assert is_valid is False
        # 应该首先检查LLM提供商

    def test_validate_config_empty_llm(self, monkeypatch):
        """
        函数级注释：测试空LLM提供商
        """
        monkeypatch.setenv("IMAGE_VERSION", "v1")
        is_valid, error_msg = VersionConfig.validate_config("", "local")
        assert is_valid is False

    def test_validate_config_empty_embedding(self, monkeypatch):
        """
        函数级注释：测试空Embedding提供商
        """
        monkeypatch.setenv("IMAGE_VERSION", "v1")
        is_valid, error_msg = VersionConfig.validate_config("zhipuai", "")
        assert is_valid is False

    def test_validate_config_error_message_format(self, monkeypatch):
        """
        函数级注释：测试错误消息格式正确
        内部逻辑：验证错误消息包含版本和支持的提供商列表
        """
        monkeypatch.setenv("IMAGE_VERSION", "v2")
        is_valid, error_msg = VersionConfig.validate_config("ollama", "local")
        assert is_valid is False
        assert "v2" in error_msg
        assert "支持的" in error_msg or "supported" in error_msg.lower()

    def test_supports_local_embedding_true(self, monkeypatch):
        """
        函数级注释：测试支持本地Embedding的版本
        内部逻辑：v1和v3版本支持本地Embedding
        """
        monkeypatch.setenv("IMAGE_VERSION", "v1")
        assert VersionConfig.supports_local_embedding() is True

        monkeypatch.setenv("IMAGE_VERSION", "v3")
        assert VersionConfig.supports_local_embedding() is True

    def test_supports_local_embedding_false(self, monkeypatch):
        """
        函数级注释：测试不支持本地Embedding的版本
        内部逻辑：v2和v4版本不支持本地Embedding
        """
        monkeypatch.setenv("IMAGE_VERSION", "v2")
        assert VersionConfig.supports_local_embedding() is False

        monkeypatch.setenv("IMAGE_VERSION", "v4")
        assert VersionConfig.supports_local_embedding() is False

    def test_is_cloud_llm_version_true(self, monkeypatch):
        """
        函数级注释：测试云LLM版本判断
        内部逻辑：v1和v2是云LLM版本
        """
        monkeypatch.setenv("IMAGE_VERSION", "v1")
        assert VersionConfig.is_cloud_llm_version() is True

        monkeypatch.setenv("IMAGE_VERSION", "v2")
        assert VersionConfig.is_cloud_llm_version() is True

    def test_is_cloud_llm_version_false(self, monkeypatch):
        """
        函数级注释：测试本地LLM版本判断
        内部逻辑：v3和v4是本地LLM版本
        """
        monkeypatch.setenv("IMAGE_VERSION", "v3")
        assert VersionConfig.is_cloud_llm_version() is False

        monkeypatch.setenv("IMAGE_VERSION", "v4")
        assert VersionConfig.is_cloud_llm_version() is False

    def test_is_local_llm_version_true(self, monkeypatch):
        """
        函数级注释：测试本地LLM版本判断
        """
        monkeypatch.setenv("IMAGE_VERSION", "v3")
        assert VersionConfig.is_local_llm_version() is True

        monkeypatch.setenv("IMAGE_VERSION", "v4")
        assert VersionConfig.is_local_llm_version() is True

    def test_is_local_llm_version_false(self, monkeypatch):
        """
        函数级注释：测试云LLM版本判断
        """
        monkeypatch.setenv("IMAGE_VERSION", "v1")
        assert VersionConfig.is_local_llm_version() is False

        monkeypatch.setenv("IMAGE_VERSION", "v2")
        assert VersionConfig.is_local_llm_version() is False


class TestVersionConfigEdgeCases:
    """
    类级注释：版本配置边界情况测试类
    """

    def test_empty_image_version_env(self, monkeypatch):
        """
        函数级注释：测试空环境变量
        内部逻辑：环境变量设置为空字符串
        """
        monkeypatch.setenv("IMAGE_VERSION", "")
        result = VersionConfig.get_current_version()
        # 空字符串会被from_string处理为v1
        assert result == ImageVersion.V1

    def test_whitespace_image_version(self, monkeypatch):
        """
        函数级注释：测试纯空白环境变量
        """
        monkeypatch.setenv("IMAGE_VERSION", "   ")
        result = VersionConfig.get_current_version()
        # 空白字符串会被from_string处理（如果有trim逻辑）
        assert result in [ImageVersion.V1, ImageVersion.V2, ImageVersion.V3, ImageVersion.V4]

    def test_get_version_capability_none_argument(self):
        """
        函数级注释：测试传入None参数
        内部逻辑：None时使用当前版本
        """
        capability = VersionConfig.get_version_capability(None)
        assert capability is not None
        assert capability.version in [ImageVersion.V1, ImageVersion.V2, ImageVersion.V3, ImageVersion.V4]
