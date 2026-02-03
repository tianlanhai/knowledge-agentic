# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：服务装饰器模块测试
内部逻辑：测试依赖注入相关的装饰器功能
"""

import pytest
from typing import Optional
from unittest.mock import MagicMock, patch

from app.core.di.service_decorator import (
    InjectMode,
    injectable,
    inject,
    inject_method,
    singleton,
    scoped,
    transient,
)
from app.core.di.service_container import (
    ServiceLifetime,
    get_container,
    reset_container,
)


# ============================================================================
# 测试用服务类
# ============================================================================


class TestService1:
    """测试用服务类1"""
    def __init__(self):
        self.value = "service1"


class TestService2:
    """测试用服务类2"""
    def __init__(self):
        self.value = "service2"


# ============================================================================
# InjectMode 枚举测试
# ============================================================================


class TestInjectMode:
    """InjectMode枚举测试类"""

    def test_mode_values(self):
        """验证注入模式枚举值"""
        assert InjectMode.POSITIONAL.value == "positional"
        assert InjectMode.KEYWORD.value == "keyword"


# ============================================================================
# @singleton 装饰器测试
# ============================================================================


class TestSingletonDecorator:
    """@singleton装饰器测试类"""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """每个测试前后重置状态"""
        reset_container()
        yield
        reset_container()

    def test_singleton_decorator(self):
        """验证单例装饰器"""
        @singleton
        class MySingletonService:
            def __init__(self):
                self.value = "singleton"

        assert MySingletonService._injectable_lifetime == ServiceLifetime.SINGLETON


# ============================================================================
# @scoped 装饰器测试
# ============================================================================


class TestScopedDecorator:
    """@scoped装饰器测试类"""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """每个测试前后重置状态"""
        reset_container()
        yield
        reset_container()

    def test_scoped_decorator(self):
        """验证作用域装饰器"""
        @scoped
        class MyScopedService:
            def __init__(self):
                self.value = "scoped"

        assert MyScopedService._injectable_lifetime == ServiceLifetime.SCOPED


# ============================================================================
# @transient 装饰器测试
# ============================================================================


class TestTransientDecorator:
    """@transient装饰器测试类"""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """每个测试前后重置状态"""
        reset_container()
        yield
        reset_container()

    def test_transient_decorator(self):
        """验证瞬态装饰器"""
        @transient
        class MyTransientService:
            def __init__(self):
                self.value = "transient"

        assert MyTransientService._injectable_lifetime == ServiceLifetime.TRANSIENT

    def test_transient_behavior(self):
        """验证瞬态行为"""
        @transient
        class TimestampService:
            def __init__(self):
                import time
                self.timestamp = time.time()

        container = get_container()
        container.register(TimestampService, TimestampService, ServiceLifetime.TRANSIENT)

        service1 = container.get_service(TimestampService)
        service2 = container.get_service(TimestampService)

        assert service1 is not service2


# ============================================================================
# @inject 装饰器测试
# ============================================================================


class TestInjectDecorator:
    """@inject装饰器测试类"""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """每个测试前后重置状态"""
        reset_container()
        yield
        reset_container()

    def test_inject_with_provided_args(self):
        """验证注入装饰器不覆盖已有参数"""
        @inject
        def process_with_service(svc: TestService1):
            return svc.value

        manual_service = TestService1()
        result = process_with_service(svc=manual_service)

        assert result == "service1"


# ============================================================================
# @inject_method 装饰器测试
# ============================================================================


class TestInjectMethodDecorator:
    """@inject_method装饰器测试类"""

    def test_inject_method_with_self(self):
        """验证方法注入正确处理self参数"""
        class Handler:
            @inject_method
            def process(self, svc: TestService1):
                return f"Processing with {svc.value}"

        handler = Handler()
        service = TestService1()
        result = handler.process(svc=service)

        assert result == "Processing with service1"


# ============================================================================
# 装饰器组合测试
# ============================================================================


class TestDecoratorCombinations:
    """装饰器组合测试类"""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """每个测试前后重置状态"""
        reset_container()
        yield
        reset_container()

    def test_singleton_with_dependencies(self):
        """验证单例服务带依赖"""
        @singleton
        class DependentService:
            def __init__(self, s1: TestService1):
                self.s1 = s1

        container = get_container()
        container.register(TestService1, TestService1, ServiceLifetime.SINGLETON)
        container.register(DependentService, DependentService, ServiceLifetime.SINGLETON)

        service = container.get_service(DependentService)

        assert service.s1 is not None
        assert isinstance(service.s1, TestService1)


# ============================================================================
# 边界条件测试
# ============================================================================


class TestDecoratorEdgeCases:
    """装饰器边界条件测试类"""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """每个测试前后重置状态"""
        reset_container()
        yield
        reset_container()

    def test_inject_unregistered_service(self):
        """验证注入未注册服务"""
        @inject
        def process(svc: TestService1):
            return svc.value

        # 手动传递服务实例
        service = TestService1()
        result = process(svc=service)
        assert result == "service1"

    def test_decorator_preserves_class_attributes(self):
        """验证装饰器保留类属性"""
        @singleton
        class DocumentedService:
            """这是文档字符串"""
            def __init__(self):
                self.value = "documented"

        assert DocumentedService.__name__ == "DocumentedService"
        assert DocumentedService.__doc__ == "这是文档字符串"
