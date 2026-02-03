# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：LLM 调用代理模块
内部逻辑：为 LLM 调用添加缓存、限流、访问控制等横切关注点
设计模式：代理模式 - 虚拟代理、智能引用
设计原则：单一职责原则、开闭原则
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable
from collections import OrderedDict
from loguru import logger
import hashlib
import time
import asyncio
from datetime import datetime, timedelta


class LRUCache:
    """
    类级注释：LRU 缓存实现
    内部逻辑：基于 OrderedDict 实现最近最少使用缓存
    设计模式：缓存模式
    """

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """
        函数级注释：初始化 LRU 缓存
        参数：
            max_size - 最大缓存条目数
            ttl_seconds - 缓存过期时间（秒）
        """
        # 内部变量：缓存存储
        self._cache: OrderedDict[str, Any] = OrderedDict()
        # 内部变量：时间戳存储
        self._timestamps: Dict[str, float] = {}
        # 内部变量：最大缓存大小
        self._max_size = max_size
        # 内部变量：过期时间
        self._ttl = ttl_seconds

    def _is_expired(self, key: str) -> bool:
        """
        函数级注释：检查缓存是否过期
        内部逻辑：当前时间 - 存储时间 > TTL 则过期
        参数：
            key - 缓存键
        返回值：是否过期
        """
        if key not in self._timestamps:
            return True
        return time.time() - self._timestamps[key] > self._ttl

    def get(self, key: str) -> Optional[Any]:
        """
        函数级注释：获取缓存值
        内部逻辑：检查过期 -> 移动到末尾（标记最近使用） -> 返回值
        参数：
            key - 缓存键
        返回值：缓存值或 None
        """
        # Guard Clauses：键不存在或已过期
        if key not in self._cache or self._is_expired(key):
            return None

        # 内部逻辑：移动到末尾（标记为最近使用）
        self._cache.move_to_end(key)
        return self._cache[key]

    def put(self, key: str, value: Any) -> None:
        """
        函数级注释：存储缓存值
        内部逻辑：达到上限时删除最旧的 -> 存储新值 -> 记录时间戳
        参数：
            key - 缓存键
            value - 缓存值
        """
        # 内部逻辑：如果键已存在，先删除（后面重新插入到末尾）
        if key in self._cache:
            del self._cache[key]

        # 内部逻辑：达到上限时删除最旧的项
        elif len(self._cache) >= self._max_size:
            # 弹出最旧的项
            oldest_key, _ = self._cache.popitem(last=False)
            del self._timestamps[oldest_key]
            logger.debug(f"LRU 缓存已满，移除最旧项: {oldest_key}")

        # 内部逻辑：存储新值
        self._cache[key] = value
        self._timestamps[key] = time.time()

    def clear(self) -> None:
        """
        函数级注释：清空缓存
        内部逻辑：清空所有缓存和时间戳
        """
        self._cache.clear()
        self._timestamps.clear()
        logger.debug("LRU 缓存已清空")

    def size(self) -> int:
        """
        函数级注释：获取缓存大小
        返回值：当前缓存条目数
        """
        return len(self._cache)


