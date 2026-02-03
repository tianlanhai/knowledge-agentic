# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：app/core/middleware.py 模块全面测试
内部逻辑：测试ValidationChainMiddleware和create_validation_middleware函数
测试覆盖范围：
    - ValidationChainMiddleware.__init__
    - ValidationChainMiddleware.dispatch
    - 跳过路径验证
    - 验证成功路径
    - 验证失败路径
    - 异常处理路径
    - create_validation_middleware工厂函数
测试类型：单元测试 + 中间件测试
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import Request, Response, HTTPException
from starlette.types import ASGIApp


# ============================================================================
# 导入被测试模块
# ============================================================================

from app.core.middleware import (
    ValidationChainMiddleware,
    create_validation_middleware,
)
from app.core.validation_chain import (
    ValidationContext,
    ValidationResult,
    ValidationError,
    ValidationSeverity,
)


# ============================================================================
# ValidationChainMiddleware 初始化测试
# ============================================================================

class TestValidationChainMiddlewareInit:
    """测试ValidationChainMiddleware初始化"""

    @pytest.fixture
    def mock_app(self):
        """模拟ASGI应用"""
        return AsyncMock(spec=ASGIApp)

    def test_init_with_default_params(self, mock_app):
        """测试使用默认参数初始化"""
        middleware = ValidationChainMiddleware(mock_app)

        # BaseHTTPMiddleware不直接暴露_app，只验证我们设置的属性
        assert middleware._required_permissions is None
        assert "/" in middleware._skip_paths
        assert "/health" in middleware._skip_paths
        assert "/docs" in middleware._skip_paths

    def test_init_with_custom_skip_paths(self, mock_app):
        """测试使用自定义跳过路径"""
        custom_skip = ["/custom1", "/custom2"]
        middleware = ValidationChainMiddleware(
            mock_app,
            skip_paths=custom_skip
        )

        assert middleware._skip_paths == custom_skip

    def test_init_with_required_permissions(self, mock_app):
        """测试使用必需权限初始化"""
        permissions = ["read", "write"]
        middleware = ValidationChainMiddleware(
            mock_app,
            required_permissions=permissions
        )

        assert middleware._required_permissions == permissions

    def test_init_with_all_params(self, mock_app):
        """测试使用所有参数初始化"""
        permissions = ["admin"]
        skip_paths = ["/public"]
        chain_factory = Mock()

        middleware = ValidationChainMiddleware(
            mock_app,
            chain_factory=chain_factory,
            required_permissions=permissions,
            skip_paths=skip_paths
        )

        assert middleware._chain_factory == chain_factory
        assert middleware._required_permissions == permissions
        assert middleware._skip_paths == skip_paths


# ============================================================================
# ValidationChainMiddleware 跳过路径测试
# ============================================================================

