# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：验证责任链模块
内部逻辑：实现灵活的验证规则组合，支持动态添加验证器
设计模式：责任链模式（Chain of Responsibility Pattern）
设计原则：开闭原则、单一职责原则
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Tuple
from dataclasses import dataclass, field as dataclass_field
from enum import Enum
from loguru import logger
import asyncio


class ValidationSeverity(Enum):
    """
    类级注释：验证严重级别枚举
    内部逻辑：定义验证失败的严重程度
    """
    # 信息级别（不阻止处理）
    INFO = "info"
    # 警告级别（不阻止处理）
    WARNING = "warning"
    # 错误级别（阻止处理）
    ERROR = "error"
    # 严重错误级别（立即停止）
    CRITICAL = "critical"


@dataclass
class ValidationError:
    """
    类级注释：验证错误数据类
    内部逻辑：封装验证失败的详细信息
    """
    # 属性：错误代码
    code: str
    # 属性：错误消息
    message: str
    # 属性：严重级别
    severity: ValidationSeverity = ValidationSeverity.ERROR
    # 属性：错误字段
    field: Optional[str] = None
    # 属性：额外数据
    extra: Dict[str, Any] = dataclass_field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        函数级注释：转换为字典
        返回值：字典表示
        """
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity.value,
            "field": self.field,
            "extra": self.extra
        }


@dataclass
class ValidationResult:
    """
    类级注释：验证结果数据类
    内部逻辑：封装验证的整体结果
    """
    # 属性：是否通过验证
    is_valid: bool
    # 属性：错误列表
    errors: List[ValidationError] = dataclass_field(default_factory=list)

    @property
    def critical_errors(self) -> List[ValidationError]:
        """
        函数级注释：获取严重错误
        返回值：严重错误列表
        """
        return [e for e in self.errors if e.severity == ValidationSeverity.CRITICAL]

    @property
    def error_count(self) -> int:
        """
        函数级注释：获取错误数量
        返回值：错误级别的错误数量
        """
        return len([e for e in self.errors if e.severity == ValidationSeverity.ERROR])

    @property
    def warning_count(self) -> int:
        """
        函数级注释：获取警告数量
        返回值：警告级别的错误数量
        """
        return len([e for e in self.errors if e.severity == ValidationSeverity.WARNING])

    def add_error(self, error: ValidationError) -> None:
        """
        函数级注释：添加错误
        参数：
            error - 验证错误
        """
        self.errors.append(error)
        if error.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
            self.is_valid = False

    def merge(self, other: 'ValidationResult') -> None:
        """
        函数级注释：合并另一个验证结果
        参数：
            other - 另一个验证结果
        """
        self.errors.extend(other.errors)
        if not other.is_valid:
            self.is_valid = False

    def to_dict(self) -> Dict[str, Any]:
        """
        函数级注释：转换为字典
        返回值：字典表示
        """
        return {
            "is_valid": self.is_valid,
            "errors": [e.to_dict() for e in self.errors],
            "error_count": self.error_count,
            "warning_count": self.warning_count
        }


class ValidationContext:
    """
    类级注释：验证上下文
    内部逻辑：在验证链中传递的上下文信息
    设计模式：上下文对象模式
    """

    def __init__(
        self,
        request: Any,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        函数级注释：初始化验证上下文
        参数：
            request - 待验证的请求对象
            metadata - 额外的元数据
        """
        # 内部变量：待验证的请求
        self.request = request
        # 内部变量：元数据
        self.metadata = metadata or {}
        # 内部变量：验证器间共享的数据
        self.shared_data: Dict[str, Any] = {}
        # 内部变量：是否应该停止处理
        self.should_stop = False

    def get(self, key: str, default: Any = None) -> Any:
        """
        函数级注释：获取共享数据
        参数：
            key - 键
            default - 默认值
        返回值：共享数据值
        """
        return self.shared_data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        函数级注释：设置共享数据
        参数：
            key - 键
            value - 值
        """
        self.shared_data[key] = value

    def stop(self) -> None:
        """
        函数级注释：停止后续处理
        """
        self.should_stop = True


class ValidationHandler(ABC):
    """
    类级注释：验证处理器抽象基类
    内部逻辑：定义验证器的统一接口
    设计模式：责任链模式 - 处理器接口
    """

    # 内部变量：下一个处理器
    _next: Optional['ValidationHandler'] = None

    def __init__(
        self,
        stop_on_error: bool = False,
        stop_on_critical: bool = True
    ):
        """
        函数级注释：初始化验证处理器
        参数：
            stop_on_error - 遇到错误时是否停止
            stop_on_critical - 遇到严重错误时是否停止
        """
        # 内部变量：遇到错误时是否停止
        self._stop_on_error = stop_on_error
        # 内部变量：遇到严重错误时是否停止
        self._stop_on_critical = stop_on_critical

    def set_next(self, handler: 'ValidationHandler') -> 'ValidationHandler':
        """
        函数级注释：设置下一个处理器
        内部逻辑：构建责任链
        参数：
            handler - 下一个处理器
        返回值：下一个处理器（支持链式调用）
        """
        self._next = handler
        return handler

    async def handle(self, context: ValidationContext) -> ValidationResult:
        """
        函数级注释：处理验证请求（模板方法）
        内部逻辑：执行当前验证 -> 检查是否停止 -> 传递给下一个处理器
        参数：
            context - 验证上下文
        返回值：验证结果
        """
        # 内部逻辑：执行当前验证
        result = await self._validate(context)

        # 内部逻辑：检查是否应该停止
        if context.should_stop:
            return result

        # 内部逻辑：检查是否遇到严重错误
        if self._stop_on_critical and result.critical_errors:
            logger.warning(f"遇到严重错误，停止验证链: {self.__class__.__name__}")
            return result

        # 内部逻辑：检查是否遇到错误
        if self._stop_on_error and not result.is_valid:
            logger.debug(f"遇到错误，停止验证链: {self.__class__.__name__}")
            return result

        # 内部逻辑：传递给下一个处理器
        if self._next:
            next_result = await self._next.handle(context)
            result.merge(next_result)

        return result

    @abstractmethod
    async def _validate(self, context: ValidationContext) -> ValidationResult:
        """
        函数级注释：执行具体的验证逻辑（抽象方法）
        参数：
            context - 验证上下文
        返回值：验证结果
        """
        pass


class AuthenticationHandler(ValidationHandler):
    """
    类级注释：认证验证处理器
    内部逻辑：验证用户身份和认证状态
    设计模式：责任链模式 - 具体处理器
    """

    def __init__(self, get_user_func: callable = None, **kwargs):
        """
        函数级注释：初始化认证处理器
        参数：
            get_user_func - 获取用户信息的函数
            **kwargs - 其他参数
        """
        super().__init__(**kwargs)
        # 内部变量：获取用户函数
        self._get_user_func = get_user_func

    async def _validate(self, context: ValidationContext) -> ValidationResult:
        """
        函数级注释：验证用户认证
        内部逻辑：检查请求中是否有有效用户信息
        参数：
            context - 验证上下文
        返回值：验证结果
        """
        result = ValidationResult(is_valid=True)

        # 内部逻辑：尝试从上下文获取用户
        request = context.request
        user = getattr(request, 'user', None)

        if user is None:
            # 内部逻辑：尝试从 headers 获取认证信息
            headers = getattr(request, 'headers', {})
            auth_token = headers.get('authorization', '')

            if not auth_token:
                result.add_error(ValidationError(
                    code="AUTH_MISSING",
                    message="缺少认证信息",
                    severity=ValidationSeverity.CRITICAL,
                    field="authorization"
                ))
                return result

            # 内部逻辑：如果有获取用户函数，尝试获取
            if self._get_user_func:
                try:
                    user = await self._get_user_func(auth_token)
                    context.set('user', user)
                except Exception as e:
                    result.add_error(ValidationError(
                        code="AUTH_FAILED",
                        message=f"认证失败: {str(e)}",
                        severity=ValidationSeverity.CRITICAL,
                        field="authorization"
                    ))
            else:
                # 内部逻辑：简单检查 token 是否存在
                if not auth_token.startswith('Bearer '):
                    result.add_error(ValidationError(
                        code="AUTH_INVALID",
                        message="无效的认证格式",
                        severity=ValidationSeverity.CRITICAL,
                        field="authorization"
                    ))
        else:
            # 内部逻辑：存储用户到上下文
            context.set('user', user)

        logger.debug(f"认证验证完成: {result.is_valid}")
        return result


class RateLimitHandler(ValidationHandler):
    """
    类级注释：限流验证处理器
    内部逻辑：验证请求频率是否超限
    设计模式：责任链模式 - 具体处理器
    """

    # 内部变量：限流记录存储
    _request_counts: Dict[str, List[float]] = {}

    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
        get_key_func: callable = None,
        **kwargs
    ):
        """
        函数级注释：初始化限流处理器
        参数：
            max_requests - 时间窗口内最大请求数
            window_seconds - 时间窗口大小（秒）
            get_key_func - 获取限流键的函数
            **kwargs - 其他参数
        """
        super().__init__(**kwargs)
        # 内部变量：最大请求数
        self._max_requests = max_requests
        # 内部变量：时间窗口
        self._window = window_seconds
        # 内部变量：获取键函数
        self._get_key_func = get_key_func

    def _clean_old_requests(self, key: str, now: float) -> None:
        """
        函数级注释：清理过期的请求记录
        参数：
            key - 限流键
            now - 当前时间戳
        """
        window_start = now - self._window
        if key in self._request_counts:
            self._request_counts[key] = [
                timestamp for timestamp in self._request_counts[key]
                if timestamp > window_start
            ]

    async def _validate(self, context: ValidationContext) -> ValidationResult:
        """
        函数级注释：验证请求频率
        内部逻辑：检查时间窗口内的请求数
        参数：
            context - 验证上下文
        返回值：验证结果
        """
        import time

        result = ValidationResult(is_valid=True)
        now = time.time()

        # 内部逻辑：获取限流键
        if self._get_key_func:
            key = self._get_key_func(context)
        else:
            # 内部逻辑：默认使用用户 ID 或 IP
            user = context.get('user')
            key = getattr(user, 'id', 'anonymous') if user else 'anonymous'

        # 内部逻辑：清理过期记录
        self._clean_old_requests(key, now)

        # 内部逻辑：初始化键
        if key not in self._request_counts:
            self._request_counts[key] = []

        # 内部逻辑：检查是否超限
        if len(self._request_counts[key]) >= self._max_requests:
            result.add_error(ValidationError(
                code="RATE_LIMIT_EXCEEDED",
                message=f"请求频率超限，{self._window}秒内最多{self._max_requests}次请求",
                severity=ValidationSeverity.ERROR
            ))
            logger.warning(f"限流触发: {key}, 请求数: {len(self._request_counts[key])}")
        else:
            # 内部逻辑：记录本次请求
            self._request_counts[key].append(now)

        return result


class ContentValidatorHandler(ValidationHandler):
    """
    类级注释：内容验证处理器
    内部逻辑：验证请求内容的格式和有效性
    设计模式：责任链模式 - 具体处理器
    """

    def __init__(
        self,
        required_fields: Optional[List[str]] = None,
        max_length: Optional[int] = None,
        forbidden_patterns: Optional[List[str]] = None,
        **kwargs
    ):
        """
        函数级注释：初始化内容验证处理器
        参数：
            required_fields - 必填字段列表
            max_length - 最大内容长度
            forbidden_patterns - 禁止的正则模式列表
            **kwargs - 其他参数
        """
        super().__init__(**kwargs)
        # 内部变量：必填字段
        self._required_fields = required_fields or []
        # 内部变量：最大长度
        self._max_length = max_length
        # 内部变量：禁止模式
        self._forbidden_patterns = forbidden_patterns or []

    async def _validate(self, context: ValidationContext) -> ValidationResult:
        """
        函数级注释：验证请求内容
        参数：
            context - 验证上下文
        返回值：验证结果
        """
        import re

        result = ValidationResult(is_valid=True)
        request = context.request

        # 内部逻辑：如果是字典类型，验证字段
        if isinstance(request, dict):
            # 内部逻辑：检查必填字段
            for field in self._required_fields:
                if field not in request or not request[field]:
                    result.add_error(ValidationError(
                        code="REQUIRED_FIELD_MISSING",
                        message=f"必填字段缺失: {field}",
                        severity=ValidationSeverity.ERROR,
                        field=field
                    ))

            # 内部逻辑：检查最大长度
            if self._max_length:
                for key, value in request.items():
                    if isinstance(value, str) and len(value) > self._max_length:
                        result.add_error(ValidationError(
                            code="FIELD_TOO_LONG",
                            message=f"字段 {key} 超过最大长度 {self._max_length}",
                            severity=ValidationSeverity.ERROR,
                            field=key,
                            extra={"max_length": self._max_length, "actual_length": len(value)}
                        ))

            # 内部逻辑：检查禁止模式
            for pattern in self._forbidden_patterns:
                for key, value in request.items():
                    if isinstance(value, str) and re.search(pattern, value):
                        result.add_error(ValidationError(
                            code="FORBIDDEN_PATTERN",
                            message=f"字段 {key} 包含禁止的内容模式",
                            severity=ValidationSeverity.ERROR,
                            field=key
                        ))

        logger.debug(f"内容验证完成: {result.is_valid}")
        return result


class SchemaValidationHandler(ValidationHandler):
    """
    类级注释：Schema 验证处理器
    内部逻辑：使用 Pydantic 模型进行验证
    设计模式：责任链模式 - 具体处理器
    """

    def __init__(self, schema_class: Type, **kwargs):
        """
        函数级注释：初始化 Schema 验证处理器
        参数：
            schema_class - Pydantic 模型类
            **kwargs - 其他参数
        """
        super().__init__(**kwargs)
        # 内部变量：Schema 类
        self._schema_class = schema_class

    async def _validate(self, context: ValidationContext) -> ValidationResult:
        """
        函数级注释：使用 Schema 验证请求
        参数：
            context - 验证上下文
        返回值：验证结果
        """
        result = ValidationResult(is_valid=True)
        request = context.request

        try:
            # 内部逻辑：尝试用 Schema 解析
            validated = self._schema_class(**request if isinstance(request, dict) else {})
            # 内部逻辑：存储验证后的对象到上下文
            context.set('validated_schema', validated)
            logger.debug(f"Schema 验证通过: {self._schema_class.__name__}")

        except Exception as e:
            # 内部逻辑：提取验证错误
            errors = []
            if hasattr(e, 'errors'):
                for error in e.errors():
                    errors.append(ValidationError(
                        code="SCHEMA_VALIDATION_ERROR",
                        message=error['msg'],
                        severity=ValidationSeverity.ERROR,
                        field=str(error['loc'][0]) if error['loc'] else None
                    ))
            else:
                errors.append(ValidationError(
                    code="SCHEMA_VALIDATION_ERROR",
                    message=str(e),
                    severity=ValidationSeverity.ERROR
                ))

            for error in errors:
                result.add_error(error)

        return result


class PermissionHandler(ValidationHandler):
    """
    类级注释：权限验证处理器
    内部逻辑：验证用户是否有执行操作的权限
    设计模式：责任链模式 - 具体处理器
    """

    def __init__(
        self,
        required_permissions: List[str],
        check_func: Optional[callable] = None,
        **kwargs
    ):
        """
        函数级注释：初始化权限处理器
        参数：
            required_permissions - 需要的权限列表
            check_func - 自定义权限检查函数
            **kwargs - 其他参数
        """
        super().__init__(**kwargs)
        # 内部变量：需要的权限
        self._required_permissions = required_permissions
        # 内部变量：自定义检查函数
        self._check_func = check_func

    async def _validate(self, context: ValidationContext) -> ValidationResult:
        """
        函数级注释：验证用户权限
        参数：
            context - 验证上下文
        返回值：验证结果
        """
        result = ValidationResult(is_valid=True)
        user = context.get('user')

        if not user:
            result.add_error(ValidationError(
                code="PERMISSION_DENIED",
                message="用户未认证，无法验证权限",
                severity=ValidationSeverity.CRITICAL
            ))
            return result

        # 内部逻辑：使用自定义检查函数
        if self._check_func:
            try:
                has_permission = await self._check_func(user, self._required_permissions)
                if not has_permission:
                    result.add_error(ValidationError(
                        code="PERMISSION_DENIED",
                        message=f"缺少必要权限: {', '.join(self._required_permissions)}",
                        severity=ValidationSeverity.ERROR
                    ))
            except Exception as e:
                result.add_error(ValidationError(
                    code="PERMISSION_CHECK_ERROR",
                    message=f"权限检查失败: {str(e)}",
                    severity=ValidationSeverity.ERROR
                ))
        else:
            # 内部逻辑：默认检查用户是否有所有必需权限
            user_permissions = getattr(user, 'permissions', [])
            missing = [p for p in self._required_permissions if p not in user_permissions]

            if missing:
                result.add_error(ValidationError(
                    code="PERMISSION_DENIED",
                    message=f"缺少权限: {', '.join(missing)}",
                    severity=ValidationSeverity.ERROR
                ))

        logger.debug(f"权限验证完成: {result.is_valid}")
        return result


class BusinessLogicHandler(ValidationHandler):
    """
    类级注释：业务逻辑验证处理器
    内部逻辑：执行自定义业务逻辑验证
    设计模式：责任链模式 - 具体处理器
    用途：允许注入自定义验证逻辑，如检查资源状态、业务规则等
    """

    def __init__(
        self,
        validate_func: callable,
        error_code: str = "BUSINESS_LOGIC_ERROR",
        **kwargs
    ):
        """
        函数级注释：初始化业务逻辑处理器
        参数：
            validate_func - 自定义验证函数，签名为 async func(context) -> ValidationResult
            error_code - 错误代码
            **kwargs - 其他参数
        """
        super().__init__(**kwargs)
        # 内部变量：自定义验证函数
        self._validate_func = validate_func
        # 内部变量：错误代码
        self._error_code = error_code

    async def _validate(self, context: ValidationContext) -> ValidationResult:
        """
        函数级注释：执行业务逻辑验证
        参数：
            context - 验证上下文
        返回值：验证结果
        """
        try:
            # 内部逻辑：调用自定义验证函数
            if asyncio.iscoroutinefunction(self._validate_func):
                result = await self._validate_func(context)
            else:
                result = self._validate_func(context)

            # 内部逻辑：确保返回 ValidationResult
            if not isinstance(result, ValidationResult):
                logger.warning(f"业务逻辑验证函数返回了非 ValidationResult 类型")
                result = ValidationResult(is_valid=True)

            return result

        except Exception as e:
            # 内部逻辑：捕获异常并返回错误结果
            logger.error(f"业务逻辑验证失败: {str(e)}")
            result = ValidationResult(is_valid=False)
            result.add_error(ValidationError(
                code=self._error_code,
                message=f"业务逻辑验证失败: {str(e)}",
                severity=ValidationSeverity.ERROR
            ))
            return result


class LoggingHandler(ValidationHandler):
    """
    类级注释：日志记录处理器
    内部逻辑：记录验证请求和结果，不进行实际验证
    设计模式：责任链模式 - 具体处理器（无副作用）
    用途：在验证链中记录日志，用于调试和监控
    """

    def __init__(
        self,
        log_level: str = "info",
        log_request: bool = True,
        log_result: bool = True,
        **kwargs
    ):
        """
        函数级注释：初始化日志处理器
        参数：
            log_level - 日志级别
            log_request - 是否记录请求
            log_result - 是否记录结果
            **kwargs - 其他参数
        """
        # 内部逻辑：日志处理器不应阻止后续处理
        kwargs.setdefault('stop_on_error', False)
        kwargs.setdefault('stop_on_critical', False)
        super().__init__(**kwargs)

        # 内部变量：日志级别
        self._log_level = log_level.lower()
        # 内部变量：是否记录请求
        self._log_request = log_request
        # 内部变量：是否记录结果
        self._log_result = log_result

    async def _validate(self, context: ValidationContext) -> ValidationResult:
        """
        函数级注释：记录日志
        参数：
            context - 验证上下文
        返回值：验证结果（始终有效）
        """
        # 内部逻辑：记录请求
        if self._log_request:
            log_func = getattr(logger, self._log_level, logger.info)
            log_func(
                f"验证请求: {context.__class__.__name__}, "
                f"metadata: {context.metadata}"
            )

        # 内部逻辑：存储开始时间到上下文
        import time
        context.set('validation_start_time', time.time())

        return ValidationResult(is_valid=True)

    async def handle(self, context: ValidationContext) -> ValidationResult:
        """
        函数级注释：处理验证请求（重写以添加结果日志）
        参数：
            context - 验证上下文
        返回值：验证结果
        """
        import time

        # 内部逻辑：执行当前验证
        result = await self._validate(context)

        # 内部逻辑：传递给下一个处理器
        if self._next:
            result = await self._next.handle(context)

        # 内部逻辑：记录结果
        if self._log_result:
            start_time = context.get('validation_start_time', time.time())
            elapsed = time.time() - start_time

            log_func = getattr(logger, self._log_level, logger.info)
            log_func(
                f"验证完成: valid={result.is_valid}, "
                f"errors={result.error_count}, warnings={result.warning_count}, "
                f"elapsed={elapsed:.3f}s"
            )

        return result


class ValidationChain:
    """
    类级注释：验证链管理器
    内部逻辑：管理和执行验证处理器链
    设计模式：责任链模式 - 链管理器
    """

    def __init__(self, name: str = "default"):
        """
        函数级注释：初始化验证链
        参数：
            name - 验证链名称
        """
        # 内部变量：链名称
        self._name = name
        # 内部变量：链头
        self._head: Optional[ValidationHandler] = None
        # 内部变量：链尾
        self._tail: Optional[ValidationHandler] = None
        # 内部变量：处理器列表
        self._handlers: List[ValidationHandler] = []

    def add_handler(self, handler: ValidationHandler) -> 'ValidationChain':
        """
        函数级注释：添加处理器到链尾
        参数：
            handler - 验证处理器
        返回值：自身（支持链式调用）
        """
        self._handlers.append(handler)

        if self._head is None:
            # 内部逻辑：第一个处理器作为链头
            self._head = handler
            self._tail = handler
        else:
            # 内部逻辑：连接到链尾
            self._tail.set_next(handler)
            self._tail = handler

        logger.debug(f"添加处理器到验证链 '{self._name}': {handler.__class__.__name__}")
        return self

    async def validate(self, request: Any, metadata: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        函数级注释：执行验证链
        参数：
            request - 待验证的请求
            metadata - 额外的元数据
        返回值：验证结果
        """
        if self._head is None:
            logger.warning(f"验证链 '{self._name}' 为空")
            return ValidationResult(is_valid=True)

        context = ValidationContext(request, metadata)
        result = await self._head.handle(context)

        logger.info(
            f"验证链 '{self._name}' 执行完成: "
            f"valid={result.is_valid}, errors={result.error_count}, warnings={result.warning_count}"
        )
        return result

    def clear(self) -> None:
        """
        函数级注释：清空验证链
        """
        self._head = None
        self._tail = None
        self._handlers.clear()
        logger.debug(f"验证链 '{self._name}' 已清空")


