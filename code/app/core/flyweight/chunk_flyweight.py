# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：文档片段享元工厂
内部逻辑：共享相同内容的文档片段，减少内存占用
设计模式：享元模式（Flyweight Pattern）
设计原则：SOLID - 单一职责原则、DRY原则

使用场景：
- 多个文档共享相同片段时，避免重复存储
- 文档去重和相似度分析
- 内存优化
"""

import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from loguru import logger


@dataclass(frozen=True)
class ChunkMetadata:
    """
    类级注释：片段元数据（外蕴状态）
    职责：存储片段的非共享信息
    设计模式：享元模式 - 外蕴状态（不共享）
    """
    document_id: int
    chunk_index: int
    page_number: Optional[int] = None
    timestamp: Optional[str] = None


@dataclass(frozen=True)
class ChunkFlyweight:
    """
    类级注释：文档片段享元对象
    设计模式：享元模式（Flyweight Pattern）- 享元对象
    职责：
        1. 存储共享的片段内容（内蕴状态）
        2. 提供内容访问接口

    设计优势：
        - 相同内容的片段只存储一份
        - 减少内存占用
        - 便于内容去重
    """

    # 内部变量：内容哈希值（作为唯一标识）
    content_hash: str

    # 内部变量：片段内容（内蕴状态，可共享）
    content: str

    # 内部变量：内容长度（缓存，避免重复计算）
    length: int = field(init=False)

    def __post_init__(self):
        """初始化后处理：计算内容长度"""
        object.__setattr__(self, 'length', len(self.content))

    def get_content(self) -> str:
        """获取片段内容"""
        return self.content

    def get_excerpt(self, max_length: int = 100) -> str:
        """
        函数级注释：获取片段摘要
        内部逻辑：截取前N个字符，添加省略号
        参数：
            max_length: 最大长度
        返回值：摘要文本
        """
        if self.length <= max_length:
            return self.content
        return self.content[:max_length] + "..."

    def similarity_ratio(self, other: "ChunkFlyweight") -> float:
        """
        函数级注释：计算与另一个片段的相似度比例
        内部逻辑：使用简单的字符匹配计算相似度
        参数：
            other: 另一个片段享元
        返回值：相似度比例（0-1）
        """
        if self.content == other.content:
            return 1.0

        # 内部逻辑：使用集合交集计算相似度
        set1 = set(self.content.lower().split())
        set2 = set(other.content.lower().split())

        if not set1 or not set2:
            return 0.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0


class ChunkFlyweightFactory:
    """
    类级注释：文档片段享元工厂
    设计模式：享元模式（Flyweight Pattern）- 享元工厂
    职责：
        1. 管理所有片段享元对象
        2. 根据内容获取或创建享元
        3. 维护内容到享元的映射

    设计优势：
        - 确保相同内容只创建一个享元对象
        - 集中管理所有享元
        - 提供内容去重功能
    """

    # 内部类变量：内容哈希到享元对象的映射
    _flyweights: Dict[str, ChunkFlyweight] = {}

    # 内部类变量：内容到哈希的映射（快速查找）
    _content_to_hash: Dict[str, str] = {}

    # 内部类变量：享元引用计数（用于垃圾回收）
    _ref_counts: Dict[str, int] = {}

    @classmethod
    def get_flyweight(cls, content: str) -> ChunkFlyweight:
        """
        函数级注释：获取或创建片段享元
        内部逻辑：计算哈希 -> 查找现有享元 -> 创建或返回
        参数：
            content: 片段内容
        返回值：ChunkFlyweight享元对象
        """
        # 内部逻辑：计算内容哈希
        content_hash = cls._compute_hash(content)

        # 内部逻辑：检查是否已存在
        if content_hash in cls._flyweights:
            cls._ref_counts[content_hash] = cls._ref_counts.get(content_hash, 0) + 1
            logger.debug(f"复用片段享元: {content_hash[:16]}...")
            return cls._flyweights[content_hash]

        # 内部逻辑：创建新的享元对象
        flyweight = ChunkFlyweight(
            content_hash=content_hash,
            content=content
        )
        cls._flyweights[content_hash] = flyweight
        cls._content_to_hash[content] = content_hash
        cls._ref_counts[content_hash] = 1

        logger.info(f"创建新片段享元: {content_hash[:16]}..., 长度: {len(content)}")
        return flyweight

    @classmethod
    def get_flyweight_by_hash(cls, content_hash: str) -> Optional[ChunkFlyweight]:
        """
        函数级注释：根据哈希获取享元
        参数：
            content_hash: 内容哈希值
        返回值：ChunkFlyweight享元对象或None
        """
        return cls._flyweights.get(content_hash)

    @classmethod
    def release_flyweight(cls, flyweight: ChunkFlyweight) -> None:
        """
        函数级注释：释放享元引用
        内部逻辑：减少引用计数，引用为0时删除享元
        参数：
            flyweight: 要释放的享元对象
        """
        content_hash = flyweight.content_hash

        # 内部逻辑：减少引用计数
        if content_hash in cls._ref_counts:
            cls._ref_counts[content_hash] -= 1

            # 内部逻辑：引用为0时删除享元
            if cls._ref_counts[content_hash] <= 0:
                del cls._flyweights[content_hash]
                # 内部逻辑：同时删除内容到哈希的映射
                content_to_remove = [
                    content for content, hash_val in cls._content_to_hash.items()
                    if hash_val == content_hash
                ]
                for content in content_to_remove:
                    del cls._content_to_hash[content]
                del cls._ref_counts[content_hash]

                logger.debug(f"释放片段享元: {content_hash[:16]}...")

    @classmethod
    def find_duplicates(cls, content: str, threshold: float = 1.0) -> List[ChunkFlyweight]:
        """
        函数级注释：查找与给定内容相似的片段
        内部逻辑：遍历所有享元，计算相似度，返回超过阈值的
        参数：
            content: 要查找的内容
            threshold: 相似度阈值（0-1）
        返回值：相似的享元列表
        """
        temp_flyweight = ChunkFlyweight(
            content_hash="temp",
            content=content
        )

        duplicates = []
        for flyweight in cls._flyweights.values():
            if flyweight.similarity_ratio(temp_flyweight) >= threshold:
                duplicates.append(flyweight)

        return duplicates

    @classmethod
    def is_duplicate(cls, content: str) -> bool:
        """
        函数级注释：检查内容是否已存在
        参数：
            content: 要检查的内容
        返回值：是否重复
        """
        content_hash = cls._compute_hash(content)
        return content_hash in cls._flyweights

    @classmethod
    def get_stats(cls) -> Dict[str, any]:
        """
        函数级注释：获取享元统计信息
        返回值：统计信息字典
        """
        total_content_length = sum(fw.length for fw in cls._flyweights.values())

        return {
            "flyweight_count": len(cls._flyweights),
            "total_ref_count": sum(cls._ref_counts.values()),
            "total_content_length": total_content_length,
            "avg_content_length": total_content_length / len(cls._flyweights) if cls._flyweights else 0,
            "unique_content_count": len(cls._content_to_hash)
        }

    @classmethod
    def clear_all(cls) -> None:
        """
        函数级注释：清除所有享元
        内部逻辑：清空所有映射表
        """
        cls._flyweights.clear()
        cls._content_to_hash.clear()
        cls._ref_counts.clear()
        logger.info("已清除所有片段享元")

    @classmethod
    def _compute_hash(cls, content: str) -> str:
        """
        函数级注释：计算内容哈希
        内部逻辑：使用MD5哈希算法
        参数：
            content: 内容文本
        返回值：哈希值字符串
        """
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    @classmethod
    def get_all_hashes(cls) -> Set[str]:
        """
        函数级注释：获取所有已存在的内容哈希
        返回值：哈希集合
        """
        return set(cls._flyweights.keys())


class ChunkManager:
    """
    类级注释：片段管理器
    设计模式：门面模式 - 提供简化的片段管理接口
    职责：
        1. 管理享元片段与文档的映射
        2. 提供片段添加、查询、删除功能
        3. 自动管理享元生命周期
    """

    def __init__(self):
        """初始化片段管理器"""
        # 内部变量：文档ID到片段享元列表的映射
        self._document_chunks: Dict[int, List[tuple[ChunkFlyweight, ChunkMetadata]]] = {}

    def add_chunk(self, document_id: int, content: str, chunk_index: int, **metadata) -> ChunkFlyweight:
        """
        函数级注释：添加文档片段
        内部逻辑：获取或创建享元 -> 创建元数据 -> 存储映射
        参数：
            document_id: 文档ID
            content: 片段内容
            chunk_index: 片段索引
            **metadata: 额外的元数据
        返回值：ChunkFlyweight享元对象
        """
        # 内部逻辑：获取或创建享元
        flyweight = ChunkFlyweightFactory.get_flyweight(content)

        # 内部逻辑：创建元数据
        chunk_metadata = ChunkMetadata(
            document_id=document_id,
            chunk_index=chunk_index,
            page_number=metadata.get('page_number'),
            timestamp=metadata.get('timestamp')
        )

        # 内部逻辑：存储映射
        if document_id not in self._document_chunks:
            self._document_chunks[document_id] = []
        self._document_chunks[document_id].append((flyweight, chunk_metadata))

        return flyweight

    def get_document_chunks(self, document_id: int) -> List[tuple[ChunkFlyweight, ChunkMetadata]]:
        """
        函数级注释：获取文档的所有片段
        参数：
            document_id: 文档ID
        返回值：(享元, 元数据)元组列表
        """
        return self._document_chunks.get(document_id, [])

    def remove_document(self, document_id: int) -> None:
        """
        函数级注释：移除文档及其片段
        内部逻辑：释放享元引用 -> 删除文档映射
        参数：
            document_id: 文档ID
        """
        if document_id in self._document_chunks:
            for flyweight, _ in self._document_chunks[document_id]:
                ChunkFlyweightFactory.release_flyweight(flyweight)
            del self._document_chunks[document_id]
            logger.info(f"已移除文档 {document_id} 的所有片段")

    def find_similar_chunks(self, content: str, threshold: float = 0.8) -> List[tuple[ChunkFlyweight, int, ChunkMetadata]]:
        """
        函数级注释：查找相似的片段
        内部逻辑：使用享元工厂查找相似内容 -> 定位文档位置
        参数：
            content: 要查找的内容
            threshold: 相似度阈值
        返回值：(享元, 文档ID, 元数据)元组列表
        """
        similar_flyweights = ChunkFlyweightFactory.find_duplicates(content, threshold)

        result = []
        for doc_id, chunks in self._document_chunks.items():
            for flyweight, metadata in chunks:
                if flyweight in similar_flyweights:
                    result.append((flyweight, doc_id, metadata))

        return result
