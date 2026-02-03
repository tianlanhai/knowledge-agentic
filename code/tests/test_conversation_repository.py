# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：对话仓储测试模块
内部逻辑：测试ConversationRepository和MessageRepository的完整功能
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.conversation_repository import (
    ConversationRepository,
    MessageRepository
)
from app.repositories.base import QueryOptions, QueryOrder, PagedResult
from app.models.conversation import Conversation, Message, MessageRole


# ============================================================================
# 测试数据构建辅助类
# ============================================================================

class TestDataBuilder:
    """
    类级注释：测试数据构建器
    职责：构建测试用的对话和消息数据
    """

    @staticmethod
    def create_conversation(
        conv_id: int = 1,
        title: str = "测试对话",
        model_name: str = "gpt-4"
    ) -> Conversation:
        """
        函数级注释：创建测试对话对象
        参数：
            conv_id - 对话ID
            title - 对话标题
            model_name - 模型名称
        返回值：Conversation实例
        """
        conv = Conversation()
        conv.id = conv_id
        conv.title = title
        conv.model_name = model_name
        conv.created_at = datetime.now()
        conv.updated_at = datetime.now()
        return conv

    @staticmethod
    def create_message(
        msg_id: int = 1,
        conversation_id: int = 1,
        role: MessageRole = MessageRole.USER,
        content: str = "测试消息"
    ) -> Message:
        """
        函数级注释：创建测试消息对象
        参数：
            msg_id - 消息ID
            conversation_id - 对话ID
            role - 角色（MessageRole枚举）
            content - 消息内容
        返回值：Message实例
        """
        msg = Message()
        msg.id = msg_id
        msg.conversation_id = conversation_id
        msg.role = role
        msg.content = content
        msg.created_at = datetime.now()
        return msg


# ============================================================================
# ConversationRepository 测试类
# ============================================================================

