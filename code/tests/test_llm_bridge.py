# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：llm_bridge模块完整测试集
内部逻辑：针对app/core/bridges/llm_bridge.py编写全面测试
设计模式：桥接模式测试、抽象层测试、工厂测试
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, Any

# ============================================================================
# 测试 app.core.bridges.llm_bridge 模块 (覆盖率 0%)
# ============================================================================
from app.core.bridges.llm_bridge import (
    MessageRole,
    Message,
    LLMConfig,
    LLMResponse,
    LLMImplementation,
    OllamaImplementation,
    ZhipuAIImplementation,
    LLMAbstraction,
    LLMBridgeFactory
)


# ============================================================================
# 测试 MessageRole 枚举
# ============================================================================
class TestMessageRole:
    """类级注释：消息角色枚举测试"""

    def test_enum_values(self):
        """函数级注释：验证所有枚举值"""
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.SYSTEM.value == "system"
        assert MessageRole.TOOL.value == "tool"


# ============================================================================
# 测试 Message 数据类
# ============================================================================
class TestMessage:
    """类级注释：消息数据类测试"""

    def test_init_minimal(self):
        """函数级注释：测试最小初始化"""
        msg = Message(role=MessageRole.USER, content="Hello")
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello"
        assert msg.tool_calls == []
        assert msg.tool_id is None
        assert msg.metadata == {}

    def test_init_full(self):
        """函数级注释：测试完整初始化"""
        msg = Message(
            role=MessageRole.ASSISTANT,
            content="Response",
            tool_calls=[{"name": "search"}],
            tool_id="call_123",
            metadata={"key": "value"}
        )
        assert msg.tool_calls == [{"name": "search"}]
        assert msg.tool_id == "call_123"
        assert msg.metadata == {"key": "value"}

    def test_to_dict_minimal(self):
        """函数级注释：测试转换为字典（最小）"""
        msg = Message(role=MessageRole.USER, content="Hello")
        result = msg.to_dict()
        assert result == {"role": "user", "content": "Hello"}

    def test_to_dict_with_tool_calls(self):
        """函数级注释：测试带工具调用的转换"""
        msg = Message(
            role=MessageRole.ASSISTANT,
            content="Response",
            tool_calls=[{"name": "search"}]
        )
        result = msg.to_dict()
        assert "tool_calls" in result
        assert result["tool_calls"] == [{"name": "search"}]

    def test_to_dict_with_tool_id(self):
        """函数级注释：测试带工具ID的转换"""
        msg = Message(
            role=MessageRole.TOOL,
            content="Result",
            tool_id="call_123"
        )
        result = msg.to_dict()
        assert "tool_call_id" in result
        assert result["tool_call_id"] == "call_123"

    def test_from_dict(self):
        """函数级注释：测试从字典创建"""
        data = {
            "role": "user",
            "content": "Hello",
            "tool_calls": [{"name": "search"}],
            "tool_call_id": "call_123",
            "metadata": {"key": "value"}
        }
        msg = Message.from_dict(data)
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello"
        assert msg.tool_calls == [{"name": "search"}]
        assert msg.tool_id == "call_123"
        assert msg.metadata == {"key": "value"}

    def test_from_dict_minimal(self):
        """函数级注释：测试从最小字典创建"""
        data = {"role": "user", "content": "Hello"}
        msg = Message.from_dict(data)
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello"
        assert msg.tool_calls == []
        assert msg.tool_id is None

    def test_from_dict_with_metadata(self):
        """函数级注释：测试带元数据的字典创建"""
        data = {
            "role": "user",
            "content": "Hello",
            "metadata": {"key": "value"}
        }
        msg = Message.from_dict(data)
        assert msg.metadata == {"key": "value"}


