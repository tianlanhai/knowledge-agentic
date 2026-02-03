# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：文档迭代器模块
内部逻辑：实现文档的流式读取和迭代
设计模式：迭代器模式（Iterator Pattern）
设计原则：SOLID - 单一职责原则
"""

from typing import List, Iterator, Optional, AsyncIterator, Any, Callable, TypeVar, Generic
from pathlib import Path
from loguru import logger
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
import time

from app.core.iterators.batch_iterator import BatchIterator, LazyBatchIterator

# 内部变量：泛型类型
T = TypeVar('T')
R = TypeVar('R')


class DocumentIterator:
    """
    类级注释：文档迭代器
    设计模式：迭代器模式（Iterator Pattern）
    职责：逐个或批量读取文档

    设计优势：
        - 支持多种数据源
        - 内存效率高
        - 统一的迭代接口
    """

    def __init__(
        self,
        documents: Optional[List[Any]] = None,
        file_path: Optional[str] = None,
        batch_size: int = 10
    ):
        """
        函数级注释：初始化文档迭代器
        参数：
            documents: 文档列表
            file_path: 文件路径（从文件读取）
            batch_size: 批处理大小
        """
        self.batch_size = batch_size
        self._documents = documents
        self._file_path = file_path
        self._index = 0

    def __iter__(self) -> Iterator[Any]:
        """
        函数级注释：迭代器接口实现
        """
        self._index = 0
        return self

    def __next__(self) -> Any:
        """
        函数级注释：获取下一个文档
        返回值：文档对象
        异常：StopIteration - 没有更多文档
        """
        if self._documents is None:
            raise StopIteration

        if self._index >= len(self._documents):
            raise StopIteration

        doc = self._documents[self._index]
        self._index += 1
        return doc

    def batches(self) -> Iterator[List[Any]]:
        """
        函数级注释：返回批量迭代器
        返回值：批量文档迭代器
        """
        if self._documents is None:
            return iter([])

        return iter(BatchIterator(self._documents, self.batch_size))

    @classmethod
    def from_files(
        cls,
        directory: str,
        pattern: str = "*",
        recursive: bool = False
    ) -> "DocumentIterator":
        """
        函数级注释：从目录创建文档迭代器
        内部逻辑：扫描目录 -> 匹配文件 -> 创建迭代器
        参数：
            directory: 目录路径
            pattern: 文件匹配模式
            recursive: 是否递归扫描
        返回值：DocumentIterator实例
        """
        path = Path(directory)
        if recursive:
            files = list(path.rglob(pattern))
        else:
            files = list(path.glob(pattern))

        # 内部逻辑：过滤出文件
        file_paths = [str(f) for f in files if f.is_file()]

        logger.info(f"从目录加载文档: {directory}, 文件数: {len(file_paths)}")

        return cls(documents=file_paths)

    def filter(self, predicate: callable) -> "DocumentIterator":
        """
        函数级注释：过滤文档
        参数：
            predicate: 谓词函数
        返回值：过滤后的DocumentIterator
        """
        if self._documents is None:
            return self

        filtered = [doc for doc in self._documents if predicate(doc)]
        return DocumentIterator(documents=filtered, batch_size=self.batch_size)

    def map(self, mapper: callable) -> "DocumentIterator":
        """
        函数级注释：映射文档
        参数：
            mapper: 映射函数
        返回值：映射后的DocumentIterator
        """
        if self._documents is None:
            return self

        mapped = [mapper(doc) for doc in self._documents]
        return DocumentIterator(documents=mapped, batch_size=self.batch_size)


class AsyncDocumentIterator:
    """
    类级注释：异步文档迭代器
    设计模式：迭代器模式 + 异步模式
    职责：异步逐个或批量读取文档

    设计优势：
        - 支持异步IO
        - 不阻塞事件循环
        - 适合网络数据源
    """

    def __init__(
        self,
        documents: Optional[List[Any]] = None,
        fetcher: Optional[callable] = None,
        batch_size: int = 10
    ):
        """
        函数级注释：初始化异步文档迭代器
        参数：
            documents: 文档列表
            fetcher: 异步数据获取函数
            batch_size: 批处理大小
        """
        self.batch_size = batch_size
        self._documents = documents
        self._fetcher = fetcher
        self._index = 0

    def __aiter__(self) -> AsyncIterator[Any]:
        """
        函数级注释：异步迭代器接口实现
        """
        self._index = 0
        return self

    async def __anext__(self) -> Any:
        """
        函数级注释：获取下一个文档（异步）
        返回值：文档对象
        异常：StopAsyncIteration - 没有更多文档
        """
        if self._documents is None and self._fetcher is None:
            raise StopAsyncIteration

        # 内部逻辑：使用fetcher获取数据
        if self._fetcher is not None:
            if self._documents is None:
                self._documents = await self._fetcher(0, self.batch_size)
                self._index = 0

            if self._index >= len(self._documents):
                # 内部逻辑：获取下一批
                next_batch = await self._fetcher(
                    len(self._documents),
                    self.batch_size
                )
                if not next_batch:
                    raise StopAsyncIteration
                self._documents.extend(next_batch)

        if self._index >= len(self._documents):
            raise StopAsyncIteration

        doc = self._documents[self._index]
        self._index += 1
        return doc

    async def batches(self) -> AsyncIterator[List[Any]]:
        """
        函数级注释：返回异步批量迭代器
        返回值：批量文档异步迭代器
        """
        while True:
            batch = []
            try:
                for _ in range(self.batch_size):
                    doc = await self.__anext__()
                    batch.append(doc)
            except StopAsyncIteration:
                pass

            if not batch:
                break

            yield batch


class DatabaseDocumentIterator:
    """
    类级注释：数据库文档迭代器
    设计模式：迭代器模式 + 惰性加载
    职责：从数据库分页读取文档

    设计优势：
        - 惰性加载，按需查询
        - 支持大数据集
        - 内存效率高
    """

    def __init__(
        self,
        db_session: Any,
        model: Any,
        batch_size: int = 100,
        filters: Optional[dict] = None
    ):
        """
        函数级注释：初始化数据库文档迭代器
        参数：
            db_session: 数据库会话
            model: 数据模型
            batch_size: 批处理大小
            filters: 查询过滤条件
        """
        self.db_session = db_session
        self.model = model
        self.batch_size = batch_size
        self.filters = filters or {}
        self._offset = 0
        self._current_batch: List[Any] = []
        self._batch_index = 0

    def __iter__(self) -> Iterator[Any]:
        """
        函数级注释：迭代器接口实现
        """
        self._offset = 0
        self._current_batch = []
        self._batch_index = 0
        return self

    def __next__(self) -> Any:
        """
        函数级注释：获取下一个文档
        返回值：文档对象
        """
        # 内部逻辑：需要加载新批次
        if self._batch_index >= len(self._current_batch):
            self._current_batch = self._fetch_batch()
            self._batch_index = 0

            # 内部逻辑：没有更多数据
            if not self._current_batch:
                raise StopIteration

        doc = self._current_batch[self._batch_index]
        self._batch_index += 1
        return doc

    def _fetch_batch(self) -> List[Any]:
        """
        私有函数级注释：从数据库获取一批数据
        返回值：文档列表
        """
        try:
            # 内部逻辑：构建查询
            query = self.db_session.query(self.model)

            # 内部逻辑：应用过滤条件
            for key, value in self.filters.items():
                query = query.filter(getattr(self.model, key) == value)

            # 内部逻辑：分页查询
            results = query.offset(self._offset).limit(self.batch_size).all()
            self._offset += self.batch_size

            logger.debug(f"从数据库获取批次: offset={self._offset - self.batch_size}, count={len(results)}")

            return results

        except Exception as e:
            logger.error(f"数据库查询失败: {str(e)}")
            return []


# ==================== 扩展迭代器 ====================

@dataclass
class IteratorStats:
    """
    类级注释：迭代器统计数据类
    内部逻辑：记录迭代过程的统计信息
    """
    # 属性：已处理数量
    processed_count: int = 0
    # 属性：失败数量
    failed_count: int = 0
    # 属性：跳过数量
    skipped_count: int = 0
    # 属性：开始时间
    start_time: float = field(default_factory=time.time)
    # 属性：结束时间
    end_time: Optional[float] = None
    # 属性：错误列表
    errors: List[tuple[int, Exception]] = field(default_factory=list)

    @property
    def duration(self) -> float:
        """获取处理时长"""
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def throughput(self) -> float:
        """获取吞吐量（条/秒）"""
        dur = self.duration
        return self.processed_count / dur if dur > 0 else 0

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "processed_count": self.processed_count,
            "failed_count": self.failed_count,
            "skipped_count": self.skipped_count,
            "duration": self.duration,
            "throughput": self.throughput,
            "error_count": len(self.errors),
        }


class ParallelIterator(Generic[T, R]):
    """
    类级注释：并行处理迭代器
    内部逻辑：使用线程池并行处理文档
    设计模式：迭代器模式 + 并行模式
    职责：加速批量文档处理

    使用场景：
        - CPU 密集型文档处理
        - 独立文档批量操作
        - 数据导入/导出
    """

    def __init__(
        self,
        items: List[T],
        processor: Callable[[T], R],
        max_workers: int = 4,
        batch_size: int = 10
    ):
        """
        函数级注释：初始化并行迭代器
        参数：
            items - 待处理项目列表
            processor - 处理函数
            max_workers - 最大工作线程数
            batch_size - 每批处理数量
        """
        self._items = items
        self._processor = processor
        self._max_workers = max_workers
        self._batch_size = batch_size
        self._stats = IteratorStats()

    def __iter__(self) -> Iterator[R]:
        """迭代器接口实现"""
        return self

    def __next__(self) -> R:
        """获取下一个结果"""
        raise NotImplementedError("使用 process() 方法进行批量处理")

    async def process(self) -> List[R]:
        """
        函数级注释：并行处理所有项目
        内部逻辑：使用线程池并行执行处理函数
        返回值：处理结果列表

        @example
        ```python
        iterator = ParallelIterator(documents, process_document)
        results = await iterator.process()
        ```
        """
        results: List[R] = []
        self._stats.start_time = time.time()

        # 内部逻辑：使用线程池并行处理
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            # 内部逻辑：提交所有任务
            future_to_index = {
                executor.submit(self._processor, item): idx
                for idx, item in enumerate(self._items)
            }

            # 内部逻辑：收集结果
            for future in as_completed(future_to_index):
                idx = future_to_index[future]
                try:
                    result = future.result()
                    results.append(result)
                    self._stats.processed_count += 1
                except Exception as e:
                    self._stats.failed_count += 1
                    self._stats.errors.append((idx, e))
                    logger.error(f"项目 {idx} 处理失败: {str(e)}")

        self._stats.end_time = time.time()

        logger.info(
            f"[ParallelIterator] 处理完成: "
            f"成功={self._stats.processed_count}, "
            f"失败={self._stats.failed_count}, "
            f"耗时={self._stats.duration:.2f}s"
        )

        return results

    def get_stats(self) -> IteratorStats:
        """获取统计信息"""
        return self._stats


class TransformIterator(Generic[T, R]):
    """
    类级注释：转换迭代器
    内部逻辑：将输入迭代器的结果转换后输出
    设计模式：迭代器模式 + 装饰器模式
    职责：提供数据转换能力

    使用场景：
        - 数据清洗
        - 格式转换
        - 数据过滤
    """

    def __init__(
        self,
        source_iterator: Iterator[T],
        transformer: Callable[[T], R],
        filter_func: Optional[Callable[[T], bool]] = None
    ):
        """
        函数级注释：初始化转换迭代器
        参数：
            source_iterator - 源迭代器
            transformer - 转换函数
            filter_func - 过滤函数（可选）
        """
        self._source = source_iterator
        self._transformer = transformer
        self._filter = filter_func

    def __iter__(self) -> Iterator[R]:
        """迭代器接口实现"""
        return self

    def __next__(self) -> R:
        """获取下一个转换后的结果"""
        while True:
            item = next(self._source)

            # 内部逻辑：应用过滤
            if self._filter and not self._filter(item):
                continue

            # 内部逻辑：应用转换
            return self._transformer(item)


class BatchProcessorIterator(Generic[T]):
    """
    类级注释：批量处理迭代器
    内部逻辑：分批处理数据并提供进度回调
    设计模式：迭代器模式 + 观察者模式
    职责：支持长时间运行的批量处理

    使用场景：
        - 大数据量导入
        - 批量数据同步
        - 定时任务处理
    """

    def __init__(
        self,
        items: List[T],
        batch_size: int = 100,
        processor: Optional[Callable[[List[T]], Any]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ):
        """
        函数级注释：初始化批量处理迭代器
        参数：
            items - 待处理项目列表
            batch_size - 批次大小
            processor - 批处理函数
            progress_callback - 进度回调函数
        """
        self._items = items
        self._batch_size = batch_size
        self._processor = processor
        self._progress_callback = progress_callback
        self._stats = IteratorStats()

    def __iter__(self) -> Iterator[List[T]]:
        """迭代器接口实现"""
        self._stats.start_time = time.time()
        self._stats.processed_count = 0
        return self

    def __next__(self) -> List[T]:
        """获取下一批数据"""
        start_idx = self._stats.processed_count

        if start_idx >= len(self._items):
            self._stats.end_time = time.time()
            raise StopIteration

        end_idx = min(start_idx + self._batch_size, len(self._items))
        batch = self._items[start_idx:end_idx]
        self._stats.processed_count = end_idx

        # 内部逻辑：报告进度
        if self._progress_callback:
            self._progress_callback(self._stats.processed_count, len(self._items))

        return batch

    async def process_all(self) -> IteratorStats:
        """
        函数级注释：处理所有批次
        内部逻辑：循环处理每批数据 -> 收集统计
        返回值：处理统计信息

        @example
        ```python
        iterator = BatchProcessorIterator(items, batch_size=100)
        stats = await iterator.process_all()
        print(f"处理了 {stats.processed_count} 个项目")
        ```
        """
        if not self._processor:
            raise ValueError("未设置处理函数 processor")

        self._stats.start_time = time.time()

        for batch in self:
            try:
                await self._processor(batch)
            except Exception as e:
                self._stats.failed_count += len(batch)
                self._stats.errors.append((self._stats.processed_count, e))
                logger.error(f"批次处理失败: {str(e)}")

        self._stats.end_time = time.time()

        logger.info(
            f"[BatchProcessorIterator] 批量处理完成: "
            f"总数={len(self._items)}, "
            f"成功={self._stats.processed_count}, "
            f"失败={self._stats.failed_count}, "
            f"耗时={self._stats.duration:.2f}s"
        )

        return self._stats

    def get_stats(self) -> IteratorStats:
        """获取统计信息"""
        return self._stats


class ChainedIterator(Generic[T]):
    """
    类级注释：链式迭代器
    内部逻辑：按顺序遍历多个迭代器
    设计模式：迭代器模式 + 责任链模式
    职责：组合多个数据源

    使用场景：
        - 多文件合并处理
        - 分页数据聚合
        - 多数据源联合查询
    """

    def __init__(self, *iterators: Iterator[T]):
        """
        函数级注释：初始化链式迭代器
        参数：
            *iterators - 可变数量的迭代器
        """
        self._iterators = list(iterators)
        self._current_index = 0
        self._current_iterator: Optional[Iterator[T]] = None

    def __iter__(self) -> Iterator[T]:
        """迭代器接口实现"""
        self._current_index = 0
        self._current_iterator = None
        return self

    def __next__(self) -> T:
        """获取下一个元素"""
        while self._current_index < len(self._iterators):
            # 内部逻辑：获取当前迭代器
            if self._current_iterator is None:
                self._current_iterator = iter(self._iterators[self._current_index])

            try:
                # 内部逻辑：从当前迭代器获取下一个元素
                return next(self._current_iterator)
            except StopIteration:
                # 内部逻辑：当前迭代器耗尽，移动到下一个
                self._current_index += 1
                self._current_iterator = None

        raise StopIteration

    def add_iterator(self, iterator: Iterator[T]) -> None:
        """
        函数级注释：添加迭代器到链的末尾
        参数：
            iterator - 要添加的迭代器
        """
        self._iterators.append(iterator)


class BufferedAsyncIterator(Generic[T]):
    """
    类级注释：缓冲异步迭代器
    内部逻辑：预读取数据到缓冲区，提高读取效率
    设计模式：迭代器模式 + 缓冲模式
    职责：平滑异步数据读取

    使用场景：
        - 网络IO密集型操作
        - 流式数据处理
        - 实时数据源
    """

    def __init__(
        self,
        source: AsyncIterator[T],
        buffer_size: int = 10
    ):
        """
        函数级注释：初始化缓冲异步迭代器
        参数：
            source - 异步数据源
            buffer_size - 缓冲区大小
        """
        self._source = source
        self._buffer_size = buffer_size
        self._buffer: List[T] = []
        self._finished = False

    def __aiter__(self) -> AsyncIterator[T]:
        """异步迭代器接口实现"""
        return self

    async def __anext__(self) -> T:
        """获取下一个元素（异步）"""
        # 内部逻辑：从缓冲区获取
        if self._buffer:
            return self._buffer.pop(0)

        # 内部逻辑：检查是否已完成
        if self._finished:
            raise StopAsyncIteration

        # 内部逻辑：预读取一批数据到缓冲区
        try:
            for _ in range(self._buffer_size):
                item = await self._source.__anext__()
                self._buffer.append(item)
        except StopAsyncIteration:
            self._finished = True

        # 内部逻辑：递归调用获取第一个元素
        if self._buffer:
            return self._buffer.pop(0)

        raise StopAsyncIteration

    async def buffer_all(self) -> List[T]:
        """
        函数级注释：缓冲所有剩余数据
        返回值：所有剩余数据列表
        """
        all_items = []

        while True:
            try:
                item = await self.__anext__()
                all_items.append(item)
            except StopAsyncIteration:
                break

        return all_items


# 导出新增的迭代器类
__all__ = [
    # 原有迭代器
    'DocumentIterator',
    'AsyncDocumentIterator',
    'DatabaseDocumentIterator',
    # 新增迭代器
    'IteratorStats',
    'ParallelIterator',
    'TransformIterator',
    'BatchProcessorIterator',
    'ChainedIterator',
    'BufferedAsyncIterator',
]
