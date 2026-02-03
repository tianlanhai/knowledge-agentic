# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：装饰器模块测试
内部逻辑：全面测试所有装饰器函数和类
设计模式：装饰器模式测试
测试覆盖范围：
    - api_error_handler API错误处理
    - log_execution 执行日志
    - validate_request 请求验证
    - cache_response 响应缓存
    - retry_on_failure 失败重试
    - timing 执行时间测量
    - singleton 单例装饰器
    - cached_property 缓存属性
    - suppress_exceptions 异常抑制
    - validate_permissions 权限验证
    - rate_limit 速率限制
    - 内部辅助函数
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from time import sleep
from functools import wraps

from app.core.decorators import (
    api_error_handler,
    log_execution,
    validate_request,
    cache_response,
    retry_on_failure,
    timing,
    singleton,
    cached_property,
    suppress_exceptions,
    validate_permissions,
    rate_limit,
    _is_retryable_error,
    _calculate_backoff,
    _filter_sensitive_args,
    _SingletonWrapper,
    _CachedProperty,
)


# ========================================================================
# 测试类：api_error_handler
# ========================================================================

class TestAPIErrorHandler:
    """
    类级注释：测试API错误处理装饰器
    测试范围：异常捕获、错误响应格式、HTTPException处理
    """

    @pytest.mark.asyncio
    async def test_success_execution(self):
        """测试：正常执行不拦截"""
        @api_error_handler("操作失败")
        async def successful_func():
            return {"success": True}

        result = await successful_func()
        assert result == {"success": True}

    @pytest.mark.asyncio
    async def test_value_error_handling(self):
        """测试：ValueError转换为400错误"""
        @api_error_handler("操作失败")
        async def func_with_value_error():
            raise ValueError("参数错误")

        with pytest.raises(HTTPException) as exc_info:
            await func_with_value_error()

        assert exc_info.value.status_code == 400
        assert "参数错误" in exc_info.value.detail["error"]["message"]

    @pytest.mark.asyncio
    async def test_generic_exception_handling(self):
        """测试：通用异常转换为500错误"""
        @api_error_handler("操作失败", error_code=500)
        async def func_with_exception():
            raise RuntimeError("系统错误")

        with pytest.raises(HTTPException) as exc_info:
            await func_with_exception()

        assert exc_info.value.status_code == 500
        assert exc_info.value.detail["error"]["code"] == 500

    @pytest.mark.asyncio
    async def test_http_exception_passthrough(self):
        """测试：HTTPException直接传递"""
        @api_error_handler("操作失败")
        async def func_with_http_error():
            raise HTTPException(status_code=404, detail="未找到")

        with pytest.raises(HTTPException) as exc_info:
            await func_with_http_error()

        # 验证：原始HTTPException被保留
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_custom_error_message(self):
        """测试：自定义错误消息"""
        @api_error_handler("自定义消息", error_code=503)
        async def failing_func():
            raise Exception("内部错误")

        with pytest.raises(HTTPException) as exc_info:
            await failing_func()

        assert "自定义消息" in exc_info.value.detail["error"]["message"]

    @pytest.mark.asyncio
    async def test_default_error_code(self):
        """测试：默认错误码为500"""
        @api_error_handler("失败")
        async def failing_func():
            raise Exception("错误")

        with pytest.raises(HTTPException) as exc_info:
            await failing_func()

        assert exc_info.value.status_code == 500


# ========================================================================
# 测试类：log_execution
# ========================================================================

