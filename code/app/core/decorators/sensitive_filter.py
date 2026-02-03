# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：敏感信息过滤装饰器模块
内部逻辑：使用装饰器模式统一处理敏感信息过滤
设计模式：装饰器模式（Decorator Pattern）
设计原则：开闭原则（OCP）、单一职责原则（SRP）

实现说明：
    - 提供装饰器函数，自动过滤函数返回值中的敏感信息
    - 支持配置过滤字段和启用状态
    - 可用于异步函数和同步函数
"""

from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar
from loguru import logger

T = TypeVar('T')


def with_sensitive_filter(
    filter_fields: Optional[List[str]] = None,
    enabled: Optional[bool] = None
) -> Callable:
    """
    函数级注释：敏感信息过滤装饰器
    内部逻辑：自动过滤函数返回值中的敏感信息
    设计模式：装饰器模式

    使用示例：
        @with_sensitive_filter(filter_fields=['answer'])
        async def generate_response(prompt: str) -> str:
            return llm.generate(prompt)

    参数：
        filter_fields - 需要过滤的字段列表
        enabled - 是否启用过滤（None则从配置读取）
    返回值：装饰器函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            # 内部逻辑：执行原函数
            result = await func(*args, **kwargs)

            # 内部逻辑：检查是否启用过滤
            should_filter = _should_enable_filter(enabled)
            if not should_filter:
                return result

            # 内部逻辑：根据返回值类型进行过滤
            return _filter_result(result, filter_fields)

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            # 内部逻辑：执行原函数
            result = func(*args, **kwargs)

            # 内部逻辑：检查是否启用过滤
            should_filter = _should_enable_filter(enabled)
            if not should_filter:
                return result

            # 内部逻辑：根据返回值类型进行过滤
            return _filter_result(result, filter_fields)

        # 内部逻辑：返回对应的包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def _should_enable_filter(explicit_enabled: Optional[bool]) -> bool:
    """
    函数级注释：判断是否应该启用过滤
    参数：
        explicit_enabled - 显式指定的启用状态
    返回值：是否启用
    """
    # 内部逻辑：如果显式指定，则使用指定值
    if explicit_enabled is not None:
        return explicit_enabled

    # 内部逻辑：否则从配置读取
    try:
        from app.core.config import settings
        return settings.ENABLE_SENSITIVE_DATA_FILTER
    except ImportError:
        return False


def _filter_result(result: Any, filter_fields: Optional[List[str]]) -> Any:
    """
    函数级注释：过滤结果中的敏感信息
    参数：
        result - 函数返回值
        filter_fields - 需要过滤的字段列表
    返回值：过滤后的结果
    """
    from app.utils.sensitive_data_filter import get_filter

    try:
        filter_instance = get_filter()
    except Exception as e:
        logger.warning(f"获取敏感信息过滤器失败: {e}")
        return result

    # 内部逻辑：根据返回值类型进行过滤
    if isinstance(result, dict):
        return _filter_dict(result, filter_instance, filter_fields)
    elif isinstance(result, str):
        filtered, _ = filter_instance.filter_all(result)
        return filtered
    elif isinstance(result, list):
        return [_filter_item(item, filter_instance, filter_fields) for item in result]
    else:
        return result


def _filter_dict(data: Dict, filter_instance, filter_fields: Optional[List[str]]) -> Dict:
    """
    函数级注释：过滤字典中的敏感字段
    参数：
        data - 数据字典
        filter_instance - 过滤器实例
        filter_fields - 需要过滤的字段列表
    返回值：过滤后的字典
    """
    result = {}

    for key, value in data.items():
        # 内部逻辑：如果指定了字段列表，且当前字段不在列表中，则跳过
        if filter_fields and key not in filter_fields:
            result[key] = value
        elif isinstance(value, str):
            filtered, _ = filter_instance.filter_all(value)
            result[key] = filtered
        elif isinstance(value, dict):
            result[key] = _filter_dict(value, filter_instance, filter_fields)
        elif isinstance(value, list):
            result[key] = [_filter_item(item, filter_instance, filter_fields) for item in value]
        else:
            result[key] = value

    return result


def _filter_item(item: Any, filter_instance, filter_fields: Optional[List[str]]) -> Any:
    """
    函数级注释：过滤单个项
    参数：
        item - 数据项
        filter_instance - 过滤器实例
        filter_fields - 需要过滤的字段列表
    返回值：过滤后的项
    """
    if isinstance(item, str):
        filtered, _ = filter_instance.filter_all(item)
        return filtered
    elif isinstance(item, dict):
        return _filter_dict(item, filter_instance, filter_fields)
    elif isinstance(item, list):
        return [_filter_item(sub_item, filter_instance, filter_fields) for sub_item in item]
    else:
        return item


class SensitiveDataFilterDecorator:
    """
    类级注释：敏感信息过滤装饰器类
    设计模式：装饰器模式 - 类形式
    职责：提供更灵活的敏感信息过滤装饰器
    """

    def __init__(
        self,
        filter_fields: Optional[List[str]] = None,
        enabled: Optional[bool] = None
    ):
        """
        函数级注释：初始化装饰器
        参数：
            filter_fields - 需要过滤的字段列表
            enabled - 是否启用过滤
        """
        # 内部变量：配置
        self.filter_fields = filter_fields
        self.enabled = enabled

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        函数级注释：使对象可调用
        参数：
            func - 被装饰的函数
        返回值：包装后的函数
        """
        return with_sensitive_filter(
            filter_fields=self.filter_fields,
            enabled=self.enabled
        )(func)


# 内部变量：导出所有公共接口
__all__ = [
    'with_sensitive_filter',
    'SensitiveDataFilterDecorator',
]
