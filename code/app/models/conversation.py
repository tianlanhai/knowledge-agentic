"""
上海宇羲伏天智能科技有限公司出品

文件级注释：对话持久化模型定义
内部逻辑：定义会话、消息、来源引用、Token统计四张核心表，支持多会话管理和历史记录
设计原则：符合数据库三原则，建立适当的索引和外键约束
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SQLEnum, Numeric, Index
from sqlalchemy.orm import relationship
from app.models.models import Base
from app.utils.timezone_helper import get_local_time
import enum


class MessageRole(enum.Enum):
    """
    类级注释：消息角色枚举
    属性：
        USER: 用户消息
        ASSISTANT: AI助手回复
        SYSTEM: 系统提示消息
    """
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Conversation(Base):
    """
    类级注释：对话会话模型，表示一组完整的对话
    属性：
        id: 主键，唯一标识会话
        title: 会话标题（自动生成或用户自定义）
        model_name: 使用的模型名称（如 deepseek-r1:8b）
        use_agent: 是否启用智能体模式
        total_tokens: 总Token消耗（统计字段）
        total_cost: 总成本（元）
        created_at: 会话创建时间
        updated_at: 会话最后更新时间
        message_count: 消息计数（缓存字段，提升查询性能）
    索引：
        - idx_updated_at: 支持按更新时间倒序查询会话列表
    关系：
        - messages: 一对多关系，关联该会话的所有消息
        - token_usages: 一对多关系，关联该会话的所有Token记录
    """
    __tablename__ = "conversations"

    # 属性：主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="会话ID")

    # 属性：基本信息
    title = Column(String(255), nullable=False, default="新对话", comment="会话标题")
    model_name = Column(String(100), nullable=True, comment="使用的模型名称")
    use_agent = Column(Integer, default=0, nullable=False, comment="是否启用智能体(0/1)")

    # 属性：统计信息
    total_tokens = Column(Integer, default=0, nullable=False, comment="总Token消耗")
    total_cost = Column(Numeric(10, 4), default=0, nullable=False, comment="总成本（元）")

    # 属性：时间戳（本地时间）
    created_at = Column(DateTime, default=get_local_time, nullable=False, comment="创建时间(本地时间)")
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time, nullable=False, comment="更新时间(本地时间)")

    # 属性：缓存字段
    message_count = Column(Integer, default=0, nullable=False, comment="消息数量(缓存)")

    # 关系：一个会话包含多条消息
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at.asc()"
    )

    # 关系：一个会话包含多条Token记录
    token_usages = relationship(
        "TokenUsage",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )

    # 复合索引：支持按更新时间倒序查询
    __table_args__ = (
        Index('idx_updated_at', 'updated_at'),
    )


class Message(Base):
    """
    类级注释：对话消息模型，存储单条对话内容
    属性：
        id: 主键
        conversation_id: 关联的会话ID
        role: 消息角色（用户/助手/系统）
        content: 消息内容文本
        streaming_state: 流式状态（idle/streaming/completed）
        tokens_count: Token数量（统计字段）
        created_at: 消息创建时间
    外键约束：
        - fk_message_conversation: 关联到conversations表，级联删除
    索引：
        - idx_conversation_created: 支持按会话查询消息并按时间排序
    关系：
        - conversation: 多对一关系，所属会话
        - sources: 一对多关系，关联的来源引用
        - token_usage: 一对一关系，关联的Token记录
    """
    __tablename__ = "messages"

    # 属性：主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="消息ID")

    # 属性：外键
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="关联会话ID"
    )

    # 属性：消息内容
    role = Column(
        SQLEnum(MessageRole),
        default=MessageRole.USER,
        nullable=False,
        comment="消息角色"
    )
    content = Column(Text, nullable=False, comment="消息内容")
    streaming_state = Column(String(20), default="idle", nullable=True, comment="流式状态")

    # 属性：统计信息
    tokens_count = Column(Integer, default=0, nullable=False, comment="Token数量")

    # 属性：时间戳（本地时间）
    created_at = Column(DateTime, default=get_local_time, nullable=False, comment="创建时间(本地时间)")

    # 关系：多对一关联到会话
    conversation = relationship("Conversation", back_populates="messages")

    # 关系：一条消息可关联多个来源引用
    sources = relationship(
        "MessageSource",
        back_populates="message",
        cascade="all, delete-orphan",
        order_by="MessageSource.position.asc()"
    )

    # 关系：一条消息关联一条Token记录
    token_usage = relationship(
        "TokenUsage",
        back_populates="message",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # 复合索引：支持快速查询某会话的所有消息
    __table_args__ = (
        Index('idx_conversation_created', 'conversation_id', 'created_at'),
    )


class MessageSource(Base):
    """
    类级注释：消息来源引用模型，关联消息与文档来源
    属性：
        id: 主键
        message_id: 关联的消息ID
        document_id: 引用的文档ID
        chunk_id: 文档片段ID（向量库中的ID）
        file_name: 文件名（冗余存储，提升查询性能）
        text_segment: 引用的文本片段内容
        score: 相关度评分
        position: 排序位置（按相关度排序）
    外键约束：
        - fk_source_message: 关联到messages表，级联删除
        - fk_source_document: 关联到documents表，置空删除
    索引：
        - idx_message_position: 支持按消息查询来源并按位置排序
    关系：
        - message: 多对一关系，所属消息
    """
    __tablename__ = "message_sources"

    # 属性：主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="来源ID")

    # 属性：外键
    message_id = Column(
        Integer,
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="关联消息ID"
    )
    document_id = Column(
        Integer,
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        comment="引用文档ID"
    )

    # 属性：来源信息
    chunk_id = Column(String(100), nullable=True, comment="向量库中的Chunk ID")
    file_name = Column(String(255), nullable=False, comment="文件名(冗余存储)")
    text_segment = Column(Text, nullable=False, comment="引用的文本片段")
    score = Column(Integer, nullable=True, comment="相关度评分(0-100)")
    position = Column(Integer, default=0, nullable=False, comment="排序位置")

    # 关系：多对一关联到消息
    message = relationship("Message", back_populates="sources")

    # 复合索引
    __table_args__ = (
        Index('idx_message_position', 'message_id', 'position'),
    )


class TokenUsage(Base):
    """
    类级注释：Token使用统计模型，记录每次LLM调用的Token消耗和成本
    属性：
        id: 主键
        conversation_id: 关联的会话ID
        message_id: 关联的消息ID
        model_name: 模型名称
        prompt_tokens: 输入Token数
        completion_tokens: 输出Token数
        total_tokens: 总Token数
        prompt_cost: 输入成本（元）
        completion_cost: 输出成本（元）
        total_cost: 总成本（元）
        created_at: 创建时间
    外键约束：
        - fk_token_conversation: 关联到conversations表，级联删除
        - fk_token_message: 关联到messages表，级联删除
    索引：
        - idx_conversation_token: 支持按会话查询Token统计
        - idx_message_token: 支持按消息查询Token记录
    关系：
        - conversation: 多对一关系，所属会话
        - message: 多对一关系，所属消息
    """
    __tablename__ = "token_usage"

    # 属性：主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="Token记录ID")

    # 属性：外键
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="关联会话ID"
    )
    message_id = Column(
        Integer,
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="关联消息ID"
    )

    # 属性：模型信息
    model_name = Column(String(100), nullable=False, comment="模型名称")

    # 属性：Token统计
    prompt_tokens = Column(Integer, default=0, nullable=False, comment="输入Token数")
    completion_tokens = Column(Integer, default=0, nullable=False, comment="输出Token数")
    total_tokens = Column(Integer, default=0, nullable=False, comment="总Token数")

    # 属性：成本统计（单位：元）
    prompt_cost = Column(Numeric(10, 6), default=0, nullable=False, comment="输入成本（元）")
    completion_cost = Column(Numeric(10, 6), default=0, nullable=False, comment="输出成本（元）")
    total_cost = Column(Numeric(10, 6), default=0, nullable=False, comment="总成本（元）")

    # 属性：时间戳（本地时间）
    created_at = Column(DateTime, default=get_local_time, nullable=False, comment="创建时间(本地时间)")

    # 关系：多对一关联到会话
    conversation = relationship("Conversation", back_populates="token_usages")

    # 关系：多对一关联到消息
    message = relationship("Message", back_populates="token_usage")

    # 复合索引
    __table_args__ = (
        Index('idx_conversation_token', 'conversation_id'),
        Index('idx_message_token', 'message_id'),
    )
