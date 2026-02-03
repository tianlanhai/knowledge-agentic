# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：仓储模块导出文件
内部逻辑：统一导出所有仓储相关的类和接口
"""

from .base import (
    IRepository,
    CachedRepository,
    QueryOptions,
    PagedResult,
    QueryOrder,
)

from .conversation_repository import (
    ConversationRepository,
    MessageRepository,
)

# 导出基础接口
__all__ = [
    'IRepository',
    'CachedRepository',
    'QueryOptions',
    'PagedResult',
    'QueryOrder',
]

# 导出具体实现
__all__ += [
    'ConversationRepository',
    'MessageRepository',
]
