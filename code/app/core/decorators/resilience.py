# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：弹性装饰器模块
内部逻辑：实现重试、限流、断路器等弹性模式
设计模式：装饰器模式（Decorator Pattern）
设计原则：开闭原则、单一职责原则

@package app.core.decorators.resilience
"""

from functools import wraps
from typing import Any, Callable, Optional, Type, Tuple, Union
from loguru import logger
import time
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


# ==================== 重试装饰器 ====================

class RetryStrategy(Enum):
    """
    类级注释：重试策略枚举
    内部逻辑：定义不同的重试策略
    """
    # 固定延迟
    FIXED = "fixed"
    # 线性退避
    LINEAR = "linear"
    # 指数退避
    EXPONENTIAL = "exponential"
    # 抖动指数退避
    EXPONENTIAL_WITH_JITTER = "exponential_with_jitter"


@dataclass
class RetryConfig:
    """
    类级注释：重试配置数据类
    内部逻辑：封装重试相关的配置
    """
    # 属性：最大重试次数
    max_attempts: int = 3
    # 属性：重试策略
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    # 属性：基础延迟（秒）
    base_delay: float = 1.0
    # 属性：最大延迟（秒）
    max_delay: float = 60.0
    # 属性：需要重试的异常类型
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
    # 属性：重试条件函数
    retry_condition: Optional[Callable[[Exception], bool]] = None
    # 属性：重试之间的回调
    on_retry: Optional[Callable[[int, Exception], Any]] = None


def retry(
    max_attempts: int = 3,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    retry_condition: Optional[Callable[[Exception], bool]] = None,
    on_retry: Optional[Callable[[int, Exception], Any]] = None
):
    """
    函数级注释：重试装饰器
    内部逻辑：执行失败时按策略重试
    设计模式：装饰器模式
    参数：
        max_attempts - 最大尝试次数
        strategy - 重试策略
        base_delay - 基础延迟
        max_delay - 最大延迟
        exceptions - 需要重试的异常类型
        retry_condition - 自定义重试条件
        on_retry - 重试回调
    返回值：装饰器函数

    @example
    ```python
    @retry(max_attempts=3, strategy=RetryStrategy.EXPONENTIAL)
    async def fetch_data():
        return await api_call()
    ```
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        strategy=strategy,
        base_delay=base_delay,
        max_delay=max_delay,
        exceptions=exceptions,
        retry_condition=retry_condition,
        on_retry=on_retry
    )

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    # 内部逻辑：检查是否应该重试
                    if config.retry_condition and not config.retry_condition(e):
                        raise

                    # 内部逻辑：最后一次尝试失败，不再重试
                    if attempt == config.max_attempts - 1:
                        break

                    # 内部逻辑：计算延迟
                    delay = _calculate_delay(attempt, config)

                    logger.warning(
                        f"[Retry] {func.__name__} 失败 (尝试 {attempt + 1}/{config.max_attempts}), "
                        f"{delay:.2f}s 后重试: {str(e)}"
                    )

                    # 内部逻辑：执行回调
                    if config.on_retry:
                        await _execute_callback(config.on_retry, attempt + 1, e)

                    await asyncio.sleep(delay)

            # 内部逻辑：所有重试失败
            raise last_exception

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if config.retry_condition and not config.retry_condition(e):
                        raise

                    if attempt == config.max_attempts - 1:
                        break

                    delay = _calculate_delay(attempt, config)

                    logger.warning(
                        f"[Retry] {func.__name__} 失败 (尝试 {attempt + 1}/{config.max_attempts}), "
                        f"{delay:.2f}s 后重试: {str(e)}"
                    )

                    if config.on_retry:
                        _execute_callback(config.on_retry, attempt + 1, e)

                    time.sleep(delay)

            raise last_exception

        # 内部逻辑：根据函数类型返回对应包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def _calculate_delay(attempt: int, config: RetryConfig) -> float:
    """
    函数级注释：计算重试延迟
    参数：
        attempt - 当前尝试次数（从0开始）
        config - 重试配置
    返回值：延迟时间（秒）
    """
    if config.strategy == RetryStrategy.FIXED:
        delay = config.base_delay
    elif config.strategy == RetryStrategy.LINEAR:
        delay = config.base_delay * (attempt + 1)
    elif config.strategy == RetryStrategy.EXPONENTIAL:
        delay = config.base_delay * (2 ** attempt)
    elif config.strategy == RetryStrategy.EXPONENTIAL_WITH_JITTER:
        base = config.base_delay * (2 ** attempt)
        # 内部逻辑：添加随机抖动（±25%）
        import random
        jitter = base * 0.25 * (random.random() * 2 - 1)
        delay = base + jitter
    else:
        delay = config.base_delay

    return min(delay, config.max_delay)


