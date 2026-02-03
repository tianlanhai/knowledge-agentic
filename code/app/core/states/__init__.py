# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：状态模式模块
内部逻辑：实现状态模式，管理对象状态转换
设计模式：状态模式（State Pattern）
设计原则：开闭原则、单一职责原则

@package app.core.states
"""

from app.core.states.document_states import (
    DocumentState,
    UploadedState,
    ParsingState,
    ChunkingState,
    VectorizingState,
    CompletedState,
    FailedState,
    DocumentContext,
    DocumentProcessingException,
)

from app.core.states.chat_states import (
    ChatState,
    IdleState,
    SendingState,
    StreamingState,
    CompletedState as ChatCompletedState,
    ErrorState as ChatErrorState,
    ChatContext,
)

# 内部变量：导出所有公共接口
__all__ = [
    # 文档状态
    'DocumentState',
    'UploadedState',
    'ParsingState',
    'ChunkingState',
    'VectorizingState',
    'CompletedState',
    'FailedState',
    'DocumentContext',
    'DocumentProcessingException',
    # 聊天状态
    'ChatState',
    'IdleState',
    'SendingState',
    'StreamingState',
    'ChatContext',
    'ChatErrorState',
    'ChatCompletedState',
]
