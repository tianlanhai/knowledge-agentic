# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：桥接模式测试模块
内部逻辑：测试bridges目录下的桥接模式实现，包括EmbeddingBridge和LLMBridge
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from typing import Any, Dict, List

from app.core.bridges.embedding_bridge import (
    EmbeddingBridge,
    EmbeddingBridgeFactory
)
from app.core.bridges.llm_bridge import (
    Message,
    MessageRole,
    LLMConfig,
    LLMResponse,
    LLMImplementation,
    OllamaImplementation,
    ZhipuAIImplementation,
    LLMAbstraction,
    LLMBridgeFactory
)


# ============================================================================
# EmbeddingBridge 测试类
# ============================================================================

class TestEmbeddingBridge:
    """
    类级注释：Embedding桥接抽象类测试
    职责：测试EmbeddingBridge接口定义
    """

    def test_abstract_class_cannot_instantiate(self):
        """
        测试目的：验证不能直接实例化抽象类
        测试场景：尝试实例化EmbeddingBridge
        """
        # Arrange & Act & Assert: 尝试创建实例应该失败
        with pytest.raises(TypeError):
            EmbeddingBridge()


class TestEmbeddingBridgeFactory:
    """
    类级注释：Embedding桥接工厂测试类
    职责：测试EmbeddingBridgeFactory的注册和管理功能
    """

    def setup_method(self):
        """
        测试前准备：清理注册表
        """
        EmbeddingBridgeFactory._registry.clear()
        EmbeddingBridgeFactory._instances.clear()

    def test_register_bridge(self):
        """
        测试目的：验证注册桥接类功能
        测试场景：注册自定义桥接类
        """
        # Arrange: 创建自定义桥接类
        class CustomBridge(EmbeddingBridge):
            provider_id = "custom"
            provider_name = "Custom Provider"

            def create_embeddings(self, config: Dict[str, Any]):
                return MagicMock()

            def validate_config(self, config: Dict[str, Any]) -> bool:
                return True

            def get_default_model(self) -> str:
                return "default-model"

        # Act: 注册桥接类
        EmbeddingBridgeFactory.register(CustomBridge)

        # Assert: 验证注册成功
        assert EmbeddingBridgeFactory.is_registered("custom")
        assert "custom" in EmbeddingBridgeFactory.get_supported_providers()

    def test_register_duplicate_overwrites(self):
        """
        测试目的：验证重复注册会覆盖
        测试场景：注册相同provider_id的桥接类
        """
        # Arrange: 创建两个相同ID的桥接类
        class Bridge1(EmbeddingBridge):
            provider_id = "test"
            provider_name = "Bridge 1"

            def create_embeddings(self, config):
                return MagicMock()

            def validate_config(self, config) -> bool:
                return True

            def get_default_model(self) -> str:
                return "model1"

        class Bridge2(EmbeddingBridge):
            provider_id = "test"
            provider_name = "Bridge 2"

            def create_embeddings(self, config):
                return MagicMock()

            def validate_config(self, config) -> bool:
                return True

            def get_default_model(self) -> str:
                return "model2"

        # Act: 注册两个桥接类
        EmbeddingBridgeFactory.register(Bridge1)
        EmbeddingBridgeFactory.register(Bridge2)

        # Assert: 验证最后注册的生效
        providers = EmbeddingBridgeFactory.get_supported_providers()
        assert providers["test"] == "Bridge 2"

    def test_unregister(self):
        """
        测试目的：验证注销桥接类功能
        测试场景：注册后注销桥接类
        """
        # Arrange: 创建并注册桥接类
        class TestBridge(EmbeddingBridge):
            provider_id = "test"
            provider_name = "Test"

            def create_embeddings(self, config):
                return MagicMock()

            def validate_config(self, config) -> bool:
                return True

            def get_default_model(self) -> str:
                return "model"

        EmbeddingBridgeFactory.register(TestBridge)

        # Act: 注销桥接类
        EmbeddingBridgeFactory.unregister("test")

        # Assert: 验证已注销
        assert not EmbeddingBridgeFactory.is_registered("test")

    def test_unregister_clears_instances(self):
        """
        测试目的：验证注销时清除实例缓存
        测试场景：获取实例后注销
        """
        # Arrange: 创建并注册桥接类，获取实例
        class TestBridge(EmbeddingBridge):
            provider_id = "test"
            provider_name = "Test"

            def create_embeddings(self, config):
                return MagicMock()

            def validate_config(self, config) -> bool:
                return True

            def get_default_model(self) -> str:
                return "model"

        EmbeddingBridgeFactory.register(TestBridge)
        EmbeddingBridgeFactory.get_bridge("test")  # 创建实例

        # Act: 注销桥接类
        EmbeddingBridgeFactory.unregister("test")

        # Assert: 验证实例已清除
        assert "test" not in EmbeddingBridgeFactory._instances

    def test_get_bridge(self):
        """
        测试目的：验证获取桥接实例功能
        测试场景：注册并获取桥接实例
        """
        # Arrange: 创建并注册桥接类
        class TestBridge(EmbeddingBridge):
            provider_id = "test"
            provider_name = "Test Provider"

            def create_embeddings(self, config):
                return MagicMock()

            def validate_config(self, config) -> bool:
                return True

            def get_default_model(self) -> str:
                return "test-model"

        EmbeddingBridgeFactory.register(TestBridge)

        # Act: 获取桥接实例
        bridge = EmbeddingBridgeFactory.get_bridge("test")

        # Assert: 验证实例类型
        assert isinstance(bridge, TestBridge)

    def test_get_bridge_not_registered(self):
        """
        测试目的：验证获取未注册的桥接抛出异常
        测试场景：尝试获取不存在的桥接
        """
        # Arrange: 工厂为空

        # Act & Assert: 尝试获取不存在的桥接应该抛出异常
        with pytest.raises(ValueError, match="未注册的Embedding提供商"):
            EmbeddingBridgeFactory.get_bridge("nonexistent")

    def test_get_bridge_caches_instances(self):
        """
        测试目的：验证桥接实例被缓存
        测试场景：多次获取返回同一实例
        """
        # Arrange: 创建并注册桥接类
        class TestBridge(EmbeddingBridge):
            provider_id = "test"
            provider_name = "Test"

            def create_embeddings(self, config):
                return MagicMock()

            def validate_config(self, config) -> bool:
                return True

            def get_default_model(self) -> str:
                return "model"

        EmbeddingBridgeFactory.register(TestBridge)

        # Act: 多次获取实例
        bridge1 = EmbeddingBridgeFactory.get_bridge("test")
        bridge2 = EmbeddingBridgeFactory.get_bridge("test")

        # Assert: 验证是同一个实例
        assert bridge1 is bridge2

    def test_create_embeddings(self):
        """
        测试目的：验证创建Embedding实例功能
        测试场景：通过工厂创建Embedding
        """
        # Arrange: 创建并注册桥接类
        mock_embeddings = MagicMock()

        class TestBridge(EmbeddingBridge):
            provider_id = "test"
            provider_name = "Test"

            def create_embeddings(self, config):
                return mock_embeddings

            def validate_config(self, config) -> bool:
                return True

            def get_default_model(self) -> str:
                return "model"

        EmbeddingBridgeFactory.register(TestBridge)

        # Act: 创建Embedding
        result = EmbeddingBridgeFactory.create_embeddings("test", {"model": "test"})

        # Assert: 验证返回的实例
        assert result is mock_embeddings

    def test_validate_provider_config(self):
        """
        测试目的：验证验证提供商配置功能
        测试场景：验证配置有效性
        """
        # Arrange: 创建并注册桥接类
        class TestBridge(EmbeddingBridge):
            provider_id = "test"
            provider_name = "Test"

            def create_embeddings(self, config):
                return MagicMock()

            def validate_config(self, config) -> bool:
                return bool(config.get("api_key"))

            def get_default_model(self) -> str:
                return "model"

        EmbeddingBridgeFactory.register(TestBridge)

        # Act: 验证配置
        valid = EmbeddingBridgeFactory.validate_provider_config(
            "test", {"api_key": "key123"}
        )
        invalid = EmbeddingBridgeFactory.validate_provider_config("test", {})

        # Assert: 验证结果
        assert valid is True
        assert invalid is False

    def test_get_supported_providers(self):
        """
        测试目的：验证获取所有支持的提供商功能
        测试场景：获取所有已注册的提供商
        """
        # Arrange: 注册多个桥接类
        class Bridge1(EmbeddingBridge):
            provider_id = "provider1"
            provider_name = "Provider One"

            def create_embeddings(self, config):
                return MagicMock()

            def validate_config(self, config) -> bool:
                return True

            def get_default_model(self) -> str:
                return "model1"

        class Bridge2(EmbeddingBridge):
            provider_id = "provider2"
            provider_name = "Provider Two"

            def create_embeddings(self, config):
                return MagicMock()

            def validate_config(self, config) -> bool:
                return True

            def get_default_model(self) -> str:
                return "model2"

        EmbeddingBridgeFactory.register(Bridge1)
        EmbeddingBridgeFactory.register(Bridge2)

        # Act: 获取支持的提供商
        providers = EmbeddingBridgeFactory.get_supported_providers()

        # Assert: 验证提供商列表
        assert len(providers) == 2
        assert providers["provider1"] == "Provider One"
        assert providers["provider2"] == "Provider Two"

    def test_get_provider_models(self):
        """
        测试目的：验证获取提供商支持的模型列表功能
        测试场景：获取指定提供商的模型列表
        """
        # Arrange: 创建并注册桥接类
        class TestBridge(EmbeddingBridge):
            provider_id = "test"
            provider_name = "Test"

            def create_embeddings(self, config):
                return MagicMock()

            def validate_config(self, config) -> bool:
                return True

            def get_default_model(self) -> str:
                return "default-model"

            def get_supported_models(self):
                return ["model1", "model2", "model3"]

        EmbeddingBridgeFactory.register(TestBridge)

        # Act: 获取模型列表
        models = EmbeddingBridgeFactory.get_provider_models("test")

        # Assert: 验证模型列表
        assert len(models) == 3
        assert "model1" in models

    def test_is_registered(self):
        """
        测试目的：验证检查提供商是否已注册功能
        """
        # Arrange: 创建并注册桥接类
        class TestBridge(EmbeddingBridge):
            provider_id = "test"
            provider_name = "Test"

            def create_embeddings(self, config):
                return MagicMock()

            def validate_config(self, config) -> bool:
                return True

            def get_default_model(self) -> str:
                return "model"

        EmbeddingBridgeFactory.register(TestBridge)

        # Act & Assert: 验证已注册和未注册的提供商
        assert EmbeddingBridgeFactory.is_registered("test") is True
        assert EmbeddingBridgeFactory.is_registered("nonexistent") is False

    def test_clear_instances(self):
        """
        测试目的：验证清除所有实例缓存功能
        测试场景：清除前后的实例状态
        """
        # Arrange: 创建并注册桥接类，获取实例
        class TestBridge(EmbeddingBridge):
            provider_id = "test"
            provider_name = "Test"

            def create_embeddings(self, config):
                return MagicMock()

            def validate_config(self, config) -> bool:
                return True

            def get_default_model(self) -> str:
                return "model"

        EmbeddingBridgeFactory.register(TestBridge)
        EmbeddingBridgeFactory.get_bridge("test")

        # Act: 清除实例缓存
        EmbeddingBridgeFactory.clear_instances()

        # Assert: 验证实例已清除
        assert len(EmbeddingBridgeFactory._instances) == 0


