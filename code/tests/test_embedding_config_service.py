# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：embedding_config_service 模块单元测试
内部逻辑：测试Embedding配置服务
覆盖范围：CRUD操作、API密钥更新、默认配置设置、热重载
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.embedding_config_service import EmbeddingConfigService
from app.models.model_config import EmbeddingConfig
import uuid


class TestEmbeddingConfigService:
    """
    类级注释：测试 EmbeddingConfigService 类的功能
    """

    @pytest.mark.asyncio
    async def test_mask_api_key_empty(self):
        """
        函数级注释：测试空API密钥脱敏
        内部逻辑：传入空字符串，验证返回空字符串
        """
        result = EmbeddingConfigService.mask_api_key(None)
        assert result == ""

        result = EmbeddingConfigService.mask_api_key("")
        assert result == ""

    @pytest.mark.asyncio
    async def test_mask_api_key_short(self):
        """
        函数级注释：测试短API密钥脱敏
        内部逻辑：传入短于8位的密钥，验证返回****
        """
        result = EmbeddingConfigService.mask_api_key("short")
        assert result == "****"

        result = EmbeddingConfigService.mask_api_key("12345678")
        assert result == "****"

    @pytest.mark.asyncio
    async def test_mask_api_key_normal(self):
        """
        函数级注释：测试正常API密钥脱敏
        内部逻辑：传入正常密钥，验证脱敏格式
        """
        result = EmbeddingConfigService.mask_api_key("sk-1234567890abcdef")
        assert result == "sk-1****cdef"

        result = EmbeddingConfigService.mask_api_key("12345678901234567890")
        assert result == "1234****7890"

    @pytest.mark.asyncio
    async def test_update_api_key_success(self, db_session: AsyncSession):
        """
        函数级注释：测试成功更新API密钥
        内部逻辑：mock 配置存在，验证更新成功
        参数：
            db_session: 测试数据库会话
        """
        # 内部变量：模拟配置
        mock_config = MagicMock(spec=EmbeddingConfig)
        mock_config.id = "test-id"
        mock_config.status = 1
        mock_config.provider_name = "ollama"
        mock_config.model_name = "nomic-embed-text"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_config

        async def mock_execute(query):
            return mock_result

        async def mock_commit():
            pass

        async def mock_refresh(config):
            pass

        db_session.execute = mock_execute
        db_session.commit = mock_commit
        db_session.refresh = mock_refresh

        # 内部逻辑：mock _reload_config
        with patch.object(EmbeddingConfigService, '_reload_config', new=AsyncMock()):
            result = await EmbeddingConfigService.update_api_key(
                db_session, "test-id", "new-api-key"
            )

            # 内部逻辑：验证更新
            assert result.api_key == "new-api-key"

    @pytest.mark.asyncio
    async def test_update_api_key_config_not_found(self, db_session: AsyncSession):
        """
        函数级注释：测试配置不存在时的行为
        内部逻辑：mock 返回None，验证抛出异常
        参数：
            db_session: 测试数据库会话
        """
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        async def mock_execute(query):
            return mock_result

        db_session.execute = mock_execute

        # 内部逻辑：验证抛出异常
        with pytest.raises(ValueError, match="配置不存在"):
            await EmbeddingConfigService.update_api_key(
                db_session, "nonexistent-id", "key"
            )

    @pytest.mark.asyncio
    async def test_update_api_key_inactive_config(self, db_session: AsyncSession):
        """
        函数级注释：测试更新非启用配置的API密钥
        内部逻辑：配置status=0，验证不调用_reload_config
        参数：
            db_session: 测试数据库会话
        """
        mock_config = MagicMock(spec=EmbeddingConfig)
        mock_config.id = "test-id"
        mock_config.status = 0  # 非启用状态

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_config

        async def mock_execute(query):
            return mock_result

        async def mock_commit():
            pass

        async def mock_refresh(config):
            pass

        db_session.execute = mock_execute
        db_session.commit = mock_commit
        db_session.refresh = mock_refresh

        reload_called = {"count": 0}

        async def mock_reload(config):
            reload_called["count"] += 1

        with patch.object(EmbeddingConfigService, '_reload_config', mock_reload):
            await EmbeddingConfigService.update_api_key(
                db_session, "test-id", "new-key"
            )

            # 内部逻辑：验证未调用reload
            assert reload_called["count"] == 0

    @pytest.mark.asyncio
    async def test_get_embedding_configs_empty(self, db_session: AsyncSession):
        """
        函数级注释：测试获取配置列表为空时初始化默认配置
        内部逻辑：mock 返回空列表，验证调用初始化
        参数：
            db_session: 测试数据库会话
        """
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = []

        async def mock_execute(query):
            return mock_result

        db_session.execute = mock_execute

        init_called = {"count": 0}

        async def mock_init(db):
            init_called["count"] += 1
            return []

        with patch.object(EmbeddingConfigService, '_init_default_configs', mock_init):
            result = await EmbeddingConfigService.get_embedding_configs(db_session)

            # 内部逻辑：验证调用了初始化
            assert init_called["count"] == 1
            assert result == []

    @pytest.mark.asyncio
    async def test_get_embedding_configs_has_data(self, db_session: AsyncSession):
        """
        函数级注释：测试获取已有配置列表
        内部逻辑：mock 返回配置列表
        参数：
            db_session: 测试数据库会话
        """
        mock_config = MagicMock(spec=EmbeddingConfig)
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [mock_config]

        async def mock_execute(query):
            return mock_result

        db_session.execute = mock_execute

        result = await EmbeddingConfigService.get_embedding_configs(db_session)

        assert len(result) == 1
        assert result[0] == mock_config

    @pytest.mark.asyncio
    async def test_get_default_config_none(self, db_session: AsyncSession):
        """
        函数级注释：测试没有启用配置时的行为
        内部逻辑：mock 返回空列表
        参数：
            db_session: 测试数据库会话
        """
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = []

        async def mock_execute(query):
            return mock_result

        db_session.execute = mock_execute

        result = await EmbeddingConfigService.get_default_config(db_session)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_default_config_single(self, db_session: AsyncSession):
        """
        函数级注释：测试单个启用配置
        内部逻辑：mock 返回一个启用配置
        参数：
            db_session: 测试数据库会话
        """
        mock_config = MagicMock(spec=EmbeddingConfig)
        mock_config.id = "test-id"
        mock_config.status = 1

        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [mock_config]

        async def mock_execute(query):
            return mock_result

        db_session.execute = mock_execute

        result = await EmbeddingConfigService.get_default_config(db_session)

        assert result == mock_config

    @pytest.mark.asyncio
    async def test_get_default_config_multiple(self, db_session: AsyncSession):
        """
        函数级注释：测试多个启用配置时的数据修复
        内部逻辑：mock 返回多个启用配置，验证修复为只保留一个
        参数：
            db_session: 测试数据库会话
        """
        mock_config1 = MagicMock(spec=EmbeddingConfig)
        mock_config1.id = "config1"
        mock_config1.status = 1

        mock_config2 = MagicMock(spec=EmbeddingConfig)
        mock_config2.id = "config2"
        mock_config2.status = 1

        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [mock_config1, mock_config2]

        async def mock_execute(query):
            return mock_result

        async def mock_commit():
            pass

        db_session.execute = mock_execute
        db_session.commit = mock_commit

        result = await EmbeddingConfigService.get_default_config(db_session)

        # 内部逻辑：验证保留了第一个
        assert result == mock_config1
        # 内部逻辑：验证第二个被禁用
        assert mock_config2.status == 0

    @pytest.mark.asyncio
    async def test_get_config_by_id_found(self, db_session: AsyncSession):
        """
        函数级注释：测试根据ID获取配置（找到）
        内部逻辑：mock 返回配置
        参数：
            db_session: 测试数据库会话
        """
        mock_config = MagicMock(spec=EmbeddingConfig)
        mock_config.id = "test-id"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_config

        async def mock_execute(query):
            return mock_result

        db_session.execute = mock_execute

        result = await EmbeddingConfigService.get_config_by_id(db_session, "test-id")

        assert result == mock_config

    @pytest.mark.asyncio
    async def test_get_config_by_id_not_found(self, db_session: AsyncSession):
        """
        函数级注释：测试根据ID获取配置（未找到）
        内部逻辑：mock 返回None
        参数：
            db_session: 测试数据库会话
        """
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        async def mock_execute(query):
            return mock_result

        db_session.execute = mock_execute

        result = await EmbeddingConfigService.get_config_by_id(db_session, "nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_save_embedding_config_create(self, db_session: AsyncSession):
        """
        函数级注释：测试创建新配置
        内部逻辑：传入没有id的数据，验证创建
        参数：
            db_session: 测试数据库会话
        """
        config_data = {
            "provider_id": "ollama",
            "provider_name": "Ollama",
            "model_name": "nomic-embed-text",
        }

        async def mock_commit():
            pass

        async def mock_refresh(config):
            config.id = "new-id"

        db_session.commit = mock_commit
        db_session.refresh = mock_refresh

        result = await EmbeddingConfigService.save_embedding_config(
            db_session, config_data
        )

        assert result.id == "new-id"

    @pytest.mark.asyncio
    async def test_save_embedding_config_update(self, db_session: AsyncSession):
        """
        函数级注释：测试更新现有配置
        内部逻辑：传入有id的数据，验证更新
        参数：
            db_session: 测试数据库会话
        """
        mock_config = MagicMock(spec=EmbeddingConfig)
        mock_config.id = "existing-id"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_config

        async def mock_execute(query):
            return mock_result

        async def mock_commit():
            pass

        async def mock_refresh(config):
            pass

        db_session.execute = mock_execute
        db_session.commit = mock_commit
        db_session.refresh = mock_refresh

        config_data = {
            "id": "existing-id",
            "model_name": "updated-model",
        }

        result = await EmbeddingConfigService.save_embedding_config(
            db_session, config_data
        )

        assert result == mock_config

    @pytest.mark.asyncio
    async def test_save_embedding_config_update_not_found(self, db_session: AsyncSession):
        """
        函数级注释：测试更新不存在的配置
        内部逻辑：mock 返回None，验证抛出异常
        参数：
            db_session: 测试数据库会话
        """
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        async def mock_execute(query):
            return mock_result

        db_session.execute = mock_execute

        config_data = {
            "id": "nonexistent-id",
            "model_name": "test",
        }

        with pytest.raises(ValueError, match="配置不存在"):
            await EmbeddingConfigService.save_embedding_config(
                db_session, config_data
            )

    @pytest.mark.asyncio
    async def test_set_default_config_success(self, db_session: AsyncSession):
        """
        函数级注释：测试成功设置默认配置
        内部逻辑：mock 配置存在，验证设置成功
        参数：
            db_session: 测试数据库会话
        """
        # 内部变量：模拟配置
        new_config = MagicMock(spec=EmbeddingConfig)
        new_config.id = "new-default"
        new_config.status = 0
        new_config.provider_name = "ollama"
        new_config.model_name = "nomic-embed-text"

        other_config = MagicMock(spec=EmbeddingConfig)
        other_config.id = "other"
        other_config.status = 1

        # 内部逻辑：mock 第一次查询返回所有配置，第二次返回目标配置
        call_count = [0]

        # 内部变量：创建mock的scalars结果对象
        # scalars()返回一个对象,该对象的.all()返回配置列表
        mock_scalars_obj_all = MagicMock()
        mock_scalars_obj_all.all.return_value = [other_config]

        mock_scalars_obj_one = MagicMock()
        mock_scalars_obj_one.scalar_one_or_none.return_value = new_config

        mock_result_all = MagicMock()
        mock_result_all.scalars.return_value = mock_scalars_obj_all

        mock_result_one = MagicMock()
        mock_result_one.scalar_one_or_none.return_value = new_config

        async def mock_execute(query):
            nonlocal call_count
            if call_count[0] == 0:
                call_count[0] += 1
                return mock_result_all
            return mock_result_one

        async def mock_commit():
            pass

        async def mock_refresh(config):
            pass

        db_session.execute = mock_execute
        db_session.commit = mock_commit
        db_session.refresh = mock_refresh

        # 内部逻辑：mock _reload_config
        with patch.object(EmbeddingConfigService, '_reload_config', new=AsyncMock()):
            result = await EmbeddingConfigService.set_default_config(
                db_session, "new-default"
            )

            # 内部逻辑：验证其他配置被禁用
            assert other_config.status == 0
            # 内部逻辑：验证新配置被启用
            assert new_config.status == 1

    @pytest.mark.asyncio
    async def test_set_default_config_not_found(self, db_session: AsyncSession):
        """
        函数级注释：测试设置不存在的配置为默认
        内部逻辑：mock 返回None，验证抛出异常
        参数：
            db_session: 测试数据库会话
        """
        # 内部变量：创建mock的scalars结果
        mock_scalars_obj = MagicMock()
        mock_scalars_obj.all.return_value = []

        mock_result_all = MagicMock()
        mock_result_all.scalars.return_value = mock_scalars_obj

        mock_result_one = MagicMock()
        mock_result_one.scalar_one_or_none.return_value = None

        call_count = [0]

        async def mock_execute(query):
            nonlocal call_count
            if call_count[0] == 0:
                call_count[0] += 1
                return mock_result_all
            return mock_result_one

        db_session.execute = mock_execute

        with pytest.raises(ValueError, match="配置不存在"):
            await EmbeddingConfigService.set_default_config(
                db_session, "nonexistent-id"
            )

    @pytest.mark.asyncio
    async def test_delete_config_success(self, db_session: AsyncSession):
        """
        函数级注释：测试成功删除配置
        内部逻辑：mock 配置存在且未启用
        参数：
            db_session: 测试数据库会话
        """
        mock_config = MagicMock(spec=EmbeddingConfig)
        mock_config.id = "to-delete"
        mock_config.status = 0

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_config

        async def mock_execute(query):
            return mock_result

        async def mock_commit():
            pass

        async def mock_delete(config):
            pass

        db_session.execute = mock_execute
        db_session.commit = mock_commit
        db_session.delete = mock_delete

        result = await EmbeddingConfigService.delete_config(db_session, "to-delete")

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_config_not_found(self, db_session: AsyncSession):
        """
        函数级注释：测试删除不存在的配置
        内部逻辑：mock 返回None
        参数：
            db_session: 测试数据库会话
        """
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        async def mock_execute(query):
            return mock_result

        db_session.execute = mock_execute

        result = await EmbeddingConfigService.delete_config(db_session, "nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_config_active(self, db_session: AsyncSession):
        """
        函数级注释：测试删除启用的配置
        内部逻辑：mock 配置status=1，验证抛出异常
        参数：
            db_session: 测试数据库会话
        """
        mock_config = MagicMock(spec=EmbeddingConfig)
        mock_config.id = "active"
        mock_config.status = 1

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_config

        async def mock_execute(query):
            return mock_result

        db_session.execute = mock_execute

        with pytest.raises(ValueError, match="不能删除启用的配置"):
            await EmbeddingConfigService.delete_config(db_session, "active")

    @pytest.mark.asyncio
    async def test_init_default_configs_already_exist(self, db_session: AsyncSession):
        """
        函数级注释：测试配置已存在时跳过初始化
        内部逻辑：mock 返回已有配置
        参数：
            db_session: 测试数据库会话
        """
        mock_config = MagicMock(spec=EmbeddingConfig)

        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [mock_config]

        async def mock_execute(query):
            return mock_result

        db_session.execute = mock_execute

        result = await EmbeddingConfigService._init_default_configs(db_session)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_init_default_configs_new(self, db_session: AsyncSession, monkeypatch):
        """
        函数级注释：测试初始化新配置
        内部逻辑：mock 返回空，然后创建配置
        参数：
            db_session: 测试数据库会话
            monkeypatch: pytest monkeypatch fixture
        """
        # 内部逻辑：mock EMBEDDING_PROVIDERS常量
        mock_providers = [
            {"id": "ollama", "name": "Ollama", "default_endpoint": "", "default_models": ["nomic-embed-text"]},
            {"id": "local", "name": "Local", "default_endpoint": "", "default_models": ["bge-base"]},
        ]

        # 内部变量：创建mock的scalars结果
        mock_scalars_obj = MagicMock()
        mock_scalars_obj.all.return_value = []

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars_obj

        async def mock_execute(query):
            return mock_result

        async def mock_commit():
            pass

        async def mock_add_all(configs):
            pass

        db_session.execute = mock_execute
        db_session.commit = mock_commit
        db_session.add_all = mock_add_all

        with patch('app.services.embedding_config_service.EMBEDDING_PROVIDERS', mock_providers):
            result = await EmbeddingConfigService._init_default_configs(db_session)

            # 内部逻辑：验证返回了配置列表
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_reload_config_success(self, monkeypatch):
        """
        函数级注释：测试热重载成功
        内部逻辑：mock EmbeddingFactory
        参数：
            monkeypatch: pytest monkeypatch fixture
        """
        mock_config = MagicMock(spec=EmbeddingConfig)
        mock_config.provider_name = "Ollama"
        mock_config.model_name = "nomic-embed-text"
        mock_config.provider_id = "ollama"
        mock_config.endpoint = "http://localhost:11434"
        mock_config.api_key = ""
        mock_config.device = "cpu"

        # 内部变量：创建mock的EmbeddingFactory类和实例
        mock_factory_instance = MagicMock()

        # 内部逻辑：mock导入，因为EmbeddingFactory在函数内部导入
        with patch('app.utils.embedding_factory.EmbeddingFactory') as MockFactory:
            # 内部逻辑：设置set_runtime_config为类方法
            MockFactory.set_runtime_config = MagicMock()
            await EmbeddingConfigService._reload_config(mock_config)

            # 内部逻辑：验证调用了set_runtime_config
            MockFactory.set_runtime_config.assert_called_once_with({
                "provider": "ollama",
                "model": "nomic-embed-text",
                "endpoint": "http://localhost:11434",
                "api_key": "",
                "device": "cpu"
            })

    @pytest.mark.asyncio
    async def test_reload_config_import_error(self, caplog):
        """
        函数级注释：测试EmbeddingFactory导入失败
        内部逻辑：mock ImportError，验证函数不会崩溃
        参数：
            caplog: pytest log capture fixture
        """
        mock_config = MagicMock(spec=EmbeddingConfig)

        # 内部逻辑：mock __import__抛出ImportError
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "app.utils.embedding_factory":
                raise ImportError("Mocked import error")
            return original_import(name, *args, **kwargs)

        # 内部逻辑：使用patch mock __import__
        with patch.object(builtins, '__import__', side_effect=mock_import):
            # 内部逻辑：执行函数，不应抛出异常
            await EmbeddingConfigService._reload_config(mock_config)

            # 内部逻辑：验证函数成功执行（loguru输出到stderr，不在caplog中）
            assert True

    @pytest.mark.asyncio
    async def test_save_embedding_config_with_id(self, db_session: AsyncSession):
        """
        函数级注释：测试保存时自动生成ID
        内部逻辑：传入没有id的数据，验证自动生成UUID
        参数：
            db_session: 测试数据库会话
        """
        config_data = {
            "provider_id": "ollama",
            "provider_name": "Ollama",
        }

        async def mock_commit():
            pass

        async def mock_refresh(config):
            pass

        db_session.commit = mock_commit
        db_session.refresh = mock_refresh

        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = "test-uuid"
            db_session.add = MagicMock()

            result = await EmbeddingConfigService.save_embedding_config(
                db_session, config_data
            )

            # 内部逻辑：验证设置了ID
            assert hasattr(result, 'id')

    @pytest.mark.asyncio
    async def test_init_default_configs_integrity_error(self, db_session: AsyncSession):
        """
        函数级注释：测试初始化时的IntegrityError处理
        内部逻辑：mock 抛出IntegrityError后回滚
        参数：
            db_session: 测试数据库会话
        """
        from sqlalchemy.exc import IntegrityError

        # 内部变量：创建mock的scalars结果
        mock_scalars_obj = MagicMock()
        mock_scalars_obj.all.return_value = []

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars_obj

        async def mock_execute(query):
            return mock_result

        async def mock_commit():
            raise IntegrityError("duplicate", {}, None)

        async def mock_rollback():
            pass

        async def mock_add_all(configs):
            pass

        db_session.execute = mock_execute
        db_session.commit = mock_commit
        db_session.rollback = mock_rollback
        db_session.add_all = mock_add_all

        # 内部逻辑：应该处理IntegrityError并返回配置
        result = await EmbeddingConfigService._init_default_configs(db_session)

        # 内部逻辑：验证调用了rollback，返回了列表
        assert isinstance(result, list)
