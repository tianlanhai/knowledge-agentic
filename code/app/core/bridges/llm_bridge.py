# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：LLM 桥接模式模块
内部逻辑：将 LLM 抽象与具体提供商实现解耦
设计模式：桥接模式（Bridge Pattern）
设计原则：SOLID - 依赖倒置原则、开闭原则

状态转换图：
    LLMAbstraction (抽象)
         ↓
    LLMImplementation (实现层)
         ↓
    Ollama/ZhipuAI/OpenAI/...
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncIterator, Union
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
import asyncio


class MessageRole(Enum):
    """
    类级注释：消息角色枚举
    内部逻辑：定义聊天消息的角色类型
    """
    # 用户
    USER = "user"
    # 助手
    ASSISTANT = "assistant"
    # 系统
    SYSTEM = "system"
    # 工具
    TOOL = "tool"


@dataclass
class Message:
    """
    类级注释：消息数据类
    内部逻辑：封装聊天消息
    """
    # 属性：角色
    role: MessageRole
    # 属性：内容
    content: str
    # 属性：工具调用（可选）
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    # 属性：工具ID（可选）
    tool_id: Optional[str] = None
    # 属性：额外元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "role": self.role.value,
            "content": self.content,
        }
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls
        if self.tool_id:
            result["tool_call_id"] = self.tool_id
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """从字典创建消息"""
        return cls(
            role=MessageRole(data["role"]),
            content=data.get("content", ""),
            tool_calls=data.get("tool_calls", []),
            tool_id=data.get("tool_call_id"),
            metadata=data.get("metadata", {})
        )


@dataclass
class LLMConfig:
    """
    类级注释：LLM 配置数据类
    内部逻辑：封装 LLM 调用的配置参数
    """
    # 属性：温度（0-2）
    temperature: float = 0.7
    # 属性：最大生成 tokens
    max_tokens: int = 2000
    # 属性：Top-P 采样
    top_p: float = 0.9
    # 属性：Top-K 采样
    top_k: int = 40
    # 属性：频率惩罚
    frequency_penalty: float = 0.0
    # 属性：存在惩罚
    presence_penalty: float = 0.0
    # 属性：停止序列
    stop: List[str] = field(default_factory=list)
    # 属性：流式输出
    stream: bool = False


@dataclass
class LLMResponse:
    """
    类级注释：LLM 响应数据类
    内部逻辑：封装 LLM 的响应结果
    """
    # 属性：生成的内容
    content: str
    # 属性：使用的 tokens
    usage: Dict[str, int] = field(default_factory=dict)
    # 属性：模型名称
    model: str = ""
    # 属性：完成原因
    finish_reason: str = ""
    # 属性：工具调用
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    # 属性：额外元数据
    metadata: Dict[str, Any] = field(default_factory=dict)


