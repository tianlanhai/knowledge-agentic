# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：AI Provider提供商模块覆盖率测试
内部逻辑：覆盖ai_provider providers的未测试代码路径
"""

import pytest
from unittest.mock import Mock, patch
from app.core.ai_provider.config import AIProviderConfig, AIProviderType
from app.core.ai_provider.providers.ollama import OllamaProviderFactory
from app.core.ai_provider.providers.zhipuai import ZhipuAIProviderFactory
from app.core.ai_provider.providers.openai import OpenAIProviderFactory
from app.core.ai_provider.providers.deepseek import DeepSeekProviderFactory
from app.core.ai_provider.providers.moonshot import MoonshotProviderFactory
from app.core.ai_provider.providers.minimax import MiniMaxProviderFactory


class TestOllamaProviderFactory:
    """
    类级注释：OllamaProviderFactory测试
    职责：覆盖Ollama提供商的所有代码路径
    """

    def test_provider_type(self):
        """测试目的：覆盖provider_type属性"""
        factory = OllamaProviderFactory()
        assert factory.provider_type == AIProviderType.OLLAMA

    def test_default_models(self):
        """测试目的：覆盖默认模型配置"""
        factory = OllamaProviderFactory()
        assert factory.DEFAULT_LLM_MODEL == "llama2"
        assert factory.DEFAULT_EMBEDDING_MODEL == "llama2"

    def test_requires_base_url(self):
        """测试目的：覆盖requires_base_url属性"""
        factory = OllamaProviderFactory()
        assert factory.REQUIRES_BASE_URL is True

    def test_customize_llm_params_with_base_url(self):
        """测试目的：覆盖_customize_llm_params添加base_url"""
        factory = OllamaProviderFactory()
        config = AIProviderConfig(
            provider_type=AIProviderType.OLLAMA,
            base_url="http://localhost:11434",
            model="llama2"
        )
        params = {}

        result = factory._customize_llm_params(params, config)

        assert result["base_url"] == "http://localhost:11434"

    def test_customize_llm_params_without_base_url(self):
        """测试目的：覆盖_customize_llm_params无base_url的路径"""
        factory = OllamaProviderFactory()
        config = AIProviderConfig(
            provider_type=AIProviderType.OLLAMA,
            model="llama2"
        )
        params = {}

        result = factory._customize_llm_params(params, config)

        # base_url不会被添加（因为没有设置）
        assert "base_url" not in result

    def test_create_llm_with_full_config(self):
        """测试目的：覆盖create_llm完整配置路径"""
        factory = OllamaProviderFactory()
        config = AIProviderConfig(
            provider_type=AIProviderType.OLLAMA,
            base_url="http://localhost:11434",
            model="llama2",
            temperature=0.7
        )

        # Mock _get_llm_class
        mock_llm_class = Mock()
        mock_instance = Mock()
        mock_llm_class.return_value = mock_instance

        with patch.object(factory, '_get_llm_class', return_value=mock_llm_class):
            result = factory.create_llm(config)

            assert result is not None
            mock_llm_class.assert_called_once()

    def test_create_embeddings_with_config(self):
        """测试目的：覆盖create_embeddings完整配置路径"""
        factory = OllamaProviderFactory()
        config = AIProviderConfig(
            provider_type=AIProviderType.OLLAMA,
            base_url="http://localhost:11434",
            model="llama2"
        )

        # Mock _get_embedding_class
        mock_embed_class = Mock()
        mock_instance = Mock()
        mock_embed_class.return_value = mock_instance

        with patch.object(factory, '_get_embedding_class', return_value=mock_embed_class):
            result = factory.create_embeddings(config)

            assert result is not None
            mock_embed_class.assert_called_once()


class TestZhipuAIProviderFactory:
    """
    类级注释：ZhipuAIProviderFactory测试
    职责：覆盖ZhipuAI提供商的所有代码路径
    """

    def test_provider_type(self):
        """测试目的：覆盖provider_type属性"""
        factory = ZhipuAIProviderFactory()
        assert factory.provider_type == AIProviderType.ZHIPUAI

    def test_default_models(self):
        """测试目的：覆盖默认模型配置"""
        factory = ZhipuAIProviderFactory()
        assert factory.DEFAULT_LLM_MODEL == "glm-4"
        assert factory.DEFAULT_EMBEDDING_MODEL == "embedding-2"

    def test_requires_api_key(self):
        """测试目的：覆盖requires_api_key属性"""
        factory = ZhipuAIProviderFactory()
        assert factory.REQUIRES_API_KEY is True

    def test_get_llm_class(self):
        """测试目的：覆盖_get_llm_class方法"""
        factory = ZhipuAIProviderFactory()
        llm_class = factory._get_llm_class()
        assert llm_class is not None

    def test_get_embedding_class(self):
        """测试目的：覆盖_get_embedding_class方法"""
        factory = ZhipuAIProviderFactory()
        embed_class = factory._get_embedding_class()
        assert embed_class is not None

    def test_create_llm_with_config(self):
        """测试目的：覆盖create_llm完整配置路径"""
        factory = ZhipuAIProviderFactory()
        config = AIProviderConfig(
            provider_type=AIProviderType.ZHIPUAI,
            api_key="test-api-key",
            model="glm-4"
        )

        # Mock langchain_community.chat_models.ChatZhipuAI
        with patch('langchain_community.chat_models.ChatZhipuAI') as mock_chat_zhipuai:
            mock_instance = Mock()
            mock_chat_zhipuai.return_value = mock_instance

            result = factory.create_llm(config)

            assert result is not None
            mock_chat_zhipuai.assert_called_once()

    def test_create_llm_fallback_to_zhipuai(self):
        """测试目的：覆盖_get_llm_class备用路径"""
        factory = ZhipuAIProviderFactory()
        # 获取类时会尝试导入备用ZhipuAI类
        llm_class = factory._get_llm_class()
        assert llm_class is not None

    def test_supports_component(self):
        """测试目的：覆盖supports_component方法"""
        factory = ZhipuAIProviderFactory()
        from app.core.ai_provider.base import AIComponentType
        # 默认情况下应该支持LLM和Embedding
        assert factory.supports_component(AIComponentType.LLM) is True


class TestOpenAIProviderFactory:
    """
    类级注释：OpenAIProviderFactory测试
    职责：覆盖OpenAI提供商的所有代码路径
    """

    def test_provider_type(self):
        """测试目的：覆盖provider_type属性"""
        factory = OpenAIProviderFactory()
        assert factory.provider_type == AIProviderType.OPENAI

    def test_default_models(self):
        """测试目的：覆盖默认模型配置"""
        factory = OpenAIProviderFactory()
        assert factory.DEFAULT_LLM_MODEL == "gpt-3.5-turbo"
        assert factory.DEFAULT_EMBEDDING_MODEL == "text-embedding-ada-002"

    def test_requires_api_key(self):
        """测试目的：覆盖requires_api_key属性"""
        factory = OpenAIProviderFactory()
        assert factory.REQUIRES_API_KEY is True

    def test_get_llm_class(self):
        """测试目的：覆盖_get_llm_class方法"""
        factory = OpenAIProviderFactory()
        llm_class = factory._get_llm_class()
        assert llm_class is not None

    def test_get_embedding_class(self):
        """测试目的：覆盖_get_embedding_class方法"""
        factory = OpenAIProviderFactory()
        embed_class = factory._get_embedding_class()
        assert embed_class is not None

    def test_create_llm_with_config(self):
        """测试目的：覆盖create_llm完整配置路径"""
        factory = OpenAIProviderFactory()
        config = AIProviderConfig(
            provider_type=AIProviderType.OPENAI,
            api_key="test-api-key",
            model="gpt-4",
            temperature=0.7
        )

        # Mock _get_llm_class
        mock_llm_class = Mock()
        mock_instance = Mock()
        mock_llm_class.return_value = mock_instance

        with patch.object(factory, '_get_llm_class', return_value=mock_llm_class):
            result = factory.create_llm(config)

            assert result is not None
            mock_llm_class.assert_called_once()

    def test_create_embeddings_with_config(self):
        """测试目的：覆盖create_embeddings完整配置路径"""
        factory = OpenAIProviderFactory()
        config = AIProviderConfig(
            provider_type=AIProviderType.OPENAI,
            api_key="test-api-key",
            model="text-embedding-ada-002"
        )

        # Mock _get_embedding_class
        mock_embed_class = Mock()
        mock_instance = Mock()
        mock_embed_class.return_value = mock_instance

        with patch.object(factory, '_get_embedding_class', return_value=mock_embed_class):
            result = factory.create_embeddings(config)

            assert result is not None
            mock_embed_class.assert_called_once()


class TestDeepSeekProviderFactory:
    """
    类级注释：DeepSeekProviderFactory测试
    职责：覆盖DeepSeek提供商的所有代码路径
    """

    def test_provider_type(self):
        """测试目的：覆盖provider_type属性"""
        factory = DeepSeekProviderFactory()
        assert factory.provider_type == AIProviderType.DEEPSEEK

    def test_default_models(self):
        """测试目的：覆盖默认模型配置"""
        factory = DeepSeekProviderFactory()
        assert factory.DEFAULT_LLM_MODEL == "deepseek-chat"
        assert factory.DEFAULT_EMBEDDING_MODEL == "deepseek-embedding"

    def test_requires_api_key(self):
        """测试目的：覆盖requires_api_key属性"""
        factory = DeepSeekProviderFactory()
        assert factory.REQUIRES_API_KEY is True

    def test_default_base_url(self):
        """测试目的：覆盖DEFAULT_BASE_URL属性"""
        factory = DeepSeekProviderFactory()
        assert factory.DEFAULT_BASE_URL == "https://api.deepseek.com/v1"

    def test_get_llm_class(self):
        """测试目的：覆盖_get_llm_class方法"""
        factory = DeepSeekProviderFactory()
        llm_class = factory._get_llm_class()
        assert llm_class is not None

    def test_get_embedding_class(self):
        """测试目的：覆盖_get_embedding_class方法"""
        factory = DeepSeekProviderFactory()
        embed_class = factory._get_embedding_class()
        assert embed_class is not None

    def test_customize_llm_params(self):
        """测试目的：覆盖_customize_llm_params方法"""
        factory = DeepSeekProviderFactory()
        config = AIProviderConfig(
            provider_type=AIProviderType.DEEPSEEK,
            model="deepseek-chat"
        )
        params = {}

        result = factory._customize_llm_params(params, config)

        assert result["base_url"] == "https://api.deepseek.com/v1"

    def test_customize_llm_params_with_custom_base_url(self):
        """测试目的：覆盖使用自定义base_url的路径"""
        factory = DeepSeekProviderFactory()
        config = AIProviderConfig(
            provider_type=AIProviderType.DEEPSEEK,
            base_url="https://custom.deepseek.com/v1",
            model="deepseek-chat"
        )
        params = {"base_url": "https://existing.com/v1"}

        result = factory._customize_llm_params(params, config)

        # 已有base_url不会被覆盖
        assert result["base_url"] == "https://existing.com/v1"

    def test_customize_embedding_params(self):
        """测试目的：覆盖_customize_embedding_params方法"""
        factory = DeepSeekProviderFactory()
        config = AIProviderConfig(
            provider_type=AIProviderType.DEEPSEEK,
            model="deepseek-embedding"
        )
        params = {}

        result = factory._customize_embedding_params(params, config)

        assert result["base_url"] == "https://api.deepseek.com/v1"

    def test_supports_component(self):
        """测试目的：覆盖supports_component方法"""
        from app.core.ai_provider.base import AIComponentType
        factory = DeepSeekProviderFactory()
        # DeepSeek主要用于对话，不支持embedding
        assert factory.supports_component(AIComponentType.LLM) is True
        assert factory.supports_component(AIComponentType.EMBEDDING) is False


class TestMoonshotProviderFactory:
    """
    类级注释：MoonshotProviderFactory测试
    职责：覆盖Moonshot提供商的所有代码路径
    """

    def test_provider_type(self):
        """测试目的：覆盖provider_type属性"""
        factory = MoonshotProviderFactory()
        assert factory.provider_type == AIProviderType.MOONSHOT

    def test_default_models(self):
        """测试目的：覆盖默认模型配置"""
        factory = MoonshotProviderFactory()
        assert factory.DEFAULT_LLM_MODEL == "moonshot-v1-8k"
        assert factory.DEFAULT_EMBEDDING_MODEL == "moonshot-embedding"

    def test_requires_api_key(self):
        """测试目的：覆盖requires_api_key属性"""
        factory = MoonshotProviderFactory()
        assert factory.REQUIRES_API_KEY is True

    def test_default_base_url(self):
        """测试目的：覆盖DEFAULT_BASE_URL属性"""
        factory = MoonshotProviderFactory()
        assert factory.DEFAULT_BASE_URL == "https://api.moonshot.cn/v1"

    def test_get_llm_class(self):
        """测试目的：覆盖_get_llm_class方法"""
        factory = MoonshotProviderFactory()
        llm_class = factory._get_llm_class()
        assert llm_class is not None

    def test_get_embedding_class(self):
        """测试目的：覆盖_get_embedding_class方法"""
        factory = MoonshotProviderFactory()
        embed_class = factory._get_embedding_class()
        assert embed_class is not None

    def test_customize_llm_params(self):
        """测试目的：覆盖_customize_llm_params方法"""
        factory = MoonshotProviderFactory()
        config = AIProviderConfig(
            provider_type=AIProviderType.MOONSHOT,
            model="moonshot-v1-8k"
        )
        params = {}

        result = factory._customize_llm_params(params, config)

        assert result["base_url"] == "https://api.moonshot.cn/v1"

    def test_customize_embedding_params(self):
        """测试目的：覆盖_customize_embedding_params方法"""
        factory = MoonshotProviderFactory()
        config = AIProviderConfig(
            provider_type=AIProviderType.MOONSHOT,
            model="moonshot-embedding"
        )
        params = {}

        result = factory._customize_embedding_params(params, config)

        assert result["base_url"] == "https://api.moonshot.cn/v1"


class TestMiniMaxProviderFactory:
    """
    类级注释：MiniMaxProviderFactory测试
    职责：覆盖MiniMax提供商的所有代码路径
    """

    def test_provider_type(self):
        """测试目的：覆盖provider_type属性"""
        factory = MiniMaxProviderFactory()
        assert factory.provider_type == AIProviderType.MINIMAX

    def test_default_models(self):
        """测试目的：覆盖默认模型配置"""
        factory = MiniMaxProviderFactory()
        assert factory.DEFAULT_LLM_MODEL == "abab5.5-chat"
        assert factory.DEFAULT_EMBEDDING_MODEL == "embedding-v1"

    def test_requires_api_key(self):
        """测试目的：覆盖requires_api_key属性"""
        factory = MiniMaxProviderFactory()
        assert factory.REQUIRES_API_KEY is True

    def test_get_llm_class(self):
        """测试目的：覆盖_get_llm_class方法"""
        factory = MiniMaxProviderFactory()
        llm_class = factory._get_llm_class()
        assert llm_class is not None

    def test_get_embedding_class(self):
        """测试目的：覆盖_get_embedding_class方法"""
        factory = MiniMaxProviderFactory()
        embed_class = factory._get_embedding_class()
        assert embed_class is not None

    def test_create_llm(self):
        """测试目的：覆盖create_llm方法"""
        factory = MiniMaxProviderFactory()
        config = AIProviderConfig(
            provider_type=AIProviderType.MINIMAX,
            api_key="test-api-key",
            model="abab5.5-chat"
        )

        result = factory.create_llm(config)

        assert result is not None

    def test_create_embeddings(self):
        """测试目的：覆盖create_embeddings方法"""
        factory = MiniMaxProviderFactory()
        config = AIProviderConfig(
            provider_type=AIProviderType.MINIMAX,
            api_key="test-api-key",
            model="embedding-v1"
        )

        result = factory.create_embeddings(config)

        assert result is not None


class TestBaseAIProviderFactory:
    """
    类级注释：BaseAIProviderFactory测试
    职责：覆盖工厂基类的模板方法
    """

    @pytest.fixture
    def concrete_factory(self):
        """创建具体的工厂实现用于测试"""
        from app.core.ai_provider.base_factory import BaseAIProviderFactory
        from app.core.ai_provider.base import AIComponentType

        class TestFactory(BaseAIProviderFactory):
            provider_type = AIProviderType.OLLAMA
            DEFAULT_LLM_MODEL = "test-model"
            DEFAULT_EMBEDDING_MODEL = "test-embedding"

            def _get_llm_class(self):
                return Mock

            def _get_embedding_class(self):
                return Mock

        return TestFactory()

    def test_build_llm_params_with_all_fields(self, concrete_factory):
        """测试目的：覆盖_build_llm_params完整参数路径"""
        config = AIProviderConfig(
            provider_type=AIProviderType.OLLAMA,
            api_key="test-key",
            base_url="http://localhost:11434",
            model="custom-model",
            max_tokens=1000,
            temperature=0.7
        )

        params = concrete_factory._build_llm_params(config)

        assert params["model"] == "custom-model"
        assert params["api_key"] == "test-key"
        assert params["base_url"] == "http://localhost:11434"
        assert params["max_tokens"] == 1000
        assert params["temperature"] == 0.7

    def test_build_llm_params_with_defaults(self, concrete_factory):
        """测试目的：覆盖_build_llm_params默认值路径"""
        config = AIProviderConfig(
            provider_type=AIProviderType.OLLAMA
        )

        params = concrete_factory._build_llm_params(config)

        assert params["model"] == "test-model"
        assert "api_key" not in params
        assert "base_url" not in params

    def test_build_embedding_params_with_all_fields(self, concrete_factory):
        """测试目的：覆盖_build_embedding_params完整参数路径"""
        config = AIProviderConfig(
            provider_type=AIProviderType.OLLAMA,
            api_key="test-key",
            base_url="http://localhost:11434",
            model="custom-embedding"
        )

        params = concrete_factory._build_embedding_params(config)

        assert params["model"] == "custom-embedding"
        assert params["api_key"] == "test-key"
        assert params["base_url"] == "http://localhost:11434"

    def test_customize_llm_params_hook(self, concrete_factory):
        """测试目的：覆盖_customize_llm_params钩子方法"""
        config = AIProviderConfig(
            provider_type=AIProviderType.OLLAMA
        )
        params = {"existing": "value"}

        result = concrete_factory._customize_llm_params(params, config)

        # 默认实现应返回原参数
        assert result == params

    def test_customize_embedding_params_hook(self, concrete_factory):
        """测试目的：覆盖_customize_embedding_params钩子方法"""
        config = AIProviderConfig(
            provider_type=AIProviderType.OLLAMA
        )
        params = {"existing": "value"}

        result = concrete_factory._customize_embedding_params(params, config)

        # 默认实现应返回原参数
        assert result == params

    def test_get_default_llm_model(self, concrete_factory):
        """测试目的：覆盖_get_default_llm_model方法"""
        assert concrete_factory._get_default_llm_model() == "test-model"

    def test_get_default_embedding_model(self, concrete_factory):
        """测试目的：覆盖_get_default_embedding_model方法"""
        assert concrete_factory._get_default_embedding_model() == "test-embedding"

    def test_get_default_llm_model_none(self):
        """测试目的：覆盖DEFAULT_LLM_MODEL为None时的路径"""
        from app.core.ai_provider.base_factory import BaseAIProviderFactory

        class NoDefaultFactory(BaseAIProviderFactory):
            provider_type = AIProviderType.OLLAMA
            DEFAULT_LLM_MODEL = None

            def _get_llm_class(self):
                return Mock

            def _get_embedding_class(self):
                return Mock

        factory = NoDefaultFactory()
        assert factory._get_default_llm_model() == "default"

    def test_supports_component_default(self, concrete_factory):
        """测试目的：覆盖supports_component默认实现"""
        from app.core.ai_provider.base import AIComponentType
        # 默认应该支持所有组件
        assert concrete_factory.supports_component(AIComponentType.LLM) is True
        assert concrete_factory.supports_component(AIComponentType.EMBEDDING) is True
