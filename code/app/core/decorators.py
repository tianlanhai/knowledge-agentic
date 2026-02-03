"""
上海宇羲伏天智能科技有限公司出品

文件级注释：装饰器工具模块
内部逻辑：提供API端点常用的装饰器，统一错误处理和响应格式
设计模式：装饰器模式 - AOP面向切面编程
设计原则：DRY（不重复）、开闭原则（对扩展开放）
"""

from functools import wraps
from typing import Callable, Any, Optional, Tuple, Type, Dict
from enum import Enum
from fastapi import HTTPException
from loguru import logger
import asyncio
import time
import hashlib


def api_error_handler(
    error_message: str = "操作失败",
    error_code: int = 500
):
    """
    函数级注释：API错误处理装饰器
    内部逻辑：统一捕获异常并返回标准错误响应格式
    设计模式：装饰器模式 - 横切关注点分离
    参数：
        error_message - 错误消息前缀
        error_code - 默认错误状态码
    返回值：装饰器函数

    使用示例：
        @router.post("/chat")
        @api_error_handler("对话处理失败")
        async def chat_completion(request: ChatRequest):
            # 业务逻辑，无需重复的错误处理
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                # 内部逻辑：执行原函数
                return await func(*args, **kwargs)
            except HTTPException:
                # 内部逻辑：HTTPException直接向上抛出
                raise
            except ValueError as e:
                # 内部逻辑：业务异常返回400状态码
                logger.warning(f"业务异常 in {func.__name__}: {str(e)}")
                raise HTTPException(
                    status_code=400,
                    detail={
                        "success": False,
                        "error": {
                            "code": 400,
                            "message": f"{error_message}: {str(e)}"
                        }
                    }
                )
            except Exception as e:
                # 内部逻辑：未知异常返回500状态码
                logger.error(f"系统异常 in {func.__name__}: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=error_code,
                    detail={
                        "success": False,
                        "error": {
                            "code": error_code,
                            "message": f"{error_message}",
                            "details": str(e)
                        }
                    }
                )
        return wrapper
    return decorator


def log_execution(
    log_args: bool = True,
    log_result: bool = False
):
    """
    函数级注释：执行日志装饰器
    内部逻辑：记录函数执行的入参和结果
    设计模式：装饰器模式 - 横切日志关注点
    参数：
        log_args - 是否记录入参
        log_result - 是否记录返回值
    返回值：装饰器函数

    使用示例：
        @router.post("/chat")
        @log_execution(log_args=True, log_result=False)
        async def chat_completion(request: ChatRequest):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 内部逻辑：记录函数调用
            func_name = f"{func.__module__}.{func.__name__}"
            logger.info(f"调用函数: {func_name}")

            # 内部逻辑：记录入参
            if log_args:
                # 内部逻辑：过滤敏感参数
                safe_args = _filter_sensitive_args(args, kwargs)
                logger.debug(f"函数 {func_name} 入参: {safe_args}")

            # 内部逻辑：执行函数
            try:
                result = await func(*args, **kwargs)

                # 内部逻辑：记录返回值
                if log_result:
                    logger.debug(f"函数 {func_name} 返回: {str(result)[:200]}")

                logger.info(f"函数 {func_name} 执行成功")
                return result
            except Exception as e:
                logger.error(f"函数 {func_name} 执行失败: {str(e)}")
                raise
        return wrapper
    return decorator