class LLMImplementation(ABC):
    """
    类级注释：LLM 实现抽象接口
    内部逻辑：定义所有 LLM 提供商的统一接口
    设计模式：桥接模式 - 实现接口
    """

    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        config: LLMConfig
    ) -> LLMResponse:
        """
        函数级注释：生成文本
        参数：
            messages - 消息列表
            config - LLM 配置
        返回值：LLM 响应
        """
        pass

    @abstractmethod
    async def stream_generate(
        self,
        messages: List[Message],
        config: LLMConfig
    ) -> AsyncIterator[str]:
        """
        函数级注释：流式生成文本
        参数：
            messages - 消息列表
            config - LLM 配置
        生成值：文本块
        """
        pass

    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """
        函数级注释：计算 tokens 数量
        参数：
            text - 输入文本
        返回值：token 数量
        """
        pass

    @abstractmethod
    def supports_tools(self) -> bool:
        """
        函数级注释：检查是否支持工具调用
        返回值：是否支持
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """获取提供商名称"""
        pass


class OllamaImplementation(LLMImplementation):
    """
    类级注释：Ollama LLM 实现
    内部逻辑：实现 Ollama 的调用接口
    设计模式：桥接模式 - 具体实现
    """

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2"):
        self._base_url = base_url
        self._model = model
        logger.info(f"[OllamaImplementation] 初始化，模型: {model}")

    @property
    def provider_name(self) -> str:
        return "ollama"

    async def generate(
        self,
        messages: List[Message],
        config: LLMConfig
    ) -> LLMResponse:
        """生成文本"""
        try:
            from ollama import AsyncClient

            client = AsyncClient(host=self._base_url)
            response = await client.chat(
                model=self._model,
                messages=[m.to_dict() for m in messages],
                options={
                    "temperature": config.temperature,
                    "num_predict": config.max_tokens,
                    "top_p": config.top_p,
                    "top_k": config.top_k,
                }
            )

            return LLMResponse(
                content=response.get("message", {}).get("content", ""),
                model=self._model,
                metadata={"provider": "ollama"}
            )

        except Exception as e:
            logger.error(f"[OllamaImplementation] 生成失败: {str(e)}")
            raise

    async def stream_generate(
        self,
        messages: List[Message],
        config: LLMConfig
    ) -> AsyncIterator[str]:
        """流式生成文本"""
        try:
            from ollama import AsyncClient

            client = AsyncClient(host=self._base_url)
            stream = await client.chat(
                model=self._model,
                messages=[m.to_dict() for m in messages],
                stream=True,
                options={
                    "temperature": config.temperature,
                    "num_predict": config.max_tokens,
                    "top_p": config.top_p,
                    "top_k": config.top_k,
                }
            )

            async for chunk in stream:
                if "message" in chunk:
                    content = chunk["message"].get("content", "")
                    if content:
                        yield content

        except Exception as e:
            logger.error(f"[OllamaImplementation] 流式生成失败: {str(e)}")
            raise

    async def count_tokens(self, text: str) -> int:
        """计算 tokens（简化版）"""
        # 内部逻辑：简化估算，约等于字符数/2
        return len(text) // 2

    def supports_tools(self) -> bool:
        return False


class ZhipuAIImplementation(LLMImplementation):
    """
    类级注释：智谱AI LLM 实现
    内部逻辑：实现智谱AI的调用接口
    设计模式：桥接模式 - 具体实现
    """

    def __init__(self, api_key: str, model: str = "glm-4-flash"):
        self._api_key = api_key
        self._model = model
        logger.info(f"[ZhipuAIImplementation] 初始化，模型: {model}")

    @property
    def provider_name(self) -> str:
        return "zhipuai"

    async def generate(
        self,
        messages: List[Message],
        config: LLMConfig
    ) -> LLMResponse:
        """生成文本"""
        try:
            from zhipuai import ZhipuAI

            client = ZhipuAI(api_key=self._api_key)
            response = await client.chat.completions.create(
                model=self._model,
                messages=[m.to_dict() for m in messages],
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p,
            )

            return LLMResponse(
                content=response.choices[0].message.content,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                model=self._model,
                finish_reason=response.choices[0].finish_reason,
                metadata={"provider": "zhipuai"}
            )

        except Exception as e:
            logger.error(f"[ZhipuAIImplementation] 生成失败: {str(e)}")
            raise

    async def stream_generate(
        self,
        messages: List[Message],
        config: LLMConfig
    ) -> AsyncIterator[str]:
        """流式生成文本"""
        try:
            from zhipuai import ZhipuAI

            client = ZhipuAI(api_key=self._api_key)
            stream = await client.chat.completions.create(
                model=self._model,
                messages=[m.to_dict() for m in messages],
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"[ZhipuAIImplementation] 流式生成失败: {str(e)}")
            raise

    async def count_tokens(self, text: str) -> int:
        """计算 tokens"""
        # 内部逻辑：使用 tiktoken 或其他库
        return len(text) // 2

    def supports_tools(self) -> bool:
        return True


class LLMAbstraction:
    """
    类级注释：LLM 抽象层
    内部逻辑：封装 LLM 的使用接口，桥接到具体实现
    设计模式：桥接模式 - 抽象层
    职责：
        1. 提供统一的调用接口
        2. 处理消息格式转换
        3. 管理配置参数

    使用场景：
        - 多模型切换
        - A/B 测试
        - 备份模型
    """

    def __init__(
        self,
        implementation: LLMImplementation,
        default_config: Optional[LLMConfig] = None
    ):
        """
        函数级注释：初始化 LLM 抽象
        参数：
            implementation - LLM 实现
            default_config - 默认配置
        """
        self._implementation = implementation
        self._default_config = default_config or LLMConfig()
        logger.info(
            f"[LLMAbstraction] 初始化，提供商: {implementation.provider_name}"
        )

    @property
    def implementation(self) -> LLMImplementation:
        """获取当前实现"""
        return self._implementation

    def set_implementation(self, implementation: LLMImplementation) -> None:
        """
        函数级注释：切换实现
        参数：
            implementation - 新的 LLM 实现
        """
        old_provider = self._implementation.provider_name
        self._implementation = implementation
        new_provider = implementation.provider_name
        logger.info(f"[LLMAbstraction] 切换提供商: {old_provider} -> {new_provider}")

    async def chat(
        self,
        messages: List[Union[Message, Dict[str, str]]],
        config: Optional[LLMConfig] = None
    ) -> LLMResponse:
        """
        函数级注释：聊天对话
        参数：
            messages - 消息列表
            config - LLM 配置
        返回值：LLM 响应

        @example
        ```python
        llm = LLMAbstraction(ollama_impl)
        response = await llm.chat([
            Message(role=MessageRole.USER, content="你好")
        ])
        ```
        """
        # 内部逻辑：转换消息格式
        converted_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                converted_messages.append(Message.from_dict(msg))
            else:
                converted_messages.append(msg)

        # 内部逻辑：合并配置
        final_config = self._default_config
        if config:
            for key, value in config.__dict__.items():
                setattr(final_config, key, value)

        return await self._implementation.generate(converted_messages, final_config)

    async def stream_chat(
        self,
        messages: List[Union[Message, Dict[str, str]]],
        config: Optional[LLMConfig] = None
    ) -> AsyncIterator[str]:
        """
        函数级注释：流式聊天对话
        参数：
            messages - 消息列表
            config - LLM 配置
        生成值：文本块

        @example
        ```python
        async for chunk in llm.stream_chat(messages):
            print(chunk, end="")
        ```
        """
        converted_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                converted_messages.append(Message.from_dict(msg))
            else:
                converted_messages.append(msg)

        final_config = self._default_config
        if config:
            for key, value in config.__dict__.items():
                setattr(final_config, key, value)

        async for chunk in self._implementation.stream_generate(
            converted_messages,
            final_config
        ):
            yield chunk

    def count_tokens(self, text: str) -> int:
        """
        函数级注释：计算 tokens
        参数：
            text - 输入文本
        返回值：token 数量
        """
        import asyncio
        return asyncio.run(self._implementation.count_tokens(text))


class LLMBridgeFactory:
    """
    类级注释：LLM 桥接工厂
    内部逻辑：统一创建 LLM 实现和抽象
    设计模式：工厂模式 + 桥接模式
    职责：
        1. 创建各种 LLM 实现
        2. 创建 LLM 抽象实例
        3. 管理配置

    使用场景：
        - 统一创建入口
        - 配置管理
    """

    @staticmethod
    def create_ollama(
        base_url: str = "http://localhost:11434",
        model: str = "qwen2",
        config: Optional[LLMConfig] = None
    ) -> LLMAbstraction:
        """
        函数级注释：创建 Ollama LLM
        参数：
            base_url - Ollama 服务地址
            model - 模型名称
            config - LLM 配置
        返回值：LLM 抽象实例
        """
        implementation = OllamaImplementation(base_url, model)
        return LLMAbstraction(implementation, config)

    @staticmethod
    def create_zhipuai(
        api_key: str,
        model: str = "glm-4-flash",
        config: Optional[LLMConfig] = None
    ) -> LLMAbstraction:
        """
        函数级注释：创建智谱AI LLM
        参数：
            api_key - API 密钥
            model - 模型名称
            config - LLM 配置
        返回值：LLM 抽象实例
        """
        implementation = ZhipuAIImplementation(api_key, model)
        return LLMAbstraction(implementation, config)

    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> LLMAbstraction:
        """
        函数级注释：从配置创建 LLM
        参数：
            config - 配置字典，包含 provider 和相关参数
        返回值：LLM 抽象实例

        @example
        ```python
        llm = LLMBridgeFactory.create_from_config({
            "provider": "ollama",
            "base_url": "http://localhost:11434",
            "model": "qwen2"
        })
        ```
        """
        provider = config.get("provider", "ollama")
        llm_config = LLMConfig(**{k: v for k, v in config.items()
                               if k in LLMConfig.__dataclass_fields__})

        if provider == "ollama":
            return LLMBridgeFactory.create_ollama(
                base_url=config.get("base_url", "http://localhost:11434"),
                model=config.get("model", "qwen2"),
                config=llm_config
            )
        elif provider == "zhipuai":
            return LLMBridgeFactory.create_zhipuai(
                api_key=config.get("api_key", ""),
                model=config.get("model", "glm-4-flash"),
                config=llm_config
            )
        else:
            raise ValueError(f"不支持的提供商: {provider}")


# 内部变量：导出所有公共接口
__all__ = [
    # 数据类
    'Message',
    'MessageRole',
    'LLMConfig',
    'LLMResponse',
    # 实现
    'LLMImplementation',
    'OllamaImplementation',
    'ZhipuAIImplementation',
    # 抽象
    'LLMAbstraction',
    # 工厂
    'LLMBridgeFactory',
]
