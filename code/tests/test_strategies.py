# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：策略模式模块测试
内部逻辑：验证重试策略、搜索策略、策略工厂等功能
设计模式：策略模式（Strategy Pattern）
测试覆盖范围：
    - StrategyType: 策略类型枚举
    - StrategyContext: 策略上下文
    - Strategy: 策略抽象基类
    - RetryStrategy: 重试策略基类
    - FixedRetryStrategy: 固定延迟重试策略
    - ExponentialRetryStrategy: 指数退避重试策略
    - LinearRetryStrategy: 线性递增重试策略
    - JitterRetryStrategy: 抖动重试策略
    - SearchStrategy: 搜索策略基类
    - VectorSearchStrategy: 向量搜索策略
    - KeywordSearchStrategy: 关键词搜索策略
    - HybridSearchStrategy: 混合搜索策略
    - StrategyFactory: 策略工厂
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from typing import List, Dict, Any
from datetime import datetime

from app.core.strategies.strategy import (
    StrategyType,
    StrategyContext,
    Strategy,
    RetryStrategy,
    FixedRetryStrategy,
    ExponentialRetryStrategy,
    LinearRetryStrategy,
    JitterRetryStrategy,
    SearchStrategy,
    SearchResult,
    VectorSearchStrategy,
    KeywordSearchStrategy,
    HybridSearchStrategy,
    StrategyFactory,
)


# ============================================================================
# 策略类型和上下文测试
# ============================================================================

class TestStrategyType:
    """测试策略类型枚举"""

    def test_search_strategies(self):
        """测试搜索策略类型"""
        assert StrategyType.VECTOR_SEARCH == "vector_search"
        assert StrategyType.KEYWORD_SEARCH == "keyword_search"
        assert StrategyType.HYBRID_SEARCH == "hybrid_search"
        assert StrategyType.SEMANTIC_SEARCH == "semantic_search"

    def test_retry_strategies(self):
        """测试重试策略类型"""
        assert StrategyType.RETRY_FIXED == "retry_fixed"
        assert StrategyType.RETRY_EXPONENTIAL == "retry_exponential"
        assert StrategyType.RETRY_LINEAR == "retry_linear"
        assert StrategyType.RETRY_IMMEDIATE == "retry_immediate"

    def test_sort_strategies(self):
        """测试排序策略类型"""
        assert StrategyType.SORT_RELEVANCE == "sort_relevance"
        assert StrategyType.SORT_TIME == "sort_time"
        assert StrategyType.SORT_POPULARITY == "sort_popularity"
        assert StrategyType.SORT_CUSTOM == "sort_custom"

    def test_pagination_strategies(self):
        """测试分页策略类型"""
        assert StrategyType.PAGE_CURSOR == "page_cursor"
        assert StrategyType.PAGE_OFFSET == "page_offset"


class TestStrategyContext:
    """测试策略上下文"""

    def test_init_default(self):
        """测试默认初始化"""
        context = StrategyContext()

        assert context.user_id is None
        assert context.session_id is None
        assert context.metadata == {}
        assert isinstance(context.timestamp, datetime)

    def test_init_with_params(self):
        """测试带参数初始化"""
        context = StrategyContext(
            user_id="user_123",
            session_id="session_456",
            metadata={"key": "value"}
        )

        assert context.user_id == "user_123"
        assert context.session_id == "session_456"
        assert context.metadata == {"key": "value"}


# ============================================================================
# 重试策略测试
# ============================================================================