async def _execute_callback(callback: Callable, *args):
    """执行回调函数（支持异步）"""
    result = callback(*args)
    if asyncio.iscoroutine(result):
        await result


# ==================== 限流装饰器 ====================

class RateLimitError(Exception):
    """限流异常"""
    pass


@dataclass
class RateLimitConfig:
    """
    类级注释：限流配置数据类
    内部逻辑：封装限流相关的配置
    """
    # 属性：调用次数限制
    calls: int = 10
    # 属性：时间窗口（秒）
    period: float = 60.0
    # 属性：限制策略（sliding 或 fixed）
    strategy: str = "sliding"


class RateLimiter:
    """
    类级注释：限流器
    内部逻辑：实现滑动窗口和固定窗口限流
    设计模式：策略模式
    """

    def __init__(self, config: RateLimitConfig):
        self._config = config
        self._requests: list = []  # [(timestamp, )]

    def _clean_old_requests(self, now: float) -> None:
        """清理过期请求记录"""
        cutoff = now - self._config.period
        self._requests = [t for t in self._requests if t > cutoff]

    def is_allowed(self) -> bool:
        """检查是否允许请求"""
        now = time.time()

        if self._config.strategy == "fixed":
            # 内部逻辑：固定窗口策略
            self._clean_old_requests(now)
            return len(self._requests) < self._config.calls
        else:
            # 内部逻辑：滑动窗口策略
            cutoff = now - self._config.period
            recent_count = sum(1 for t in self._requests if t > cutoff)
            return recent_count < self._config.calls

    def record_request(self) -> None:
        """记录请求"""
        self._requests.append(time.time())

    def get_reset_time(self) -> float:
        """获取限流重置时间"""
        if not self._requests:
            return 0

        if self._config.strategy == "fixed":
            # 内部逻辑：固定窗口返回最早的过期时间
            return self._requests[0] + self._config.period
        else:
            # 内部逻辑：滑动窗口返回当前窗口结束时间
            return self._requests[-1] + self._config.period


# 内部变量：全局限流器实例
_limiters: dict = {}


def get_limiter(key: str, config: RateLimitConfig) -> RateLimiter:
    """获取或创建限流器"""
    if key not in _limiters:
        _limiters[key] = RateLimiter(config)
    return _limiters[key]


def rate_limit(
    calls: int = 10,
    period: float = 60.0,
    strategy: str = "sliding",
    key_func: Optional[Callable] = None
):
    """
    函数级注释：限流装饰器
    内部逻辑：限制函数调用频率
    设计模式：装饰器模式
    参数：
        calls - 调用次数限制
        period - 时间窗口（秒）
        strategy - 限流策略（sliding 或 fixed）
        key_func - 自定义键生成函数
    返回值：装饰器函数

    @example
    ```python
    @rate_limit(calls=100, period=60)  # 每分钟最多100次
    async def api_handler():
        return await process_request()
    ```
    """
    config = RateLimitConfig(calls=calls, period=period, strategy=strategy)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 内部逻辑：生成限流键
            if key_func:
                key = key_func(func, args, kwargs)
            else:
                key = func.__name__

            limiter = get_limiter(key, config)

            # 内部逻辑：检查是否允许请求
            if not limiter.is_allowed():
                reset_time = limiter.get_reset_time()
                raise RateLimitError(
                    f"调用频率超限，请在 {reset_time - time.time():.1f} 秒后重试"
                )

            # 内部逻辑：记录请求
            limiter.record_request()

            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if key_func:
                key = key_func(func, args, kwargs)
            else:
                key = func.__name__

            limiter = get_limiter(key, config)

            if not limiter.is_allowed():
                reset_time = limiter.get_reset_time()
                raise RateLimitError(
                    f"调用频率超限，请在 {reset_time - time.time():.1f} 秒后重试"
                )

            limiter.record_request()

            return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# ==================== 断路器装饰器 ====================

class CircuitBreakerState(Enum):
    """断路器状态枚举"""
    # 关闭状态（正常）
    CLOSED = "closed"
    # 开启状态（熔断）
    OPEN = "open"
    # 半开状态（试探）
    HALF_OPEN = "half_open"


