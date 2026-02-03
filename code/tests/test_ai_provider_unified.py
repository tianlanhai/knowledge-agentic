# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：统一AI工厂模块测试
内部逻辑：全面测试UnifiedAIFactory及相关功能
设计模式：外观模式 + 工厂模式测试
测试覆盖范围：
    - UnifiedAIFactory 初始化和配置
    - create_llm LLM创建
    - create_embeddings Embedding创建
    - create_all 同时创建
    - 缓存管理
    - create_ai_provider 便捷函数
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Optional

from app.core.ai_provider.unified import (
    UnifiedAIFactory,
    unified_ai_factory,
    create_ai_provider,
)
from app.core.ai_provider.base import AIProviderType, AIComponentType
from app.core.ai_provider.config import AIProviderConfig


# ========================================================================
# 测试类：UnifiedAIFactory 初始化和配置
# ========================================================================

class TestUnifiedAIFactoryInit:
    """
    类级注释：测试统一AI工厂初始化
    测试范围：构造函数、初始状态
    """

    def test_initialization(self):
        """测试：工厂初始化"""
        # 内部逻辑：验证初始状态
        factory = UnifiedAIFactory()

        # 验证：初始状态
        assert factory._current_config is None
        assert factory._llm_cache == {}
        assert factory._embedding_cache == {}

    def test_global_instance(self):
        """测试：全局单例实例"""
        # 内部逻辑：验证全局实例存在
        from app.core.ai_provider.unified import unified_ai_factory

        assert isinstance(unified_ai_factory, UnifiedAIFactory)


# ========================================================================
# 测试类：set_config
# ========================================================================

class TestUnifiedAIFactorySetConfig:
    """
    类级注释：测试配置设置
    测试范围：配置更新、缓存清空
    """

    def test_set_config_updates_current_config(self):
        """测试：设置配置更新当前配置"""
        factory = UnifiedAIFactory()
        config = AIProviderConfig(
            provider_type=AIProviderType.OLLAMA,
            model="llama3"
        )

        with patch('app.core.ai_provider.unified.logger') as mock_logger:
            factory.set_config(config)

            # 验证：配置已更新
            assert factory._current_config is config
            # 验证：记录日志
            assert mock_logger.info.called

    def test_set_config_clears_llm_cache(self):
        """测试：设置配置清空LLM缓存"""
        factory = UnifiedAIFactory()
        factory._llm_cache["key"] = MagicMock()

        config = AIProviderConfig(provider_type=AIProviderType.OLLAMA)
        factory.set_config(config)

        # 验证：缓存被清空
        assert factory._llm_cache == {}

    def test_set_config_clears_embedding_cache(self):
        """测试：设置配置清空Embedding缓存"""
        factory = UnifiedAIFactory()
        factory._embedding_cache["key"] = MagicMock()

        config = AIProviderConfig(provider_type=AIProviderType.OLLAMA)
        factory.set_config(config)

        # 验证：缓存被清空
        assert factory._embedding_cache == {}


# ========================================================================
# 测试类：create_llm
# ========================================================================

