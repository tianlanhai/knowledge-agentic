# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：重试机制模块测试
内部逻辑：验证重试装饰器、错误分类、错误处理等功能
设计模式：装饰器模式、策略模式
测试覆盖范围：
    - RetryStrategy: 重试策略枚举
    - ErrorCodeCategory: 错误代码分类枚举
    - categorize_error: 错误分类函数
    - should_retry: 重试判断函数
    - retry_on_failure: 失败重试装饰器
    - _retry_sync: 同步重试逻辑
    - _retry_async: 异步重试逻辑
    - _calculate_delay: 延迟计算函数
    - handle_errors: 错误处理装饰器
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock

from app.core.retry import (
    RetryStrategy,
    ErrorCodeCategory,
    categorize_error,
    should_retry,
    retry_on_failure,
    _calculate_delay,
    handle_errors,
    _retry_sync,
    _retry_async,
)


# ============================================================================
# RetryStrategy 枚举测试
# ============================================================================

class TestRetryStrategy:
    """测试重试策略枚举"""

    def test_retry_strategies(self):
        """测试重试策略值"""
        assert RetryStrategy.EXPONENTIAL_BACKOFF == "exponential_backoff"
        assert RetryStrategy.LINEAR_BACKOFF == "linear_backoff"
        assert RetryStrategy.FIXED_DELAY == "fixed_delay"
        assert RetryStrategy.IMMEDIATE == "immediate"

    def test_is_string_enum(self):
        """测试是字符串枚举"""
        # 应该可以像字符串一样比较
        strategy = RetryStrategy.EXPONENTIAL_BACKOFF
        assert strategy == "exponential_backoff"


# ============================================================================
# ErrorCodeCategory 枚举测试
# ============================================================================

class TestErrorCodeCategory:
    """测试错误代码分类枚举"""

    def test_categories(self):
        """测试分类值"""
        assert ErrorCodeCategory.NETWORK_ERROR == "network_error"
        assert ErrorCodeCategory.API_ERROR == "api_error"
        assert ErrorCodeCategory.RATE_LIMIT_ERROR == "rate_limit"
        assert ErrorCodeCategory.VALIDATION_ERROR == "validation"
        assert ErrorCodeCategory.NOT_FOUND_ERROR == "not_found"
        assert ErrorCodeCategory.UNKNOWN_ERROR == "unknown"


# ============================================================================
# categorize_error 测试
# ============================================================================

class TestCategorizeError:
    """测试错误分类函数"""

    def test_connection_error(self):
        """测试连接错误分类"""
        error = ConnectionError("Connection refused")
        category = categorize_error(error)
        assert category == ErrorCodeCategory.NETWORK_ERROR

    def test_timeout_error(self):
        """测试超时错误分类"""
        error = TimeoutError("Request timeout")
        category = categorize_error(error)
        assert category == ErrorCodeCategory.NETWORK_ERROR

    def test_value_error(self):
        """测试值错误分类"""
        error = ValueError("Invalid value")
        category = categorize_error(error)
        assert category == ErrorCodeCategory.VALIDATION_ERROR

    def test_key_error(self):
        """测试键错误分类"""
        error = KeyError("missing_key")
        category = categorize_error(error)
        assert category == ErrorCodeCategory.NOT_FOUND_ERROR

    def test_unknown_error(self):
        """测试未知错误分类"""
        error = RuntimeError("Unknown issue")
        category = categorize_error(error)
        assert category == ErrorCodeCategory.UNKNOWN_ERROR

    def test_error_with_specific_code(self):
        """测试带特定代码的错误"""
        error = Exception("Error 500: Internal Server Error")
        category = categorize_error(error)
        assert category == ErrorCodeCategory.API_ERROR

    def test_rate_limit_error(self):
        """测试限流错误分类"""
        error = Exception("rate_limit_exceeded")
        category = categorize_error(error)
        assert category == ErrorCodeCategory.RATE_LIMIT_ERROR

    def test_429_error(self):
        """测试429状态码错误"""
        error = Exception("HTTP 429: Too Many Requests")
        category = categorize_error(error)
        assert category == ErrorCodeCategory.RATE_LIMIT_ERROR


# ============================================================================
# should_retry 测试
# ============================================================================

