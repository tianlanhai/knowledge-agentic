# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：依赖注入模块导出文件
内部逻辑：统一导出所有依赖注入相关的类型和函数
"""

from .service_container import (
    ServiceContainer,
    ServiceScope,
    ServiceLifetime,
    ServiceDescriptor,
    get_container,
    reset_container,
)

from .service_decorator import (
    InjectMode,
    injectable,
    inject,
    inject_method,
    inject_property,
    singleton,
    scoped,
    transient,
)

# 导出核心类
__all__ = [
    'ServiceContainer',
    'ServiceScope',
    'ServiceLifetime',
    'ServiceDescriptor',
    'get_container',
    'reset_container',
]

# 导出装饰器
__all__ += [
    'InjectMode',
    'injectable',
    'inject',
    'inject_method',
    'inject_property',
    'singleton',
    'scoped',
    'transient',
]