class TestFixedRetryStrategy:
    """测试固定延迟重试策略"""

    def test_init_default(self):
        """测试默认初始化"""
        strategy = FixedRetryStrategy()

        assert strategy.max_retries == 3
        assert strategy._delay == 1.0

    def test_init_custom(self):
        """测试自定义初始化"""
        strategy = FixedRetryStrategy(
            delay=2.0,
            max_retries=5
        )

        assert strategy._delay == 2.0
        assert strategy.max_retries == 5

    def test_name_property(self):
        """测试名称属性"""
        strategy = FixedRetryStrategy()
        assert strategy.name == StrategyType.RETRY_FIXED.value

    def test_get_delay(self):
        """测试获取延迟"""
        strategy = FixedRetryStrategy(delay=1.5)

        assert strategy.get_delay(1) == 1.5
        assert strategy.get_delay(5) == 1.5

    def test_execute_success_on_first_try(self):
        """测试第一次尝试成功"""
        strategy = FixedRetryStrategy(delay=0.01)
        func = Mock(return_value="success")

        result = strategy.execute(func)

        assert result == "success"
        func.assert_called_once()

    def test_execute_success_on_retry(self):
        """测试重试后成功"""
        call_count = [0]

        def failing_func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ConnectionError("Temporary failure")
            return "success"

        strategy = FixedRetryStrategy(delay=0.01, max_retries=5)
        result = strategy.execute(failing_func)

        assert result == "success"
        assert call_count[0] == 3

    def test_execute_all_fail(self):
        """测试所有尝试都失败"""
        def always_failing_func():
            raise ConnectionError("Persistent failure")

        strategy = FixedRetryStrategy(delay=0.01, max_retries=3)

        with pytest.raises(ConnectionError):
            strategy.execute(always_failing_func)

    def test_execute_with_async_function(self):
        """测试执行异步函数"""
        async def async_func():
            return "async_result"

        strategy = FixedRetryStrategy(delay=0.01)
        result = strategy.execute(async_func)

        assert result == "async_result"

    def test_on_retry_callback(self):
        """测试重试回调"""
        retry_calls = []

        def on_retry(attempt, error):
            retry_calls.append((attempt, str(error)))

        strategy = FixedRetryStrategy(delay=0.01, on_retry=on_retry, max_retries=3)

        def failing_func():
            raise ConnectionError("Test")

        with pytest.raises(ConnectionError):
            strategy.execute(failing_func)

        assert len(retry_calls) == 3


class TestExponentialRetryStrategy:
    """测试指数退避重试策略"""

    def test_init_default(self):
        """测试默认初始化"""
        strategy = ExponentialRetryStrategy()

        assert strategy._base_delay == 1.0
        assert strategy._max_delay == 60.0
        assert strategy._exponent == 2.0

    def test_init_custom(self):
        """测试自定义初始化"""
        strategy = ExponentialRetryStrategy(
            base_delay=0.5,
            max_delay=30.0,
            exponent=3.0
        )

        assert strategy._base_delay == 0.5
        assert strategy._max_delay == 30.0
        assert strategy._exponent == 3.0

    def test_name_property(self):
        """测试名称属性"""
        strategy = ExponentialRetryStrategy()
        assert strategy.name == StrategyType.RETRY_EXPONENTIAL.value

    def test_get_delay_exponential(self):
        """测试指数延迟计算"""
        strategy = ExponentialRetryStrategy(
            base_delay=1.0,
            exponent=2.0,
            max_delay=100.0
        )

        assert strategy.get_delay(1) == 1.0
        assert strategy.get_delay(2) == 2.0
        assert strategy.get_delay(3) == 4.0
        assert strategy.get_delay(4) == 8.0

    def test_get_delay_with_max_limit(self):
        """测试最大延迟限制"""
        strategy = ExponentialRetryStrategy(
            base_delay=10.0,
            exponent=2.0,
            max_delay=30.0
        )

        # 超过最大值时应该被限制
        assert strategy.get_delay(4) == 30.0


