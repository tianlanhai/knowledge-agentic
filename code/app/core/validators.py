# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：统一的配置验证器模块
内部逻辑：提供可复用的配置验证装饰器和验证器类
设计模式：策略模式、装饰器模式
设计原则：DRY（不重复）、开闭原则（对扩展开放）
"""

from functools import wraps
from typing import Callable, Dict, Any, Optional, List, Set
from enum import Enum
from loguru import logger


class ValidationRule(str, Enum):
    """
    类级注释：验证规则枚举
    属性：
        API_KEY_REQUIRED: API密钥必填
        GROUP_ID_REQUIRED: Group ID必填
        ENDPOINT_REQUIRED: 端点地址必填
    """
    API_KEY_REQUIRED = "api_key_required"
    GROUP_ID_REQUIRED = "group_id_required"
    ENDPOINT_REQUIRED = "endpoint_required"


class ConfigValidator:
    """
    类级注释：配置验证器类
    设计模式：策略模式
    职责：提供各种配置验证策略
    """

    # 内部常量：错误消息模板
    ERROR_MESSAGES = {
        ValidationRule.API_KEY_REQUIRED: "使用{provider}需要配置API密钥",
        ValidationRule.GROUP_ID_REQUIRED: "使用{provider}需要配置Group ID",
        ValidationRule.ENDPOINT_REQUIRED: "使用{provider}需要配置端点地址",
    }

    @classmethod
    def validate_api_key(
        cls,
        api_key: Optional[str],
        provider_name: str,
        allow_empty: bool = False
    ) -> None:
        """
        函数级注释：验证 API 密钥
        内部逻辑：检查密钥是否为空 -> 为空且不允许时抛出异常
        参数：
            api_key: API 密钥
            provider_name: 提供商名称（用于错误消息）
            allow_empty: 是否允许为空（本地模型可能不需要）
        异常：ValueError - 当密钥为空且不允许时
        """
        if not allow_empty and not api_key:
            raise ValueError(
                cls.ERROR_MESSAGES[ValidationRule.API_KEY_REQUIRED].format(
                    provider=provider_name
                )
            )

    @classmethod
    def validate_group_id(
        cls,
        group_id: Optional[str],
        provider_name: str
    ) -> None:
        """
        函数级注释：验证 Group ID
        参数：
            group_id: Group ID
            provider_name: 提供商名称
        异常：ValueError - 当 Group ID 为空时
        """
        if not group_id:
            raise ValueError(
                cls.ERROR_MESSAGES[ValidationRule.GROUP_ID_REQUIRED].format(
                    provider=provider_name
                )
            )

    @classmethod
    def validate_endpoint(
        cls,
        endpoint: Optional[str],
        provider_name: str
    ) -> None:
        """
        函数级注释：验证端点地址
        参数：
            endpoint: 端点地址
            provider_name: 提供商名称
        异常：ValueError - 当端点为空时
        """
        if not endpoint:
            raise ValueError(
                cls.ERROR_MESSAGES[ValidationRule.ENDPOINT_REQUIRED].format(
                    provider=provider_name
                )
            )


def validate_config(*rules: ValidationRule, allow_empty_local: bool = True):
    """
    函数级注释：配置验证装饰器
    设计模式：装饰器模式
    内部逻辑：在函数执行前验证配置，验证失败则抛出异常

    参数：
        *rules: 要应用的验证规则列表
        allow_empty_local: 是否允许本地提供商的 API 密钥为空（默认True）

    返回值：装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, config: Dict[str, Any], *args, **kwargs):
            # 内部逻辑：获取提供商信息
            provider = config.get("provider", "unknown")

            # 内部逻辑：获取提供商显示名称
            if hasattr(self, 'SUPPORTED_PROVIDERS'):
                provider_name = self.SUPPORTED_PROVIDERS.get(provider, provider)
            else:
                provider_name = provider

            # 内部逻辑：获取本地提供商列表（如果有的话）
            local_providers: Set[str] = set()
            if allow_empty_local and hasattr(self, '_LOCAL_PROVIDERS'):
                local_providers = self._LOCAL_PROVIDERS

            # 内部逻辑：根据规则执行验证
            for rule in rules:
                if rule == ValidationRule.API_KEY_REQUIRED:
                    api_key = config.get("api_key", "")
                    # 内部逻辑：检查是否允许为空（本地模型）
                    allow_empty = provider in local_providers
                    ConfigValidator.validate_api_key(api_key, provider_name, allow_empty)

                elif rule == ValidationRule.GROUP_ID_REQUIRED:
                    group_id = config.get("group_id", "")
                    ConfigValidator.validate_group_id(group_id, provider_name)

                elif rule == ValidationRule.ENDPOINT_REQUIRED:
                    endpoint = config.get("endpoint", "")
                    ConfigValidator.validate_endpoint(endpoint, provider_name)

            # 内部逻辑：验证通过，执行原函数
            return func(self, config, *args, **kwargs)

        return wrapper

    return decorator


class ValidationBuilder:
    """
    类级注释：验证构建器类
    设计模式：建造者模式
    职责：提供链式调用方式构建复杂的验证逻辑
    """

    def __init__(self):
        """内部变量：初始化验证规则列表和本地提供商集合"""
        self._rules: List[ValidationRule] = []
        self._local_providers: Set[str] = set()

    def require_api_key(self) -> 'ValidationBuilder':
        """
        函数级注释：添加 API 密钥必填规则
        返回值：当前构建器实例（支持链式调用）
        """
        self._rules.append(ValidationRule.API_KEY_REQUIRED)
        return self

    def require_group_id(self) -> 'ValidationBuilder':
        """
        函数级注释：添加 Group ID 必填规则
        返回值：当前构建器实例
        """
        self._rules.append(ValidationRule.GROUP_ID_REQUIRED)
        return self

    def require_endpoint(self) -> 'ValidationBuilder':
        """
        函数级注释：添加端点必填规则
        返回值：当前构建器实例
        """
        self._rules.append(ValidationRule.ENDPOINT_REQUIRED)
        return self

    def with_local_providers(self, providers: Set[str]) -> 'ValidationBuilder':
        """
        函数级注释：设置本地提供商集合（本地提供商不需要 API 密钥）
        参数：
            providers: 本地提供商名称集合
        返回值：当前构建器实例
        """
        self._local_providers = providers
        return self

    def build(self):
        """
        函数级注释：构建验证装饰器
        返回值：验证装饰器函数
        """
        return validate_config(*self._rules, allow_empty_local=True)