# ============================================================================
# 测试 LLMConfig 数据类
# ============================================================================
class TestLLMConfig:
    """类级注释：LLM配置数据类测试"""

    def test_init_defaults(self):
        """函数级注释：测试默认初始化值"""
        config = LLMConfig()
        assert config.temperature == 0.7
        assert config.max_tokens == 2000
        assert config.top_p == 0.9
        assert config.top_k == 40
        assert config.frequency_penalty == 0.0
        assert config.presence_penalty == 0.0
        assert config.stop == []
        assert config.stream is False

    def test_init_custom(self):
        """函数级注释：测试自定义初始化值"""
        config = LLMConfig(
            temperature=0.5,
            max_tokens=1000,
            top_p=0.8,
            top_k=30,
            frequency_penalty=0.5,
            presence_penalty=0.3,
            stop=["</END>"],
            stream=True
        )
        assert config.temperature == 0.5
        assert config.max_tokens == 1000
        assert config.stream is True


# ============================================================================
# 测试 LLMResponse 数据类
# ============================================================================
class TestLLMResponse:
    """类级注释：LLM响应数据类测试"""

    def test_init_minimal(self):
        """函数级注释：测试最小初始化"""
        response = LLMResponse(content="Hello")
        assert response.content == "Hello"
        assert response.usage == {}
        assert response.model == ""
        assert response.finish_reason == ""
        assert response.tool_calls == []
        assert response.metadata == {}

    def test_init_full(self):
        """函数级注释：测试完整初始化"""
        response = LLMResponse(
            content="Hello",
            usage={"prompt_tokens": 10, "completion_tokens": 5},
            model="qwen2",
            finish_reason="stop",
            tool_calls=[{"name": "search"}],
            metadata={"provider": "ollama"}
        )
        assert response.usage["prompt_tokens"] == 10
        assert response.model == "qwen2"
        assert response.finish_reason == "stop"


# ============================================================================
# 测试 LLMImplementation 抽象类
# ============================================================================
class TestLLMImplementation:
    """类级注释：LLM实现抽象类测试"""

    def test_cannot_instantiate(self):
        """函数级注释：测试不能直接实例化"""
        with pytest.raises(TypeError):
            LLMImplementation()


# ============================================================================
# 测试 OllamaImplementation
# ============================================================================
class TestOllamaImplementation:
    """类级注释：Ollama实现测试"""

    def test_init(self):
        """函数级注释：测试初始化"""
        impl = OllamaImplementation()
        assert impl._base_url == "http://localhost:11434"
        assert impl._model == "qwen2"

    def test_init_with_params(self):
        """函数级注释：测试带参数初始化"""
        impl = OllamaImplementation(base_url="http://other:11434", model="llama2")
        assert impl._base_url == "http://other:11434"
        assert impl._model == "llama2"

    def test_provider_name(self):
        """函数级注释：测试提供商名称"""
        impl = OllamaImplementation()
        assert impl.provider_name == "ollama"

    @pytest.mark.asyncio
    async def test_generate_success(self):
        """函数级注释：测试成功生成"""
        # Mock ollama.AsyncClient
        mock_client = AsyncMock()
        mock_response = {
            "message": {"content": "Generated response"}
        }
        mock_client.chat = AsyncMock(return_value=mock_response)

        with patch('ollama.AsyncClient', return_value=mock_client):
            impl = OllamaImplementation()
            messages = [Message(role=MessageRole.USER, content="Hello")]
            config = LLMConfig()

            response = await impl.generate(messages, config)

            assert response.content == "Generated response"
            assert response.model == "qwen2"
            assert response.metadata["provider"] == "ollama"

    @pytest.mark.asyncio
    async def test_generate_failure(self):
        """函数级注释：测试生成失败"""
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(side_effect=Exception("Connection error"))

        with patch('ollama.AsyncClient', return_value=mock_client):
            impl = OllamaImplementation()
            messages = [Message(role=MessageRole.USER, content="Hello")]
            config = LLMConfig()

            with pytest.raises(Exception, match="Connection error"):
                await impl.generate(messages, config)

    @pytest.mark.asyncio
    async def test_stream_generate_success(self):
        """函数级注释：测试流式生成成功"""
        async def mock_stream():
            yield {"message": {"content": "Hello"}}
            yield {"message": {"content": " World"}}
            yield {"message": {}}  # 空内容

        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(return_value=mock_stream())

        with patch('ollama.AsyncClient', return_value=mock_client):
            impl = OllamaImplementation()
            messages = [Message(role=MessageRole.USER, content="Hello")]
            config = LLMConfig()

            chunks = []
            async for chunk in impl.stream_generate(messages, config):
                chunks.append(chunk)

            assert chunks == ["Hello", " World"]

    @pytest.mark.asyncio
    async def test_stream_generate_failure(self):
        """函数级注释：测试流式生成失败"""
        async def mock_stream_fail():
            raise Exception("Stream error")
            yield  # 使它成为异步生成器

        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(return_value=mock_stream_fail())

        with patch('ollama.AsyncClient', return_value=mock_client):
            impl = OllamaImplementation()
            messages = [Message(role=MessageRole.USER, content="Hello")]
            config = LLMConfig()

            with pytest.raises(Exception, match="Stream error"):
                async for _ in impl.stream_generate(messages, config):
                    pass

    def test_count_tokens(self):
        """函数级注释：测试计算tokens"""
        impl = OllamaImplementation()
        # 简化版：字符数/2
        count = asyncio.run(impl.count_tokens("Hello World"))
        assert count == 5  # 10字符 / 2

    def test_supports_tools(self):
        """函数级注释：测试工具支持"""
        impl = OllamaImplementation()
        assert impl.supports_tools() is False


