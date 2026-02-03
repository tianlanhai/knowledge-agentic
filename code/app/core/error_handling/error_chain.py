# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：错误处理责任链模块
内部逻辑：实现责任链模式处理各种错误类型
设计模式：责任链模式 + 模板方法模式
设计原则：单一职责原则（SRP）、开闭原则（OCP）
职责：统一管理错误处理逻辑，消除重复的try-except代码
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, Dict, List
from loguru import logger
import asyncio


class ErrorHandler(ABC):
    """
    类级注释：错误处理器抽象基类
    设计模式：责任链模式 - 处理器接口
    职责：定义错误处理器的通用接口
    """

    # 内部变量：下一个处理器的引用
    _next: Optional['ErrorHandler'] = None

    def set_next(self, handler: 'ErrorHandler') -> 'ErrorHandler':
        """
        函数级注释：设置下一个处理器
        内部逻辑：构建责任链，返回下一个处理器引用以支持链式调用
        参数：
            handler - 下一个错误处理器
        返回值：ErrorHandler - 下一个处理器（支持链式调用）

        使用示例：
            handler1.set_next(handler2).set_next(handler3)
        """
        self._next = handler
        return handler

    def handle(self, error: Exception, context: Dict[str, Any]) -> Any:
        """
        函数级注释：处理错误（模板方法）
        内部逻辑：尝试当前处理 -> 未处理则传递给下一个
        设计模式：模板方法模式 - 定义处理流程骨架
        参数：
            error - 异常对象
            context - 上下文信息（包含重试次数、函数名等）
        返回值：
            - 处理结果（如果错误被处理）
            - None（如果错误未被处理，继续传递）

        使用示例：
            result = handler.handle(exception, {'retry_count': 0})
        """
        # 内部逻辑：尝试当前处理器
        result = self._do_handle(error, context)

        # 内部逻辑：如果已处理或没有下一个处理器，返回结果
        if result is not None or self._next is None:
            return result

        # 内部逻辑：传递给下一个处理器
        return self._next.handle(error, context)

    @abstractmethod
    def _do_handle(self, error: Exception, context: Dict[str, Any]) -> Optional[Any]:
        """
        函数级注释：具体处理逻辑（抽象方法）
        内部逻辑：子类实现具体的错误处理逻辑
        参数：
            error - 异常对象
            context - 上下文信息
        返回值：
            - 处理结果（如果错误被处理）
            - None（如果错误未被当前处理器处理）
        """
        pass

    def can_handle(self, error: Exception) -> bool:
        """
        函数级注释：判断是否可以处理该错误
        内部逻辑：检查错误类型或错误消息特征
        参数：
            error - 异常对象
        返回值：bool - 是否可以处理
        """
        return True


class SensitiveDataErrorHandler(ErrorHandler):
    """
    类级注释：敏感数据过滤错误处理器
    职责：处理敏感信息过滤相关错误
    """

    def _do_handle(self, error: Exception, context: Dict[str, Any]) -> Optional[Any]:
        """
        函数级注释：处理敏感数据过滤错误
        内部逻辑：检测敏感信息错误 -> 返回默认处理结果
        参数：
            error - 异常对象
            context - 上下文信息
        返回值：处理后的文本或默认值
        """
        error_str = str(error).lower()
        # 内部逻辑：检查是否为敏感数据错误
        if any(keyword in error_str for keyword in ['sensitive', '敏感', 'filter', '过滤']):
            logger.warning(f"敏感数据过滤错误: {error}")
            # 内部逻辑：返回上下文中的原始文本或空字符串
            return context.get('text', context.get('default_return', ''))
        return None

    def can_handle(self, error: Exception) -> bool:
        """判断是否为敏感数据错误"""
        error_str = str(error).lower()
        return any(keyword in error_str for keyword in ['sensitive', '敏感', 'filter', '过滤'])


class LLMErrorHandler(ErrorHandler):
    """
    类级注释：LLM调用错误处理器
    职责：处理LLM模型调用相关错误，支持自动重试
    """

    # 内部变量：最大重试次数
    MAX_RETRIES = 3

    def _do_handle(self, error: Exception, context: Dict[str, Any]) -> Optional[Any]:
        """
        函数级注释：处理LLM调用错误
        内部逻辑：检测LLM错误 -> 判断是否重试 -> 返回用户友好消息
        参数：
            error - 异常对象
            context - 上下文信息（包含retry_count）
        返回值：重试标记或用户友好消息
        """
        error_str = str(error).lower()
        # 内部逻辑：检查是否为LLM相关错误
        llm_keywords = ['llm', 'model', 'api', 'timeout', 'rate limit', 'connection']
        if any(keyword in error_str for keyword in llm_keywords):
            logger.error(f"LLM调用错误: {error}")

            # 内部逻辑：获取当前重试次数
            retry_count = context.get('retry_count', 0)

            # 内部逻辑：未达到最大重试次数时返回重试标记
            if retry_count < self.MAX_RETRIES:
                context['retry_count'] = retry_count + 1
                logger.info(f"LLM错误重试 {retry_count + 1}/{self.MAX_RETRIES}")
                return 'RETRY'

            # 内部逻辑：达到最大重试次数，返回用户友好消息
            return '帅哥，AI服务暂时不可用，请稍后重试。'

        return None

    def can_handle(self, error: Exception) -> bool:
        """判断是否为LLM错误"""
        error_str = str(error).lower()
        llm_keywords = ['llm', 'model', 'api', 'timeout', 'rate limit', 'connection']
        return any(keyword in error_str for keyword in llm_keywords)


