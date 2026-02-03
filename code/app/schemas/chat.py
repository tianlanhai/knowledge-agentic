"""
上海宇羲伏天智能科技有限公司出品

文件级注释：对话与问答相关的 Pydantic 模型
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ChatMessage(BaseModel):
    """
    类级注释：对话消息模型
    属性：
        role: 角色 (user/assistant/system)
        content: 消息内容
    """
    role: str
    content: str

class ChatRequest(BaseModel):
    """
    类级注释：对话请求模型
    属性：
        message: 用户当前输入
        history: 对话历史列表
        use_agent: 是否启用 Agent 模式
        stream: 是否启用流式返回
        formatting_options: 文档格式化选项
    """
    message: str
    history: Optional[List[ChatMessage]] = []
    use_agent: bool = False
    stream: bool = False
    formatting_options: Optional[Dict[str, Any]] = None

class SourceInfo(BaseModel):
    """
    类级注释：引用来源信息模型
    属性：
        doc_id: 文档 ID
        file_name: 文件名
        text_segment: 文本片段内容
        score: 相关度评分
    """
    doc_id: int
    file_name: str
    text_segment: str
    score: Optional[float] = None

class ChatResponse(BaseModel):
    """
    类级注释：对话响应模型
    属性：
        answer: 模型生成的回答内容
        sources: 引用来源列表
        formatting_applied: 是否应用了格式化
    """
    answer: str
    sources: List[SourceInfo]
    formatting_applied: bool = False

class SourceDetail(BaseModel):
    """
    类级注释：详细来源信息模型，用于 /sources 接口
    属性：
        doc_id: 文档 ID
        file_name: 文件名
        content: 完整片段内容
        score: 相关度评分
        formatted_content: 格式化后的内容
    """
    doc_id: int
    file_name: str
    content: str
    score: Optional[float] = None
    formatted_content: Optional[str] = None

class SummaryRequest(BaseModel):
    """
    类级注释：文档总结请求模型
    属性：
        doc_id: 需要总结的文档 ID
    """
    doc_id: int

class ComparisonRequest(BaseModel):
    """
    类级注释：文档对比请求模型
    属性：
        doc_ids: 需要对比的文档 ID 列表
    """
    doc_ids: List[int]

class SummaryResponse(BaseModel):
    """
    类级注释：总结/对比结果响应模型
    属性：
        result: 总结或对比生成的文本内容
    """
    result: str

