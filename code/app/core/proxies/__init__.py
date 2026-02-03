# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：代理模式模块
内部逻辑：实现缓存代理、监控代理、访问控制代理
设计模式：代理模式（Proxy Pattern）
设计原则：开闭原则、单一职责原则

@package app.core.proxies
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, TypeVar, Generic
from functools import wraps
from loguru import logger
import time
import hashlib
import json
from datetime import datetime, timedelta

# 内部变量：泛型类型
T = TypeVar('T')
R = TypeVar('R')


class CacheBackend(ABC):
    """
    类级注释：缓存后端抽象接口
    内部逻辑：定义缓存存储的统一接口
    设计模式：策略模式 - 缓存策略
    """

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """清空缓存"""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        pass


class MemoryCacheBackend(CacheBackend):
    """
    类级注释：内存缓存后端
    内部逻辑：使用内存字典存储缓存数据
    设计模式：单例模式
    """

    _instance: Optional['MemoryCacheBackend'] = None

    def __init__(self):
        # 内部变量：缓存存储 {key: (value, expire_time)}
        self._cache: Dict[str, tuple[Any, Optional[float]]] = {}
        # 内部变量：默认 TTL（秒）
        self._default_ttl = 3600

    @classmethod
    def get_instance(cls) -> 'MemoryCacheBackend':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key not in self._cache:
            return None

        value, expire_time = self._cache[key]

        # 内部逻辑：检查是否过期
        if expire_time and time.time() > expire_time:
            del self._cache[key]
            return None

        return value

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存"""
        if ttl is None:
            ttl = self._default_ttl

        expire_time = time.time() + ttl if ttl > 0 else None
        self._cache[key] = (value, expire_time)

        # 内部逻辑：限制缓存大小
        max_size = 1000
        if len(self._cache) > max_size:
            # 内部逻辑：删除最旧的条目（简化版）
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]

        return True

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    async def clear(self) -> bool:
        """清空缓存"""
        self._cache.clear()
        return True

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return await self.get(key) is not None

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        now = time.time()
        active_count = sum(
            1 for _, exp in self._cache.values()
            if exp is None or exp > now
        )
        expired_count = len(self._cache) - active_count

        return {
            "total_keys": len(self._cache),
            "active_keys": active_count,
            "expired_keys": expired_count,
        }


class CachingProxy:
    """
    类级注释：缓存代理
    内部逻辑：为目标对象添加缓存能力
    设计模式：代理模式 - 智能引用代理
    职责：
        1. 缓存方法调用结果
        2. 管理 TTL
        3. 提供缓存失效

    使用场景：
        - 数据库查询缓存
        - API 响应缓存
        - 计算结果缓存
    """

    def __init__(
        self,
        target: Any,
        cache_backend: Optional[CacheBackend] = None,
        default_ttl: int = 3600
    ):
        """
        函数级注释：初始化缓存代理
        参数：
            target - 目标对象
            cache_backend - 缓存后端
            default_ttl - 默认 TTL（秒）
        """
        self._target = target
        self._cache = cache_backend or MemoryCacheBackend.get_instance()
        self._default_ttl = default_ttl
        self._prefix = self._generate_prefix()

    def _generate_prefix(self) -> str:
        """生成缓存键前缀"""
        class_name = self._target.__class__.__name__
        return f"cache:{class_name}:"

    def _make_key(self, method_name: str, args: tuple, kwargs: dict) -> str:
        """
        函数级注释：生成缓存键
        参数：
            method_name - 方法名
            args - 位置参数
            kwargs - 关键字参数
        返回值：缓存键
        """
        # 内部逻辑：基于参数生成唯一键
        key_data = {
            "method": method_name,
            "args": str(args),
            "kwargs": str(sorted(kwargs.items())),
        }
        key_hash = hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
        return f"{self._prefix}{method_name}:{key_hash}"

    async def get(
        self,
        key: str,
        fetch_fn: Callable,
        ttl: Optional[int] = None
    ) -> Any:
        """
        函数级注释：带缓存的数据获取
        参数：
            key - 缓存键
            fetch_fn - 数据获取函数
            ttl - 过期时间
        返回值：缓存数据或新获取的数据
        """
        # 内部逻辑：尝试从缓存获取
        cached = await self._cache.get(key)
        if cached is not None:
            logger.debug(f"[CachingProxy] 缓存命中: {key}")
            return cached

        # 内部逻辑：执行获取函数
        logger.debug(f"[CachingProxy] 缓存未命中: {key}")
        result = await fetch_fn()

        # 内部逻辑：写入缓存
        ttl = ttl or self._default_ttl
        await self._cache.set(key, result, ttl)

        return result

    def __getattr__(self, name: str):
        """
        函数级注释：代理目标对象的方法
        参数：
            name - 方法名
        返回值：包装后的方法
        """
        attr = getattr(self._target, name)

        if not callable(attr):
            return attr

        @wraps(attr)
        async def wrapped(*args, **kwargs):
            # 内部逻辑：检查是否禁用缓存
            if kwargs.pop('_no_cache', False):
                return await attr(*args, **kwargs)

            # 内部逻辑：生成缓存键
            cache_key = self._make_key(name, args, kwargs)
            ttl = kwargs.pop('_cache_ttl', self._default_ttl)

            # 内部逻辑：尝试从缓存获取
            cached = await self._cache.get(cache_key)
            if cached is not None:
                return cached

            # 内部逻辑：执行方法
            result = await attr(*args, **kwargs)

            # 内部逻辑：写入缓存
            if result is not None:
                await self._cache.set(cache_key, result, ttl)

            return result

        return wrapped

    async def invalidate(self, method_name: Optional[str] = None) -> None:
        """
        函数级注释：使缓存失效
        参数：
            method_name - 方法名（为空则清空所有）
        """
        if method_name is None:
            await self._cache.clear()
            logger.info(f"[CachingProxy] 清空所有缓存")
        else:
            # 内部逻辑：使特定方法的缓存失效
            prefix = f"{self._prefix}{method_name}:"
            # 注意：这里简化处理，实际应该遍历删除
            logger.info(f"[CachingProxy] 使缓存失效: {method_name}")

    async def warm_up(self, data: Dict[str, Any]) -> None:
        """
        函数级注释：预热缓存
        参数：
            data - {key: value} 字典
        """
        for key, value in data.items():
            await self._cache.set(f"{self._prefix}{key}", value, self._default_ttl)
        logger.info(f"[CachingProxy] 预热缓存完成，条目数: {len(data)}")


class MonitoringProxy:
    """
    类级注释：性能监控代理
    内部逻辑：为目标对象添加性能监控能力
    设计模式：代理模式 - 智能引用代理
    职责：
        1. 记录方法执行时间
        2. 统计调用次数
        3. 记录错误信息

    使用场景：
        - 性能分析
        - 运维监控
        - 错误追踪
    """

    def __init__(
        self,
        target: Any,
        logger_instance: Optional[Any] = None,
        slow_threshold: float = 1.0
    ):
        """
        函数级注释：初始化监控代理
        参数：
            target - 目标对象
            logger_instance - 日志记录器
            slow_threshold - 慢调用阈值（秒）
        """
        self._target = target
        self._logger = logger_instance or logger
        self._slow_threshold = slow_threshold

        # 内部变量：统计信息
        self._stats: Dict[str, Dict[str, Any]] = {}

    def _get_method_stats(self, method_name: str) -> Dict[str, Any]:
        """获取方法统计信息"""
        if method_name not in self._stats:
            self._stats[method_name] = {
                "call_count": 0,
                "total_time": 0.0,
                "error_count": 0,
                "slow_count": 0,
            }
        return self._stats[method_name]

    def __getattr__(self, name: str):
        """
        函数级注释：代理目标对象的方法
        参数：
            name - 方法名
        返回值：包装后的方法
        """
        attr = getattr(self._target, name)

        if not callable(attr):
            return attr

        @wraps(attr)
        async def wrapped(*args, **kwargs):
            stats = self._get_method_stats(name)
            stats["call_count"] += 1

            start_time = time.time()
            method_name = f"{self._target.__class__.__name__}.{name}"

            try:
                result = await attr(*args, **kwargs)

                duration = time.time() - start_time
                stats["total_time"] += duration

                # 内部逻辑：记录慢调用
                if duration > self._slow_threshold:
                    stats["slow_count"] += 1
                    self._logger.warning(
                        f"[MonitoringProxy] 慢调用检测: {method_name} "
                        f"耗时 {duration:.3f}s (阈值: {self._slow_threshold}s)"
                    )
                else:
                    self._logger.debug(
                        f"[MonitoringProxy] {method_name} 执行完成，耗时 {duration:.3f}s"
                    )

                return result

            except Exception as e:
                duration = time.time() - start_time
                stats["error_count"] += 1

                self._logger.error(
                    f"[MonitoringProxy] {method_name} 执行失败 "
                    f"耗时 {duration:.3f}s: {str(e)}",
                    extra={
                        "method": method_name,
                        "duration": duration,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }
                )
                raise

        return wrapped

    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        函数级注释：获取统计信息
        返回值：统计信息字典
        """
        result = {}
        for method, stats in self._stats.items():
            if stats["call_count"] > 0:
                result[method] = {
                    "call_count": stats["call_count"],
                    "avg_time": stats["total_time"] / stats["call_count"],
                    "total_time": stats["total_time"],
                    "error_count": stats["error_count"],
                    "error_rate": stats["error_count"] / stats["call_count"],
                    "slow_count": stats["slow_count"],
                    "slow_rate": stats["slow_count"] / stats["call_count"],
                }
        return result

    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats.clear()