# ============================================================================
# 测试 ZhipuAIImplementation
# ============================================================================
class TestZhipuAIImplementation:
    """类级注释：智谱AI实现测试"""

    def test_init(self):
        """函数级注释：测试初始化"""
        impl = ZhipuAIImplementation(api_key="test_key")
        assert impl._api_key == "test_key"
        assert impl._model == "glm-4-flash"

    def test_init_with_params(self):
        """函数级注释：测试带参数初始化"""
        impl = ZhipuAIImplementation(api_key="key", model="glm-4")
        assert impl._model == "glm-4"

    def test_provider_name(self):
        """函数级注释：测试提供商名称"""
        impl = ZhipuAIImplementation(api_key="key")
        assert impl.provider_name == "zhipuai"

    @pytest.mark.asyncio
    async def test_generate_success(self):
        """函数级注释：测试成功生成"""
        # Mock 响应
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "智谱AI回复"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch('zhipuai.ZhipuAI', return_value=mock_client):
            impl = ZhipuAIImplementation(api_key="test_key")
            messages = [Message(role=MessageRole.USER, content="你好")]
            config = LLMConfig()

            response = await impl.generate(messages, config)

            assert response.content == "智谱AI回复"
            assert response.usage["prompt_tokens"] == 10
            assert response.usage["total_tokens"] == 15
            assert response.model == "glm-4-flash"
            assert response.finish_reason == "stop"
            assert response.metadata["provider"] == "zhipuai"

    @pytest.mark.asyncio
    async def test_generate_failure(self):
        """函数级注释：测试生成失败"""
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=Exception("API Error")
        )

        with patch('zhipuai.ZhipuAI', return_value=mock_client):
            impl = ZhipuAIImplementation(api_key="test_key")
            messages = [Message(role=MessageRole.USER, content="你好")]
            config = LLMConfig()

            with pytest.raises(Exception, match="API Error"):
                await impl.generate(messages, config)

    @pytest.mark.asyncio
    async def test_stream_generate_success(self):
        """函数级注释：测试流式生成成功"""
        # 创建流式响应
        async def mock_stream():
            chunks = [
                MagicMock(choices=[MagicMock(delta=MagicMock(content="你"))]),
                MagicMock(choices=[MagicMock(delta=MagicMock(content="好"))]),
                MagicMock(choices=[MagicMock(delta=MagicMock(content=""))]),
            ]
            for chunk in chunks:
                yield chunk

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_stream())

        with patch('zhipuai.ZhipuAI', return_value=mock_client):
            impl = ZhipuAIImplementation(api_key="test_key")
            messages = [Message(role=MessageRole.USER, content="你好")]
            config = LLMConfig()

            chunks = []
            async for chunk in impl.stream_generate(messages, config):
                chunks.append(chunk)

            assert chunks == ["你", "好"]

    def test_count_tokens(self):
        """函数级注释：测试计算tokens"""
        impl = ZhipuAIImplementation(api_key="key")
        count = asyncio.run(impl.count_tokens("你好世界"))
        assert count == 2  # 4字符 / 2

    def test_supports_tools(self):
        """函数级注释：测试工具支持"""
        impl = ZhipuAIImplementation(api_key="key")
        assert impl.supports_tools() is True


