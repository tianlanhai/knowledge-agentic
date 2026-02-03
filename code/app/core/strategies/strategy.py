# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：策略模式实现模块
内部逻辑：定义策略模式的核心接口
设计模式：策略模式（Strategy Pattern）
设计原则：SOLID - 开闭原则、里氏替换原则

使用场景：
    - 搜索策略（向量搜索、关键词搜索、混合搜索）
    - 重试策略（固定延迟、指数退避、随机抖动）
    - 排序策略（相关性、时间、热度）
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable, TypeVar
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from loguru import logger
import time
import random
import asyncio

T = TypeVar('T')


class StrategyType(str, Enum):
    """
    类级注释：策略类型枚举
    职责：定义系统中的策略类型
    """
    # 搜索策略
    VECTOR_SEARCH = "vector_search"
    KEYWORD_SEARCH = "keyword_search"
    HYBRID_SEARCH = "hybrid_search"
    SEMANTIC_SEARCH = "semantic_search"

    # 重试策略
    RETRY_FIXED = "retry_fixed"
    RETRY_EXPONENTIAL = "retry_exponential"
    RETRY_LINEAR = "retry_linear"
    RETRY_IMMEDIATE = "retry_immediate"

    # 排序策略
    SORT_RELEVANCE = "sort_relevance"
    SORT_TIME = "sort_time"
    SORT_POPULARITY = "sort_popularity"
    SORT_CUSTOM = "sort_custom"

    # 分页策略
    PAGE_CURSOR = "page_cursor"
    PAGE_OFFSET = "page_offset"


@dataclass
class StrategyContext:
    """
    类级注释：策略上下文
    职责：封装策略执行时的上下文信息
    """
    user_id: Optional[str] = None  # 用户ID
    session_id: Optional[str] = None  # 会话ID
    timestamp: datetime = field(default_factory=datetime.now)  # 执行时间
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据


class Strategy(ABC):
    """
    类级注释：策略抽象基类
    设计模式：策略模式（Strategy Pattern）- 策略接口
    职责：定义策略的执行接口

    设计优势：
        - 算法与使用者解耦
        - 运行时动态切换策略
        - 易于扩展新策略
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        函数级注释：获取策略名称
        返回值：策略名称
        """
        pass

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """
        函数级注释：执行策略
        参数：
            *args: 位置参数
            **kwargs: 关键字参数
        返回值：策略执行结果
        """
        pass

    def before_execute(self, context: StrategyContext) -> None:
        """
        函数级注释：执行前钩子
        参数：
            context: 策略上下文
        """
        pass

    def after_execute(self, context: StrategyContext, result: Any) -> Any:
        """
        函数级注释：执行后钩子
        参数：
            context: 策略上下文
            result: 执行结果
        返回值：可能被修改的结果
        """
        return result

    def on_error(self, context: StrategyContext, error: Exception) -> None:
        """
        函数级注释：错误处理钩子
        参数：
            context: 策略上下文
            error: 异常对象
        """
        logger.error(f"策略 {self.name} 执行出错: {error}")


# ============================================================================
# 重试策略
# ============================================================================

class RetryStrategy(Strategy):
    """
    类级注释：重试策略基类
    设计模式：策略模式 + 模板方法模式
    职责：定义重试策略的模板
    """

    def __init__(
        self,
        max_retries: int = 3,
        on_retry: Optional[Callable[[int, Exception], None]] = None
    ):
        """
        函数级注释：初始化重试策略
        参数：
            max_retries: 最大重试次数
            on_retry: 重试回调函数
        """
        self.max_retries = max_retries
        self.on_retry = on_retry

    @abstractmethod
    def get_delay(self, attempt: int) -> float:
        """
        函数级注释：计算重试延迟
        参数：
            attempt: 当前尝试次数
        返回值：延迟秒数
        """
        pass

    def execute(
        self,
        func: Callable,
        *args,
        context: Optional[StrategyContext] = None,
        **kwargs
    ) -> Any:
        """
        函数级注释：执行带重试的函数
        参数：
            func: 要执行的函数
            *args: 位置参数
            context: 策略上下文
            **kwargs: 关键字参数
        返回值：函数执行结果
        """
        context = context or StrategyContext()
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                self.before_execute(context)

                # 内部逻辑：执行函数
                if asyncio.iscoroutinefunction(func):
                    result = asyncio.run(func(*args, **kwargs))
                else:
                    result = func(*args, **kwargs)

                return self.after_execute(context, result)

            except Exception as e:
                last_error = e

                # 内部逻辑：检查是否需要重试
                if attempt < self.max_retries:
                    delay = self.get_delay(attempt + 1)
                    logger.warning(f"策略 {self.name} 第 {attempt + 1} 次尝试失败，{delay}秒后重试: {e}")

                    # 内部逻辑：调用重试回调
                    if self.on_retry:
                        self.on_retry(attempt + 1, e)

                    time.sleep(delay)
                else:
                    self.on_error(context, e)
                    raise

        # 内部逻辑：所有重试都失败
        raise last_error


