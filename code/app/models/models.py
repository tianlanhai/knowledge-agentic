"""
上海宇羲伏天智能科技有限公司出品

文件级注释：数据库基础配置与模型定义
内部逻辑：定义 SQLAlchemy 基础类和文档元数据模型，符合数据库三原则
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from app.utils.timezone_helper import get_local_time
import enum

# 变量：SQLAlchemy 模型基础类
Base = declarative_base()

class TaskStatus(enum.Enum):
    """
    类级注释：任务状态枚举
    属性：
        PENDING: 等待处理
        PROCESSING: 处理中
        COMPLETED: 已完成
        FAILED: 失败
    """
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Document(Base):
    """
    类级注释：文档元数据模型，存储上传或抓取的文档基本信息
    属性：
        id: 主键，唯一标识
        file_name: 文件名或网页标题
        file_path: 文件物理路径或来源 URL
        file_hash: 内容哈希值，用于版本校验和去重
        source_type: 来源类型 (FILE, WEB, DB)
        created_at: 摄入时间
        updated_at: 最后更新时间
    索引：在 file_hash 上建立索引以加速重复性校验
    """
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    file_name = Column(String(255), nullable=False, comment="文件名或网页标题")
    file_path = Column(String(512), nullable=False, comment="文件物理路径或来源 URL")
    file_hash = Column(String(64), nullable=False, unique=True, index=True, comment="内容哈希值")
    source_type = Column(String(50), nullable=False, comment="来源类型 (FILE, WEB, DB)")
    tags = Column(String(512), nullable=True, comment="标签列表 (JSON 字符串存储)")
    # 属性：时间戳（本地时间）
    created_at = Column(DateTime, default=get_local_time, comment="创建时间(本地时间)")
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time, comment="更新时间(本地时间)")

    # 关系：一个文档对应多个向量片段映射
    mappings = relationship("VectorMapping", back_populates="document", cascade="all, delete-orphan")

class VectorMapping(Base):
    """
    类级注释：向量索引映射模型，将文档片段与向量库中的 ID 关联
    属性：
        id: 主键
        document_id: 关联的文档 ID
        chunk_id: 向量库中的 Chunk 唯一标识
        chunk_content: 文档片段内容的备份，用于快速回显
    外键约束：关联到 documents 表的 id 字段
    """
    __tablename__ = "vector_mappings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, comment="关联文档ID")
    chunk_id = Column(String(100), nullable=False, index=True, comment="向量库中的Chunk ID")
    chunk_content = Column(Text, nullable=False, comment="片段内容备份")

    # 关系：关联回文档对象
    document = relationship("Document", back_populates="mappings")

class IngestTask(Base):
    """
    类级注释：文件摄入任务模型，用于异步处理文件上传
    属性：
        id: 主键，任务唯一标识
        file_name: 文件名
        file_path: 文件物理路径
        file_hash: 文件内容哈希值
        source_type: 来源类型 (FILE, WEB, DB)
        tags: 标签列表 (JSON 字符串存储)
        status: 任务状态 (pending, processing, completed, failed)
        progress: 处理进度 (0-100)
        error_message: 错误信息（如果失败）
        document_id: 关联的文档 ID（完成后）
        created_at: 任务创建时间
        updated_at: 任务更新时间
    索引：在 status 上建立索引以加速状态查询
    外键约束：关联到 documents 表的 id 字段
    """
    __tablename__ = "ingest_tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="任务ID")
    file_name = Column(String(255), nullable=False, comment="文件名或网页标题")
    file_path = Column(String(512), nullable=True, comment="文件物理路径或来源 URL")
    file_hash = Column(String(64), nullable=True, comment="内容哈希值")
    source_type = Column(String(50), nullable=False, comment="来源类型 (FILE, WEB, DB)")
    tags = Column(String(512), nullable=True, comment="标签列表 (JSON 字符串存储)")
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False, index=True, comment="任务状态")
    progress = Column(Integer, default=0, nullable=False, comment="处理进度 (0-100)")
    error_message = Column(Text, nullable=True, comment="错误信息")
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, comment="关联文档ID")
    # 属性：时间戳（本地时间）
    created_at = Column(DateTime, default=get_local_time, comment="创建时间(本地时间)")
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time, comment="更新时间(本地时间)")