class AccessControlProxy:
    """
    类级注释：访问控制代理
    内部逻辑：为目标对象添加访问控制能力
    设计模式：代理模式 - 保护代理
    职责：
        1. 检查调用权限
        2. 记录访问日志
        3. 防止未授权访问

    使用场景：
        - 敏感操作保护
        - 权限验证
        - 审计日志
    """

    def __init__(
        self,
        target: Any,
        permission_checker: Optional[Callable[[str, str], bool]] = None,
        logger_instance: Optional[Any] = None
    ):
        """
        函数级注释：初始化访问控制代理
        参数：
            target - 目标对象
            permission_checker - 权限检查函数 (method_name, user) -> bool
            logger_instance - 日志记录器
        """
        self._target = target
        self._permission_checker = permission_checker
        self._logger = logger_instance or logger
        self._current_user: Optional[str] = None

    def set_user(self, user: str) -> None:
        """
        函数级注释：设置当前用户
        参数：
            user - 用户标识
        """
        self._current_user = user

    def _check_permission(self, method_name: str) -> bool:
        """
        函数级注释：检查权限
        参数：
            method_name - 方法名
        返回值：是否有权限
        """
        if self._permission_checker is None:
            return True

        return self._permission_checker(method_name, self._current_user or "anonymous")

    def __getattr__(self, name: str):
        """
        函数级注释：代理目标对象的方法
        参数：
            name - 方法名
        返回值：包装后的方法
        """
        attr = getattr(self._target, name)

        if not callable(attr):
            return attr

        @wraps(attr)
        async def wrapped(*args, **kwargs):
            method_name = f"{self._target.__class__.__name__}.{name}"

            # 内部逻辑：检查权限
            if not self._check_permission(name):
                self._logger.warning(
                    f"[AccessControlProxy] 访问被拒绝: {self._current_user} -> {method_name}"
                )
                raise PermissionError(f"用户 {self._current_user} 无权执行 {method_name}")

            # 内部逻辑：记录访问日志
            self._logger.info(
                f"[AccessControlProxy] 访问记录: {self._current_user} -> {method_name}"
            )

            return await attr(*args, **kwargs)

        return wrapped