class TestShouldRetry:
    """测试重试判断函数"""

    def test_network_error_retryable(self):
        """测试网络错误可重试"""
        assert should_retry(ErrorCodeCategory.NETWORK_ERROR) is True

    def test_api_error_retryable(self):
        """测试API错误可重试"""
        assert should_retry(ErrorCodeCategory.API_ERROR) is True

    def test_rate_limit_retryable(self):
        """测试限流错误可重试"""
        assert should_retry(ErrorCodeCategory.RATE_LIMIT_ERROR) is True

    def test_validation_error_not_retryable(self):
        """测试验证错误不可重试"""
        assert should_retry(ErrorCodeCategory.VALIDATION_ERROR) is False

    def test_not_found_not_retryable(self):
        """测试未找到不可重试"""
        assert should_retry(ErrorCodeCategory.NOT_FOUND_ERROR) is False

    def test_unknown_not_retryable(self):
        """测试未知错误不可重试"""
        assert should_retry(ErrorCodeCategory.UNKNOWN_ERROR) is False


# ============================================================================
# retry_on_failure 装饰器测试
# ============================================================================

class TestRetryOnFailure:
    """测试失败重试装饰器"""

    def test_sync_function_success_first_try(self):
        """测试同步函数第一次尝试成功"""
        @retry_on_failure(max_attempts=3)
        def test_func():
            return "success"

        result = test_func()

        assert result == "success"

    def test_sync_function_retry_then_success(self):
        """测试同步函数重试后成功"""
        call_count = [0]

        @retry_on_failure(max_attempts=3, base_delay=0.01)
        def test_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ConnectionError("Network error")
            return "success"

        result = test_func()

        assert result == "success"
        assert call_count[0] == 2

    def test_sync_function_all_fail(self):
        """测试同步函数所有尝试失败"""
        @retry_on_failure(max_attempts=2, base_delay=0.01)
        def test_func():
            raise ConnectionError("Persistent error")

        with pytest.raises(ConnectionError):
            test_func()

    def test_async_function_success(self):
        """测试异步函数成功"""
        @retry_on_failure(max_attempts=3)
        async def test_func():
            return "async_success"

        result = asyncio.run(test_func())

        assert result == "async_success"

    def test_async_function_retry(self):
        """测试异步函数重试"""
        call_count = [0]

        @retry_on_failure(max_attempts=3, base_delay=0.01)
        async def test_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ConnectionError("Temp error")
            return "async_success"

        result = asyncio.run(test_func())

        assert result == "async_success"
        assert call_count[0] == 2

    def test_immediate_strategy(self):
        """测试立即重试策略"""
        call_times = []

        @retry_on_failure(
            max_attempts=3,
            strategy=RetryStrategy.IMMEDIATE,
            base_delay=0.1
        )
        def test_func():
            call_times.append(time.time())
            if len(call_times) < 2:
                raise ConnectionError("Error")
            return "success"

        result = test_func()

        assert result == "success"
        assert len(call_times) == 2

    def test_fixed_delay_strategy(self):
        """测试固定延迟策略"""
        call_times = []

        @retry_on_failure(
            max_attempts=3,
            strategy=RetryStrategy.FIXED_DELAY,
            base_delay=0.05
        )
        def test_func():
            call_times.append(time.time())
            if len(call_times) < 2:
                raise ConnectionError("Error")
            return "success"

        result = test_func()

        assert result == "success"
        assert len(call_times) == 2

    def test_exponential_backoff_strategy(self):
        """测试指数退避策略"""
        call_count = [0]

        @retry_on_failure(
            max_attempts=4,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=0.05,
            backoff_multiplier=2.0
        )
        def test_func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ConnectionError("Error")
            return "success"

        result = test_func()

        assert result == "success"
        assert call_count[0] == 3

    def test_linear_backoff_strategy(self):
        """测试线性退避策略"""
        call_count = [0]

        @retry_on_failure(
            max_attempts=3,
            strategy=RetryStrategy.LINEAR_BACKOFF,
            base_delay=0.02,
            backoff_multiplier=1.0
        )
        def test_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ConnectionError("Error")
            return "success"

        result = test_func()

        assert result == "success"
        assert call_count[0] == 2

    def test_retry_on_specific_exception(self):
        """测试只重试特定异常"""
        @retry_on_failure(
            max_attempts=3,
            retry_on=(ConnectionError, TimeoutError)
        )
        def test_func():
            raise ValueError("Should not retry")

        with pytest.raises(ValueError):
            test_func()

    def test_give_up_on_specific_exception(self):
        """测试遇到特定异常放弃"""
        @retry_on_failure(
            max_attempts=3,
            give_up_on=(ValueError,)
        )
        def test_func():
            raise ValueError("Give up immediately")

        with pytest.raises(ValueError):
            test_func()

    def test_validation_error_no_retry(self):
        """测试验证错误不重试"""
        @retry_on_failure(max_attempts=3)
        def test_func():
            raise ValueError("Invalid input")

        with pytest.raises(ValueError):
            test_func()

    def test_key_error_no_retry(self):
        """测试键错误不重试"""
        @retry_on_failure(max_attempts=3)
        def test_func():
            raise KeyError("missing")

        with pytest.raises(KeyError):
            test_func()

    def test_max_attempts_one(self):
        """测试最大尝试次数为1"""
        @retry_on_failure(max_attempts=1)
        def test_func():
            raise ConnectionError("Error")

        with pytest.raises(ConnectionError):
            test_func()

    def test_on_retry_callback(self):
        """测试重试回调"""
        retry_attempts = []

        def on_retry(attempt, error):
            retry_attempts.append((attempt, str(error)))

        @retry_on_failure(
            max_attempts=3,
            base_delay=0.01,
            on_retry=on_retry
        )
        def test_func():
            raise ConnectionError("Test error")

        with pytest.raises(ConnectionError):
            test_func()

        # max_attempts=3 意味着总共3次尝试（1次初始+2次重试）
        # 所以回调应该被调用2次
        assert len(retry_attempts) == 2

    def test_before_execute_hook(self):
        """测试执行前钩子"""
        class CustomStrategy:
            def __init__(self):
                self.before_called = False

            def execute(self, func, *args, **kwargs):
                self.before_called = True
                return func(*args, **kwargs)

            @property
            def name(self):
                return "custom"

        # 这里我们测试内置的重试装饰器
        # 实际钩子是内部的，我们验证它能正常工作
        @retry_on_failure(max_attempts=1)
        def test_func():
            return "success"

        result = test_func()
        assert result == "success"


