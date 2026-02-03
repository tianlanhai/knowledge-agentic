# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：仓储模式模块
内部逻辑：定义数据访问的抽象接口，支持缓存和 CRUD 操作
设计模式：仓储模式（Repository Pattern）+ 装饰器模式（缓存）
设计原则：依赖倒置原则（DIP）、开闭原则（OCP）、单一职责原则（SRP）

参考：DDD（领域驱动设计）中的仓储模式
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Dict, Any, Callable, Type
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
import asyncio

# 内部变量：泛型类型
T = TypeVar('T')
ID = TypeVar('ID')


class QueryOrder(Enum):
    """
    类级注释：查询排序方向枚举
    属性：
        ASC - 升序
        DESC - 降序
    """
    ASC = "asc"
    DESC = "desc"


@dataclass
class QueryOptions:
    """
    类级注释：查询选项数据类
    属性：分页、排序、过滤等选项
    """
    # 内部属性：跳过数量
    skip: int = 0
    # 内部属性：返回数量
    limit: int = 100
    # 内部属性：排序字段
    order_by: Optional[str] = None
    # 内部属性：排序方向
    order: QueryOrder = QueryOrder.DESC
    # 内部属性：过滤条件
    filters: Dict[str, Any] = field(default_factory=dict)
    # 内部属性：是否包含已删除数据
    include_deleted: bool = False

    def __post_init__(self):
        """初始化后验证"""
        if self.skip < 0:
            raise ValueError("skip 不能为负数")
        if self.limit <= 0:
            raise ValueError("limit 必须大于 0")


@dataclass
class PagedResult:
    """
    类级注释：分页结果数据类
    属性：数据列表、总数、当前页信息
    """
    # 内部属性：数据列表
    items: List[Any]
    # 内部属性：总数
    total: int
    # 内部属性：当前页
    page: int
    # 内部属性：每页数量
    page_size: int
    # 内部属性：总页数
    total_pages: int

    @property
    def has_next(self) -> bool:
        """是否有下一页"""
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        """是否有上一页"""
        return self.page > 1