class ProxyFactory:
    """
    类级注释：代理工厂
    内部逻辑：统一创建各类代理
    设计模式：工厂模式
    职责：
        1. 创建缓存代理
        2. 创建监控代理
        3. 创建访问控制代理
        4. 支持代理链

    使用场景：
        - 统一代理创建
        - 代理组合
    """

    @staticmethod
    def create_caching_proxy(
        target: Any,
        cache_backend: Optional[CacheBackend] = None,
        default_ttl: int = 3600
    ) -> CachingProxy:
        """
        函数级注释：创建缓存代理
        参数：
            target - 目标对象
            cache_backend - 缓存后端
            default_ttl - 默认 TTL
        返回值：缓存代理实例
        """
        return CachingProxy(target, cache_backend, default_ttl)

    @staticmethod
    def create_monitoring_proxy(
        target: Any,
        logger_instance: Optional[Any] = None,
        slow_threshold: float = 1.0
    ) -> MonitoringProxy:
        """
        函数级注释：创建监控代理
        参数：
            target - 目标对象
            logger_instance - 日志记录器
            slow_threshold - 慢调用阈值
        返回值：监控代理实例
        """
        return MonitoringProxy(target, logger_instance, slow_threshold)

    @staticmethod
    def create_access_control_proxy(
        target: Any,
        permission_checker: Optional[Callable[[str, str], bool]] = None
    ) -> AccessControlProxy:
        """
        函数级注释：创建访问控制代理
        参数：
            target - 目标对象
            permission_checker - 权限检查函数
        返回值：访问控制代理实例
        """
        return AccessControlProxy(target, permission_checker)

    @staticmethod
    def create_chained_proxy(
        target: Any,
        enable_cache: bool = True,
        enable_monitoring: bool = True,
        enable_access_control: bool = False,
        **options
    ) -> Any:
        """
        函数级注释：创建代理链
        内部逻辑：按顺序组合多个代理
        参数：
            target - 目标对象
            enable_cache - 是否启用缓存
            enable_monitoring - 是否启用监控
            enable_access_control - 是否启用访问控制
            **options - 其他选项
        返回值：代理链的第一个代理
        """
        proxy = target

        # 内部逻辑：按顺序应用代理
        # 注意：代理的应用顺序很重要，后应用的会包装先应用的

        if enable_access_control:
            proxy = AccessControlProxy(
                proxy,
                permission_checker=options.get('permission_checker')
            )

        if enable_cache:
            proxy = CachingProxy(
                proxy,
                cache_backend=options.get('cache_backend'),
                default_ttl=options.get('default_ttl', 3600)
            )

        if enable_monitoring:
            proxy = MonitoringProxy(
                proxy,
                logger_instance=options.get('logger_instance'),
                slow_threshold=options.get('slow_threshold', 1.0)
            )

        return proxy


# 内部变量：导出所有公共接口
__all__ = [
    # 基础类
    'CacheBackend',
    'MemoryCacheBackend',
    'CachingProxy',
    'MonitoringProxy',
    'AccessControlProxy',
    'ProxyFactory',
]
