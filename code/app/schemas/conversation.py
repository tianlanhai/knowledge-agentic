"""
上海宇羲伏天智能科技有限公司出品

文件级注释：对话持久化相关的 Pydantic 模型
内部逻辑：定义会话、消息、来源引用、Token统计的请求和响应模型
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from enum import Enum
from decimal import Decimal


# ============================================================================
# 枚举类型
# ============================================================================

class MessageRole(str, Enum):
    """
    类级注释：消息角色枚举
    属性：
        USER: 用户消息
        ASSISTANT: AI助手消息
        SYSTEM: 系统消息
    """
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# ============================================================================
# 响应模型
# ============================================================================

class MessageSourceResponse(BaseModel):
    """
    类级注释：来源引用响应模型
    属性：
        id: 来源ID
        document_id: 文档ID
        chunk_id: 片段ID
        file_name: 文件名
        text_segment: 文本片段
        score: 相关度评分
        position: 排序位置
    """
    id: int
    document_id: Optional[int] = None
    chunk_id: Optional[str] = None
    file_name: str
    text_segment: str
    score: Optional[int] = None
    position: int

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """
    类级注释：消息响应模型
    属性：
        id: 消息ID
        conversation_id: 会话ID
        role: 消息角色
        content: 消息内容
        streaming_state: 流式状态
        tokens_count: Token数量
        created_at: 创建时间
        sources: 来源引用列表
    """
    id: int
    conversation_id: int
    role: MessageRole
    content: str
    streaming_state: Optional[str] = None
    tokens_count: int = 0
    created_at: datetime
    sources: List[MessageSourceResponse] = []

    class Config:
        from_attributes = True


class TokenUsageResponse(BaseModel):
    """
    类级注释：Token统计响应模型
    属性：
        id: Token记录ID
        model_name: 模型名称
        prompt_tokens: 输入Token数
        completion_tokens: 输出Token数
        total_tokens: 总Token数
        prompt_cost: 输入成本（元）
        completion_cost: 输出成本（元）
        total_cost: 总成本（元）
    """
    id: int
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    prompt_cost: Decimal
    completion_cost: Decimal
    total_cost: Decimal

    # 属性：Pydantic v2 配置，允许使用 model_ 前缀的字段
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)


class ConversationResponse(BaseModel):
    """
    类级注释：会话响应模型
    属性：
        id: 会话ID
        title: 会话标题
        model_name: 模型名称
        use_agent: 是否启用智能体
        total_tokens: 总Token消耗
        total_cost: 总成本
        created_at: 创建时间
        updated_at: 更新时间
        message_count: 消息数量
        last_message: 最后一条消息预览
    """
    id: int
    title: str
    model_name: Optional[str] = None
    use_agent: bool
    total_tokens: int = 0
    total_cost: Decimal = Decimal("0")
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    last_message: Optional[str] = None

    # 属性：Pydantic v2 配置，允许使用 model_ 前缀的字段
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)


class ConversationDetailResponse(BaseModel):
    """
    类级注释：会话详情响应模型（包含完整消息列表）
    属性：
        conversation: 会话信息
        messages: 消息列表
    """
    conversation: ConversationResponse
    messages: List[MessageResponse]


class MessageListResponse(BaseModel):
    """
    类级注释：消息列表响应模型
    属性：
        messages: 消息列表
        total: 总数
        has_more: 是否有更多
    """
    messages: List[MessageResponse]
    total: int
    has_more: bool


class ConversationListResponse(BaseModel):
    """
    类级注释：会话列表响应模型
    属性：
        conversations: 会话列表
        total: 总数
        has_more: 是否有更多
    """
    conversations: List[ConversationResponse]
    total: int
    has_more: bool


# ============================================================================
# 请求模型
# ============================================================================

class CreateConversationRequest(BaseModel):
    """
    类级注释：创建会话请求模型
    属性：
        title: 会话标题（可选，默认"新对话"）
        model_name: 模型名称（可选）
        use_agent: 是否启用智能体（可选）
    """
    title: Optional[str] = "新对话"
    model_name: Optional[str] = None
    use_agent: bool = False

    # 属性：Pydantic v2 配置，允许使用 model_ 前缀的字段
    model_config = ConfigDict(protected_namespaces=())


class UpdateConversationRequest(BaseModel):
    """
    类级注释：更新会话请求模型
    属性：
        title: 新标题
    """
    title: str


class SendMessageRequest(BaseModel):
    """
    类级注释：发送消息请求模型
    属性：
        content: 消息内容
        use_agent: 是否启用智能体
        stream: 是否流式返回
    """
    content: str = Field(..., min_length=1, max_length=10000, description="消息内容")
    use_agent: bool = False
    stream: bool = False
