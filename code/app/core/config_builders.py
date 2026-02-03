# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：配置构建器模块
内部逻辑：分离配置的各个职责，遵循单一职责原则
设计模式：建造者模式、责任链模式
设计原则：单一职责原则、开闭原则
"""

from typing import Dict, Any, Optional, Callable, List
from abc import ABC, abstractmethod
from loguru import logger


class ConfigValidator(ABC):
    """
    类级注释：配置验证器抽象基类
    设计模式：责任链模式
    职责：定义配置验证的接口
    """

    def __init__(self, next_validator: Optional['ConfigValidator'] = None):
        """
        函数级注释：初始化验证器
        参数：
            next_validator: 责任链中的下一个验证器
        """
        self._next_validator = next_validator

    def validate(self, field_name: str, value: Any, config: Dict[str, Any]) -> None:
        """
        函数级注释：执行验证（责任链模式）
        内部逻辑：执行当前验证 -> 调用下一个验证器
        参数：
            field_name: 字段名
            value: 字段值
            config: 完整配置
        异常：ValueError - 验证失败时
        """
        self._validate_specific(field_name, value, config)

        if self._next_validator:
            self._next_validator.validate(field_name, value, config)

    @abstractmethod
    def _validate_specific(self, field_name: str, value: Any, config: Dict[str, Any]) -> None:
        """具体验证逻辑（抽象方法）"""
        pass


class DatabaseProviderValidator(ConfigValidator):
    """
    类级注释：数据库提供商验证器
    职责：验证数据库提供商配置是否有效
    """

    def _validate_specific(self, field_name: str, value: Any, config: Dict[str, Any]) -> None:
        if field_name == "DATABASE_PROVIDER" or field_name == "database_provider":
            valid_providers = ["postgresql", "sqlite"]
            if value and value.lower() not in valid_providers:
                raise ValueError(
                    f"不支持的数据库提供商: {value}. "
                    f"支持的提供商: {valid_providers}"
                )


class LLMProviderValidator(ConfigValidator):
    """
    类级注释：LLM提供商验证器
    职责：验证LLM提供商配置是否有效
    """

    def _validate_specific(self, field_name: str, value: Any, config: Dict[str, Any]) -> None:
        if field_name == "LLM_PROVIDER" or field_name == "llm_provider":
            valid_providers = ["ollama", "zhipuai", "minimax", "moonshot", "openai", "deepseek"]
            if value and value.lower() not in valid_providers:
                raise ValueError(
                    f"不支持的LLM提供商: {value}. "
                    f"支持的提供商: {valid_providers}"
                )


class TimezoneValidator(ConfigValidator):
    """
    类级注释：时区验证器
    职责：验证时区配置是否有效
    """

    def _validate_specific(self, field_name: str, value: Any, config: Dict[str, Any]) -> None:
        if field_name == "TIMEZONE" or field_name == "timezone":
            if value:
                try:
                    from zoneinfo import ZoneInfo
                    ZoneInfo(value)
                except Exception:
                    raise ValueError(
                        f"无效的时区配置: {value}. "
                        f"请使用IANA时区标识符"
                    )


class SensitiveDataConfigBuilder:
    """
    类级注释：敏感数据配置构建器
    设计模式：建造者模式
    职责：专门管理敏感数据过滤相关配置
    """

    def __init__(self):
        """内部变量：初始化配置项"""
        self._enable_filter: bool = True
        self._mask_strategy: str = "full"
        self._filter_mobile: bool = True
        self._filter_email: bool = True

    def enable_filter(self, enable: bool) -> 'SensitiveDataConfigBuilder':
        """设置是否启用过滤"""
        self._enable_filter = enable
        return self

    def set_mask_strategy(self, strategy: str) -> 'SensitiveDataConfigBuilder':
        """设置脱敏策略"""
        self._mask_strategy = strategy
        return self

    def filter_mobile(self, filter_mobile: bool) -> 'SensitiveDataConfigBuilder':
        """设置是否过滤手机号"""
        self._filter_mobile = filter_mobile
        return self

    def filter_email(self, filter_email: bool) -> 'SensitiveDataConfigBuilder':
        """设置是否过滤邮箱"""
        self._filter_email = filter_email
        return self

    def build(self) -> Dict[str, Any]:
        """构建配置字典"""
        return {
            "ENABLE_SENSITIVE_DATA_FILTER": self._enable_filter,
            "SENSITIVE_DATA_MASK_STRATEGY": self._mask_strategy,
            "FILTER_MOBILE": self._filter_mobile,
            "FILTER_EMAIL": self._filter_email,
        }


class LLMConfigBuilder:
    """
    类级注释：LLM配置构建器
    设计模式：建造者模式
    职责：专门管理LLM相关配置
    """

    def __init__(self):
        """内部变量：初始化配置项"""
        self._provider: str = "ollama"
        self._model: str = "deepseek-r1:8b"
        self._embedding_provider: str = "ollama"
        self._embedding_model: str = "mxbai-embed-large:latest"

    def with_provider(self, provider: str) -> 'LLMConfigBuilder':
        """设置LLM提供商"""
        self._provider = provider
        return self

    def with_model(self, model: str) -> 'LLMConfigBuilder':
        """设置模型名称"""
        self._model = model
        return self

    def with_embedding_provider(self, provider: str) -> 'LLMConfigBuilder':
        """设置Embedding提供商"""
        self._embedding_provider = provider
        return self

    def with_embedding_model(self, model: str) -> 'LLMConfigBuilder':
        """设置Embedding模型"""
        self._embedding_model = model
        return self

    def build(self) -> Dict[str, Any]:
        """构建配置字典"""
        return {
            "LLM_PROVIDER": self._provider,
            "CHAT_MODEL": self._model,
            "EMBEDDING_PROVIDER": self._embedding_provider,
            "EMBEDDING_MODEL": self._embedding_model,
        }


class DatabaseConfigBuilder:
    """
    类级注释：数据库配置构建器
    设计模式：建造者模式
    职责：专门管理数据库相关配置
    """

    def __init__(self):
        """内部变量：初始化配置项"""
        self._provider: str = "postgresql"
        self._host: str = "localhost"
        self._port: int = 5432
        self._name: str = "knowledge_db"
        self._user: str = "postgres"
        self._password: str = ""

    def with_provider(self, provider: str) -> 'DatabaseConfigBuilder':
        """设置数据库提供商"""
        self._provider = provider
        return self

    def with_host(self, host: str) -> 'DatabaseConfigBuilder':
        """设置数据库主机"""
        self._host = host
        return self

    def with_port(self, port: int) -> 'DatabaseConfigBuilder':
        """设置数据库端口"""
        self._port = port
        return self

    def with_name(self, name: str) -> 'DatabaseConfigBuilder':
        """设置数据库名称"""
        self._name = name
        return self

    def with_user(self, user: str) -> 'DatabaseConfigBuilder':
        """设置数据库用户"""
        self._user = user
        return self

    def with_password(self, password: str) -> 'DatabaseConfigBuilder':
        """设置数据库密码"""
        self._password = password
        return self

    def build(self) -> Dict[str, Any]:
        """构建配置字典"""
        return {
            "DATABASE_PROVIDER": self._provider,
            "DB_HOST": self._host,
            "DB_PORT": self._port,
            "DB_NAME": self._name,
            "DB_USER": self._user,
            "DB_PASSWORD": self._password,
        }


# 便捷函数
def build_sensitive_data_config() -> Dict[str, Any]:
    """
    函数级注释：使用敏感数据构建器创建配置
    返回值：配置字典
    """
    return (SensitiveDataConfigBuilder()
            .enable_filter(True)
            .set_mask_strategy("full")
            .filter_mobile(True)
            .filter_email(True)
            .build())


def build_llm_config(
    provider: str = "ollama",
    model: str = "deepseek-r1:8b",
    embedding_provider: str = "ollama",
    embedding_model: str = "mxbai-embed-large:latest"
) -> Dict[str, Any]:
    """
    函数级注释：使用LLM构建器创建配置
    返回值：配置字典
    """
    return (LLMConfigBuilder()
            .with_provider(provider)
            .with_model(model)
            .with_embedding_provider(embedding_provider)
            .with_embedding_model(embedding_model)
            .build())


def build_database_config(
    provider: str = "postgresql",
    host: str = "localhost",
    port: int = 5432,
    name: str = "knowledge_db",
    user: str = "postgres",
    password: str = ""
) -> Dict[str, Any]:
    """
    函数级注释：使用数据库构建器创建配置
    返回值：配置字典
    """
    return (DatabaseConfigBuilder()
            .with_provider(provider)
            .with_host(host)
            .with_port(port)
            .with_name(name)
            .with_user(user)
            .with_password(password)
            .build())