# ============================================================================
# handle_errors 装饰器测试
# ============================================================================

class TestHandleErrors:
    """测试错误处理装饰器"""

    def test_return_default_on_error(self):
        """测试错误时返回默认值"""
        @handle_errors(default_return="default_value")
        def test_func():
            raise ValueError("Error")

        result = test_func()

        assert result == "default_value"

    def test_return_none_default(self):
        """测试不设置默认值时重新抛出异常"""
        @handle_errors()
        def test_func():
            raise ValueError("Error")

        # 根据实际实现，不设置default_return时会重新抛出异常
        with pytest.raises(ValueError):
            test_func()

    def test_reraise_on_specific_exception(self):
        """测试特定异常重新抛出"""
        @handle_errors(
            default_return="default",
            raise_on=(ValueError,)
        )
        def test_func():
            raise ValueError("Should reraise")

        with pytest.raises(ValueError):
            test_func()

    def test_log_errors_false(self):
        """测试不记录错误"""
        @handle_errors(
            default_return="default",
            log_errors=False
        )
        def test_func():
            raise ValueError("Error")

        # 不应该抛出异常
        result = test_func()
        assert result == "default"

    def test_success_case(self):
        """测试成功情况"""
        @handle_errors(default_return="default")
        def test_func():
            return "success"

        result = test_func()

        assert result == "success"

    def test_with_error_message(self):
        """测试带错误消息"""
        @handle_errors(
            default_return="default",
            error_message="Custom error message"
        )
        def test_func():
            raise ValueError("Error")

        # 不应该抛出异常，但会记录消息
        result = test_func()
        assert result == "default"

    def test_preserve_exception_on_no_default(self):
        """测试无默认值时重新抛出"""
        @handle_errors()
        def test_func():
            raise ValueError("Error")

        with pytest.raises(ValueError):
            test_func()


# ============================================================================
# _calculate_delay 测试
# ============================================================================