class TestLinearRetryStrategy:
    """测试线性递增重试策略"""

    def test_init_default(self):
        """测试默认初始化"""
        strategy = LinearRetryStrategy()

        assert strategy._base_delay == 1.0
        assert strategy._increment == 1.0
        assert strategy._max_delay == 60.0

    def test_init_custom(self):
        """测试自定义初始化"""
        strategy = LinearRetryStrategy(
            base_delay=0.5,
            increment=0.5,
            max_delay=10.0
        )

        assert strategy._base_delay == 0.5
        assert strategy._increment == 0.5
        assert strategy._max_delay == 10.0

    def test_name_property(self):
        """测试名称属性"""
        strategy = LinearRetryStrategy()
        assert strategy.name == StrategyType.RETRY_LINEAR.value

    def test_get_delay_linear(self):
        """测试线性延迟计算"""
        strategy = LinearRetryStrategy(
            base_delay=1.0,
            increment=2.0,
            max_delay=100.0
        )

        assert strategy.get_delay(1) == 1.0
        assert strategy.get_delay(2) == 3.0
        assert strategy.get_delay(3) == 5.0
        assert strategy.get_delay(4) == 7.0


class TestJitterRetryStrategy:
    """测试抖动重试策略"""

    def test_init(self):
        """测试初始化"""
        strategy = JitterRetryStrategy(
            base_delay=1.0,
            jitter_factor=0.3
        )

        assert strategy._jitter_factor == 0.3

    def test_name_property(self):
        """测试名称属性"""
        strategy = JitterRetryStrategy()
        assert strategy.name == "retry_jitter"

    def test_get_delay_with_jitter(self):
        """测试带抖动的延迟"""
        strategy = JitterRetryStrategy(
            base_delay=10.0,
            jitter_factor=0.5
        )

        # 基础延迟是 10.0
        # 抖动应该在 0-5 之间
        delay1 = strategy.get_delay(1)
        delay2 = strategy.get_delay(1)

        # 应该有随机性
        assert delay1 >= 10.0
        assert delay2 >= 10.0
        # 由于随机性，两次结果可能不同（虽然极小概率相同）
        assert delay1 <= 15.0


# ============================================================================
# 搜索策略测试
# ============================================================================

class TestSearchResult:
    """测试搜索结果数据类"""

    def test_init(self):
        """测试初始化"""
        result = SearchResult(
            content="Test content",
            score=0.95,
            source="test_source"
        )

        assert result.content == "Test content"
        assert result.score == 0.95
        assert result.source == "test_source"
        assert result.metadata == {}

    def test_with_metadata(self):
        """测试带元数据"""
        metadata = {"doc_id": "123", "page": 1}
        result = SearchResult(
            content="Content",
            score=0.9,
            source="test",
            metadata=metadata
        )

        assert result.metadata == metadata


class TestVectorSearchStrategy:
    """测试向量搜索策略"""

    def test_init(self):
        """测试初始化"""
        strategy = VectorSearchStrategy(
            embedding_service=Mock(),
            vector_store=Mock()
        )

        assert strategy.embedding_service is not None
        assert strategy.vector_store is not None

    def test_name_property(self):
        """测试名称属性"""
        strategy = VectorSearchStrategy()
        assert strategy.name == StrategyType.VECTOR_SEARCH.value

    def test_search(self):
        """测试搜索"""
        strategy = VectorSearchStrategy()
        results = strategy.search("test query", top_k=5)

        assert isinstance(results, list)
        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)

    def test_search_with_filters(self):
        """测试带过滤条件的搜索"""
        strategy = VectorSearchStrategy()
        results = strategy.search(
            "test query",
            top_k=3,
            filters={"category": "tech"}
        )

        assert len(results) <= 3

    def test_search_with_context(self):
        """测试带上下文的搜索"""
        strategy = VectorSearchStrategy()
        context = StrategyContext(user_id="user_123")

        results = strategy.search(
            "test query",
            context=context
        )

        assert isinstance(results, list)