# ============================================================================
# 测试 LLMAbstraction
# ============================================================================
class TestLLMAbstraction:
    """类级注释：LLM抽象层测试"""

    def test_init(self):
        """函数级注释：测试初始化"""
        impl = OllamaImplementation()
        abstraction = LLMAbstraction(impl)
        assert abstraction._implementation is impl
        assert isinstance(abstraction._default_config, LLMConfig)

    def test_init_with_config(self):
        """函数级注释：测试带配置初始化"""
        impl = OllamaImplementation()
        config = LLMConfig(temperature=0.5)
        abstraction = LLMAbstraction(impl, config)
        assert abstraction._default_config.temperature == 0.5

    def test_implementation_property(self):
        """函数级注释：测试实现属性"""
        impl = OllamaImplementation()
        abstraction = LLMAbstraction(impl)
        assert abstraction.implementation is impl

    def test_set_implementation(self):
        """函数级注释：测试切换实现"""
        impl1 = OllamaImplementation()
        impl2 = ZhipuAIImplementation(api_key="key")
        abstraction = LLMAbstraction(impl1)

        abstraction.set_implementation(impl2)

        assert abstraction._implementation is impl2

    @pytest.mark.asyncio
    async def test_chat_with_messages(self):
        """函数级注释：测试聊天（Message对象）"""
        impl = OllamaImplementation()
        abstraction = LLMAbstraction(impl)

        # Mock generate方法
        async def mock_generate(messages, config):
            return LLMResponse(content="Response", model="qwen2")

        impl.generate = mock_generate

        messages = [Message(role=MessageRole.USER, content="Hello")]
        response = await abstraction.chat(messages)

        assert response.content == "Response"

    @pytest.mark.asyncio
    async def test_chat_with_dict_messages(self):
        """函数级注释：测试聊天（字典消息）"""
        impl = OllamaImplementation()
        abstraction = LLMAbstraction(impl)

        async def mock_generate(messages, config):
            return LLMResponse(content="Response", model="qwen2")

        impl.generate = mock_generate

        messages = [{"role": "user", "content": "Hello"}]
        response = await abstraction.chat(messages)

        assert response.content == "Response"

    @pytest.mark.asyncio
    async def test_chat_with_config(self):
        """函数级注释：测试带配置的聊天"""
        impl = OllamaImplementation()
        abstraction = LLMAbstraction(impl)

        async def mock_generate(messages, config):
            return LLMResponse(
                content="Response",
                model="qwen2"
            )

        impl.generate = mock_generate

        messages = [Message(role=MessageRole.USER, content="Hello")]
        config = LLMConfig(temperature=0.5)
        response = await abstraction.chat(messages, config)

        assert response.content == "Response"

    @pytest.mark.asyncio
    async def test_stream_chat(self):
        """函数级注释：测试流式聊天"""
        impl = OllamaImplementation()

        async def mock_stream(messages, config):
            yield "Hello"
            yield " World"

        impl.stream_generate = mock_stream
        abstraction = LLMAbstraction(impl)

        messages = [Message(role=MessageRole.USER, content="Hello")]
        chunks = []
        async for chunk in abstraction.stream_chat(messages):
            chunks.append(chunk)

        assert chunks == ["Hello", " World"]

    @pytest.mark.asyncio
    async def test_stream_chat_with_dict_messages(self):
        """函数级注释：测试流式聊天（字典消息）"""
        impl = OllamaImplementation()

        async def mock_stream(messages, config):
            yield "Response"

        impl.stream_generate = mock_stream
        abstraction = LLMAbstraction(impl)

        messages = [{"role": "user", "content": "Hello"}]
        chunks = []
        async for chunk in abstraction.stream_chat(messages):
            chunks.append(chunk)

        assert chunks == ["Response"]

    def test_count_tokens(self):
        """函数级注释：测试计算tokens"""
        impl = OllamaImplementation()
        abstraction = LLMAbstraction(impl)
        count = abstraction.count_tokens("Hello World")
        assert count == 5  # 10字符 / 2