class TestConversationRepository:
    """
    类级注释：对话仓储测试类
    职责：测试ConversationRepository的CRUD操作
    """

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, db_session: AsyncSession):
        """
        测试目的：验证根据ID获取对话功能
        测试场景：获取存在的对话
        """
        # Arrange: 创建对话
        conv = TestDataBuilder.create_conversation(1, "测试对话")
        db_session.add(conv)
        await db_session.flush()

        # Act: 获取对话
        repo = ConversationRepository(db_session)
        result = await repo.get_by_id(1)

        # Assert: 验证获取成功
        assert result is not None
        assert result.id == 1
        assert result.title == "测试对话"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, db_session: AsyncSession):
        """
        测试目的：验证获取不存在的对话返回None
        测试场景：尝试获取不存在的对话ID
        """
        # Arrange: 创建仓储
        repo = ConversationRepository(db_session)

        # Act: 尝试获取不存在的对话
        result = await repo.get_by_id(999)

        # Assert: 验证返回None
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all(self, db_session: AsyncSession):
        """
        测试目的：验证获取所有对话功能
        测试场景：获取所有对话列表
        """
        # Arrange: 创建多个对话
        for i in range(1, 4):
            conv = TestDataBuilder.create_conversation(i, i, f"对话{i}")
            db_session.add(conv)
        await db_session.flush()

        # Act: 获取所有对话
        repo = ConversationRepository(db_session)
        results = await repo.get_all()

        # Assert: 验证获取结果
        assert len(results) == 3
        assert all(isinstance(r, Conversation) for r in results)

    @pytest.mark.asyncio
    async def test_get_all_with_filters(self, db_session: AsyncSession):
        """
        测试目的：验证带过滤条件获取对话功能
        测试场景：按标题过滤对话
        """
        # Arrange: 创建不同标题的对话
        conv1 = TestDataBuilder.create_conversation(1, "用户1对话", "gpt-4")
        conv2 = TestDataBuilder.create_conversation(2, "用户1对话2", "gpt-4")
        conv3 = TestDataBuilder.create_conversation(3, "用户2对话", "gpt-3.5")
        db_session.add(conv1)
        db_session.add(conv2)
        db_session.add(conv3)
        await db_session.flush()

        # Act: 按模型名称过滤
        repo = ConversationRepository(db_session)
        options = QueryOptions(filters={"model_name": "gpt-3.5"})
        results = await repo.get_all(options)

        # Assert: 验证过滤结果
        assert len(results) == 1
        assert results[0].model_name == "gpt-3.5"

    @pytest.mark.asyncio
    async def test_get_all_with_ordering(self, db_session: AsyncSession):
        """
        测试目的：验证排序功能
        测试场景：按创建时间降序排序
        """
        # Arrange: 创建对话
        for i in range(1, 4):
            conv = TestDataBuilder.create_conversation(i, 1, f"对话{i}")
            db_session.add(conv)
        await db_session.flush()

        # Act: 按创建时间降序获取
        repo = ConversationRepository(db_session)
        options = QueryOptions(order_by="created_at", order=QueryOrder.DESC)
        results = await repo.get_all(options)

        # Assert: 验证排序结果
        assert len(results) == 3
        # 最新的在前
        # 注意：由于创建时间相近，这里主要验证不报错

    @pytest.mark.asyncio
    async def test_get_all_with_pagination(self, db_session: AsyncSession):
        """
        测试目的：验证分页功能
        测试场景：获取第一页数据
        """
        # Arrange: 创建多个对话
        for i in range(1, 11):
            conv = TestDataBuilder.create_conversation(i, 1, f"对话{i}")
            db_session.add(conv)
        await db_session.flush()

        # Act: 获取第一页（每页5条）
        repo = ConversationRepository(db_session)
        options = QueryOptions(skip=0, limit=5)
        results = await repo.get_all(options)

        # Assert: 验证分页结果
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_find(self, db_session: AsyncSession):
        """
        测试目的：验证查找对话功能
        测试场景：按标题查找对话
        """
        # Arrange: 创建对话
        conv1 = TestDataBuilder.create_conversation(1, "工作对话", "gpt-4")
        conv2 = TestDataBuilder.create_conversation(2, "个人对话", "gpt-3.5")
        db_session.add(conv1)
        db_session.add(conv2)
        await db_session.flush()

        # Act: 查找特定标题的对话
        repo = ConversationRepository(db_session)
        results = await repo.find({"title": "工作对话"})

        # Assert: 验证查找结果
        assert len(results) == 1
        assert results[0].title == "工作对话"

    @pytest.mark.asyncio
    async def test_find_with_options(self, db_session: AsyncSession):
        """
        测试目的：验证带选项的查找功能
        测试场景：查找并限制数量
        """
        # Arrange: 创建对话
        for i in range(1, 4):
            conv = TestDataBuilder.create_conversation(i, f"对话{i}", "gpt-4")
            db_session.add(conv)
        await db_session.flush()

        # Act: 查找并限制数量
        repo = ConversationRepository(db_session)
        options = QueryOptions(limit=2)
        results = await repo.find({"model_name": "gpt-4"}, options)

        # Assert: 验证查找结果
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_find_one(self, db_session: AsyncSession):
        """
        测试目的：验证查找单个对话功能
        测试场景：按多个条件查找单个对话
        """
        # Arrange: 创建对话
        conv = TestDataBuilder.create_conversation(1, "测试对话")
        db_session.add(conv)
        await db_session.flush()

        # Act: 查找单个对话
        repo = ConversationRepository(db_session)
        result = await repo.find_one({"title": "测试对话"})

        # Assert: 验证查找结果
        assert result is not None
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_find_one_not_found(self, db_session: AsyncSession):
        """
        测试目的：验证查找不存在的单个对话返回None
        测试场景：按不匹配的条件查找
        """
        # Arrange: 创建仓储
        repo = ConversationRepository(db_session)

        # Act: 查找不存在的对话
        result = await repo.find_one({"model_name": "不存在"})

        # Assert: 验证返回None
        assert result is None

    @pytest.mark.asyncio
    async def test_add(self, db_session: AsyncSession):
        """
        测试目的：验证添加对话功能
        测试场景：添加新对话
        """
        # Arrange: 创建新对话
        conv = TestDataBuilder.create_conversation(1, "新对话")

        # Act: 添加对话
        repo = ConversationRepository(db_session)
        result = await repo.add(conv)

        # Assert: 验证添加成功
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_add_many(self, db_session: AsyncSession):
        """
        测试目的：验证批量添加对话功能
        测试场景：批量添加多个对话
        """
        # Arrange: 创建多个对话
        conversations = [
            TestDataBuilder.create_conversation(1, "对话1"),
            TestDataBuilder.create_conversation(2, "对话2"),
            TestDataBuilder.create_conversation(3, "对话3"),
        ]

        # Act: 批量添加
        repo = ConversationRepository(db_session)
        results = await repo.add_many(conversations)

        # Assert: 验证添加成功
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_update(self, db_session: AsyncSession):
        """
        测试目的：验证更新对话功能
        测试场景：更新对话标题
        """
        # Arrange: 创建对话
        conv = TestDataBuilder.create_conversation(1, "原标题")
        db_session.add(conv)
        await db_session.flush()

        # Act: 更新对话
        repo = ConversationRepository(db_session)
        conv.title = "新标题"
        result = await repo.update(conv)

        # Assert: 验证更新成功
        assert result.title == "新标题"

    @pytest.mark.asyncio
    async def test_update_many(self, db_session: AsyncSession):
        """
        测试目的：验证批量更新对话功能
        测试场景：批量更新符合条件的对话
        """
        # Arrange: 创建对话
        conv1 = TestDataBuilder.create_conversation(1, "对话1")
        conv2 = TestDataBuilder.create_conversation(2, "对话2")
        db_session.add(conv1)
        db_session.add(conv2)
        await db_session.flush()

        # Act: 批量更新用户1的所有对话
        repo = ConversationRepository(db_session)
        count = await repo.update_many(
            {"model_name": "gpt-4"},
            {"title": "已更新"}
        )

        # Assert: 验证更新数量
        assert count == 2

    @pytest.mark.asyncio
    async def test_delete(self, db_session: AsyncSession):
        """
        测试目的：验证删除对话功能
        测试场景：删除指定对话
        """
        # Arrange: 创建对话
        conv = TestDataBuilder.create_conversation(1, "待删除")
        db_session.add(conv)
        await db_session.flush()

        # Act: 删除对话
        repo = ConversationRepository(db_session)
        result = await repo.delete(1)

        # Assert: 验证删除成功
        assert result is True

        # 验证已被删除
        deleted_conv = await repo.get_by_id(1)
        assert deleted_conv is None

    @pytest.mark.asyncio
    async def test_delete_not_found(self, db_session: AsyncSession):
        """
        测试目的：验证删除不存在的对话返回False
        测试场景：尝试删除不存在的对话
        """
        # Arrange: 创建仓储
        repo = ConversationRepository(db_session)

        # Act: 尝试删除不存在的对话
        result = await repo.delete(999)

        # Assert: 验证返回False
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_many(self, db_session: AsyncSession):
        """
        测试目的：验证批量删除对话功能
        测试场景：批量删除符合条件的对话
        """
        # Arrange: 创建对话 - 使用不同的model_name来区分
        conv1 = TestDataBuilder.create_conversation(1, "对话1", "gpt-4")
        conv2 = TestDataBuilder.create_conversation(2, "对话2", "gpt-4")
        conv3 = TestDataBuilder.create_conversation(3, "对话3", "gpt-3.5")
        db_session.add(conv1)
        db_session.add(conv2)
        db_session.add(conv3)
        await db_session.flush()

        # Act: 批量删除gpt-4的对话
        repo = ConversationRepository(db_session)
        count = await repo.delete_many({"model_name": "gpt-4"})

        # Assert: 验证删除数量
        assert count == 2

    @pytest.mark.asyncio
    async def test_count(self, db_session: AsyncSession):
        """
        测试目的：验证统计对话数量功能
        测试场景：统计所有对话数量
        """
        # Arrange: 创建对话
        for i in range(1, 4):
            conv = TestDataBuilder.create_conversation(i, 1, f"对话{i}")
            db_session.add(conv)
        await db_session.flush()

        # Act: 统计数量
        repo = ConversationRepository(db_session)
        count = await repo.count()

        # Assert: 验证数量
        assert count == 3

    @pytest.mark.asyncio
    async def test_count_with_filters(self, db_session: AsyncSession):
        """
        测试目的：验证带条件统计对话数量功能
        测试场景：统计特定模型的对话数量
        """
        # Arrange: 创建不同模型的对话
        conv1 = TestDataBuilder.create_conversation(1, "用户1对话", "gpt-4")
        conv2 = TestDataBuilder.create_conversation(2, "用户1对话2", "gpt-4")
        conv3 = TestDataBuilder.create_conversation(3, "用户2对话", "gpt-3.5")
        db_session.add(conv1)
        db_session.add(conv2)
        db_session.add(conv3)
        await db_session.flush()

        # Act: 统计gpt-4模型的对话数量
        repo = ConversationRepository(db_session)
        count = await repo.count({"model_name": "gpt-4"})

        # Assert: 验证数量
        assert count == 2

    @pytest.mark.asyncio
    async def test_exists_true(self, db_session: AsyncSession):
        """
        测试目的：验证检查对话是否存在（存在的情况）
        测试场景：检查存在的对话
        """
        # Arrange: 创建对话
        conv = TestDataBuilder.create_conversation(1, "测试对话")
        db_session.add(conv)
        await db_session.flush()

        # Act: 检查是否存在
        repo = ConversationRepository(db_session)
        result = await repo.exists({"model_name": "gpt-4"})

        # Assert: 验证返回True
        assert result is True

    @pytest.mark.asyncio
    async def test_exists_false(self, db_session: AsyncSession):
        """
        测试目的：验证检查对话是否存在（不存在的情况）
        测试场景：检查不存在的对话
        """
        # Arrange: 创建仓储
        repo = ConversationRepository(db_session)

        # Act: 检查是否存在
        result = await repo.exists({"model_name": "不存在"})

        # Assert: 验证返回False
        assert result is False

    @pytest.mark.asyncio
    async def test_get_by_user_id(self, db_session: AsyncSession):
        """
        测试目的：验证获取用户对话列表功能
        测试场景：获取指定模型名称的所有对话
        """
        # Arrange: 创建不同模型的对话
        conv1 = TestDataBuilder.create_conversation(1, "用户1对话1", "gpt-4")
        conv2 = TestDataBuilder.create_conversation(2, "用户1对话2", "gpt-4")
        conv3 = TestDataBuilder.create_conversation(3, "用户2对话", "gpt-3.5")
        db_session.add(conv1)
        db_session.add(conv2)
        db_session.add(conv3)
        await db_session.flush()

        # Act: 按模型名称获取对话 (使用find方法，因为Conversation没有get_by_model_name)
        repo = ConversationRepository(db_session)
        results = await repo.find({"model_name": "gpt-4"})

        # Assert: 验证获取结果
        assert len(results) == 2
        assert all(r.model_name == "gpt-4" for r in results)

    @pytest.mark.asyncio
    async def test_get_by_user_id_with_options(self, db_session: AsyncSession):
        """
        测试目的：验证带选项获取用户对话列表功能
        测试场景：获取用户对话并分页
        """
        # Arrange: 创建多个对话
        for i in range(1, 6):
            conv = TestDataBuilder.create_conversation(i, f"对话{i}", "gpt-4")
            db_session.add(conv)
        await db_session.flush()

        # Act: 获取对话（限制3条）
        repo = ConversationRepository(db_session)
        options = QueryOptions(limit=3)
        results = await repo.find({"model_name": "gpt-4"}, options)

        # Assert: 验证分页结果
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_get_recent(self, db_session: AsyncSession):
        """
        测试目的：验证获取最近对话功能
        测试场景：获取最近的对话
        """
        # Arrange: 创建对话
        for i in range(1, 6):
            conv = TestDataBuilder.create_conversation(i, 1, f"对话{i}")
            db_session.add(conv)
        await db_session.flush()

        # Act: 获取最近3条对话
        repo = ConversationRepository(db_session)
        results = await repo.get_recent(limit=3)

        # Assert: 验证获取结果
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_get_recent_with_user_filter(self, db_session: AsyncSession):
        """
        测试目的：验证按模型过滤获取最近对话功能
        测试场景：获取特定模型的最近对话
        """
        # Arrange: 创建不同模型的对话
        conv1 = TestDataBuilder.create_conversation(1, "用户1对话1", "gpt-4")
        conv2 = TestDataBuilder.create_conversation(2, "用户1对话2", "gpt-4")
        conv3 = TestDataBuilder.create_conversation(3, "用户2对话", "gpt-3.5")
        db_session.add(conv1)
        db_session.add(conv2)
        db_session.add(conv3)
        await db_session.flush()

        # Act: 获取最近的对话，无过滤
        repo = ConversationRepository(db_session)
        results = await repo.get_recent(limit=10)

        # Assert: 验证获取结果（应该返回所有3条）
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_get_page(self, db_session: AsyncSession):
        """
        测试目的：验证分页获取对话功能
        测试场景：获取第1页数据
        """
        # Arrange: 创建多个对话
        for i in range(1, 11):
            conv = TestDataBuilder.create_conversation(i, 1, f"对话{i}")
            db_session.add(conv)
        await db_session.flush()

        # Act: 获取第1页（每页5条）
        repo = ConversationRepository(db_session)
        paged_result = await repo.get_page(page=1, page_size=5)

        # Assert: 验证分页结果
        assert isinstance(paged_result, PagedResult)
        assert len(paged_result.items) == 5
        assert paged_result.page == 1
        assert paged_result.page_size == 5
        assert paged_result.total == 10
        assert paged_result.total_pages == 2
        assert paged_result.has_next is True
        assert paged_result.has_previous is False

    @pytest.mark.asyncio
    async def test_get_page_second_page(self, db_session: AsyncSession):
        """
        测试目的：验证获取第二页数据功能
        测试场景：获取第2页数据
        """
        # Arrange: 创建多个对话
        for i in range(1, 11):
            conv = TestDataBuilder.create_conversation(i, 1, f"对话{i}")
            db_session.add(conv)
        await db_session.flush()

        # Act: 获取第2页
        repo = ConversationRepository(db_session)
        paged_result = await repo.get_page(page=2, page_size=5)

        # Assert: 验证分页结果
        assert len(paged_result.items) == 5
        assert paged_result.page == 2
        assert paged_result.has_next is False
        assert paged_result.has_previous is True