class TestLogExecution:
    """
    类级注释：测试执行日志装饰器
    测试范围：函数调用日志、参数日志、返回值日志
    """

    @pytest.mark.asyncio
    async def test_logs_function_call(self):
        """测试：记录函数调用"""
        @log_execution(log_args=False, log_result=False)
        async def test_func():
            return "result"

        with patch('app.core.decorators.logger') as mock_logger:
            result = await test_func()

            # 验证：记录了调用和成功
            assert mock_logger.info.call_count >= 2  # 调用和成功
            assert result == "result"

    @pytest.mark.asyncio
    async def test_logs_with_args(self):
        """测试：记录参数"""
        @log_execution(log_args=True, log_result=False)
        async def test_func(arg1, arg2=None):
            return arg1

        with patch('app.core.decorators.logger') as mock_logger:
            await test_func("value1", arg2="value2")

            # 验证：记录了参数
            assert any("入参" in str(call) for call in mock_logger.debug.call_args_list)

    @pytest.mark.asyncio
    async def test_logs_with_result(self):
        """测试：记录返回值"""
        @log_execution(log_args=False, log_result=True)
        async def test_func():
            return {"key": "value"}

        with patch('app.core.decorators.logger') as mock_logger:
            result = await test_func()

            # 验证：记录了返回值
            assert result == {"key": "value"}
            assert any("返回" in str(call) for call in mock_logger.debug.call_args_list)

    @pytest.mark.asyncio
    async def test_logs_exception(self):
        """测试：记录异常"""
        @log_execution()
        async def failing_func():
            raise ValueError("测试错误")

        with patch('app.core.decorators.logger') as mock_logger:
            with pytest.raises(ValueError):
                await failing_func()

            # 验证：记录了错误
            assert mock_logger.error.called

    @pytest.mark.asyncio
    async def test_filters_sensitive_args(self):
        """
        函数级注释：测试过滤敏感参数
        内部逻辑：验证包含password、api_key等关键词的参数被脱敏处理
        """
        @log_execution(log_args=True, log_result=False)
        async def test_func(normal_param, password="secret123", api_key="key456"):
            return "done"

        with patch('app.core.decorators.logger') as mock_logger:
            # 内部逻辑：使用关键字参数传入敏感数据
            await test_func("normal", password="secret123", api_key="key456")

            # 验证：敏感参数被脱敏（格式为 ***{len}chars*** 或 ***）
            debug_calls = [str(call) for call in mock_logger.debug.call_args_list]
            # 内部逻辑：检查是否包含脱敏标记（格式可能是 ***9chars*** 或类似）
            assert any("chars" in call or "***" in call for call in debug_calls), f"Expected masking in: {debug_calls}"

    @pytest.mark.asyncio
    async def test_sync_function(self):
        """
        函数级注释：测试同步函数日志
        内部逻辑：注意：log_execution装饰器当前只支持async函数
        此测试验证同步函数调用async装饰器时的行为
        """
        @log_execution(log_args=False, log_result=False)
        def sync_func():
            return "sync_result"

        with patch('app.core.decorators.logger') as mock_logger:
            # 内部逻辑：同步函数调用async装饰器会返回coroutine
            result = sync_func()

            # 内部逻辑：需要await才能得到实际结果
            # 但由于这是同步函数，实际上是返回了coroutine对象
            assert asyncio.iscoroutine(result), "同步函数调用async装饰器返回coroutine"

            # 内部逻辑：如果需要实际执行，需要运行coroutine
            # 这里我们验证coroutine对象被正确返回
            assert result is not None


# ========================================================================
# 测试类：validate_request
# ========================================================================

class TestValidateRequest:
    """
    类级注释：测试请求验证装饰器
    测试范围：Pydantic模型验证、参数查找
    """

    @pytest.mark.asyncio
    async def test_finds_schema_in_args(self):
        """测试：在位置参数中查找schema"""
        class TestSchema:
            def __init__(self, **kwargs):
                self.data = kwargs

        @validate_request(TestSchema)
        async def test_func(request):
            return request.data

        schema_instance = TestSchema(field1="value1")
        result = await test_func(schema_instance)

        assert result == {"field1": "value1"}

    @pytest.mark.asyncio
    async def test_finds_schema_in_kwargs(self):
        """测试：在关键字参数中查找schema"""
        class TestSchema:
            def __init__(self, **kwargs):
                self.data = kwargs

        @validate_request(TestSchema)
        async def test_func(other_param, request=None):
            return request.data if request else None

        schema_instance = TestSchema(field1="value1")
        result = await test_func("other", request=schema_instance)

        assert result == {"field1": "value1"}

    @pytest.mark.asyncio
    async def test_no_schema_found_logs_warning(self):
        """测试：未找到schema时记录警告"""
        class TestSchema:
            pass

        @validate_request(TestSchema)
        async def test_func(no_schema_param):
            return "result"

        with patch('app.core.decorators.logger') as mock_logger:
            result = await test_func("value")

            assert result == "result"
            assert mock_logger.warning.called


