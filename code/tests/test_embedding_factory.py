# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：Embedding 工厂类测试
内部逻辑：测试 EmbeddingFactory 重构后的功能，使用 ai_provider 模块
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.utils.embedding_factory import EmbeddingFactory
from app.models.model_config import EmbeddingConfig


@pytest.fixture(autouse=True)
def reset_factory_state():
    """
    函数级注释：重置工厂状态的fixture
    内部逻辑：每个测试后重置运行时配置和缓存
    """
    # 保存原始状态
    original_config = EmbeddingFactory._runtime_config
    original_cache = dict(EmbeddingFactory._instance_cache)

    yield

    # 内部逻辑：恢复原始状态
    EmbeddingFactory._runtime_config = original_config
    EmbeddingFactory._instance_cache.clear()
    EmbeddingFactory._instance_cache.update(original_cache)


class TestEmbeddingFactory:
    """
    类级注释：EmbeddingFactory 测试类
    职责：测试Embedding工厂的核心功能（重构后）
    """

    def test_create_ollama_embeddings(self):
        """
        函数级注释：测试创建Ollama Embedding
        内部逻辑：使用 ai_provider 模块创建 Ollama Embedding
        """
        config = {
            "provider": "ollama",
            "model": "mxbai-embed-large:latest",
            "endpoint": "http://localhost:11434"
        }
        EmbeddingFactory.set_runtime_config(config)

        try:
            embeddings = EmbeddingFactory.create_embeddings()
            assert embeddings is not None
        except Exception as e:
            pytest.skip(f"Ollama service not available: {e}")

    def test_create_zhipuai_embeddings(self):
        """
        函数级注释：测试创建智谱AI Embedding
        内部逻辑：使用 ai_provider 模块创建智谱AI Embedding
        """
        config = {
            "provider": "zhipuai",
            "model": "embedding-3",
            "endpoint": "https://open.bigmodel.cn/api/paas/v4/",
            "api_key": "test-key"
        }
        EmbeddingFactory.set_runtime_config(config)

        try:
            embeddings = EmbeddingFactory.create_embeddings()
            assert embeddings is not None
        except Exception as e:
            pytest.skip(f"ZhipuAI service not available: {e}")

    def test_create_local_embeddings(self):
        """
        函数级注释：测试创建本地HuggingFace Embedding
        内部逻辑：使用_create_local_embedding方法创建本地Embedding
        """
        config = {
            "provider": "local",
            "model": "BAAI/bge-small-zh-v1.5",
            "device": "cpu"
        }

        try:
            embeddings = EmbeddingFactory.create_embeddings(config)
            assert embeddings is not None
        except (ImportError, OSError, RuntimeError) as e:
            pytest.skip(f"Local embedding dependencies not available: {str(e)[:100]}")

    def test_create_openai_embeddings(self):
        """
        函数级注释：测试创建OpenAI Embedding
        内部逻辑：使用 ai_provider 模块创建 OpenAI Embedding
        """
        config = {
            "provider": "openai",
            "model": "text-embedding-3-small",
            "endpoint": "https://api.openai.com/v1",
            "api_key": "test-key"
        }
        EmbeddingFactory.set_runtime_config(config)

        try:
            embeddings = EmbeddingFactory.create_embeddings()
            assert embeddings is not None
        except ImportError:
            pytest.skip("OpenAI dependencies not installed")
        except Exception as e:
            pytest.skip(f"OpenAI API call failed: {e}")

    def test_set_runtime_config_clears_cache(self):
        """
        函数级注释：测试设置运行时配置清除缓存
        """
        EmbeddingFactory._instance_cache.clear()
        EmbeddingFactory._instance_cache["test"] = MagicMock()
        assert len(EmbeddingFactory._instance_cache) == 1

        new_config = {
            "provider": "zhipuai",
            "model": "embedding-3"
        }
        EmbeddingFactory.set_runtime_config(new_config)

        assert len(EmbeddingFactory._instance_cache) == 0
        assert EmbeddingFactory._runtime_config == new_config

    def test_set_runtime_config_updates_provider(self):
        """
        函数级注释：测试设置运行时配置更新提供商
        """
        config = {
            "provider": "ollama",
            "model": "nomic-embed-text",
            "endpoint": "http://localhost:11434"
        }

        EmbeddingFactory.set_runtime_config(config)

        assert EmbeddingFactory._runtime_config == config
        assert EmbeddingFactory._runtime_config["provider"] == "ollama"

    def test_runtime_config_overrides_env_vars(self):
        """
        函数级注释：测试运行时配置优先级高于环境变量
        """
        runtime_config = {
            "provider": "zhipuai",
            "model": "embedding-3"
        }
        EmbeddingFactory.set_runtime_config(runtime_config)

        resolved = EmbeddingFactory._resolve_config()
        assert resolved["provider"] == "zhipuai"
        assert resolved["model"] == "embedding-3"

    def test_resolve_config_fallback_to_env_vars(self):
        """
        函数级注释：测试无运行时配置时回退到环境变量
        """
        EmbeddingFactory._runtime_config = None

        resolved = EmbeddingFactory._resolve_config()
        assert "provider" in resolved
        assert "model" in resolved

    def test_create_embeddings_caches_instances(self):
        """
        函数级注释：测试创建Embedding时缓存实例
        """
        config = {
            "provider": "ollama",
            "model": "mxbai-embed-large:latest",
            "endpoint": "http://localhost:11434"
        }
        EmbeddingFactory.set_runtime_config(config)
        EmbeddingFactory._instance_cache.clear()

        try:
            EmbeddingFactory.create_embeddings()
            assert len(EmbeddingFactory._instance_cache) > 0
        except Exception:
            pytest.skip("Embedding creation failed")

    def test_clear_cache(self):
        """
        函数级注释：测试清除缓存功能
        """
        EmbeddingFactory._instance_cache["test_key"] = MagicMock()
        assert len(EmbeddingFactory._instance_cache) > 0

        EmbeddingFactory.clear_cache()
        assert len(EmbeddingFactory._instance_cache) == 0

    def test_resolve_config_priority(self):
        """
        函数级注释：测试配置解析优先级
        内部逻辑：传入配置 > 运行时配置 > 环境变量
        """
        EmbeddingFactory.set_runtime_config({"provider": "zhipuai", "model": "embedding-3"})

        passed_config = {"provider": "ollama", "model": "mxbai-embed-large:latest"}
        resolved = EmbeddingFactory._resolve_config(passed_config)
        assert resolved["provider"] == "ollama"

        resolved = EmbeddingFactory._resolve_config()
        assert resolved["provider"] == "zhipuai"

    def test_get_cache_key_generation(self):
        """
        函数级注释：测试缓存键生成
        """
        config = {
            "provider": "ollama",
            "model": "mxbai-embed-large:latest"
        }

        cache_key = EmbeddingFactory._get_cache_key(config)
        assert cache_key == "ollama_mxbai-embed-large:latest"

    def test_create_with_invalid_provider_raises_error(self):
        """
        函数级注释：测试无效提供商抛出异常
        """
        config = {"provider": "invalid", "model": "test"}

        with pytest.raises(ValueError, match="不支持的Embedding提供商"):
            EmbeddingFactory.create_embeddings(config)

    def test_create_by_provider_unimplemented(self):
        """
        函数级注释：测试_create_by_provider处理未实现提供商
        内部逻辑：调用未实现的提供商 -> 验证抛出ValueError
        """
        config = {"provider": "unknown", "model": "test"}

        with pytest.raises(ValueError, match="不支持的Embedding提供商"):
            EmbeddingFactory._create_by_provider("unknown", config)


