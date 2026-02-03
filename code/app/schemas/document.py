"""
上海宇羲伏天智能科技有限公司出品

文件级注释：文档管理相关的 Pydantic 模型
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, Field

class DocumentBase(BaseModel):
    """
    类级注释：文档基础模型
    """
    file_name: str = Field(..., validation_alias="name")
    source_type: str = Field(..., validation_alias="type")
    tags: Optional[List[str]] = None

class DocumentRead(DocumentBase):
    """
    类级注释：文档读取响应模型
    属性：
        id: 文档唯一标识
        created_at: 创建时间
        chunk_count: 文档片段数量
    """
    id: int
    created_at: datetime
    chunk_count: int = 0

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }

class DocumentListResponse(BaseModel):
    """
    类级注释：文档列表响应模型
    属性：
        items: 文档对象列表
        total: 总数
        skip: 跳过数量
        limit: 返回限制
    """
    items: List[DocumentRead]
    total: int
    skip: int = 0
    limit: int = 10

