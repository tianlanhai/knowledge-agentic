# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：对话仓储实现模块
内部逻辑：实现对话相关的数据访问层
设计模式：仓储模式（Repository Pattern）
设计原则：依赖倒置原则（DIP）、单一职责原则（SRP）
"""

from typing import List, Optional, Dict, Any
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from .base import IRepository, QueryOptions, PagedResult, CachedRepository, QueryOrder
from ..models.conversation import Conversation, Message


class ConversationRepository(IRepository[Conversation, int]):
    """
    类级注释：对话仓储类
    设计模式：仓储模式（Repository Pattern）
    职责：管理对话数据的 CRUD 操作
    """

    def __init__(self, session: AsyncSession):
        """
        函数级注释：初始化对话仓储
        参数：
            session - 数据库会话
        """
        self._session = session

    async def get_by_id(self, id: int) -> Optional[Conversation]:
        """
        函数级注释：根据 ID 获取对话
        参数：
            id - 对话 ID
        返回值：对话实例或 None
        """
        stmt = select(Conversation).where(Conversation.id == id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, options: Optional[QueryOptions] = None) -> List[Conversation]:
        """
        函数级注释：获取所有对话
        参数：
            options - 查询选项
        返回值：对话列表
        """
        stmt = select(Conversation)

        # 内部逻辑：应用过滤条件
        if options and options.filters:
            for key, value in options.filters.items():
                if hasattr(Conversation, key):
                    stmt = stmt.where(getattr(Conversation, key) == value)

        # 内部逻辑：应用排序
        if options and options.order_by:
            order_column = getattr(Conversation, options.order_by)
            if options.order.value == "desc":
                stmt = stmt.order_by(order_column.desc())
            else:
                stmt = stmt.order_by(order_column.asc())

        # 内部逻辑：应用分页
        if options:
            stmt = stmt.offset(options.skip).limit(options.limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def find(
        self,
        filters: Dict[str, Any],
        options: Optional[QueryOptions] = None
    ) -> List[Conversation]:
        """
        函数级注释：查找对话
        参数：
            filters - 过滤条件
            options - 查询选项
        返回值：对话列表
        """
        if options is None:
            options = QueryOptions()
        options.filters = filters
        return await self.get_all(options)

    async def find_one(self, filters: Dict[str, Any]) -> Optional[Conversation]:
        """
        函数级注释：查找单个对话
        参数：
            filters - 过滤条件
        返回值：对话实例或 None
        """
        stmt = select(Conversation)

        for key, value in filters.items():
            if hasattr(Conversation, key):
                stmt = stmt.where(getattr(Conversation, key) == value)

        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def add(self, entity: Conversation) -> Conversation:
        """
        函数级注释：添加对话
        参数：
            entity - 对话实体
        返回值：添加后的对话
        """
        self._session.add(entity)
        await self._session.flush()
        return entity

    async def add_many(self, entities: List[Conversation]) -> List[Conversation]:
        """
        函数级注释：批量添加对话
        参数：
            entities - 对话列表
        返回值：添加后的对话列表
        """
        for entity in entities:
            self._session.add(entity)
        await self._session.flush()
        return entities

    async def update(self, entity: Conversation) -> Conversation:
        """
        函数级注释：更新对话
        参数：
            entity - 对话实体
        返回值：更新后的对话
        """
        # 内部逻辑：将实体附加到会话
        self._session.merge(entity)
        await self._session.flush()
        return entity

    async def update_many(
        self,
        filters: Dict[str, Any],
        updates: Dict[str, Any]
    ) -> int:
        """
        函数级注释：批量更新对话
        参数：
            filters - 过滤条件
            updates - 要更新的字段
        返回值：更新的对话数量
        """
        stmt = select(Conversation)

        for key, value in filters.items():
            if hasattr(Conversation, key):
                stmt = stmt.where(getattr(Conversation, key) == value)

        result = await self._session.execute(stmt)
        entities = result.scalars().all()
        count = 0

        for entity in entities:
            for key, value in updates.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            count += 1

        await self._session.flush()
        return count

    async def delete(self, id: int) -> bool:
        """
        函数级注释：删除对话
        参数：
            id - 对话 ID
        返回值：是否删除成功
        """
        entity = await self.get_by_id(id)
        if entity:
            await self._session.delete(entity)
            await self._session.flush()
            return True
        return False

    async def delete_many(self, filters: Dict[str, Any]) -> int:
        """
        函数级注释：批量删除对话
        参数：
            filters - 过滤条件
        返回值：删除的对话数量
        """
        stmt = select(Conversation)

        for key, value in filters.items():
            if hasattr(Conversation, key):
                stmt = stmt.where(getattr(Conversation, key) == value)

        result = await self._session.execute(stmt)
        entities = result.scalars().all()
        count = len(entities)

        for entity in entities:
            await self._session.delete(entity)

        await self._session.flush()
        return count

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        函数级注释：统计对话数量
        参数：
            filters - 过滤条件
        返回值：对话数量
        """
        stmt = select(func.count(Conversation.id))

        if filters:
            for key, value in filters.items():
                if hasattr(Conversation, key):
                    stmt = stmt.where(getattr(Conversation, key) == value)

        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def exists(self, filters: Dict[str, Any]) -> bool:
        """
        函数级注释：检查对话是否存在
        参数：
            filters - 过滤条件
        返回值：是否存在
        """
        return await self.count(filters) > 0

    async def get_by_user_id(
        self,
        user_id: int,
        options: Optional[QueryOptions] = None
    ) -> List[Conversation]:
        """
        函数级注释：获取用户的对话列表
        参数：
            user_id - 用户 ID
            options - 查询选项
        返回值：对话列表
        """
        return await self.find({"user_id": user_id}, options)

    async def get_recent(
        self,
        limit: int = 10,
        user_id: Optional[int] = None
    ) -> List[Conversation]:
        """
        函数级注释：获取最近的对话
        参数：
            limit - 返回数量
            user_id - 用户 ID（可选）
        返回值：对话列表
        """
        options = QueryOptions(
            limit=limit,
            order_by="created_at",
            order=QueryOrder.DESC
        )

        if user_id is not None:
            options.filters = {"user_id": user_id}

        return await self.get_all(options)


