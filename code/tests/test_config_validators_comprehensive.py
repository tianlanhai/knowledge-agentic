# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：配置验证器模块全面测试
内部逻辑：测试配置验证器的责任链模式和所有验证器
"""

import pytest
from typing import Any
from unittest.mock import MagicMock

from app.core.config.validators import (
    Validator,
    DatabaseProviderValidator,
    LLMProviderValidator,
    TimezoneValidator,
    validate_timezone,
)


# ============================================================================
# 测试用配置对象
# ============================================================================


class MockConfig:
    """测试用配置对象"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


# ============================================================================
# Validator 抽象类测试
# ============================================================================


class TestValidatorAbstract:
    """Validator抽象类测试类"""

    def test_validator_has_next(self):
        """验证验证器有_next属性"""
        validator = DatabaseProviderValidator()
        assert validator._next is None

    def test_validate_calls_next(self):
        """验证调用下一个验证器"""
        validator1 = DatabaseProviderValidator()
        validator2 = LLMProviderValidator()
        validator1._next = validator2

        config = MockConfig(
            DATABASE_PROVIDER="postgresql",
            LLM_PROVIDER="ollama"
        )

        is_valid, errors = validator1.validate(config)

        assert is_valid is True
        assert len(errors) == 0


# ============================================================================
# DatabaseProviderValidator 测试
# ============================================================================


class TestDatabaseProviderValidator:
    """DatabaseProviderValidator测试类"""

    @pytest.fixture
    def validator(self):
        """创建验证器实例"""
        return DatabaseProviderValidator()

    def test_validate_postgresql(self, validator):
        """验证PostgreSQL提供商"""
        config = MockConfig(DATABASE_PROVIDER="postgresql")
        is_valid, errors = validator._validate(config)
        assert is_valid is True

    def test_validate_sqlite(self, validator):
        """验证SQLite提供商"""
        config = MockConfig(DATABASE_PROVIDER="sqlite")
        is_valid, errors = validator._validate(config)
        assert is_valid is True

    def test_validate_invalid_provider(self, validator):
        """验证无效提供商"""
        config = MockConfig(DATABASE_PROVIDER="mysql")
        is_valid, errors = validator._validate(config)
        assert is_valid is False
        assert "不支持的数据库提供商" in errors[0]


# ============================================================================
# LLMProviderValidator 测试
# ============================================================================


class TestLLMProviderValidator:
    """LLMProviderValidator测试类"""

    @pytest.fixture
    def validator(self):
        """创建验证器实例"""
        return LLMProviderValidator()

    def test_validate_ollama(self, validator):
        """验证Ollama提供商"""
        config = MockConfig(LLM_PROVIDER="ollama")
        is_valid, errors = validator._validate(config)
        assert is_valid is True

    def test_validate_zhipuai(self, validator):
        """验证智谱AI提供商"""
        config = MockConfig(LLM_PROVIDER="zhipuai")
        is_valid, errors = validator._validate(config)
        assert is_valid is True

    def test_validate_invalid_provider(self, validator):
        """验证无效提供商"""
        config = MockConfig(LLM_PROVIDER="claude")
        is_valid, errors = validator._validate(config)
        assert is_valid is False
        assert "不支持的LLM提供商" in errors[0]


# ============================================================================
# TimezoneValidator 测试
# ============================================================================


class TestTimezoneValidator:
    """TimezoneValidator测试类"""

    @pytest.fixture
    def validator(self):
        """创建验证器实例"""
        return TimezoneValidator()

    def test_validate_shanghai(self, validator):
        """验证上海时区"""
        config = MockConfig(TIMEZONE="Asia/Shanghai")
        is_valid, errors = validator._validate(config)
        assert is_valid is True

    def test_validate_utc(self, validator):
        """验证UTC时区"""
        config = MockConfig(TIMEZONE="UTC")
        is_valid, errors = validator._validate(config)
        assert is_valid is True

    def test_validate_invalid_timezone(self, validator):
        """验证无效时区"""
        config = MockConfig(TIMEZONE="Invalid/Timezone")
        is_valid, errors = validator._validate(config)
        assert is_valid is False
        assert "无效的时区配置" in errors[0]


# ============================================================================
# validate_timezone 函数测试
# ============================================================================


class TestValidateTimezoneFunction:
    """validate_timezone函数测试类"""

    def test_validate_timezone_valid(self):
        """验证有效时区"""
        result = validate_timezone("Asia/Shanghai")
        assert result == "Asia/Shanghai"

    def test_validate_timezone_empty_returns_default(self):
        """验证空时区返回默认值"""
        result = validate_timezone("")
        assert result == "Asia/Shanghai"

    def test_validate_timezone_none_returns_default(self):
        """验证None时区返回默认值"""
        result = validate_timezone(None)
        assert result == "Asia/Shanghai"

    def test_validate_timezone_invalid_raises_error(self):
        """验证无效时区抛出异常"""
        with pytest.raises(ValueError):
            validate_timezone("Invalid/Timezone")


# ============================================================================
# 责任链组合测试
# ============================================================================


class TestValidatorChain:
    """责任链组合测试类"""

    def test_validator_chain_all_pass(self):
        """验证责任链全部通过"""
        config = MockConfig(
            DATABASE_PROVIDER="postgresql",
            LLM_PROVIDER="ollama",
            TIMEZONE="Asia/Shanghai"
        )

        chain = DatabaseProviderValidator(
            LLMProviderValidator(
                TimezoneValidator()
            )
        )

        is_valid, errors = chain.validate(config)

        assert is_valid is True
        assert len(errors) == 0

    def test_validator_chain_first_fails(self):
        """验证责任链第一个失败"""
        config = MockConfig(
            DATABASE_PROVIDER="mysql",
            LLM_PROVIDER="ollama",
            TIMEZONE="Asia/Shanghai"
        )

        chain = DatabaseProviderValidator(
            LLMProviderValidator(
                TimezoneValidator()
            )
        )

        is_valid, errors = chain.validate(config)

        assert is_valid is False
        assert "不支持的数据库提供商" in errors[0]


# ============================================================================
# 边界条件测试
# ============================================================================


class TestValidatorEdgeCases:
    """验证器边界条件测试类"""

    def test_validator_with_none_config(self):
        """验证None配置处理"""
        validator = DatabaseProviderValidator()
        is_valid, errors = validator._validate(None)
        assert is_valid is True

    def test_validate_timezone_with_none(self):
        """验证None时区处理"""
        result = validate_timezone(None)
        assert result == "Asia/Shanghai"

    def test_validate_without_attribute(self):
        """验证没有属性时跳过验证"""
        validator = DatabaseProviderValidator()
        config = MockConfig()  # 没有DATABASE_PROVIDER属性
        is_valid, errors = validator._validate(config)
        assert is_valid is True