def validate_request(schema: type):
    """
    函数级注释：请求验证装饰器
    内部逻辑：验证请求参数是否符合Pydantic模式
    设计模式：装饰器模式 - 参数验证关注点
    参数：
        schema - Pydantic模式类
    返回值：装饰器函数

    使用示例：
        @router.post("/chat")
        @validate_request(ChatRequest)
        async def chat_completion(request: ChatRequest):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 内部逻辑：查找请求参数
            for arg in args:
                if isinstance(arg, schema):
                    # 内部逻辑：Pydantic会自动验证
                    break
            else:
                # 内部逻辑：查找kwargs中的请求参数
                for key, value in kwargs.items():
                    if isinstance(value, schema):
                        break
                else:
                    logger.warning(f"未找到类型为 {schema.__name__} 的请求参数")

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def cache_response(
    ttl_seconds: int = 60,
    key_prefix: Optional[str] = None
):
    """
    函数级注释：响应缓存装饰器
    内部逻辑：缓存函数返回值，减少重复计算
    设计模式：装饰器模式 - 缓存关注点
    参数：
        ttl_seconds - 缓存存活时间（秒）
        key_prefix - 缓存键前缀
    返回值：装饰器函数

    注意：此装饰器为内存缓存，适用于单实例场景
    多实例场景建议使用Redis等外部缓存

    使用示例：
        @router.get("/sources")
        @cache_response(ttl_seconds=300, key_prefix="sources")
        async def get_sources(doc_id: int):
            pass
    """
    # 内部变量：缓存存储
    _cache: dict = {}

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 内部逻辑：生成缓存键
            import time
            import hashlib

            # 内部变量：基于函数名和参数生成唯一键
            params_str = str(args) + str(sorted(kwargs.items()))
            hash_key = hashlib.md5(params_str.encode()).hexdigest()
            cache_key = f"{key_prefix or func.__name__}:{hash_key}"

            # 内部逻辑：检查缓存
            if cache_key in _cache:
                cached_data, timestamp = _cache[cache_key]
                if time.time() - timestamp < ttl_seconds:
                    logger.debug(f"缓存命中: {cache_key}")
                    return cached_data
                else:
                    # 内部逻辑：缓存过期，删除
                    del _cache[cache_key]

            # 内部逻辑：执行函数并缓存结果
            result = await func(*args, **kwargs)
            _cache[cache_key] = (result, time.time())
            logger.debug(f"缓存更新: {cache_key}")

            return result
        return wrapper
    return decorator


def retry_on_failure(
    max_retries: int = 3,
    exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    backoff_factor: float = 0.5,
    strategy: str = "exponential"
):
    """
    函数级注释：失败重试装饰器（增强版）
    内部逻辑：当函数抛出指定异常时自动重试，支持多种退避策略
    设计模式：装饰器模式 - 重试逻辑关注点
    参数：
        max_retries - 最大重试次数
        exceptions - 需要重试的异常类型（None时自动判断可重试的异常）
        backoff_factor - 退避因子
        strategy - 退避策略（exponential/linear/fixed/immediate）
    返回值：装饰器函数

    使用示例：
        @router.post("/llm")
        @retry_on_failure(max_retries=2, exceptions=(ConnectionError,), strategy="exponential")
        async def call_llm(request: LLMRequest):
            pass
    """
    def decorator(func: Callable) -> Callable:
        # 内部逻辑：判断是否为异步函数
        is_async = asyncio.iscoroutinefunction(func)

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # 内部逻辑：检查是否为需要重试的异常类型
                    if exceptions and not isinstance(e, exceptions):
                        raise

                    # 内部逻辑：判断异常是否可重试
                    if not _is_retryable_error(e):
                        raise

                    # 内部逻辑：最后一次尝试不再等待
                    if attempt >= max_retries:
                        logger.error(
                            f"函数 {func.__name__} 达到最大重试次数 {max_retries}"
                        )
                        break

                    # 内部逻辑：计算等待时间
                    wait_time = _calculate_backoff(attempt, backoff_factor, strategy)
                    logger.warning(
                        f"函数 {func.__name__} 第 {attempt + 1} 次调用失败，"
                        f"{wait_time:.2f}秒后重试: {str(e)}"
                    )
                    await asyncio.sleep(wait_time)

            # 内部逻辑：所有重试失败后抛出最后一个异常
            raise last_exception

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if exceptions and not isinstance(e, exceptions):
                        raise

                    if not _is_retryable_error(e):
                        raise

                    if attempt >= max_retries:
                        logger.error(
                            f"函数 {func.__name__} 达到最大重试次数 {max_retries}"
                        )
                        break

                    wait_time = _calculate_backoff(attempt, backoff_factor, strategy)
                    logger.warning(
                        f"函数 {func.__name__} 第 {attempt + 1} 次调用失败，"
                        f"{wait_time:.2f}秒后重试: {str(e)}"
                    )
                    time.sleep(wait_time)

            raise last_exception

        # 内部逻辑：根据函数类型返回对应的包装器
        return async_wrapper if is_async else sync_wrapper

    return decorator


def _is_retryable_error(error: Exception) -> bool:
    """
    函数级注释：判断异常是否可重试（内部方法）
    参数：
        error - 异常对象
    返回值：是否可重试
    @private
    """
    # 内部逻辑：网络错误可重试
    if isinstance(error, (ConnectionError, TimeoutError)):
        return True

    # 内部逻辑：超时可重试
    error_msg = str(error).lower()
    retryable_keywords = [
        "timeout", "connection", "network", "temporarily",
        "rate limit", "429", "503", "502", "504"
    ]

    return any(keyword in error_msg for keyword in retryable_keywords)


def _calculate_backoff(attempt: int, factor: float, strategy: str) -> float:
    """
    函数级注释：计算退避时间（内部方法）
    参数：
        attempt - 当前尝试次数
        factor - 退避因子
        strategy - 退避策略
    返回值：等待时间（秒）
    @private
    """
    if strategy == "immediate":
        return 0
    elif strategy == "fixed":
        return factor
    elif strategy == "linear":
        return factor * (attempt + 1)
    else:  # exponential (默认)
        return factor * (2 ** attempt)


def _filter_sensitive_args(args: tuple, kwargs: dict) -> dict:
    """
    函数级注释：过滤敏感参数
    内部逻辑：移除或脱敏包含敏感信息的参数
    参数：
        args - 位置参数
        kwargs - 关键字参数
    返回值：过滤后的参数字典
    @private
    """
    # 内部变量：敏感参数名称列表
    sensitive_keys = {'password', 'api_key', 'token', 'secret', 'key'}

    safe_kwargs = {}
    for key, value in kwargs.items():
        # 内部逻辑：检查是否为敏感参数
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            # 内部逻辑：脱敏处理
            safe_value = f"***{len(str(value))}chars***" if value else "***"
            safe_kwargs[key] = safe_value
        else:
            safe_kwargs[key] = value

    return {
        "args_count": len(args),
        "kwargs": safe_kwargs
    }


# 内部逻辑：导入敏感信息过滤装饰器
# 注意：由于 decorators.py 和 decorators/ 目录同名冲突，需要使用绝对路径导入
# 将 decorators.py 重命名或重构为 decorators/__init__.py 可以解决此问题
# 这里暂时注释掉导入，需要时再处理
# from app.core.decorators.sensitive_filter import with_sensitive_filter, SensitiveDataFilterDecorator

# 内部变量：导出所有装饰器
__all__ = [
    'api_error_handler',
    'log_execution',
    'validate_request',
    'cache_response',
    'retry_on_failure',
    'timing',
    'singleton',
    'cached_property',
    'suppress_exceptions',
    'validate_permissions',
    'rate_limit',
    # 'with_sensitive_filter',  # 暂时禁用，由于导入冲突
    # 'SensitiveDataFilterDecorator',  # 暂时禁用，由于导入冲突
]


def timing(log_level: str = "debug"):
    """
    函数级注释：执行时间测量装饰器
    内部逻辑：记录函数执行时间，用于性能分析
    设计模式：装饰器模式 - 性能监控关注点
    参数：
        log_level - 日志级别
    返回值：装饰器函数

    使用示例：
        @timing(log_level="info")
        async def process_document(doc_id: int):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start_time
                log_func = getattr(logger, log_level, logger.debug)
                log_func(f"函数 {func.__name__} 执行时间: {elapsed:.3f}秒")

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start_time
                log_func = getattr(logger, log_level, logger.debug)
                log_func(f"函数 {func.__name__} 执行时间: {elapsed:.3f}秒")

        # 内部逻辑：根据函数类型返回对应的包装器
        is_async = asyncio.iscoroutinefunction(func)
        return async_wrapper if is_async else sync_wrapper

    return decorator