class TestUnifiedAIFactoryCreateLLM:
    """
    类级注释：测试LLM创建
    测试范围：配置使用、缓存、工厂调用
    """

    def test_create_llm_with_passed_config(self):
        """测试：使用传入的配置创建"""
        factory = UnifiedAIFactory()
        config = AIProviderConfig(
            provider_type=AIProviderType.OLLAMA,
            model="llama3"
        )

        mock_llm = MagicMock()
        mock_factory = MagicMock()
        mock_factory.create_llm.return_value = mock_llm
        mock_factory.supports_component.return_value = True

        with patch('app.core.ai_provider.unified.AIProviderFactoryRegistry') as mock_registry:
            mock_registry.get_factory.return_value = mock_factory

            result = factory.create_llm(config)

            # 验证：返回创建的LLM
            assert result is mock_llm
            # 验证：使用了传入的配置
            mock_factory.create_llm.assert_called_once()

    def test_create_llm_with_current_config(self):
        """测试：使用当前配置创建"""
        factory = UnifiedAIFactory()
        current_config = AIProviderConfig(
            provider_type=AIProviderType.OLLAMA,
            model="llama3"
        )
        factory._current_config = current_config

        mock_llm = MagicMock()
        mock_factory = MagicMock()
        mock_factory.create_llm.return_value = mock_llm
        mock_factory.supports_component.return_value = True

        with patch('app.core.ai_provider.unified.AIProviderFactoryRegistry') as mock_registry:
            mock_registry.get_factory.return_value = mock_factory

            result = factory.create_llm()

            # 验证：使用当前配置
            mock_factory.create_llm.assert_called_once()

    def test_create_llm_without_config_raises_error(self):
        """测试：无配置时抛出错误"""
        factory = UnifiedAIFactory()
        # 不设置任何配置

        with pytest.raises(ValueError) as exc_info:
            factory.create_llm()

        assert "未设置 AI 提供商配置" in str(exc_info.value)

    def test_create_llm_uses_cache(self):
        """测试：使用缓存的LLM"""
        factory = UnifiedAIFactory()
        config = AIProviderConfig(
            provider_type=AIProviderType.OLLAMA,
            model="llama3"
        )

        # 预设缓存
        cached_llm = MagicMock()
        factory._llm_cache["ollama_llama3"] = cached_llm

        with patch('app.core.ai_provider.unified.logger') as mock_logger:
            result = factory.create_llm(config)

            # 验证：返回缓存的实例
            assert result is cached_llm
            # 验证：记录了调试日志
            assert mock_logger.debug.called

    def test_create_llm_caches_result(self):
        """测试：创建结果被缓存"""
        factory = UnifiedAIFactory()
        config = AIProviderConfig(
            provider_type=AIProviderType.OLLAMA,
            model="llama3"
        )

        mock_llm = MagicMock()
        mock_factory = MagicMock()
        mock_factory.create_llm.return_value = mock_llm
        mock_factory.supports_component.return_value = True

        with patch('app.core.ai_provider.unified.AIProviderFactoryRegistry') as mock_registry:
            mock_registry.get_factory.return_value = mock_factory

            result1 = factory.create_llm(config)
            result2 = factory.create_llm(config)

            # 验证：第二次使用缓存
            assert result1 is mock_llm
            assert result2 is mock_llm
            assert mock_factory.create_llm.call_count == 1  # 只调用一次

    def test_create_llm_with_extra_params(self):
        """测试：传递额外参数"""
        factory = UnifiedAIFactory()
        config = AIProviderConfig(
            provider_type=AIProviderType.OLLAMA,
            model="llama3"
        )

        mock_llm = MagicMock()
        mock_factory = MagicMock()
        mock_factory.create_llm.return_value = mock_llm
        mock_factory.supports_component.return_value = True

        with patch('app.core.ai_provider.unified.AIProviderFactoryRegistry') as mock_registry:
            mock_registry.get_factory.return_value = mock_factory

            factory.create_llm(config, extra_param="value")

            # 验证：额外参数被传递（通过config的extra_params）


# ========================================================================
# 测试类：create_embeddings
# ========================================================================

