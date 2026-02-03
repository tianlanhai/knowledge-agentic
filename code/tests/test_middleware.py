# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：中间件模块测试
内部逻辑：测试ValidationChainMiddleware和相关功能
测试覆盖范围：
    - ValidationChainMiddleware初始化
    - dispatch方法的各种分支
    - create_validation_middleware工厂函数
测试类型：单元测试
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import Request, HTTPException
from starlette.types import ASGIApp, Receive, Scope
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.middleware import (
    ValidationChainMiddleware,
    create_validation_middleware,
)


class TestValidationChainMiddleware:
    """测试ValidationChainMiddleware类"""

    @pytest.fixture
    def app(self):
        """创建ASGI应用"""
        return Mock(spec=ASGIApp)

    def test_init_with_all_params(self, app):
        """测试完整参数初始化"""
        def chain_factory(permissions):
            return Mock()

        middleware = ValidationChainMiddleware(
            app,
            chain_factory=chain_factory,
            required_permissions=["chat:write", "chat:read"],
            skip_paths=["/health", "/docs"]
        )

        assert middleware._chain_factory == chain_factory
        assert middleware._required_permissions == ["chat:write", "chat:read"]
        assert "/health" in middleware._skip_paths
        assert "/docs" in middleware._skip_paths

    def test_init_with_default_params(self, app):
        """测试默认参数初始化（覆盖lines 60-73）"""
        middleware = ValidationChainMiddleware(app)

        assert middleware._chain_factory is not None
        assert middleware._required_permissions is None
        assert middleware._skip_paths == [
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/static",
        ]

    @pytest.mark.asyncio
    async def test_dispatch_skip_root_path(self, app):
        """测试跳过根路径验证（覆盖lines 89-91）"""
        middleware = ValidationChainMiddleware(app)

        # 创建mock request
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": []
        }
        receive = AsyncMock()
        request = Request(scope, receive)

        # Mock call_next
        async def call_next(req):
            return Mock()

        response = await middleware.dispatch(request, call_next)
        assert response is not None  # call_next被调用

    @pytest.mark.asyncio
    async def test_dispatch_skip_health_path(self, app):
        """测试跳过health路径验证"""
        middleware = ValidationChainMiddleware(app)

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/health",
            "headers": []
        }
        receive = AsyncMock()
        request = Request(scope, receive)

        async def call_next(req):
            return Mock()

        response = await middleware.dispatch(request, call_next)
        assert response is not None

    @pytest.mark.asyncio
    async def test_dispatch_with_validation_passed(self, app):
        """测试验证通过的情况（覆盖lines 94-128）"""
        def chain_factory(permissions):
            chain = Mock()
            result = Mock()
            result.is_valid = True
            result.errors = []
            chain.validate = AsyncMock(return_value=result)
            return chain

        middleware = ValidationChainMiddleware(
            app,
            chain_factory=chain_factory,
            required_permissions=["chat:write"]
        )

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/chat",
            "headers": [],
            "state": {}
        }
        receive = AsyncMock()
        request = Request(scope, receive)

        async def call_next(req):
            response = Mock()
            response.status_code = 200
            return response

        response = await middleware.dispatch(request, call_next)
        assert response is not None

    @pytest.mark.asyncio
    async def test_dispatch_with_validation_failed(self, app):
        """测试验证失败的情况（覆盖lines 114-124）"""
        # 创建一个验证链，返回失败结果
        def chain_factory(permissions):
            chain = Mock()
            result = Mock()
            result.is_valid = False
            error = Mock()
            error.to_dict = Mock(return_value={"field": "api_key", "message": "Required"})
            result.errors = [error]
            chain.validate = AsyncMock(return_value=result)
            return chain

        middleware = ValidationChainMiddleware(
            app,
            chain_factory=chain_factory,
            required_permissions=["chat:write"]
        )

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/chat",
            "headers": [],
            "state": {}
        }
        receive = AsyncMock()
        request = Request(scope, receive)

        async def call_next(req):
            return Mock()

        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(request, call_next)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_dispatch_with_http_exception(self, app):
        """测试dispatch中HTTPException重新抛出（覆盖lines 129-131）"""
        def chain_factory(permissions):
            chain = Mock()
            chain.validate = AsyncMock(side_effect=HTTPException(status_code=401, detail="Unauthorized"))
            return chain

        middleware = ValidationChainMiddleware(
            app,
            chain_factory=chain_factory,
            required_permissions=["chat:write"]
        )

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/chat",
            "headers": [],
            "state": {}
        }
        receive = AsyncMock()
        request = Request(scope, receive)

        async def call_next(req):
            return Mock()

        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(request, call_next)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_dispatch_with_generic_exception(self, app):
        """测试dispatch中通用异常处理（覆盖lines 132-138）"""
        def chain_factory(permissions):
            chain = Mock()
            chain.validate = AsyncMock(side_effect=Exception("Unexpected error"))
            return chain

        middleware = ValidationChainMiddleware(
            app,
            chain_factory=chain_factory,
            required_permissions=["chat:write"]
        )

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/chat",
            "headers": [],
            "state": {}
        }
        receive = AsyncMock()
        request = Request(scope, receive)

        async def call_next(req):
            return Mock()

        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(request, call_next)
        assert exc_info.value.status_code == 500


class TestCreateValidationMiddleware:
    """测试create_validation_middleware工厂函数"""

    def test_create_with_all_params(self):
        """测试使用所有参数创建中间件（覆盖lines 170-183）"""
        def chain_factory(permissions):
            return Mock()

        MiddlewareClass = create_validation_middleware(
            chain_factory=chain_factory,
            required_permissions=["chat:write"],
            skip_paths=["/health", "/docs"]
        )

        # 验证返回的是类
        assert MiddlewareClass is not None

        # 创建实例验证
        app = Mock(spec=ASGIApp)
        middleware = MiddlewareClass(app)
        assert middleware._chain_factory == chain_factory
        assert middleware._required_permissions == ["chat:write"]

    def test_create_with_no_params(self):
        """测试使用默认参数创建中间件"""
        MiddlewareClass = create_validation_middleware()

        app = Mock(spec=ASGIApp)
        middleware = MiddlewareClass(app)
        assert middleware._required_permissions is None
        assert middleware._skip_paths is not None

    def test_create_returns_class(self):
        """测试工厂返回类而不是实例（覆盖line 188）"""
        result = create_validation_middleware()
        # 结果应该是一个类
        assert isinstance(result, type)
        # 类名应该被设置
        assert "ValidationMiddleware" in result.__name__