# ============================================================================
# 测试 LLMBridgeFactory
# ============================================================================
class TestLLMBridgeFactory:
    """类级注释：LLM桥接工厂测试"""

    def test_create_ollama_default(self):
        """函数级注释：测试创建默认Ollama"""
        abstraction = LLMBridgeFactory.create_ollama()
        assert isinstance(abstraction, LLMAbstraction)
        assert isinstance(abstraction._implementation, OllamaImplementation)
        assert abstraction._implementation._model == "qwen2"

    def test_create_ollama_with_params(self):
        """函数级注释：测试创建带参数的Ollama"""
        abstraction = LLMBridgeFactory.create_ollama(
            base_url="http://other:11434",
            model="llama2"
        )
        impl = abstraction._implementation
        assert impl._base_url == "http://other:11434"
        assert impl._model == "llama2"

    def test_create_ollama_with_config(self):
        """函数级注释：测试创建带配置的Ollama"""
        config = LLMConfig(temperature=0.3)
        abstraction = LLMBridgeFactory.create_ollama(config=config)
        assert abstraction._default_config.temperature == 0.3

    def test_create_zhipuai_default(self):
        """函数级注释：测试创建默认智谱AI"""
        abstraction = LLMBridgeFactory.create_zhipuai(api_key="test_key")
        assert isinstance(abstraction, LLMAbstraction)
        assert isinstance(abstraction._implementation, ZhipuAIImplementation)
        assert abstraction._implementation._model == "glm-4-flash"

    def test_create_zhipuai_with_params(self):
        """函数级注释：测试创建带参数的智谱AI"""
        abstraction = LLMBridgeFactory.create_zhipuai(
            api_key="test_key",
            model="glm-4"
        )
        impl = abstraction._implementation
        assert impl._model == "glm-4"

    def test_create_zhipuai_with_config(self):
        """函数级注释：测试创建带配置的智谱AI"""
        config = LLMConfig(max_tokens=500)
        abstraction = LLMBridgeFactory.create_zhipuai(
            api_key="test_key",
            config=config
        )
        assert abstraction._default_config.max_tokens == 500

    def test_create_from_config_ollama(self):
        """函数级注释：测试从配置创建Ollama"""
        config = {
            "provider": "ollama",
            "base_url": "http://localhost:11434",
            "model": "qwen2",
            "temperature": 0.5
        }
        abstraction = LLMBridgeFactory.create_from_config(config)
        assert isinstance(abstraction._implementation, OllamaImplementation)
        assert abstraction._default_config.temperature == 0.5

    def test_create_from_config_zhipuai(self):
        """函数级注释：测试从配置创建智谱AI"""
        config = {
            "provider": "zhipuai",
            "api_key": "test_key",
            "model": "glm-4",
            "max_tokens": 1000
        }
        abstraction = LLMBridgeFactory.create_from_config(config)
        assert isinstance(abstraction._implementation, ZhipuAIImplementation)
        assert abstraction._default_config.max_tokens == 1000

    def test_create_from_config_default_provider(self):
        """函数级注释：测试从配置创建（默认提供商）"""
        config = {
            "model": "qwen2"
        }
        abstraction = LLMBridgeFactory.create_from_config(config)
        assert isinstance(abstraction._implementation, OllamaImplementation)

    def test_create_from_config_invalid_provider(self):
        """函数级注释：测试无效提供商"""
        config = {"provider": "invalid"}
        with pytest.raises(ValueError, match="不支持的提供商"):
            LLMBridgeFactory.create_from_config(config)

    def test_create_from_config_with_llm_config_params(self):
        """函数级注释：测试从配置创建（包含LLMConfig参数）"""
        config = {
            "provider": "ollama",
            "temperature": 0.1,
            "max_tokens": 500,
            "top_p": 0.8,
            "top_k": 20,
            "frequency_penalty": 0.5,
            "presence_penalty": 0.3,
            "stream": True
        }
        abstraction = LLMBridgeFactory.create_from_config(config)
        assert abstraction._default_config.temperature == 0.1
        assert abstraction._default_config.max_tokens == 500
        assert abstraction._default_config.stream is True


