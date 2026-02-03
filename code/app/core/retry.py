# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：统一错误处理和重试机制模块
内部逻辑：提供装饰器实现统一的错误处理和重试
设计模式：装饰器模式、策略模式
设计原则：DRY（不重复）、开闭原则（对扩展开放）
"""

import functools
import asyncio
from typing import Callable, TypeVar, Optional, Dict, Any, Type, Tuple
from enum import Enum
from loguru import logger

T = TypeVar('T')


class RetryStrategy(str, Enum):
    """
    类级注释：重试策略枚举
    属性：
        EXPONENTIAL_BACKOFF: 指数退避（每次重试延迟时间翻倍）
        LINEAR_BACKOFF: 线性退避（每次重试延迟时间线性增加）
        FIXED_DELAY: 固定延迟（每次重试延迟时间固定）
        IMMEDIATE: 立即重试（不延迟）
    """
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    IMMEDIATE = "immediate"


class ErrorCodeCategory(str, Enum):
    """
    类级注释：错误代码分类枚举
    属性：
        NETWORK_ERROR: 网络错误，可重试
        API_ERROR: API错误，可重试
        RATE_LIMIT_ERROR: 限流错误，需要延迟重试
        VALIDATION_ERROR: 验证错误，不可重试
        NOT_FOUND_ERROR: 资源不存在，不可重试
        UNKNOWN_ERROR: 未知错误
    """
    NETWORK_ERROR = "network_error"
    API_ERROR = "api_error"
    RATE_LIMIT_ERROR = "rate_limit"
    VALIDATION_ERROR = "validation"
    NOT_FOUND_ERROR = "not_found"
    UNKNOWN_ERROR = "unknown"


# 错误代码分类映射（内部变量）
_ERROR_CODE_CATEGORIES: Dict[str, ErrorCodeCategory] = {
    # 网络错误
    "ECONNREFUSED": ErrorCodeCategory.NETWORK_ERROR,
    "ETIMEDOUT": ErrorCodeCategory.NETWORK_ERROR,
    "ConnectionError": ErrorCodeCategory.NETWORK_ERROR,
    "TimeoutError": ErrorCodeCategory.NETWORK_ERROR,

    # API错误
    "500": ErrorCodeCategory.API_ERROR,
    "502": ErrorCodeCategory.API_ERROR,
    "503": ErrorCodeCategory.API_ERROR,
    "504": ErrorCodeCategory.API_ERROR,

    # 限流错误
    "429": ErrorCodeCategory.RATE_LIMIT_ERROR,
    "rate_limit_exceeded": ErrorCodeCategory.RATE_LIMIT_ERROR,

    # 验证错误
    "400": ErrorCodeCategory.VALIDATION_ERROR,
    "422": ErrorCodeCategory.VALIDATION_ERROR,
    "ValidationError": ErrorCodeCategory.VALIDATION_ERROR,

    # 资源不存在
    "404": ErrorCodeCategory.NOT_FOUND_ERROR,
    "NotFoundError": ErrorCodeCategory.NOT_FOUND_ERROR,
}


def categorize_error(error: Exception) -> ErrorCodeCategory:
    """
    函数级注释：对错误进行分类
    内部逻辑：根据错误类型和消息判断错误类别
    参数：
        error: 异常对象
    返回值：错误分类
    """
    error_message = str(error)
    error_type = type(error).__name__

    # 内部逻辑：检查是否在错误代码映射中
    for code, category in _ERROR_CODE_CATEGORIES.items():
        if code in error_message or code == error_type:
            return category

    # 内部逻辑：检查特定错误类型
    if isinstance(error, (ConnectionError, TimeoutError)):
        return ErrorCodeCategory.NETWORK_ERROR

    if isinstance(error, ValueError):
        return ErrorCodeCategory.VALIDATION_ERROR

    if isinstance(error, KeyError):
        return ErrorCodeCategory.NOT_FOUND_ERROR

    return ErrorCodeCategory.UNKNOWN_ERROR


def should_retry(category: ErrorCodeCategory) -> bool:
    """
    函数级注释：判断错误是否应该重试
    内部逻辑：只有网络错误、API错误、限流错误才重试
    参数：
        category: 错误分类
    返回值：是否可重试
    """
    return category in {
        ErrorCodeCategory.NETWORK_ERROR,
        ErrorCodeCategory.API_ERROR,
        ErrorCodeCategory.RATE_LIMIT_ERROR,
    }


def retry_on_failure(
    max_attempts: int = 3,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_multiplier: float = 2.0,
    retry_on: Optional[Tuple[Type[Exception], ...]] = None,
    give_up_on: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
):
    """
    函数级注释：失败重试装饰器
    设计模式：装饰器模式
    内部逻辑：捕获异常 -> 判断是否重试 -> 计算延迟 -> 重试或抛出异常

    参数：
        max_attempts: 最大尝试次数（默认3次）
        strategy: 重试策略（默认指数退避）
        base_delay: 基础延迟时间（秒，默认1秒）
        max_delay: 最大延迟时间（秒，默认60秒）
        backoff_multiplier: 退避乘数（默认2）
        retry_on: 指定需要重试的异常类型（为空则自动判断）
        give_up_on: 指定不重试的异常类型
        on_retry: 重试回调函数 (attempt, error) -> None

    返回值：装饰器函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            return _retry_sync(
                func, max_attempts, strategy, base_delay,
                max_delay, backoff_multiplier, retry_on, give_up_on,
                on_retry, *args, **kwargs
            )

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            return await _retry_async(
                func, max_attempts, strategy, base_delay,
                max_delay, backoff_multiplier, retry_on, give_up_on,
                on_retry, *args, **kwargs
            )

        # 内部逻辑：根据函数是否为协程函数返回对应的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def _retry_sync(
    func: Callable,
    max_attempts: int,
    strategy: RetryStrategy,
    base_delay: float,
    max_delay: float,
    backoff_multiplier: float,
    retry_on: Optional[Tuple[Type[Exception], ...]],
    give_up_on: Optional[Tuple[Type[Exception], ...]],
    on_retry: Optional[Callable[[int, Exception], None]],
    *args,
    **kwargs
):
    """
    函数级注释：同步重试逻辑（内部方法）
    内部逻辑：循环尝试执行函数，失败时根据策略延迟后重试

    参数：
        func: 要执行的函数
        max_attempts: 最大尝试次数
        strategy: 重试策略
        base_delay: 基础延迟
        max_delay: 最大延迟
        backoff_multiplier: 退避乘数
        retry_on: 指定重试的异常类型
        give_up_on: 指定不重试的异常类型
        on_retry: 重试回调函数
        *args, **kwargs: 函数参数

    返回值：函数执行结果
    """
    import time

    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e

            # 内部逻辑：检查是否为放弃重试的错误类型
            if give_up_on and isinstance(e, give_up_on):
                raise

            # 内部逻辑：检查是否为指定重试的错误类型
            if retry_on and not isinstance(e, retry_on):
                raise

            # 内部逻辑：对错误进行分类，判断是否可重试
            category = categorize_error(e)
            if not should_retry(category):
                raise

            # 内部逻辑：最后一次尝试不再等待
            if attempt >= max_attempts:
                break

            # 内部逻辑：调用重试回调
            if on_retry:
                on_retry(attempt, e)

            # 内部逻辑：计算延迟时间
            delay = _calculate_delay(
                attempt, strategy, base_delay,
                max_delay, backoff_multiplier, category
            )

            logger.warning(
                f"调用 {func.__name__} 失败 (尝试 {attempt}/{max_attempts}): "
                f"{str(e)}, {delay:.2f}秒后重试..."
            )
            time.sleep(delay)

    # 内部逻辑：所有重试都失败，抛出最后一次错误
    logger.error(f"调用 {func.__name__} 在 {max_attempts} 次尝试后仍然失败")
    raise last_error


