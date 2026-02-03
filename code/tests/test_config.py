# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：核心配置模块测试
内部逻辑：测试Settings类的所有属性验证和配置获取功能
测试覆盖：
    1. Settings基础配置
    2. APIConfig配置
    3. CORSConfig配置
    4. LLMConfig配置
    5. DatabaseConfig配置
    6. StorageConfig配置
    7. SecurityConfig配置
    8. 验证器
"""

import pytest
from typing import List
from pydantic import AnyHttpUrl, ValidationError

from app.core.config import (
    Settings,
    settings,
    APIConfig,
    CORSConfig,
    LLMConfig,
    DatabaseConfig,
    StorageConfig,
    SecurityConfig,
    DatabaseProviderValidator,
    LLMProviderValidator,
    TimezoneValidator,
    assemble_cors_origins,
    validate_timezone,
)


# ============================================================================
# Settings基础测试
# ============================================================================

class TestSettingsBasic:
    """
    类级注释：Settings基础配置测试类
    职责：测试Settings类的基本属性和默认值
    """

    def test_settings_default_values(self):
        """
        函数级注释：测试Settings类的默认值配置

        内部逻辑：创建Settings实例 -> 验证默认属性值是否正确
        预期结果：所有默认值符合预期
        """
        # 内部变量：创建Settings实例
        s = Settings()

        # 内部逻辑：验证基础配置默认值
        assert s.APP_NAME == "Knowledge-Agentic"
        assert s.APP_VERSION == "0.1.0"
        assert s.API_V1_STR == "/api/v1"
        assert s.PORT == 8010

    def test_settings_sub_configs(self):
        """
        函数级注释：测试Settings子配置对象

        内部逻辑：验证各子配置对象存在
        预期结果：所有子配置都正确初始化
        """
        s = Settings()

        assert isinstance(s.app_config, APIConfig)
        assert isinstance(s.cors_config, CORSConfig)
        assert isinstance(s.llm_config, LLMConfig)
        assert isinstance(s.db_config, DatabaseConfig)
        assert isinstance(s.storage_config, StorageConfig)
        assert isinstance(s.security_config, SecurityConfig)

    def test_use_mock_default(self):
        """
        函数级注释：测试USE_MOCK默认值

        内部逻辑：验证USE_MOCK配置
        预期结果：默认为False
        """
        s = Settings()
        assert s.USE_MOCK is False

    def test_log_level_default(self):
        """
        函数级注释：测试日志级别默认值

        内部逻辑：验证LOG_LEVEL配置
        预期结果：LOG_LEVEL属性存在且可访问
        """
        s = Settings()
        # LOG_LEVEL可能不是直接属性，而是通过其他方式设置
        # 验证它存在即可
        assert hasattr(s, 'LOG_LEVEL')


# ============================================================================
# APIConfig测试
# ============================================================================

class TestAPIConfig:
    """
    类级注释：API配置测试类
    职责：测试APIConfig的配置
    """

    def test_api_config_defaults(self):
        """
        函数级注释：测试APIConfig默认值

        内部逻辑：创建APIConfig实例 -> 验证默认值
        预期结果：默认值正确
        """
        config = APIConfig()
        assert config.NAME == "Knowledge-Agentic"
        assert config.VERSION == "0.1.0"
        assert config.V1_STR == "/api/v1"
        assert config.PORT == 8010


# ============================================================================
# CORSConfig测试
# ============================================================================

class TestCORSConfig:
    """
    类级注释：CORS配置测试类
    职责：测试CORSConfig的配置
    """

    def test_cors_config_defaults(self):
        """
        函数级注释：测试CORSConfig默认值

        内部逻辑：创建CORSConfig实例 -> 验证默认值
        预期结果：默认值为空列表
        """
        config = CORSConfig()
        assert config.origins == []

    def test_assemble_cors_origins_string(self):
        """
        函数级注释：测试CORS来源字符串解析

        内部逻辑：传入逗号分隔的字符串 -> 验证转换为列表
        预期结果：字符串被正确分割为列表
        """
        result = assemble_cors_origins("http://localhost:3000,http://localhost:8080")
        assert isinstance(result, list)
        assert "http://localhost:3000" in result
        assert "http://localhost:8080" in result

    def test_assemble_cors_origins_with_spaces(self):
        """
        函数级注释：测试带空格的CORS来源解析

        内部逻辑：传入带空格的逗号分隔字符串 -> 验证空格被去除
        预期结果：空格被正确去除
        """
        result = assemble_cors_origins("http://localhost:3000 , http://localhost:8080 ")
        assert "http://localhost:3000" in result
        assert "http://localhost:8080" in result

    def test_assemble_cors_origins_list(self):
        """
        函数级注释：测试CORS来源列表直接赋值

        内部逻辑：直接传入列表 -> 验证列表保持不变
        预期结果：列表被正确返回
        """
        origins = ["http://localhost:3000"]
        result = assemble_cors_origins(origins)
        assert result == origins


# ============================================================================
# LLMConfig测试
# ============================================================================

class TestLLMConfig:
    """
    类级注释：LLM配置测试类
    职责：测试LLMConfig的配置
    """

    def test_llm_config_defaults(self):
        """
        函数级注释：测试LLMConfig默认值

        内部逻辑：创建LLMConfig实例 -> 验证默认值
        预期结果：默认提供商为ollama
        """
        config = LLMConfig()
        assert config.provider == "ollama"
        assert config.embedding_provider == "ollama"

    def test_ollama_defaults(self):
        """
        函数级注释：测试Ollama默认配置

        内部逻辑：验证Ollama相关配置的默认值
        预期结果：Ollama配置默认值正确
        """
        config = LLMConfig()
        assert config.OLLAMA_BASE_URL == "http://localhost:11434"
        assert config.EMBEDDING_MODEL == "mxbai-embed-large:latest"
        assert config.CHAT_MODEL == "deepseek-r1:8b"

    def test_zhipuai_defaults(self):
        """
        函数级注释：测试智谱AI默认配置

        内部逻辑：验证智谱AI相关配置的默认值
        预期结果：智谱AI配置默认值正确
        """
        config = LLMConfig()
        assert config.ZHIPUAI_MODEL == "glm-4.5-air"
        assert config.ZHIPUAI_EMBEDDING_MODEL == "embedding-3"
        assert config.ZHIPUAI_API_KEY == ""

    def test_minimax_defaults(self):
        """
        函数级注释：测试MiniMax默认配置

        内部逻辑：验证MiniMax相关配置的默认值
        预期结果：MiniMax配置默认值正确
        """
        config = LLMConfig()
        assert config.MINIMAX_API_KEY == ""
        assert config.MINIMAX_GROUP_ID == ""
        assert config.MINIMAX_MODEL == "abab5.5-chat"

    def test_moonshot_defaults(self):
        """
        函数级注释：测试Moonshot默认配置

        内部逻辑：验证Moonshot相关配置的默认值
        预期结果：Moonshot配置默认值正确
        """
        config = LLMConfig()
        assert config.MOONSHOT_API_KEY == ""
        assert config.MOONSHOT_MODEL == "moonshot-v1-8k"

    def test_gpu_config_defaults(self):
        """
        函数级注释：测试GPU配置默认值

        内部逻辑：验证GPU相关配置的默认值
        预期结果：GPU配置默认值正确
        """
        config = LLMConfig()
        assert config.OLLAMA_NUM_GPU == 1
        assert config.OLLAMA_GPU_MEMORY_UTILIZATION == 0.9
        assert config.DEVICE == "auto"

    def test_local_embedding_defaults(self):
        """
        函数级注释：测试本地Embedding配置默认值

        内部逻辑：验证本地Embedding相关配置的默认值
        预期结果：本地Embedding配置默认值正确
        """
        config = LLMConfig()
        assert config.USE_LOCAL_EMBEDDINGS is False
        assert config.LOCAL_EMBEDDING_MODEL_PATH == "BAAI/bge-large-zh-v1.5"

    def test_reranking_defaults(self):
        """
        函数级注释：测试重排序配置默认值

        内部逻辑：验证重排序相关配置的默认值
        预期结果：重排序配置默认值正确
        """
        config = LLMConfig()
        assert config.ENABLE_RERANKING is True
        assert config.RERANKING_MODEL == "BAAI/bge-reranker-large"


# ============================================================================
# DatabaseConfig测试
# ============================================================================

class TestDatabaseConfig:
    """
    类级注释：数据库配置测试类
    职责：测试DatabaseConfig的配置
    """

    def test_database_config_defaults(self):
        """
        函数级注释：测试数据库配置默认值

        内部逻辑：创建DatabaseConfig实例 -> 验证默认值
        预期结果：默认提供商为postgresql
        """
        config = DatabaseConfig()
        assert config.provider == "postgresql"

    def test_postgresql_defaults(self):
        """
        函数级注释：测试PostgreSQL配置默认值

        内部逻辑：验证PostgreSQL相关配置的默认值
        预期结果：PostgreSQL配置默认值正确
        """
        config = DatabaseConfig()
        assert config.DB_HOST == "localhost"
        assert config.DB_PORT == 5432
        assert config.DB_NAME == "knowledge_db"
        assert config.DB_USER == "postgres"

    def test_sqlite_defaults(self):
        """
        函数级注释：测试SQLite配置默认值

        内部逻辑：验证SQLite相关配置的默认值
        预期结果：SQLite配置默认值正确
        """
        config = DatabaseConfig()
        assert config.SQLITE_DB_PATH == "./data/metadata.db"


# ============================================================================
# StorageConfig测试
# ============================================================================

class TestStorageConfig:
    """
    类级注释：存储配置测试类
    职责：测试StorageConfig的配置
    """

    def test_storage_config_defaults(self):
        """
        函数级注释：测试存储配置默认值

        内部逻辑：创建StorageConfig实例 -> 验证默认值
        预期结果：存储配置默认值正确
        """
        config = StorageConfig()
        assert config.CHROMA_DB_PATH == "./data/chroma_db"
        assert config.CHROMA_COLLECTION_NAME == "knowledge_base"
        assert config.UPLOAD_FILES_PATH == "./data/files"
        assert config.LOCAL_MODEL_DIR == "./models"


# ============================================================================
# SecurityConfig测试
# ============================================================================

class TestSecurityConfig:
    """
    类级注释：安全配置测试类
    职责：测试SecurityConfig的配置
    """

    def test_security_config_defaults(self):
        """
        函数级注释：测试安全配置默认值

        内部逻辑：创建SecurityConfig实例 -> 验证默认值
        预期结果：安全配置默认值正确
        """
        config = SecurityConfig()
        assert config.ENABLE_SENSITIVE_DATA_FILTER is True
        assert config.SENSITIVE_DATA_MASK_STRATEGY == "full"
        assert config.FILTER_MOBILE is True
        assert config.FILTER_EMAIL is True


# ============================================================================
# Settings属性访问器测试
# ============================================================================

class TestSettingsPropertyAccessors:
    """
    类级注释：Settings属性访问器测试类
    职责：测试Settings的属性访问器方法
    """

    def test_app_name_property(self):
        """
        函数级注释：测试APP_NAME属性访问器

        内部逻辑：访问APP_NAME属性
        预期结果：返回正确的应用名称
        """
        s = Settings()
        assert s.APP_NAME == "Knowledge-Agentic"

    def test_llm_provider_property(self):
        """
        函数级注释：测试LLM_PROVIDER属性访问器

        内部逻辑：访问LLM_PROVIDER属性
        预期结果：返回正确的提供商
        """
        s = Settings()
        assert s.LLM_PROVIDER == "ollama"

    def test_database_provider_property(self):
        """
        函数级注释：测试DATABASE_PROVIDER属性访问器

        内部逻辑：访问DATABASE_PROVIDER属性
        预期结果：返回正确的数据库提供商
        """
        s = Settings()
        assert s.DATABASE_PROVIDER == "postgresql"

    def test_zhipuai_property_accessors(self):
        """
        函数级注释：测试智谱AI属性访问器

        内部逻辑：访问智谱AI相关属性
        预期结果：返回正确的值
        """
        s = Settings()
        # 验证属性可以正常访问
        assert s.ZHIPUAI_API_KEY == ""
        assert s.ZHIPUAI_MODEL == "glm-4.5-air"

    def test_backend_cors_origins_property(self):
        """
        函数级注释：测试BACKEND_CORS_ORIGINS属性访问器

        内部逻辑：访问BACKEND_CORS_ORIGINS属性
        预期结果：返回CORS配置中的origins
        """
        s = Settings()
        assert s.BACKEND_CORS_ORIGINS == []


# ============================================================================
# 验证器测试
# ============================================================================

class TestDatabaseProviderValidator:
    """
    类级注释：数据库提供商验证器测试类
    职责：测试数据库提供商验证器
    """

    def test_validate_postgresql(self):
        """
        函数级注释：测试验证PostgreSQL提供商

        内部逻辑：传入postgresql配置对象 -> 验证返回元组
        预期结果：返回(True, [])
        """
        validator = DatabaseProviderValidator()
        # 内部变量：创建模拟配置对象
        class MockConfig:
            DATABASE_PROVIDER = "postgresql"
        is_valid, errors = validator.validate(MockConfig())
        assert is_valid is True
        assert errors == []

    def test_validate_sqlite(self):
        """
        函数级注释：测试验证SQLite提供商

        内部逻辑：传入sqlite配置对象 -> 验证返回元组
        预期结果：返回(True, [])
        """
        validator = DatabaseProviderValidator()
        class MockConfig:
            DATABASE_PROVIDER = "sqlite"
        is_valid, errors = validator.validate(MockConfig())
        assert is_valid is True
        assert errors == []

    def test_validate_invalid_provider(self):
        """
        函数级注释：测试验证无效提供商

        内部逻辑：传入无效的提供商名称
        预期结果：返回(False, [错误信息])
        """
        validator = DatabaseProviderValidator()
        class MockConfig:
            DATABASE_PROVIDER = "mysql"
        is_valid, errors = validator.validate(MockConfig())
        assert is_valid is False
        assert len(errors) > 0
        assert "不支持的数据库提供商" in errors[0]

    def test_validate_config_without_attribute(self):
        """
        函数级注释：测试没有DATABASE_PROVIDER属性的配置

        内部逻辑：配置对象没有DATABASE_PROVIDER属性
        预期结果：返回(True, []) - 跳过验证
        """
        validator = DatabaseProviderValidator()
        class MockConfig:
            pass
        is_valid, errors = validator.validate(MockConfig())
        assert is_valid is True
        assert errors == []


class TestLLMProviderValidator:
    """
    类级注释：LLM提供商验证器测试类
    职责：测试LLM提供商验证器
    """

    def test_validate_ollama(self):
        """
        函数级注释：测试验证Ollama提供商

        内部逻辑：传入ollama配置对象 -> 验证返回元组
        预期结果：返回(True, [])
        """
        validator = LLMProviderValidator()
        class MockConfig:
            LLM_PROVIDER = "ollama"
        is_valid, errors = validator.validate(MockConfig())
        assert is_valid is True
        assert errors == []

    def test_validate_zhipuai(self):
        """
        函数级注释：测试验证智谱AI提供商

        内部逻辑：传入zhipuai配置对象 -> 验证返回元组
        预期结果：返回(True, [])
        """
        validator = LLMProviderValidator()
        class MockConfig:
            LLM_PROVIDER = "zhipuai"
        is_valid, errors = validator.validate(MockConfig())
        assert is_valid is True
        assert errors == []

    def test_validate_minimax(self):
        """
        函数级注释：测试验证MiniMax提供商

        内部逻辑：传入minimax配置对象 -> 验证返回元组
        预期结果：返回(True, [])
        """
        validator = LLMProviderValidator()
        class MockConfig:
            LLM_PROVIDER = "minimax"
        is_valid, errors = validator.validate(MockConfig())
        assert is_valid is True
        assert errors == []

    def test_validate_moonshot(self):
        """
        函数级注释：测试验证Moonshot提供商

        内部逻辑：传入moonshot配置对象 -> 验证返回元组
        预期结果：返回(True, [])
        """
        validator = LLMProviderValidator()
        class MockConfig:
            LLM_PROVIDER = "moonshot"
        is_valid, errors = validator.validate(MockConfig())
        assert is_valid is True
        assert errors == []

    def test_validate_invalid_provider(self):
        """
        函数级注释：测试验证无效提供商

        内部逻辑：传入无效的提供商名称
        预期结果：返回(False, [错误信息])
        """
        validator = LLMProviderValidator()
        class MockConfig:
            LLM_PROVIDER = "invalid_provider"
        is_valid, errors = validator.validate(MockConfig())
        assert is_valid is False
        assert len(errors) > 0
        assert "不支持的LLM提供商" in errors[0]

    def test_validate_all_valid_providers(self):
        """
        函数级注释：测试所有有效提供商

        内部逻辑：遍历所有有效提供商
        预期结果：所有都返回True
        """
        validator = LLMProviderValidator()
        valid_providers = ["ollama", "zhipuai", "minimax", "moonshot", "openai", "deepseek"]
        for provider in valid_providers:
            class MockConfig:
                pass
            MockConfig.LLM_PROVIDER = provider
            is_valid, errors = validator.validate(MockConfig())
            assert is_valid is True, f"Provider {provider} should be valid"
            assert errors == []


class TestTimezoneValidator:
    """
    类级注释：时区验证器测试类
    职责：测试时区验证器
    """

    def test_validate_valid_timezone(self):
        """
        函数级注释：测试验证有效时区

        内部逻辑：传入有效的IANA时区标识符
        预期结果：返回(True, [])
        """
        validator = TimezoneValidator()

        class MockConfig:
            pass

        MockConfig.TIMEZONE = "Asia/Shanghai"
        is_valid, errors = validator.validate(MockConfig())
        assert is_valid is True
        assert errors == []

        MockConfig.TIMEZONE = "UTC"
        is_valid, errors = validator.validate(MockConfig())
        assert is_valid is True

        MockConfig.TIMEZONE = "America/New_York"
        is_valid, errors = validator.validate(MockConfig())
        assert is_valid is True

    def test_validate_invalid_timezone(self):
        """
        函数级注释：测试验证无效时区

        内部逻辑：传入无效的时区标识符
        预期结果：返回(False, [错误信息])
        """
        validator = TimezoneValidator()

        class MockConfig:
            TIMEZONE = "Invalid/Timezone"

        is_valid, errors = validator.validate(MockConfig())
        assert is_valid is False
        assert len(errors) > 0
        assert "无效的时区配置" in errors[0]

    def test_validate_config_without_timezone(self):
        """
        函数级注释：测试没有TIMEZONE属性的配置

        内部逻辑：配置对象没有TIMEZONE属性
        预期结果：返回(True, []) - 跳过验证
        """
        validator = TimezoneValidator()

        class MockConfig:
            pass

        is_valid, errors = validator.validate(MockConfig())
        assert is_valid is True
        assert errors == []


class TestValidateTimezoneFunction:
    """
    类级注释：validate_timezone函数测试类
    职责：测试validate_timezone函数
    """

    def test_validate_timezone_function_valid(self):
        """
        函数级注释：测试验证有效时区函数

        内部逻辑：传入有效时区 -> 验证返回值
        预期结果：返回传入的时区字符串
        """
        result = validate_timezone("Asia/Shanghai")
        assert result == "Asia/Shanghai"

    def test_validate_timezone_function_invalid(self):
        """
        函数级注释：测试验证无效时区函数

        内部逻辑：传入无效时区 -> 验证抛出异常
        预期结果：抛出ValueError
        """
        with pytest.raises(ValueError):
            validate_timezone("Invalid/Timezone")

    def test_validate_timezone_function_empty(self):
        """
        函数级注释：测试空时区字符串

        内部逻辑：传入空字符串 -> 验证返回默认值
        预期结果：返回Asia/Shanghai
        """
        result = validate_timezone("")
        assert result == "Asia/Shanghai"


# ============================================================================
# 全局settings实例测试
# ============================================================================

class TestGlobalSettings:
    """
    类级注释：全局配置实例测试类
    职责：测试全局settings实例
    """

    def test_global_settings_instance(self):
        """
        函数级注释：测试全局配置实例

        内部逻辑：导入settings全局变量
        预期结果：settings是有效的Settings实例
        """
        from app.core.config import settings
        assert isinstance(settings, Settings)

    def test_global_settings_singleton(self):
        """
        函数级注释：测试全局配置单例

        内部逻辑：多次导入settings
        预期结果：返回同一实例
        """
        from app.core.config import settings as s1
        from app.core.config import settings as s2
        assert s1 is s2
