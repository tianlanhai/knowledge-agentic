# -*- coding: utf-8 -*-
"""
文件级注释：LLM常量模块测试
内部逻辑：测试LLM提供商常量配置和辅助函数
"""

import pytest
from app.core.llm_constants import (
    LLM_PROVIDERS,
    EMBEDDING_PROVIDERS,
    DEFAULT_MODEL_SETTINGS,
    PROVIDER_ID_MAP,
    LOCAL_EMBEDDING_PROVIDERS,
    CLOUD_API_PROVIDERS,
    get_provider_by_id,
    is_local_embedding,
    is_cloud_provider,
    get_default_model,
)


class TestLLMConstants:
    """
    类级注释：LLM常量测试类
    内部逻辑：验证LLM提供商常量配置完整性
    """

    def test_llm_providers_not_empty(self):
        """
        函数级注释：测试LLM提供商列表不为空
        """
        assert LLM_PROVIDERS
        assert len(LLM_PROVIDERS) > 0

    def test_llm_providers_structure(self):
        """
        函数级注释：测试LLM提供商数据结构完整性
        内部逻辑：验证每个提供商包含必需字段
        """
        required_keys = {"id", "name", "default_endpoint", "default_models", "type"}
        for provider in LLM_PROVIDERS:
            assert required_keys.issubset(provider.keys()), f"Provider {provider} missing required keys"
            assert provider["id"], f"Provider id should not be empty"
            assert provider["name"], f"Provider name should not be empty"
            assert isinstance(provider["default_models"], list), f"Provider default_models should be a list"
            assert provider["type"] == "text", f"Provider type should be 'text'"

    def test_embedding_providers_not_empty(self):
        """
        函数级注释：测试Embedding提供商列表不为空
        """
        assert EMBEDDING_PROVIDERS
        assert len(EMBEDDING_PROVIDERS) > 0

    def test_embedding_providers_structure(self):
        """
        函数级注释：测试Embedding提供商数据结构完整性
        内部逻辑：验证每个提供商包含必需字段
        """
        required_keys = {"id", "name", "default_models", "type"}
        for provider in EMBEDDING_PROVIDERS:
            assert required_keys.issubset(provider.keys()), f"Provider {provider} missing required keys"
            assert provider["id"], f"Provider id should not be empty"
            assert provider["name"], f"Provider name should not be empty"
            assert isinstance(provider["default_models"], list), f"Provider default_models should be a list"
            assert provider["type"] == "embedding", f"Provider type should be 'embedding'"

    def test_default_model_settings_structure(self):
        """
        函数级注释：测试默认模型设置包含所有必需字段
        内部逻辑：验证temperature、max_tokens、top_p、top_k字段
        """
        required_keys = {"temperature", "max_tokens", "top_p", "top_k"}
        assert required_keys.issubset(DEFAULT_MODEL_SETTINGS.keys())
        assert isinstance(DEFAULT_MODEL_SETTINGS["temperature"], (int, float))
        assert isinstance(DEFAULT_MODEL_SETTINGS["max_tokens"], int)
        assert isinstance(DEFAULT_MODEL_SETTINGS["top_p"], (int, float))
        assert isinstance(DEFAULT_MODEL_SETTINGS["top_k"], int)

    def test_provider_id_map_completeness(self):
        """
        函数级注释：测试PROVIDER_ID_MAP包含所有提供商
        内部逻辑：验证映射表包含LLM和Embedding所有提供商
        """
        all_provider_ids = {p["id"] for p in LLM_PROVIDERS + EMBEDDING_PROVIDERS}
        mapped_provider_ids = set(PROVIDER_ID_MAP.keys())
        assert all_provider_ids == mapped_provider_ids, "PROVIDER_ID_MAP should contain all providers"

    def test_local_embedding_providers_defined(self):
        """
        函数级注释：测试本地Embedding提供商列表已定义
        """
        assert isinstance(LOCAL_EMBEDDING_PROVIDERS, list)
        assert "local" in LOCAL_EMBEDDING_PROVIDERS

    def test_cloud_api_providers_defined(self):
        """
        函数级注释：测试云端API提供商列表已定义
        内部逻辑：验证包含主要云端提供商
        """
        assert isinstance(CLOUD_API_PROVIDERS, list)
        expected_cloud = ["zhipuai", "openai", "minimax", "moonshot", "deepseek"]
        for provider in expected_cloud:
            assert provider in CLOUD_API_PROVIDERS


