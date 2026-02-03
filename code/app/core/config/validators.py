# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：配置验证器模块
内部逻辑：提供配置验证的处理器
设计模式：责任链模式 - 验证链
设计原则：单一职责原则
"""

from abc import ABC, abstractmethod
from typing import Optional, Any


class Validator(ABC):
    """
    类级注释：验证器抽象基类
    设计模式：责任链模式 - 验证器接口
    职责：定义验证器的统一接口
    """

    # 内部变量：下一个验证器
    _next: Optional['Validator'] = None

    def __init__(self, next_validator: Optional['Validator'] = None):
        """
        函数级注释：初始化验证器
        参数：
            next_validator - 下一个验证器（责任链）
        """
        self._next = next_validator

    def validate(self, config: Any) -> tuple[bool, list]:
        """
        函数级注释：执行验证（模板方法）
        参数：
            config - 待验证的配置对象
        返回值：(是否通过, 错误列表)
        """
        # 内部逻辑：执行当前验证
        is_valid, errors = self._validate(config)

        # 内部逻辑：传递给下一个验证器
        if self._next:
            next_valid, next_errors = self._next.validate(config)
            is_valid = is_valid and next_valid
            errors.extend(next_errors)

        return is_valid, errors

    @abstractmethod
    def _validate(self, config: Any) -> tuple[bool, list]:
        """
        函数级注释：执行具体的验证逻辑（抽象方法）
        参数：
            config - 待验证的配置对象
        返回值：(是否通过, 错误列表)
        """
        pass


class DatabaseProviderValidator(Validator):
    """
    类级注释：数据库提供商验证器
    职责：验证数据库提供商配置
    """

    def _validate(self, config: Any) -> tuple[bool, list]:
        """
        函数级注释：验证数据库提供商
        参数：config - 配置对象
        返回值：(是否通过, 错误列表)
        """
        errors = []

        # 内部逻辑：检查数据库提供商
        if hasattr(config, 'DATABASE_PROVIDER'):
            provider = config.DATABASE_PROVIDER
            valid_providers = ["postgresql", "sqlite"]
            if provider.lower() not in valid_providers:
                errors.append(f"不支持的数据库提供商: {provider}")

        return len(errors) == 0, errors


class LLMProviderValidator(Validator):
    """
    类级注释：LLM提供商验证器
    职责：验证LLM提供商配置
    """

    def _validate(self, config: Any) -> tuple[bool, list]:
        """
        函数级注释：验证LLM提供商
        参数：config - 配置对象
        返回值：(是否通过, 错误列表)
        """
        errors = []

        # 内部逻辑：检查LLM提供商
        if hasattr(config, 'LLM_PROVIDER'):
            provider = config.LLM_PROVIDER
            valid_providers = ["ollama", "zhipuai", "minimax", "moonshot", "openai", "deepseek"]
            if provider.lower() not in valid_providers:
                errors.append(f"不支持的LLM提供商: {provider}")

        return len(errors) == 0, errors


class TimezoneValidator(Validator):
    """
    类级注释：时区验证器
    职责：验证时区配置
    """

    def _validate(self, config: Any) -> tuple[bool, list]:
        """
        函数级注释：验证时区配置
        参数：config - 配置对象
        返回值：(是否通过, 错误列表)
        """
        errors = []

        # 内部逻辑：检查时区
        if hasattr(config, 'TIMEZONE'):
            timezone = config.TIMEZONE
            try:
                from zoneinfo import ZoneInfo
                ZoneInfo(timezone)
            except Exception:
                errors.append(f"无效的时区配置: {timezone}")

        return len(errors) == 0, errors


def validate_timezone(v: str) -> str:
    """
    函数级注释：验证时区配置是否有效
    参数：v - 时区字符串（如 Asia/Shanghai）
    返回值：验证后的时区字符串
    """
    if not v:
        return "Asia/Shanghai"

    try:
        from zoneinfo import ZoneInfo
        ZoneInfo(v)
    except Exception:
        raise ValueError(
            f"无效的时区配置: {v}. "
            f"请使用IANA时区标识符，如: Asia/Shanghai, UTC, America/New_York"
        )
    return v


# 内部变量：导出所有公共接口
# 注意：assemble_cors_origins 已移至 cors_config.py，此处保留别名以兼容旧代码
from app.core.config.cors_config import assemble_cors_origins

__all__ = [
    'Validator',
    'DatabaseProviderValidator',
    'LLMProviderValidator',
    'TimezoneValidator',
    'validate_timezone',
    'assemble_cors_origins',
]