class FixedRetryStrategy(RetryStrategy):
    """
    类级注释：固定延迟重试策略
    设计模式：策略模式 - 具体策略
    职责：使用固定延迟进行重试
    """

    def __init__(
        self,
        delay: float = 1.0,
        max_retries: int = 3,
        on_retry: Optional[Callable[[int, Exception], None]] = None
    ):
        """
        函数级注释：初始化固定延迟重试策略
        参数：
            delay: 固定延迟秒数
            max_retries: 最大重试次数
            on_retry: 重试回调
        """
        super().__init__(max_retries, on_retry)
        self._delay = delay

    @property
    def name(self) -> str:
        return StrategyType.RETRY_FIXED.value

    def get_delay(self, attempt: int) -> float:
        """固定延迟"""
        return self._delay


class ExponentialRetryStrategy(RetryStrategy):
    """
    类级注释：指数退避重试策略
    设计模式：策略模式 - 具体策略
    职责：使用指数退避进行重试
    """

    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponent: float = 2.0,
        max_retries: int = 3,
        on_retry: Optional[Callable[[int, Exception], None]] = None
    ):
        """
        函数级注释：初始化指数退避重试策略
        参数：
            base_delay: 基础延迟秒数
            max_delay: 最大延迟秒数
            exponent: 指数因子
            max_retries: 最大重试次数
            on_retry: 重试回调
        """
        super().__init__(max_retries, on_retry)
        self._base_delay = base_delay
        self._max_delay = max_delay
        self._exponent = exponent

    @property
    def name(self) -> str:
        return StrategyType.RETRY_EXPONENTIAL.value

    def get_delay(self, attempt: int) -> float:
        """指数退避延迟"""
        delay = self._base_delay * (self._exponent ** (attempt - 1))
        return min(delay, self._max_delay)


class LinearRetryStrategy(RetryStrategy):
    """
    类级注释：线性递增重试策略
    设计模式：策略模式 - 具体策略
    职责：使用线性递增延迟进行重试
    """

    def __init__(
        self,
        base_delay: float = 1.0,
        increment: float = 1.0,
        max_delay: float = 60.0,
        max_retries: int = 3,
        on_retry: Optional[Callable[[int, Exception], None]] = None
    ):
        """
        函数级注释：初始化线性递增重试策略
        参数：
            base_delay: 基础延迟秒数
            increment: 每次递增的延迟
            max_delay: 最大延迟秒数
            max_retries: 最大重试次数
            on_retry: 重试回调
        """
        super().__init__(max_retries, on_retry)
        self._base_delay = base_delay
        self._increment = increment
        self._max_delay = max_delay

    @property
    def name(self) -> str:
        return StrategyType.RETRY_LINEAR.value

    def get_delay(self, attempt: int) -> float:
        """线性递增延迟"""
        delay = self._base_delay + (attempt - 1) * self._increment
        return min(delay, self._max_delay)


class JitterRetryStrategy(ExponentialRetryStrategy):
    """
    类级注释：抖动重试策略
    设计模式：策略模式 - 装饰器模式
    职责：在指数退避基础上添加随机抖动

    设计优势：
        - 避免雷鸣羊群效应
        - 更均匀的重试分布
    """

    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponent: float = 2.0,
        jitter_factor: float = 0.5,
        max_retries: int = 3,
        on_retry: Optional[Callable[[int, Exception], None]] = None
    ):
        """
        函数级注释：初始化抖动重试策略
        参数：
            jitter_factor: 抖动因子（0-1）
            其他参数同指数退避
        """
        super().__init__(base_delay, max_delay, exponent, max_retries, on_retry)
        self._jitter_factor = jitter_factor

    @property
    def name(self) -> str:
        return "retry_jitter"

    def get_delay(self, attempt: int) -> float:
        """带抖动的指数退避延迟"""
        base_delay = super().get_delay(attempt)
        # 内部逻辑：添加随机抖动
        jitter = base_delay * self._jitter_factor * random.random()
        return base_delay + jitter


# ============================================================================
# 搜索策略
# ============================================================================