class DatabaseErrorHandler(ErrorHandler):
    """
    类级注释：数据库操作错误处理器
    职责：处理数据库相关错误
    """

    def _do_handle(self, error: Exception, context: Dict[str, Any]) -> Optional[Any]:
        """
        函数级注释：处理数据库错误
        内部逻辑：检测数据库错误 -> 记录日志 -> 返回用户友好消息
        参数：
            error - 异常对象
            context - 上下文信息
        返回值：用户友好错误消息
        """
        error_str = str(error).lower()
        # 内部逻辑：检查是否为数据库相关错误
        db_keywords = ['database', 'db error', 'sql', 'connection', 'unique constraint']
        if any(keyword in error_str for keyword in db_keywords):
            logger.error(f"数据库错误: {error}")
            return '帅哥，数据库操作失败，请稍后重试。'

        return None

    def can_handle(self, error: Exception) -> bool:
        """判断是否为数据库错误"""
        error_str = str(error).lower()
        db_keywords = ['database', 'db error', 'sql', 'connection']
        return any(keyword in error_str for keyword in db_keywords)


class ValidationErrorHandler(ErrorHandler):
    """
    类级注释：数据验证错误处理器
    职责：处理输入验证相关错误
    """

    def _do_handle(self, error: Exception, context: Dict[str, Any]) -> Optional[Any]:
        """
        函数级注释：处理验证错误
        内部逻辑：检测验证错误 -> 返回具体错误信息
        参数：
            error - 异常对象
            context - 上下文信息
        返回值：验证错误消息
        """
        error_str = str(error).lower()
        # 内部逻辑：检查是否为验证相关错误
        validation_keywords = ['validation', 'invalid', 'missing', 'required', 'format']
        if any(keyword in error_str for keyword in validation_keywords):
            logger.warning(f"数据验证错误: {error}")
            # 内部逻辑：返回原始错误消息
            return f'帅哥，数据验证失败：{str(error)}'

        return None

    def can_handle(self, error: Exception) -> bool:
        """判断是否为验证错误"""
        error_str = str(error).lower()
        validation_keywords = ['validation', 'invalid', 'missing', 'required']
        return any(keyword in error_str for keyword in validation_keywords)


class ErrorChainBuilder:
    """
    类级注释：错误处理链建造者
    设计模式：建造者模式
    职责：构建完整的错误处理责任链
    """

    def __init__(self):
        """初始化建造者"""
        # 内部变量：处理器列表
        self._handlers: List[ErrorHandler] = []
        # 内部变量：链头
        self._chain_head: Optional[ErrorHandler] = None

    def add_handler(self, handler: ErrorHandler) -> 'ErrorChainBuilder':
        """
        函数级注释：添加处理器
        参数：
            handler - 错误处理器
        返回值：建造者自身（支持链式调用）
        """
        self._handlers.append(handler)
        return self

    def build(self) -> Optional[ErrorHandler]:
        """
        函数级注释：构建责任链
        内部逻辑：按添加顺序连接所有处理器
        返回值：责任链头节点
        """
        if not self._handlers:
            return None

        # 内部逻辑：连接处理器形成链
        self._chain_head = self._handlers[0]
        current = self._chain_head
        for handler in self._handlers[1:]:
            current.set_next(handler)
            current = handler

        return self._chain_head

    def reset(self) -> None:
        """重置建造者"""
        self._handlers.clear()
        self._chain_head = None


def create_default_error_chain() -> ErrorHandler:
    """
    函数级注释：创建默认错误处理链
    内部逻辑：按优先级添加各类型处理器
    设计模式：工厂方法模式
    返回值：配置完整的错误处理链

    处理顺序：
    1. 敏感数据错误（最高优先级）
    2. 验证错误
    3. LLM调用错误（支持重试）
    4. 数据库错误（最低优先级）
    """
    return (ErrorChainBuilder()
        .add_handler(SensitiveDataErrorHandler())
        .add_handler(ValidationErrorHandler())
        .add_handler(LLMErrorHandler())
        .add_handler(DatabaseErrorHandler())
        .build())


# 内部变量：默认错误处理链实例（单例）
_default_chain: Optional[ErrorHandler] = None


def get_default_chain() -> ErrorHandler:
    """
    函数级注释：获取默认错误处理链（单例）
    返回值：默认错误处理链
    """
    global _default_chain
    if _default_chain is None:
        _default_chain = create_default_error_chain()
    return _default_chain


# 内部变量：导出所有公共接口
__all__ = [
    'ErrorHandler',
    'SensitiveDataErrorHandler',
    'LLMErrorHandler',
    'DatabaseErrorHandler',
    'ValidationErrorHandler',
    'ErrorChainBuilder',
    'create_default_error_chain',
    'get_default_chain',
]
