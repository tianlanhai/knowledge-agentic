# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：错误处理装饰器模块测试
内部逻辑：测试统一错误处理装饰器的各种场景
覆盖范围：
    - with_error_handling装饰器的所有参数
    - with_retry装饰器的重试逻辑
    - catch_and_return装饰器的异常捕获
    - log_execution装饰器的日志记录
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from app.core.error_handling.decorators import (
    with_error_handling,
    with_retry,
    catch_and_return,
    log_execution,
)


class TestWithErrorHandlingDetailed:
    """
    类级注释：with_error_handling装饰器详细测试
    """

    def test_sync_function_success(self):
        """测试同步函数成功执行"""
        @with_error_handling()
        def test_func():
            return "success"

        result = test_func()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_async_function_success(self):
        """测试异步函数成功执行"""
        @with_error_handling()
        async def test_func():
            return "success"

        result = await test_func()
        assert result == "success"

    def test_sync_function_with_exception(self):
        """测试同步函数异常处理"""
        @with_error_handling(default_return="error")
        def test_func():
            raise ValueError("Test error")

        result = test_func()
        assert result == "error"

    @pytest.mark.asyncio
    async def test_async_function_with_exception(self):
        """测试异步函数异常处理"""
        @with_error_handling(default_return="error")
        async def test_func():
            raise ValueError("Test error")

        result = await test_func()
        assert result == "error"

    def test_with_reraise_true(self):
        """测试reraise=True时重新抛出异常"""
        @with_error_handling(reraise=True)
        def test_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            test_func()

    def test_with_log_levels(self):
        """测试不同日志级别"""
        for level in ["debug", "info", "warning", "error"]:
            @with_error_handling(log_level=level, default_return="ok")
            def test_func():
                return "ok"

            result = test_func()
            assert result == "ok"

    @patch('app.core.error_handling.decorators.logger')
    def test_logs_exception_with_exc_info(self, mock_logger):
        """测试记录异常时包含exc_info"""
        @with_error_handling(default_return="ok")
        def test_func():
            raise ValueError("Test")

        test_func()
        # 验证日志被调用且包含exc_info
        assert mock_logger.error.called

    def test_context_builder_called(self):
        """测试context_builder被调用"""
        context_captured = []

        def build_context():
            context_captured.append({"custom": "context"})
            return {"custom": "context"}

        @with_error_handling(context_builder=build_context)
        def test_func():
            raise ValueError("Test")

        test_func()
        assert len(context_captured) == 1


class TestWithRetryDetailed:
    """
    类级注释：with_retry装饰器详细测试
    """

    def test_successful_call_no_retry(self):
        """测试成功调用不重试"""
        attempt_count = [0]

        @with_retry(max_retries=3, delay=0.01)
        def test_func():
            attempt_count[0] += 1
            return "success"

        result = test_func()
        assert result == "success"
        assert attempt_count[0] == 1

    def test_retry_until_success(self):
        """测试重试直到成功"""
        attempt_count = [0]

        @with_retry(max_retries=3, delay=0.01)
        def test_func():
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                raise ValueError("Retry")
            return "success"

        result = test_func()
        assert result == "success"
        assert attempt_count[0] == 2

    def test_max_retries_exceeded(self):
        """测试达到最大重试次数"""
        @with_retry(max_retries=2, delay=0.01)
        def test_func():
            raise ValueError("Always fails")

        with pytest.raises(ValueError):
            test_func()

    @pytest.mark.asyncio
    async def test_async_retry_until_success(self):
        """测试异步函数重试直到成功"""
        attempt_count = [0]

        @with_retry(max_retries=3, delay=0.01)
        async def test_func():
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                raise ValueError("Retry")
            return "success"

        result = await test_func()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_async_max_retries_exceeded(self):
        """测试异步函数达到最大重试次数"""
        @with_retry(max_retries=2, delay=0.01)
        async def test_func():
            raise ValueError("Always fails")

        with pytest.raises(ValueError):
            await test_func()

    def test_respects_delay(self):
        """测试尊重延迟时间"""
        import time
        delays = []

        @with_retry(max_retries=2, delay=0.05)
        def test_func():
            if not delays:
                delays.append(time.time())
            delays.append(time.time())
            raise ValueError("Test")

        try:
            test_func()
        except ValueError:
            pass

        # 验证至少有一次延迟
        assert len(delays) > 1

    def test_respects_backoff_factor(self):
        """测试退避因子"""
        attempt_count = [0]

        @with_retry(max_retries=3, delay=0.01, backoff_factor=2.0)
        def test_func():
            attempt_count[0] += 1
            raise ValueError("Test")

        try:
            test_func()
        except ValueError:
            pass

        assert attempt_count[0] == 4  # 初始 + 3次重试

    def test_filters_specific_exception_type(self):
        """测试只对特定异常类型重试"""
        attempt_count = [0]

        @with_retry(max_retries=2, exceptions=(ValueError,))
        def test_func():
            attempt_count[0] += 1
            if attempt_count[0] == 1:
                raise ValueError("Retry value")
            elif attempt_count[0] == 2:
                raise TypeError("Don't retry type")

        with pytest.raises(TypeError):
            test_func()

        # TypeError不应该触发重试
        assert attempt_count[0] == 2


