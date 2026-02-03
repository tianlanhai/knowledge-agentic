# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：FastAPI中间件模块
内部逻辑：提供责任链模式集成的中间件
设计模式：责任链模式 + 中间件模式
设计原则：开闭原则、单一职责原则
"""

from typing import Any, Callable, Optional, List
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from loguru import logger

from app.core.validation_chain import (
    ValidationChain,
    ValidationChainFactory,
    ValidationContext,
    ValidationResult,
    ValidationError,
    ValidationSeverity,
    BusinessLogicHandler,
)


class ValidationChainMiddleware(BaseHTTPMiddleware):
    """
    类级注释：验证链中间件
    内部逻辑：在请求处理前执行验证链
    设计模式：中间件模式 + 责任链模式
    用途：统一API请求验证流程

    @example
    ```python
    app.add_middleware(
        ValidationChainMiddleware,
        chain_factory=ValidationChainFactory.create_api_chain,
        required_permissions=["chat:write"]
    )
    ```
    """

    def __init__(
        self,
        app: ASGIApp,
        chain_factory: Optional[Callable] = None,
        required_permissions: Optional[List[str]] = None,
        skip_paths: Optional[List[str]] = None,
    ):
        """
        函数级注释：初始化验证链中间件
        参数：
            app - ASGI应用
            chain_factory - 验证链工厂函数
            required_permissions - 需要的权限列表
            skip_paths - 跳过验证的路径列表
        """
        super().__init__(app)
        # 内部变量：验证链工厂函数
        self._chain_factory = chain_factory or ValidationChainFactory.create_api_chain
        # 内部变量：需要的权限
        self._required_permissions = required_permissions
        # 内部变量：跳过验证的路径
        self._skip_paths = skip_paths or [
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/static",
        ]

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        函数级注释：处理请求
        内部逻辑：检查是否跳过 -> 创建验证链 -> 执行验证 -> 传递或拒绝
        参数：
            request - 请求对象
            call_next - 下一个中间件/路由处理器
        返回值：响应对象
        """
        # 内部逻辑：检查是否跳过验证
        path = request.url.path
        if path == "/" or any(path.startswith(skip_path) for skip_path in self._skip_paths if skip_path != "/"):
            return await call_next(request)

        # 内部逻辑：创建验证链
        if self._required_permissions:
            chain = self._chain_factory(self._required_permissions)
        else:
            chain = self._chain_factory()

        # 内部逻辑：创建验证上下文
        context = ValidationContext(
            request=request,
            metadata={
                "path": path,
                "method": request.method,
                "headers": dict(request.headers),
            }
        )

        # 内部逻辑：执行验证链
        try:
            result = await chain.validate(request, context.metadata)

            # 内部逻辑：检查验证结果
            if not result.is_valid:
                # 内部逻辑：将验证结果存储到请求状态
                request.state.validation_result = result

                # 内部逻辑：抛出 HTTP 异常
                error_detail = {
                    "code": "VALIDATION_FAILED",
                    "message": "请求验证失败",
                    "errors": [e.to_dict() for e in result.errors]
                }
                raise HTTPException(status_code=400, detail=error_detail)
            else:
                # 内部逻辑：存储验证结果到请求状态
                request.state.validation_result = result

        except HTTPException:
            # 内部逻辑：重新抛出 HTTP 异常
            raise
        except Exception as e:
            # 内部逻辑：捕获其他异常
            logger.error(f"验证链执行失败: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail={"code": "VALIDATION_ERROR", "message": "验证过程发生错误"}
            )

        # 内部逻辑：传递给下一个处理器
        return await call_next(request)


def create_validation_middleware(
    chain_factory: Optional[Callable] = None,
    required_permissions: Optional[List[str]] = None,
    skip_paths: Optional[List[str]] = None,
) -> type:
    """
    函数级注释：创建验证中间件工厂
    设计模式：工厂模式 - 动态创建中间件类
    参数：
        chain_factory - 验证链工厂函数
        required_permissions - 需要的权限列表
        skip_paths - 跳过验证的路径列表
    返回值：中间件类

    @example
    ```python
    from app.core.middleware import create_validation_middleware

    ValidationMiddleware = create_validation_middleware(
        required_permissions=["chat:write"],
        skip_paths=["/health", "/docs"]
    )
    app.add_middleware(ValidationMiddleware)
    ```
    """

    class DynamicValidationMiddleware(ValidationChainMiddleware):
        """
        类级注释：动态生成的验证中间件
        设计模式：工厂模式 - 根据参数动态创建中间件类
        """

        def __init__(self, app: ASGIApp):
            # 内部逻辑：使用闭包参数初始化
            super().__init__(
                app,
                chain_factory=chain_factory,
                required_permissions=required_permissions,
                skip_paths=skip_paths
            )

    # 内部逻辑：设置类名便于调试
    DynamicValidationMiddleware.__name__ = "ValidationMiddleware"

    return DynamicValidationMiddleware


class ServiceScopeMiddleware(BaseHTTPMiddleware):
    """
    类级注释：服务作用域中间件
    设计模式：中间件模式 + 作用域模式
    用途：为每个请求自动创建和释放服务作用域
    职责：管理依赖注入容器中作用域服务的生命周期

    @example
    ```python
    app.add_middleware(ServiceScopeMiddleware)
    ```
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        函数级注释：处理请求并管理作用域生命周期
        内部逻辑：请求前创建作用域 -> 请求后释放作用域
        参数：
            request - 请求对象
            call_next - 下一个中间件/路由处理器
        返回值：响应对象

        设计模式：RAII模式 - 通过try-finally确保资源正确释放
        """
        # 内部逻辑：延迟导入，避免循环依赖
        from app.core.di.service_container import get_container

        # 内部变量：获取全局服务容器
        container = get_container()

        # 内部逻辑：创建请求作用域
        # 设计模式：作用域模式 - 同一请求内共享scoped服务实例
        scope = container.create_scope()
        container._current_scope = scope

        try:
            # 内部逻辑：执行请求处理
            response = await call_next(request)
            return response
        finally:
            # 内部逻辑：释放作用域，清理资源
            # 确保即使发生异常也能正确释放
            scope.release()
            container._current_scope = None


# 内部变量：导出所有公共接口
__all__ = [
    'ValidationChainMiddleware',
    'create_validation_middleware',
    'ServiceScopeMiddleware',
]
