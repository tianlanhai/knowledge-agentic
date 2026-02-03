# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：错误处理模块
内部逻辑：统一管理错误处理相关的类和函数
设计模式：门面模式 - 提供简单的导入接口
职责：集中导出所有错误处理相关的公共接口
"""

# 内部逻辑：从 error_chain 导入错误处理器相关类和函数
from .error_chain import (
    ErrorHandler,
    SensitiveDataErrorHandler,
    LLMErrorHandler,
    DatabaseErrorHandler,
    ValidationErrorHandler,
    ErrorChainBuilder,
    create_default_error_chain,
    get_default_chain,
)

# 内部逻辑：从 decorators 导入装饰器相关函数
from .decorators import (
    with_error_handling,
    with_retry,
    catch_and_return,
    log_execution,
)

# 内部逻辑：从 security 导入安全错误处理相关函数
from .security import (
    SecurityErrorHandler,
    get_security_handler,
)

# 内部变量：导出所有公共接口
__all__ = [
    # 错误处理器
    'ErrorHandler',
    'SensitiveDataErrorHandler',
    'LLMErrorHandler',
    'DatabaseErrorHandler',
    'ValidationErrorHandler',
    'ErrorChainBuilder',
    'create_default_error_chain',
    'get_default_chain',
    # 装饰器
    'with_error_handling',
    'with_retry',
    'catch_and_return',
    'log_execution',
    # 安全错误处理
    'SecurityErrorHandler',
    'get_security_handler',
]

# 内部变量：模块版本
__version__ = '1.0.0'