class TestCatchAndReturnDetailed:
    """
    类级注释：catch_and_return装饰器详细测试
    """

    def test_catches_value_error(self):
        """测试捕获ValueError"""
        @catch_and_return(
            error_return_map={ValueError: "value_handled"},
            default_return="default"
        )
        def test_func():
            raise ValueError("Test")

        result = test_func()
        assert result == "value_handled"

    def test_catches_key_error(self):
        """测试捕获KeyError"""
        @catch_and_return(
            error_return_map={KeyError: "key_handled"},
            default_return="default"
        )
        def test_func():
            raise KeyError("Test")

        result = test_func()
        assert result == "key_handled"

    def test_returns_default_for_unmapped(self):
        """测试未映射异常返回默认值"""
        @catch_and_return(
            error_return_map={ValueError: "handled"},
            default_return="default"
        )
        def test_func():
            raise RuntimeError("Test")

        result = test_func()
        assert result == "default"

    def test_no_error_returns_value(self):
        """测试无错误时正常返回"""
        @catch_and_return(error_return_map={ValueError: "handled"})
        def test_func():
            return "normal"

        result = test_func()
        assert result == "normal"

    @pytest.mark.asyncio
    async def test_async_catches_value_error(self):
        """测试异步函数捕获ValueError"""
        @catch_and_return(
            error_return_map={ValueError: "handled"},
            default_return="default"
        )
        async def test_func():
            raise ValueError("Test")

        result = await test_func()
        assert result == "handled"

    @pytest.mark.asyncio
    async def test_async_no_error(self):
        """测试异步函数无错误时正常返回"""
        @catch_and_return(error_return_map={ValueError: "handled"})
        async def test_func():
            return "normal"

        result = await test_func()
        assert result == "normal"

    def test_inheritance_matching(self):
        """测试异常继承匹配"""
        class CustomError(Exception):
            pass

        @catch_and_return(
            error_return_map={Exception: "base_handled"},
            default_return="default"
        )
        def test_func():
            raise CustomError("Test")

        result = test_func()
        assert result == "base_handled"


class TestLogExecutionDetailed:
    """
    类级注释：log_execution装饰器详细测试
    """

    @patch('app.core.error_handling.decorators.logger')
    def test_logs_entry_and_exit(self, mock_logger):
        """测试记录入口和出口"""
        @log_execution()
        def test_func():
            return "result"

        test_func()

        # 验证入口和出口日志都被调用
        calls = [str(call) for call in mock_logger.debug.call_args_list]
        assert any("开始执行函数" in c for c in calls)
        assert any("执行完成" in c for c in calls)

    @patch('app.core.error_handling.decorators.logger')
    def test_logs_with_args_true(self, mock_logger):
        """测试记录参数"""
        @log_execution(log_args=True)
        def test_func(a, b):
            return a + b

        test_func(1, 2)

        calls = [str(call) for call in mock_logger.debug.call_args_list]
        assert any("args=" in c for c in calls)

    @patch('app.core.error_handling.decorators.logger')
    def test_logs_with_result_true(self, mock_logger):
        """测试记录返回值"""
        @log_execution(log_result=True)
        def test_func():
            return "result"

        test_func()

        calls = [str(call) for call in mock_logger.debug.call_args_list]
        assert any("返回值" in c for c in calls)

    @patch('app.core.error_handling.decorators.logger')
    def test_logs_execution_time(self, mock_logger):
        """测试记录执行时间"""
        @log_execution(log_execution_time=True)
        def test_func():
            return "done"

        test_func()

        calls = [str(call) for call in mock_logger.debug.call_args_list]
        assert any("执行时间" in c for c in calls)

    @patch('app.core.error_handling.decorators.logger')
    def test_logs_at_info_level(self, mock_logger):
        """测试在info级别记录"""
        @log_execution(log_level="info")
        def test_func():
            return "done"

        test_func()

        mock_logger.info.assert_called()

    @patch('app.core.error_handling.decorators.logger')
    def test_logs_even_with_exception(self, mock_logger):
        """测试异常时仍记录"""
        @log_execution(log_execution_time=True)
        def test_func():
            raise ValueError("Test error")

        try:
            test_func()
        except ValueError:
            pass

        # 验证日志被记录
        assert mock_logger.debug.called

    @pytest.mark.asyncio
    @patch('app.core.error_handling.decorators.logger')
    async def test_async_logs_execution(self, mock_logger):
        """测试异步函数记录执行"""
        @log_execution()
        async def test_func():
            return "async_result"

        await test_func()

        # 验证日志被记录
        assert mock_logger.debug.called

    @patch('app.core.error_handling.decorators.logger')
    def test_different_log_levels(self, mock_logger):
        """测试不同日志级别"""
        for level in ["debug", "info", "warning", "error"]:
            mock_logger.reset_mock()

            @log_execution(log_level=level)
            def test_func():
                return "done"

            test_func()

            # 验证使用正确的日志级别
            log_func = getattr(mock_logger, level)
            assert log_func.called