class CircuitBreakerOpenError(Exception):
    """断路器开启异常"""
    def __init__(self, reset_time: float):
        self.reset_time = reset_time
        super().__init__(f"断路器已开启，请在 {reset_time:.1f} 秒后重试")


@dataclass
class CircuitBreakerConfig:
    """
    类级注释：断路器配置数据类
    内部逻辑：封装断路器相关的配置
    """
    # 属性：失败阈值
    failure_threshold: int = 5
    # 属性：超时时间（秒）
    timeout: float = 60.0
    # 属性：成功恢复阈值
    success_threshold: int = 2
    # 属性：需要捕获的异常类型
    exceptions: Tuple[Type[Exception], ...] = (Exception,)


class CircuitBreaker:
    """
    类级注释：断路器
    内部逻辑：实现断路器模式
    设计模式：状态模式
    职责：
        1. 监控失败率
        2. 在达到阈值时开启
        3. 超时后进入半开状态
        4. 成功后恢复关闭状态
    """

    def __init__(self, config: CircuitBreakerConfig):
        self._config = config
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._opened_at: Optional[float] = None

    @property
    def state(self) -> CircuitBreakerState:
        """获取当前状态"""
        return self._state

    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试重置"""
        if self._state != CircuitBreakerState.OPEN:
            return False

        if self._opened_at is None:
            return True

        return time.time() - self._opened_at >= self._config.timeout

    def record_success(self) -> None:
        """记录成功"""
        if self._state == CircuitBreakerState.HALF_OPEN:
            self._success_count += 1

            # 内部逻辑：半开状态下达到成功阈值，恢复关闭状态
            if self._success_count >= self._config.success_threshold:
                self._state = CircuitBreakerState.CLOSED
                self._failure_count = 0
                self._success_count = 0
                logger.info("[CircuitBreaker] 断路器恢复到关闭状态")
        else:
            # 内部逻辑：关闭状态下，失败计数归零
            self._failure_count = 0

    def record_failure(self) -> None:
        """记录失败"""
        self._failure_count += 1
        self._last_failure_time = time.time()

        # 内部逻辑：达到失败阈值，开启断路器
        if self._state == CircuitBreakerState.CLOSED and \
           self._failure_count >= self._config.failure_threshold:
            self._state = CircuitBreakerState.OPEN
            self._opened_at = time.time()
            logger.warning(
                f"[CircuitBreaker] 断路器开启，失败次数: {self._failure_count}"
            )
        elif self._state == CircuitBreakerState.HALF_OPEN:
            # 内部逻辑：半开状态下失败，重新开启
            self._state = CircuitBreakerState.OPEN
            self._opened_at = time.time()
            logger.warning("[CircuitBreaker] 半开状态失败，断路器重新开启")

    def can_execute(self) -> bool:
        """检查是否可以执行"""
        if self._state == CircuitBreakerState.CLOSED:
            return True

        if self._state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self._state = CircuitBreakerState.HALF_OPEN
                self._success_count = 0
                logger.info("[CircuitBreaker] 断路器进入半开状态")
                return True
            return False

        return True  # HALF_OPEN

    def get_reset_time(self) -> Optional[float]:
        """获取重置时间"""
        if self._state != CircuitBreakerState.OPEN or self._opened_at is None:
            return None
        return self._opened_at + self._config.timeout


# 内部变量：全局断路器实例
_breakers: dict = {}


def get_breaker(key: str, config: CircuitBreakerConfig) -> CircuitBreaker:
    """获取或创建断路器"""
    if key not in _breakers:
        _breakers[key] = CircuitBreaker(config)
    return _breakers[key]


def circuit_breaker(
    failure_threshold: int = 5,
    timeout: float = 60.0,
    success_threshold: int = 2,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    key_func: Optional[Callable] = None
):
    """
    函数级注释：断路器装饰器
    内部逻辑：在失败率过高时熔断，防止雪崩
    设计模式：装饰器模式
    参数：
        failure_threshold - 失败阈值
        timeout - 超时时间（秒）
        success_threshold - 成功恢复阈值
        exceptions - 需要捕获的异常类型
        key_func - 自定义键生成函数
    返回值：装饰器函数

    @example
    ```python
    @circuit_breaker(failure_threshold=5, timeout=60)
    async def external_api_call():
        return await api.call()
    ```
    """
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        timeout=timeout,
        success_threshold=success_threshold,
        exceptions=exceptions
    )

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 内部逻辑：生成断路器键
            if key_func:
                key = key_func(func, args, kwargs)
            else:
                key = func.__name__

            breaker = get_breaker(key, config)

            # 内部逻辑：检查是否可以执行
            if not breaker.can_execute():
                reset_time = breaker.get_reset_time()
                raise CircuitBreakerOpenError(
                    reset_time or 0
                )

            try:
                result = await func(*args, **kwargs)
                breaker.record_success()
                return result
            except exceptions as e:
                breaker.record_failure()
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if key_func:
                key = key_func(func, args, kwargs)
            else:
                key = func.__name__

            breaker = get_breaker(key, config)

            if not breaker.can_execute():
                reset_time = breaker.get_reset_time()
                raise CircuitBreakerOpenError(
                    reset_time or 0
                )

            try:
                result = func(*args, **kwargs)
                breaker.record_success()
                return result
            except exceptions as e:
                breaker.record_failure()
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# ==================== 超时装饰器 ====================

class TimeoutError(Exception):
    """超时异常"""
    pass


def timeout(seconds: float, exception_class: Type[Exception] = TimeoutError):
    """
    函数级注释：超时装饰器
    内部逻辑：为函数添加超时控制
    设计模式：装饰器模式
    参数：
        seconds - 超时时间（秒）
        exception_class - 超时时抛出的异常类型
    返回值：装饰器函数

    @example
    ```python
    @timeout(seconds=5.0)
    async def slow_operation():
        return await long_running_task()
    ```
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                logger.warning(f"[Timeout] {func.__name__} 超时 ({seconds}s)")
                raise exception_class(f"操作超时: {func.__name__}")

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            import signal

            def handler(signum, frame):
                raise exception_class(f"操作超时: {func.__name__}")

            # 内部逻辑：设置信号处理器
            old_handler = signal.signal(signal.SIGALRM, handler)
            signal.alarm(int(seconds))

            try:
                result = func(*args, **kwargs)
            finally:
                # 内部逻辑：恢复旧处理器
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)

            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# ==================== 弹性组合装饰器 ====================