# ============================================================================
# 测试集成场景
# ============================================================================
class TestLLMBridgeIntegration:
    """类级注释：桥接模式集成场景测试"""

    @pytest.mark.asyncio
    async def test_bridge_pattern_switching(self):
        """函数级注释：测试桥接模式切换提供商"""
        # 创建Ollama抽象
        ollama_impl = OllamaImplementation()
        abstraction = LLMAbstraction(ollama_impl)

        # Mock实现
        async def mock_ollama(messages, config):
            return LLMResponse(content="Ollama response", model="qwen2")

        ollama_impl.generate = mock_ollama

        response1 = await abstraction.chat([Message(role=MessageRole.USER, content="Hello")])
        assert response1.content == "Ollama response"

        # 切换到智谱AI
        zhipuai_impl = ZhipuAIImplementation(api_key="key")

        async def mock_zhipuai(messages, config):
            return LLMResponse(content="ZhipuAI response", model="glm-4")

        zhipuai_impl.generate = mock_zhipuai
        abstraction.set_implementation(zhipuai_impl)

        response2 = await abstraction.chat([Message(role=MessageRole.USER, content="Hello")])
        assert response2.content == "ZhipuAI response"

    @pytest.mark.asyncio
    async def test_factory_create_and_use(self):
        """函数级注释：测试工厂创建和使用"""
        # 使用工厂创建
        abstraction = LLMBridgeFactory.create_ollama()

        # Mock实现
        async def mock_generate(messages, config):
            return LLMResponse(
                content="Factory created",
                model="qwen2",
                usage={"total_tokens": 10}
            )

        abstraction._implementation.generate = mock_generate

        response = await abstraction.chat([
            Message(role=MessageRole.USER, content="Test")
        ])

        assert response.content == "Factory created"

    @pytest.mark.asyncio
    async def test_message_format_conversion(self):
        """函数级注释：测试消息格式转换"""
        impl = OllamaImplementation()

        received_messages = []

        async def mock_generate(messages, config):
            received_messages.extend(messages)
            return LLMResponse(content="OK", model="qwen2")

        impl.generate = mock_generate
        abstraction = LLMAbstraction(impl)

        # 使用字典格式
        await abstraction.chat([
            {"role": "user", "content": "Hello"},
            Message(role=MessageRole.ASSISTANT, content="Hi"),
            {"role": "user", "content": "How are you?"}
        ])

        # 验证所有消息都转换为Message对象
        assert len(received_messages) == 3
        assert all(isinstance(m, Message) for m in received_messages)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