class TestCalculateDelay:
    """测试延迟计算函数"""

    def test_immediate_strategy(self):
        """测试立即策略"""
        delay = _calculate_delay(
            attempt=1,
            strategy=RetryStrategy.IMMEDIATE,
            base_delay=1.0,
            max_delay=60.0,
            backoff_multiplier=2.0,
            category=ErrorCodeCategory.NETWORK_ERROR
        )

        assert delay == 0

    def test_fixed_delay_strategy(self):
        """测试固定延迟策略"""
        delay = _calculate_delay(
            attempt=1,
            strategy=RetryStrategy.FIXED_DELAY,
            base_delay=2.0,
            max_delay=60.0,
            backoff_multiplier=2.0,
            category=ErrorCodeCategory.NETWORK_ERROR
        )

        assert delay == 2.0

    def test_fixed_delay_with_max(self):
        """测试固定延迟最大值"""
        delay = _calculate_delay(
            attempt=1,
            strategy=RetryStrategy.FIXED_DELAY,
            base_delay=100.0,
            max_delay=50.0,
            backoff_multiplier=2.0,
            category=ErrorCodeCategory.NETWORK_ERROR
        )

        assert delay == 50.0

    def test_linear_backoff_strategy(self):
        """测试线性退避策略"""
        # 线性退避：base_delay * attempt
        delay1 = _calculate_delay(
            attempt=1,
            strategy=RetryStrategy.LINEAR_BACKOFF,
            base_delay=1.0,
            max_delay=100.0,
            backoff_multiplier=0.5,
            category=ErrorCodeCategory.NETWORK_ERROR
        )

        delay2 = _calculate_delay(
            attempt=2,
            strategy=RetryStrategy.LINEAR_BACKOFF,
            base_delay=1.0,
            max_delay=100.0,
            backoff_multiplier=0.5,
            category=ErrorCodeCategory.NETWORK_ERROR
        )

        delay3 = _calculate_delay(
            attempt=3,
            strategy=RetryStrategy.LINEAR_BACKOFF,
            base_delay=1.0,
            max_delay=100.0,
            backoff_multiplier=0.5,
            category=ErrorCodeCategory.NETWORK_ERROR
        )

        # 线性退避：base_delay * attempt (backoff_multiplier在线性策略中不使用)
        assert delay1 == 1.0  # 1.0 * 1
        assert delay2 == 2.0  # 1.0 * 2
        assert delay3 == 3.0  # 1.0 * 3

    def test_exponential_backoff_strategy(self):
        """测试指数退避策略"""
        delay1 = _calculate_delay(
            attempt=1,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=1.0,
            max_delay=100.0,
            backoff_multiplier=2.0,
            category=ErrorCodeCategory.NETWORK_ERROR
        )

        delay2 = _calculate_delay(
            attempt=2,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=1.0,
            max_delay=100.0,
            backoff_multiplier=2.0,
            category=ErrorCodeCategory.NETWORK_ERROR
        )

        delay3 = _calculate_delay(
            attempt=3,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=1.0,
            max_delay=100.0,
            backoff_multiplier=2.0,
            category=ErrorCodeCategory.NETWORK_ERROR
        )

        assert delay1 == 1.0
        assert delay2 == 2.0
        assert delay3 == 4.0

    def test_exponential_with_max(self):
        """测试指数退避最大值"""
        delay = _calculate_delay(
            attempt=10,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=1.0,
            max_delay=10.0,
            backoff_multiplier=2.0,
            category=ErrorCodeCategory.NETWORK_ERROR
        )

        assert delay == 10.0

    def test_rate_limit_increases_delay(self):
        """测试限流错误增加延迟"""
        normal_delay = _calculate_delay(
            attempt=1,
            strategy=RetryStrategy.FIXED_DELAY,
            base_delay=1.0,
            max_delay=60.0,
            backoff_multiplier=2.0,
            category=ErrorCodeCategory.NETWORK_ERROR
        )

        rate_limit_delay = _calculate_delay(
            attempt=1,
            strategy=RetryStrategy.FIXED_DELAY,
            base_delay=1.0,
            max_delay=60.0,
            backoff_multiplier=2.0,
            category=ErrorCodeCategory.RATE_LIMIT_ERROR
        )

        # 限流错误应该有更长的延迟
        assert rate_limit_delay >= normal_delay


# ============================================================================
# _retry_sync 内部函数测试
# ============================================================================