# ========================================================================
# 测试类：cache_response
# ========================================================================

class TestCacheResponse:
    """
    类级注释：测试响应缓存装饰器
    测试范围：缓存命中、过期、键生成
    """

    @pytest.mark.asyncio
    async def test_caches_result(self):
        """测试：缓存函数结果"""
        call_count = [0]

        @cache_response(ttl_seconds=60, key_prefix="test")
        async def expensive_func(arg1):
            call_count[0] += 1
            return f"result_{arg1}"

        # 第一次调用
        result1 = await expensive_func("value1")
        # 第二次调用（应从缓存返回）
        result2 = await expensive_func("value1")

        assert result1 == result2
        assert call_count[0] == 1  # 只调用一次

    @pytest.mark.asyncio
    async def test_cache_key_different_params(self):
        """测试：不同参数生成不同缓存键"""
        call_count = [0]

        @cache_response(ttl_seconds=60)
        async def func(arg1):
            call_count[0] += 1
            return arg1

        await func("value1")
        await func("value2")

        # 验证：不同参数不共享缓存
        assert call_count[0] == 2

    @pytest.mark.asyncio
    async def test_cache_expiration(self):
        """测试：缓存过期"""
        call_count = [0]

        @cache_response(ttl_seconds=0)  # 立即过期
        async def func():
            call_count[0] += 1
            return "result"

        with patch('time.time', side_effect=[0, 1, 1.1]):  # 模拟时间流逝
            result1 = await func()
            result2 = await func()

        # 验证：缓存过期后重新计算
        assert call_count[0] == 2

    @pytest.mark.asyncio
    async def test_custom_key_prefix(self):
        """测试：自定义缓存键前缀"""
        @cache_response(ttl_seconds=60, key_prefix="custom")
        async def func():
            return "result"

        with patch('app.core.decorators.logger') as mock_logger:
            await func()
            await func()  # 第二次从缓存

            # 验证：使用自定义前缀
            debug_calls = [str(call) for call in mock_logger.debug.call_args_list]
            assert any("custom" in call for call in debug_calls)


# ========================================================================
# 测试类：retry_on_failure
# ========================================================================

