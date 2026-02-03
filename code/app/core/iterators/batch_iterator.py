# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：批量迭代器模块
内部逻辑：将大数据集分批处理，避免内存溢出
设计模式：迭代器模式（Iterator Pattern）
设计原则：SOLID - 单一职责原则

使用场景：
- 大批量文档处理
- 数据库分页查询
- 文件流式读取
"""

from typing import List, Any, Iterator, Optional, Callable, TypeVar
from loguru import logger

T = TypeVar('T')


class BatchIterator:
    """
    类级注释：批量迭代器
    设计模式：迭代器模式（Iterator Pattern）
    职责：
        1. 将大数据集分批处理
        2. 支持惰性加载
        3. 减少内存占用

    设计优势：
        - 避免一次性加载全部数据
        - 支持流式处理
        - 可配置批处理大小
    """

    def __init__(
        self,
        data: List[T],
        batch_size: int = 100,
        drop_incomplete: bool = False
    ):
        """
        函数级注释：初始化批量迭代器
        参数：
            data: 原始数据列表
            batch_size: 每批数据大小
            drop_incomplete: 是否丢弃不完整的最后一批
        """
        self.data = data
        self.batch_size = batch_size
        self.drop_incomplete = drop_incomplete
        self._index = 0

    def __iter__(self) -> Iterator[List[T]]:
        """
        函数级注释：迭代器接口实现
        返回值：迭代器自身
        """
        self._index = 0
        return self

    def __next__(self) -> List[T]:
        """
        函数级注释：获取下一批数据
        返回值：一批数据
        异常：StopIteration - 没有更多数据
        """
        # 内部逻辑：检查是否还有数据
        if self._index >= len(self.data):
            raise StopIteration

        # 内部逻辑：计算当前批的结束位置
        end_index = min(self._index + self.batch_size, len(self.data))
        batch = self.data[self._index:end_index]

        # 内部逻辑：检查是否需要丢弃不完整的批次
        if self.drop_incomplete and len(batch) < self.batch_size:
            raise StopIteration

        self._index = end_index

        if self._index % (self.batch_size * 10) == 0:
            logger.debug(f"已处理 {self._index} 条数据")

        return batch

    def __len__(self) -> int:
        """
        函数级注释：计算批次数
        返回值：总批次数
        """
        if self.drop_incomplete:
            return len(self.data) // self.batch_size
        return (len(self.data) + self.batch_size - 1) // self.batch_size

    def reset(self) -> None:
        """
        函数级注释：重置迭代器
        内部逻辑：将索引重置为0
        """
        self._index = 0


class LazyBatchIterator:
    """
    类级注释：惰性批量迭代器
    设计模式：迭代器模式 + 生成器模式
    职责：按需生成数据批次，支持无限数据集

    设计优势：
        - 支持无限数据集
        - 按需加载数据
        - 内存效率更高
    """

    def __init__(
        self,
        data_fetcher: Callable[[int, int], List[T]],
        batch_size: int = 100,
        max_batches: Optional[int] = None
    ):
        """
        函数级注释：初始化惰性批量迭代器
        参数：
            data_fetcher: 数据获取函数 (offset, limit) -> List[T]
            batch_size: 每批数据大小
            max_batches: 最大批次数（None表示无限制）
        """
        self.data_fetcher = data_fetcher
        self.batch_size = batch_size
        self.max_batches = max_batches
        self._batch_count = 0

    def __iter__(self) -> Iterator[List[T]]:
        """
        函数级注释：迭代器接口实现
        """
        self._batch_count = 0
        return self

    def __next__(self) -> List[T]:
        """
        函数级注释：获取下一批数据
        内部逻辑：调用data_fetcher获取数据
        """
        # 内部逻辑：检查批次限制
        if self.max_batches is not None and self._batch_count >= self.max_batches:
            raise StopIteration

        # 内部逻辑：获取数据
        offset = self._batch_count * self.batch_size
        batch = self.data_fetcher(offset, self.batch_size)

        # 内部逻辑：没有更多数据
        if not batch:
            raise StopIteration

        self._batch_count += 1
        logger.debug(f"惰性加载批次 {self._batch_count}, 数据量: {len(batch)}")

        return batch


class BatchProcessor:
    """
    类级注释：批量处理器
    设计模式：模板方法模式
    职责：提供批量处理的高层接口

    设计优势：
        - 封装批量处理流程
        - 支持进度回调
        - 统一错误处理
    """

    def __init__(self, batch_size: int = 100):
        """
        函数级注释：初始化批量处理器
        参数：
            batch_size: 每批数据大小
        """
        self.batch_size = batch_size

    def process(
        self,
        data: List[T],
        processor: Callable[[List[T]], Any],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Any]:
        """
        函数级注释：批量处理数据
        内部逻辑：分批 -> 处理每批 -> 收集结果
        参数：
            data: 原始数据
            processor: 处理函数
            progress_callback: 进度回调 (current, total)
        返回值：处理结果列表
        """
        results = []
        total = len(data)

        for batch in BatchIterator(data, self.batch_size):
            try:
                # 内部逻辑：处理当前批次
                result = processor(batch)
                results.append(result)

                # 内部逻辑：报告进度
                if progress_callback:
                    processed = min(results[0].__len__() if results else 0, total)
                    progress_callback(processed, total)

            except Exception as e:
                logger.error(f"批次处理失败: {str(e)}")
                raise

        return results

    async def aprocess(
        self,
        data: List[T],
        processor: Callable[[List[T]], Any],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Any]:
        """
        函数级注释：异步批量处理数据
        内部逻辑：分批 -> 异步处理每批 -> 收集结果
        """
        results = []
        total = len(data)

        for batch in BatchIterator(data, self.batch_size):
            try:
                # 内部逻辑：异步处理当前批次
                import asyncio
                if asyncio.iscoroutinefunction(processor):
                    result = await processor(batch)
                else:
                    result = processor(batch)
                results.append(result)

                if progress_callback:
                    processed = min(len(results) * self.batch_size, total)
                    progress_callback(processed, total)

            except Exception as e:
                logger.error(f"异步批次处理失败: {str(e)}")
                raise

        return results


class BatchIteratorFactory:
    """
    类级注释：批量迭代器工厂
    设计模式：工厂模式
    职责：创建不同类型的批量迭代器

    设计优势：
        - 统一创建接口
        - 支持多种迭代器类型
        - 便于扩展
    """

    @staticmethod
    def from_list(data: List[T], batch_size: int = 100) -> BatchIterator:
        """
        函数级注释：从列表创建批量迭代器
        参数：
            data: 数据列表
            batch_size: 批处理大小
        返回值：BatchIterator实例
        """
        return BatchIterator(data, batch_size)

    @staticmethod
    def from_fetcher(
        fetcher: Callable[[int, int], List[T]],
        batch_size: int = 100,
        max_batches: Optional[int] = None
    ) -> LazyBatchIterator:
        """
        函数级注释：从数据获取函数创建惰性迭代器
        参数：
            fetcher: 数据获取函数
            batch_size: 批处理大小
            max_batches: 最大批次数
        返回值：LazyBatchIterator实例
        """
        return LazyBatchIterator(fetcher, batch_size, max_batches)

    @staticmethod
    def from_generator(
        generator: Callable[[], Iterator[T]],
        batch_size: int = 100
    ) -> Iterator[List[T]]:
        """
        函数级注释：从生成器创建批量迭代器
        内部逻辑：从生成器逐个获取元素，累积成批返回
        参数：
            generator: 生成器函数
            batch_size: 批处理大小
        返回值：批量数据的迭代器
        """
        def batch_generator():
            batch = []
            for item in generator():
                batch.append(item)
                if len(batch) >= batch_size:
                    yield batch
                    batch = []
            if batch:
                yield batch

        return batch_generator()
