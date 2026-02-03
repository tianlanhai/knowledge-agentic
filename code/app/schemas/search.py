"""
上海宇羲伏天智能科技有限公司出品

文件级注释：语义搜索相关的 Pydantic 模型
"""

from pydantic import BaseModel
from typing import List, Optional

class SearchResult(BaseModel):
    """
    类级注释：搜索结果模型
    属性：
        doc_id: 文档 ID
        file_name: 文件名
        source_type: 来源类型（FILE/WEB/DB）
        content: 匹配的文本内容
        score: 相关度评分
    """
    doc_id: int
    file_name: Optional[str] = None
    source_type: Optional[str] = None
    content: str
    score: float