class MessageRepository(IRepository[Message, int]):
    """
    类级注释：消息仓储类
    设计模式：仓储模式（Repository Pattern）
    职责：管理消息数据的 CRUD 操作
    """

    def __init__(self, session: AsyncSession):
        """
        函数级注释：初始化消息仓储
        参数：
            session - 数据库会话
        """
        self._session = session

    async def get_by_id(self, id: int) -> Optional[Message]:
        """
        函数级注释：根据 ID 获取消息
        参数：
            id - 消息 ID
        返回值：消息实例或 None
        """
        stmt = select(Message).where(Message.id == id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, options: Optional[QueryOptions] = None) -> List[Message]:
        """
        函数级注释：获取所有消息
        参数：
            options - 查询选项
        返回值：消息列表
        """
        stmt = select(Message)

        if options and options.filters:
            for key, value in options.filters.items():
                if hasattr(Message, key):
                    stmt = stmt.where(getattr(Message, key) == value)

        if options and options.order_by:
            order_column = getattr(Message, options.order_by)
            if options.order.value == "desc":
                stmt = stmt.order_by(order_column.desc())
            else:
                stmt = stmt.order_by(order_column.asc())

        if options:
            stmt = stmt.offset(options.skip).limit(options.limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def find(
        self,
        filters: Dict[str, Any],
        options: Optional[QueryOptions] = None
    ) -> List[Message]:
        """
        函数级注释：查找消息
        参数：
            filters - 过滤条件
            options - 查询选项
        返回值：消息列表
        """
        if options is None:
            options = QueryOptions()
        options.filters = filters
        return await self.get_all(options)

    async def find_one(self, filters: Dict[str, Any]) -> Optional[Message]:
        """
        函数级注释：查找单条消息
        参数：
            filters - 过滤条件
        返回值：消息实例或 None
        """
        stmt = select(Message)

        for key, value in filters.items():
            if hasattr(Message, key):
                stmt = stmt.where(getattr(Message, key) == value)

        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def add(self, entity: Message) -> Message:
        """
        函数级注释：添加消息
        参数：
            entity - 消息实体
        返回值：添加后的消息
        """
        self._session.add(entity)
        await self._session.flush()
        return entity

    async def add_many(self, entities: List[Message]) -> List[Message]:
        """
        函数级注释：批量添加消息
        参数：
            entities - 消息列表
        返回值：添加后的消息列表
        """
        for entity in entities:
            self._session.add(entity)
        await self._session.flush()
        return entities

    async def update(self, entity: Message) -> Message:
        """
        函数级注释：更新消息
        参数：
            entity - 消息实体
        返回值：更新后的消息
        """
        self._session.merge(entity)
        await self._session.flush()
        return entity

    async def update_many(
        self,
        filters: Dict[str, Any],
        updates: Dict[str, Any]
    ) -> int:
        """
        函数级注释：批量更新消息
        参数：
            filters - 过滤条件
            updates - 要更新的字段
        返回值：更新的消息数量
        """
        stmt = select(Message)

        for key, value in filters.items():
            if hasattr(Message, key):
                stmt = stmt.where(getattr(Message, key) == value)

        result = await self._session.execute(stmt)
        entities = result.scalars().all()
        count = 0

        for entity in entities:
            for key, value in updates.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            count += 1

        await self._session.flush()
        return count

    async def delete(self, id: int) -> bool:
        """
        函数级注释：删除消息
        参数：
            id - 消息 ID
        返回值：是否删除成功
        """
        entity = await self.get_by_id(id)
        if entity:
            await self._session.delete(entity)
            await self._session.flush()
            return True
        return False

    async def delete_many(self, filters: Dict[str, Any]) -> int:
        """
        函数级注释：批量删除消息
        参数：
            filters - 过滤条件
        返回值：删除的消息数量
        """
        stmt = select(Message)

        for key, value in filters.items():
            if hasattr(Message, key):
                stmt = stmt.where(getattr(Message, key) == value)

        result = await self._session.execute(stmt)
        entities = result.scalars().all()
        count = len(entities)

        for entity in entities:
            await self._session.delete(entity)

        await self._session.flush()
        return count

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        函数级注释：统计消息数量
        参数：
            filters - 过滤条件
        返回值：消息数量
        """
        stmt = select(func.count(Message.id))

        if filters:
            for key, value in filters.items():
                if hasattr(Message, key):
                    stmt = stmt.where(getattr(Message, key) == value)

        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def exists(self, filters: Dict[str, Any]) -> bool:
        """
        函数级注释：检查消息是否存在
        参数：
            filters - 过滤条件
        返回值：是否存在
        """
        return await self.count(filters) > 0

    async def get_by_conversation_id(
        self,
        conversation_id: int,
        options: Optional[QueryOptions] = None
    ) -> List[Message]:
        """
        函数级注释：获取对话的消息列表
        参数：
            conversation_id - 对话 ID
            options - 查询选项
        返回值：消息列表
        """
        return await self.find({"conversation_id": conversation_id}, options)


# 内部变量：导出所有公共接口
__all__ = [
    'ConversationRepository',
    'MessageRepository',
]