class TestRetryOnFailure:
    """
    类级注释：测试失败重试装饰器
    测试范围：重试逻辑、退避策略、异常过滤
    """

    @pytest.mark.asyncio
    async def test_success_no_retry(self):
        """测试：成功不重试"""
        call_count = [0]

        @retry_on_failure(max_retries=3)
        async def func():
            call_count[0] += 1
            return "success"

        result = await func()

        assert result == "success"
        assert call_count[0] == 1

    @pytest.mark.asyncio
    async def test_retry_on_connection_error(self):
        """测试：连接错误重试"""
        call_count = [0]

        @retry_on_failure(max_retries=2, exceptions=(ConnectionError,))
        async def func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ConnectionError("连接失败")
            return "success"

        result = await func()

        assert result == "success"
        assert call_count[0] == 2

    @pytest.mark.asyncio
    async def test_exhausted_retries_raises(self):
        """测试：重试次数耗尽后抛出异常"""
        call_count = [0]

        @retry_on_failure(max_retries=2)
        async def func():
            call_count[0] += 1
            raise ConnectionError("始终失败")

        with pytest.raises(ConnectionError):
            await func()

        assert call_count[0] == 3  # 初始调用 + 2次重试

    @pytest.mark.asyncio
    async def test_no_retry_for_non_retryable_error(self):
        """测试：不可重试错误不重试"""
        call_count = [0]

        @retry_on_failure(max_retries=3, exceptions=(ValueError,))
        async def func():
            call_count[0] += 1
            raise TypeError("不可重试")

        with pytest.raises(TypeError):
            await func()

        # 验证：没有重试
        assert call_count[0] == 1

    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """测试：指数退避策略"""
        import time as time_module

        wait_times = []

        @retry_on_failure(max_retries=2, strategy="exponential", backoff_factor=0.1)
        async def func():
            if len(wait_times) < 2:
                wait_times.append(time_module.time())
                raise ConnectionError("失败")
            return "success"

        with patch('asyncio.sleep', new=AsyncMock()) as mock_sleep:
            await func()

            # 验证：sleep被调用两次且时间递增
            assert mock_sleep.call_count == 2
            # 指数退避: 0.1, 0.2
            calls = [call[0][0] for call in mock_sleep.call_args_list]
            assert calls[0] == 0.1
            assert calls[1] == 0.2

    @pytest.mark.asyncio
    async def test_linear_backoff(self):
        """测试：线性退避策略"""
        @retry_on_failure(max_retries=2, strategy="linear", backoff_factor=0.1)
        async def func():
            raise ConnectionError("失败")

        with patch('asyncio.sleep', new=AsyncMock()) as mock_sleep:
            with pytest.raises(ConnectionError):
                await func()

            # 线性退避: 0.1, 0.2
            calls = [call[0][0] for call in mock_sleep.call_args_list]
            assert calls[0] == 0.1
            assert calls[1] == 0.2

    @pytest.mark.asyncio
    async def test_fixed_backoff(self):
        """测试：固定退避策略"""
        @retry_on_failure(max_retries=2, strategy="fixed", backoff_factor=0.15)
        async def func():
            raise ConnectionError("失败")

        with patch('asyncio.sleep', new=AsyncMock()) as mock_sleep:
            with pytest.raises(ConnectionError):
                await func()

            # 固定退避: 0.15, 0.15
            calls = [call[0][0] for call in mock_sleep.call_args_list]
            assert all(c == 0.15 for c in calls)

    @pytest.mark.asyncio
    async def test_immediate_strategy(self):
        """测试：立即重试策略"""
        @retry_on_failure(max_retries=2, strategy="immediate")
        async def func():
            raise ConnectionError("失败")

        with patch('asyncio.sleep', new=AsyncMock()) as mock_sleep:
            with pytest.raises(ConnectionError):
                await func()

            # 立即重试: 等待时间为0
            calls = [call[0][0] for call in mock_sleep.call_args_list]
            assert all(c == 0 for c in calls)

    @pytest.mark.asyncio
    async def test_sync_function_retry(self):
        """测试：同步函数重试"""
        call_count = [0]

        @retry_on_failure(max_retries=2)
        def sync_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ConnectionError("失败")
            return "success"

        result = sync_func()

        assert result == "success"
        assert call_count[0] == 2


# ========================================================================
# 测试类：timing
# ========================================================================

class TestTiming:
    """
    类级注释：测试执行时间测量装饰器
    测试范围：时间测量、日志级别
    """

    @pytest.mark.asyncio
    async def test_measures_execution_time(self):
        """测试：测量执行时间"""
        @timing(log_level="debug")
        async def func():
            await asyncio.sleep(0.01)  # 10ms
            return "result"

        with patch('app.core.decorators.logger') as mock_logger:
            result = await func()

            assert result == "result"
            assert mock_logger.debug.called

    @pytest.mark.asyncio
    async def test_info_log_level(self):
        """测试：info日志级别"""
        @timing(log_level="info")
        async def func():
            return "result"

        with patch('app.core.decorators.logger') as mock_logger:
            await func()

            assert mock_logger.info.called

    @pytest.mark.asyncio
    async def test_sync_function_timing(self):
        """测试：同步函数计时"""
        @timing()
        def sync_func():
            sleep(0.01)
            return "result"

        with patch('app.core.decorators.logger') as mock_logger:
            result = sync_func()

            assert result == "result"
            assert mock_logger.debug.called


# ========================================================================
# 测试类：singleton
# ========================================================================

class TestSingleton:
    """
    类级注释：测试单例装饰器
    测试范围：单例行为、参数处理
    """

    def test_returns_same_instance(self):
        """测试：返回同一实例"""
        @singleton
        class TestClass:
            def __init__(self, value=None):
                self.value = value

        instance1 = TestClass("value1")
        instance2 = TestClass("value2")

        # 验证：返回同一实例
        assert instance1 is instance2
        # 验证：使用第一次的值
        assert instance1.value == "value1"

    def test_multiple_classes_independent(self):
        """测试：不同类的单例独立"""
        @singleton
        class ClassA:
            pass

        @singleton
        class ClassB:
            pass

        a1 = ClassA()
        a2 = ClassA()
        b1 = ClassB()
        b2 = ClassB()

        assert a1 is a2
        assert b1 is b2
        assert a1 is not b1

    def test_wrapper_attribute_access(self):
        """测试：包装器属性访问"""
        @singleton
        class TestClass:
            class_attr = "value"

        instance = TestClass()

        # 验证：可以访问类属性
        assert instance.class_attr == "value"