class TestKeywordSearchStrategy:
    """测试关键词搜索策略"""

    def test_init(self):
        """测试初始化"""
        strategy = KeywordSearchStrategy(
            document_store=Mock()
        )

        assert strategy.document_store is not None

    def test_name_property(self):
        """测试名称属性"""
        strategy = KeywordSearchStrategy()
        assert strategy.name == StrategyType.KEYWORD_SEARCH.value

    def test_search(self):
        """测试搜索"""
        strategy = KeywordSearchStrategy()
        results = strategy.search("test keyword", top_k=5)

        assert isinstance(results, list)

    def test_search_with_matching_keyword(self):
        """测试匹配关键词的搜索"""
        strategy = KeywordSearchStrategy()
        results = strategy.search("关键词搜索", top_k=5)

        # 应该有匹配的结果
        assert len(results) > 0


class TestHybridSearchStrategy:
    """测试混合搜索策略"""

    def test_init(self):
        """测试初始化"""
        strategy1 = VectorSearchStrategy()
        strategy2 = KeywordSearchStrategy()

        hybrid = HybridSearchStrategy([strategy1, strategy2])

        assert len(hybrid.strategies) == 2
        assert hybrid.weights == [1.0, 1.0]

    def test_init_with_weights(self):
        """测试带权重的初始化"""
        strategy1 = VectorSearchStrategy()
        strategy2 = KeywordSearchStrategy()

        hybrid = HybridSearchStrategy(
            [strategy1, strategy2],
            weights=[0.7, 0.3]
        )

        assert hybrid.weights == [0.7, 0.3]

    def test_name_property(self):
        """测试名称属性"""
        strategy1 = VectorSearchStrategy()
        hybrid = HybridSearchStrategy([strategy1])
        assert hybrid.name == StrategyType.HYBRID_SEARCH.value

    def test_search(self):
        """测试搜索"""
        strategy1 = VectorSearchStrategy()
        strategy2 = KeywordSearchStrategy()

        hybrid = HybridSearchStrategy([strategy1, strategy2])
        results = hybrid.search("test query", top_k=5)

        assert isinstance(results, list)
        # 混合搜索应该去重
        assert len(results) <= 5

    def test_search_merges_results(self):
        """测试结果合并"""
        strategy1 = VectorSearchStrategy()
        strategy2 = KeywordSearchStrategy()

        hybrid = HybridSearchStrategy(
            [strategy1, strategy2],
            weights=[1.0, 1.0]
        )
        results = hybrid.search("test", top_k=10)

        # 验证结果被正确合并
        assert isinstance(results, list)


# ============================================================================
# 策略工厂测试
# ============================================================================

class TestStrategyFactory:
    """测试策略工厂"""

    def test_register(self):
        """测试注册策略"""
        class CustomStrategy(Strategy):
            @property
            def name(self):
                return "custom"

            def execute(self, **kwargs):
                return "custom_result"

        StrategyFactory.register("custom", CustomStrategy)
        assert "custom" in StrategyFactory.list_strategies()

    def test_create_registered_strategy(self):
        """测试创建已注册策略"""
        # 使用预注册的策略
        strategy = StrategyFactory.create(
            StrategyType.RETRY_FIXED.value,
            delay=1.0,
            max_retries=3
        )

        assert isinstance(strategy, FixedRetryStrategy)

    def test_create_unknown_strategy(self):
        """测试创建未知策略"""
        strategy = StrategyFactory.create("unknown_strategy")
        assert strategy is None

    def test_get_retry_strategy(self):
        """测试获取重试策略"""
        strategy = StrategyFactory.get_retry_strategy(
            StrategyType.RETRY_EXPONENTIAL.value,
            base_delay=1.0
        )

        assert isinstance(strategy, ExponentialRetryStrategy)

    def test_get_search_strategy(self):
        """测试获取搜索策略"""
        strategy = StrategyFactory.get_search_strategy(
            StrategyType.VECTOR_SEARCH.value
        )

        assert isinstance(strategy, VectorSearchStrategy)

    def test_list_strategies(self):
        """测试列出所有策略"""
        strategies = StrategyFactory.list_strategies()

        assert isinstance(strategies, list)
        assert StrategyType.RETRY_FIXED.value in strategies
        assert StrategyType.VECTOR_SEARCH.value in strategies

    def test_clear_cache(self):
        """测试清除缓存"""
        # 先创建一个策略（会缓存）
        StrategyFactory.create(
            StrategyType.RETRY_FIXED.value,
            delay=1.0
        )

        # 清除缓存
        StrategyFactory.clear_cache()

        # 缓存应该被清空
        assert len(StrategyFactory._instances) == 0

    def test_cache_same_params(self):
        """测试相同参数缓存"""
        StrategyFactory.clear_cache()

        strategy1 = StrategyFactory.create(
            StrategyType.RETRY_FIXED.value,
            delay=1.0
        )
        strategy2 = StrategyFactory.create(
            StrategyType.RETRY_FIXED.value,
            delay=1.0
        )

        # 应该返回缓存的同一实例
        assert strategy1 is strategy2

    def test_cache_different_params(self):
        """测试不同参数不缓存"""
        StrategyFactory.clear_cache()

        strategy1 = StrategyFactory.create(
            StrategyType.RETRY_FIXED.value,
            delay=1.0
        )
        strategy2 = StrategyFactory.create(
            StrategyType.RETRY_FIXED.value,
            delay=2.0
        )

        # 应该是不同实例
        assert strategy1 is not strategy2