# ============================================================================
# LLM Bridge 测试类
# ============================================================================

class TestMessageRole:
    """
    类级注释：消息角色枚举测试类
    """

    def test_user_enum_value(self):
        """验证USER枚举值"""
        assert MessageRole.USER.value == "user"

    def test_assistant_enum_value(self):
        """验证ASSISTANT枚举值"""
        assert MessageRole.ASSISTANT.value == "assistant"

    def test_system_enum_value(self):
        """验证SYSTEM枚举值"""
        assert MessageRole.SYSTEM.value == "system"

    def test_tool_enum_value(self):
        """验证TOOL枚举值"""
        assert MessageRole.TOOL.value == "tool"


class TestMessage:
    """
    类级注释：消息数据类测试类
    """

    def test_creation(self):
        """验证创建消息"""
        message = Message(
            role=MessageRole.USER,
            content="Hello"
        )
        assert message.role == MessageRole.USER
        assert message.content == "Hello"
        assert message.tool_calls == []
        assert message.metadata == {}

    def test_to_dict(self):
        """验证转换为字典"""
        message = Message(
            role=MessageRole.USER,
            content="Test",
            tool_calls=[{"name": "tool"}],
            tool_id="call_123"
        )
        result = message.to_dict()
        assert result["role"] == "user"
        assert result["content"] == "Test"
        assert result["tool_calls"] == [{"name": "tool"}]
        assert result["tool_call_id"] == "call_123"

    def test_from_dict(self):
        """验证从字典创建"""
        data = {
            "role": "user",
            "content": "Test",
            "tool_calls": [{"name": "tool"}],
            "tool_call_id": "call_123",
            "metadata": {"key": "value"}
        }
        message = Message.from_dict(data)
        assert message.role == MessageRole.USER
        assert message.content == "Test"
        assert message.tool_calls == [{"name": "tool"}]
        assert message.tool_id == "call_123"
        assert message.metadata == {"key": "value"}


