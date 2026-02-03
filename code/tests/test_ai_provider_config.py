# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：AI提供商配置模块单元测试
内部逻辑：测试AI提供商配置类的各种功能
测试策略：
   - 单元测试：测试配置类的各个方法
   - 验证测试：测试配置验证逻辑
"""

import pytest
from app.core.ai_provider.config import AIProviderConfig
from app.core.ai_provider.base import AIProviderType


class TestAIProviderType:
    """
    类级注释：提供商类型枚举测试
    """

    def test_openai_value(self):
        """验证 OPENAI 枚举值"""
        assert AIProviderType.OPENAI.value == "openai"

    def test_zhipuai_value(self):
        """验证 ZHIPUAI 枚举值"""
        assert AIProviderType.ZHIPUAI.value == "zhipuai"

    def test_ollama_value(self):
        """验证 OLLAMA 枚举值"""
        assert AIProviderType.OLLAMA.value == "ollama"


class TestAIProviderConfig:
    """
    类级注释：提供商配置类测试
    """

    def test_create_minimal_config(self):
        """
        函数级注释：测试创建最小配置
        内部逻辑：验证只提供必填字段时配置创建成功
        """
        # 内部变量：创建最小配置
        config = AIProviderConfig(
            provider_type=AIProviderType.OPENAI,
            api_key="sk-test"
        )

        assert config.provider_type == AIProviderType.OPENAI
        assert config.api_key == "sk-test"
        assert config.base_url is None
        assert config.model is None

    def test_create_full_config(self):
        """
        函数级注释：测试创建完整配置
        内部逻辑：验证所有字段正确赋值
        """
        # 内部变量：创建完整配置
        config = AIProviderConfig(
            provider_type=AIProviderType.OPENAI,
            api_key="sk-test",
            base_url="https://api.openai.com/v1",
            model="gpt-4",
            timeout=60,
            max_retries=3
        )

        assert config.provider_type == AIProviderType.OPENAI
        assert config.api_key == "sk-test"
        assert config.base_url == "https://api.openai.com/v1"
        assert config.model == "gpt-4"
        assert config.extra_params == {"timeout": 60, "max_retries": 3}

    def test_to_dict_with_all_fields(self):
        """
        函数级注释：测试转换为字典（包含所有字段）
        内部逻辑：验证字典包含所有配置
        """
        # 内部变量：创建配置
        config = AIProviderConfig(
            provider_type=AIProviderType.OPENAI,
            api_key="sk-test",
            base_url="https://api.example.com",
            model="gpt-4"
        )

        # 内部逻辑：转换为字典
        config_dict = config.to_dict()

        assert config_dict["provider"] == "openai"
        assert config_dict["api_key"] == "sk-test"
        assert config_dict["base_url"] == "https://api.example.com"
        assert config_dict["model"] == "gpt-4"

    def test_to_dict_with_optional_fields_none(self):
        """
        函数级注释：测试转换字典（可选字段为 None）
        内部逻辑：验证 None 值的字段不在字典中
        """
        # 内部变量：创建配置（可选字段为 None）
        config = AIProviderConfig(
            provider_type=AIProviderType.OLLAMA,
            api_key=None,
            base_url=None,
            model=None
        )

        # 内部逻辑：转换为字典
        config_dict = config.to_dict()

        # 验证：只有 provider 字段
        assert config_dict == {"provider": "ollama"}

    def test_from_dict_with_valid_provider(self):
        """
        函数级注释：测试从字典创建配置（有效提供商）
        内部逻辑：验证从字典正确创建配置
        """
        # 内部变量：配置字典
        config_dict = {
            "provider": "openai",
            "api_key": "sk-test",
            "base_url": "https://api.example.com",
            "model": "gpt-4"
        }

        # 内部逻辑：从字典创建
        config = AIProviderConfig.from_dict(config_dict)

        assert config.provider_type == AIProviderType.OPENAI
        assert config.api_key == "sk-test"
        assert config.base_url == "https://api.example.com"
        assert config.model == "gpt-4"

    def test_from_dict_with_invalid_provider(self):
        """
        函数级注释：测试从字典创建配置（无效提供商）
        内部逻辑：验证默认使用 OLLAMA
        """
        # 内部变量：配置字典（无效提供商）
        config_dict = {
            "provider": "invalid_provider",
            "api_key": "test-key"
        }

        # 内部逻辑：从字典创建
        config = AIProviderConfig.from_dict(config_dict)

        # 验证：默认使用 OLLAMA
        assert config.provider_type == AIProviderType.OLLAMA
        assert config.api_key == "test-key"

    def test_from_dict_without_provider(self):
        """
        函数级注释：测试从字典创建配置（无提供商字段）
        内部逻辑：验证默认使用 OLLAMA
        """
        # 内部变量：配置字典（无 provider）
        config_dict = {
            "api_key": "test-key"
        }

        # 内部逻辑：从字典创建
        config = AIProviderConfig.from_dict(config_dict)

        # 验证：默认使用 OLLAMA
        assert config.provider_type == AIProviderType.OLLAMA

    def test_from_dict_with_extra_params(self):
        """
        函数级注释：测试从字典创建配置（包含额外参数）
        内部逻辑：验证额外参数正确保存
        """
        # 内部变量：配置字典（包含额外参数）
        config_dict = {
            "provider": "openai",
            "api_key": "sk-test",
            "temperature": 0.7,
            "max_tokens": 2000
        }

        # 内部逻辑：从字典创建
        config = AIProviderConfig.from_dict(config_dict)

        # 验证：额外参数保存
        assert config.extra_params == {"temperature": 0.7, "max_tokens": 2000}

    def test_to_dict_includes_extra_params(self):
        """
        函数级注释：测试转换字典包含额外参数
        内部逻辑：验证额外参数包含在输出字典中
        """
        # 内部变量：创建配置（包含额外参数）
        config = AIProviderConfig(
            provider_type=AIProviderType.OPENAI,
            api_key="sk-test",
            temperature=0.7,
            max_tokens=2000
        )

        # 内部逻辑：转换为字典
        config_dict = config.to_dict()

        # 验证：额外参数包含在内
        assert config_dict["temperature"] == 0.7
        assert config_dict["max_tokens"] == 2000

    def test_round_trip_conversion(self):
        """
        函数级注释：测试往返转换
        内部逻辑：验证 to_dict 和 from_dict 一致性
        """
        # 内部变量：原始配置
        original = AIProviderConfig(
            provider_type=AIProviderType.ZHIPUAI,
            api_key="zhipu-key",
            base_url="https://api.zhipu.ai",
            model="chatglm-turbo",
            top_p=0.9
        )

        # 内部逻辑：往返转换
        config_dict = original.to_dict()
        restored = AIProviderConfig.from_dict(config_dict)

        # 验证：配置一致
        assert restored.provider_type == original.provider_type
        assert restored.api_key == original.api_key
        assert restored.base_url == original.base_url
        assert restored.model == original.model
        assert restored.extra_params == original.extra_params
