# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：AI提供商抽象基类和类型定义
内部逻辑：定义AI提供商工厂的统一接口和类型枚举
设计模式：抽象工厂模式（Abstract Factory Pattern）
设计原则：开闭原则、依赖倒置原则
"""

from abc import ABC, abstractmethod
from typing import Any
from enum import Enum


class AIProviderType(Enum):
    """
    类级注释：AI 提供商类型枚举
    属性：定义所有支持的 AI 提供商
    """
    # Ollama（本地模型）
    OLLAMA = "ollama"
    # 智谱 AI
    ZHIPUAI = "zhipuai"
    # MiniMax
    MINIMAX = "minimax"
    # 月之暗面
    MOONSHOT = "moonshot"
    # OpenAI
    OPENAI = "openai"
    # DeepSeek
    DEEPSEEK = "deepseek"


class AIComponentType(Enum):
    """
    类级注释：AI 组件类型枚举
    属性：定义可创建的 AI 组件类型
    """
    # 大语言模型
    LLM = "llm"
    # 嵌入模型
    EMBEDDING = "embedding"


class AIProviderFactory(ABC):
    """
    类级注释：AI 提供商抽象工厂
    内部逻辑：定义创建 AI 组件的统一接口
    设计模式：抽象工厂模式 - 抽象工厂接口
    职责：
        1. 定义创建LLM的接口
        2. 定义创建Embedding的接口
        3. 提供组件支持检查
    """

    # 内部变量：提供商类型
    provider_type: AIProviderType = AIProviderType.OLLAMA

    @abstractmethod
    def create_llm(self, config: 'AIProviderConfig') -> Any:
        """
        函数级注释：创建大语言模型实例
        参数：
            config - 提供商配置
        返回值：LLM 实例
        """
        pass

    @abstractmethod
    def create_embeddings(self, config: 'AIProviderConfig') -> Any:
        """
        函数级注释：创建嵌入模型实例
        参数：
            config - 提供商配置
        返回值：Embeddings 实例
        """
        pass

    def supports_component(self, component_type: AIComponentType) -> bool:
        """
        函数级注释：检查是否支持指定组件
        参数：
            component_type - 组件类型
        返回值：是否支持
        """
        return True  # 默认支持所有组件


# 内部逻辑：导入模板方法基类
from app.core.ai_provider.base_factory import BaseAIProviderFactory

# 内部变量：导出所有公共接口
__all__ = [
    'AIProviderType',
    'AIComponentType',
    'AIProviderFactory',
    'BaseAIProviderFactory',
]
