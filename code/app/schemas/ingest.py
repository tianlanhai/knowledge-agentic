"""
上海宇羲伏天智能科技有限公司出品

文件级注释：知识摄入相关的 Pydantic 模型
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

class TaskStatusEnum(str, Enum):
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

class IngestResponse(BaseModel):
    """
    类级注释：摄入接口响应模型
    属性：
        document_id: 文档唯一标识
        status: 处理状态 (processing/completed/failed)
        chunk_count: 切分出的片段数量
    """
    document_id: int
    status: str
    chunk_count: int

class DBIngestRequest(BaseModel):
    """
    类级注释：数据库摄入请求模型
    属性：
        connection_uri: 数据库连接字符串 (如 sqlite:///test.db)
        table_name: 要同步的表名
        content_column: 包含知识内容的列名
        metadata_columns: 可选的其他列名列表，作为元数据存入
    """
    connection_uri: str
    table_name: str
    content_column: str
    metadata_columns: Optional[List[str]] = None

class URLIngestRequest(BaseModel):
    """
    类级注释：网页摄入请求模型
    属性：
        url: 目标网页的完整 URL 地址
        tags: 可选的元数据标签
    """
    url: str
    tags: Optional[List[str]] = None

class TaskResponse(BaseModel):
    """
    类级注释：任务响应模型
    属性：
        id: 任务ID
        file_name: 文件名
        status: 任务状态
        progress: 处理进度 (0-100)
        error_message: 错误信息
        document_id: 关联文档ID
        created_at: 创建时间
        updated_at: 更新时间
    """
    id: int
    file_name: str
    status: TaskStatusEnum
    progress: int
    error_message: Optional[str] = None
    document_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

class TaskListResponse(BaseModel):
    """
    类级注释：任务列表响应模型
    属性：
        items: 任务列表
        total: 总数
    """
    items: List[TaskResponse]
    total: int

