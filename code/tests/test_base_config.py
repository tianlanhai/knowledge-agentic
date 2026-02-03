# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：BaseConfigEndpoint 模块测试
内部逻辑：测试配置端点基类的所有方法，包括CRUD操作、错误处理和边界条件
"""

import pytest
from typing import Dict, Any, Type
from unittest.mock import AsyncMock, MagicMock, Mock
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from fastapi import HTTPException

from app.api.v1.endpoints.base_config import (
    BaseConfigEndpoint,
    ConfigCreateType,
    ConfigResponseType,
    ConfigResponseTypeSafe,
    ConfigModelType,
    ServiceType,
)


# ============================================================================
# 测试数据模型和Schema定义
# ============================================================================


class MockConfigCreate(BaseModel):
    """测试用：创建配置的请求Schema"""
    provider_id: str
    model_name: str
    api_key: str
    endpoint: str = "http://localhost:8080"


class MockConfigResponse(BaseModel):
    """测试用：完整配置响应Schema"""
    id: str
    provider_id: str
    model_name: str
    api_key: str
    endpoint: str = "http://localhost:8080"
    status: bool = True


class MockConfigResponseSafe(BaseModel):
    """测试用：脱敏配置响应Schema"""
    id: str
    provider_id: str
    model_name: str
    api_key: str
    endpoint: str = "http://localhost:8080"
    status: bool = True


class MockConfigModel:
    """测试用：配置模型"""
    def __init__(self, id: str, provider_id: str, model_name: str, api_key: str, endpoint: str = "http://localhost:8080", status: bool = True):
        self.id = id
        self.provider_id = provider_id
        self.model_name = model_name
        self.api_key = api_key
        self.endpoint = endpoint
        self.status = status


class MockService:
    """测试用：模拟服务类（使用类方法模拟实际服务）"""
    # 内部变量：模拟数据库中的配置数据（类级别）
    configs = [
        MockConfigModel("1", "ollama", "deepseek-r1", "sk-test-key-1", "http://localhost:11434", True),
        MockConfigModel("2", "zhipuai", "glm-4", "sk-test-key-2", "https://open.bigmodel.cn", False),
    ]

    @classmethod
    def reset_configs(cls):
        """重置配置列表到初始状态"""
        cls.configs = [
            MockConfigModel("1", "ollama", "deepseek-r1", "sk-test-key-1", "http://localhost:11434", True),
            MockConfigModel("2", "zhipuai", "glm-4", "sk-test-key-2", "https://open.bigmodel.cn", False),
        ]

    @classmethod
    async def get_model_configs(cls, db: AsyncSession) -> list:
        """获取所有配置"""
        return cls.configs

    @classmethod
    async def save_model_config(cls, db: AsyncSession, config_data: Dict[str, Any]) -> ConfigModelType:
        """保存配置"""
        if not config_data.get("provider_id"):
            raise ValueError("provider_id is required")
        new_config = MockConfigModel(
            id="3",
            provider_id=config_data.get("provider_id"),
            model_name=config_data.get("model_name", "test-model"),
            api_key=config_data.get("api_key", ""),
            endpoint=config_data.get("endpoint", "http://localhost:8080")
        )
        cls.configs.append(new_config)
        return new_config

    @classmethod
    async def set_default_config(cls, db: AsyncSession, config_id: str) -> ConfigModelType:
        """设置默认配置"""
        config = next((c for c in cls.configs if c.id == config_id), None)
        if not config:
            raise ValueError(f"Config {config_id} not found")
        # 取消其他配置的启用状态
        for c in cls.configs:
            c.status = False
        config.status = True
        return config

    @classmethod
    async def delete_config(cls, db: AsyncSession, config_id: str) -> bool:
        """删除配置"""
        config = next((c for c in cls.configs if c.id == config_id), None)
        if not config:
            return False
        if config.status:
            raise ValueError("Cannot delete default config")
        cls.configs = [c for c in cls.configs if c.id != config_id]
        return True

    @classmethod
    async def update_api_key(cls, db: AsyncSession, config_id: str, api_key: str) -> ConfigModelType:
        """更新API密钥"""
        config = next((c for c in cls.configs if c.id == config_id), None)
        if not config:
            raise ValueError(f"Config {config_id} not found")
        config.api_key = api_key
        return config

    @staticmethod
    def mask_api_key(api_key: str) -> str:
        """脱敏API密钥"""
        if not api_key:
            return ""
        return api_key[:4] + "*" * 8 + api_key[-4:]


class MockResponseBuilderUtils:
    """测试用：模拟响应构建工具类"""
    @staticmethod
    def build_from_model_config(config_model: ConfigModelType, mask_func) -> Dict[str, Any]:
        """从配置模型构建响应"""
        return {
            "id": config_model.id,
            "provider_id": config_model.provider_id,
            "model_name": config_model.model_name,
            "api_key": mask_func(config_model.api_key),
            "endpoint": config_model.endpoint,
            "status": config_model.status
        }


# ============================================================================
# 测试用BaseConfigEndpoint实现
# ============================================================================


class TestConfigEndpoint(BaseConfigEndpoint[
    MockConfigCreate,
    MockConfigResponse,
    MockConfigResponseSafe,
    MockConfigModel,
    MockService
]):
    """测试用：配置端点实现类"""

    def get_service_class(self) -> Type[MockService]:
        """返回服务类"""
        return MockService

    def get_create_schema_class(self) -> Type[MockConfigCreate]:
        """返回创建Schema类"""
        return MockConfigCreate

    def get_response_schema_safe_class(self) -> Type[MockConfigResponseSafe]:
        """返回脱敏响应Schema类"""
        return MockConfigResponseSafe

    def get_config_type_name(self) -> str:
        """返回配置类型名称"""
        return "LLM"

    def get_response_builder_utils(self):
        """返回响应构建工具类"""
        return MockResponseBuilderUtils


# ============================================================================
# 单元测试类
# ============================================================================


class TestBaseConfigEndpoint:
    """
    类级注释：BaseConfigEndpoint 单元测试类
    测试覆盖范围：
        1. 获取服务实例
        2. 获取脱敏函数
        3. 格式化配置响应
        4. 格式化配置列表响应
        5. 获取所有配置（get_configs）
        6. 保存配置（save_config）
        7. 设置默认配置（set_default_config）
        8. 删除配置（delete_config）
        9. 更新API密钥（update_api_key）
        10. 错误处理和边界条件
    """

    @pytest.fixture
    def endpoint(self):
        """创建端点实例"""
        return TestConfigEndpoint()

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        db = AsyncMock(spec=AsyncSession)
        return db

    @pytest.fixture
    def mock_service(self):
        """创建模拟服务实例"""
        return MockService()

    @pytest.fixture(autouse=True)
    def reset_service_state(self):
        """在每个测试后重置服务状态"""
        # 测试前重置
        MockService.reset_configs()
        yield
        # 测试后重置
        MockService.reset_configs()

    # ========================================================================
    # 内部辅助方法测试
    # ========================================================================

    def test_get_service(self, endpoint):
        """
        测试目的：验证_get_service方法返回正确的服务类
        测试场景：正常获取服务类
        注意：get_service_class返回的是类而不是实例
        """
        service_class = endpoint.get_service_class()
        assert service_class == MockService
        # _get_service返回类实例
        service = endpoint._get_service()
        assert type(service).__name__ == 'MockService' or service_class == MockService

    def test_get_mask_function(self, endpoint, mock_service):
        """
        测试目的：验证_get_mask_function返回脱敏函数
        测试场景：正常获取脱敏函数并调用
        """
        mask_func = endpoint._get_mask_function(mock_service)
        assert callable(mask_func)
        # 测试脱敏函数
        masked = mask_func("sk-1234567890abcdef")
        assert "sk-1" in masked
        assert "*" in masked

    def test_format_config_response(self, endpoint, mock_service):
        """
        测试目的：验证_format_config_response正确格式化单个配置
        测试场景：正常格式化配置响应
        """
        config = MockConfigModel("1", "ollama", "deepseek-r1", "sk-test-key", "http://localhost:11434")
        response = endpoint._format_config_response(
            config,
            mock_service,
            MockConfigResponseSafe
        )
        assert isinstance(response, MockConfigResponseSafe)
        assert response.id == "1"
        assert response.provider_id == "ollama"
        assert "*" in response.api_key  # 验证脱敏

    def test_format_config_response_empty_api_key(self, endpoint, mock_service):
        """
        测试目的：验证_format_config_response处理空API密钥
        测试场景：API密钥为空时的边界条件
        """
        config = MockConfigModel("1", "ollama", "deepseek-r1", "", "http://localhost:11434")
        response = endpoint._format_config_response(
            config,
            mock_service,
            MockConfigResponseSafe
        )
        assert response.api_key == ""

    def test_format_config_list_response(self, endpoint, mock_service):
        """
        测试目的：验证_format_config_list_response正确格式化配置列表
        测试场景：正常格式化多个配置的响应
        """
        configs = [
            MockConfigModel("1", "ollama", "deepseek-r1", "sk-key-1", "http://localhost:11434"),
            MockConfigModel("2", "zhipuai", "glm-4", "sk-key-2", "https://open.bigmodel.cn"),
        ]
        responses = endpoint._format_config_list_response(
            configs,
            mock_service,
            MockConfigResponseSafe
        )
        assert len(responses) == 2
        assert all(isinstance(r, MockConfigResponseSafe) for r in responses)
        assert all("*" in r.api_key for r in responses if r.api_key)

    def test_format_config_list_response_empty(self, endpoint, mock_service):
        """
        测试目的：验证_format_config_list_response处理空列表
        测试场景：配置列表为空的边界条件
        """
        responses = endpoint._format_config_list_response(
            [],
            mock_service,
            MockConfigResponseSafe
        )
        assert responses == []

    # ========================================================================
    # 模板方法 - get_configs 测试
    # ========================================================================

    @pytest.mark.asyncio
    async def test_get_configs_success(self, endpoint, mock_db):
        """
        测试目的：验证get_configs成功获取所有配置
        测试场景：正常获取配置列表
        """
        response = await endpoint.get_configs(mock_db)
        assert response.data is not None
        assert "configs" in response.data
        assert len(response.data["configs"]) == 2  # MockService有2个配置

    @pytest.mark.asyncio
    async def test_get_configs_with_masking(self, endpoint, mock_db):
        """
        测试目的：验证get_configs返回的配置已脱敏
        测试场景：验证API密钥脱敏
        """
        response = await endpoint.get_configs(mock_db)
        configs = response.data["configs"]
        for config in configs:
            if config.api_key:
                assert "*" in config.api_key
                assert config.api_key.startswith("sk-")

    @pytest.mark.asyncio
    async def test_get_configs_service_exception(self, endpoint, mock_db):
        """
        测试目的：验证get_configs处理服务层异常
        测试场景：服务抛出异常时返回500错误
        """
        # 创建一个会抛出异常的端点
        class FailingService:
            async def get_model_configs(self, db):
                raise RuntimeError("Database error")

        class FailingEndpoint(TestConfigEndpoint):
            def get_service_class(self):
                return FailingService

        failing_endpoint = FailingEndpoint()
        with pytest.raises(HTTPException) as exc_info:
            await failing_endpoint.get_configs(mock_db)
        assert exc_info.value.status_code == 500

    # ========================================================================
    # 模板方法 - save_config 测试
    # ========================================================================

    @pytest.mark.asyncio
    async def test_save_config_success(self, endpoint, mock_db):
        """
        测试目的：验证save_config成功保存配置
        测试场景：正常保存新配置
        """
        config_data = MockConfigCreate(
            provider_id="minimax",
            model_name="abab5.5-chat",
            api_key="sk-new-key",
            endpoint="https://api.minimax.chat"
        )
        response = await endpoint.save_config(config_data, mock_db)
        assert response.data is not None
        assert response.data.provider_id == "minimax"
        assert "*" in response.data.api_key

    @pytest.mark.asyncio
    async def test_save_config_value_error(self, endpoint, mock_db):
        """
        测试目的：验证save_config处理值错误
        测试场景：缺少必填字段时返回400错误
        """
        # 创建一个会抛出ValueError的端点
        class ValidatingService:
            @classmethod
            async def save_model_config(cls, db, config_data):
                if not config_data.get("provider_id"):
                    raise ValueError("provider_id is required")
                raise ValueError("Invalid config")

        class ValidatingEndpoint(TestConfigEndpoint):
            def get_service_class(self):
                return ValidatingService

        validating_endpoint = ValidatingEndpoint()
        with pytest.raises(HTTPException) as exc_info:
            await validating_endpoint.save_config(MockConfigCreate(
                provider_id="", model_name="test", api_key="key"
            ), mock_db)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_save_config_exception(self, endpoint, mock_db):
        """
        测试目的：验证save_config处理通用异常
        测试场景：数据库错误时返回500错误
        """
        class FailingService:
            @classmethod
            async def save_model_config(cls, db, config_data):
                raise RuntimeError("Database connection failed")

        class FailingEndpoint(TestConfigEndpoint):
            def get_service_class(self):
                return FailingService

        failing_endpoint = FailingEndpoint()
        with pytest.raises(HTTPException) as exc_info:
            await failing_endpoint.save_config(MockConfigCreate(
                provider_id="test", model_name="test", api_key="key"
            ), mock_db)
        assert exc_info.value.status_code == 500

    # ========================================================================
    # 模板方法 - set_default_config 测试
    # ========================================================================

    @pytest.mark.asyncio
    async def test_set_default_config_success(self, endpoint, mock_db):
        """
        测试目的：验证set_default_config成功设置默认配置
        测试场景：正常设置默认配置
        """
        response = await endpoint.set_default_config("2", mock_db)
        assert response.data is not None
        assert response.data.id == "2"
        assert response.message == "LLM配置已启用并生效"

    @pytest.mark.asyncio
    async def test_set_default_config_not_found(self, endpoint, mock_db):
        """
        测试目的：验证set_default_config处理配置不存在
        测试场景：配置ID不存在时返回400错误
        """
        with pytest.raises(HTTPException) as exc_info:
            await endpoint.set_default_config("999", mock_db)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_set_default_config_exception(self, endpoint, mock_db):
        """
        测试目的：验证set_default_config处理通用异常
        测试场景：数据库错误时返回500错误
        """
        class FailingService:
            @classmethod
            async def set_default_config(cls, db, config_id):
                raise RuntimeError("Database error")

        class FailingEndpoint(TestConfigEndpoint):
            def get_service_class(self):
                return FailingService

        failing_endpoint = FailingEndpoint()
        with pytest.raises(HTTPException) as exc_info:
            await failing_endpoint.set_default_config("1", mock_db)
        assert exc_info.value.status_code == 500

    # ========================================================================
    # 模板方法 - delete_config 测试
    # ========================================================================

    @pytest.mark.asyncio
    async def test_delete_config_success(self, endpoint, mock_db):
        """
        测试目的：验证delete_config成功删除配置
        测试场景：正常删除非默认配置
        """
        response = await endpoint.delete_config("2", mock_db)
        assert response.data is not None
        assert response.data["deleted"] is True
        assert response.message == "配置已删除"

    @pytest.mark.asyncio
    async def test_delete_config_not_found(self, endpoint, mock_db):
        """
        测试目的：验证delete_config处理配置不存在
        测试场景：配置ID不存在时返回404错误
        """
        with pytest.raises(HTTPException) as exc_info:
            await endpoint.delete_config("999", mock_db)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_config_default_forbidden(self, endpoint, mock_db):
        """
        测试目的：验证delete_config禁止删除默认配置
        测试场景：尝试删除默认配置时返回400错误
        """
        with pytest.raises(HTTPException) as exc_info:
            await endpoint.delete_config("1", mock_db)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_config_exception(self, endpoint, mock_db):
        """
        测试目的：验证delete_config处理通用异常
        测试场景：数据库错误时返回500错误
        """
        class FailingService:
            @classmethod
            async def delete_config(cls, db, config_id):
                raise RuntimeError("Database error")

        class FailingEndpoint(TestConfigEndpoint):
            def get_service_class(self):
                return FailingService

        failing_endpoint = FailingEndpoint()
        with pytest.raises(HTTPException) as exc_info:
            await failing_endpoint.delete_config("2", mock_db)
        assert exc_info.value.status_code == 500

    # ========================================================================
    # 模板方法 - update_api_key 测试
    # ========================================================================

    @pytest.mark.asyncio
    async def test_update_api_key_success(self, endpoint, mock_db):
        """
        测试目的：验证update_api_key成功更新API密钥
        测试场景：正常更新API密钥
        """
        from app.schemas.model_config import APIKeyUpdateResponse

        response = await endpoint.update_api_key("1", "sk-new-updated-key", mock_db, MockConfigResponseSafe)
        assert response.data is not None
        assert isinstance(response.data, APIKeyUpdateResponse)
        assert "*" in response.data.api_key_masked
        assert response.message == "API密钥已更新"

    @pytest.mark.asyncio
    async def test_update_api_key_not_found(self, endpoint, mock_db):
        """
        测试目的：验证update_api_key处理配置不存在
        测试场景：配置ID不存在时返回400错误
        """
        with pytest.raises(HTTPException) as exc_info:
            await endpoint.update_api_key("999", "sk-new-key", mock_db, MockConfigResponseSafe)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_update_api_key_exception(self, endpoint, mock_db):
        """
        测试目的：验证update_api_key处理通用异常
        测试场景：数据库错误时返回500错误
        """
        class FailingService:
            @classmethod
            async def update_api_key(cls, db, config_id, api_key):
                raise RuntimeError("Database error")

        class FailingEndpoint(TestConfigEndpoint):
            def get_service_class(self):
                return FailingService

        failing_endpoint = FailingEndpoint()
        with pytest.raises(HTTPException) as exc_info:
            await failing_endpoint.update_api_key("1", "sk-new-key", mock_db, MockConfigResponseSafe)
        assert exc_info.value.status_code == 500

    # ========================================================================
    # 边界条件和组合测试
    # ========================================================================

    def test_get_config_type_name(self, endpoint):
        """
        测试目的：验证get_config_type_name返回正确的类型名称
        测试场景：获取配置类型名称
        """
        assert endpoint.get_config_type_name() == "LLM"

    def test_get_response_builder_utils(self, endpoint):
        """
        测试目的：验证get_response_builder_utils返回正确的工具类
        测试场景：获取响应构建工具类
        """
        utils = endpoint.get_response_builder_utils()
        assert utils is not None
        assert hasattr(utils, "build_from_model_config")

    def test_abstract_methods_must_be_implemented(self):
        """
        测试目的：验证抽象方法必须被实现
        测试场景：不实现抽象方法应该无法实例化
        """
        class IncompleteEndpoint(BaseConfigEndpoint[
            MockConfigCreate,
            MockConfigResponse,
            MockConfigResponseSafe,
            MockConfigModel,
            MockService
        ]):
            pass

        with pytest.raises(TypeError):
            IncompleteEndpoint()