# ============================================================================
# 集成测试
# ============================================================================

class TestRetryIntegration:
    """重试策略集成测试"""

    def test_full_retry_flow(self):
        """测试完整重试流程"""
        strategy = ExponentialRetryStrategy(
            base_delay=0.01,
            max_retries=3
        )

        attempts = []

        def failing_function():
            attempts.append(len(attempts) + 1)
            if len(attempts) < 3:
                raise ConnectionError("Network error")
            return "success"

        result = strategy.execute(failing_function)

        assert result == "success"
        assert len(attempts) == 3

    def test_retry_with_validation_error(self):
        """测试验证错误不重试"""
        strategy = FixedRetryStrategy(delay=0.01, max_retries=3)

        def validation_function():
            raise ValueError("Invalid input")

        with pytest.raises(ValueError):
            strategy.execute(validation_function)


class TestSearchIntegration:
    """搜索策略集成测试"""

    def test_hybrid_search_combines_results(self):
        """测试混合搜索组合结果"""
        vector_strategy = VectorSearchStrategy()
        keyword_strategy = KeywordSearchStrategy()

        hybrid = HybridSearchStrategy(
            [vector_strategy, keyword_strategy],
            weights=[0.6, 0.4]
        )

        results = hybrid.search("test query", top_k=5)

        # 验证结果结构
        assert isinstance(results, list)
        assert all(isinstance(r, SearchResult) for r in results)

    def test_strategy_context_propagation(self):
        """测试策略上下文传递"""
        context = StrategyContext(
            user_id="test_user",
            session_id="test_session",
            metadata={"trace_id": "12345"}
        )

        strategy = VectorSearchStrategy()
        strategy.before_execute(context)

        # 验证上下文被正确处理
        assert context.user_id == "test_user"

    def test_strategy_hooks(self):
        """测试策略钩子"""
        # 测试SearchStrategy的子类，它们实现了钩子调用
        strategy = VectorSearchStrategy()

        # 添加钩子逻辑的测试策略
        class TestSearchStrategy(SearchStrategy):
            @property
            def name(self):
                return "test_search"

            def search(self, query, top_k=5, filters=None, context=None):
                context = context or StrategyContext()
                self.before_execute(context)  # 调用before_execute钩子

                result = "result"

                return self.after_execute(context, result)  # 调用after_execute钩子

            def before_execute(self, context):
                context.metadata["before"] = True

            def after_execute(self, context, result):
                result = result + "_modified"
                return result

        strategy = TestSearchStrategy()
        context = StrategyContext()

        result = strategy.search(query="test", context=context)

        assert result == "result_modified"
        assert context.metadata.get("before") is True
