# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：配置验证器模块（责任链模式）单元测试
内部逻辑：测试配置验证器的责任链模式实现
测试策略：
   - 单元测试：测试每个验证器的验证逻辑
   - 责任链测试：测试验证器链式调用
"""

import pytest
from app.core.config.validators import (
    Validator,
    DatabaseProviderValidator,
    LLMProviderValidator,
    TimezoneValidator,
    validate_timezone,
)


class MockConfig:
    """
    类级注释：Mock 配置类
    职责：模拟配置对象用于测试
    """

    def __init__(self, **kwargs):
        """内部逻辑：设置配置属性"""
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestValidator:
    """
    类级注释：验证器基类测试
    """

    def test_abstract_class_cannot_be_instantiated(self):
        """
        函数级注释：测试抽象类不能直接实例化
        内部逻辑：验证抛出 TypeError
        """
        # 验证：抽象类不能实例化
        with pytest.raises(TypeError):
            Validator()

    def test_validate_calls_chain(self):
        """
        函数级注释：测试验证链调用
        内部逻辑：验证责任链正确执行
        """
        # 内部变量：创建具体验证器
        validator1 = DatabaseProviderValidator()
        validator2 = LLMProviderValidator(validator1)

        # 内部逻辑：调用验证
        config = MockConfig(
            DATABASE_PROVIDER="sqlite",
            LLM_PROVIDER="ollama"
        )
        is_valid, errors = validator2.validate(config)

        # 验证：验证通过
        assert is_valid is True
        assert len(errors) == 0


class TestDatabaseProviderValidator:
    """
    类级注释：数据库提供商验证器测试
    """

    def test_validate_postgresql_provider(self):
        """
        函数级注释：测试验证 PostgreSQL 提供商
        内部逻辑：验证 PostgreSQL 是有效提供商
        """
        # 内部变量：创建验证器
        validator = DatabaseProviderValidator()
        config = MockConfig(DATABASE_PROVIDER="postgresql")

        # 内部逻辑：执行验证
        is_valid, errors = validator.validate(config)

        # 验证：通过
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_sqlite_provider(self):
        """
        函数级注释：测试验证 SQLite 提供商
        内部逻辑：验证 SQLite 是有效提供商
        """
        # 内部变量：创建验证器
        validator = DatabaseProviderValidator()
        config = MockConfig(DATABASE_PROVIDER="sqlite")

        # 内部逻辑：执行验证
        is_valid, errors = validator.validate(config)

        # 验证：通过
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_sqlite_uppercase(self):
        """
        函数级注释：测试验证 SQLite（大写）
        内部逻辑：验证大小写不敏感
        """
        # 内部变量：创建验证器
        validator = DatabaseProviderValidator()
        config = MockConfig(DATABASE_PROVIDER="SQLite")

        # 内部逻辑：执行验证
        is_valid, errors = validator.validate(config)

        # 验证：通过
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_invalid_provider(self):
        """
        函数级注释：测试验证无效提供商
        内部逻辑：验证无效提供商返回错误
        """
        # 内部变量：创建验证器
        validator = DatabaseProviderValidator()
        config = MockConfig(DATABASE_PROVIDER="mysql")

        # 内部逻辑：执行验证
        is_valid, errors = validator.validate(config)

        # 验证：不通过
        assert is_valid is False
        assert len(errors) == 1
        assert "不支持的数据库提供商" in errors[0]

    def test_validate_without_database_provider_attribute(self):
        """
        函数级注释：测试验证没有提供商属性的配置
        内部逻辑：验证缺少属性时通过
        """
        # 内部变量：创建验证器
        validator = DatabaseProviderValidator()
        config = MockConfig()  # 没有 DATABASE_PROVIDER 属性

        # 内部逻辑：执行验证
        is_valid, errors = validator.validate(config)

        # 验证：通过（没有属性不报错）
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_with_next_validator(self):
        """
        函数级注释：测试验证链（带下一个验证器）
        内部逻辑：验证责任链正确传递
        """
        # 内部变量：创建验证器链
        next_validator = LLMProviderValidator()
        validator = DatabaseProviderValidator(next_validator)

        # 内部逻辑：配置中数据库有效，LLM无效
        config = MockConfig(
            DATABASE_PROVIDER="sqlite",
            LLM_PROVIDER="invalid_llm"
        )

        # 内部逻辑：执行验证
        is_valid, errors = validator.validate(config)

        # 验证：LLM验证失败
        assert is_valid is False
        assert len(errors) == 1
        assert "不支持的LLM提供商" in errors[0]


class TestLLMProviderValidator:
    """
    类级注释：LLM提供商验证器测试
    """

    def test_validate_ollama_provider(self):
        """
        函数级注释：测试验证 Ollama 提供商
        内部逻辑：验证 Ollama 是有效提供商
        """
        # 内部变量：创建验证器
        validator = LLMProviderValidator()
        config = MockConfig(LLM_PROVIDER="ollama")

        # 内部逻辑：执行验证
        is_valid, errors = validator.validate(config)

        # 验证：通过
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_zhipuai_provider(self):
        """
        函数级注释：测试验证智谱AI提供商
        内部逻辑：验证智谱AI是有效提供商
        """
        # 内部变量：创建验证器
        validator = LLMProviderValidator()
        config = MockConfig(LLM_PROVIDER="zhipuai")

        # 内部逻辑：执行验证
        is_valid, errors = validator.validate(config)

        # 验证：通过
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_minimax_provider(self):
        """
        函数级注释：测试验证 MiniMax 提供商
        内部逻辑：验证 MiniMax 是有效提供商
        """
        # 内部变量：创建验证器
        validator = LLMProviderValidator()
        config = MockConfig(LLM_PROVIDER="minimax")

        # 内部逻辑：执行验证
        is_valid, errors = validator.validate(config)

        # 验证：通过
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_moonshot_provider(self):
        """
        函数级注释：测试验证 Moonshot 提供商
        内部逻辑：验证 Moonshot 是有效提供商
        """
        # 内部变量：创建验证器
        validator = LLMProviderValidator()
        config = MockConfig(LLM_PROVIDER="moonshot")

        # 内部逻辑：执行验证
        is_valid, errors = validator.validate(config)

        # 验证：通过
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_openai_provider(self):
        """
        函数级注释：测试验证 OpenAI 提供商
        内部逻辑：验证 OpenAI 是有效提供商
        """
        # 内部变量：创建验证器
        validator = LLMProviderValidator()
        config = MockConfig(LLM_PROVIDER="openai")

        # 内部逻辑：执行验证
        is_valid, errors = validator.validate(config)

        # 验证：通过
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_deepseek_provider(self):
        """
        函数级注释：测试验证 DeepSeek 提供商
        内部逻辑：验证 DeepSeek 是有效提供商
        """
        # 内部变量：创建验证器
        validator = LLMProviderValidator()
        config = MockConfig(LLM_PROVIDER="deepseek")

        # 内部逻辑：执行验证
        is_valid, errors = validator.validate(config)

        # 验证：通过
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_invalid_provider(self):
        """
        函数级注释：测试验证无效提供商
        内部逻辑：验证无效提供商返回错误
        """
        # 内部变量：创建验证器
        validator = LLMProviderValidator()
        config = MockConfig(LLM_PROVIDER="invalid_provider")

        # 内部逻辑：执行验证
        is_valid, errors = validator.validate(config)

        # 验证：不通过
        assert is_valid is False
        assert len(errors) == 1
        assert "不支持的LLM提供商" in errors[0]

    def test_validate_without_llm_provider_attribute(self):
        """
        函数级注释：测试验证没有提供商属性的配置
        内部逻辑：验证缺少属性时通过
        """
        # 内部变量：创建验证器
        validator = LLMProviderValidator()
        config = MockConfig()  # 没有 LLM_PROVIDER 属性

        # 内部逻辑：执行验证
        is_valid, errors = validator.validate(config)

        # 验证：通过（没有属性不报错）
        assert is_valid is True
        assert len(errors) == 0


class TestTimezoneValidator:
    """
    类级注释：时区验证器测试
    """

    def test_valid_timezone_asia_shanghai(self):
        """
        函数级注释：测试验证有效的 Asia/Shanghai 时区
        内部逻辑：验证标准时区通过
        """
        # 内部变量：创建验证器
        validator = TimezoneValidator()
        config = MockConfig(TIMEZONE="Asia/Shanghai")

        # 内部逻辑：执行验证
        is_valid, errors = validator.validate(config)

        # 验证：通过
        assert is_valid is True
        assert len(errors) == 0

    def test_valid_timezone_utc(self):
        """
        函数级注释：测试验证 UTC 时区
        内部逻辑：验证 UTC 通过
        """
        # 内部变量：创建验证器
        validator = TimezoneValidator()
        config = MockConfig(TIMEZONE="UTC")

        # 内部逻辑：执行验证
        is_valid, errors = validator.validate(config)

        # 验证：通过
        assert is_valid is True
        assert len(errors) == 0

    def test_valid_timezone_america_new_york(self):
        """
        函数级注释：测试验证 America/New_York 时区
        内部逻辑：验证美国时区通过
        """
        # 内部变量：创建验证器
        validator = TimezoneValidator()
        config = MockConfig(TIMEZONE="America/New_York")

        # 内部逻辑：执行验证
        is_valid, errors = validator.validate(config)

        # 验证：通过
        assert is_valid is True
        assert len(errors) == 0

    def test_invalid_timezone(self):
        """
        函数级注释：测试验证无效时区
        内部逻辑：验证无效时区返回错误
        """
        # 内部变量：创建验证器
        validator = TimezoneValidator()
        config = MockConfig(TIMEZONE="Invalid/Timezone")

        # 内部逻辑：执行验证
        is_valid, errors = validator.validate(config)

        # 验证：不通过
        assert is_valid is False
        assert len(errors) == 1
        assert "无效的时区配置" in errors[0]

    def test_validate_without_timezone_attribute(self):
        """
        函数级注释：测试验证没有时区属性的配置
        内部逻辑：验证缺少属性时通过
        """
        # 内部变量：创建验证器
        validator = TimezoneValidator()
        config = MockConfig()  # 没有 TIMEZONE 属性

        # 内部逻辑：执行验证
        is_valid, errors = validator.validate(config)

        # 验证：通过（没有属性不报错）
        assert is_valid is True
        assert len(errors) == 0


class TestValidateTimezoneFunction:
    """
    类级注释：时区验证函数测试
    """

    def test_valid_timezone_string(self):
        """
        函数级注释：测试验证有效时区字符串
        内部逻辑：验证有效时区返回原值
        """
        # 内部逻辑：验证有效时区
        result = validate_timezone("Asia/Shanghai")
        assert result == "Asia/Shanghai"

    def test_empty_timezone_returns_default(self):
        """
        函数级注释：测试空时区返回默认值
        内部逻辑：验证空字符串返回默认时区
        """
        # 内部逻辑：空字符串
        result = validate_timezone("")
        assert result == "Asia/Shanghai"

    def test_none_timezone_returns_default(self):
        """
        函数级注释：测试 None 时区返回默认值
        内部逻辑：验证 None 返回默认时区
        """
        # 内部逻辑：None 值
        result = validate_timezone(None)
        assert result == "Asia/Shanghai"

    def test_invalid_timezone_raises_error(self):
        """
        函数级注释：测试无效时区抛出异常
        内部逻辑：验证无效时区抛出 ValueError
        """
        # 验证：抛出异常
        with pytest.raises(ValueError) as exc_info:
            validate_timezone("Invalid/Timezone")

        assert "无效的时区配置" in str(exc_info.value)
        assert "IANA时区标识符" in str(exc_info.value)

    def test_utc_timezone(self):
        """
        函数级注释：测试 UTC 时区
        内部逻辑：验证 UTC 通过
        """
        # 内部逻辑：UTC 时区
        result = validate_timezone("UTC")
        assert result == "UTC"


class TestValidatorChain:
    """
    类级注释：验证器责任链测试
    """

    def test_full_validation_chain(self):
        """
        函数级注释：测试完整的验证链
        内部逻辑：验证所有验证器按顺序执行
        """
        # 内部变量：创建验证器链
        # 数据库 -> LLM -> 时区
        validator_chain = TimezoneValidator(
            LLMProviderValidator(
                DatabaseProviderValidator()
            )
        )

        # 内部逻辑：全部有效的配置
        config = MockConfig(
            DATABASE_PROVIDER="postgresql",
            LLM_PROVIDER="zhipuai",
            TIMEZONE="Asia/Shanghai"
        )

        # 内部逻辑：执行验证
        is_valid, errors = validator_chain.validate(config)

        # 验证：全部通过
        assert is_valid is True
        assert len(errors) == 0

    def test_chain_with_first_validator_fails(self):
        """
        函数级注释：测试链中第一个验证器失败
        内部逻辑：验证第一个失败被正确收集
        """
        # 内部变量：创建验证器链
        validator_chain = TimezoneValidator(
            LLMProviderValidator(
                DatabaseProviderValidator()
            )
        )

        # 内部逻辑：数据库配置无效
        config = MockConfig(
            DATABASE_PROVIDER="mysql",  # 无效
            LLM_PROVIDER="zhipuai",
            TIMEZONE="Asia/Shanghai"
        )

        # 内部逻辑：执行验证
        is_valid, errors = validator_chain.validate(config)

        # 验证：数据库验证失败
        assert is_valid is False
        assert len(errors) == 1
        assert "数据库" in errors[0]

    def test_chain_with_multiple_validators_fail(self):
        """
        函数级注释：测试链中多个验证器失败
        内部逻辑：验证所有失败都被收集
        """
        # 内部变量：创建验证器链
        validator_chain = TimezoneValidator(
            LLMProviderValidator(
                DatabaseProviderValidator()
            )
        )

        # 内部逻辑：多个配置无效
        config = MockConfig(
            DATABASE_PROVIDER="mysql",  # 无效
            LLM_PROVIDER="invalid",     # 无效
            TIMEZONE="Invalid/Zone"     # 无效
        )

        # 内部逻辑：执行验证
        is_valid, errors = validator_chain.validate(config)

        # 验证：所有错误都被收集
        assert is_valid is False
        assert len(errors) == 3

    def test_chain_stops_at_null_link(self):
        """
        函数级注释：测试链在空链接处停止
        内部逻辑：验证链在下一个验证器为 None 时正确终止
        """
        # 内部变量：创建单个验证器（无下一个）
        validator = DatabaseProviderValidator(None)
        config = MockConfig(DATABASE_PROVIDER="sqlite")

        # 内部逻辑：执行验证
        is_valid, errors = validator.validate(config)

        # 验证：正常终止
        assert is_valid is True
        assert len(errors) == 0