# ========================================================================
# 测试类：cached_property
# ========================================================================

class TestCachedProperty:
    """
    类级注释：测试缓存属性装饰器
    测试范围：缓存行为、多次访问
    """

    def test_caches_property_value(self):
        """测试：缓存属性值"""
        call_count = [0]

        class TestClass:
            @cached_property
            def expensive_prop(self):
                call_count[0] += 1
                return "computed_value"

        instance = TestClass()

        # 第一次访问
        value1 = instance.expensive_prop
        # 第二次访问
        value2 = instance.expensive_prop

        assert value1 == value2
        assert call_count[0] == 1  # 只计算一次

    def test_different_instances_independent(self):
        """测试：不同实例独立缓存"""
        class TestClass:
            @cached_property
            def prop(self):
                return id(self)

        instance1 = TestClass()
        instance2 = TestClass()

        # 验证：不同实例有独立的缓存
        assert instance1.prop != instance2.prop

    def test_none_attribute(self):
        """测试：访问未缓存属性时返回描述符"""
        class TestClass:
            @cached_property
            def prop(self):
                return "value"

        # 通过类访问返回描述符本身
        descriptor = TestClass.prop
        assert isinstance(descriptor, _CachedProperty)


# ========================================================================
# 测试类：suppress_exceptions
# ========================================================================

class TestSuppressExceptions:
    """
    类级注释：测试异常抑制装饰器
    测试范围：异常捕获、默认返回值、日志记录
    """

    @pytest.mark.asyncio
    async def test_suppresses_specific_exception(self):
        """测试：抑制指定异常"""
        @suppress_exceptions(ValueError, default_return="fallback")
        async def func():
            raise ValueError("错误")

        result = await func()

        assert result == "fallback"

    @pytest.mark.asyncio
    async def test_suppresses_all_exceptions(self):
        """测试：不指定异常时抑制所有"""
        @suppress_exceptions(default_return=None)
        async def func():
            raise RuntimeError("任何错误")

        result = await func()

        assert result is None

    @pytest.mark.asyncio
    async def test_no_exception_no_suppression(self):
        """测试：无异常时正常返回"""
        @suppress_exceptions(ValueError)
        async def func():
            return "normal"

        result = await func()

        assert result == "normal"

    @pytest.mark.asyncio
    async def test_logs_error_when_enabled(self):
        """测试：记录错误日志"""
        @suppress_exceptions(ValueError, log_error=True)
        async def func():
            raise ValueError("测试错误")

        with patch('app.core.decorators.logger') as mock_logger:
            await func()

            assert mock_logger.warning.called

    @pytest.mark.asyncio
    async def test_no_log_when_disabled(self):
        """测试：禁用日志时不记录"""
        @suppress_exceptions(ValueError, log_error=False)
        async def func():
            raise ValueError("测试错误")

        with patch('app.core.decorators.logger') as mock_logger:
            await func()

            assert not mock_logger.warning.called

    @pytest.mark.asyncio
    async def test_sync_function_suppression(self):
        """测试：同步函数异常抑制"""
        @suppress_exceptions(ValueError, default_return=0)
        def func():
            raise ValueError("错误")

        result = func()

        assert result == 0


# ========================================================================
# 测试类：validate_permissions
# ========================================================================