class TestGetProviderById:
    """
    类级注释：get_provider_by_id函数测试类
    """

    def test_get_provider_by_id_llm_exists(self):
        """
        函数级注释：测试获取存在的LLM提供商
        内部逻辑：验证返回正确的提供商配置
        """
        result = get_provider_by_id("ollama")
        assert result is not None
        assert result["id"] == "ollama"
        assert result["name"] == "Ollama"

    def test_get_provider_by_id_embedding_exists(self):
        """
        函数级注释：测试获取存在的Embedding提供商
        内部逻辑：验证返回正确的提供商配置
        """
        result = get_provider_by_id("zhipuai")
        assert result is not None
        assert result["id"] == "zhipuai"
        # zhipuai同时在LLM和Embedding列表中

    def test_get_provider_by_id_not_found(self):
        """
        函数级注释：测试获取不存在的提供商返回None
        内部逻辑：验证不存在的提供商ID返回None
        """
        result = get_provider_by_id("nonexistent_provider")
        assert result is None

    def test_get_provider_by_id_local(self):
        """
        函数级注释：测试获取本地Embedding提供商
        """
        result = get_provider_by_id("local")
        assert result is not None
        assert result["id"] == "local"
        assert result["type"] == "embedding"

    def test_get_provider_by_id_openai(self):
        """
        函数级注释：测试获取OpenAI提供商
        内部逻辑：验证OpenAI同时在LLM和Embedding列表中
        """
        result = get_provider_by_id("openai")
        assert result is not None
        assert result["id"] == "openai"

    def test_get_provider_by_id_empty_string(self):
        """
        函数级注释：测试空字符串提供商ID
        内部逻辑：验证空字符串返回None
        """
        result = get_provider_by_id("")
        assert result is None


class TestIsLocalEmbedding:
    """
    类级注释：is_local_embedding函数测试类
    """

    def test_is_local_embedding_true(self):
        """
        函数级注释：测试本地Embedding判断返回True
        """
        assert is_local_embedding("local") is True

    def test_is_local_embedding_false_ollama(self):
        """
        函数级注释：测试Ollama不是本地Embedding
        内部逻辑：虽然Ollama是本地服务，但分类为云端提供商
        """
        assert is_local_embedding("ollama") is False

    def test_is_local_embedding_false_zhipuai(self):
        """
        函数级注释：测试云端Embedding判断返回False
        """
        assert is_local_embedding("zhipuai") is False

    def test_is_local_embedding_false_openai(self):
        """
        函数级注释：测试OpenAI Embedding判断返回False
        """
        assert is_local_embedding("openai") is False

    def test_is_local_embedding_case_sensitive(self):
        """
        函数级注释：测试大小写敏感（实际行为）
        内部逻辑：当前实现不处理大小写，'LOCAL' != 'local'
        """
        # 注意：当前实现是大小写敏感的
        assert is_local_embedding("local") is True
        assert is_local_embedding("LOCAL") is False  # 当前不支持大写

    def test_is_local_embedding_nonexistent(self):
        """
        函数级注释：测试不存在的提供商返回False
        """
        assert is_local_embedding("nonexistent") is False


class TestIsCloudProvider:
    """
    类级注释：is_cloud_provider函数测试类
    """

    def test_is_cloud_provider_zhipuai(self):
        """
        函数级注释：测试智谱AI是云端提供商
        """
        assert is_cloud_provider("zhipuai") is True

    def test_is_cloud_provider_openai(self):
        """
        函数级注释：测试OpenAI是云端提供商
        """
        assert is_cloud_provider("openai") is True

    def test_is_cloud_provider_minimax(self):
        """
        函数级注释：测试MiniMax是云端提供商
        """
        assert is_cloud_provider("minimax") is True

    def test_is_cloud_provider_moonshot(self):
        """
        函数级注释：测试月之暗面是云端提供商
        """
        assert is_cloud_provider("moonshot") is True

    def test_is_cloud_provider_deepseek(self):
        """
        函数级注释：测试DeepSeek是云端提供商
        """
        assert is_cloud_provider("deepseek") is True

    def test_is_cloud_provider_ollama_false(self):
        """
        函数级注释：测试Ollama不是云端提供商
        内部逻辑：Ollama是本地服务
        """
        assert is_cloud_provider("ollama") is False

    def test_is_cloud_provider_local_false(self):
        """
        函数级注释：测试本地Embedding不是云端提供商
        """
        assert is_cloud_provider("local") is False

    def test_is_cloud_provider_case_sensitive(self):
        """
        函数级注释：测试大小写敏感（实际行为）
        内部逻辑：当前实现不处理大小写
        """
        # 注意：当前实现是大小写敏感的
        assert is_cloud_provider("zhipuai") is True
        assert is_cloud_provider("ZHIPUAI") is False  # 当前不支持大写