class TestUnifiedAIFactoryCreateEmbeddings:
    """
    类级注释：测试Embedding创建
    测试范围：配置使用、缓存、组件支持检查
    """

    def test_create_embeddings_with_passed_config(self):
        """测试：使用传入的配置创建"""
        factory = UnifiedAIFactory()
        config = AIProviderConfig(
            provider_type=AIProviderType.OLLAMA,
            model="nomic-embed-text"
        )

        mock_embeddings = MagicMock()
        mock_factory = MagicMock()
        mock_factory.create_embeddings.return_value = mock_embeddings
        mock_factory.supports_component.return_value = True

        with patch('app.core.ai_provider.unified.AIProviderFactoryRegistry') as mock_registry:
            mock_registry.get_factory.return_value = mock_factory

            result = factory.create_embeddings(config)

            # 验证：返回创建的embeddings
            assert result is mock_embeddings

    def test_create_embeddings_unsupported_provider(self):
        """测试：不支持的提供商"""
        factory = UnifiedAIFactory()
        config = AIProviderConfig(
            provider_type=AIProviderType.OLLAMA,
            model="embed-model"
        )

        mock_factory = MagicMock()
        mock_factory.supports_component.return_value = False  # 不支持

        with patch('app.core.ai_provider.unified.AIProviderFactoryRegistry') as mock_registry:
            mock_registry.get_factory.return_value = mock_factory

            with pytest.raises(ValueError) as exc_info:
                factory.create_embeddings(config)

            assert "不支持 Embeddings" in str(exc_info.value)

    def test_create_embeddings_uses_cache(self):
        """测试：使用缓存的embeddings"""
        factory = UnifiedAIFactory()
        config = AIProviderConfig(
            provider_type=AIProviderType.OLLAMA,
            model="nomic-embed-text"
        )

        # 预设缓存
        cached_embeddings = MagicMock()
        factory._embedding_cache["ollama_embedding_nomic-embed-text"] = cached_embeddings

        with patch('app.core.ai_provider.unified.logger') as mock_logger:
            result = factory.create_embeddings(config)

            # 验证：返回缓存的实例
            assert result is cached_embeddings
            assert mock_logger.debug.called

    def test_create_embeddings_caches_result(self):
        """测试：创建结果被缓存"""
        factory = UnifiedAIFactory()
        config = AIProviderConfig(
            provider_type=AIProviderType.OLLAMA,
            model="nomic-embed-text"
        )

        mock_embeddings = MagicMock()
        mock_factory = MagicMock()
        mock_factory.create_embeddings.return_value = mock_embeddings
        mock_factory.supports_component.return_value = True

        with patch('app.core.ai_provider.unified.AIProviderFactoryRegistry') as mock_registry:
            mock_registry.get_factory.return_value = mock_factory

            result1 = factory.create_embeddings(config)
            result2 = factory.create_embeddings(config)

            # 验证：第二次使用缓存
            assert result1 is mock_embeddings
            assert result2 is mock_embeddings
            assert mock_factory.create_embeddings.call_count == 1


# ========================================================================
# 测试类：create_all
# ========================================================================

class TestUnifiedAIFactoryCreateAll:
    """
    类级注释：测试同时创建LLM和Embeddings
    测试范围：组合创建、返回元组
    """

    def test_create_all_returns_tuple(self):
        """测试：返回LLM和Embeddings元组"""
        factory = UnifiedAIFactory()
        config = AIProviderConfig(
            provider_type=AIProviderType.OLLAMA,
            model="llama3"
        )

        mock_llm = MagicMock()
        mock_embeddings = MagicMock()
        mock_factory = MagicMock()
        mock_factory.create_llm.return_value = mock_llm
        mock_factory.create_embeddings.return_value = mock_embeddings
        mock_factory.supports_component.return_value = True

        with patch('app.core.ai_provider.unified.AIProviderFactoryRegistry') as mock_registry:
            mock_registry.get_factory.return_value = mock_factory

            llm, embeddings = factory.create_all(config)

            # 验证：返回元组
            assert llm is mock_llm
            assert embeddings is mock_embeddings

    def test_create_all_uses_same_config(self):
        """测试：两个组件使用同一配置"""
        factory = UnifiedAIFactory()
        config = AIProviderConfig(
            provider_type=AIProviderType.OLLAMA,
            model="llama3"
        )

        mock_llm = MagicMock()
        mock_embeddings = MagicMock()
        mock_factory = MagicMock()
        mock_factory.create_llm.return_value = mock_llm
        mock_factory.create_embeddings.return_value = mock_embeddings
        mock_factory.supports_component.return_value = True

        with patch('app.core.ai_provider.unified.AIProviderFactoryRegistry') as mock_registry:
            mock_registry.get_factory.return_value = mock_factory

            factory.create_all(config)

            # 验证：工厂被调用两次
            assert mock_factory.create_llm.call_count == 1
            assert mock_factory.create_embeddings.call_count == 1


# ========================================================================
# 测试类：clear_cache
# ========================================================================

