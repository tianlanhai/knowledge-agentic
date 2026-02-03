# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：配置构建器模块补充测试
内部逻辑：测试config_builders.py中未覆盖的代码路径
覆盖范围：
    - ConfigValidator验证器
    - DatabaseProviderValidator
    - LLMProviderValidator
    - TimezoneValidator
    - 各种Builder类的流式接口
    - 便捷工厂函数
"""

import pytest
from unittest.mock import patch
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.config_builders import (
    ConfigValidator,
    DatabaseProviderValidator,
    LLMProviderValidator,
    TimezoneValidator,
    SensitiveDataConfigBuilder,
    LLMConfigBuilder,
    DatabaseConfigBuilder,
    build_sensitive_data_config,
    build_llm_config,
    build_database_config,
)


class TestConfigValidatorChain:
    """
    类级注释：ConfigValidator责任链测试
    """

    def test_validator_chain_single(self):
        """测试单个验证器"""
        validator = DatabaseProviderValidator()
        config = {"DATABASE_PROVIDER": "postgresql"}

        # 不应该抛出异常
        validator.validate("DATABASE_PROVIDER", "postgresql", config)

    def test_validator_chain_multiple(self):
        """测试验证器链"""
        config = {"DATABASE_PROVIDER": "postgresql", "LLM_PROVIDER": "ollama"}

        validator = DatabaseProviderValidator(LLMProviderValidator())
        validator.validate("DATABASE_PROVIDER", "postgresql", config)
        validator.validate("LLM_PROVIDER", "ollama", config)

    def test_validator_invalid_database_provider(self):
        """测试无效数据库提供商"""
        validator = DatabaseProviderValidator()
        config = {}

        with pytest.raises(ValueError, match="不支持的数据库提供商"):
            validator.validate("DATABASE_PROVIDER", "invalid", config)

    def test_validator_invalid_llm_provider(self):
        """测试无效LLM提供商"""
        validator = LLMProviderValidator()
        config = {}

        with pytest.raises(ValueError, match="不支持的LLM提供商"):
            validator.validate("LLM_PROVIDER", "invalid", config)

    def test_validator_invalid_timezone(self):
        """测试无效时区"""
        validator = TimezoneValidator()
        config = {}

        with pytest.raises(ValueError, match="无效的时区配置"):
            validator.validate("TIMEZONE", "Invalid/Zone", config)

    def test_validator_valid_timezone(self):
        """测试有效时区"""
        validator = TimezoneValidator()
        config = {}

        # 不应该抛出异常
        validator.validate("TIMEZONE", "Asia/Shanghai", config)
        validator.validate("TIMEZONE", "UTC", config)

    def test_validator_empty_timezone(self):
        """测试空时区"""
        validator = TimezoneValidator()
        config = {}

        # 空值不抛出异常
        validator.validate("TIMEZONE", "", config)


class TestSensitiveDataConfigBuilder:
    """
    类级注释：SensitiveDataConfigBuilder测试
    """

    def test_default_values(self):
        """测试默认值"""
        builder = SensitiveDataConfigBuilder()
        config = builder.build()

        assert config["ENABLE_SENSITIVE_DATA_FILTER"] is True
        assert config["SENSITIVE_DATA_MASK_STRATEGY"] == "full"
        assert config["FILTER_MOBILE"] is True
        assert config["FILTER_EMAIL"] is True

    def test_enable_filter_false(self):
        """测试禁用过滤"""
        builder = SensitiveDataConfigBuilder()
        config = builder.enable_filter(False).build()

        assert config["ENABLE_SENSITIVE_DATA_FILTER"] is False

    def test_set_mask_strategy_partial(self):
        """测试部分脱敏策略"""
        builder = SensitiveDataConfigBuilder()
        config = builder.set_mask_strategy("partial").build()

        assert config["SENSITIVE_DATA_MASK_STRATEGY"] == "partial"

    def test_set_mask_strategy_hash(self):
        """测试哈希脱敏策略"""
        builder = SensitiveDataConfigBuilder()
        config = builder.set_mask_strategy("hash").build()

        assert config["SENSITIVE_DATA_MASK_STRATEGY"] == "hash"

    def test_filter_mobile_false(self):
        """测试不过滤手机号"""
        builder = SensitiveDataConfigBuilder()
        config = builder.filter_mobile(False).build()

        assert config["FILTER_MOBILE"] is False

    def test_filter_email_false(self):
        """测试不过滤邮箱"""
        builder = SensitiveDataConfigBuilder()
        config = builder.filter_email(False).build()

        assert config["FILTER_EMAIL"] is False

    def test_fluent_interface(self):
        """测试流式接口"""
        builder = SensitiveDataConfigBuilder()
        config = (builder
                  .enable_filter(False)
                  .set_mask_strategy("partial")
                  .filter_mobile(True)
                  .filter_email(False)
                  .build())

        assert config["ENABLE_SENSITIVE_DATA_FILTER"] is False
        assert config["SENSITIVE_DATA_MASK_STRATEGY"] == "partial"
        assert config["FILTER_MOBILE"] is True
        assert config["FILTER_EMAIL"] is False


class TestLLMConfigBuilder:
    """
    类级注释：LLMConfigBuilder测试
    """

    def test_default_values(self):
        """测试默认值"""
        builder = LLMConfigBuilder()
        config = builder.build()

        assert config["LLM_PROVIDER"] == "ollama"
        assert config["CHAT_MODEL"] == "deepseek-r1:8b"
        assert config["EMBEDDING_PROVIDER"] == "ollama"
        assert config["EMBEDDING_MODEL"] == "mxbai-embed-large:latest"

    def test_with_provider_zhipuai(self):
        """测试设置智谱AI提供商"""
        builder = LLMConfigBuilder()
        config = builder.with_provider("zhipuai").build()

        assert config["LLM_PROVIDER"] == "zhipuai"

    def test_with_provider_minimax(self):
        """测试设置MiniMax提供商"""
        builder = LLMConfigBuilder()
        config = builder.with_provider("minimax").build()

        assert config["LLM_PROVIDER"] == "minimax"

    def test_with_provider_moonshot(self):
        """测试设置月之暗面提供商"""
        builder = LLMConfigBuilder()
        config = builder.with_provider("moonshot").build()

        assert config["LLM_PROVIDER"] == "moonshot"

    def test_with_model(self):
        """测试设置模型"""
        builder = LLMConfigBuilder()
        config = builder.with_model("glm-4").build()

        assert config["CHAT_MODEL"] == "glm-4"

    def test_with_embedding_provider(self):
        """测试设置Embedding提供商"""
        builder = LLMConfigBuilder()
        config = builder.with_embedding_provider("zhipuai").build()

        assert config["EMBEDDING_PROVIDER"] == "zhipuai"

    def test_with_embedding_model(self):
        """测试设置Embedding模型"""
        builder = LLMConfigBuilder()
        config = builder.with_embedding_model("embedding-3").build()

        assert config["EMBEDDING_MODEL"] == "embedding-3"

    def test_fluent_interface(self):
        """测试流式接口"""
        builder = LLMConfigBuilder()
        config = (builder
                  .with_provider("minimax")
                  .with_model("abab5.5-chat")
                  .with_embedding_provider("local")
                  .with_embedding_model("bge-large-zh")
                  .build())

        assert config["LLM_PROVIDER"] == "minimax"
        assert config["CHAT_MODEL"] == "abab5.5-chat"
        assert config["EMBEDDING_PROVIDER"] == "local"
        assert config["EMBEDDING_MODEL"] == "bge-large-zh"


class TestDatabaseConfigBuilder:
    """
    类级注释：DatabaseConfigBuilder测试
    """

    def test_default_values(self):
        """测试默认值"""
        builder = DatabaseConfigBuilder()
        config = builder.build()

        assert config["DATABASE_PROVIDER"] == "postgresql"
        assert config["DB_HOST"] == "localhost"
        assert config["DB_PORT"] == 5432
        assert config["DB_NAME"] == "knowledge_db"
        assert config["DB_USER"] == "postgres"
        assert config["DB_PASSWORD"] == ""

    def test_with_provider_sqlite(self):
        """测试设置SQLite提供商"""
        builder = DatabaseConfigBuilder()
        config = builder.with_provider("sqlite").build()

        assert config["DATABASE_PROVIDER"] == "sqlite"

    def test_with_host(self):
        """测试设置主机"""
        builder = DatabaseConfigBuilder()
        config = builder.with_host("192.168.1.1").build()

        assert config["DB_HOST"] == "192.168.1.1"

    def test_with_port(self):
        """测试设置端口"""
        builder = DatabaseConfigBuilder()
        config = builder.with_port(3306).build()

        assert config["DB_PORT"] == 3306

    def test_with_name(self):
        """测试设置数据库名"""
        builder = DatabaseConfigBuilder()
        config = builder.with_name("mydb").build()

        assert config["DB_NAME"] == "mydb"

    def test_with_user(self):
        """测试设置用户"""
        builder = DatabaseConfigBuilder()
        config = builder.with_user("admin").build()

        assert config["DB_USER"] == "admin"

    def test_with_password(self):
        """测试设置密码"""
        builder = DatabaseConfigBuilder()
        config = builder.with_password("secret123").build()

        assert config["DB_PASSWORD"] == "secret123"

    def test_fluent_interface(self):
        """测试流式接口"""
        builder = DatabaseConfigBuilder()
        config = (builder
                  .with_provider("postgresql")
                  .with_host("db.example.com")
                  .with_port(5432)
                  .with_name("production_db")
                  .with_user("dbuser")
                  .with_password("dbpass")
                  .build())

        assert config["DATABASE_PROVIDER"] == "postgresql"
        assert config["DB_HOST"] == "db.example.com"
        assert config["DB_PORT"] == 5432
        assert config["DB_NAME"] == "production_db"
        assert config["DB_USER"] == "dbuser"
        assert config["DB_PASSWORD"] == "dbpass"


class TestConvenienceFunctions:
    """
    类级注释：便捷工厂函数测试
    """

    def test_build_sensitive_data_config(self):
        """测试构建敏感数据配置"""
        config = build_sensitive_data_config()

        assert config["ENABLE_SENSITIVE_DATA_FILTER"] is True
        assert config["SENSITIVE_DATA_MASK_STRATEGY"] == "full"
        assert config["FILTER_MOBILE"] is True
        assert config["FILTER_EMAIL"] is True

    def test_build_llm_config_default(self):
        """测试构建LLM配置默认值"""
        config = build_llm_config()

        assert config["LLM_PROVIDER"] == "ollama"
        assert config["CHAT_MODEL"] == "deepseek-r1:8b"
        assert config["EMBEDDING_PROVIDER"] == "ollama"
        assert config["EMBEDDING_MODEL"] == "mxbai-embed-large:latest"

    def test_build_llm_config_custom(self):
        """测试构建自定义LLM配置"""
        config = build_llm_config(
            provider="zhipuai",
            model="glm-4",
            embedding_provider="zhipuai",
            embedding_model="embedding-3"
        )

        assert config["LLM_PROVIDER"] == "zhipuai"
        assert config["CHAT_MODEL"] == "glm-4"
        assert config["EMBEDDING_PROVIDER"] == "zhipuai"
        assert config["EMBEDDING_MODEL"] == "embedding-3"

    def test_build_database_config_default(self):
        """测试构建数据库配置默认值"""
        config = build_database_config()

        assert config["DATABASE_PROVIDER"] == "postgresql"
        assert config["DB_HOST"] == "localhost"
        assert config["DB_PORT"] == 5432
        assert config["DB_NAME"] == "knowledge_db"
        assert config["DB_USER"] == "postgres"
        assert config["DB_PASSWORD"] == ""

    def test_build_database_config_custom(self):
        """测试构建自定义数据库配置"""
        config = build_database_config(
            provider="sqlite",
            host="/data",
            port=0,
            name="mydb.db",
            user="",
            password=""
        )

        assert config["DATABASE_PROVIDER"] == "sqlite"
        assert config["DB_HOST"] == "/data"
        assert config["DB_NAME"] == "mydb.db"

    def test_build_database_config_postgresql(self):
        """测试构建PostgreSQL配置"""
        config = build_database_config(
            provider="postgresql",
            host="localhost",
            port=5432,
            name="testdb",
            user="testuser",
            password="testpass"
        )

        assert config["DATABASE_PROVIDER"] == "postgresql"
        assert config["DB_NAME"] == "testdb"
        assert config["DB_USER"] == "testuser"
        assert config["DB_PASSWORD"] == "testpass"


class TestValidatorCoverage:
    """
    类级注释：验证器覆盖率测试
    """

    def test_all_supported_database_providers(self):
        """测试所有支持的数据库提供商"""
        validator = DatabaseProviderValidator()
        config = {}

        for provider in ["postgresql", "sqlite"]:
            validator.validate("DATABASE_PROVIDER", provider, config)

    def test_all_supported_llm_providers(self):
        """测试所有支持的LLM提供商"""
        validator = LLMProviderValidator()
        config = {}

        for provider in ["ollama", "zhipuai", "minimax", "moonshot", "openai", "deepseek"]:
            validator.validate("LLM_PROVIDER", provider, config)

    def test_common_timezones(self):
        """测试常用时区"""
        validator = TimezoneValidator()
        config = {}

        timezones = [
            "Asia/Shanghai",
            "Asia/Tokyo",
            "America/New_York",
            "Europe/London",
            "UTC",
            "Europe/Paris",
            "Australia/Sydney"
        ]

        for tz in timezones:
            validator.validate("TIMEZONE", tz, config)

    def test_field_name_variants(self):
        """测试字段名变体"""
        # 测试小写字段名
        validator = DatabaseProviderValidator()
        config = {}

        validator.validate("database_provider", "postgresql", config)

        validator_llm = LLMProviderValidator()
        validator_llm.validate("llm_provider", "ollama", config)

        validator_tz = TimezoneValidator()
        validator_tz.validate("timezone", "Asia/Shanghai", config)