class TestValidatePermissions:
    """
    类级注释：测试权限验证装饰器
    测试范围：权限检查、用户查找、错误处理
    """

    @pytest.mark.asyncio
    async def test_pass_with_valid_permissions(self):
        """测试：有效权限通过验证"""
        class User:
            permissions = ["read", "write"]

        @validate_permissions("read", "write")
        async def func(user):
            return "success"

        user = User()
        result = await func(user=user)

        assert result == "success"

    @pytest.mark.asyncio
    async def test_fails_with_missing_permissions(self):
        """测试：缺少权限时失败"""
        class User:
            permissions = ["read"]

        @validate_permissions("write")
        async def func(user):
            return "success"

        user = User()

        with pytest.raises(HTTPException) as exc_info:
            await func(user=user)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_fails_with_no_user(self):
        """测试：无用户时返回401"""
        @validate_permissions("read")
        async def func():
            return "success"

        with pytest.raises(HTTPException) as exc_info:
            await func()

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_finds_user_in_args(self):
        """测试：在位置参数中查找用户"""
        class User:
            permissions = ["admin"]

        @validate_permissions("admin")
        async def func(user):
            return "success"

        user = User()
        result = await func(user)

        assert result == "success"

    @pytest.mark.asyncio
    async def test_string_permissions(self):
        """测试：字符串类型权限"""
        class User:
            permissions = "read"  # 字符串而非列表

        @validate_permissions("read")
        async def func(user):
            return "success"

        user = User()
        result = await func(user=user)

        assert result == "success"


# ========================================================================
# 测试类：rate_limit
# ========================================================================

class TestRateLimit:
    """
    类级注释：测试速率限制装饰器
    测试范围：调用限制、时间窗口、清理过期记录
    """

    @pytest.mark.asyncio
    async def test_allows_within_limit(self):
        """测试：限制内允许调用"""
        @rate_limit(max_calls=3, period_seconds=60)
        async def func():
            return "success"

        # 调用3次应都成功
        for _ in range(3):
            result = await func()
            assert result == "success"

    @pytest.mark.asyncio
    async def test_blocks_over_limit(self):
        """测试：超过限制时阻塞"""
        @rate_limit(max_calls=2, period_seconds=60)
        async def func():
            return "success"

        # 调用2次成功
        for _ in range(2):
            await func()

        # 第3次应被限制
        with pytest.raises(HTTPException) as exc_info:
            await func()

        assert exc_info.value.status_code == 429

    @pytest.mark.asyncio
    async def test_resets_after_period(self):
        """测试：时间窗口结束后重置"""
        import time as time_module

        @rate_limit(max_calls=1, period_seconds=1)
        async def func():
            return "success"

        # 第一次调用成功
        result1 = await func()
        assert result1 == "success"

        # 模拟时间流逝
        with patch('time.time', return_value=time_module.time() + 2):
            # 时间窗口后应允许再次调用
            result2 = await func()
            assert result2 == "success"


# ========================================================================
# 测试类：内部辅助函数
# ========================================================================

class TestHelperFunctions:
    """
    类级注释：测试内部辅助函数
    测试范围：重试判断、退避计算、参数过滤
    """

    def test_is_retryable_error_connection_error(self):
        """测试：连接错误可重试"""
        assert _is_retryable_error(ConnectionError("连接失败")) is True

    def test_is_retryable_error_timeout(self):
        """测试：超时可重试"""
        assert _is_retryable_error(TimeoutError("超时")) is True

    def test_is_retryable_error_by_message(self):
        """测试：根据错误消息判断可重试"""
        assert _is_retryable_error(Exception("timeout occurred")) is True
        assert _is_retryable_error(Exception("connection lost")) is True
        assert _is_retryable_error(Exception("rate limit exceeded")) is True
        assert _is_retryable_error(Exception("503 Service Unavailable")) is True

    def test_is_retryable_error_non_retryable(self):
        """测试：不可重试错误"""
        assert _is_retryable_error(ValueError("参数错误")) is False
        assert _is_retryable_error(Exception("unknown error")) is False

    def test_calculate_backoff_exponential(self):
        """测试：指数退避计算"""
        assert _calculate_backoff(0, 0.5, "exponential") == 0.5
        assert _calculate_backoff(1, 0.5, "exponential") == 1.0
        assert _calculate_backoff(2, 0.5, "exponential") == 2.0

    def test_calculate_backoff_linear(self):
        """测试：线性退避计算"""
        assert _calculate_backoff(0, 0.5, "linear") == 0.5
        assert _calculate_backoff(1, 0.5, "linear") == 1.0
        assert _calculate_backoff(2, 0.5, "linear") == 1.5

    def test_calculate_backoff_fixed(self):
        """测试：固定退避计算"""
        assert _calculate_backoff(0, 0.5, "fixed") == 0.5
        assert _calculate_backoff(1, 0.5, "fixed") == 0.5
        assert _calculate_backoff(2, 0.5, "fixed") == 0.5

    def test_calculate_backoff_immediate(self):
        """测试：立即重试（无等待）"""
        assert _calculate_backoff(0, 0.5, "immediate") == 0
        assert _calculate_backoff(1, 0.5, "immediate") == 0

    def test_filter_sensitive_args(self):
        """测试：过滤敏感参数"""
        kwargs = {
            "name": "test",
            "password": "secret123",
            "api_key": "key456",
            "normal_value": "public"
        }

        result = _filter_sensitive_args((), kwargs)

        # 验证：敏感参数被脱敏
        assert "***" in result["kwargs"]["password"]
        assert "***" in result["kwargs"]["api_key"]
        assert result["kwargs"]["normal_value"] == "public"

    def test_filter_sensitive_empty_value(self):
        """测试：空敏感值处理"""
        kwargs = {"password": ""}

        result = _filter_sensitive_args((), kwargs)

        assert result["kwargs"]["password"] == "***"