class TestLLMConfig:
    """
    类级注释：LLM配置数据类测试类
    """

    def test_default_values(self):
        """验证默认配置值"""
        config = LLMConfig()
        assert config.temperature == 0.7
        assert config.max_tokens == 2000
        assert config.top_p == 0.9
        assert config.top_k == 40
        assert config.frequency_penalty == 0.0
        assert config.presence_penalty == 0.0
        assert config.stop == []
        assert config.stream is False

    def test_custom_values(self):
        """验证自定义配置值"""
        config = LLMConfig(
            temperature=0.5,
            max_tokens=1000,
            top_p=0.8,
            stream=True
        )
        assert config.temperature == 0.5
        assert config.max_tokens == 1000
        assert config.top_p == 0.8
        assert config.stream is True


class TestLLMResponse:
    """
    类级注释：LLM响应数据类测试类
    """

    def test_creation(self):
        """验证创建响应"""
        response = LLMResponse(content="Generated text")
        assert response.content == "Generated text"
        assert response.usage == {}
        assert response.model == ""
        assert response.finish_reason == ""

    def test_with_all_fields(self):
        """验证完整字段"""
        response = LLMResponse(
            content="Text",
            usage={"prompt_tokens": 10, "completion_tokens": 20},
            model="gpt-4",
            finish_reason="stop",
            metadata={"provider": "openai"}
        )
        assert response.content == "Text"
        assert response.usage["prompt_tokens"] == 10
        assert response.model == "gpt-4"
        assert response.finish_reason == "stop"
        assert response.metadata["provider"] == "openai"