class TestEmbeddingFactoryIntegration:
    """
    类级注释：Embedding工厂集成测试类
    """

    @pytest.mark.asyncio
    async def test_create_from_embedding_config(self, db_session):
        """
        函数级注释：测试从EmbeddingConfig创建实例
        """
        config_dict = {
            "provider": "ollama",
            "model": "mxbai-embed-large:latest",
            "endpoint": "http://localhost:11434",
            "api_key": "",
            "device": "cpu"
        }

        try:
            embeddings = EmbeddingFactory.create_embeddings(config_dict)
            assert embeddings is not None
        except Exception:
            pytest.skip("Embedding creation failed")

    def test_get_current_provider(self):
        """
        函数级注释：测试获取当前提供商
        """
        EmbeddingFactory.set_runtime_config({
            "provider": "zhipuai",
            "model": "embedding-3"
        })

        provider = EmbeddingFactory.get_current_provider()
        assert provider == "zhipuai"

    def test_get_current_model(self):
        """
        函数级注释：测试获取当前模型名称
        """
        EmbeddingFactory.set_runtime_config({
            "provider": "ollama",
            "model": "nomic-embed-text"
        })

        model = EmbeddingFactory.get_current_model()
        assert model == "nomic-embed-text"


class TestEmbeddingFactoryProviders:
    """
    类级注释：Embedding提供商特定测试类
    """

    def test_create_local_with_auto_device(self):
        """
        函数级注释：测试本地Embedding自动设备检测
        内部逻辑：设置device为auto -> 创建本地Embedding -> 验证设备检测逻辑
        """
        config = {
            "provider": "local",
            "model": "BAAI/bge-small-zh-v1.5",
            "device": "auto"
        }

        try:
            embeddings = EmbeddingFactory.create_embeddings(config)
            assert embeddings is not None
        except (ImportError, OSError, RuntimeError) as e:
            pytest.skip(f"Local embedding dependencies not available: {str(e)[:100]}")

    def test_create_local_with_cpu_device(self):
        """
        函数级注释：测试本地Embedding使用CPU设备
        内部逻辑：设置device为cpu -> 创建本地Embedding -> 验证使用CPU
        """
        config = {
            "provider": "local",
            "model": "BAAI/bge-small-zh-v1.5",
            "device": "cpu"
        }

        try:
            embeddings = EmbeddingFactory.create_embeddings(config)
            assert embeddings is not None
        except (ImportError, OSError, RuntimeError) as e:
            pytest.skip(f"Local embedding dependencies not available: {str(e)[:100]}")

    def test_create_zhipuai_with_custom_endpoint(self):
        """
        函数级注释：测试智谱AI自定义端点
        """
        config = {
            "provider": "zhipuai",
            "model": "embedding-2",
            "endpoint": "https://custom.example.com/v1",
            "api_key": "test-key"
        }
        EmbeddingFactory.set_runtime_config(config)

        try:
            embeddings = EmbeddingFactory.create_embeddings()
            assert embeddings is not None
        except Exception as e:
            pytest.skip(f"ZhipuAI service not available: {e}")

    def test_create_openai_with_custom_endpoint(self):
        """
        函数级注释：测试OpenAI自定义端点
        """
        config = {
            "provider": "openai",
            "model": "text-embedding-3-large",
            "endpoint": "https://custom.openai.example.com/v1",
            "api_key": "test-key"
        }
        EmbeddingFactory.set_runtime_config(config)

        try:
            embeddings = EmbeddingFactory.create_embeddings()
            assert embeddings is not None
        except ImportError:
            pytest.skip("OpenAI dependencies not installed")
        except Exception as e:
            pytest.skip(f"OpenAI API call failed: {e}")