# ========================================================================
# 测试类：内部类
# ========================================================================

class TestInternalClasses:
    """
    类级注释：测试内部包装类
    测试范围：_CachedProperty, _SingletonWrapper
    """

    def test_cached_property_get_on_instance(self):
        """测试：_CachedProperty在实例上的行为"""
        descriptor = _CachedProperty(lambda self: "value")

        class TestClass:
            pass

        instance = TestClass()
        result = descriptor.__get__(instance, TestClass)

        assert result == "value"

    def test_cached_property_get_on_class(self):
        """测试：_CachedProperty在类上的行为"""
        descriptor = _CachedProperty(lambda self: "value")

        result = descriptor.__get__(None, object)

        assert result is descriptor

    def test_singleton_wrapper_call(self):
        """测试：_SingletonWrapper的__call__方法"""
        class TestClass:
            def __init__(self, value):
                self.value = value

        wrapper = _SingletonWrapper(TestClass)
        instance1 = wrapper("value1")
        instance2 = wrapper("value2")

        assert instance1 is instance2
        assert instance1.value == "value1"

    def test_singleton_wrapper_getattr(self):
        """测试：_SingletonWrapper的属性访问"""
        class TestClass:
            class_attr = "value"

        wrapper = _SingletonWrapper(TestClass)

        # 验证：可以访问类属性
        assert wrapper.class_attr == "value"


# ========================================================================
# 测试类：边界情况
# ========================================================================

class TestDecoratorsEdgeCases:
    """
    类级注释：测试装饰器边界情况
    测试范围：None处理、空参数、极端情况
    """

    @pytest.mark.asyncio
    async def test_retry_with_zero_max_retries(self):
        """测试：max_retries为0时不重试"""
        call_count = [0]

        @retry_on_failure(max_retries=0)
        async def func():
            call_count[0] += 1
            raise ConnectionError("失败")

        with pytest.raises(ConnectionError):
            await func()

        # 验证：只调用一次（不重试）
        assert call_count[0] == 1

    @pytest.mark.asyncio
    async def test_cache_with_no_args(self):
        """测试：无参数函数的缓存"""
        call_count = [0]

        @cache_response(ttl_seconds=60)
        async def func():
            call_count[0] += 1
            return "result"

        await func()
        await func()

        assert call_count[0] == 1

    @pytest.mark.asyncio
    async def test_log_execution_with_no_args_function(self):
        """测试：无参数函数的日志"""
        @log_execution()
        async def func():
            return "result"

        with patch('app.core.decorators.logger') as mock_logger:
            await func()

            assert mock_logger.info.called

    @pytest.mark.asyncio
    async def test_rate_limit_with_different_callers(self):
        """测试：不同调用者独立计数"""
        @rate_limit(max_calls=1, period_seconds=60)
        async def func(self):
            return "success"

        # 模拟不同调用者
        caller1 = MagicMock()
        caller2 = MagicMock()

        result1 = await func(caller1)
        result2 = await func(caller2)

        # 不同调用者应有独立的计数
        assert result1 == "success"
        assert result2 == "success"