class IRepository(ABC, Generic[T, ID]):
    """
    类级注释：仓储接口（泛型）
    设计模式：仓储模式（Repository Pattern）
    职责：定义数据访问的抽象接口

    @template T - 实体类型
    @template ID - ID 类型
    """

    @abstractmethod
    async def get_by_id(self, id: ID) -> Optional[T]:
        """
        函数级注释：根据 ID 获取实体
        参数：
            id - 实体 ID
        返回值：实体实例或 None
        """
        pass

    @abstractmethod
    async def get_all(self, options: Optional[QueryOptions] = None) -> List[T]:
        """
        函数级注释：获取所有实体
        参数：
            options - 查询选项
        返回值：实体列表
        """
        pass

    @abstractmethod
    async def find(
        self,
        filters: Dict[str, Any],
        options: Optional[QueryOptions] = None
    ) -> List[T]:
        """
        函数级注释：查找符合条件的实体
        参数：
            filters - 过滤条件
            options - 查询选项
        返回值：实体列表
        """
        pass

    @abstractmethod
    async def find_one(
        self,
        filters: Dict[str, Any]
    ) -> Optional[T]:
        """
        函数级注释：查找单个符合条件的实体
        参数：
            filters - 过滤条件
        返回值：实体实例或 None
        """
        pass

    @abstractmethod
    async def add(self, entity: T) -> T:
        """
        函数级注释：添加实体
        参数：
            entity - 要添加的实体
        返回值：添加后的实体（包含生成的 ID）
        """
        pass

    @abstractmethod
    async def add_many(self, entities: List[T]) -> List[T]:
        """
        函数级注释：批量添加实体
        参数：
            entities - 要添加的实体列表
        返回值：添加后的实体列表
        """
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """
        函数级注释：更新实体
        参数：
            entity - 要更新的实体
        返回值：更新后的实体
        """
        pass

    @abstractmethod
    async def update_many(
        self,
        filters: Dict[str, Any],
        updates: Dict[str, Any]
    ) -> int:
        """
        函数级注释：批量更新实体
        参数：
            filters - 过滤条件
            updates - 要更新的字段
        返回值：更新的实体数量
        """
        pass

    @abstractmethod
    async def delete(self, id: ID) -> bool:
        """
        函数级注释：删除实体
        参数：
            id - 实体 ID
        返回值：是否删除成功
        """
        pass

    @abstractmethod
    async def delete_many(self, filters: Dict[str, Any]) -> int:
        """
        函数级注释：批量删除实体
        参数：
            filters - 过滤条件
        返回值：删除的实体数量
        """
        pass

    @abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        函数级注释：统计实体数量
        参数：
            filters - 过滤条件（可选）
        返回值：实体数量
        """
        pass

    @abstractmethod
    async def exists(self, filters: Dict[str, Any]) -> bool:
        """
        函数级注释：检查实体是否存在
        参数：
            filters - 过滤条件
        返回值：是否存在
        """
        pass

    async def get_page(
        self,
        page: int,
        page_size: int,
        options: Optional[QueryOptions] = None
    ) -> PagedResult:
        """
        函数级注释：获取分页结果
        参数：
            page - 页码（从 1 开始）
            page_size - 每页数量
            options - 额外的查询选项
        返回值：分页结果
        """
        if options is None:
            options = QueryOptions()

        # 内部逻辑：计算 skip 和 limit
        options.skip = (page - 1) * page_size
        options.limit = page_size

        # 内部逻辑：获取数据和总数
        items = await self.get_all(options)
        total = await self.count(options.filters)

        # 内部逻辑：计算总页数
        total_pages = (total + page_size - 1) // page_size

        return PagedResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )


class CachedRepository(Generic[T, ID], IRepository[T, ID], ABC):
    """
    类级注释：带缓存的仓储基类
    设计模式：装饰器模式 + 仓储模式
    职责：为仓储添加缓存能力
    """

    # 内部变量：缓存过期时间（秒）
    _cache_ttl: int = 300

    # 内部变量：内存缓存
    _cache: Dict[str, tuple[Any, float]] = field(default_factory=dict)

    def __init__(self, cache_ttl: int = 300):
        """
        函数级注释：初始化缓存仓储
        参数：
            cache_ttl - 缓存过期时间（秒）
        """
        self._cache_ttl = cache_ttl
        self._cache = {}

    async def get_by_id(self, id: ID) -> Optional[T]:
        """
        函数级注释：根据 ID 获取实体（带缓存）
        参数：
            id - 实体 ID
        返回值：实体实例或 None
        """
        cache_key = f"get_by_id:{id}"

        # 内部逻辑：检查缓存
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        # 内部逻辑：从存储获取
        entity = await self._get_by_id_from_store(id)

        # 内部逻辑：写入缓存
        if entity is not None:
            self._set_cache(cache_key, entity)

        return entity

    async def find(self, filters: Dict[str, Any], options: Optional[QueryOptions] = None) -> List[T]:
        """
        函数级注释：查找实体（带缓存）
        参数：
            filters - 过滤条件
            options - 查询选项
        返回值：实体列表
        """
        # 内部逻辑：为查询生成缓存键
        import json
        cache_key = f"find:{json.dumps(filters, sort_keys=True)}:{options}"

        # 内部逻辑：检查缓存
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        # 内部逻辑：从存储获取
        entities = await self._find_from_store(filters, options)

        # 内部逻辑：写入缓存
        self._set_cache(cache_key, entities)

        return entities

    async def update(self, entity: T) -> T:
        """
        函数级注释：更新实体（清除缓存）
        参数：
            entity - 要更新的实体
        返回值：更新后的实体
        """
        # 内部逻辑：先执行更新
        result = await self._update_in_store(entity)

        # 内部逻辑：清除相关缓存
        self._clear_cache_for_entity(result)

        return result

    async def delete(self, id: ID) -> bool:
        """
        函数级注释：删除实体（清除缓存）
        参数：
            id - 实体 ID
        返回值：是否删除成功
        """
        # 内部逻辑：先执行删除
        success = await self._delete_from_store(id)

        # 内部逻辑：如果成功，清除缓存
        if success:
            self._clear_cache_for_id(id)

        return success

    async def add(self, entity: T) -> T:
        """
        函数级注释：添加实体（带缓存）
        参数：
            entity - 要添加的实体
        返回值：添加后的实体
        """
        result = await self._add_to_store(entity)

        # 内部逻辑：清除列表缓存（防止列表缓存不一致）
        self._clear_list_cache()

        return result

    def clear_cache(self) -> None:
        """
        函数级注释：清空所有缓存
        """
        self._cache.clear()
        logger.debug("[CachedRepository] 缓存已清空")

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """
        函数级注释：从缓存获取数据（内部方法）
        参数：
            key - 缓存键
        返回值：缓存的数据或 None
        """
        import time

        if key not in self._cache:
            return None

        data, timestamp = self._cache[key]

        # 内部逻辑：检查是否过期
        if time.time() - timestamp > self._cache_ttl:
            del self._cache[key]
            return None

        return data

    def _set_cache(self, key: str, data: Any) -> None:
        """
        函数级注释：设置缓存（内部方法）
        参数：
            key - 缓存键
            data - 要缓存的数据
        """
        import time
        self._cache[key] = (data, time.time())

    def _clear_list_cache(self) -> None:
        """
        函数级注释：清除列表缓存（内部方法）
        """
        keys_to_delete = [k for k in self._cache.keys() if k.startswith('find:')]
        for key in keys_to_delete:
            del self._cache[key]

    def _clear_cache_for_id(self, id: ID) -> None:
        """
        函数级注释：清除指定 ID 的缓存（内部方法）
        参数：
            id - 实体 ID
        """
        keys_to_delete = [k for k in self._cache.keys() if str(id) in k]
        for key in keys_to_delete:
            del self._cache[key]

    def _clear_cache_for_entity(self, entity: T) -> None:
        """
        函数级注释：清除实体相关的缓存（内部方法，子类可覆盖）
        参数：
            entity - 实体对象
        """
        # 内部逻辑：尝试获取实体的 ID
        if hasattr(entity, 'id'):
            self._clear_cache_for_id(entity.id)
        else:
            # 内部逻辑：如果没有 ID 属性，清空所有缓存
            self.clear_cache()

    # 内部逻辑：抽象方法 - 子类必须实现存储操作

    @abstractmethod
    async def _get_by_id_from_store(self, id: ID) -> Optional[T]:
        """从存储获取实体（子类实现）"""
        pass

    @abstractmethod
    async def _find_from_store(
        self,
        filters: Dict[str, Any],
        options: Optional[QueryOptions]
    ) -> List[T]:
        """从存储查找实体（子类实现）"""
        pass

    @abstractmethod
    async def _update_in_store(self, entity: T) -> T:
        """更新存储中的实体（子类实现）"""
        pass

    @abstractmethod
    async def _delete_from_store(self, id: ID) -> bool:
        """从存储删除实体（子类实现）"""
        pass

    @abstractmethod
    async def _add_to_store(self, entity: T) -> T:
        """添加实体到存储（子类实现）"""
        pass

    # 内部逻辑：继承的抽象方法，子类仍需实现

    @abstractmethod
    async def get_all(self, options: Optional[QueryOptions] = None) -> List[T]:
        """获取所有实体（子类实现）"""
        pass

    @abstractmethod
    async def find_one(self, filters: Dict[str, Any]) -> Optional[T]:
        """查找单个实体（子类实现）"""
        pass

    @abstractmethod
    async def add_many(self, entities: List[T]) -> List[T]:
        """批量添加实体（子类实现）"""
        pass

    @abstractmethod
    async def update_many(
        self,
        filters: Dict[str, Any],
        updates: Dict[str, Any]
    ) -> int:
        """批量更新实体（子类实现）"""
        pass

    @abstractmethod
    async def delete_many(self, filters: Dict[str, Any]) -> int:
        """批量删除实体（子类实现）"""
        pass

    @abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """统计实体数量（子类实现）"""
        pass

    @abstractmethod
    async def exists(self, filters: Dict[str, Any]) -> bool:
        """检查实体是否存在（子类实现）"""
        pass


# 内部变量：导出所有公共接口
__all__ = [
    'IRepository',
    'CachedRepository',
    'QueryOptions',
    'PagedResult',
    'QueryOrder',
]
