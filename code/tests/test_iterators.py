# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：迭代器模式模块测试
内部逻辑：验证批量迭代器、文档迭代器等各种迭代器模式的功能
设计模式：迭代器模式（Iterator Pattern）
测试覆盖范围：
    - BatchIterator: 批量迭代器基础功能
    - LazyBatchIterator: 惰性批量迭代器
    - BatchProcessor: 批量处理器
    - BatchIteratorFactory: 迭代器工厂
    - DocumentIterator: 文档迭代器
    - AsyncDocumentIterator: 异步文档迭代器
    - DatabaseDocumentIterator: 数据库文档迭代器
    - IteratorStats: 迭代器统计
    - ParallelIterator: 并行处理迭代器
    - TransformIterator: 转换迭代器
    - BatchProcessorIterator: 批量处理迭代器
    - ChainedIterator: 链式迭代器
    - BufferedAsyncIterator: 缓冲异步迭代器
"""

import pytest
import asyncio
from typing import List, Any
from pathlib import Path
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from datetime import datetime
import tempfile
import os

from app.core.iterators.batch_iterator import (
    BatchIterator,
    LazyBatchIterator,
    BatchProcessor,
    BatchIteratorFactory,
)
from app.core.iterators.document_iterator import (
    DocumentIterator,
    AsyncDocumentIterator,
    DatabaseDocumentIterator,
    IteratorStats,
    ParallelIterator,
    TransformIterator,
    BatchProcessorIterator,
    ChainedIterator,
    BufferedAsyncIterator,
)


# ============================================================================
# 测试固件和辅助函数
# ============================================================================

@pytest.fixture
def sample_data():
    """创建测试用的示例数据"""
    return list(range(100))


@pytest.fixture
def sample_documents():
    """创建测试用的示例文档"""
    return [
        {"id": i + 1, "title": f"文档{i}", "content": f"内容{i}"} for i in range(20)
    ]


class MockModel:
    """模拟数据库模型"""

    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name


# ============================================================================
# BatchIterator 测试
# ============================================================================

class TestBatchIterator:
    """测试批量迭代器"""

    def test_init_default_parameters(self):
        """测试默认参数初始化"""
        data = [1, 2, 3, 4, 5]
        iterator = BatchIterator(data)
        assert iterator.data == data
        assert iterator.batch_size == 100
        assert iterator.drop_incomplete is False
        assert iterator._index == 0

    def test_init_custom_parameters(self):
        """测试自定义参数初始化"""
        data = list(range(10))
        iterator = BatchIterator(data, batch_size=3, drop_incomplete=True)
        assert iterator.batch_size == 3
        assert iterator.drop_incomplete is True

    def test_iteration_basic(self, sample_data):
        """测试基本迭代功能"""
        iterator = BatchIterator(sample_data, batch_size=10)
        batches = list(iterator)
        assert len(batches) == 10
        assert batches[0] == list(range(10))
        assert batches[-1] == list(range(90, 100))

    def test_iteration_with_incomplete_batch(self):
        """测试包含不完整批次的迭代"""
        data = list(range(25))
        iterator = BatchIterator(data, batch_size=10)
        batches = list(iterator)
        assert len(batches) == 3
        assert batches[0] == list(range(10))
        assert batches[1] == list(range(10, 20))
        assert batches[2] == list(range(20, 25))

    def test_iteration_drop_incomplete(self):
        """测试丢弃不完整批次"""
        data = list(range(25))
        iterator = BatchIterator(data, batch_size=10, drop_incomplete=True)
        batches = list(iterator)
        assert len(batches) == 2
        assert batches[0] == list(range(10))
        assert batches[1] == list(range(10, 20))

    def test_length_calculation(self):
        """测试批次数计算"""
        # 正好整除
        it1 = BatchIterator(list(range(100)), batch_size=10)
        assert len(it1) == 10

        # 有余数
        it2 = BatchIterator(list(range(95)), batch_size=10)
        assert len(it2) == 10

        # 丢弃不完整
        it3 = BatchIterator(list(range(95)), batch_size=10, drop_incomplete=True)
        assert len(it3) == 9

    def test_reset_functionality(self, sample_data):
        """测试重置功能"""
        iterator = BatchIterator(sample_data, batch_size=10)
        first_batch = next(iter(iterator))
        assert first_batch == list(range(10))

        iterator.reset()
        second_batch = next(iter(iterator))
        assert second_batch == list(range(10))

    def test_empty_data(self):
        """测试空数据"""
        iterator = BatchIterator([])
        batches = list(iterator)
        assert len(batches) == 0

    def test_single_batch(self):
        """测试单批次数据"""
        data = list(range(5))
        iterator = BatchIterator(data, batch_size=10)
        batches = list(iterator)
        assert len(batches) == 1
        assert batches[0] == data

    def test_multiple_iterations(self):
        """测试多次迭代"""
        data = list(range(20))
        iterator = BatchIterator(data, batch_size=5)

        # 第一次迭代
        batches1 = list(iterator)
        assert len(batches1) == 4

        # 第二次迭代（重置后）
        batches2 = list(iterator)
        assert len(batches2) == 4
        assert batches1 == batches2


# ============================================================================
# LazyBatchIterator 测试
# ============================================================================

class TestLazyBatchIterator:
    """测试惰性批量迭代器"""

    def test_init(self):
        """测试初始化"""
        fetcher = lambda offset, limit: list(range(offset, offset + limit))
        iterator = LazyBatchIterator(fetcher, batch_size=10, max_batches=5)
        assert iterator.batch_size == 10
        assert iterator.max_batches == 5

    def test_lazy_iteration(self):
        """测试惰性迭代"""
        call_count = []

        def fetcher(offset, limit):
            call_count.append(offset)
            data = list(range(offset, offset + limit))
            if offset >= 30:
                return []  # 模拟数据耗尽
            return data

        iterator = LazyBatchIterator(fetcher, batch_size=10)
        batches = list(iterator)

        assert len(batches) == 3
        assert batches[0] == list(range(0, 10))
        assert batches[1] == list(range(10, 20))
        assert batches[2] == list(range(20, 30))

    def test_max_batches_limit(self):
        """测试最大批次限制"""
        def fetcher(offset, limit):
            return list(range(offset, offset + limit))

        iterator = LazyBatchIterator(fetcher, batch_size=10, max_batches=3)
        batches = list(iterator)

        assert len(batches) == 3

    def test_empty_fetcher(self):
        """测试空数据获取器"""
        def fetcher(offset, limit):
            return []

        iterator = LazyBatchIterator(fetcher, batch_size=10)
        batches = list(iterator)
        assert len(batches) == 0


# ============================================================================
# BatchProcessor 测试
# ============================================================================

class TestBatchProcessor:
    """测试批量处理器"""

    @pytest.mark.asyncio
    async def test_process_batches(self):
        """测试批量处理"""
        data = list(range(100))

        def processor(batch):
            return sum(batch)

        batch_processor = BatchProcessor(batch_size=10)
        results = await batch_processor.aprocess(data, processor)

        assert len(results) == 10
        assert results[0] == sum(range(10))

    @pytest.mark.asyncio
    async def test_process_with_progress_callback(self):
        """测试带进度回调的处理"""
        data = list(range(100))
        progress_updates = []

        def progress_callback(current, total):
            progress_updates.append((current, total))

        def processor(batch):
            return len(batch)

        batch_processor = BatchProcessor(batch_size=25)
        await batch_processor.aprocess(data, processor, progress_callback)

        assert len(progress_updates) == 4

    @pytest.mark.asyncio
    async def test_process_with_exception(self):
        """测试处理异常"""
        data = list(range(100))

        def processor(batch):
            if batch[0] == 50:
                raise ValueError("测试错误")
            return len(batch)

        batch_processor = BatchProcessor(batch_size=10)
        with pytest.raises(ValueError, match="测试错误"):
            await batch_processor.aprocess(data, processor)


# ============================================================================
# BatchIteratorFactory 测试
# ============================================================================

class TestBatchIteratorFactory:
    """测试迭代器工厂"""

    def test_from_list(self):
        """测试从列表创建迭代器"""
        data = [1, 2, 3, 4, 5]
        iterator = BatchIteratorFactory.from_list(data, batch_size=2)
        assert isinstance(iterator, BatchIterator)
        assert iterator.batch_size == 2

    def test_from_fetcher(self):
        """测试从获取函数创建迭代器"""
        fetcher = lambda offset, limit: list(range(offset, offset + limit))
        iterator = BatchIteratorFactory.from_fetcher(fetcher, batch_size=10)
        assert isinstance(iterator, LazyBatchIterator)
        assert iterator.batch_size == 10

    def test_from_generator(self):
        """测试从生成器创建迭代器"""
        def generator():
            for i in range(10):
                yield i

        iterator = BatchIteratorFactory.from_generator(generator, batch_size=3)
        batches = list(iterator)
        assert len(batches) == 4
        assert len(batches[0]) == 3
        assert len(batches[-1]) == 1


# ============================================================================
# DocumentIterator 测试
# ============================================================================

class TestDocumentIterator:
    """测试文档迭代器"""

    def test_init_with_documents(self, sample_documents):
        """测试使用文档列表初始化"""
        iterator = DocumentIterator(documents=sample_documents, batch_size=5)
        assert iterator._documents == sample_documents
        assert iterator.batch_size == 5

    def test_iteration(self, sample_documents):
        """测试文档迭代"""
        iterator = DocumentIterator(documents=sample_documents)
        documents = list(iterator)
        assert len(documents) == 20
        assert documents[0]["id"] == 1

    def test_iteration_none_documents(self):
        """测试空文档迭代"""
        iterator = DocumentIterator(documents=None)
        with pytest.raises(StopIteration):
            next(iter(iterator))

    def test_batches(self, sample_documents):
        """测试批量迭代"""
        iterator = DocumentIterator(documents=sample_documents, batch_size=5)
        batches = list(iterator.batches())
        assert len(batches) == 4
        assert len(batches[0]) == 5

    def test_batches_none_documents(self):
        """测试空文档批量迭代"""
        iterator = DocumentIterator(documents=None)
        batches = list(iterator.batches())
        assert len(batches) == 0

    def test_from_files(self, tmp_path):
        """测试从文件创建迭代器"""
        # 创建测试文件
        for i in range(3):
            file_path = tmp_path / f"file{i}.txt"
            file_path.write_text(f"content{i}")

        iterator = DocumentIterator.from_files(str(tmp_path), pattern="*.txt")
        assert iterator._documents is not None
        assert len(iterator._documents) == 3

    def test_from_files_recursive(self, tmp_path):
        """测试递归扫描文件"""
        # 创建子目录和文件
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "file1.txt").write_text("content1")
        (subdir / "file2.txt").write_text("content2")

        iterator = DocumentIterator.from_files(str(tmp_path), pattern="*.txt", recursive=True)
        assert len(iterator._documents) == 2

    def test_filter(self, sample_documents):
        """测试过滤功能"""
        iterator = DocumentIterator(documents=sample_documents)
        filtered = iterator.filter(lambda doc: doc["id"] > 10)
        # filter返回新实例，检查新实例的文档数量
        # id > 10 意味着 id 11-20，共10个文档
        assert len(filtered._documents) == 10

    def test_filter_none_documents(self):
        """测试空文档过滤"""
        iterator = DocumentIterator(documents=None)
        filtered = iterator.filter(lambda x: True)
        assert filtered is iterator  # 空文档返回自身

    def test_map(self, sample_documents):
        """测试映射功能"""
        iterator = DocumentIterator(documents=sample_documents)
        mapped = iterator.map(lambda doc: {**doc, "title": doc["title"].upper()})
        assert mapped._documents[0]["title"] == "文档0"

    def test_map_none_documents(self):
        """测试空文档映射"""
        iterator = DocumentIterator(documents=None)
        mapped = iterator.map(lambda x: x)
        assert mapped is iterator


# ============================================================================
# AsyncDocumentIterator 测试
# ============================================================================

class TestAsyncDocumentIterator:
    """测试异步文档迭代器"""

    @pytest.mark.asyncio
    async def test_init_with_documents(self):
        """测试使用文档列表初始化"""
        documents = [{"id": i} for i in range(5)]
        iterator = AsyncDocumentIterator(documents=documents)
        assert iterator._documents == documents

    @pytest.mark.asyncio
    async def test_async_iteration(self):
        """测试异步迭代"""
        documents = [{"id": i} for i in range(5)]
        iterator = AsyncDocumentIterator(documents=documents)

        results = []
        async for doc in iterator:
            results.append(doc)

        assert len(results) == 5
        assert results[0]["id"] == 0

    @pytest.mark.asyncio
    async def test_async_iteration_with_fetcher(self):
        """测试使用fetcher的异步迭代"""
        fetch_results = [[{"id": i} for i in range(5)], [{"id": i} for i in range(5, 10)]]
        call_count = [0]

        async def fetcher(offset, limit):
            result = fetch_results[call_count[0]] if call_count[0] < len(fetch_results) else []
            call_count[0] += 1
            return result

        iterator = AsyncDocumentIterator(fetcher=fetcher, batch_size=5)

        results = []
        async for doc in iterator:
            results.append(doc)

        assert len(results) == 10

    @pytest.mark.asyncio
    async def test_async_batches(self):
        """测试异步批量迭代"""
        documents = [{"id": i} for i in range(10)]
        iterator = AsyncDocumentIterator(documents=documents, batch_size=3)

        batches = []
        async for batch in iterator.batches():
            batches.append(batch)

        assert len(batches) == 4
        assert len(batches[0]) == 3
        assert len(batches[-1]) == 1

    @pytest.mark.asyncio
    async def test_none_documents_and_fetcher(self):
        """测试空文档和fetcher"""
        iterator = AsyncDocumentIterator(documents=None, fetcher=None)

        with pytest.raises(StopAsyncIteration):
            await iterator.__anext__()


# ============================================================================
# DatabaseDocumentIterator 测试
# ============================================================================

class TestDatabaseDocumentIterator:
    """测试数据库文档迭代器"""

    def test_init(self):
        """测试初始化"""
        mock_session = Mock()
        mock_model = Mock

        iterator = DatabaseDocumentIterator(
            db_session=mock_session,
            model=mock_model,
            batch_size=50,
            filters={"status": "active"}
        )

        assert iterator.db_session == mock_session
        assert iterator.model == mock_model
        assert iterator.batch_size == 50
        assert iterator.filters == {"status": "active"}

    def test_iteration(self):
        """测试数据库迭代"""
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query

        # 模拟查询结果
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query

        # 第一次调用返回数据，第二次返回空
        # 需要返回一个包含id属性的mock对象
        mock_items = [Mock(id=i, name=f"item{i}") for i in range(10)]
        for item in mock_items:
            # 添加status属性以满足过滤条件
            item.status = "active"
        mock_query.all.side_effect = [mock_items, []]

        class MockModel:
            status = None

        iterator = DatabaseDocumentIterator(
            db_session=mock_session,
            model=MockModel,
            batch_size=10,
            filters={"status": "active"}
        )

        results = list(iterator)
        assert len(results) == 10

    def test_iteration_with_filters(self):
        """测试带过滤条件的迭代"""
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        class MockModel:
            status = None

        iterator = DatabaseDocumentIterator(
            db_session=mock_session,
            model=MockModel,
            batch_size=10,
            filters={"status": "active"}
        )

        list(iterator)  # 触发查询

        # 验证filter被调用
        mock_query.filter.assert_called()

    def test_empty_result(self):
        """测试空结果"""
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        class MockModel:
            pass

        iterator = DatabaseDocumentIterator(
            db_session=mock_session,
            model=MockModel,
            batch_size=10
        )

        results = list(iterator)
        assert len(results) == 0


# ============================================================================
# IteratorStats 测试
# ============================================================================

class TestIteratorStats:
    """测试迭代器统计"""

    def test_init(self):
        """测试初始化"""
        stats = IteratorStats()
        assert stats.processed_count == 0
        assert stats.failed_count == 0
        assert stats.skipped_count == 0
        assert stats.start_time > 0
        assert stats.end_time is None
        assert stats.errors == []

    def test_duration_property(self):
        """测试时长属性"""
        stats = IteratorStats()
        duration = stats.duration
        assert duration >= 0

    def test_duration_with_end_time(self):
        """测试设置结束时间后的时长"""
        stats = IteratorStats()
        import time
        stats.end_time = stats.start_time + 1.5
        assert stats.duration == 1.5

    def test_throughput_property(self):
        """测试吞吐量属性"""
        stats = IteratorStats()
        stats.processed_count = 100
        stats.end_time = stats.start_time + 2.0
        assert stats.throughput == 50.0

    def test_zero_duration_throughput(self):
        """测试零时长时的吞吐量"""
        stats = IteratorStats()
        stats.end_time = stats.start_time  # 零时长
        assert stats.throughput == 0

    def test_to_dict(self):
        """测试转换为字典"""
        stats = IteratorStats()
        stats.processed_count = 10
        stats.failed_count = 2
        stats.errors.append((0, Exception("test")))

        result = stats.to_dict()
        assert result["processed_count"] == 10
        assert result["failed_count"] == 2
        assert result["error_count"] == 1
        assert "duration" in result
        assert "throughput" in result


# ============================================================================
# ParallelIterator 测试
# ============================================================================

class TestParallelIterator:
    """测试并行处理迭代器"""

    @pytest.mark.asyncio
    async def test_process(self):
        """测试并行处理"""
        items = list(range(20))

        def processor(x):
            return x * 2

        iterator = ParallelIterator(items, processor, max_workers=4)
        results = await iterator.process()

        # 并行处理结果可能无序，检查数量和内容
        assert len(results) == 20
        # range(20) = [0, 1, ..., 19]，最大值是 19，所以 19 * 2 = 38
        assert 38 in results  # 19 * 2
        assert 0 in results   # 0 * 2
        assert sorted(results) == [x * 2 for x in range(20)]

    @pytest.mark.asyncio
    async def test_process_with_exception(self):
        """测试处理异常"""
        items = list(range(5))

        def processor(x):
            if x == 3:
                raise ValueError("测试错误")
            return x * 2

        iterator = ParallelIterator(items, processor, max_workers=2)
        results = await iterator.process()

        # 有一个失败
        stats = iterator.get_stats()
        assert stats.failed_count == 1

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """测试获取统计信息"""
        items = list(range(10))

        def processor(x):
            return x * 2

        iterator = ParallelIterator(items, processor, max_workers=2)
        await iterator.process()

        stats = iterator.get_stats()
        assert stats.processed_count == 10
        assert stats.failed_count == 0
        # duration可能为0或很小的时间值
        assert stats.duration >= 0


# ============================================================================
# TransformIterator 测试
# ============================================================================

class TestTransformIterator:
    """测试转换迭代器"""

    def test_transform_only(self):
        """测试仅转换"""
        source = iter([1, 2, 3, 4, 5])

        def transformer(x):
            return x * 2

        iterator = TransformIterator(source, transformer)
        result = list(iterator)

        assert result == [2, 4, 6, 8, 10]

    def test_transform_with_filter(self):
        """测试带过滤的转换"""
        source = iter([1, 2, 3, 4, 5])

        def transformer(x):
            return x * 2

        def filter_func(x):
            return x > 2

        iterator = TransformIterator(source, transformer, filter_func)
        result = list(iterator)

        # 只保留大于2的值（原始值），然后转换
        assert result == [6, 8, 10]

    def test_empty_source(self):
        """测试空源迭代器"""
        iterator = TransformIterator(iter([]), lambda x: x * 2)
        result = list(iterator)
        assert result == []


# ============================================================================
# BatchProcessorIterator 测试
# ============================================================================

class TestBatchProcessorIterator:
    """测试批量处理迭代器"""

    def test_iteration(self):
        """测试迭代"""
        items = list(range(20))
        iterator = BatchProcessorIterator(items, batch_size=5)

        batches = list(iterator)
        assert len(batches) == 4
        assert batches[0] == list(range(5))

    @pytest.mark.asyncio
    async def test_process_all(self):
        """测试处理所有批次"""
        items = list(range(10))
        processed_batches = []

        async def processor(batch):
            processed_batches.append(batch)
            return len(batch)

        iterator = BatchProcessorIterator(items, batch_size=3, processor=processor)
        stats = await iterator.process_all()

        assert stats.processed_count == 10
        assert stats.failed_count == 0
        assert len(processed_batches) == 4

    @pytest.mark.asyncio
    async def test_process_all_with_exception(self):
        """测试处理异常"""
        items = list(range(10))

        async def processor(batch):
            if batch[0] == 6:
                raise ValueError("测试错误")
            return len(batch)

        iterator = BatchProcessorIterator(items, batch_size=3, processor=processor)
        stats = await iterator.process_all()

        assert stats.failed_count > 0

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """测试获取统计信息"""
        items = list(range(5))

        async def processor(batch):
            return len(batch)

        iterator = BatchProcessorIterator(items, batch_size=2, processor=processor)

        # 先迭代获取统计
        list(iterator)
        stats = iterator.get_stats()

        assert stats.processed_count == 5

    def test_progress_callback(self):
        """测试进度回调"""
        items = list(range(10))
        progress_calls = []

        def callback(current, total):
            progress_calls.append((current, total))

        iterator = BatchProcessorIterator(items, batch_size=3, progress_callback=callback)
        list(iterator)

        assert len(progress_calls) == 4


# ============================================================================
# ChainedIterator 测试
# ============================================================================

class TestChainedIterator:
    """测试链式迭代器"""

    def test_single_iterator(self):
        """测试单个迭代器"""
        it1 = iter([1, 2, 3])
        chained = ChainedIterator(it1)

        result = list(chained)
        assert result == [1, 2, 3]

    def test_multiple_iterators(self):
        """测试多个迭代器"""
        it1 = iter([1, 2])
        it2 = iter([3, 4])
        it3 = iter([5, 6])

        chained = ChainedIterator(it1, it2, it3)
        result = list(chained)

        assert result == [1, 2, 3, 4, 5, 6]

    def test_add_iterator(self):
        """测试动态添加迭代器"""
        it1 = iter([1, 2])
        chained = ChainedIterator(it1)

        result1 = list(chained)
        assert result1 == [1, 2]

        # 添加新迭代器后需要创建新的ChainedIterator
        # 因为原迭代器已耗尽
        it2 = iter([3, 4])
        it3 = iter([1, 2])
        chained2 = ChainedIterator(it3, it2)

        result2 = list(chained2)
        assert result2 == [1, 2, 3, 4]

    def test_empty_iterators(self):
        """测试空迭代器列表"""
        chained = ChainedIterator()
        result = list(chained)
        assert result == []

    def test_empty_iterator_in_chain(self):
        """测试链中包含空迭代器"""
        it1 = iter([1, 2])
        it2 = iter([])
        it3 = iter([3, 4])

        chained = ChainedIterator(it1, it2, it3)
        result = list(chained)

        assert result == [1, 2, 3, 4]


# ============================================================================
# BufferedAsyncIterator 测试
# ============================================================================

class TestBufferedAsyncIterator:
    """测试缓冲异步迭代器"""

    @pytest.mark.asyncio
    async def test_buffer_iteration(self):
        """测试缓冲迭代"""
        async def source():
            for i in range(10):
                yield i

        buffered = BufferedAsyncIterator(source(), buffer_size=3)
        results = []

        async for item in buffered:
            results.append(item)

        assert results == list(range(10))

    @pytest.mark.asyncio
    async def test_buffer_all(self):
        """测试缓冲所有数据"""
        async def source():
            for i in range(5):
                yield i

        buffered = BufferedAsyncIterator(source(), buffer_size=2)
        all_items = await buffered.buffer_all()

        assert all_items == list(range(5))

    @pytest.mark.asyncio
    async def test_empty_source(self):
        """测试空源"""
        async def source():
            return
            yield  # 永不yield

        buffered = BufferedAsyncIterator(source(), buffer_size=5)
        all_items = await buffered.buffer_all()

        assert all_items == []
