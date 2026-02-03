# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：文档摄入增强服务模块
内部逻辑：集成享元模式进行文档去重和内存优化
设计模式：享元模式 + 装饰器模式
设计原则：单一职责原则、DRY原则
"""

from typing import List, Dict, Any, Optional, Tuple
from loguru import logger

from app.core.flyweight.chunk_flyweight import (
    ChunkFlyweightFactory,
    ChunkManager,
    ChunkFlyweight,
    ChunkMetadata
)


class IngestOptimizationService:
    """
    类级注释：文档摄入优化服务
    设计模式：享元模式 + 装饰器模式
    职责：
        1. 在文档摄入时进行去重
        2. 优化内存使用
        3. 提供重复内容检测

    使用场景：
        - 批量文档上传
        - 相同文档的多次上传
        - 文档版本管理
    """

    def __init__(self, similarity_threshold: float = 0.9):
        """
        函数级注释：初始化优化服务
        参数：
            similarity_threshold - 相似度阈值（0-1）
        """
        self.similarity_threshold = similarity_threshold
        # 内部变量：片段管理器
        self.chunk_manager = ChunkManager()

    async def optimize_document_ingest(
        self,
        document_id: int,
        chunks: List[str]
    ) -> Dict[str, Any]:
        """
        函数级注释：优化文档摄入
        内部逻辑：使用享元模式处理文档片段 -> 检测重复 -> 返回优化结果
        参数：
            document_id - 文档ID
            chunks - 文档片段列表
        返回值：优化结果统计
        """
        # 内部变量：统计信息
        stats = {
            "total_chunks": len(chunks),
            "unique_chunks": 0,
            "duplicate_chunks": 0,
            "saved_memory": 0,
            "dedup_ratio": 0.0
        }

        # 内部变量：存储原始片段总长度
        original_total_length = sum(len(chunk) for chunk in chunks)

        for index, chunk in enumerate(chunks):
            # 内部逻辑：检查是否重复
            if ChunkFlyweightFactory.is_duplicate(chunk):
                stats["duplicate_chunks"] += 1
                # 内部逻辑：复用现有享元
                flyweight = ChunkFlyweightFactory.get_flyweight(chunk)
                logger.debug(f"文档 {document_id} 片段 {index} 发现重复，复用享元")
            else:
                stats["unique_chunks"] += 1
                # 内部逻辑：创建新享元
                flyweight = ChunkFlyweightFactory.get_flyweight(chunk)

                # 内部逻辑：添加到管理器
                self.chunk_manager.add_chunk(
                    document_id=document_id,
                    content=chunk,
                    chunk_index=index
                )

        # 内部逻辑：计算节省的内存
        # 假设重复的片段节省了存储空间
        stats["saved_memory"] = stats["duplicate_chunks"] * 1000  # 假设每个片段平均1KB

        # 内部逻辑：计算去重率
        if stats["total_chunks"] > 0:
            stats["dedup_ratio"] = stats["duplicate_chunks"] / stats["total_chunks"]

        logger.info(
            f"文档 {document_id} 摄入优化完成: "
            f"总数={stats['total_chunks']}, "
            f"重复={stats['duplicate_chunks']}, "
            f"去重率={stats['dedup_ratio']:.2%}"
        )

        return stats

    def find_duplicate_content(
        self,
        content: str,
        document_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        函数级注释：查找重复内容
        内部逻辑：使用享元工厂查找相似内容
        参数：
            content - 要查找的内容
            document_id - 排除的文档ID
        返回值：重复内容列表
        """
        duplicates = []

        # 内部逻辑：查找相似的享元
        similar_flyweights = ChunkFlyweightFactory.find_duplicates(
            content,
            threshold=self.similarity_threshold
        )

        # 内部逻辑：定位重复内容的文档位置
        for doc_id, chunks in self.chunk_manager._document_chunks.items():
            if document_id and doc_id == document_id:
                continue

            for flyweight, metadata in chunks:
                if flyweight in similar_flyweights:
                    duplicates.append({
                        "document_id": doc_id,
                        "chunk_index": metadata.chunk_index,
                        "content_preview": flyweight.get_excerpt(50)
                    })

        return duplicates

    def get_optimization_stats(self) -> Dict[str, Any]:
        """
        函数级注释：获取优化统计信息
        返回值：统计信息字典
        """
        factory_stats = ChunkFlyweightFactory.get_stats()

        return {
            "flyweight_stats": factory_stats,
            "document_count": len(self.chunk_manager._document_chunks),
            "memory_saved_estimate": factory_stats["total_content_length"] - factory_stats["unique_content_count"] * 1000,
        }

    def clear_document(self, document_id: int) -> None:
        """
        函数级注释：清理文档数据
        内部逻辑：释放文档相关的所有享元引用
        参数：
            document_id - 文档ID
        """
        self.chunk_manager.remove_document(document_id)
        logger.info(f"已清理文档 {document_id} 的享元数据")


class DocumentDeduplicator:
    """
    类级注释：文档去重器
    设计模式：策略模式 + 享元模式
    职责：
        1. 检测重复文档
        2. 计算文档相似度
        3. 提供去重建议

    使用场景：
        - 批量导入文档前检查
        - 定期清理重复文档
    """

    def __init__(self, similarity_threshold: float = 0.95):
        """
        函数级注释：初始化去重器
        参数：
            similarity_threshold - 相似度阈值
        """
        self.similarity_threshold = similarity_threshold

    async def check_duplicate(
        self,
        content: str,
        existing_documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        函数级注释：检查重复文档
        参数：
            content - 文档内容
            existing_documents - 现有文档列表
        返回值：重复文档列表
        """
        duplicates = []

        # 内部逻辑：使用享元工厂检查
        is_duplicate = ChunkFlyweightFactory.is_duplicate(content)

        if is_duplicate:
            # 内部逻辑：查找使用该内容的文档
            flyweight = ChunkFlyweightFactory.get_flyweight(content)
            for doc in existing_documents:
                if doc.get("content", "") == content:
                    duplicates.append(doc)

        # 内部逻辑：检查相似文档
        if not duplicates:
            for doc in existing_documents:
                doc_content = doc.get("content", "")
                similarity = self._calculate_similarity(content, doc_content)

                if similarity >= self.similarity_threshold:
                    duplicates.append({
                        **doc,
                        "similarity": similarity
                    })

        return duplicates

    def _calculate_similarity(self, content1: str, content2: str) -> float:
        """
        函数级注释：计算两段文本的相似度
        参数：
            content1 - 文本1
            content2 - 文本2
        返回值：相似度（0-1）
        @private
        """
        # 内部逻辑：简单的词汇重叠度计算
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0


# 内部变量：导出所有公共接口
__all__ = [
    'IngestOptimizationService',
    'DocumentDeduplicator',
]