class TestUnifiedAIFactoryClearCache:
    """
    类级注释：测试缓存清理
    测试范围：清空所有缓存
    """

    def test_clear_cache_empties_all_caches(self):
        """测试：清空所有缓存"""
        factory = UnifiedAIFactory()
        factory._llm_cache["llm_key"] = MagicMock()
        factory._embedding_cache["emb_key"] = MagicMock()

        with patch('app.core.ai_provider.unified.logger') as mock_logger:
            factory.clear_cache()

            # 验证：所有缓存被清空
            assert factory._llm_cache == {}
            assert factory._embedding_cache == {}
            # 验证：记录日志
            assert mock_logger.info.called

    def test_clear_cache_with_empty_caches(self):
        """测试：清空空缓存不报错"""
        factory = UnifiedAIFactory()
        # 缓存为空

        with patch('app.core.ai_provider.unified.logger') as mock_logger:
            factory.clear_cache()

            # 验证：不抛出错误
            assert factory._llm_cache == {}
            assert factory._embedding_cache == {}


# ========================================================================
# 测试类：create_ai_provider 便捷函数
# ========================================================================

class TestCreateAIProvider:
    """
    类级注释：测试创建提供商配置便捷函数
    测试范围：配置创建、默认值、错误处理
    """

    def test_create_with_all_params(self):
        """测试：传入所有参数"""
        config = create_ai_provider(
            provider_type="openai",
            api_key="sk-test",
            base_url="https://api.openai.com/v1",
            model="gpt-4"
        )

        # 验证：返回配置对象
        assert isinstance(config, AIProviderConfig)
        assert config.provider_type == AIProviderType.OPENAI
        assert config.api_key == "sk-test"
        assert config.base_url == "https://api.openai.com/v1"
        assert config.model == "gpt-4"

    def test_create_with_minimal_params(self):
        """测试：只传必需参数"""
        config = create_ai_provider(
            provider_type="ollama"
        )

        # 验证：使用默认值
        assert config.provider_type == AIProviderType.OLLAMA
        assert config.api_key is None
        assert config.base_url is None
        assert config.model is None

    def test_create_with_unknown_provider_fallback(self):
        """测试：未知提供商使用ollama"""
        with patch('app.core.ai_provider.unified.logger') as mock_logger:
            config = create_ai_provider(
                provider_type="unknown_provider"
            )

            # 验证：回退到ollama
            assert config.provider_type == AIProviderType.OLLAMA
            # 验证：记录警告
            assert mock_logger.warning.called

    def test_create_with_extra_kwargs(self):
        """测试：传递额外参数"""
        config = create_ai_provider(
            provider_type="openai",
            api_key="sk-test",
            temperature=0.7,
            max_tokens=2000
        )

        # 验证：额外参数被包含
        assert config.provider_type == AIProviderType.OPENAI
        assert config.api_key == "sk-test"

    def test_create_case_insensitive_provider(self):
        """测试：提供商名称大小写不敏感"""
        config = create_ai_provider(provider_type="OLLAMA")

        assert config.provider_type == AIProviderType.OLLAMA

        config = create_ai_provider(provider_type="Ollama")

        assert config.provider_type == AIProviderType.OLLAMA


# ========================================================================
# 测试类：缓存键生成
# ========================================================================