class TestValidationChainMiddlewareSkipPaths:
    """测试跳过路径功能"""

    @pytest.fixture
    def mock_app(self):
        """模拟ASGI应用"""
        async def call_next(request):
            return Response(content="OK", status_code=200)
        return call_next

    @pytest.fixture
    def mock_request(self):
        """模拟请求对象"""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/test"
        request.method = "GET"
        request.headers = {}
        return request

    @pytest.mark.asyncio
    async def test_skip_root_path(self, mock_app):
        """测试跳过根路径"""
        middleware = ValidationChainMiddleware(mock_app)
        request = Mock(spec=Request)
        request.url.path = "/"

        response = await middleware.dispatch(request, mock_app)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_skip_health_path(self, mock_app):
        """测试跳过health路径"""
        middleware = ValidationChainMiddleware(mock_app)
        request = Mock(spec=Request)
        request.url.path = "/health"

        response = await middleware.dispatch(request, mock_app)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_skip_docs_path(self, mock_app):
        """测试跳过docs路径"""
        middleware = ValidationChainMiddleware(mock_app)
        request = Mock(spec=Request)
        request.url.path = "/docs"

        response = await middleware.dispatch(request, mock_app)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_skip_redoc_path(self, mock_app):
        """测试跳过redoc路径"""
        middleware = ValidationChainMiddleware(mock_app)
        request = Mock(spec=Request)
        request.url.path = "/redoc"

        response = await middleware.dispatch(request, mock_app)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_skip_openapi_path(self, mock_app):
        """测试跳过openapi.json路径"""
        middleware = ValidationChainMiddleware(mock_app)
        request = Mock(spec=Request)
        request.url.path = "/openapi.json"

        response = await middleware.dispatch(request, mock_app)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_skip_static_path(self, mock_app):
        """测试跳过static路径"""
        middleware = ValidationChainMiddleware(mock_app)
        request = Mock(spec=Request)
        request.url.path = "/static/style.css"

        response = await middleware.dispatch(request, mock_app)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_skip_path_with_prefix(self, mock_app):
        """测试跳过带前缀的路径"""
        middleware = ValidationChainMiddleware(mock_app)
        request = Mock(spec=Request)
        request.url.path = "/static/js/app.js"

        response = await middleware.dispatch(request, mock_app)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_custom_skip_path(self, mock_app):
        """测试自定义跳过路径"""
        middleware = ValidationChainMiddleware(
            mock_app,
            skip_paths=["/custom", "/api/public"]
        )
        request = Mock(spec=Request)
        request.url.path = "/custom"

        response = await middleware.dispatch(request, mock_app)
        assert response.status_code == 200


# ============================================================================
# ValidationChainMiddleware 验证成功路径测试
# ============================================================================

class TestValidationChainMiddlewareSuccessPath:
    """测试验证成功路径"""

    @pytest.fixture
    def mock_app(self):
        """模拟ASGI应用"""
        async def call_next(request):
            return Response(content="OK", status_code=200)
        return call_next

    @pytest.fixture
    def mock_chain(self):
        """模拟验证链"""
        chain = Mock()
        result = ValidationResult(is_valid=True, errors=[])
        # validate接收(request, metadata)参数
        chain.validate = AsyncMock(return_value=result)
        return chain

    @pytest.fixture
    def mock_chain_factory(self, mock_chain):
        """模拟验证链工厂"""
        return Mock(return_value=mock_chain)

    @pytest.mark.asyncio
    async def test_validation_success_passes_to_next(self, mock_app, mock_chain_factory):
        """测试验证成功后传递给下一个中间件"""
        middleware = ValidationChainMiddleware(
            mock_app,
            chain_factory=mock_chain_factory
        )

        request = Mock(spec=Request)
        request.url.path = "/api/protected"
        request.method = "POST"
        request.headers = {}
        request.state = MagicMock()

        response = await middleware.dispatch(request, mock_app)

        # 验证验证链被调用
        mock_chain_factory.return_value.validate.assert_called_once()
        # 验证验证结果存储到request.state
        assert hasattr(request.state, 'validation_result')
        assert request.state.validation_result.is_valid is True

    @pytest.mark.asyncio
    async def test_validation_success_with_permissions(self, mock_app, mock_chain_factory):
        """测试带权限的验证成功"""
        permissions = ["read", "write"]
        middleware = ValidationChainMiddleware(
            mock_app,
            chain_factory=mock_chain_factory,
            required_permissions=permissions
        )

        request = Mock(spec=Request)
        request.url.path = "/api/protected"
        request.method = "POST"
        request.headers = {}
        request.state = MagicMock()

        response = await middleware.dispatch(request, mock_app)

        # 验证工厂被调用并传入权限
        mock_chain_factory.assert_called_once_with(permissions)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_validation_context_contains_metadata(self, mock_app, mock_chain_factory):
        """测试验证上下文包含元数据"""
        middleware = ValidationChainMiddleware(
            mock_app,
            chain_factory=mock_chain_factory
        )

        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.method = "GET"
        request.headers = {"Authorization": "Bearer token123"}
        request.state = MagicMock()

        await middleware.dispatch(request, mock_app)

        # 获取调用validate时的参数 - validate(request, metadata)
        call_args = mock_chain_factory.return_value.validate.call_args
        # 第一个参数是request，第二个是metadata
        metadata = call_args[0][1] if len(call_args[0]) > 1 else {}

        # 验证元数据包含正确的值
        assert metadata["path"] == "/api/test"
        assert metadata["method"] == "GET"


