# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：错误处理装饰器模块
内部逻辑：提供统一的错误处理装饰器，简化异常处理代码
设计模式：装饰器模式 + 模板方法模式
设计原则：DRY原则、开闭原则（OCP）
职责：消除重复的try-except代码，提供声明式错误处理
"""

from functools import wraps
from typing import Optional, Callable, Any, Type, Tuple, Union
from loguru import logger
import asyncio

from .error_chain import ErrorHandler, get_default_chain


# 内部变量：装饰器配置类型
DecoratorConfig = dict


def with_error_handling(
    error_chain: Optional[ErrorHandler] = None,
    default_return: Any = None,
    reraise: bool = False,
    log_level: str = "error",
    context_builder: Optional[Callable[[], dict]] = None
):
    """
    函数级注释：错误处理装饰器工厂
    内部逻辑：返回一个装饰器，为函数添加统一的错误处理能力
    设计模式：装饰器模式 + 工厂方法模式
    参数：
        error_chain - 错误处理责任链（默认使用全局链）
        default_return - 发生错误时的默认返回值
        reraise - 是否在处理后重新抛出异常
        log_level - 日志级别（debug/info/warning/error）
        context_builder - 上下文构建函数，返回额外上下文信息
    返回值：装饰器函数

    使用示例：
        # 基本用法
        @with_error_handling()
        async def my_function():
            ...

        # 自定义默认返回值
        @with_error_handling(default_return={"success": False})
        async def my_function():
            ...

        # 不重新抛出异常，使用自定义错误链
        @with_error_handling(reraise=False, error_chain=my_chain)
        async def my_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        """
        内部函数：实际的装饰器
        参数：
            func - 被装饰的函数
        返回值：包装后的函数
        """
        # 内部逻辑：获取配置的错误处理链
        chain = error_chain if error_chain is not None else get_default_chain()

        # 内部逻辑：获取函数名称，用于日志
        func_name = func.__name__
        module_name = func.__module__

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            """
            内部函数：异步函数的包装器
            内部逻辑：捕获异常 -> 通过责任链处理 -> 返回结果或默认值
            """
            try:
                # 内部逻辑：调用原始函数
                return await func(*args, **kwargs)

            except Exception as e:
                # 内部逻辑：构建上下文信息
                context = {
                    'function': func_name,
                    'module': module_name,
                    'args_type': [type(arg).__name__ for arg in args],
                    'kwargs_keys': list(kwargs.keys()),
                    'default_return': default_return,
                    'retry_count': 0
                }

                # 内部逻辑：添加自定义上下文
                if context_builder:
                    custom_context = context_builder()
                    if isinstance(custom_context, dict):
                        context.update(custom_context)

                # 内部逻辑：通过责任链处理错误
                if chain:
                    result = chain.handle(e, context)
                    # 内部逻辑：检查是否需要重试
                    if result == 'RETRY':
                        logger.info(f"重试函数: {func_name}")
                        return await async_wrapper(*args, **kwargs)
                    # 内部逻辑：如果处理器返回了结果，使用该结果
                    if result is not None and result != 'RETRY':
                        return result

                # 内部逻辑：记录日志
                log_func = getattr(logger, log_level.lower(), logger.error)
                log_func(f"函数 {func_name} 执行失败: {str(e)}", exc_info=True)

                # 内部逻辑：根据配置决定是否重新抛出
                if reraise:
                    raise

                # 内部逻辑：返回默认值
                return default_return

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            """
            内部函数：同步函数的包装器
            内部逻辑：捕获异常 -> 通过责任链处理 -> 返回结果或默认值
            """
            try:
                # 内部逻辑：调用原始函数
                return func(*args, **kwargs)

            except Exception as e:
                # 内部逻辑：构建上下文信息
                context = {
                    'function': func_name,
                    'module': module_name,
                    'args_type': [type(arg).__name__ for arg in args],
                    'kwargs_keys': list(kwargs.keys()),
                    'default_return': default_return,
                    'retry_count': 0
                }

                # 内部逻辑：添加自定义上下文
                if context_builder:
                    custom_context = context_builder()
                    if isinstance(custom_context, dict):
                        context.update(custom_context)

                # 内部逻辑：通过责任链处理错误
                if chain:
                    result = chain.handle(e, context)
                    # 内部逻辑：检查是否需要重试（仅异步支持重试）
                    if result == 'RETRY':
                        logger.warning(f"同步函数 {func_name} 不支持重试")
                    # 内部逻辑：如果处理器返回了结果，使用该结果
                    if result is not None and result != 'RETRY':
                        return result

                # 内部逻辑：记录日志
                log_func = getattr(logger, log_level.lower(), logger.error)
                log_func(f"函数 {func_name} 执行失败: {str(e)}", exc_info=True)

                # 内部逻辑：根据配置决定是否重新抛出
                if reraise:
                    raise

                # 内部逻辑：返回默认值
                return default_return

        # 内部逻辑：返回适当的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def with_retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    函数级注释：重试装饰器
    内部逻辑：捕获指定异常后按指数退避策略重试
    设计模式：装饰器模式
    参数：
        max_retries - 最大重试次数
        delay - 初始延迟时间（秒）
        backoff_factor - 退避因子，每次重试延迟时间乘以该因子
        exceptions - 需要重试的异常类型
    返回值：装饰器函数

    使用示例：
        @with_retry(max_retries=3, delay=1.0)
        async def fetch_data():
            ...
    """
    def decorator(func: Callable) -> Callable:
        """内部函数：实际的装饰器"""
        func_name = func.__name__

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            """异步函数包装器"""
            current_delay = delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.info(
                            f"函数 {func_name} 第 {attempt + 1} 次尝试失败，"
                            f"{current_delay:.1f}秒后重试: {str(e)}"
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(
                            f"函数 {func_name} 达到最大重试次数 {max_retries}"
                        )

            raise last_exception

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            """同步函数包装器"""
            import time
            current_delay = delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.info(
                            f"函数 {func_name} 第 {attempt + 1} 次尝试失败，"
                            f"{current_delay:.1f}秒后重试: {str(e)}"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(
                            f"函数 {func_name} 达到最大重试次数 {max_retries}"
                        )

            raise last_exception

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def catch_and_return(
    error_return_map: Optional[dict] = None,
    default_return: Any = None
):
    """
    函数级注释：捕获异常并返回指定值的装饰器
    内部逻辑：捕获异常后根据异常类型返回对应值
    设计模式：装饰器模式
    参数：
        error_return_map - 异常类型到返回值的映射
        default_return - 默认返回值
    返回值：装饰器函数

    使用示例：
        @catch_and_return(
            error_return_map={
                ValueError: "无效输入",
                KeyError: "缺少必需参数"
            },
            default_return="未知错误"
        )
        def process_data(data):
            ...
    """
    def decorator(func: Callable) -> Callable:
        """内部函数：实际的装饰器"""
        func_name = func.__name__
        error_map = error_return_map or {}

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            """异步函数包装器"""
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # 内部逻辑：查找匹配的异常类型
                for error_type, return_value in error_map.items():
                    if isinstance(e, error_type):
                        # 内部变量：获取异常类型名称，支持元组类型
                        if isinstance(error_type, tuple):
                            type_names = ", ".join(t.__name__ for t in error_type)
                        else:
                            type_names = error_type.__name__
                        logger.debug(f"函数 {func_name} 捕获 {type_names}: {str(e)}")
                        return return_value
                logger.warning(f"函数 {func_name} 捕获未处理异常: {str(e)}")
                return default_return

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            """同步函数包装器"""
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 内部逻辑：查找匹配的异常类型
                for error_type, return_value in error_map.items():
                    if isinstance(e, error_type):
                        # 内部变量：获取异常类型名称，支持元组类型
                        if isinstance(error_type, tuple):
                            type_names = ", ".join(t.__name__ for t in error_type)
                        else:
                            type_names = error_type.__name__
                        logger.debug(f"函数 {func_name} 捕获 {type_names}: {str(e)}")
                        return return_value
                logger.warning(f"函数 {func_name} 捕获未处理异常: {str(e)}")
                return default_return

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def log_execution(
    log_level: str = "debug",
    log_args: bool = False,
    log_result: bool = False,
    log_execution_time: bool = True
):
    """
    函数级注释：记录函数执行日志的装饰器
    内部逻辑：在函数执行前后记录日志
    设计模式：装饰器模式
    参数：
        log_level - 日志级别
        log_args - 是否记录参数
        log_result - 是否记录返回值
        log_execution_time - 是否记录执行时间
    返回值：装饰器函数

    使用示例：
        @log_execution(log_args=True, log_execution_time=True)
        async def process_data(data):
            ...
    """
    def decorator(func: Callable) -> Callable:
        """内部函数：实际的装饰器"""
        func_name = func.__name__
        log_func = getattr(logger, log_level.lower(), logger.debug)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            """异步函数包装器"""
            import time
            start_time = time.time()

            # 内部逻辑：记录入口日志
            if log_args:
                log_func(f"开始执行函数: {func_name}, 参数: args={args}, kwargs={kwargs}")
            else:
                log_func(f"开始执行函数: {func_name}")

            try:
                # 内部逻辑：执行函数
                result = await func(*args, **kwargs)

                # 内部逻辑：记录出口日志
                if log_result:
                    log_func(f"函数 {func_name} 执行完成, 返回值: {result}")
                else:
                    log_func(f"函数 {func_name} 执行完成")

                return result

            finally:
                # 内部逻辑：记录执行时间
                if log_execution_time:
                    execution_time = time.time() - start_time
                    log_func(f"函数 {func_name} 执行时间: {execution_time:.3f}秒")

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            """同步函数包装器"""
            import time
            start_time = time.time()

            # 内部逻辑：记录入口日志
            if log_args:
                log_func(f"开始执行函数: {func_name}, 参数: args={args}, kwargs={kwargs}")
            else:
                log_func(f"开始执行函数: {func_name}")

            try:
                # 内部逻辑：执行函数
                result = func(*args, **kwargs)

                # 内部逻辑：记录出口日志
                if log_result:
                    log_func(f"函数 {func_name} 执行完成, 返回值: {result}")
                else:
                    log_func(f"函数 {func_name} 执行完成")

                return result

            finally:
                # 内部逻辑：记录执行时间
                if log_execution_time:
                    execution_time = time.time() - start_time
                    log_func(f"函数 {func_name} 执行时间: {execution_time:.3f}秒")

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# 内部变量：导出所有公共接口
__all__ = [
    'with_error_handling',
    'with_retry',
    'catch_and_return',
    'log_execution',
]