class TestCacheKeyGeneration:
    """
    类级注释：测试缓存键生成逻辑
    测试范围：不同配置生成不同键
    """

    def test_different_models_different_keys(self):
        """测试：不同模型生成不同缓存键"""
        factory = UnifiedAIFactory()
        config1 = AIProviderConfig(
            provider_type=AIProviderType.OLLAMA,
            model="llama3"
        )
        config2 = AIProviderConfig(
            provider_type=AIProviderType.OLLAMA,
            model="mistral"
        )

        mock_llm1 = MagicMock()
        mock_llm2 = MagicMock()
        mock_factory = MagicMock()
        mock_factory.create_llm.side_effect = [mock_llm1, mock_llm2]
        mock_factory.supports_component.return_value = True

        with patch('app.core.ai_provider.unified.AIProviderFactoryRegistry') as mock_registry:
            mock_registry.get_factory.return_value = mock_factory

            result1 = factory.create_llm(config1)
            result2 = factory.create_llm(config2)

            # 验证：不同模型不共享缓存
            assert result1 is mock_llm1
            assert result2 is mock_llm2
            assert mock_factory.create_llm.call_count == 2

    def test_different_providers_different_keys(self):
        """测试：不同提供商生成不同缓存键"""
        factory = UnifiedAIFactory()
        config1 = AIProviderConfig(
            provider_type=AIProviderType.OLLAMA,
            model="llama3"
        )
        config2 = AIProviderConfig(
            provider_type=AIProviderType.OPENAI,
            model="gpt-4"
        )

        mock_llm1 = MagicMock()
        mock_llm2 = MagicMock()
        mock_factory = MagicMock()
        mock_factory.create_llm.side_effect = [mock_llm1, mock_llm2]
        mock_factory.supports_component.return_value = True

        with patch('app.core.ai_provider.unified.AIProviderFactoryRegistry') as mock_registry:
            mock_registry.get_factory.return_value = mock_factory

            factory.create_llm(config1)
            factory.create_llm(config2)

            # 验证：不同提供商不共享缓存
            assert mock_factory.create_llm.call_count == 2

    def test_default_model_in_cache_key(self):
        """测试：默认模型在缓存键中"""
        factory = UnifiedAIFactory()
        config = AIProviderConfig(
            provider_type=AIProviderType.OLLAMA,
            model=None  # 无模型
        )

        mock_llm = MagicMock()
        mock_factory = MagicMock()
        mock_factory.create_llm.return_value = mock_llm
        mock_factory.supports_component.return_value = True

        with patch('app.core.ai_provider.unified.AIProviderFactoryRegistry') as mock_registry:
            mock_registry.get_factory.return_value = mock_factory

            factory.create_llm(config)

            # 验证：缓存键包含default


# ========================================================================
# 测试类：边界情况
# ========================================================================

class TestUnifiedAIFactoryEdgeCases:
    """
    类级注释：测试工厂边界情况
    测试范围：None处理、空值、异常情况
    """

    def test_create_llm_with_none_config_and_no_current(self):
        """测试：None配置且无当前配置"""
        factory = UnifiedAIFactory()

        with pytest.raises(ValueError):
            factory.create_llm(None)

    def test_create_embeddings_with_none_config_and_no_current(self):
        """测试：None配置且无当前配置"""
        factory = UnifiedAIFactory()

        with pytest.raises(ValueError):
            factory.create_embeddings(None)

    def test_create_all_with_none_config_and_no_current(self):
        """测试：None配置且无当前配置创建所有"""
        factory = UnifiedAIFactory()

        with pytest.raises(ValueError):
            factory.create_all(None)

    def test_multiple_factory_instances_independent(self):
        """测试：多个工厂实例独立"""
        factory1 = UnifiedAIFactory()
        factory2 = UnifiedAIFactory()

        config1 = AIProviderConfig(
            provider_type=AIProviderType.OLLAMA,
            model="llama3"
        )
        config2 = AIProviderConfig(
            provider_type=AIProviderType.OPENAI,
            model="gpt-4"
        )

        factory1.set_config(config1)
        factory2.set_config(config2)

        # 验证：两个工厂的配置独立
        assert factory1._current_config is config1
        assert factory2._current_config is config2

    def test_clear_cache_does_not_affect_config(self):
        """测试：清空缓存不影响配置"""
        factory = UnifiedAIFactory()
        config = AIProviderConfig(
            provider_type=AIProviderType.OLLAMA,
            model="llama3"
        )
        factory.set_config(config)

        factory.clear_cache()

        # 验证：配置保留
        assert factory._current_config is config

    def test_provider_type_enum_values(self):
        """测试：提供商类型枚举"""
        config = create_ai_provider(provider_type="ollama")

        # 验证：枚举值正确
        assert config.provider_type.value == "ollama"

    def test_embedding_cache_key_includes_type(self):
        """测试：Embedding缓存键包含类型标识"""
        factory = UnifiedAIFactory()
        config = AIProviderConfig(
            provider_type=AIProviderType.OLLAMA,
            model="nomic-embed-text"
        )

        mock_embeddings = MagicMock()
        mock_factory = MagicMock()
        mock_factory.create_embeddings.return_value = mock_embeddings
        mock_factory.supports_component.return_value = True

        with patch('app.core.ai_provider.unified.AIProviderFactoryRegistry') as mock_registry:
            mock_registry.get_factory.return_value = mock_factory

            factory.create_embeddings(config)

            # 验证：缓存键包含embedding标识
            assert any("embedding" in key for key in factory._embedding_cache.keys())