# ============================================================================
# ValidationChainMiddleware 验证失败路径测试
# ============================================================================

class TestValidationChainMiddlewareFailurePath:
    """测试验证失败路径"""

    @pytest.fixture
    def mock_app(self):
        """模拟ASGI应用"""
        async def call_next(request):
            return Response(content="OK", status_code=200)
        return call_next

    @pytest.fixture
    def failing_chain(self):
        """模拟返回错误的验证链"""
        chain = Mock()
        error = ValidationError(
            code="VALIDATION_ERROR",
            message="验证失败",
            severity=ValidationSeverity.ERROR
        )
        result = ValidationResult(is_valid=False, errors=[error])
        chain.validate = AsyncMock(return_value=result)
        return chain

    @pytest.fixture
    def mock_chain_factory(self, failing_chain):
        """模拟返回失败链的工厂"""
        return Mock(return_value=failing_chain)

    @pytest.mark.asyncio
    async def test_validation_failure_raises_http_exception(
        self, mock_app, mock_chain_factory
    ):
        """测试验证失败抛出HTTP异常"""
        middleware = ValidationChainMiddleware(
            mock_app,
            chain_factory=mock_chain_factory
        )

        request = Mock(spec=Request)
        request.url.path = "/api/protected"
        request.method = "POST"
        request.headers = {}
        request.state = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(request, mock_app)

        assert exc_info.value.status_code == 400
        detail = exc_info.value.detail
        assert detail["code"] == "VALIDATION_FAILED"

    @pytest.mark.asyncio
    async def test_validation_failure_stores_result_in_state(
        self, mock_app, mock_chain_factory
    ):
        """测试验证失败时存储结果到state"""
        middleware = ValidationChainMiddleware(
            mock_app,
            chain_factory=mock_chain_factory
        )

        request = Mock(spec=Request)
        request.url.path = "/api/protected"
        request.method = "POST"
        request.headers = {}
        request.state = MagicMock()

        try:
            await middleware.dispatch(request, mock_app)
        except HTTPException:
            pass

        # 验证验证结果存储到request.state
        assert hasattr(request.state, 'validation_result')
        assert request.state.validation_result.is_valid is False
        assert len(request.state.validation_result.errors) > 0


# ============================================================================
# ValidationChainMiddleware 异常处理测试
# ============================================================================

class TestValidationChainMiddlewareExceptionHandling:
    """测试中间件异常处理"""

    @pytest.fixture
    def mock_app(self):
        """模拟ASGI应用"""
        async def call_next(request):
            return Response(content="OK", status_code=200)
        return call_next

    @pytest.fixture
    def error_chain_factory(self):
        """模拟抛出异常的验证链工厂"""
        chain = Mock()
        chain.validate = AsyncMock(side_effect=RuntimeError("验证链错误"))
        return Mock(return_value=chain)

    @pytest.mark.asyncio
    async def test_chain_exception_causes_http_exception(
        self, mock_app, error_chain_factory
    ):
        """测试验证链异常导致HTTP异常"""
        middleware = ValidationChainMiddleware(
            mock_app,
            chain_factory=error_chain_factory
        )

        request = Mock(spec=Request)
        request.url.path = "/api/protected"
        request.method = "POST"
        request.headers = {}
        request.state = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(request, mock_app)

        assert exc_info.value.status_code == 500
        detail = exc_info.value.detail
        assert detail["code"] == "VALIDATION_ERROR"


# ============================================================================
# create_validation_middleware 工厂函数测试
# ============================================================================