@dataclass
class SearchResult:
    """
    类级注释：搜索结果数据类
    职责：封装搜索结果
    """
    content: str  # 匹配的内容
    score: float  # 相关性分数
    source: str  # 来源
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据


class SearchStrategy(Strategy):
    """
    类级注释：搜索策略基类
    设计模式：策略模式 - 抽象策略
    职责：定义搜索策略的接口
    """

    @abstractmethod
    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        context: Optional[StrategyContext] = None
    ) -> List[SearchResult]:
        """
        函数级注释：执行搜索
        参数：
            query: 搜索查询
            top_k: 返回结果数量
            filters: 过滤条件
            context: 搜索上下文
        返回值：搜索结果列表
        """
        pass

    def execute(self, query: str, **kwargs) -> List[SearchResult]:
        """执行搜索（适配Strategy接口）"""
        return self.search(query, **kwargs)


class VectorSearchStrategy(SearchStrategy):
    """
    类级注释：向量搜索策略
    设计模式：策略模式 - 具体策略
    职责：基于向量相似度进行搜索

    使用场景：
        - 语义搜索
        - 相似文档查找
    """

    def __init__(self, embedding_service=None, vector_store=None):
        """
        函数级注释：初始化向量搜索策略
        参数：
            embedding_service: 向量化服务
            vector_store: 向量数据库
        """
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    @property
    def name(self) -> str:
        return StrategyType.VECTOR_SEARCH.value

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        context: Optional[StrategyContext] = None
    ) -> List[SearchResult]:
        """执行向量搜索"""
        context = context or StrategyContext()
        self.before_execute(context)

        try:
            # 内部逻辑：向量化查询
            # embedding = self.embedding_service.embed(query)
            # results = self.vector_store.similarity_search(embedding, top_k, filters)

            # 内部逻辑：模拟返回（实际使用时替换为真实实现）
            results = [
                SearchResult(
                    content=f"向量搜索结果 {i+1}",
                    score=0.9 - i * 0.1,
                    source="vector_db",
                    metadata={"query": query}
                )
                for i in range(min(top_k, 3))
            ]

            return self.after_execute(context, results)

        except Exception as e:
            self.on_error(context, e)
            return []


class KeywordSearchStrategy(SearchStrategy):
    """
    类级注释：关键词搜索策略
    设计模式：策略模式 - 具体策略
    职责：基于关键词匹配进行搜索

    使用场景：
        - 精确匹配
        - 标题搜索
    """

    def __init__(self, document_store=None):
        """
        函数级注释：初始化关键词搜索策略
        参数：
            document_store: 文档存储
        """
        self.document_store = document_store

    @property
    def name(self) -> str:
        return StrategyType.KEYWORD_SEARCH.value

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        context: Optional[StrategyContext] = None
    ) -> List[SearchResult]:
        """执行关键词搜索"""
        context = context or StrategyContext()
        self.before_execute(context)

        try:
            # 内部逻辑：执行关键词搜索
            # results = self.document_store.keyword_search(query, top_k, filters)

            # 内部逻辑：模拟返回
            results = [
                SearchResult(
                    content=f"关键词搜索结果 {i+1}",
                    score=1.0 if query.lower() in f"关键词搜索结果 {i+1}".lower() else 0.5,
                    source="keyword_db",
                    metadata={"query": query}
                )
                for i in range(min(top_k, 3))
            ]

            return self.after_execute(context, results)

        except Exception as e:
            self.on_error(context, e)
            return []


class HybridSearchStrategy(SearchStrategy):
    """
    类级注释：混合搜索策略
    设计模式：策略模式 + 组合模式
    职责：组合多种搜索策略

    设计优势：
        - 综合多种搜索方式
        - 提高搜索召回率
        - 可配置权重
    """

    def __init__(
        self,
        strategies: List[SearchStrategy],
        weights: Optional[List[float]] = None
    ):
        """
        函数级注释：初始化混合搜索策略
        参数：
            strategies: 子策略列表
            weights: 各策略权重
        """
        self.strategies = strategies
        self.weights = weights or [1.0] * len(strategies)

    @property
    def name(self) -> str:
        return StrategyType.HYBRID_SEARCH.value

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        context: Optional[StrategyContext] = None
    ) -> List[SearchResult]:
        """执行混合搜索"""
        context = context or StrategyContext()
        self.before_execute(context)

        try:
            # 内部逻辑：收集所有策略的结果
            all_results: Dict[str, SearchResult] = {}

            for strategy, weight in zip(self.strategies, self.weights):
                strategy_results = strategy.search(query, top_k * 2, filters, context)

                # 内部逻辑：合并结果并加权
                for result in strategy_results:
                    key = f"{result.source}_{result.content}"
                    if key in all_results:
                        # 内部逻辑：合并分数
                        all_results[key].score += result.score * weight
                    else:
                        result.score *= weight
                        all_results[key] = result

            # 内部逻辑：排序并取前top_k
            sorted_results = sorted(
                all_results.values(),
                key=lambda r: r.score,
                reverse=True
            )[:top_k]

            return self.after_execute(context, sorted_results)

        except Exception as e:
            self.on_error(context, e)
            return []