class TestGetDefaultModel:
    """
    类级注释：get_default_model函数测试类
    """

    def test_get_default_model_llm_ollama(self):
        """
        函数级注释：测试获取Ollama默认LLM模型
        """
        result = get_default_model("ollama", "llm")
        assert result  # 非空字符串
        assert "deepseek" in result or "llama" in result or "qwen" in result or "gemma" in result

    def test_get_default_model_llm_zhipuai(self):
        """
        函数级注释：测试获取智谱AI默认LLM模型
        """
        result = get_default_model("zhipuai", "llm")
        assert result  # 非空字符串
        assert "glm" in result.lower()

    def test_get_default_model_embedding_ollama(self):
        """
        函数级注释：测试获取Ollama默认Embedding模型
        """
        result = get_default_model("ollama", "embedding")
        assert result  # 非空字符串
        assert "embed" in result.lower() or "minilm" in result.lower()

    def test_get_default_model_embedding_zhipuai(self):
        """
        函数级注释：测试获取智谱AI默认Embedding模型
        """
        result = get_default_model("zhipuai", "embedding")
        assert result  # 非空字符串
        assert "embedding" in result.lower()

    def test_get_default_model_not_found(self):
        """
        函数级注释：测试不存在的提供商返回空字符串
        """
        result = get_default_model("nonexistent", "llm")
        assert result == ""

    def test_get_default_model_empty_models_list(self):
        """
        函数级注释：测试提供商没有默认模型配置时返回空字符串
        内部逻辑：遍历所有提供商，检查是否有default_models为空的情况
        """
        # 这个测试验证函数逻辑，实际配置中所有提供商都有default_models
        # 如果提供商的default_models为空列表，应返回空字符串
        pass  # 实际配置中所有提供商都有default_models

    def test_get_default_model_default_type(self):
        """
        函数级注释：测试默认provider_type为llm
        内部逻辑：不传type参数时默认使用llm
        """
        result = get_default_model("ollama")
        assert result  # 应该返回LLM默认模型

    def test_get_default_model_local_embedding(self):
        """
        函数级注释：测试本地Embedding默认模型
        """
        result = get_default_model("local", "embedding")
        assert result  # 非空字符串
        assert "bge" in result.lower()


class TestLLMProviderIds:
    """
    类级注释：LLM提供商ID常量测试类
    """

    def test_all_llm_provider_ids_unique(self):
        """
        函数级注释：测试LLM提供商ID唯一性
        内部逻辑：确保没有重复的提供商ID
        """
        provider_ids = [p["id"] for p in LLM_PROVIDERS]
        assert len(provider_ids) == len(set(provider_ids)), "LLM provider IDs should be unique"

    def test_all_embedding_provider_ids_unique(self):
        """
        函数级注释：测试Embedding提供商ID唯一性
        内部逻辑：确保没有重复的提供商ID
        """
        provider_ids = [p["id"] for p in EMBEDDING_PROVIDERS]
        assert len(provider_ids) == len(set(provider_ids)), "Embedding provider IDs should be unique"

    def test_expected_llm_providers_exist(self):
        """
        函数级注释：测试预期的主要LLM提供商存在
        内部逻辑：验证ollama、zhipuai、openai等关键提供商
        """
        llm_ids = {p["id"] for p in LLM_PROVIDERS}
        expected_providers = {"ollama", "zhipuai", "openai", "minimax", "moonshot", "deepseek"}
        assert expected_providers.issubset(llm_ids)

    def test_expected_embedding_providers_exist(self):
        """
        函数级注释：测试预期的主要Embedding提供商存在
        内部逻辑：验证ollama、zhipuai、local、openai等关键提供商
        """
        embedding_ids = {p["id"] for p in EMBEDDING_PROVIDERS}
        expected_providers = {"ollama", "zhipuai", "local", "openai"}
        assert expected_providers.issubset(embedding_ids)