class ValidationChainFactory:
    """
    类级注释：验证链工厂
    内部逻辑：创建和管理预配置的验证链
    设计模式：工厂模式 + 抽象工厂模式
    """

    # 内部变量：注册的验证链
    _chains: Dict[str, ValidationChain] = {}

    @classmethod
    def register_chain(cls, name: str, chain: ValidationChain) -> None:
        """
        函数级注释：注册验证链
        参数：
            name - 链名称
            chain - 验证链
        """
        cls._chains[name] = chain
        logger.info(f"注册验证链: {name}")

    @classmethod
    def get_chain(cls, name: str) -> Optional[ValidationChain]:
        """
        函数级注释：获取验证链
        参数：
            name - 链名称
        返回值：验证链或 None
        """
        return cls._chains.get(name)

    @classmethod
    def create_chat_chain(cls, rate_limit: int = 100) -> ValidationChain:
        """
        函数级注释：创建聊天验证链
        内部逻辑：认证 -> 限流 -> 内容验证
        参数：
            rate_limit - 限流请求数
        返回值：配置好的验证链
        """
        chain = ValidationChain("chat")
        chain.add_handler(AuthenticationHandler(stop_on_critical=True))
        chain.add_handler(RateLimitHandler(max_requests=rate_limit))
        chain.add_handler(ContentValidatorHandler(
            required_fields=["message"],
            max_length=10000
        ))
        return chain

    @classmethod
    def create_api_chain(cls, required_permissions: List[str] = None, strict: bool = False) -> ValidationChain:
        """
        函数级注释：创建 API 验证链
        内部逻辑：认证（严格模式）-> 权限 -> 内容验证
        参数：
            required_permissions - 需要的权限列表
            strict - 是否启用严格验证（包括认证），默认False
        返回值：配置好的验证链
        """
        chain = ValidationChain("api")
        # 内部逻辑：只在严格模式下添加认证处理器
        if strict:
            chain.add_handler(AuthenticationHandler(stop_on_critical=True))
        if required_permissions:
            chain.add_handler(PermissionHandler(required_permissions))
        chain.add_handler(RateLimitHandler(max_requests=200))
        return chain


# 内部变量：导出所有公共接口
__all__ = [
    'ValidationHandler',
    'ValidationResult',
    'ValidationError',
    'ValidationContext',
    'ValidationChain',
    'ValidationChainFactory',
    'ValidationSeverity',
    'AuthenticationHandler',
    'RateLimitHandler',
    'ContentValidatorHandler',
    'SchemaValidationHandler',
    'PermissionHandler',
    'BusinessLogicHandler',
    'LoggingHandler',
]
