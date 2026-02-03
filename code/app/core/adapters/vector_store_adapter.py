# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：向量存储适配器抽象基类与工厂
内部逻辑：定义统一的向量存储接口，支持多种向量存储后端
设计模式：适配器模式（Adapter Pattern）+ 工厂模式
设计原则：SOLID - 开闭原则、依赖倒置原则、接口隔离原则
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Type
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from loguru import logger


@dataclass
class SearchQuery:
    """
    类级注释：搜索查询数据类
    职责：封装向量搜索的查询参数
    """
    query: str  # 查询文本
    k: int = 4  # 返回结果数量
    filter: Optional[Dict[str, Any]] = None  # 元数据过滤条件
    score_threshold: Optional[float] = None  # 相似度阈值


@dataclass
class SearchResult:
    """
    类级注释：搜索结果数据类
    职责：封装向量搜索的结果
    """
    document: Document  # 匹配的文档
    score: float  # 相似度得分

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "content": self.document.page_content,
            "metadata": self.document.metadata,
            "score": self.score
        }


@dataclass
class VectorStoreConfig:
    """
    类级注释：向量存储配置数据类
    职责：封装向量存储的配置参数
    """
    persist_directory: str  # 持久化目录
    collection_name: str = "default"  # 集合名称
    embedding_function: Optional[Embeddings] = None  # 嵌入函数

    # 内部变量：额外的配置参数（支持不同后端的特定配置）
    extra_params: Dict[str, Any] = field(default_factory=dict)


class VectorStoreAdapter(ABC):
    """
    类级注释：向量存储适配器抽象基类
    设计模式：适配器模式（Adapter Pattern）- 目标接口
    职责：
        1. 定义统一的向量存储接口
        2. 将不同的向量存储实现适配为统一接口
        3. 支持运行时切换不同的向量存储后端

    设计优势：
        - 客户端代码无需关心具体的向量存储实现
        - 新增向量存储后端只需实现适配器
        - 便于测试和Mock
    """

    # 类变量：适配器类型标识
    adapter_type: str = "base"

    @abstractmethod
    async def add_documents(
        self,
        documents: List[Document],
        **kwargs
    ) -> List[str]:
        """
        函数级注释：添加文档到向量存储
        内部逻辑：将文档列表添加到向量存储，返回文档ID列表
        参数：
            documents: 文档列表
            **kwargs: 额外参数
        返回值：文档ID列表
        """
        pass

    @abstractmethod
    async def similarity_search(
        self,
        query: SearchQuery,
        **kwargs
    ) -> List[SearchResult]:
        """
        函数级注释：相似度搜索
        内部逻辑：根据查询向量进行相似度搜索
        参数：
            query: 搜索查询对象
            **kwargs: 额外参数
        返回值：搜索结果列表
        """
        pass

    @abstractmethod
    async def delete_documents(
        self,
        ids: List[str],
        **kwargs
    ) -> bool:
        """
        函数级注释：删除文档
        内部逻辑：根据ID列表删除文档
        参数：
            ids: 文档ID列表
            **kwargs: 额外参数
        返回值：是否删除成功
        """
        pass

    @abstractmethod
    async def count_documents(self) -> int:
        """
        函数级注释：统计文档数量
        返回值：文档总数
        """
        pass

    @abstractmethod
    async def clear_collection(self) -> bool:
        """
        函数级注释：清空集合
        返回值：是否清空成功
        """
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """
        函数级注释：检查向量存储是否就绪
        返回值：是否就绪
        """
        pass

    async def health_check(self) -> Dict[str, Any]:
        """
        函数级注释：健康检查
        返回值：健康状态字典
        """
        return {
            "adapter_type": self.adapter_type,
            "is_ready": self.is_ready(),
            "document_count": await self.count_documents()
        }


class VectorStoreAdapterFactory:
    """
    类级注释：向量存储适配器工厂
    设计模式：工厂模式 + 注册表模式
    职责：
        1. 管理所有向量存储适配器
        2. 根据配置创建对应的适配器实例
        3. 支持动态注册新的适配器
    """

    # 内部类变量：适配器注册表（adapter_type -> 适配器类）
    _registry: Dict[str, Type[VectorStoreAdapter]] = {}

    # 内部类变量：单例实例缓存
    _instances: Dict[str, VectorStoreAdapter] = {}

    @classmethod
    def register(cls, adapter_class: Type[VectorStoreAdapter]) -> None:
        """
        函数级注释：注册向量存储适配器
        内部逻辑：将适配器类添加到注册表中
        参数：
            adapter_class: 适配器类（继承自VectorStoreAdapter）
        """
        adapter_type = adapter_class.adapter_type

        if adapter_type in cls._registry:
            logger.warning(f"向量存储适配器 {adapter_type} 已注册，将被覆盖")

        cls._registry[adapter_type] = adapter_class
        logger.info(f"已注册向量存储适配器: {adapter_type}")

    @classmethod
    def unregister(cls, adapter_type: str) -> None:
        """
        函数级注释：注销向量存储适配器
        参数：
            adapter_type: 适配器类型
        """
        if adapter_type in cls._registry:
            del cls._registry[adapter_type]
            if adapter_type in cls._instances:
                del cls._instances[adapter_type]
            logger.info(f"已注销向量存储适配器: {adapter_type}")

    @classmethod
    def create_adapter(cls, config: VectorStoreConfig, adapter_type: str = "chroma") -> VectorStoreAdapter:
        """
        函数级注释：创建向量存储适配器实例
        内部逻辑：检查注册表 -> 创建适配器实例 -> 返回
        参数：
            config: 向量存储配置
            adapter_type: 适配器类型（默认chroma）
        返回值：VectorStoreAdapter实例
        """
        # 内部逻辑：生成缓存键
        cache_key = f"{adapter_type}_{config.collection_name}"

        # 内部逻辑：检查实例缓存
        if cache_key in cls._instances:
            logger.debug(f"使用缓存的向量存储适配器: {cache_key}")
            return cls._instances[cache_key]

        # 内部逻辑：检查适配器是否已注册
        if adapter_type not in cls._registry:
            supported = list(cls._registry.keys())
            raise ValueError(
                f"未注册的向量存储适配器: {adapter_type}。"
                f"已注册的适配器: {supported}"
            )

        # 内部逻辑：创建新实例
        adapter_class = cls._registry[adapter_type]
        adapter = adapter_class(config)
        cls._instances[cache_key] = adapter

        logger.info(f"创建向量存储适配器: {adapter_type}, 集合: {config.collection_name}")
        return adapter

    @classmethod
    def get_supported_adapters(cls) -> List[str]:
        """
        函数级注释：获取所有已注册的适配器类型
        返回值：适配器类型列表
        """
        return list(cls._registry.keys())

    @classmethod
    def is_registered(cls, adapter_type: str) -> bool:
        """
        函数级注释：检查适配器是否已注册
        参数：
            adapter_type: 适配器类型
        返回值：是否已注册
        """
        return adapter_type in cls._registry

    @classmethod
    def clear_instances(cls) -> None:
        """
        函数级注释：清除所有实例缓存
        """
        cls._instances.clear()
        logger.info("向量存储适配器实例缓存已清除")
