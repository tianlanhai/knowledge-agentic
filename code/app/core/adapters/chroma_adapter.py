# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：Chroma向量存储适配器
内部逻辑：将Chroma向量存储适配为统一的VectorStoreAdapter接口
设计模式：适配器模式（Adapter Pattern）- 具体适配器
设计原则：SOLID - 单一职责原则
"""

from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from loguru import logger

from app.core.adapters.vector_store_adapter import (
    VectorStoreAdapter,
    VectorStoreConfig,
    SearchQuery,
    SearchResult,
    VectorStoreAdapterFactory,
)


class ChromaAdapter(VectorStoreAdapter):
    """
    类级注释：Chroma向量存储适配器
    设计模式：适配器模式（Adapter Pattern）- 具体适配器
    职责：将Chroma向量存储适配为统一接口
    """

    adapter_type = "chroma"

    def __init__(self, config: VectorStoreConfig):
        """
        函数级注释：初始化Chroma适配器
        内部逻辑：创建Chroma实例 -> 初始化就绪状态
        参数：
            config: 向量存储配置
        """
        self.config = config
        self._vector_store: Optional[Chroma] = None
        self._is_ready = False

        # 内部逻辑：创建Chroma实例
        try:
            self._vector_store = Chroma(
                persist_directory=config.persist_directory,
                embedding_function=config.embedding_function,
                collection_name=config.collection_name
            )
            self._is_ready = True
            logger.info(f"Chroma适配器初始化成功，集合: {config.collection_name}")
        except Exception as e:
            logger.error(f"Chroma适配器初始化失败: {str(e)}")
            self._is_ready = False

    async def add_documents(
        self,
        documents: List[Document],
        **kwargs
    ) -> List[str]:
        """
        函数级注释：添加文档到Chroma
        内部逻辑：调用Chroma的add_documents方法
        参数：
            documents: 文档列表
            **kwargs: 额外参数（ids等）
        返回值：文档ID列表
        """
        if not self.is_ready():
            raise RuntimeError("Chroma适配器未就绪")

        ids = kwargs.get("ids")
        result = self._vector_store.add_documents(documents, ids=ids)

        # 内部逻辑：Chroma返回的是添加的文档，需要提取ID
        if isinstance(result, list):
            # 内部逻辑：Chroma可能返回字符串ID或文档列表
            if result and isinstance(result[0], str):
                return result

        # 内部逻辑：如果返回的是Document列表，从metadata中提取ID
        if result and hasattr(result[0], 'metadata'):
            return [doc.metadata.get('id', '') for doc in result]

        return []

    async def similarity_search(
        self,
        query: SearchQuery,
        **kwargs
    ) -> List[SearchResult]:
        """
        函数级注释：相似度搜索
        内部逻辑：调用Chroma的similarity_search_with_score方法
        参数：
            query: 搜索查询对象
            **kwargs: 额外参数
        返回值：搜索结果列表
        """
        if not self.is_ready():
            raise RuntimeError("Chroma适配器未就绪")

        # 内部逻辑：构建搜索参数
        search_kwargs = {"k": query.k}
        if query.filter:
            search_kwargs["filter"] = query.filter

        # 内部逻辑：执行带分数的相似度搜索
        results = self._vector_store.similarity_search_with_score(
            query.query,
            **search_kwargs
        )

        # 内部逻辑：转换为统一的SearchResult格式
        search_results = []
        for doc, score in results:
            # 内部逻辑：应用分数阈值过滤
            if query.score_threshold is None or score >= query.score_threshold:
                search_results.append(SearchResult(document=doc, score=float(score)))

        return search_results

    async def delete_documents(
        self,
        ids: List[str],
        **kwargs
    ) -> bool:
        """
        函数级注释：删除文档
        内部逻辑：调用Chroma的delete方法
        参数：
            ids: 文档ID列表
            **kwargs: 额外参数
        返回值：是否删除成功
        """
        if not self.is_ready():
            raise RuntimeError("Chroma适配器未就绪")

        try:
            self._vector_store.delete(ids=ids)
            return True
        except Exception as e:
            logger.error(f"删除文档失败: {str(e)}")
            return False

    async def count_documents(self) -> int:
        """
        函数级注释：统计文档数量
        返回值：文档总数
        """
        if not self.is_ready():
            return 0

        try:
            collection = self._vector_store._collection
            return collection.count()
        except Exception as e:
            logger.error(f"统计文档数量失败: {str(e)}")
            return 0

    async def clear_collection(self) -> bool:
        """
        函数级注释：清空集合
        返回值：是否清空成功
        """
        if not self.is_ready():
            return False

        try:
            # 内部逻辑：删除并重新创建集合
            collection = self._vector_store._collection
            collection.delete(where={})
            return True
        except Exception as e:
            logger.error(f"清空集合失败: {str(e)}")
            return False

    def is_ready(self) -> bool:
        """
        函数级注释：检查Chroma是否就绪
        返回值：是否就绪
        """
        return self._is_ready and self._vector_store is not None

    @property
    def raw_store(self) -> Optional[Chroma]:
        """
        函数级注释：获取原始Chroma实例
        返回值：Chroma实例（用于需要直接访问原始实例的场景）
        """
        return self._vector_store


# 内部逻辑：自动注册Chroma适配器
VectorStoreAdapterFactory.register(ChromaAdapter)
