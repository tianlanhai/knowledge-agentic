# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：建造者模式模块
内部逻辑：提供复杂对象的流式构建接口
设计模式：建造者模式（Builder Pattern）
设计原则：单一职责原则（SRP）、开闭原则（OCP）
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from loguru import logger

# 内部变量：泛型类型 T，表示构建结果类型
T = TypeVar('T')


class BuildStep(Enum):
    """
    类级注释：构建步骤枚举
    属性：建造者模式的验证步骤
    """
    # 基础步骤
    BASIC = "basic"
    # 参数配置
    PARAMS = "params"
    # 验证
    VALIDATION = "validation"


@dataclass
class BuildResult:
    """
    类级注释：构建结果数据类
    属性：构建的成功状态、结果对象或错误信息
    """
    # 内部属性：是否成功
    success: bool
    # 内部属性：构建结果
    result: Optional[Any] = None
    # 内部属性：错误信息
    errors: List[str] = field(default_factory=list)
    # 内部属性：构建耗时（秒）
    duration: float = 0.0

    def add_error(self, error: str) -> None:
        """
        函数级注释：添加错误信息
        参数：
            error - 错误信息
        """
        self.success = False
        self.errors.append(error)


class BaseBuilder(ABC, Generic[T]):
    """
    类级注释：建造者抽象基类
    设计模式：建造者模式（Builder Pattern）
    职责：
        1. 定义建造者接口
        2. 提供构建结果验证
        3. 支持链式调用
    """

    # 内部变量：构建步骤记录
    _completed_steps: set = field(default_factory=set)

    # 内部变量：构建开始时间
    _start_time: Optional[float] = None

    @abstractmethod
    def build(self) -> BuildResult:
        """
        函数级注释：构建最终对象（抽象方法）
        返回值：构建结果
        """
        pass

    def reset(self) -> 'BaseBuilder[T]':
        """
        函数级注释：重置建造者状态
        返回值：建造者自身（支持链式调用）
        """
        self._completed_steps.clear()
        self._start_time = None
        return self

    def _start_build(self) -> None:
        """
        函数级注释：开始构建计时（内部方法）
        """
        import time
        self._start_time = time.time()

    def _end_build(self) -> float:
        """
        函数级注释：结束构建计时（内部方法）
        返回值：构建耗时（秒）
        """
        if self._start_time is None:
            return 0.0
        import time
        return time.time() - self._start_time