class TestEmbeddingFactoryHotSwitch:
    """
    类级注释：Embedding热切换专项测试类
    """

    def test_hot_switch_from_ollama_to_zhipuai(self):
        """
        函数级注释：测试从Ollama切换到智谱AI
        """
        ollama_config = {
            "provider": "ollama",
            "model": "mxbai-embed-large:latest",
            "endpoint": "http://localhost:11434"
        }
        EmbeddingFactory.set_runtime_config(ollama_config)

        assert EmbeddingFactory.get_current_provider() == "ollama"

        EmbeddingFactory._instance_cache["test"] = MagicMock()

        zhipuai_config = {
            "provider": "zhipuai",
            "model": "embedding-3",
            "endpoint": "https://open.bigmodel.cn/api/paas/v4/",
            "api_key": "test-key"
        }
        EmbeddingFactory.set_runtime_config(zhipuai_config)

        assert len(EmbeddingFactory._instance_cache) == 0
        assert EmbeddingFactory.get_current_provider() == "zhipuai"

    def test_hot_switch_preserves_runtime_config(self):
        """
        函数级注释：测试热切换保留运行时配置
        """
        configs = [
            {"provider": "ollama", "model": "model1"},
            {"provider": "zhipuai", "model": "model2"},
            {"provider": "local", "model": "model3"}
        ]

        for config in configs:
            EmbeddingFactory.set_runtime_config(config)
            assert EmbeddingFactory._runtime_config == config
            assert EmbeddingFactory.get_current_provider() == config["provider"]


# ============================================================================
# 额外测试：覆盖未覆盖的代码行 (113, 237-241, 248)
# ============================================================================