class RateLimiter:
    """
    类级注释：限流器实现
    内部逻辑：基于滑动窗口的限流算法
    设计模式：限流模式（Rate Limiting Pattern）
    """

    def __init__(self, max_calls: int = 100, window_seconds: int = 60):
        """
        函数级注释：初始化限流器
        参数：
            max_calls - 时间窗口内最大调用次数
            window_seconds - 时间窗口大小（秒）
        """
        # 内部变量：调用记录存储 {key: [(timestamp, count), ...]}
        self._calls: Dict[str, List[float]] = {}
        # 内部变量：最大调用次数
        self._max_calls = max_calls
        # 内部变量：时间窗口大小
        self._window = window_seconds

    def _clean_old_calls(self, key: str) -> None:
        """
        函数级注释：清理过期的调用记录
        内部逻辑：移除时间窗口外的记录
        参数：
            key - 限流键
        """
        now = time.time()
        window_start = now - self._window

        # 内部逻辑：只保留窗口内的记录
        if key in self._calls:
            self._calls[key] = [
                timestamp for timestamp in self._calls[key]
                if timestamp > window_start
            ]

    def is_allowed(self, key: str) -> bool:
        """
        函数级注释：检查是否允许调用
        内部逻辑：清理过期记录 -> 检查当前窗口内调用次数
        参数：
            key - 限流键
        返回值：是否允许调用
        """
        now = time.time()

        # 内部逻辑：初始化键
        if key not in self._calls:
            self._calls[key] = []

        # 内部逻辑：清理过期记录
        self._clean_old_calls(key)

        # 内部逻辑：检查是否超过限制
        if len(self._calls[key]) >= self._max_calls:
            logger.warning(f"限流触发: {key}, 当前调用数: {len(self._calls[key])}")
            return False

        # 内部逻辑：记录本次调用
        self._calls[key].append(now)
        return True

    def get_wait_time(self, key: str) -> float:
        """
        函数级注释：获取需要等待的时间
        内部逻辑：计算最早调用记录的剩余时间
        参数：
            key - 限流键
        返回值：需要等待的秒数
        """
        self._clean_old_calls(key)

        # 内部逻辑：如果没有超过限制，无需等待
        if key not in self._calls or len(self._calls[key]) < self._max_calls:
            return 0.0

        # 内部逻辑：计算最早记录的剩余时间
        oldest_call = self._calls[key][0]
        wait_time = self._window - (time.time() - oldest_call)
        return max(0.0, wait_time)

    def clear(self, key: Optional[str] = None) -> None:
        """
        函数级注释：清除限流记录
        参数：
            key - 限流键，为 None 时清除所有
        """
        if key:
            self._calls.pop(key, None)
        else:
            self._calls.clear()


class CircuitBreaker:
    """
    类级注释：熔断器实现
    内部逻辑：连续失败达到阈值后熔断，一段时间后半开尝试
    设计模式：熔断器模式（Circuit Breaker Pattern）
    """

    # 内部变量：熔断状态枚举
    CLOSED = "closed"      # 正常状态
    OPEN = "open"          # 熔断状态
    HALF_OPEN = "half_open"  # 半开状态

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        success_threshold: int = 2
    ):
        """
        函数级注释：初始化熔断器
        参数：
            failure_threshold - 失败阈值
            timeout_seconds - 熔断超时时间（秒）
            success_threshold - 半开状态成功恢复阈值
        """
        # 内部变量：失败计数
        self._failure_count = 0
        # 内部变量：成功计数（半开状态用）
        self._success_count = 0
        # 内部变量：熔断状态
        self._state = self.CLOSED
        # 内部变量：最后失败时间
        self._last_failure_time: Optional[float] = None
        # 内部变量：失败阈值
        self._failure_threshold = failure_threshold
        # 内部变量：熔断超时
        self._timeout = timeout_seconds
        # 内部变量：成功恢复阈值
        self._success_threshold = success_threshold

    def _can_attempt_reset(self) -> bool:
        """
        函数级注释：检查是否可以尝试重置
        内部逻辑：超时时间已过则允许尝试
        返回值：是否可以尝试重置
        """
        if self._last_failure_time is None:
            return True
        return time.time() - self._last_failure_time >= self._timeout

    def record_success(self) -> None:
        """
        函数级注释：记录成功
        内部逻辑：重置失败计数 -> 半开状态下检查是否恢复
        """
        if self._state == self.HALF_OPEN:
            self._success_count += 1
            # 内部逻辑：达到成功阈值则恢复
            if self._success_count >= self._success_threshold:
                self._state = self.CLOSED
                self._failure_count = 0
                self._success_count = 0
                logger.info("熔断器已恢复到正常状态")
        else:
            self._failure_count = 0

    def record_failure(self) -> None:
        """
        函数级注释：记录失败
        内部逻辑：增加失败计数 -> 达到阈值则熔断
        """
        self._failure_count += 1
        self._last_failure_time = time.time()

        # 内部逻辑：达到失败阈值则熔断
        if self._failure_count >= self._failure_threshold:
            if self._state != self.OPEN:
                self._state = self.OPEN
                logger.error(f"熔断器已打开，失败次数: {self._failure_count}")

    def can_execute(self) -> bool:
        """
        函数级注释：检查是否可以执行
        内部逻辑：根据状态判断
        返回值：是否允许执行
        """
        # 内部逻辑：正常状态可以执行
        if self._state == self.CLOSED:
            return True

        # 内部逻辑：熔断状态检查是否可以尝试
        if self._state == self.OPEN:
            if self._can_attempt_reset():
                self._state = self.HALF_OPEN
                self._success_count = 0
                logger.info("熔断器进入半开状态")
                return True
            return False

        # 内部逻辑：半开状态可以执行
        return self._state == self.HALF_OPEN

    def get_state(self) -> str:
        """
        函数级注释：获取当前状态
        返回值：熔断状态
        """
        return self._state

    def reset(self) -> None:
        """
        函数级注释：重置熔断器
        内部逻辑：恢复到正常状态
        """
        self._state = self.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        logger.info("熔断器已手动重置")