class ChatRequestBuilder(BaseBuilder):
    """
    类级注释：聊天请求建造者
    设计模式：建造者模式（Builder Pattern）
    职责：
        1. 流式构建聊天请求对象
        2. 参数验证
        3. 默认值处理

    @example
    ```python
    request = (ChatRequestBuilder()
        .with_message("Hello, AI!")
        .with_history(history)
        .with_temperature(0.7)
        .with_streaming(True)
        .build())
    ```
    """

    def __init__(self):
        """
        函数级注释：初始化建造者
        """
        super().__init__()
        # 内部变量：请求参数
        self._message: Optional[str] = None
        self._history: List[Dict[str, Any]] = []
        self._use_agent: bool = False
        self._stream: bool = False
        self._temperature: float = 0.7
        self._max_tokens: Optional[int] = None
        self._top_p: float = 1.0
        self._frequency_penalty: float = 0.0
        self._presence_penalty: float = 0.0
        self._stop: Optional[List[str]] = None
        self._model: Optional[str] = None
        self._conversation_id: Optional[str] = None
        self._metadata: Dict[str, Any] = field(default_factory=dict)

    def with_message(self, message: str) -> 'ChatRequestBuilder':
        """
        函数级注释：设置消息内容
        参数：
            message - 用户消息
        返回值：建造者自身（支持链式调用）
        """
        if not message or not message.strip():
            logger.warning("[ChatRequestBuilder] 消息内容为空")
        self._message = message
        self._completed_steps.add(BuildStep.BASIC)
        return self

    def with_history(self, history: List[Dict[str, Any]]) -> 'ChatRequestBuilder':
        """
        函数级注释：设置对话历史
        参数：
            history - 历史消息列表
        返回值：建造者自身
        """
        self._history = history.copy()
        return self

    def append_history(self, role: str, content: str) -> 'ChatRequestBuilder':
        """
        函数级注释：添加单条历史消息
        参数：
            role - 角色（user/assistant/system）
            content - 消息内容
        返回值：建造者自身
        """
        self._history.append({"role": role, "content": content})
        return self

    def with_agent(self, enabled: bool = True) -> 'ChatRequestBuilder':
        """
        函数级注释：设置是否使用智能体模式
        参数：
            enabled - 是否启用
        返回值：建造者自身
        """
        self._use_agent = enabled
        return self

    def with_streaming(self, enabled: bool = True) -> 'ChatRequestBuilder':
        """
        函数级注释：设置是否流式输出
        参数：
            enabled - 是否启用
        返回值：建造者自身
        """
        self._stream = enabled
        return self

    def with_temperature(self, temperature: float) -> 'ChatRequestBuilder':
        """
        函数级注释：设置温度参数
        参数：
            temperature - 温度值（0-2）
        返回值：建造者自身
        """
        if not 0 <= temperature <= 2:
            logger.warning(f"[ChatRequestBuilder] 温度值异常: {temperature}")
        self._temperature = temperature
        self._completed_steps.add(BuildStep.PARAMS)
        return self

    def with_max_tokens(self, max_tokens: int) -> 'ChatRequestBuilder':
        """
        函数级注释：设置最大生成 tokens
        参数：
            max_tokens - 最大 tokens 数
        返回值：建造者自身
        """
        if max_tokens <= 0:
            logger.warning(f"[ChatRequestBuilder] max_tokens 必须大于0: {max_tokens}")
        self._max_tokens = max_tokens
        return self

    def with_top_p(self, top_p: float) -> 'ChatRequestBuilder':
        """
        函数级注释：设置 top_p 参数
        参数：
            top_p - top_p 值（0-1）
        返回值：建造者自身
        """
        if not 0 <= top_p <= 1:
            logger.warning(f"[ChatRequestBuilder] top_p 值异常: {top_p}")
        self._top_p = top_p
        return self

    def with_model(self, model: str) -> 'ChatRequestBuilder':
        """
        函数级注释：设置模型名称
        参数：
            model - 模型名称
        返回值：建造者自身
        """
        self._model = model
        return self

    def with_conversation(self, conversation_id: str) -> 'ChatRequestBuilder':
        """
        函数级注释：设置会话 ID
        参数：
            conversation_id - 会话 ID
        返回值：建造者自身
        """
        self._conversation_id = conversation_id
        return self

    def with_metadata(self, metadata: Dict[str, Any]) -> 'ChatRequestBuilder':
        """
        函数级注释：设置元数据
        参数：
            metadata - 元数据字典
        返回值：建造者自身
        """
        self._metadata.update(metadata)
        return self

    def with_penalty(self, frequency: float = 0.0, presence: float = 0.0) -> 'ChatRequestBuilder':
        """
        函数级注释：设置惩罚参数
        参数：
            frequency - 频率惩罚
            presence - 存在惩罚
        返回值：建造者自身
        """
        self._frequency_penalty = frequency
        self._presence_penalty = presence
        return self

    def with_stop_sequences(self, stop: List[str]) -> 'ChatRequestBuilder':
        """
        函数级注释：设置停止序列
        参数：
            stop - 停止序列列表
        返回值：建造者自身
        """
        self._stop = stop
        return self

    def build(self) -> BuildResult:
        """
        函数级注释：构建聊天请求对象
        返回值：构建结果
        """
        self._start_build()
        result = BuildResult(success=True)

        # 内部逻辑：验证必需参数
        if not self._message:
            result.add_error("消息内容不能为空")

        # 内部逻辑：验证参数范围
        if self._temperature < 0 or self._temperature > 2:
            result.add_error(f"温度值必须在 0-2 之间: {self._temperature}")

        if self._top_p < 0 or self._top_p > 1:
            result.add_error(f"top_p 值必须在 0-1 之间: {self._top_p}")

        if self._max_tokens is not None and self._max_tokens <= 0:
            result.add_error(f"max_tokens 必须大于0: {self._max_tokens}")

        # 内部逻辑：如果有错误，返回失败结果
        if not result.success:
            result.duration = self._end_build()
            return result

        # 内部逻辑：构建请求对象
        request = {
            "message": self._message,
            "history": self._history,
            "use_agent": self._use_agent,
            "stream": self._stream,
        }

        # 内部逻辑：添加可选参数
        params = {}
        if self._temperature != 0.7:
            params["temperature"] = self._temperature
        if self._max_tokens is not None:
            params["max_tokens"] = self._max_tokens
        if self._top_p != 1.0:
            params["top_p"] = self._top_p
        if self._frequency_penalty != 0.0:
            params["frequency_penalty"] = self._frequency_penalty
        if self._presence_penalty != 0.0:
            params["presence_penalty"] = self._presence_penalty
        if self._stop:
            params["stop"] = self._stop
        if self._model:
            params["model"] = self._model

        # 内部逻辑：添加参数到请求
        if params:
            request["parameters"] = params

        # 内部逻辑：添加元信息
        if self._conversation_id:
            request["conversation_id"] = self._conversation_id
        if self._metadata:
            request["metadata"] = self._metadata

        result.result = request
        result.duration = self._end_build()

        logger.debug(f"[ChatRequestBuilder] 构建完成，耗时: {result.duration:.3f}s")

        return result


