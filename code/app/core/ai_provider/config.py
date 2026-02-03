# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：AI提供商配置类模块
内部逻辑：封装提供商的配置信息
设计模式：建造者模式的简化版
设计原则：封装原则、不可变对象原则
"""

from typing import Dict, Any, Optional
from loguru import logger

from app.core.ai_provider.base import AIProviderType


class AIProviderConfig:
    """
    类级注释：AI 提供商配置类
    内部逻辑：封装提供商的配置信息
    设计模式：建造者模式的简化版
    职责：
        1. 存储提供商配置
        2. 提供配置转换方法
        3. 支持字典序列化
    """

    def __init__(
        self,
        provider_type: AIProviderType,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ):
        """
        函数级注释：初始化提供商配置
        参数：
            provider_type - 提供商类型
            api_key - API 密钥
            base_url - 基础 URL
            model - 模型名称
            **kwargs - 其他配置参数
        """
        # 属性：提供商类型
        self.provider_type = provider_type
        # 属性：API 密钥
        self.api_key = api_key
        # 属性：基础 URL
        self.base_url = base_url
        # 属性：模型名称
        self.model = model
        # 属性：额外参数
        self.extra_params = kwargs

    def to_dict(self) -> Dict[str, Any]:
        """
        函数级注释：转换为字典
        返回值：配置字典
        """
        config = {
            "provider": self.provider_type.value,
        }

        if self.api_key:
            config["api_key"] = self.api_key
        if self.base_url:
            config["base_url"] = self.base_url
        if self.model:
            config["model"] = self.model

        config.update(self.extra_params)
        return config

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'AIProviderConfig':
        """
        函数级注释：从字典创建配置
        参数：
            config - 配置字典
        返回值：配置对象
        """
        provider_str = config.get("provider", "ollama")

        try:
            provider_type = AIProviderType(provider_str)
        except ValueError:
            logger.warning(f"未知的提供商: {provider_str}, 使用 ollama")
            provider_type = AIProviderType.OLLAMA

        # 内部逻辑：提取已知参数
        known_params = {"provider", "api_key", "base_url", "model"}
        extra_params = {k: v for k, v in config.items() if k not in known_params}

        return cls(
            provider_type=provider_type,
            api_key=config.get("api_key"),
            base_url=config.get("base_url"),
            model=config.get("model"),
            **extra_params
        )


# 内部变量：导出所有公共接口
__all__ = [
    'AIProviderConfig',
]