async def _retry_async(
    func: Callable,
    max_attempts: int,
    strategy: RetryStrategy,
    base_delay: float,
    max_delay: float,
    backoff_multiplier: float,
    retry_on: Optional[Tuple[Type[Exception], ...]],
    give_up_on: Optional[Tuple[Type[Exception], ...]],
    on_retry: Optional[Callable[[int, Exception], None]],
    *args,
    **kwargs
):
    """
    函数级注释：异步重试逻辑（内部方法）
    内部逻辑：循环尝试执行异步函数，失败时根据策略延迟后重试

    参数：
        func: 要执行的异步函数
        max_attempts: 最大尝试次数
        strategy: 重试策略
        base_delay: 基础延迟
        max_delay: 最大延迟
        backoff_multiplier: 退避乘数
        retry_on: 指定重试的异常类型
        give_up_on: 指定不重试的异常类型
        on_retry: 重试回调函数
        *args, **kwargs: 函数参数

    返回值：函数执行结果
    """
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_error = e

            if give_up_on and isinstance(e, give_up_on):
                raise

            if retry_on and not isinstance(e, retry_on):
                raise

            category = categorize_error(e)
            if not should_retry(category):
                raise

            if attempt >= max_attempts:
                break

            # 内部逻辑：调用重试回调
            if on_retry:
                on_retry(attempt, e)

            delay = _calculate_delay(
                attempt, strategy, base_delay,
                max_delay, backoff_multiplier, category
            )

            logger.warning(
                f"调用 {func.__name__} 失败 (尝试 {attempt}/{max_attempts}): "
                f"{str(e)}, {delay:.2f}秒后重试..."
            )
            await asyncio.sleep(delay)

    logger.error(f"调用 {func.__name__} 在 {max_attempts} 次尝试后仍然失败")
    raise last_error