class TestCreateValidationMiddleware:
    """测试create_validation_middleware工厂函数"""

    @pytest.fixture
    def mock_app(self):
        """模拟ASGI应用"""
        return Mock(spec=ASGIApp)

    def test_create_middleware_returns_class(self, mock_app):
        """测试返回中间件类"""
        middleware_class = create_validation_middleware()

        assert callable(middleware_class)
        # 可以实例化
        instance = middleware_class(mock_app)
        assert isinstance(instance, ValidationChainMiddleware)

    def test_create_middleware_with_permissions(self, mock_app):
        """测试创建带权限的中间件"""
        permissions = ["admin", "write"]
        middleware_class = create_validation_middleware(
            required_permissions=permissions
        )

        instance = middleware_class(mock_app)
        assert instance._required_permissions == permissions

    def test_create_middleware_with_skip_paths(self, mock_app):
        """测试创建带跳过路径的中间件"""
        skip_paths = ["/public", "/health"]
        middleware_class = create_validation_middleware(
            skip_paths=skip_paths
        )

        instance = middleware_class(mock_app)
        assert instance._skip_paths == skip_paths

    def test_create_middleware_with_chain_factory(self, mock_app):
        """测试创建带自定义链工厂的中间件"""
        custom_factory = Mock()
        middleware_class = create_validation_middleware(
            chain_factory=custom_factory
        )

        instance = middleware_class(mock_app)
        assert instance._chain_factory == custom_factory

    def test_create_middleware_class_name(self):
        """测试创建的中间件类名"""
        middleware_class = create_validation_middleware()
        assert middleware_class.__name__ == "ValidationMiddleware"

    def test_create_middleware_all_params(self, mock_app):
        """测试创建中间件时使用所有参数"""
        permissions = ["read"]
        skip_paths = ["/api/public"]
        chain_factory = Mock()

        middleware_class = create_validation_middleware(
            chain_factory=chain_factory,
            required_permissions=permissions,
            skip_paths=skip_paths
        )

        instance = middleware_class(mock_app)
        assert instance._chain_factory == chain_factory
        assert instance._required_permissions == permissions
        assert instance._skip_paths == skip_paths


# ============================================================================
# 集成测试
# ============================================================================

class TestValidationChainMiddlewareIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_full_validation_flow_with_real_chain(self):
        """测试使用真实验证链的完整流程"""
        from app.core.validation_chain import ValidationChain, ContentValidatorHandler

        # 创建验证链
        chain = ValidationChain("test")
        chain.add_handler(ContentValidatorHandler(
            required_fields=["message"],
            max_length=1000
        ))

        # 创建中间件 - lambda需要支持可选参数
        async def mock_app(request):
            return Response(content="OK", status_code=200)

        middleware = ValidationChainMiddleware(
            mock_app,
            chain_factory=lambda permissions=None: chain
        )

        # 测试有效请求
        request = Mock(spec=Request)
        request.url.path = "/api/chat"
        request.method = "POST"
        request.headers = {}
        request.state = MagicMock()

        # 模拟请求体
        request_json = {"message": "Hello"}

        with patch.object(request, 'json', return_value=request_json):
            response = await middleware.dispatch(request, mock_app)
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_validation_failure_with_real_chain(self):
        """测试使用真实验证链的验证失败"""
        from app.core.validation_chain import ValidationChain, AuthenticationHandler

        # 创建验证链 - 使用AuthenticationHandler，它会检查request中的user属性
        chain = ValidationChain("test")
        chain.add_handler(AuthenticationHandler(stop_on_critical=True))

        # 创建中间件
        async def mock_app(request):
            return Response(content="OK", status_code=200)

        middleware = ValidationChainMiddleware(
            mock_app,
            chain_factory=lambda permissions=None: chain
        )

        # 测试无效请求 - 没有认证信息
        request = Mock(spec=Request)
        request.url.path = "/api/chat"
        request.method = "POST"
        request.headers = {}  # 没有Authorization头
        request.state = MagicMock()
        request.user = None

        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(request, mock_app)

        # 可能抛出400（验证失败）或500（验证错误）
        assert exc_info.value.status_code in [400, 500]


# ============================================================================
# 运行测试入口
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