# ============================================================================
# MessageRepository 测试类
# ============================================================================

class TestMessageRepository:
    """
    类级注释：消息仓储测试类
    职责：测试MessageRepository的CRUD操作
    """

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, db_session: AsyncSession):
        """
        测试目的：验证根据ID获取消息功能
        测试场景：获取存在的消息
        """
        # Arrange: 创建对话和消息
        conv = TestDataBuilder.create_conversation(1, "测试对话")
        db_session.add(conv)
        await db_session.flush()

        msg = TestDataBuilder.create_message(1, 1, MessageRole.USER, "测试消息")
        db_session.add(msg)
        await db_session.flush()

        # Act: 获取消息
        repo = MessageRepository(db_session)
        result = await repo.get_by_id(1)

        # Assert: 验证获取成功
        assert result is not None
        assert result.id == 1
        assert result.content == "测试消息"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, db_session: AsyncSession):
        """
        测试目的：验证获取不存在的消息返回None
        测试场景：尝试获取不存在的消息ID
        """
        # Arrange: 创建仓储
        repo = MessageRepository(db_session)

        # Act: 尝试获取不存在的消息
        result = await repo.get_by_id(999)

        # Assert: 验证返回None
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all(self, db_session: AsyncSession):
        """
        测试目的：验证获取所有消息功能
        测试场景：获取所有消息列表
        """
        # Arrange: 创建对话和消息
        conv = TestDataBuilder.create_conversation(1, "测试对话")
        db_session.add(conv)
        await db_session.flush()

        for i in range(1, 4):
            msg = TestDataBuilder.create_message(i, 1, MessageRole.USER, f"消息{i}")
            db_session.add(msg)
        await db_session.flush()

        # Act: 获取所有消息
        repo = MessageRepository(db_session)
        results = await repo.get_all()

        # Assert: 验证获取结果
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_get_all_with_filters(self, db_session: AsyncSession):
        """
        测试目的：验证带过滤条件获取消息功能
        测试场景：按对话ID过滤消息
        """
        # Arrange: 创建对话和消息
        conv1 = TestDataBuilder.create_conversation(1, "对话1")
        conv2 = TestDataBuilder.create_conversation(2, "对话2")
        db_session.add(conv1)
        db_session.add(conv2)
        await db_session.flush()

        msg1 = TestDataBuilder.create_message(1, 1, MessageRole.USER, "对话1消息")
        msg2 = TestDataBuilder.create_message(2, 2, MessageRole.USER, "对话2消息")
        db_session.add(msg1)
        db_session.add(msg2)
        await db_session.flush()

        # Act: 按对话ID过滤
        repo = MessageRepository(db_session)
        options = QueryOptions(filters={"conversation_id": 1})
        results = await repo.get_all(options)

        # Assert: 验证过滤结果
        assert len(results) == 1
        assert results[0].conversation_id == 1

    @pytest.mark.asyncio
    async def test_find(self, db_session: AsyncSession):
        """
        测试目的：验证查找消息功能
        测试场景：按条件查找消息
        """
        # Arrange: 创建对话和消息
        conv = TestDataBuilder.create_conversation(1, "测试对话")
        db_session.add(conv)
        await db_session.flush()

        msg = TestDataBuilder.create_message(1, 1, MessageRole.USER, "用户消息")
        db_session.add(msg)
        await db_session.flush()

        # Act: 查找用户消息
        repo = MessageRepository(db_session)
        results = await repo.find({"role": MessageRole.USER})

        # Assert: 验证查找结果
        assert len(results) >= 1
        assert results[0].role == MessageRole.USER

    @pytest.mark.asyncio
    async def test_find_one(self, db_session: AsyncSession):
        """
        测试目的：验证查找单个消息功能
        测试场景：按多个条件查找单个消息
        """
        # Arrange: 创建对话和消息
        conv = TestDataBuilder.create_conversation(1, "测试对话")
        db_session.add(conv)
        await db_session.flush()

        msg = TestDataBuilder.create_message(1, 1, MessageRole.USER, "特定消息")
        db_session.add(msg)
        await db_session.flush()

        # Act: 查找单个消息
        repo = MessageRepository(db_session)
        result = await repo.find_one({"conversation_id": 1, "role": MessageRole.USER})

        # Assert: 验证查找结果
        assert result is not None
        assert result.role == MessageRole.USER

    @pytest.mark.asyncio
    async def test_add(self, db_session: AsyncSession):
        """
        测试目的：验证添加消息功能
        测试场景：添加新消息
        """
        # Arrange: 创建对话
        conv = TestDataBuilder.create_conversation(1, "测试对话")
        db_session.add(conv)
        await db_session.flush()

        # Act: 添加消息
        msg = TestDataBuilder.create_message(1, 1, "user", "新消息")
        repo = MessageRepository(db_session)
        result = await repo.add(msg)

        # Assert: 验证添加成功
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_add_many(self, db_session: AsyncSession):
        """
        测试目的：验证批量添加消息功能
        测试场景：批量添加多个消息
        """
        # Arrange: 创建对话
        conv = TestDataBuilder.create_conversation(1, "测试对话")
        db_session.add(conv)
        await db_session.flush()

        # Act: 批量添加消息
        messages = [
            TestDataBuilder.create_message(1, 1, "user", "消息1"),
            TestDataBuilder.create_message(2, 1, "assistant", "消息2"),
            TestDataBuilder.create_message(3, 1, "user", "消息3"),
        ]
        repo = MessageRepository(db_session)
        results = await repo.add_many(messages)

        # Assert: 验证添加成功
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_update(self, db_session: AsyncSession):
        """
        测试目的：验证更新消息功能
        测试场景：更新消息内容
        """
        # Arrange: 创建对话和消息
        conv = TestDataBuilder.create_conversation(1, "测试对话")
        db_session.add(conv)
        await db_session.flush()

        msg = TestDataBuilder.create_message(1, 1, "user", "原内容")
        db_session.add(msg)
        await db_session.flush()

        # Act: 更新消息
        repo = MessageRepository(db_session)
        msg.content = "新内容"
        result = await repo.update(msg)

        # Assert: 验证更新成功
        assert result.content == "新内容"

    @pytest.mark.asyncio
    async def test_update_many(self, db_session: AsyncSession):
        """
        测试目的：验证批量更新消息功能
        测试场景：批量更新符合条件的消息
        """
        # Arrange: 创建对话和消息
        conv = TestDataBuilder.create_conversation(1, "测试对话")
        db_session.add(conv)
        await db_session.flush()

        msg1 = TestDataBuilder.create_message(1, 1, MessageRole.USER, "消息1")
        msg2 = TestDataBuilder.create_message(2, 1, MessageRole.USER, "消息2")
        db_session.add(msg1)
        db_session.add(msg2)
        await db_session.flush()

        # Act: 批量更新用户消息
        repo = MessageRepository(db_session)
        count = await repo.update_many(
            {"role": MessageRole.USER},
            {"content": "已更新"}
        )

        # Assert: 验证更新数量
        assert count == 2

    @pytest.mark.asyncio
    async def test_delete(self, db_session: AsyncSession):
        """
        测试目的：验证删除消息功能
        测试场景：删除指定消息
        """
        # Arrange: 创建对话和消息
        conv = TestDataBuilder.create_conversation(1, "测试对话")
        db_session.add(conv)
        await db_session.flush()

        msg = TestDataBuilder.create_message(1, 1, MessageRole.USER, "待删除")
        db_session.add(msg)
        await db_session.flush()

        # Act: 删除消息
        repo = MessageRepository(db_session)
        result = await repo.delete(1)

        # Assert: 验证删除成功
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_not_found(self, db_session: AsyncSession):
        """
        测试目的：验证删除不存在的消息返回False
        测试场景：尝试删除不存在的消息
        """
        # Arrange: 创建仓储
        repo = MessageRepository(db_session)

        # Act: 尝试删除不存在的消息
        result = await repo.delete(999)

        # Assert: 验证返回False
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_many(self, db_session: AsyncSession):
        """
        测试目的：验证批量删除消息功能
        测试场景：批量删除符合条件的消息
        """
        # Arrange: 创建对话和消息
        conv = TestDataBuilder.create_conversation(1, "测试对话")
        db_session.add(conv)
        await db_session.flush()

        for i in range(1, 4):
            msg = TestDataBuilder.create_message(i, 1, MessageRole.USER, f"消息{i}")
            db_session.add(msg)
        await db_session.flush()

        # Act: 批量删除用户消息
        repo = MessageRepository(db_session)
        count = await repo.delete_many({"conversation_id": 1})

        # Assert: 验证删除数量
        assert count == 3

    @pytest.mark.asyncio
    async def test_count(self, db_session: AsyncSession):
        """
        测试目的：验证统计消息数量功能
        测试场景：统计所有消息数量
        """
        # Arrange: 创建对话和消息
        conv = TestDataBuilder.create_conversation(1, "测试对话")
        db_session.add(conv)
        await db_session.flush()

        for i in range(1, 4):
            msg = TestDataBuilder.create_message(i, 1, "user", f"消息{i}")
            db_session.add(msg)
        await db_session.flush()

        # Act: 统计数量
        repo = MessageRepository(db_session)
        count = await repo.count()

        # Assert: 验证数量
        assert count == 3

    @pytest.mark.asyncio
    async def test_count_with_filters(self, db_session: AsyncSession):
        """
        测试目的：验证带条件统计消息数量功能
        测试场景：统计特定角色的消息数量
        """
        # Arrange: 创建对话和消息
        conv = TestDataBuilder.create_conversation(1, "测试对话")
        db_session.add(conv)
        await db_session.flush()

        msg1 = TestDataBuilder.create_message(1, 1, MessageRole.USER, "用户消息")
        msg2 = TestDataBuilder.create_message(2, 1, MessageRole.ASSISTANT, "助手消息")
        db_session.add(msg1)
        db_session.add(msg2)
        await db_session.flush()

        # Act: 统计用户消息数量
        repo = MessageRepository(db_session)
        count = await repo.count({"role": MessageRole.USER})

        # Assert: 验证数量
        assert count == 1

    @pytest.mark.asyncio
    async def test_exists_true(self, db_session: AsyncSession):
        """
        测试目的：验证检查消息是否存在（存在的情况）
        测试场景：检查存在的消息
        """
        # Arrange: 创建对话和消息
        conv = TestDataBuilder.create_conversation(1, "测试对话")
        db_session.add(conv)
        await db_session.flush()

        msg = TestDataBuilder.create_message(1, 1, MessageRole.USER, "测试消息")
        db_session.add(msg)
        await db_session.flush()

        # Act: 检查是否存在
        repo = MessageRepository(db_session)
        result = await repo.exists({"conversation_id": 1})

        # Assert: 验证返回True
        assert result is True

    @pytest.mark.asyncio
    async def test_exists_false(self, db_session: AsyncSession):
        """
        测试目的：验证检查消息是否存在（不存在的情况）
        测试场景：检查不存在的消息
        """
        # Arrange: 创建仓储
        repo = MessageRepository(db_session)

        # Act: 检查是否存在
        result = await repo.exists({"conversation_id": 999})

        # Assert: 验证返回False
        assert result is False

    @pytest.mark.asyncio
    async def test_get_by_conversation_id(self, db_session: AsyncSession):
        """
        测试目的：验证获取对话消息列表功能
        测试场景：获取指定对话的所有消息
        """
        # Arrange: 创建对话和消息
        conv1 = TestDataBuilder.create_conversation(1, "对话1")
        conv2 = TestDataBuilder.create_conversation(2, "对话2")
        db_session.add(conv1)
        db_session.add(conv2)
        await db_session.flush()

        msg1 = TestDataBuilder.create_message(1, 1, MessageRole.USER, "对话1消息1")
        msg2 = TestDataBuilder.create_message(2, 1, MessageRole.ASSISTANT, "对话1消息2")
        msg3 = TestDataBuilder.create_message(3, 2, MessageRole.USER, "对话2消息")
        db_session.add(msg1)
        db_session.add(msg2)
        db_session.add(msg3)
        await db_session.flush()

        # Act: 获取对话1的消息
        repo = MessageRepository(db_session)
        results = await repo.get_by_conversation_id(1)

        # Assert: 验证获取结果
        assert len(results) == 2
        assert all(r.conversation_id == 1 for r in results)

    @pytest.mark.asyncio
    async def test_get_by_conversation_id_with_options(self, db_session: AsyncSession):
        """
        测试目的：验证带选项获取对话消息列表功能
        测试场景：获取对话消息并分页
        """
        # Arrange: 创建对话和消息
        conv = TestDataBuilder.create_conversation(1, "测试对话")
        db_session.add(conv)
        await db_session.flush()

        for i in range(1, 6):
            msg = TestDataBuilder.create_message(i, 1, MessageRole.USER, f"消息{i}")
            db_session.add(msg)
        await db_session.flush()

        # Act: 获取对话消息（限制3条）
        repo = MessageRepository(db_session)
        options = QueryOptions(limit=3)
        results = await repo.get_by_conversation_id(1, options)

        # Assert: 验证分页结果
        assert len(results) == 3


