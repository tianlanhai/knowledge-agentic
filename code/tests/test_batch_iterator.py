# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：批量迭代器模块测试
内部逻辑：测试batch_iterator.py中的所有类和方法
测试覆盖范围：
    - BatchIterator类
    - LazyBatchIterator类
    - BatchProcessor类
测试类型：单元测试
"""

import pytest
from typing import List
from app.core.iterators.batch_iterator import BatchIterator, LazyBatchIterator, BatchProcessor


# ============================================================================
# BatchIterator 测试
# ============================================================================

class TestBatchIterator:
    """测试BatchIterator类"""

    def test_init_default_params(self):
        """测试默认参数初始化"""
        data = [1, 2, 3, 4, 5]
        iterator = BatchIterator(data)
        assert iterator.data == data
        assert iterator.batch_size == 100
        assert iterator.drop_incomplete is False
        assert iterator._index == 0

    def test_init_custom_params(self):
        """测试自定义参数初始化"""
        data = list(range(10))
        iterator = BatchIterator(data, batch_size=3, drop_incomplete=True)
        assert iterator.batch_size == 3
        assert iterator.drop_incomplete is True

    def test_iteration_single_batch(self):
        """测试单批迭代"""
        data = [1, 2, 3]
        iterator = BatchIterator(data, batch_size=10)
        batches = list(iterator)
        assert len(batches) == 1
        assert batches[0] == [1, 2, 3]

    def test_iteration_multiple_batches(self):
        """测试多批迭代"""
        data = list(range(10))
        iterator = BatchIterator(data, batch_size=3)
        batches = list(iterator)
        assert len(batches) == 4  # 3, 3, 3, 1
        assert batches[0] == [0, 1, 2]
        assert batches[1] == [3, 4, 5]
        assert batches[2] == [6, 7, 8]
        assert batches[3] == [9]

    def test_iteration_drop_incomplete(self):
        """测试丢弃不完整批次"""
        data = list(range(10))
        iterator = BatchIterator(data, batch_size=3, drop_incomplete=True)
        batches = list(iterator)
        assert len(batches) == 3  # 只保留完整的批次
        assert batches[0] == [0, 1, 2]
        assert batches[1] == [3, 4, 5]
        assert batches[2] == [6, 7, 8]
        # 9被丢弃

    def test_iteration_keeps_incomplete(self):
        """测试保留不完整批次"""
        data = list(range(10))
        iterator = BatchIterator(data, batch_size=3, drop_incomplete=False)
        batches = list(iterator)
        assert len(batches) == 4  # 包含不完整批次
        assert batches[3] == [9]

    def test_iteration_empty_data(self):
        """测试空数据迭代"""
        data: List[int] = []
        iterator = BatchIterator(data)
        batches = list(iterator)
        assert len(batches) == 0

    def test_iteration_with_restart(self):
        """测试重启迭代器"""
        data = list(range(10))
        iterator = BatchIterator(data, batch_size=3)

        # 第一次迭代
        batches1 = list(iterator)
        assert len(batches1) == 4

        # 重置后再次迭代
        iterator.reset()
        batches2 = list(iterator)
        assert len(batches2) == 4

    def test_len(self):
        """测试计算批次数"""
        data = list(range(10))
        iterator = BatchIterator(data, batch_size=3)
        assert len(iterator) == 4

    def test_len_drop_incomplete(self):
        """测试计算批次数（丢弃不完整）"""
        data = list(range(10))
        iterator = BatchIterator(data, batch_size=3, drop_incomplete=True)
        assert len(iterator) == 3

    def test_len_exact_division(self):
        """测试整除情况"""
        data = list(range(9))
        iterator = BatchIterator(data, batch_size=3)
        assert len(iterator) == 3  # 9/3=3, 完整批次

    def test_reset(self):
        """测试重置方法"""
        data = list(range(10))
        iterator = BatchIterator(data, batch_size=3)

        # 消费一些数据
        next(iterator)
        next(iterator)

        iterator.reset()
        assert iterator._index == 0

        # 可以重新迭代
        batches = list(iterator)
        assert len(batches) == 4


# ============================================================================
# LazyBatchIterator 测试
# ============================================================================

class TestLazyBatchIterator:
    """测试LazyBatchIterator类"""

    def test_init_default_params(self):
        """测试默认参数初始化"""
        def fetcher(offset, limit):
            return list(range(offset, offset + limit))

        iterator = LazyBatchIterator(fetcher)
        assert iterator.batch_size == 100
        assert iterator.max_batches is None
        assert iterator._batch_count == 0

    def test_init_custom_params(self):
        """测试自定义参数初始化"""
        def fetcher(offset, limit):
            return list(range(offset, offset + limit))

        iterator = LazyBatchIterator(fetcher, batch_size=10, max_batches=5)
        assert iterator.batch_size == 10
        assert iterator.max_batches == 5

    def test_iteration_with_data(self):
        """测试有数据的迭代"""
        def fetcher(offset, limit):
            total = 25
            end = min(offset + limit, total)
            return list(range(offset, end)) if offset < total else []

        iterator = LazyBatchIterator(fetcher, batch_size=10)
        batches = list(iterator)
        assert len(batches) == 3  # 10, 10, 5
        assert sum(len(b) for b in batches) == 25

    def test_iteration_with_max_batches(self):
        """测试最大批次数限制"""
        def fetcher(offset, limit):
            return list(range(offset, offset + limit))

        iterator = LazyBatchIterator(fetcher, batch_size=10, max_batches=2)
        batches = list(iterator)
        assert len(batches) == 2
        assert len(batches[0]) == 10
        assert len(batches[1]) == 10

    def test_iteration_empty_data(self):
        """测试空数据迭代"""
        def fetcher(offset, limit):
            return []

        iterator = LazyBatchIterator(fetcher)
        batches = list(iterator)
        assert len(batches) == 0

    def test_iteration_restart(self):
        """测试重启迭代"""
        def fetcher(offset, limit):
            return list(range(offset, offset + limit)) if offset < 20 else []

        iterator = LazyBatchIterator(fetcher, batch_size=10)

        # 第一次迭代
        batches1 = list(iterator)
        assert len(batches1) == 2

        # 创建新迭代器进行第二次迭代（LazyBatchIterator没有reset方法）
        iterator2 = LazyBatchIterator(fetcher, batch_size=10)
        batches2 = list(iterator2)
        assert len(batches2) == 2


# ============================================================================
# BatchProcessor 测试
# ============================================================================

class TestBatchProcessor:
    """测试BatchProcessor类"""

    def test_init(self):
        """测试初始化"""
        processor = BatchProcessor(batch_size=50)
        assert processor.batch_size == 50

    def test_process_single_batch(self):
        """测试单批处理"""
        data = list(range(5))
        processor = BatchProcessor(batch_size=10)

        def doubler(items):
            return [x * 2 for x in items]

        results = processor.process(data, doubler)
        assert len(results) == 1
        assert results[0] == [0, 2, 4, 6, 8]

    def test_process_multiple_batches(self):
        """测试多批处理"""
        data = list(range(15))
        processor = BatchProcessor(batch_size=5)

        def doubler(items):
            return [x * 2 for x in items]

        results = processor.process(data, doubler)
        assert len(results) == 3

    def test_process_with_progress_callback(self):
        """测试带进度回调的处理"""
        data = list(range(20))
        processor = BatchProcessor(batch_size=5)

        progress_calls = []

        def progress_callback(current, total):
            progress_calls.append((current, total))

        def identity(items):
            return items

        results = processor.process(data, identity, progress_callback)
        # 进度回调在每批处理后调用
        # 由于results[0].__len__()获取第一个结果的长度，每批返回5个元素
        # 所以应该是：5, 10, 15, 20
        assert len(progress_calls) == 4
        # 第一批：5个
        assert progress_calls[0][0] == 5
        assert progress_calls[0][1] == 20

    def test_process_empty_data(self):
        """测试处理空数据"""
        data: List[int] = []
        processor = BatchProcessor()

        def identity(items):
            return items

        results = processor.process(data, identity)
        assert results == []

    def test_process_exception_handling(self):
        """测试处理过程中的异常"""
        data = list(range(10))
        processor = BatchProcessor(batch_size=3)

        def faulty_processor(items):
            if 5 in items:
                raise ValueError("Test error")
            return items

        # 应该抛出异常
        with pytest.raises(ValueError):
            processor.process(data, faulty_processor)

    def test_process_collects_all_results(self):
        """测试收集所有处理结果"""
        data = list(range(10))
        processor = BatchProcessor(batch_size=3)

        def stringify(items):
            return [str(x) for x in items]

        results = processor.process(data, stringify)
        assert len(results) == 4  # 3, 3, 3, 1
        all_values = []
        for batch in results:
            all_values.extend(batch)
        assert len(all_values) == 10


# ============================================================================
# 边界条件测试
# ============================================================================

class TestBatchIteratorEdgeCases:
    """测试BatchIterator边界条件"""

    def test_batch_size_equals_data_length(self):
        """测试批大小等于数据长度"""
        data = [1, 2, 3]
        iterator = BatchIterator(data, batch_size=3)
        batches = list(iterator)
        assert len(batches) == 1
        assert batches[0] == [1, 2, 3]

    def test_batch_size_larger_than_data(self):
        """测试批大小大于数据长度"""
        data = [1, 2]
        iterator = BatchIterator(data, batch_size=10)
        batches = list(iterator)
        assert len(batches) == 1
        assert batches[0] == [1, 2]

    def test_batch_size_one(self):
        """测试批大小为1"""
        data = [1, 2, 3]
        iterator = BatchIterator(data, batch_size=1)
        batches = list(iterator)
        assert len(batches) == 3
        assert batches[0] == [1]
        assert batches[1] == [2]
        assert batches[2] == [3]

    def test_large_data(self):
        """测试大数据集"""
        data = list(range(1000))
        iterator = BatchIterator(data, batch_size=100)
        batches = list(iterator)
        assert len(batches) == 10
        for batch in batches:
            assert len(batch) == 100


class TestLazyBatchIteratorEdgeCases:
    """测试LazyBatchIterator边界条件"""

    def test_fetcher_returns_empty(self):
        """测试fetcher返回空列表"""
        def empty_fetcher(offset, limit):
            return []

        iterator = LazyBatchIterator(empty_fetcher)
        batches = list(iterator)
        assert len(batches) == 0

    def test_max_batches_zero(self):
        """测试max_batches为0"""
        def fetcher(offset, limit):
            return [1, 2, 3]

        iterator = LazyBatchIterator(fetcher, max_batches=0)
        batches = list(iterator)
        assert len(batches) == 0

    def test_batch_size_one(self):
        """测试批大小为1"""
        def fetcher(offset, limit):
            return [offset] if offset < 5 else []

        iterator = LazyBatchIterator(fetcher, batch_size=1)
        batches = list(iterator)
        assert len(batches) == 5
        assert batches == [[0], [1], [2], [3], [4]]