# ============================================================================
# 策略工厂
# ============================================================================

class StrategyFactory:
    """
    类级注释：策略工厂
    设计模式：工厂模式 + 策略模式
    职责：创建和管理策略实例

    设计优势：
        - 集中管理策略
        - 支持策略缓存
        - 便于扩展新策略
    """

    # 内部类变量：策略注册表
    _strategies: Dict[str, type] = {}
    _instances: Dict[str, Strategy] = {}

    @classmethod
    def register(cls, name: str, strategy_class: type) -> None:
        """
        函数级注释：注册策略
        参数：
            name: 策略名称
            strategy_class: 策略类
        """
        cls._strategies[name] = strategy_class
        logger.info(f"注册策略: {name}")

    @classmethod
    def create(cls, name: str, **kwargs) -> Optional[Strategy]:
        """
        函数级注释：创建策略实例
        参数：
            name: 策略名称
            **kwargs: 策略参数
        返回值：策略实例或None
        """
        strategy_class = cls._strategies.get(name)
        if not strategy_class:
            logger.error(f"未知策略: {name}")
            return None

        # 内部逻辑：创建缓存键
        cache_key = f"{name}_{hash(frozenset(kwargs.items()))}"

        # 内部逻辑：检查缓存
        if cache_key in cls._instances:
            return cls._instances[cache_key]

        # 内部逻辑：创建新实例
        instance = strategy_class(**kwargs)
        cls._instances[cache_key] = instance
        return instance

    @classmethod
    def get_retry_strategy(
        cls,
        strategy_type: str = StrategyType.RETRY_EXPONENTIAL.value,
        **kwargs
    ) -> RetryStrategy:
        """
        函数级注释：获取重试策略
        参数：
            strategy_type: 策略类型
            **kwargs: 策略参数
        返回值：重试策略实例
        """
        return cls.create(strategy_type, **kwargs)

    @classmethod
    def get_search_strategy(
        cls,
        strategy_type: str = StrategyType.VECTOR_SEARCH.value,
        **kwargs
    ) -> SearchStrategy:
        """
        函数级注释：获取搜索策略
        参数：
            strategy_type: 策略类型
            **kwargs: 策略参数
        返回值：搜索策略实例
        """
        return cls.create(strategy_type, **kwargs)

    @classmethod
    def list_strategies(cls) -> List[str]:
        """
        函数级注释：列出所有已注册策略
        返回值：策略名称列表
        """
        return list(cls._strategies.keys())

    @classmethod
    def clear_cache(cls) -> None:
        """清除策略实例缓存"""
        cls._instances.clear()


# 内部逻辑：注册默认策略
StrategyFactory.register(StrategyType.RETRY_FIXED.value, FixedRetryStrategy)
StrategyFactory.register(StrategyType.RETRY_EXPONENTIAL.value, ExponentialRetryStrategy)
StrategyFactory.register(StrategyType.RETRY_LINEAR.value, LinearRetryStrategy)
StrategyFactory.register("retry_jitter", JitterRetryStrategy)
StrategyFactory.register(StrategyType.VECTOR_SEARCH.value, VectorSearchStrategy)
StrategyFactory.register(StrategyType.KEYWORD_SEARCH.value, KeywordSearchStrategy)
StrategyFactory.register(StrategyType.HYBRID_SEARCH.value, HybridSearchStrategy)


# 导入asyncio用于异步检测
import asyncio


# 内部变量：导出公共接口
__all__ = [
    'StrategyType',
    'StrategyContext',
    'Strategy',
    'RetryStrategy',
    'FixedRetryStrategy',
    'ExponentialRetryStrategy',
    'LinearRetryStrategy',
    'JitterRetryStrategy',
    'SearchStrategy',
    'SearchResult',
    'VectorSearchStrategy',
    'KeywordSearchStrategy',
    'HybridSearchStrategy',
    'StrategyFactory',
]