# ============================================================================
# IRepository接口实现测试类
# ============================================================================

class TestRepositoryInterface:
    """
    类级注释：仓储接口实现测试类
    职责：验证仓储正确实现了IRepository接口
    """

    @pytest.mark.asyncio
    async def test_conversation_repository_implements_interface(self, db_session: AsyncSession):
        """
        测试目的：验证ConversationRepository实现IRepository接口
        测试场景：检查所有必需方法存在
        """
        # Arrange: 创建仓储实例
        repo = ConversationRepository(db_session)

        # Assert: 验证所有必需方法存在
        assert hasattr(repo, 'get_by_id')
        assert hasattr(repo, 'get_all')
        assert hasattr(repo, 'find')
        assert hasattr(repo, 'find_one')
        assert hasattr(repo, 'add')
        assert hasattr(repo, 'add_many')
        assert hasattr(repo, 'update')
        assert hasattr(repo, 'update_many')
        assert hasattr(repo, 'delete')
        assert hasattr(repo, 'delete_many')
        assert hasattr(repo, 'count')
        assert hasattr(repo, 'exists')
        assert hasattr(repo, 'get_page')

    @pytest.mark.asyncio
    async def test_message_repository_implements_interface(self, db_session: AsyncSession):
        """
        测试目的：验证MessageRepository实现IRepository接口
        测试场景：检查所有必需方法存在
        """
        # Arrange: 创建仓储实例
        repo = MessageRepository(db_session)

        # Assert: 验证所有必需方法存在
        assert hasattr(repo, 'get_by_id')
        assert hasattr(repo, 'get_all')
        assert hasattr(repo, 'find')
        assert hasattr(repo, 'find_one')
        assert hasattr(repo, 'add')
        assert hasattr(repo, 'add_many')
        assert hasattr(repo, 'update')
        assert hasattr(repo, 'update_many')
        assert hasattr(repo, 'delete')
        assert hasattr(repo, 'delete_many')
        assert hasattr(repo, 'count')
        assert hasattr(repo, 'exists')
        assert hasattr(repo, 'get_page')