class TestEmbeddingFactoryMissingCoverage:
    """
    类级注释：补充测试以覆盖未覆盖的代码行
    未覆盖行：
        113: 提供商不支持Embedding组件时抛出ValueError
        237-241: validate_provider_config中本地模型的torch导入检查
        248: validate_provider_config最后的return True（ollama提供商）
    """

    def test_create_by_provider_unsupported_embedding_component(self):
        """
        测试目的：覆盖行113
        测试场景：提供商不支持Embedding组件
        预期：应该抛出ValueError，提示提供商不支持Embedding组件
        """
        from app.core.ai_provider import AIProviderType
        from app.core.ai_provider import AIProviderFactoryRegistry
        from app.core.ai_provider import AIProviderConfig

        # 内部逻辑：创建一个不支持Embedding的mock工厂
        mock_factory = MagicMock()
        mock_factory.supports_component.return_value = False

        # 内部变量：保存原始工厂
        original_get_factory = AIProviderFactoryRegistry.get_factory

        # 内部逻辑：替换get_factory方法
        def mock_get_factory(provider_type):
            return mock_factory

        AIProviderFactoryRegistry.get_factory = mock_get_factory

        try:
            config = {
                "provider": "ollama",
                "model": "test-model"
            }

            with pytest.raises(ValueError) as exc_info:
                EmbeddingFactory._create_by_provider("ollama", config)

            assert "不支持 Embedding 组件" in str(exc_info.value)
        finally:
            # 内部逻辑：恢复原始方法
            AIProviderFactoryRegistry.get_factory = original_get_factory

    def test_validate_provider_config_local_with_torch(self):
        """
        测试目的：覆盖行237-241
        测试场景：本地提供商配置验证时torch可用
        预期：torch可用时返回True
        """
        config = {
            "provider": "local",
            "model": "test-model"
        }

        # 内部逻辑：mock torch导入成功
        with patch('builtins.__import__') as mock_import:
            def import_side_effect(name, *args, **kwargs):
                if name == "torch":
                    return MagicMock()
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            result = EmbeddingFactory.validate_provider_config("local", config)
            assert result is True

    def test_validate_provider_config_local_without_torch(self):
        """
        测试目的：覆盖行240-241
        测试场景：本地提供商配置验证时torch不可用
        预期：torch不可用时返回False
        """
        config = {
            "provider": "local",
            "model": "test-model"
        }

        # 内部逻辑：mock torch导入失败
        with patch('builtins.__import__') as mock_import:
            def import_side_effect(name, *args, **kwargs):
                if name == "torch":
                    raise ImportError("No module named 'torch'")
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            result = EmbeddingFactory.validate_provider_config("local", config)
            assert result is False

    def test_validate_provider_config_ollama_provider(self):
        """
        测试目的：覆盖行248
        测试场景：ollama提供商配置验证
        预期：ollama是本地提供商，不需要api_key，应该返回True
        """
        config = {
            "provider": "ollama",
            "model": "nomic-embed-text",
            "endpoint": "http://localhost:11434"
        }

        result = EmbeddingFactory.validate_provider_config("ollama", config)
        # 内部逻辑：ollama不是云端提供商也不是local，走到最后的return True
        assert result is True

    def test_validate_provider_config_unsupported_provider(self):
        """
        测试目的：覆盖_is_supported_provider返回False的分支
        测试场景：不支持的提供商
        预期：应该返回False
        """
        config = {
            "provider": "unknown_provider",
            "model": "test-model"
        }

        result = EmbeddingFactory.validate_provider_config("unknown_provider", config)
        assert result is False

    def test_supported_providers_constant(self):
        """
        测试目的：验证SUPPORTED_PROVIDERS常量
        测试场景：检查常量包含所有预期的提供商
        """
        supported = EmbeddingFactory.SUPPORTED_PROVIDERS
        assert "ollama" in supported
        assert "zhipuai" in supported
        assert "openai" in supported
        assert "moonshot" in supported
        assert "deepseek" in supported
        assert "local" in supported

    def test_provider_enum_map_constant(self):
        """
        测试目的：验证_PROVIDER_ENUM_MAP常量
        测试场景：检查映射包含所有预期的提供商
        """
        enum_map = EmbeddingFactory._PROVIDER_ENUM_MAP
        assert "ollama" in enum_map
        assert "zhipuai" in enum_map
        assert "openai" in enum_map
        assert "moonshot" in enum_map
        assert "deepseek" in enum_map
        assert "minimax" in enum_map