class TestLLMImplementation:
    """
    类级注释：LLM实现抽象类测试类
    """

    def test_abstract_class_cannot_instantiate(self):
        """验证不能直接实例化抽象类"""
        with pytest.raises(TypeError):
            LLMImplementation()


class TestOllamaImplementation:
    """
    类级注释：Ollama LLM实现测试类
    """

    def test_initialization(self):
        """验证初始化"""
        impl = OllamaImplementation(
            base_url="http://localhost:11434",
            model="qwen2"
        )
        assert impl._base_url == "http://localhost:11434"
        assert impl._model == "qwen2"

    def test_provider_name(self):
        """验证提供商名称"""
        impl = OllamaImplementation()
        assert impl.provider_name == "ollama"

    @pytest.mark.asyncio
    async def test_count_tokens(self):
        """验证计算tokens（简化版）"""
        impl = OllamaImplementation()
        count = await impl.count_tokens("Hello world")
        # 简化版约为字符数/2
        assert count == 5  # "Hello world" 11字符 -> 5

    def test_supports_tools(self):
        """验证工具支持"""
        impl = OllamaImplementation()
        assert impl.supports_tools() is False


class TestZhipuAIImplementation:
    """
    类级注释：智谱AI LLM实现测试类
    """

    def test_initialization(self):
        """验证初始化"""
        impl = ZhipuAIImplementation(
            api_key="test_key",
            model="glm-4-flash"
        )
        assert impl._api_key == "test_key"
        assert impl._model == "glm-4-flash"

    def test_provider_name(self):
        """验证提供商名称"""
        impl = ZhipuAIImplementation(api_key="test")
        assert impl.provider_name == "zhipuai"

    @pytest.mark.asyncio
    async def test_count_tokens(self):
        """验证计算tokens"""
        impl = ZhipuAIImplementation(api_key="test")
        count = await impl.count_tokens("Hello world")
        # 简化版约为字符数/2
        assert count == 5

    def test_supports_tools(self):
        """验证工具支持"""
        impl = ZhipuAIImplementation(api_key="test")
        assert impl.supports_tools() is True


