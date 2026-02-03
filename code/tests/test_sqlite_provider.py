"""
文件级注释：SQLite Provider 测试
内部逻辑：补充测试用例以提高SQLite provider模块覆盖率
"""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from app.db.providers.sqlite import SQLiteProvider


class TestSQLiteProviderConnection:
    """
    类级注释：连接URL测试类
    """

    def test_get_connection_url_default(self):
        """
        函数级注释：测试获取默认连接URL
        """
        config = {"path": "./data/metadata.db"}
        provider = SQLiteProvider(config)
        url = provider.get_connection_url()
        assert url == "sqlite+aiosqlite:///data/metadata.db"

    def test_get_connection_url_custom_path(self):
        """
        函数级注释：测试自定义路径连接URL
        """
        config = {"path": "/custom/path/test.db"}
        provider = SQLiteProvider(config)
        url = provider.get_connection_url()
        assert url == "sqlite+aiosqlite:///custom/path/test.db"

    def test_get_connection_url_with_leading_slash(self):
        """
        函数级注释：测试带前导斜杠的路径
        """
        config = {"path": "/absolute/path.db"}
        provider = SQLiteProvider(config)
        url = provider.get_connection_url()
        assert url == "sqlite+aiosqlite:///absolute/path.db"

    def test_get_connection_url_with_leading_dot_slash(self):
        """
        函数级注释：测试带./前缀的路径
        """
        config = {"path": "./data/test.db"}
        provider = SQLiteProvider(config)
        url = provider.get_connection_url()
        # 应该移除./前缀
        assert url == "sqlite+aiosqlite:///data/test.db"

    def test_get_connection_url_memory(self):
        """
        函数级注释：测试内存数据库连接URL
        """
        config = {"path": ":memory:"}
        provider = SQLiteProvider(config)
        url = provider.get_connection_url()
        assert url == "sqlite+aiosqlite:///:memory:"


class TestSQLiteProviderEngineOptions:
    """
    类级注释：引擎选项测试类
    """

    def test_get_engine_options(self):
        """
        函数级注释：测试获取引擎选项
        """
        config = {"path": "./data/test.db"}
        provider = SQLiteProvider(config)
        options = provider.get_engine_options()
        assert options == {"echo": False}

    def test_get_engine_options_dict(self):
        """
        函数级注释：测试引擎选项是字典
        """
        config = {"path": "./data/test.db"}
        provider = SQLiteProvider(config)
        options = provider.get_engine_options()
        assert isinstance(options, dict)
        assert "echo" in options
        assert options["echo"] is False


class TestSQLiteProviderEnsureDatabase:
    """
    类级注释：数据库确保存在测试类
    """

    @pytest.mark.asyncio
    async def test_ensure_database_exists_creates_directory(self):
        """
        函数级注释：测试创建数据库目录
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "data", "test.db")
            config = {"path": db_path}
            provider = SQLiteProvider(config)

            await provider.ensure_database_exists()

            # 验证目录被创建
            expected_dir = os.path.join(temp_dir, "data")
            assert os.path.exists(expected_dir)

    @pytest.mark.asyncio
    async def test_ensure_database_exists_existing_directory(self):
        """
        函数级注释：测试目录已存在时不报错
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            config = {"path": db_path}
            provider = SQLiteProvider(config)

            # 不应抛出异常
            await provider.ensure_database_exists()

    @pytest.mark.asyncio
    async def test_ensure_database_exists_memory_db(self):
        """
        函数级注释：测试内存数据库不需要目录
        """
        config = {"path": ":memory:"}
        provider = SQLiteProvider(config)

        # 不应抛出异常
        await provider.ensure_database_exists()

    @pytest.mark.asyncio
    async def test_ensure_database_exists_nested_path(self):
        """
        函数级注释：测试嵌套路径目录创建
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "level1", "level2", "test.db")
            config = {"path": db_path}
            provider = SQLiteProvider(config)

            await provider.ensure_database_exists()

            # 验证所有目录被创建
            assert os.path.exists(os.path.join(temp_dir, "level1"))
            assert os.path.exists(os.path.join(temp_dir, "level1", "level2"))

    @pytest.mark.asyncio
    async def test_ensure_database_exists_relative_path(self):
        """
        函数级注释：测试相对路径目录创建
        """
        config = {"path": "./data/test.db"}
        provider = SQLiteProvider(config)

        with patch('os.makedirs') as mock_makedirs:
            await provider.ensure_database_exists()
            # 应该尝试创建目录
            assert mock_makedirs.called


class TestSQLiteProviderGetter:
    """
    类级注释：获取器方法测试类
    """

    def test_get_provider_name(self):
        """
        函数级注释：测试获取提供商名称
        """
        config = {"path": "./data/test.db"}
        provider = SQLiteProvider(config)
        name = provider.get_provider_name()
        assert name == "SQLite"

    def test_driver_constant(self):
        """
        函数级注释：测试驱动常量
        """
        assert SQLiteProvider.DRIVER == "aiosqlite"


class TestSQLiteProviderEdgeCases:
    """
    类级注释：边界条件测试类
    """

    def test_connection_url_empty_path(self):
        """
        函数级注释：测试空路径使用默认值
        """
        config = {}
        provider = SQLiteProvider(config)
        url = provider.get_connection_url()
        assert url == "sqlite+aiosqlite:///data/metadata.db"

    def test_connection_url_windows_path(self):
        """
        函数级注释：测试Windows风格路径
        """
        config = {"path": "C:\\data\\test.db"}
        provider = SQLiteProvider(config)
        url = provider.get_connection_url()
        assert "sqlite+aiosqlite:///" in url
        assert "C:" in url or "test.db" in url

    def test_engine_options_returns_new_dict(self):
        """
        函数级注释：测试每次调用返回新字典
        """
        config = {"path": "./data/test.db"}
        provider = SQLiteProvider(config)
        options1 = provider.get_engine_options()
        options2 = provider.get_engine_options()
        # 应该是不同的字典实例
        assert options1 is not options2
        assert options1 == options2


class TestSQLiteProviderIntegration:
    """
    类级注释：集成测试类
    """

    def test_inherits_from_base(self):
        """
        函数级注释：测试继承自BaseProvider
        """
        from app.db.providers.base import DatabaseProvider
        config = {"path": "./data/test.db"}
        provider = SQLiteProvider(config)
        assert isinstance(provider, DatabaseProvider)

    def test_config_property(self):
        """
        函数级注释：测试配置属性
        """
        config = {"path": "./test.db"}
        provider = SQLiteProvider(config)
        assert provider.config == config

    def test_all_required_methods(self):
        """
        函数级注释：测试实现所有必需方法
        """
        config = {"path": "./data/test.db"}
        provider = SQLiteProvider(config)
        assert hasattr(provider, 'get_connection_url')
        assert hasattr(provider, 'get_engine_options')
        assert hasattr(provider, 'ensure_database_exists')
        assert hasattr(provider, 'get_provider_name')
        assert callable(provider.get_connection_url)
        assert callable(provider.get_engine_options)
        assert callable(provider.ensure_database_exists)
        assert callable(provider.get_provider_name)