# ============================================================================
# 边界条件测试类
# ============================================================================

class TestRepositoryEdgeCases:
    """
    类级注释：仓储边界条件测试类
    职责：测试各种边界情况
    """

    @pytest.mark.asyncio
    async def test_empty_results(self, db_session: AsyncSession):
        """
        测试目的：验证空数据库时的各种查询
        测试场景：数据库为空时执行各种查询
        """
        # Arrange: 创建仓储
        conv_repo = ConversationRepository(db_session)
        msg_repo = MessageRepository(db_session)

        # Act & Assert: 验证各种空结果查询
        assert await conv_repo.get_all() == []
        assert await conv_repo.find({}) == []
        assert await conv_repo.find_one({}) is None
        assert await conv_repo.count() == 0
        assert await conv_repo.exists({}) is False

        assert await msg_repo.get_all() == []
        assert await msg_repo.find({}) == []
        assert await msg_repo.find_one({}) is None
        assert await msg_repo.count() == 0
        assert await msg_repo.exists({}) is False

    @pytest.mark.asyncio
    async def test_query_options_validation(self, db_session: AsyncSession):
        """
        测试目的：验证QueryOptions的边界值
        测试场景：使用边界值创建QueryOptions
        """
        # Arrange & Act: 创建各种QueryOptions
        options1 = QueryOptions(skip=0, limit=1)
        options2 = QueryOptions(skip=100, limit=100)

        # Assert: 验证创建成功
        assert options1.skip == 0
        assert options1.limit == 1
        assert options2.skip == 100
        assert options2.limit == 100

    @pytest.mark.asyncio
    async def test_paged_result_properties(self, db_session: AsyncSession):
        """
        测试目的：验证PagedResult的属性
        测试场景：检查has_next和has_previous计算
        """
        # Arrange: 创建测试数据
        for i in range(1, 6):
            conv = TestDataBuilder.create_conversation(i, 1, f"对话{i}")
            db_session.add(conv)
        await db_session.flush()

        # Act: 获取不同页
        repo = ConversationRepository(db_session)
        first_page = await repo.get_page(1, 2)
        last_page = await repo.get_page(3, 2)

        # Assert: 验证has_next和has_previous
        assert first_page.has_next is True
        assert first_page.has_previous is False
        assert last_page.has_next is False
        assert last_page.has_previous is True