class TestLLMAbstraction:
    """
    类级注释：LLM抽象层测试类
    """

    def test_initialization(self):
        """验证初始化"""
        impl = OllamaImplementation()
        abstraction = LLMAbstraction(impl)
        assert abstraction._implementation is impl
        assert abstraction._default_config.temperature == 0.7

    def test_initialization_with_custom_config(self):
        """验证使用自定义配置初始化"""
        config = LLMConfig(temperature=0.5, max_tokens=1000)
        impl = OllamaImplementation()
        abstraction = LLMAbstraction(impl, config)
        assert abstraction._default_config.temperature == 0.5
        assert abstraction._default_config.max_tokens == 1000

    def test_implementation_property(self):
        """验证获取当前实现"""
        impl = OllamaImplementation()
        abstraction = LLMAbstraction(impl)
        assert abstraction.implementation is impl

    def test_set_implementation(self):
        """验证切换实现"""
        impl1 = OllamaImplementation()
        impl2 = ZhipuAIImplementation(api_key="test")
        abstraction = LLMAbstraction(impl1)

        abstraction.set_implementation(impl2)

        assert abstraction.implementation is impl2

    def test_count_tokens(self):
        """验证计算tokens"""
        impl = OllamaImplementation()
        abstraction = LLMAbstraction(impl)
        count = abstraction.count_tokens("Hello world")
        assert count == 5