class SearchQueryBuilder(BaseBuilder):
    """
    类级注释：搜索查询建造者
    设计模式：建造者模式（Builder Pattern）
    职责：
        1. 流式构建搜索查询
        2. 支持复杂查询条件组合

    @example
    ```python
    query = (SearchQueryBuilder()
        .with_text("机器学习")
        .with_filters({"category": "AI"})
        .with_limit(10)
        .build())
    ```
    """

    def __init__(self):
        """
        函数级注释：初始化建造者
        """
        super().__init__()
        # 内部变量：查询参数
        self._text: Optional[str] = None
        self._filters: Dict[str, Any] = {}
        self._limit: int = 10
        self._offset: int = 0
        self._sort_by: Optional[str] = None
        self._sort_order: str = "desc"
        self._include_metadata: bool = True
        self._score_threshold: Optional[float] = None

    def with_text(self, text: str) -> 'SearchQueryBuilder':
        """
        函数级注释：设置搜索文本
        参数：
            text - 搜索文本
        返回值：建造者自身
        """
        self._text = text
        self._completed_steps.add(BuildStep.BASIC)
        return self

    def with_filters(self, filters: Dict[str, Any]) -> 'SearchQueryBuilder':
        """
        函数级注释：设置过滤条件
        参数：
            filters - 过滤条件字典
        返回值：建造者自身
        """
        self._filters.update(filters)
        return self

    def add_filter(self, key: str, value: Any) -> 'SearchQueryBuilder':
        """
        函数级注释：添加单个过滤条件
        参数：
            key - 键
            value - 值
        返回值：建造者自身
        """
        self._filters[key] = value
        return self

    def with_pagination(self, limit: int, offset: int = 0) -> 'SearchQueryBuilder':
        """
        函数级注释：设置分页参数
        参数：
            limit - 每页数量
            offset - 偏移量
        返回值：建造者自身
        """
        if limit <= 0:
            logger.warning(f"[SearchQueryBuilder] limit 必须大于0: {limit}")
        self._limit = max(1, limit)
        self._offset = max(0, offset)
        return self

    def with_sort(self, sort_by: str, order: str = "desc") -> 'SearchQueryBuilder':
        """
        函数级注释：设置排序
        参数：
            sort_by - 排序字段
            order - 排序方向（asc/desc）
        返回值：建造者自身
        """
        if order not in ["asc", "desc"]:
            logger.warning(f"[SearchQueryBuilder] 排序方向必须是 asc 或 desc: {order}")
        self._sort_by = sort_by
        self._sort_order = order if order in ["asc", "desc"] else "desc"
        return self

    def with_score_threshold(self, threshold: float) -> 'SearchQueryBuilder':
        """
        函数级注释：设置相似度阈值
        参数：
            threshold - 阈值（0-1）
        返回值：建造者自身
        """
        if not 0 <= threshold <= 1:
            logger.warning(f"[SearchQueryBuilder] 阈值必须在 0-1 之间: {threshold}")
        self._score_threshold = max(0, min(1, threshold))
        return self

    def with_metadata(self, include: bool = True) -> 'SearchQueryBuilder':
        """
        函数级注释：设置是否包含元数据
        参数：
            include - 是否包含
        返回值：建造者自身
        """
        self._include_metadata = include
        return self

    def build(self) -> BuildResult:
        """
        函数级注释：构建搜索查询对象
        返回值：构建结果
        """
        self._start_build()
        result = BuildResult(success=True)

        # 内部逻辑：验证必需参数
        if not self._text:
            result.add_error("搜索文本不能为空")

        # 内部逻辑：验证参数范围
        if self._limit <= 0:
            result.add_error(f"limit 必须大于0: {self._limit}")

        if self._offset < 0:
            result.add_error(f"offset 不能为负数: {self._offset}")

        if self._score_threshold is not None and not 0 <= self._score_threshold <= 1:
            result.add_error(f"score_threshold 必须在 0-1 之间: {self._score_threshold}")

        if not result.success:
            result.duration = self._end_build()
            return result

        # 内部逻辑：构建查询对象
        query = {
            "query": self._text,
            "limit": self._limit,
            "offset": self._offset,
        }

        # 内部逻辑：添加可选参数
        if self._filters:
            query["filters"] = self._filters
        if self._sort_by:
            query["sort"] = {"by": self._sort_by, "order": self._sort_order}
        if self._include_metadata:
            query["include_metadata"] = True
        if self._score_threshold is not None:
            query["score_threshold"] = self._score_threshold

        result.result = query
        result.duration = self._end_build()

        logger.debug(f"[SearchQueryBuilder] 构建完成，耗时: {result.duration:.3f}s")

        return result


# 内部变量：导出所有公共接口
__all__ = [
    'BuildStep',
    'BuildResult',
    'BaseBuilder',
    'ChatRequestBuilder',
    'SearchQueryBuilder',
]