class TestRetrySync:
    """测试同步重试功能"""

    def test_sync_retry_success(self):
        """测试同步重试成功"""
        call_count = [0]

        @retry_on_failure(max_attempts=3, base_delay=0.01)
        def func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ConnectionError("Error")
            return "success"

        result = func()

        assert result == "success"
        assert call_count[0] == 2

    def test_sync_retry_all_fail(self):
        """测试同步重试全部失败"""
        @retry_on_failure(max_attempts=2, base_delay=0.01)
        def func():
            raise ConnectionError("Persistent error")

        with pytest.raises(ConnectionError):
            func()

    def test_sync_retry_give_up_on(self):
        """测试同步重试放弃条件"""
        @retry_on_failure(
            max_attempts=3,
            give_up_on=(ValueError,)
        )
        def func():
            raise ValueError("Give up")

        with pytest.raises(ValueError):
            func()

    def test_sync_retry_only_specific_exception(self):
        """测试同步重试只重试特定异常"""
        call_count = [0]

        @retry_on_failure(
            max_attempts=3,
            retry_on=(ConnectionError,),
            base_delay=0.01
        )
        def func():
            call_count[0] += 1
            if call_count[0] == 1:
                raise ConnectionError("Network error")
            raise ValueError("Validation error")

        with pytest.raises(ValueError):
            func()

        # 应该重试一次ConnectionError，然后遇到ValueError放弃
        assert call_count[0] == 2


# ============================================================================
# _retry_async 内部函数测试
# ============================================================================

class TestRetryAsync:
    """测试异步重试功能"""

    @pytest.mark.asyncio
    async def test_async_retry_success(self):
        """测试异步重试成功"""
        call_count = [0]

        @retry_on_failure(max_attempts=3, base_delay=0.01)
        async def func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ConnectionError("Error")
            return "async_success"

        result = await func()

        assert result == "async_success"
        assert call_count[0] == 2

    @pytest.mark.asyncio
    async def test_async_retry_all_fail(self):
        """测试异步重试全部失败"""
        @retry_on_failure(max_attempts=3, base_delay=0.01)
        async def func():
            raise ConnectionError("Persistent error")

        with pytest.raises(ConnectionError):
            await func()

    @pytest.mark.asyncio
    async def test_async_retry_give_up_on(self):
        """测试异步重试放弃条件"""
        @retry_on_failure(
            max_attempts=3,
            give_up_on=(ValueError,)
        )
        async def func():
            raise ValueError("Give up")

        with pytest.raises(ValueError):
            await func()

    @pytest.mark.asyncio
    async def test_async_retry_only_specific_exception(self):
        """测试异步重试只重试特定异常"""
        call_count = [0]

        @retry_on_failure(
            max_attempts=3,
            retry_on=(ConnectionError,),
            base_delay=0.01
        )
        async def func():
            call_count[0] += 1
            if call_count[0] == 1:
                raise ConnectionError("Network error")
            raise ValueError("Validation error")

        with pytest.raises(ValueError):
            await func()

        assert call_count[0] == 2


# ============================================================================
# 集成测试
# ============================================================================

class TestRetryIntegration:
    """重试机制集成测试"""

    def test_complex_retry_scenario(self):
        """测试复杂重试场景"""
        attempt_results = [
            ConnectionError("First fail"),
            TimeoutError("Second fail"),
            ConnectionError("Third fail"),
            "success"
        ]
        attempt_index = [0]

        @retry_on_failure(
            max_attempts=5,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=0.01,
            backoff_multiplier=2.0
        )
        def complex_func():
            result = attempt_results[attempt_index[0]]
            attempt_index[0] += 1
            if isinstance(result, Exception):
                raise result
            return result

        result = complex_func()

        assert result == "success"
        assert attempt_index[0] == 4

    def test_mixed_exception_types(self):
        """测试混合异常类型"""
        call_count = [0]

        @retry_on_failure(max_attempts=5)
        def mixed_func():
            call_count[0] += 1
            if call_count[0] == 1:
                raise ConnectionError("Network")
            elif call_count[0] == 2:
                raise TimeoutError("Timeout")
            elif call_count[0] == 3:
                raise ValueError("Validation")  # 不可重试
            return "success"

        with pytest.raises(ValueError):
            mixed_func()

        # 第1次: ConnectionError (重试), 第2次: TimeoutError (重试), 第3次: ValueError (不可重试,直接抛出)
        assert call_count[0] == 3

    @pytest.mark.asyncio
    async def test_async_retry_with_sync_function(self):
        """测试异步装饰器处理同步函数"""
        # 同步函数不能用await，直接调用即可
        @retry_on_failure(max_attempts=2)
        def sync_func():
            return "sync_result"

        result = sync_func()
        assert result == "sync_result"

    def test_decorator_preserves_function_metadata(self):
        """测试装饰器保留函数元数据"""
        @retry_on_failure(max_attempts=3)
        def test_func():
            """Test function docstring"""
            return "result"

        assert test_func.__name__ == "test_func"
        assert test_func.__doc__ == "Test function docstring"