def _calculate_delay(
    attempt: int,
    strategy: RetryStrategy,
    base_delay: float,
    max_delay: float,
    backoff_multiplier: float,
    category: ErrorCodeCategory
) -> float:
    """
    函数级注释：计算重试延迟时间（内部方法）
    内部逻辑：根据策略和错误类别计算延迟时间

    参数：
        attempt: 当前尝试次数
        strategy: 重试策略
        base_delay: 基础延迟
        max_delay: 最大延迟
        backoff_multiplier: 退避乘数
        category: 错误分类

    返回值：延迟时间（秒）
    """
    # 内部逻辑：限流错误需要更长的延迟
    if category == ErrorCodeCategory.RATE_LIMIT_ERROR:
        base_delay = min(base_delay * 2, max_delay)

    if strategy == RetryStrategy.IMMEDIATE:
        return 0
    elif strategy == RetryStrategy.FIXED_DELAY:
        return min(base_delay, max_delay)
    elif strategy == RetryStrategy.LINEAR_BACKOFF:
        return min(base_delay * attempt, max_delay)
    elif strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
        return min(base_delay * (backoff_multiplier ** (attempt - 1)), max_delay)

    return base_delay


def handle_errors(
    default_return: Any = None,
    raise_on: Optional[Tuple[Type[Exception], ...]] = None,
    log_errors: bool = True,
    error_message: Optional[str] = None,
):
    """
    函数级注释：统一错误处理装饰器
    设计模式：装饰器模式
    内部逻辑：捕获异常 -> 记录日志 -> 返回默认值或重新抛出

    参数：
        default_return: 发生异常时的默认返回值
        raise_on: 指定需要重新抛出的异常类型
        log_errors: 是否记录错误日志
        error_message: 自定义错误消息

    返回值：装饰器函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 内部逻辑：检查是否需要重新抛出
                if raise_on and isinstance(e, raise_on):
                    raise

                # 内部逻辑：记录错误日志
                if log_errors:
                    logger.error(
                        f"调用 {func.__name__} 失败: {str(e)}",
                        exc_info=True
                    )

                # 内部逻辑：如果有自定义错误消息，记录
                if error_message:
                    logger.error(error_message)

                # 内部逻辑：返回默认值
                if default_return is not None:
                    return default_return

                # 内部逻辑：否则重新抛出异常
                raise

        return wrapper

    return decorator