class TestLLMBridgeFactory:
    """
    类级注释：LLM桥接工厂测试类
    """

    def test_create_ollama(self):
        """验证创建Ollama LLM"""
        llm = LLMBridgeFactory.create_ollama(
            base_url="http://localhost:11434",
            model="qwen2"
        )
        assert isinstance(llm, LLMAbstraction)
        assert llm.implementation.provider_name == "ollama"

    def test_create_ollama_with_config(self):
        """验证创建带配置的Ollama LLM"""
        config = LLMConfig(temperature=0.5)
        llm = LLMBridgeFactory.create_ollama(config=config)
        assert llm._default_config.temperature == 0.5

    def test_create_zhipuai(self):
        """验证创建智谱AI LLM"""
        llm = LLMBridgeFactory.create_zhipuai(
            api_key="test_key",
            model="glm-4-flash"
        )
        assert isinstance(llm, LLMAbstraction)
        assert llm.implementation.provider_name == "zhipuai"

    def test_create_zhipuai_with_config(self):
        """验证创建带配置的智谱AI LLM"""
        config = LLMConfig(temperature=0.3)
        llm = LLMBridgeFactory.create_zhipuai(
            api_key="test",
            config=config
        )
        assert llm._default_config.temperature == 0.3

    def test_create_from_config_ollama(self):
        """验证从配置创建Ollama LLM"""
        config = {
            "provider": "ollama",
            "base_url": "http://localhost:11434",
            "model": "qwen2",
            "temperature": 0.5
        }
        llm = LLMBridgeFactory.create_from_config(config)
        assert isinstance(llm, LLMAbstraction)
        assert llm.implementation.provider_name == "ollama"

    def test_create_from_config_zhipuai(self):
        """验证从配置创建智谱AI LLM"""
        config = {
            "provider": "zhipuai",
            "api_key": "test_key",
            "model": "glm-4-flash"
        }
        llm = LLMBridgeFactory.create_from_config(config)
        assert isinstance(llm, LLMAbstraction)
        assert llm.implementation.provider_name == "zhipuai"

    def test_create_from_config_invalid_provider(self):
        """验证从配置创建不支持的提供商抛出异常"""
        config = {"provider": "unsupported"}
        with pytest.raises(ValueError, match="不支持的提供商"):
            LLMBridgeFactory.create_from_config(config)

    def test_create_from_config_with_llm_config_fields(self):
        """验证从配置创建时LLM配置字段正确传递"""
        config = {
            "provider": "ollama",
            "model": "qwen2",
            "temperature": 0.3,
            "max_tokens": 500,
            "stream": True
        }
        llm = LLMBridgeFactory.create_from_config(config)
        # 验证配置被正确应用
        assert llm._default_config.temperature == 0.3
        assert llm._default_config.max_tokens == 500
        assert llm._default_config.stream is True


# ============================================================================
# 集成测试类
# ============================================================================

class TestBridgesIntegration:
    """
    类级注释：桥接模式集成测试类
    职责：测试桥接模式的完整流程
    """

    def test_embedding_bridge_end_to_end(self):
        """
        测试目的：验证Embedding桥接完整流程
        测试场景：注册 -> 获取 -> 创建Embedding
        """
        # Arrange: 创建自定义桥接类
        class TestEmbeddingBridge(EmbeddingBridge):
            provider_id = "test_embed"
            provider_name = "Test Embedding"

            def __init__(self):
                self.embeddings_created = 0

            def create_embeddings(self, config):
                self.embeddings_created += 1
                mock_emb = MagicMock()
                mock_emb.config = config
                return mock_emb

            def validate_config(self, config) -> bool:
                return bool(config.get("model"))

            def get_default_model(self) -> str:
                return "default-model"

        # Act: 注册并使用
        EmbeddingBridgeFactory.register(TestEmbeddingBridge)
        bridge = EmbeddingBridgeFactory.get_bridge("test_embed")
        embeddings = bridge.create_embeddings({"model": "test-model"})

        # Assert: 验证完整流程
        assert isinstance(bridge, TestEmbeddingBridge)
        assert embeddings.config["model"] == "test-model"
        assert bridge.embeddings_created == 1

        # 清理
        EmbeddingBridgeFactory._registry.clear()
        EmbeddingBridgeFactory._instances.clear()

    def test_llm_bridge_end_to_end(self):
        """
        测试目的：验证LLM桥接完整流程
        测试场景：创建 -> 配置 -> 切换实现
        """
        # Arrange: 创建两个实现
        ollama_impl = OllamaImplementation(model="qwen2")
        zhipu_impl = ZhipuAIImplementation(api_key="test", model="glm-4")

        # Act: 创建抽象并切换实现
        llm = LLMBridgeFactory.create_ollama(model="qwen2")
        original_provider = llm.implementation.provider_name

        llm.set_implementation(zhipu_impl)
        new_provider = llm.implementation.provider_name

        # Assert: 验证切换成功
        assert original_provider == "ollama"
        assert new_provider == "zhipuai"