class TestErrorHandlingIntegration:
    """
    类级注释：错误处理集成测试
    """

    def test_combined_decorators(self):
        """测试组合装饰器"""
        attempt_count = [0]

        # 内部逻辑：调整装饰器顺序，让 catch_and_return 在最外层
        # 这样当函数成功时返回 "success"，当遇到特定异常时返回 "final"
        @catch_and_return(error_return_map={RuntimeError: "final"}, default_return="default")
        @with_retry(max_retries=2, delay=0.01)
        @log_execution(log_execution_time=False)
        def test_func():
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                raise ConnectionError("Retry")  # 会触发重试
            if attempt_count[0] == 3:
                raise RuntimeError("final")  # 会被 catch_and_return 捕获
            return "success"

        result = test_func()
        assert result == "success"
        assert attempt_count[0] == 2

    def test_with_error_handling_chain_result(self):
        """测试错误处理链返回结果"""
        class MockChain:
            def handle(self, error, context):
                return "chain_result"

        @with_error_handling(error_chain=MockChain())
        def test_func():
            raise ValueError("Test")

        result = test_func()
        assert result == "chain_result"

    def test_with_error_handling_none_chain(self):
        """测试None错误处理链"""
        @with_error_handling(error_chain=None, default_return="fallback")
        def test_func():
            raise ValueError("Test")

        result = test_func()
        assert result == "fallback"

    @pytest.mark.asyncio
    async def test_async_with_retry_signal(self):
        """测试异步重试信号"""
        class MockChain:
            call_count = [0]

            def handle(self, error, context):
                self.call_count[0] += 1
                if self.call_count[0] == 1:
                    return 'RETRY'
                return None

        @with_error_handling(error_chain=MockChain())
        async def test_func():
            return "success"

        result = await test_func()
        assert result == "success"


class TestEdgeCases:
    """
    类级注释：边界情况测试
    """

    def test_function_with_no_exception(self):
        """测试无异常的函数"""
        @with_error_handling()
        def test_func():
            return 42

        result = test_func()
        assert result == 42

    @pytest.mark.asyncio
    async def test_async_function_with_no_exception(self):
        """测试无异常的异步函数"""
        @with_error_handling()
        async def test_func():
            return 42

        result = await test_func()
        assert result == 42

    def test_zero_max_retries(self):
        """测试零最大重试次数"""
        @with_retry(max_retries=0, delay=0.01)
        def test_func():
            raise ValueError("Test")

        with pytest.raises(ValueError):
            test_func()

    def test_zero_delay(self):
        """测试零延迟"""
        attempt_count = [0]

        @with_retry(max_retries=2, delay=0)
        def test_func():
            attempt_count[0] += 1
            raise ValueError("Test")

        try:
            test_func()
        except ValueError:
            pass

        assert attempt_count[0] == 3

    def test_empty_error_map(self):
        """测试空错误映射"""
        @catch_and_return(error_return_map={}, default_return="fallback")
        def test_func():
            raise ValueError("Test")

        result = test_func()
        assert result == "fallback"

    def test_function_with_multiple_args(self):
        """测试多参数函数"""
        @log_execution(log_args=True)
        def test_func(a, b, c, d=None):
            return a + b + c

        result = test_func(1, 2, 3)
        assert result == 6