class _SingletonWrapper:
    """
    类级注释：单例包装器类
    设计模式：单例模式
    内部逻辑：确保一个类只有一个实例
    """

    # 内部变量：存储单例实例的字典
    _instances: Dict[type, Any] = {}
    # 内部变量：锁对象，用于线程安全
    _lock = asyncio.Lock()

    def __init__(self, cls: type):
        """
        函数级注释：初始化单例包装器
        参数：
            cls - 要包装的类
        """
        self._cls = cls
        self._lock = None

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        函数级注释：创建或获取单例实例
        参数：
            *args, **kwargs - 类构造函数参数
        返回值：单例实例
        """
        # 内部逻辑：检查是否已存在实例
        if self._cls not in self._instances:
            self._instances[self._cls] = self._cls(*args, **kwargs)
            logger.debug(f"创建单例实例: {self._cls.__name__}")
        return self._instances[self._cls]

    def __getattr__(self, name: str) -> Any:
        """
        函数级注释：代理属性访问到原始类
        参数：
            name - 属性名称
        返回值：属性值
        """
        return getattr(self._cls, name)


def singleton(cls: type) -> type:
    """
    函数级注释：单例类装饰器
    内部逻辑：确保一个类只有一个实例
    设计模式：单例模式 - 装饰器实现
    参数：
        cls - 要装饰的类
    返回值：单例包装后的类

    使用示例：
        @singleton
        class ConfigManager:
            def __init__(self):
                self.config = {}

        # 两次调用返回同一个实例
        config1 = ConfigManager()
        config2 = ConfigManager()
        assert config1 is config2
    """
    return _SingletonWrapper(cls)


class _CachedProperty:
    """
    类级注释：缓存属性描述符
    设计模式：享元模式 - 缓存计算结果
    内部逻辑：缓存属性值，避免重复计算
    """

    def __init__(self, func: Callable):
        """
        函数级注释：初始化缓存属性
        参数：
            func - 获取属性值的函数
        """
        self.func = func
        self.name = func.__name__
        self.cache_name = f"_cached_{self.name}"

    def __get__(self, instance: Any, owner: type) -> Any:
        """
        函数级注释：获取属性值
        参数：
            instance - 实例对象
            owner - 所有者类
        返回值：属性值
        """
        # 内部逻辑：如果实例为None，返回自身
        if instance is None:
            return self

        # 内部逻辑：检查缓存
        if hasattr(instance, self.cache_name):
            return getattr(instance, self.cache_name)

        # 内部逻辑：计算并缓存值
        value = self.func(instance)
        setattr(instance, self.cache_name, value)
        return value


def cached_property(func: Callable) -> _CachedProperty:
    """
    函数级注释：缓存属性装饰器
    内部逻辑：将方法转换为只读属性，并缓存结果
    设计模式：享元模式 - 缓存计算结果
    参数：
        func - 获取属性值的函数
    返回值：描述符对象

    使用示例：
        class DataProcessor:
            def __init__(self, data):
                self.data = data

            @cached_property
            def processed_data(self):
                # 昂贵的计算只执行一次
                return self._complex_processing()

    注意：Python 3.8+ 已有 functools.cached_property
    此实现用于兼容性和额外功能
    """
    return _CachedProperty(func)


def suppress_exceptions(
    *exceptions: Type[Exception],
    default_return: Any = None,
    log_error: bool = True
):
    """
    函数级注释：抑制异常装饰器
    内部逻辑：捕获指定异常并返回默认值，不中断程序流程
    设计模式：装饰器模式 - 异常处理关注点
    参数：
        *exceptions - 要抑制的异常类型（默认所有异常）
        default_return - 发生异常时的默认返回值
        log_error - 是否记录错误日志
    返回值：装饰器函数

    使用示例：
        @suppress_exceptions(ValueError, default_return=0)
        def parse_int(value: str) -> int:
            return int(value)

        result = parse_int("invalid")  # 返回0，不抛出异常
    """
    if not exceptions:
        exceptions = (Exception,)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except exceptions as e:
                if log_error:
                    logger.warning(
                        f"函数 {func.__name__} 抑制异常: {type(e).__name__}: {str(e)}"
                    )
                return default_return

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                if log_error:
                    logger.warning(
                        f"函数 {func.__name__} 抑制异常: {type(e).__name__}: {str(e)}"
                    )
                return default_return

        is_async = asyncio.iscoroutinefunction(func)
        return async_wrapper if is_async else sync_wrapper

    return decorator


def validate_permissions(*required_permissions: str):
    """
    函数级注释：权限验证装饰器
    内部逻辑：验证当前用户是否拥有所需权限
    设计模式：装饰器模式 - 权限验证关注点
    参数：
        *required_permissions - 需要的权限列表
    返回值：装饰器函数

    使用示例：
        @router.delete("/documents/{doc_id}")
        @validate_permissions("document:delete")
        async def delete_document(doc_id: int):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 内部逻辑：尝试从kwargs获取用户信息
            user = kwargs.get('user') or kwargs.get('current_user')

            if user is None:
                # 内部逻辑：尝试从args获取
                for arg in args:
                    if hasattr(arg, 'permissions'):
                        user = arg
                        break

            if user is None:
                logger.warning(f"函数 {func.__name__} 权限验证失败：未找到用户信息")
                raise HTTPException(
                    status_code=401,
                    detail={"code": "UNAUTHORIZED", "message": "用户未认证"}
                )

            # 内部逻辑：检查权限
            user_permissions = getattr(user, 'permissions', [])
            if isinstance(user_permissions, str):
                user_permissions = [user_permissions]

            missing = [
                p for p in required_permissions
                if p not in user_permissions
            ]

            if missing:
                logger.warning(
                    f"函数 {func.__name__} 权限验证失败：缺少权限 {missing}"
                )
                raise HTTPException(
                    status_code=403,
                    detail={
                        "code": "FORBIDDEN",
                        "message": f"缺少必要权限: {', '.join(missing)}"
                    }
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def rate_limit(max_calls: int, period_seconds: int = 60):
    """
    函数级注释：速率限制装饰器
    内部逻辑：限制函数在指定时间内的调用次数
    设计模式：装饰器模式 - 速率限制关注点
    参数：
        max_calls - 时间窗口内最大调用次数
        period_seconds - 时间窗口大小（秒）
    返回值：装饰器函数

    使用示例：
        @rate_limit(max_calls=10, period_seconds=60)
        async def expensive_operation():
            pass
    """
    # 内部变量：调用记录存储 {func_name: [(timestamp, caller_id), ...]}
    _call_history: Dict[str, list] = {}

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            import time as time_module

            # 内部逻辑：生成调用者标识
            caller_id = id(args[0]) if args else "default"
            func_name = func.__name__
            key = f"{func_name}:{caller_id}"
            now = time_module.time()

            # 内部逻辑：初始化调用记录
            if key not in _call_history:
                _call_history[key] = []

            # 内部逻辑：清理过期记录
            _call_history[key] = [
                (ts, cid) for ts, cid in _call_history[key]
                if now - ts < period_seconds
            ]

            # 内部逻辑：检查是否超过限制
            if len(_call_history[key]) >= max_calls:
                logger.warning(
                    f"函数 {func_name} 速率限制触发："
                    f"{period_seconds}秒内最多{max_calls}次调用"
                )
                raise HTTPException(
                    status_code=429,
                    detail={
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"调用频率超限，{period_seconds}秒内最多{max_calls}次"
                    }
                )

            # 内部逻辑：记录本次调用
            _call_history[key].append((now, caller_id))

            return await func(*args, **kwargs)

        return wrapper

    return decorator