class LLMProxyInterface(ABC):
    """
    类级注释：LLM 代理接口
    内部逻辑：定义 LLM 代理的统一接口
    设计模式：代理模式 - 抽象主题接口
    """

    @abstractmethod
    async def ainvoke(self, prompt: str, **kwargs) -> str:
        """
        函数级注释：异步调用 LLM
        参数：
            prompt - 提示词
            **kwargs - 额外参数
        返回值：LLM 响应文本
        """
        pass

    @abstractmethod
    async def astream(self, prompt: str, **kwargs):
        """
        函数级注释：异步流式调用 LLM
        参数：
            prompt - 提示词
            **kwargs - 额外参数
        返回值：异步生成器
        """
        pass


class LLMProxy(LLMProxyInterface):
    """
    类级注释：LLM 调用代理
    内部逻辑：包装真实的 LLM 实例，添加缓存、限流、熔断等功能
    设计模式：代理模式 - 智能引用代理
    职责：
        1. 缓存 LLM 响应（减少成本）
        2. 限流控制（防止 API 滥用）
        3. 熔断保护（防止级联故障）
        4. 访问控制（权限验证）
        5. 日志记录（调用审计）
    """

    def __init__(
        self,
        real_llm: Any,
        cache_enabled: bool = True,
        cache_size: int = 1000,
        cache_ttl: int = 3600,
        rate_limit_enabled: bool = True,
        max_calls: int = 100,
        window_seconds: int = 60,
        circuit_breaker_enabled: bool = True,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        success_threshold: int = 2
    ):
        """
        函数级注释：初始化 LLM 代理
        参数：
            real_llm - 真实的 LLM 实例
            cache_enabled - 是否启用缓存
            cache_size - 缓存大小
            cache_ttl - 缓存过期时间（秒）
            rate_limit_enabled - 是否启用限流
            max_calls - 时间窗口内最大调用次数
            window_seconds - 时间窗口大小（秒）
            circuit_breaker_enabled - 是否启用熔断
            failure_threshold - 熔断失败阈值
            timeout_seconds - 熔断超时时间（秒）
            success_threshold - 熔断恢复成功阈值
        """
        # 内部变量：真实的 LLM 实例
        self._real_llm = real_llm

        # 内部变量：缓存配置
        self._cache_enabled = cache_enabled
        self._cache = LRUCache(max_size=cache_size, ttl_seconds=cache_ttl) if cache_enabled else None

        # 内部变量：限流配置
        self._rate_limit_enabled = rate_limit_enabled
        self._rate_limiter = RateLimiter(max_calls=max_calls, window_seconds=window_seconds) if rate_limit_enabled else None

        # 内部变量：熔断配置
        self._circuit_breaker_enabled = circuit_breaker_enabled
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            timeout_seconds=timeout_seconds,
            success_threshold=success_threshold
        ) if circuit_breaker_enabled else None

        # 内部变量：访问控制函数列表
        self._access_checkers: List[Callable[[str, Dict[str, Any]], bool]] = []

        # 内部变量：统计信息
        self._stats = {
            "total_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "rate_limited": 0,
            "circuit_opened": 0,
            "failures": 0
        }

        logger.info(
            f"LLM代理初始化完成: 缓存={cache_enabled}, "
            f"限流={rate_limit_enabled}, 熔断={circuit_breaker_enabled}"
        )

    def add_access_checker(self, checker: Callable[[str, Dict[str, Any]], bool]) -> None:
        """
        函数级注释：添加访问控制函数
        参数：
            checker - 访问检查函数，接收 (prompt, kwargs)，返回是否允许
        """
        self._access_checkers.append(checker)

    def _generate_cache_key(self, prompt: str, **kwargs) -> str:
        """
        函数级注释：生成缓存键
        内部逻辑：基于 prompt 和 kwargs 的哈希值
        参数：
            prompt - 提示词
            **kwargs - 额外参数
        返回值：缓存键
        """
        # 内部逻辑：创建包含所有参数的字符串
        params_str = f"{prompt}:{sorted(kwargs.items())}"
        # 内部逻辑：生成哈希
        return hashlib.md5(params_str.encode()).hexdigest()

    def _check_access(self, prompt: str, kwargs: Dict[str, Any]) -> bool:
        """
        函数级注释：检查访问权限
        内部逻辑：执行所有访问控制函数
        参数：
            prompt - 提示词
            kwargs - 额外参数
        返回值：是否允许访问
        """
        for checker in self._access_checkers:
            if not checker(prompt, kwargs):
                logger.warning("访问被拒绝: 访问控制检查失败")
                return False
        return True

    async def ainvoke(self, prompt: str, **kwargs) -> str:
        """
        函数级注释：异步调用 LLM（代理入口）
        内部逻辑：访问控制 -> 熔断检查 -> 限流检查 -> 缓存检查 -> 调用真实对象 -> 缓存结果
        参数：
            prompt - 提示词
            **kwargs - 额外参数
        返回值：LLM 响应文本
        异常： RuntimeError - 熔断器打开时
                 PermissionError - 访问被拒绝时
        """
        self._stats["total_calls"] += 1

        # 内部逻辑：访问控制检查
        if not self._check_access(prompt, kwargs):
            raise PermissionError("LLM 调用被访问控制拒绝")

        # 内部逻辑：熔断检查
        if self._circuit_breaker_enabled and not self._circuit_breaker.can_execute():
            self._stats["circuit_opened"] += 1
            raise RuntimeError(
                f"熔断器已打开，请稍后重试。"
                f"当前状态: {self._circuit_breaker.get_state()}"
            )

        # 内部逻辑：限流检查
        if self._rate_limit_enabled:
            cache_key = self._generate_cache_key(prompt, **kwargs)
            if not self._rate_limiter.is_allowed(cache_key):
                wait_time = self._rate_limiter.get_wait_time(cache_key)
                self._stats["rate_limited"] += 1
                raise RuntimeError(
                    f"调用频率超限，请等待 {wait_time:.1f} 秒后重试"
                )

        # 内部逻辑：缓存检查
        cache_key = self._generate_cache_key(prompt, **kwargs)
        if self._cache_enabled:
            cached_result = self._cache.get(cache_key)
            if cached_result is not None:
                self._stats["cache_hits"] += 1
                logger.debug(f"缓存命中: {cache_key[:8]}...")
                return cached_result
            self._stats["cache_misses"] += 1

        # 内部逻辑：调用真实 LLM
        try:
            logger.info(f"调用 LLM: {prompt[:50]}...")
            result = await self._real_llm.ainvoke(prompt, **kwargs)

            # 内部逻辑：缓存结果
            if self._cache_enabled:
                self._cache.put(cache_key, result)

            # 内部逻辑：记录成功
            if self._circuit_breaker_enabled:
                self._circuit_breaker.record_success()

            return result

        except Exception as e:
            # 内部逻辑：记录失败
            if self._circuit_breaker_enabled:
                self._circuit_breaker.record_failure()
            self._stats["failures"] += 1
            logger.error(f"LLM 调用失败: {str(e)}")
            raise

    async def astream(self, prompt: str, **kwargs):
        """
        函数级注释：异步流式调用 LLM
        内部逻辑：流式调用不使用缓存，但仍需熔断和限流检查
        参数：
            prompt - 提示词
            **kwargs - 额外参数
        返回值：异步生成器
        """
        self._stats["total_calls"] += 1

        # 内部逻辑：访问控制检查
        if not self._check_access(prompt, kwargs):
            raise PermissionError("LLM 调用被访问控制拒绝")

        # 内部逻辑：熔断检查
        if self._circuit_breaker_enabled and not self._circuit_breaker.can_execute():
            self._stats["circuit_opened"] += 1
            raise RuntimeError("熔断器已打开，流式调用被拒绝")

        # 内部逻辑：限流检查
        if self._rate_limit_enabled:
            cache_key = f"stream:{self._generate_cache_key(prompt, **kwargs)}"
            if not self._rate_limiter.is_allowed(cache_key):
                wait_time = self._rate_limiter.get_wait_time(cache_key)
                raise RuntimeError(
                    f"调用频率超限，请等待 {wait_time:.1f} 秒后重试"
                )

        # 内部逻辑：流式调用真实 LLM
        try:
            logger.info(f"流式调用 LLM: {prompt[:50]}...")
            async for chunk in self._real_llm.astream(prompt, **kwargs):
                yield chunk

            # 内部逻辑：记录成功
            if self._circuit_breaker_enabled:
                self._circuit_breaker.record_success()

        except Exception as e:
            if self._circuit_breaker_enabled:
                self._circuit_breaker.record_failure()
            self._stats["failures"] += 1
            logger.error(f"LLM 流式调用失败: {str(e)}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """
        函数级注释：获取统计信息
        返回值：统计信息字典
        """
        stats = self._stats.copy()
        stats["cache_hit_rate"] = (
            stats["cache_hits"] / stats["total_calls"] * 100
            if stats["total_calls"] > 0 else 0
        )
        stats["circuit_state"] = (
            self._circuit_breaker.get_state()
            if self._circuit_breaker else "disabled"
        )
        return stats

    def reset_stats(self) -> None:
        """
        函数级注释：重置统计信息
        内部逻辑：清空所有统计数据
        """
        self._stats = {
            "total_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "rate_limited": 0,
            "circuit_opened": 0,
            "failures": 0
        }
        logger.info("LLM代理统计信息已重置")

    def clear_cache(self) -> None:
        """
        函数级注释：清空缓存
        内部逻辑：调用 LRU 缓存的清空方法
        """
        if self._cache:
            self._cache.clear()
            logger.info("LLM代理缓存已清空")

    def reset_circuit_breaker(self) -> None:
        """
        函数级注释：重置熔断器
        内部逻辑：调用熔断器的重置方法
        """
        if self._circuit_breaker:
            self._circuit_breaker.reset()


class LLMProxyFactory:
    """
    类级注释：LLM 代理工厂
    内部逻辑：管理 LLM 代理的创建和配置
    设计模式：工厂模式 + 单例模式
    """

    # 内部变量：单例实例
    _instance: Optional['LLMProxyFactory'] = None

    # 内部变量：代理实例缓存
    _proxies: Dict[str, LLMProxy] = {}

    def __new__(cls) -> 'LLMProxyFactory':
        """
        函数级注释：实现单例模式
        返回值：LLMProxyFactory 单例实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def create_proxy(
        self,
        real_llm: Any,
        name: str = "default",
        **config
    ) -> LLMProxy:
        """
        函数级注释：创建或获取 LLM 代理
        内部逻辑：检查缓存 -> 存在则返回 -> 不存在则创建
        参数：
            real_llm - 真实的 LLM 实例
            name - 代理名称（用于缓存）
            **config - 代理配置
        返回值：LLM 代理实例
        """
        # 内部逻辑：检查缓存
        if name in self._proxies:
            logger.debug(f"返回已存在的 LLM 代理: {name}")
            return self._proxies[name]

        # 内部逻辑：创建新代理
        proxy = LLMProxy(real_llm, **config)
        self._proxies[name] = proxy
        logger.info(f"创建新的 LLM 代理: {name}")
        return proxy

    def get_proxy(self, name: str) -> Optional[LLMProxy]:
        """
        函数级注释：获取已创建的代理
        参数：
            name - 代理名称
        返回值：代理实例或 None
        """
        return self._proxies.get(name)

    def remove_proxy(self, name: str) -> None:
        """
        函数级注释：移除代理
        参数：
            name - 代理名称
        """
        self._proxies.pop(name, None)
        logger.info(f"移除 LLM 代理: {name}")

    def clear_all(self) -> None:
        """
        函数级注释：清空所有代理
        """
        self._proxies.clear()
        logger.info("清空所有 LLM 代理")


# 内部变量：全局代理工厂实例
llm_proxy_factory = LLMProxyFactory()


# 内部变量：导出所有公共接口
__all__ = [
    'LLMProxy',
    'LLMProxyInterface',
    'LLMProxyFactory',
    'llm_proxy_factory',
    'LRUCache',
    'RateLimiter',
    'CircuitBreaker',
]