def resilient(
    enable_retry: bool = True,
    enable_circuit_breaker: bool = True,
    enable_timeout: bool = True,
    enable_rate_limit: bool = False,
    retry_config: Optional[dict] = None,
    circuit_breaker_config: Optional[dict] = None,
    timeout_seconds: Optional[float] = None,
    rate_limit_config: Optional[dict] = None
):
    """
    函数级注释：弹性组合装饰器
    内部逻辑：组合多个弹性模式
    设计模式：装饰器模式 + 责任链模式
    参数：
        enable_retry - 是否启用重试
        enable_circuit_breaker - 是否启用断路器
        enable_timeout - 是否启用超时
        enable_rate_limit - 是否启用限流
        retry_config - 重试配置
        circuit_breaker_config - 断路器配置
        timeout_seconds - 超时时间
        rate_limit_config - 限流配置
    返回值：装饰器函数

    @example
    ```python
    @resilient(
        enable_retry=True,
        enable_circuit_breaker=True,
        enable_timeout=True,
        timeout_seconds=10.0
    )
    async def external_api_call():
        return await api.call()
    ```
    """
    def decorator(func: Callable) -> Callable:
        # 内部逻辑：按顺序应用装饰器
        # 注意：装饰器的应用顺序很重要

        decorated = func

        if enable_timeout and timeout_seconds is not None:
            decorated = timeout(timeout_seconds)(decorated)

        if enable_circuit_breaker and circuit_breaker_config:
            decorated = circuit_breaker(**circuit_breaker_config)(decorated)

        if enable_retry and retry_config:
            decorated = retry(**retry_config)(decorated)

        if enable_rate_limit and rate_limit_config:
            decorated = rate_limit(**rate_limit_config)(decorated)

        return decorated

    return decorator


# 内部变量：导出所有公共接口
__all__ = [
    # 重试
    'RetryConfig',
    'RetryStrategy',
    'retry',
    # 限流
    'RateLimitConfig',
    'RateLimiter',
    'RateLimitError',
    'rate_limit',
    # 断路器
    'CircuitBreakerConfig',
    'CircuitBreakerState',
    'CircuitBreaker',
    'CircuitBreakerOpenError',
    'circuit_breaker',
    # 超时
    'TimeoutError',
    'timeout',
    # 组合
    'resilient',
]
