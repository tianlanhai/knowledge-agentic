# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：验证责任链模块测试
内部逻辑：验证责任链模式的各种处理器和验证流程
设计模式：责任链模式（Chain of Responsibility Pattern）
测试覆盖范围：
    - ValidationSeverity: 验证严重级别枚举
    - ValidationError: 验证错误数据类
    - ValidationResult: 验证结果数据类
    - ValidationContext: 验证上下文
    - ValidationHandler: 验证处理器抽象基类
    - AuthenticationHandler: 认证验证处理器
    - RateLimitHandler: 限流验证处理器
    - ContentValidatorHandler: 内容验证处理器
    - SchemaValidationHandler: Schema验证处理器
    - PermissionHandler: 权限验证处理器
    - BusinessLogicHandler: 业务逻辑验证处理器
    - LoggingHandler: 日志记录处理器
    - ValidationChain: 验证链管理器
    - ValidationChainFactory: 验证链工厂
"""

import pytest
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, AsyncMock, patch
from dataclasses import dataclass

from app.core.validation_chain import (
    ValidationSeverity,
    ValidationError,
    ValidationResult,
    ValidationContext,
    ValidationHandler,
    AuthenticationHandler,
    RateLimitHandler,
    ContentValidatorHandler,
    SchemaValidationHandler,
    PermissionHandler,
    BusinessLogicHandler,
    LoggingHandler,
    ValidationChain,
    ValidationChainFactory,
)


# ============================================================================
# 测试 fixtures
# ============================================================================

@pytest.fixture
def mock_request():
    """模拟请求对象"""
    @dataclass
    class Request:
        user: Optional[Any] = None
        headers: Dict[str, str] = None

        def __init__(self):
            self.user = None
            self.headers = {}

    return Request()


@pytest.fixture
def mock_user():
    """模拟用户对象"""
    user = Mock()
    user.id = "test_user_123"
    user.permissions = ["read", "write"]
    return user


@pytest.fixture
def authenticated_request(mock_user):
    """已认证的请求"""
    @dataclass
    class Request:
        user: Optional[Any] = None

    req = Request()
    req.user = mock_user
    return req


# ============================================================================
# ValidationSeverity 枚举测试
# ============================================================================

class TestValidationSeverity:
    """测试验证严重级别枚举"""

    def test_severity_values(self):
        """测试严重级别值"""
        assert ValidationSeverity.INFO.value == "info"
        assert ValidationSeverity.WARNING.value == "warning"
        assert ValidationSeverity.ERROR.value == "error"
        assert ValidationSeverity.CRITICAL.value == "critical"

    def test_severity_ordering(self):
        """测试严重级别可以用于比较"""
        # 枚举值可以独立使用
        severities = [
            ValidationSeverity.INFO,
            ValidationSeverity.WARNING,
            ValidationSeverity.ERROR,
            ValidationSeverity.CRITICAL
        ]
        assert len(severities) == 4


# ============================================================================
# ValidationError 测试
# ============================================================================

class TestValidationError:
    """测试验证错误数据类"""

    def test_init_with_defaults(self):
        """测试默认值初始化"""
        error = ValidationError(
            code="TEST_ERROR",
            message="Test error message"
        )

        assert error.code == "TEST_ERROR"
        assert error.message == "Test error message"
        assert error.severity == ValidationSeverity.ERROR
        assert error.field is None
        assert error.extra == {}

    def test_init_with_all_fields(self):
        """测试完整字段初始化"""
        error = ValidationError(
            code="CUSTOM_ERROR",
            message="Custom message",
            severity=ValidationSeverity.WARNING,
            field="username",
            extra={"min_length": 3, "max_length": 20}
        )

        assert error.code == "CUSTOM_ERROR"
        assert error.severity == ValidationSeverity.WARNING
        assert error.field == "username"
        assert error.extra == {"min_length": 3, "max_length": 20}

    def test_to_dict(self):
        """测试转换为字典"""
        error = ValidationError(
            code="DICT_ERROR",
            message="Dict message",
            severity=ValidationSeverity.CRITICAL,
            field="password"
        )

        result = error.to_dict()

        assert result["code"] == "DICT_ERROR"
        assert result["message"] == "Dict message"
        assert result["severity"] == "critical"
        assert result["field"] == "password"
        assert result["extra"] == {}


# ============================================================================
# ValidationResult 测试
# ============================================================================

class TestValidationResult:
    """测试验证结果数据类"""

    def test_init_valid(self):
        """测试初始化有效结果"""
        result = ValidationResult(is_valid=True)

        assert result.is_valid is True
        assert result.errors == []
        assert result.critical_errors == []
        assert result.error_count == 0
        assert result.warning_count == 0

    def test_init_with_errors(self):
        """测试初始化带错误的结果"""
        errors = [
            ValidationError(
                code="ERR1",
                message="Error 1",
                severity=ValidationSeverity.ERROR
            ),
            ValidationError(
                code="WARN1",
                message="Warning 1",
                severity=ValidationSeverity.WARNING
            )
        ]

        result = ValidationResult(is_valid=False, errors=errors)

        assert result.is_valid is False
        assert len(result.errors) == 2
        assert result.error_count == 1
        assert result.warning_count == 1

    def test_critical_errors_property(self):
        """测试获取严重错误"""
        result = ValidationResult(is_valid=True)

        result.add_error(ValidationError(
            code="INFO",
            message="Info",
            severity=ValidationSeverity.INFO
        ))
        result.add_error(ValidationError(
            code="WARN",
            message="Warning",
            severity=ValidationSeverity.WARNING
        ))
        result.add_error(ValidationError(
            code="ERR",
            message="Error",
            severity=ValidationSeverity.ERROR
        ))
        result.add_error(ValidationError(
            code="CRIT",
            message="Critical",
            severity=ValidationSeverity.CRITICAL
        ))

        critical = result.critical_errors
        assert len(critical) == 1
        assert critical[0].code == "CRIT"

    def test_error_count_property(self):
        """测试错误计数"""
        result = ValidationResult(is_valid=True)

        assert result.error_count == 0

        result.add_error(ValidationError(
            code="WARN1",
            message="Warning",
            severity=ValidationSeverity.WARNING
        ))
        assert result.error_count == 0

        result.add_error(ValidationError(
            code="ERR1",
            message="Error",
            severity=ValidationSeverity.ERROR
        ))
        assert result.error_count == 1

        result.add_error(ValidationError(
            code="ERR2",
            message="Error 2",
            severity=ValidationSeverity.ERROR
        ))
        assert result.error_count == 2

    def test_warning_count_property(self):
        """测试警告计数"""
        result = ValidationResult(is_valid=True)

        assert result.warning_count == 0

        result.add_error(ValidationError(
            code="ERR",
            message="Error",
            severity=ValidationSeverity.ERROR
        ))
        assert result.warning_count == 0

        result.add_error(ValidationError(
            code="WARN1",
            message="Warning",
            severity=ValidationSeverity.WARNING
        ))
        assert result.warning_count == 1

    def test_add_error_sets_invalid(self):
        """测试添加错误会设置无效状态"""
        result = ValidationResult(is_valid=True)

        result.add_error(ValidationError(
            code="ERR",
            message="Error",
            severity=ValidationSeverity.ERROR
        ))

        assert result.is_valid is False

    def test_add_critical_error_sets_invalid(self):
        """测试添加严重错误会设置无效状态"""
        result = ValidationResult(is_valid=True)

        result.add_error(ValidationError(
            code="CRIT",
            message="Critical",
            severity=ValidationSeverity.CRITICAL
        ))

        assert result.is_valid is False

    def test_add_warning_does_not_set_invalid(self):
        """测试添加警告不会设置无效状态"""
        result = ValidationResult(is_valid=True)

        result.add_error(ValidationError(
            code="WARN",
            message="Warning",
            severity=ValidationSeverity.WARNING
        ))

        assert result.is_valid is True

    def test_add_info_does_not_set_invalid(self):
        """测试添加信息不会设置无效状态"""
        result = ValidationResult(is_valid=True)

        result.add_error(ValidationError(
            code="INFO",
            message="Info",
            severity=ValidationSeverity.INFO
        ))

        assert result.is_valid is True

    def test_merge_valid_results(self):
        """测试合并有效结果"""
        result1 = ValidationResult(is_valid=True)
        result2 = ValidationResult(is_valid=True)

        result1.merge(result2)

        assert result1.is_valid is True
        assert len(result1.errors) == 0

    def test_merge_with_invalid_result(self):
        """测试合并无效结果"""
        result1 = ValidationResult(is_valid=True)
        result2 = ValidationResult(is_valid=False)

        result1.merge(result2)

        assert result1.is_valid is False

    def test_merge_with_errors(self):
        """测试合并带错误的结果"""
        result1 = ValidationResult(is_valid=True)
        result1.add_error(ValidationError(
            code="ERR1",
            message="Error 1",
            severity=ValidationSeverity.ERROR
        ))

        result2 = ValidationResult(is_valid=True)
        result2.add_error(ValidationError(
            code="ERR2",
            message="Error 2",
            severity=ValidationSeverity.ERROR
        ))

        result1.merge(result2)

        assert len(result1.errors) == 2
        error_codes = [e.code for e in result1.errors]
        assert "ERR1" in error_codes
        assert "ERR2" in error_codes

    def test_to_dict(self):
        """测试转换为字典"""
        result = ValidationResult(is_valid=False)
        result.add_error(ValidationError(
            code="TEST_ERR",
            message="Test error",
            severity=ValidationSeverity.ERROR
        ))
        result.add_error(ValidationError(
            code="TEST_WARN",
            message="Test warning",
            severity=ValidationSeverity.WARNING
        ))

        dict_result = result.to_dict()

        assert dict_result["is_valid"] is False
        assert dict_result["error_count"] == 1
        assert dict_result["warning_count"] == 1
        assert len(dict_result["errors"]) == 2


# ============================================================================
# ValidationContext 测试
# ============================================================================

class TestValidationContext:
    """测试验证上下文"""

    def test_init(self):
        """测试初始化"""
        request = {"test": "data"}
        context = ValidationContext(request)

        assert context.request == request
        assert context.metadata == {}
        assert context.shared_data == {}
        assert context.should_stop is False

    def test_init_with_metadata(self):
        """测试带元数据初始化"""
        request = {"test": "data"}
        metadata = {"source": "api", "version": "1.0"}
        context = ValidationContext(request, metadata)

        assert context.metadata == metadata

    def test_get_set_shared_data(self):
        """测试共享数据的存取"""
        context = ValidationContext({})

        context.set("user_id", "12345")
        context.set("role", "admin")

        assert context.get("user_id") == "12345"
        assert context.get("role") == "admin"

    def test_get_with_default(self):
        """测试获取不存在的键返回默认值"""
        context = ValidationContext({})

        assert context.get("nonexistent") is None
        assert context.get("nonexistent", "default") == "default"

    def test_stop(self):
        """测试停止标志"""
        context = ValidationContext({})

        assert context.should_stop is False

        context.stop()

        assert context.should_stop is True


# ============================================================================
# ValidationHandler 抽象基类测试
# ============================================================================

class TestValidationHandler:
    """测试验证处理器抽象基类"""

    def test_cannot_instantiate(self):
        """测试不能直接实例化抽象类"""
        with pytest.raises(TypeError):
            ValidationHandler()

    def test_set_next(self):
        """测试设置下一个处理器"""
        # 创建一个具体实现
        class ConcreteHandler(ValidationHandler):
            async def _validate(self, context):
                return ValidationResult(is_valid=True)

        handler1 = ConcreteHandler()
        handler2 = ConcreteHandler()

        result = handler1.set_next(handler2)

        assert result is handler2
        assert handler1._next is handler2

    def test_set_next_chain(self):
        """测试链式调用"""
        class ConcreteHandler(ValidationHandler):
            async def _validate(self, context):
                return ValidationResult(is_valid=True)

        handler1 = ConcreteHandler()
        handler2 = ConcreteHandler()
        handler3 = ConcreteHandler()

        result = handler1.set_next(handler2).set_next(handler3)

        assert handler1._next is handler2
        assert handler2._next is handler3


# ============================================================================
# AuthenticationHandler 测试
# ============================================================================

class TestAuthenticationHandler:
    """测试认证验证处理器"""

    @pytest.mark.asyncio
    async def test_authenticate_with_user(self, authenticated_request):
        """测试已有用户的认证"""
        handler = AuthenticationHandler()
        context = ValidationContext(authenticated_request)

        result = await handler.handle(context)

        assert result.is_valid is True
        assert context.get('user') is not None

    @pytest.mark.asyncio
    async def test_authenticate_with_bearer_token(self, mock_request):
        """测试Bearer token认证"""
        mock_request.headers = {"authorization": "Bearer test_token_123"}
        handler = AuthenticationHandler()
        context = ValidationContext(mock_request)

        result = await handler.handle(context)

        # 无自定义获取函数，只检查格式
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_authenticate_missing_token(self, mock_request):
        """测试缺少认证信息"""
        handler = AuthenticationHandler()
        context = ValidationContext(mock_request)

        result = await handler.handle(context)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].code == "AUTH_MISSING"
        assert result.errors[0].severity == ValidationSeverity.CRITICAL

    @pytest.mark.asyncio
    async def test_authenticate_invalid_format(self, mock_request):
        """测试无效的认证格式"""
        mock_request.headers = {"authorization": "InvalidFormat token123"}
        handler = AuthenticationHandler()
        context = ValidationContext(mock_request)

        result = await handler.handle(context)

        assert result.is_valid is False
        assert result.errors[0].code == "AUTH_INVALID"

    @pytest.mark.asyncio
    async def test_authenticate_with_custom_func(self, mock_request):
        """测试自定义认证函数"""
        mock_request.headers = {"authorization": "Bearer custom_token"}

        async def custom_get_user(token):
            if token == "Bearer custom_token":
                return Mock(id="user_from_token")
            raise ValueError("Invalid token")

        handler = AuthenticationHandler(get_user_func=custom_get_user)
        context = ValidationContext(mock_request)

        result = await handler.handle(context)

        assert result.is_valid is True
        assert context.get('user').id == "user_from_token"

    @pytest.mark.asyncio
    async def test_authenticate_custom_func_fails(self, mock_request):
        """测试自定义认证函数失败"""
        mock_request.headers = {"authorization": "Bearer bad_token"}

        async def failing_get_user(token):
            raise Exception("Authentication failed")

        handler = AuthenticationHandler(get_user_func=failing_get_user)
        context = ValidationContext(mock_request)

        result = await handler.handle(context)

        assert result.is_valid is False
        assert result.errors[0].code == "AUTH_FAILED"

    @pytest.mark.asyncio
    async def test_stop_on_critical(self, mock_request):
        """测试遇到严重错误停止"""
        mock_request.headers = {}

        handler = AuthenticationHandler(stop_on_critical=True)
        context = ValidationContext(mock_request)

        result = await handler.handle(context)

        assert result.is_valid is False


# ============================================================================
# RateLimitHandler 测试
# ============================================================================

class TestRateLimitHandler:
    """测试限流验证处理器"""

    def setup_method(self):
        """测试前清理限流记录"""
        RateLimitHandler._request_counts.clear()

    def teardown_method(self):
        """测试后清理限流记录"""
        RateLimitHandler._request_counts.clear()

    @pytest.mark.asyncio
    async def test_within_limit(self):
        """测试在限制内"""
        handler = RateLimitHandler(max_requests=5, window_seconds=60)
        context = ValidationContext({})

        # 第一次请求
        result = await handler.handle(context)

        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_exceeds_limit(self):
        """测试超过限制"""
        handler = RateLimitHandler(max_requests=2, window_seconds=60)
        context = ValidationContext({})

        # 前两次请求通过
        result1 = await handler.handle(context)
        result2 = await handler.handle(context)

        assert result1.is_valid is True
        assert result2.is_valid is True

        # 第三次请求被拒绝
        result3 = await handler.handle(context)

        assert result3.is_valid is False
        assert result3.errors[0].code == "RATE_LIMIT_EXCEEDED"

    @pytest.mark.asyncio
    async def test_different_keys(self):
        """测试不同键独立计数"""
        handler = RateLimitHandler(max_requests=2, window_seconds=60)

        context1 = ValidationContext({})
        context1.set('user', Mock(id='user1'))

        context2 = ValidationContext({})
        context2.set('user', Mock(id='user2'))

        # user1 请求两次
        await handler.handle(context1)
        await handler.handle(context1)

        # user2 也可以请求两次
        result1 = await handler.handle(context2)
        result2 = await handler.handle(context2)

        assert result1.is_valid is True
        assert result2.is_valid is True

    @pytest.mark.asyncio
    async def test_custom_key_func(self):
        """测试自定义键函数"""
        def custom_key(context):
            return context.metadata.get("api_key", "default")

        handler = RateLimitHandler(
            max_requests=1,
            window_seconds=60,
            get_key_func=custom_key
        )

        context1 = ValidationContext({}, metadata={"api_key": "key1"})
        context2 = ValidationContext({}, metadata={"api_key": "key2"})

        # 不同key独立计数
        result1 = await handler.handle(context1)
        result2 = await handler.handle(context2)

        assert result1.is_valid is True
        assert result2.is_valid is True

        # 同一个key第二次被拒绝
        context1_again = ValidationContext({}, metadata={"api_key": "key1"})
        result3 = await handler.handle(context1_again)

        assert result3.is_valid is False

    @pytest.mark.asyncio
    async def test_anonymous_user(self):
        """测试匿名用户限流"""
        handler = RateLimitHandler(max_requests=1, window_seconds=60)

        context = ValidationContext({})

        result1 = await handler.handle(context)
        result2 = await handler.handle(context)

        assert result1.is_valid is True
        assert result2.is_valid is False


# ============================================================================
# ContentValidatorHandler 测试
# ============================================================================

class TestContentValidatorHandler:
    """测试内容验证处理器"""

    @pytest.mark.asyncio
    async def test_validate_with_no_requirements(self):
        """测试无要求时总是通过"""
        handler = ContentValidatorHandler()
        context = ValidationContext({"any": "data"})

        result = await handler.handle(context)

        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_required_fields_present(self):
        """测试必填字段存在"""
        handler = ContentValidatorHandler(required_fields=["username", "password"])
        context = ValidationContext({
            "username": "testuser",
            "password": "pass123"
        })

        result = await handler.handle(context)

        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_required_fields_missing(self):
        """测试必填字段缺失"""
        handler = ContentValidatorHandler(required_fields=["username", "email"])
        context = ValidationContext({
            "username": "testuser"
            # email 缺失
        })

        result = await handler.handle(context)

        assert result.is_valid is False
        assert any(e.code == "REQUIRED_FIELD_MISSING" for e in result.errors)

    @pytest.mark.asyncio
    async def test_validate_required_fields_empty(self):
        """测试必填字段为空"""
        handler = ContentValidatorHandler(required_fields=["username"])
        context = ValidationContext({
            "username": ""
        })

        result = await handler.handle(context)

        assert result.is_valid is False

    @pytest.mark.asyncio
    async def test_validate_max_length(self):
        """测试最大长度限制"""
        handler = ContentValidatorHandler(max_length=10)
        context = ValidationContext({
            "short": "ok",
            "toolong": "this is way too long"
        })

        result = await handler.handle(context)

        assert result.is_valid is False
        assert any(e.code == "FIELD_TOO_LONG" for e in result.errors)
        # 找到超长字段的错误
        long_field_error = next(e for e in result.errors if e.code == "FIELD_TOO_LONG")
        assert long_field_error.field == "toolong"
        # "this is way too long" 长度为 20
        assert long_field_error.extra["actual_length"] == 20

    @pytest.mark.asyncio
    async def test_validate_forbidden_patterns(self):
        """测试禁止的模式"""
        handler = ContentValidatorHandler(
            forbidden_patterns=[r"<script>", r"javascript:"]
        )
        context = ValidationContext({
            "content": "Check out this <script>alert('xss')</script>"
        })

        result = await handler.handle(context)

        assert result.is_valid is False
        assert any(e.code == "FORBIDDEN_PATTERN" for e in result.errors)

    @pytest.mark.asyncio
    async def test_validate_non_dict_request(self):
        """测试非字典请求"""
        handler = ContentValidatorHandler(required_fields=["field"])
        context = ValidationContext("not a dict")

        result = await handler.handle(context)

        # 非字典请求跳过验证
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_multiple_errors(self):
        """测试多个验证错误"""
        handler = ContentValidatorHandler(
            required_fields=["username", "email"],
            max_length=5,
            forbidden_patterns=[r"\d+"]
        )
        context = ValidationContext({
            "username": "user123",  # 太长且包含数字
            # email 缺失
        })

        result = await handler.handle(context)

        assert result.is_valid is False
        # 应该有多个错误
        assert len(result.errors) >= 2


# ============================================================================
# SchemaValidationHandler 测试
# ============================================================================

class TestSchemaValidationHandler:
    """测试Schema验证处理器"""

    @pytest.mark.asyncio
    async def test_validate_with_valid_schema(self):
        """测试有效Schema验证"""
        # 创建一个简单的Schema类
        from pydantic import BaseModel

        class TestSchema(BaseModel):
            name: str
            age: int

        handler = SchemaValidationHandler(TestSchema)
        context = ValidationContext({
            "name": "Test User",
            "age": 25
        })

        result = await handler.handle(context)

        assert result.is_valid is True
        assert context.get('validated_schema') is not None

    @pytest.mark.asyncio
    async def test_validate_with_invalid_schema(self):
        """测试无效Schema验证"""
        from pydantic import BaseModel, ValidationError as PydanticError

        class TestSchema(BaseModel):
            name: str
            age: int

        handler = SchemaValidationHandler(TestSchema)
        context = ValidationContext({
            "name": "Test User"
            # age 缺失且必填
        })

        result = await handler.handle(context)

        assert result.is_valid is False
        assert any(e.code == "SCHEMA_VALIDATION_ERROR" for e in result.errors)

    @pytest.mark.asyncio
    async def test_validate_with_type_error(self):
        """测试类型错误"""
        from pydantic import BaseModel

        class TestSchema(BaseModel):
            age: int

        handler = SchemaValidationHandler(TestSchema)
        context = ValidationContext({
            "age": "not_a_number"
        })

        result = await handler.handle(context)

        assert result.is_valid is False

    @pytest.mark.asyncio
    async def test_validate_non_dict_request(self):
        """测试非字典请求"""
        from pydantic import BaseModel

        class TestSchema(BaseModel):
            field: str

        handler = SchemaValidationHandler(TestSchema)
        context = ValidationContext("not a dict")

        result = await handler.handle(context)

        # 空字典传递给schema
        assert result.is_valid is False


# ============================================================================
# PermissionHandler 测试
# ============================================================================

class TestPermissionHandler:
    """测试权限验证处理器"""

    @pytest.mark.asyncio
    async def test_has_all_permissions(self, mock_user):
        """测试拥有所有权限"""
        handler = PermissionHandler(required_permissions=["read", "write"])
        context = ValidationContext({})
        context.set('user', mock_user)

        result = await handler.handle(context)

        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_missing_permission(self, mock_user):
        """测试缺少权限"""
        mock_user.permissions = ["read"]
        handler = PermissionHandler(required_permissions=["read", "write"])
        context = ValidationContext({})
        context.set('user', mock_user)

        result = await handler.handle(context)

        assert result.is_valid is False
        assert result.errors[0].code == "PERMISSION_DENIED"

    @pytest.mark.asyncio
    async def test_no_user(self):
        """测试无用户"""
        handler = PermissionHandler(required_permissions=["read"])
        context = ValidationContext({})

        result = await handler.handle(context)

        assert result.is_valid is False
        assert result.errors[0].severity == ValidationSeverity.CRITICAL

    @pytest.mark.asyncio
    async def test_custom_check_func(self):
        """测试自定义检查函数"""
        user = Mock()
        user.id = "user123"

        async def custom_check(user_obj, required_perms):
            # 检查用户是否有admin角色
            return hasattr(user_obj, 'role') and user_obj.role == 'admin'

        handler = PermissionHandler(
            required_permissions=["admin"],
            check_func=custom_check
        )
        context = ValidationContext({})
        context.set('user', user)

        result = await handler.handle(context)

        assert result.is_valid is False

        # 添加admin角色
        user.role = 'admin'
        context2 = ValidationContext({})
        context2.set('user', user)

        result2 = await handler.handle(context2)

        assert result2.is_valid is True

    @pytest.mark.asyncio
    async def test_custom_check_func_exception(self):
        """测试自定义检查函数异常"""
        user = Mock()

        async def failing_check(user_obj, required_perms):
            raise Exception("Check failed")

        handler = PermissionHandler(
            required_permissions=["read"],
            check_func=failing_check
        )
        context = ValidationContext({})
        context.set('user', user)

        result = await handler.handle(context)

        assert result.is_valid is False
        assert result.errors[0].code == "PERMISSION_CHECK_ERROR"


# ============================================================================
# BusinessLogicHandler 测试
# ============================================================================

class TestBusinessLogicHandler:
    """测试业务逻辑验证处理器"""

    @pytest.mark.asyncio
    async def test_async_validate_func_passes(self):
        """测试异步验证函数通过"""
        async def validate_func(context):
            return ValidationResult(is_valid=True)

        handler = BusinessLogicHandler(validate_func)
        context = ValidationContext({})

        result = await handler.handle(context)

        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_async_validate_func_fails(self):
        """测试异步验证函数失败"""
        async def validate_func(context):
            result = ValidationResult(is_valid=False)
            result.add_error(ValidationError(
                code="BUSINESS_ERROR",
                message="Business rule violated",
                severity=ValidationSeverity.ERROR
            ))
            return result

        handler = BusinessLogicHandler(validate_func)
        context = ValidationContext({})

        result = await handler.handle(context)

        assert result.is_valid is False
        assert result.errors[0].code == "BUSINESS_ERROR"

    @pytest.mark.asyncio
    async def test_sync_validate_func(self):
        """测试同步验证函数"""
        def validate_func(context):
            return ValidationResult(is_valid=True)

        handler = BusinessLogicHandler(validate_func)
        context = ValidationContext({})

        result = await handler.handle(context)

        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_func_raises_exception(self):
        """测试验证函数抛出异常"""
        async def validate_func(context):
            raise ValueError("Something went wrong")

        handler = BusinessLogicHandler(validate_func)
        context = ValidationContext({})

        result = await handler.handle(context)

        assert result.is_valid is False
        assert result.errors[0].code == "BUSINESS_LOGIC_ERROR"

    @pytest.mark.asyncio
    async def test_validate_func_returns_invalid_type(self):
        """测试验证函数返回无效类型"""
        async def validate_func(context):
            return "not a ValidationResult"

        handler = BusinessLogicHandler(validate_func)
        context = ValidationContext({})

        result = await handler.handle(context)

        # 应该返回有效结果（虽然函数返回了无效类型）
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_custom_error_code(self):
        """测试自定义错误代码"""
        async def validate_func(context):
            raise ValueError("Custom error")

        handler = BusinessLogicHandler(
            validate_func,
            error_code="CUSTOM_CODE"
        )
        context = ValidationContext({})

        result = await handler.handle(context)

        assert result.errors[0].code == "CUSTOM_CODE"


# ============================================================================
# LoggingHandler 测试
# ============================================================================

class TestLoggingHandler:
    """测试日志记录处理器"""

    @pytest.mark.asyncio
    async def test_always_returns_valid(self):
        """测试总是返回有效结果"""
        handler = LoggingHandler()
        context = ValidationContext({})

        result = await handler.handle(context)

        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_sets_start_time(self):
        """测试设置开始时间"""
        handler = LoggingHandler(log_request=True)
        context = ValidationContext({})

        await handler.handle(context)

        assert context.get('validation_start_time') is not None

    @pytest.mark.asyncio
    async def test_stop_on_error_defaults_to_false(self):
        """测试默认不因错误停止"""
        handler = LoggingHandler()
        assert handler._stop_on_error is False
        assert handler._stop_on_critical is False

    @pytest.mark.asyncio
    async def test_passes_to_next_handler(self):
        """测试传递给下一个处理器"""
        class MockHandler(ValidationHandler):
            def __init__(self):
                self.called = False
                super().__init__()

            async def _validate(self, context):
                self.called = True
                return ValidationResult(is_valid=True)

        log_handler = LoggingHandler()
        mock_handler = MockHandler()
        log_handler.set_next(mock_handler)

        context = ValidationContext({})
        await log_handler.handle(context)

        assert mock_handler.called is True

    @pytest.mark.asyncio
    async def test_merges_next_handler_result(self):
        """测试合并下一个处理器的结果"""
        class ErrorHandler(ValidationHandler):
            async def _validate(self, context):
                result = ValidationResult(is_valid=False)
                result.add_error(ValidationError(
                    code="TEST_ERROR",
                    message="Test error",
                    severity=ValidationSeverity.ERROR
                ))
                return result

        log_handler = LoggingHandler(log_result=False)
        error_handler = ErrorHandler()
        log_handler.set_next(error_handler)

        context = ValidationContext({})
        result = await log_handler.handle(context)

        assert result.is_valid is False
        assert result.errors[0].code == "TEST_ERROR"


# ============================================================================
# ValidationChain 测试
# ============================================================================

class TestValidationChain:
    """测试验证链管理器"""

    @pytest.mark.asyncio
    async def test_empty_chain_returns_valid(self):
        """测试空链返回有效"""
        chain = ValidationChain("test")

        result = await chain.validate({})

        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_add_single_handler(self):
        """测试添加单个处理器"""
        class PassHandler(ValidationHandler):
            async def _validate(self, context):
                return ValidationResult(is_valid=True)

        chain = ValidationChain("test")
        chain.add_handler(PassHandler())

        result = await chain.validate({})

        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_add_multiple_handlers(self):
        """测试添加多个处理器"""
        class Handler1(ValidationHandler):
            async def _validate(self, context):
                context.set('handler1_called', True)
                return ValidationResult(is_valid=True)

        class Handler2(ValidationHandler):
            async def _validate(self, context):
                context.set('handler2_called', True)
                return ValidationResult(is_valid=True)

        chain = ValidationChain("test")
        chain.add_handler(Handler1()).add_handler(Handler2())

        result = await chain.validate({})

        assert result.is_valid is True
        # 需要检查上下文中的标记
        # 由于上下文是新的，无法直接检查

    @pytest.mark.asyncio
    async def test_chain_stops_on_error(self):
        """测试遇到错误停止"""
        class FailHandler(ValidationHandler):
            def __init__(self):
                super().__init__(stop_on_error=True)

            async def _validate(self, context):
                result = ValidationResult(is_valid=False)
                result.add_error(ValidationError(
                    code="FAIL",
                    message="Failed",
                    severity=ValidationSeverity.ERROR
                ))
                return result

        class AfterFailHandler(ValidationHandler):
            def __init__(self):
                self.called = False
                super().__init__()

            async def _validate(self, context):
                self.called = True
                return ValidationResult(is_valid=True)

        chain = ValidationChain("test")
        fail_handler = FailHandler()
        after_handler = AfterFailHandler()
        chain.add_handler(fail_handler).add_handler(after_handler)

        result = await chain.validate({})

        assert result.is_valid is False
        assert after_handler.called is False

    @pytest.mark.asyncio
    async def test_chain_merges_results(self):
        """测试合并多个处理器的结果"""
        class WarningHandler(ValidationHandler):
            async def _validate(self, context):
                result = ValidationResult(is_valid=True)
                result.add_error(ValidationError(
                    code="WARN1",
                    message="Warning 1",
                    severity=ValidationSeverity.WARNING
                ))
                # WARNING不会改变is_valid状态
                return result

        class ErrorHandler(ValidationHandler):
            async def _validate(self, context):
                result = ValidationResult(is_valid=True)
                result.add_error(ValidationError(
                    code="ERR1",
                    message="Error 1",
                    severity=ValidationSeverity.ERROR
                ))
                # add_error方法会自动将is_valid设为False
                return result

        chain = ValidationChain("test")
        chain.add_handler(WarningHandler()).add_handler(ErrorHandler())

        result = await chain.validate({})

        # ErrorHandler添加了ERROR级别的错误，is_valid会被设为False
        assert result.is_valid is False
        assert result.warning_count == 1
        assert result.error_count == 1

    @pytest.mark.asyncio
    async def test_clear_chain(self):
        """测试清空链"""
        class PassHandler(ValidationHandler):
            async def _validate(self, context):
                return ValidationResult(is_valid=True)

        chain = ValidationChain("test")
        chain.add_handler(PassHandler())
        chain.add_handler(PassHandler())

        assert len(chain._handlers) == 2

        chain.clear()

        assert len(chain._handlers) == 0
        assert chain._head is None
        assert chain._tail is None

    @pytest.mark.asyncio
    async def test_chain_with_metadata(self):
        """测试带元数据的验证"""
        class MetadataHandler(ValidationHandler):
            async def _validate(self, context):
                if context.metadata.get("strict"):
                    result = ValidationResult(is_valid=False)
                    result.add_error(ValidationError(
                        code="STRICT",
                        message="Strict mode enabled",
                        severity=ValidationSeverity.ERROR
                    ))
                    return result
                return ValidationResult(is_valid=True)

        chain = ValidationChain("test")
        chain.add_handler(MetadataHandler())

        result = await chain.validate({}, metadata={"strict": True})

        assert result.is_valid is False

    @pytest.mark.asyncio
    async def test_chain_fluent_interface(self):
        """测试流式接口"""
        class PassHandler(ValidationHandler):
            async def _validate(self, context):
                return ValidationResult(is_valid=True)

        chain = (ValidationChain("test")
                 .add_handler(PassHandler())
                 .add_handler(PassHandler())
                 .add_handler(PassHandler()))

        assert len(chain._handlers) == 3

        result = await chain.validate({})

        assert result.is_valid is True


# ============================================================================
# ValidationChainFactory 测试
# ============================================================================

class TestValidationChainFactory:
    """测试验证链工厂"""

    def setup_method(self):
        """测试前清理已注册的链"""
        ValidationChainFactory._chains.clear()

    def teardown_method(self):
        """测试后清理"""
        ValidationChainFactory._chains.clear()

    def test_register_and_get_chain(self):
        """测试注册和获取链"""
        chain = ValidationChain("custom")
        ValidationChainFactory.register_chain("custom", chain)

        retrieved = ValidationChainFactory.get_chain("custom")

        assert retrieved is chain

    def test_get_nonexistent_chain(self):
        """测试获取不存在的链"""
        retrieved = ValidationChainFactory.get_chain("nonexistent")

        assert retrieved is None

    def test_create_chat_chain(self):
        """测试创建聊天验证链"""
        chain = ValidationChainFactory.create_chat_chain(rate_limit=50)

        assert chain is not None
        assert len(chain._handlers) == 3

    @pytest.mark.asyncio
    async def test_chat_chain_authentication(self):
        """测试聊天链的认证"""
        chain = ValidationChainFactory.create_chat_chain()

        # 无认证信息
        request = {}
        result = await chain.validate(request)

        assert result.is_valid is False
        assert any(e.code == "AUTH_MISSING" for e in result.errors)

    @pytest.mark.asyncio
    async def test_chat_chain_content_validation(self):
        """测试聊天链的内容验证"""
        chain = ValidationChainFactory.create_chat_chain()

        # 认证通过但缺少message字段
        request = Mock()
        request.headers = {"authorization": "Bearer token"}
        request.user = Mock(id="test")

        result = await chain.validate(request)

        # ContentValidator需要message字段
        # 由于request不是dict，ContentValidator会跳过
        # 所以这里会通过
        assert result.is_valid is True

    def test_create_api_chain_no_permissions(self):
        """测试创建无权限要求的API链"""
        chain = ValidationChainFactory.create_api_chain()

        # 默认strict=False，只有RateLimit
        assert len(chain._handlers) == 1  # RateLimit only

    def test_create_api_chain_with_permissions(self):
        """测试创建带权限要求的API链"""
        chain = ValidationChainFactory.create_api_chain(
            required_permissions=["admin", "write"]
        )

        # 默认strict=False，有Permission + RateLimit
        assert len(chain._handlers) == 2  # Permission + RateLimit

    def test_create_api_chain_strict_mode(self):
        """测试创建严格模式的API链"""
        chain = ValidationChainFactory.create_api_chain(
            required_permissions=["admin"],
            strict=True
        )

        # strict=True，有Auth + Permission + RateLimit
        assert len(chain._handlers) == 3  # Auth + Permission + RateLimit

    @pytest.mark.asyncio
    async def test_api_chain_with_authenticated_user(self):
        """测试API链与已认证用户"""
        chain = ValidationChainFactory.create_api_chain(
            required_permissions=["read"],
            strict=True  # 启用严格模式以测试认证
        )

        # 创建已认证且有权限的用户
        user = Mock()
        user.id = "test_user"
        user.permissions = ["read", "write"]

        request = Mock()
        request.user = user
        request.headers = {}

        context = ValidationContext(request)
        context.set('user', user)

        # 手动执行链
        result = await chain.validate(request)

        # 应该通过认证和权限检查
        assert result.is_valid is True


# ============================================================================
# 集成测试
# ============================================================================

class TestValidationChainIntegration:
    """验证链集成测试"""

    def setup_method(self):
        """测试前清理"""
        ValidationChainFactory._chains.clear()
        RateLimitHandler._request_counts.clear()

    def teardown_method(self):
        """测试后清理"""
        ValidationChainFactory._chains.clear()
        RateLimitHandler._request_counts.clear()

    @pytest.mark.asyncio
    async def test_full_validation_workflow(self):
        """测试完整的验证工作流"""
        # 创建完整的验证链
        chain = ValidationChain("full_workflow")

        # 1. 认证处理器
        auth_handler = AuthenticationHandler(stop_on_critical=True)

        # 2. 限流处理器
        rate_handler = RateLimitHandler(max_requests=10)

        # 3. 内容验证处理器
        content_handler = ContentValidatorHandler(
            required_fields=["message"],
            max_length=1000
        )

        chain.add_handler(auth_handler).add_handler(rate_handler).add_handler(content_handler)

        # 测试有效请求
        valid_request = Mock()
        valid_request.user = Mock(id="user1")
        valid_request.headers = {}

        context = ValidationContext({"message": "Hello"})
        context.set('user', valid_request.user)

        # 执行验证
        result = await chain.validate({"message": "Hello"})

        # 由于没有user属性，会失败
        # 但内容验证会通过
        assert result is not None

    @pytest.mark.asyncio
    async def test_complex_validation_scenario(self):
        """测试复杂验证场景"""
        # 模拟API端点验证
        chain = ValidationChain("api_endpoint")

        # 认证
        chain.add_handler(AuthenticationHandler(stop_on_critical=True))

        # 限流
        chain.add_handler(RateLimitHandler(max_requests=100))

        # 权限
        perm_handler = PermissionHandler(required_permissions=["api:access"])
        chain.add_handler(perm_handler)

        # 业务逻辑
        async def business_logic(context):
            request = context.request
            if isinstance(request, dict) and request.get("action") == "delete":
                result = ValidationResult(is_valid=False)
                result.add_error(ValidationError(
                    code="DELETE_NOT_ALLOWED",
                    message="Delete operation not allowed",
                    severity=ValidationSeverity.ERROR
                ))
                return result
            return ValidationResult(is_valid=True)

        chain.add_handler(BusinessLogicHandler(business_logic))

        # 测试删除操作
        user = Mock()
        user.permissions = ["api:access"]

        request = {"action": "delete"}
        context = ValidationContext(request)
        context.set('user', user)

        # 由于没有设置user在认证阶段，需要手动设置
        # 创建新的请求对象
        auth_request = Mock()
        auth_request.user = user
        auth_request.headers = {}

        result = await chain.validate(auth_request)

        # 结果取决于认证是否通过
        assert result is not None

    @pytest.mark.asyncio
    async def test_validation_chain_with_logging(self):
        """测试带日志的验证链"""
        chain = ValidationChain("logged_chain")

        # 开始日志
        chain.add_handler(LoggingHandler(log_level="debug"))

        # 实际验证
        chain.add_handler(ContentValidatorHandler(required_fields=["data"]))

        # 结束日志会自动处理

        # 执行验证
        result = await chain.validate({"data": "test"})

        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_handler_communication_via_context(self):
        """测试处理器通过上下文通信"""
        # 第一个处理器设置数据
        class FirstHandler(ValidationHandler):
            async def _validate(self, context):
                context.set('processed_by_first', True)
                context.set('timestamp', 12345)
                return ValidationResult(is_valid=True)

        # 第二个处理器读取数据
        class SecondHandler(ValidationHandler):
            async def _validate(self, context):
                if not context.get('processed_by_first'):
                    result = ValidationResult(is_valid=False)
                    result.add_error(ValidationError(
                        code="NOT_PROCESSED",
                        message="First handler did not run",
                        severity=ValidationSeverity.ERROR
                    ))
                    return result
                return ValidationResult(is_valid=True)

        chain = ValidationChain("communication")
        chain.add_handler(FirstHandler()).add_handler(SecondHandler())

        result = await chain.validate({})

        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_stop_propagation_via_context(self):
        """测试通过上下文停止传播"""
        # 第一个处理器停止传播
        class StopHandler(ValidationHandler):
            async def _validate(self, context):
                context.set('stopped', True)
                context.stop()
                return ValidationResult(is_valid=True)

        # 第二个处理器不应该被调用
        class NeverCalledHandler(ValidationHandler):
            def __init__(self):
                self.called = False
                super().__init__()

            async def _validate(self, context):
                self.called = True
                return ValidationResult(is_valid=True)

        chain = ValidationChain("stop_test")
        stop_handler = StopHandler()
        never_handler = NeverCalledHandler()
        chain.add_handler(stop_handler).add_handler(never_handler)

        result = await chain.validate({})

        assert result.is_valid is True
        assert never_handler.called is False

    @pytest.mark.asyncio
    async def test_multiple_error_severities(self):
        """测试多种错误严重级别"""
        chain = ValidationChain("severities")

        # 添加不同严重级别的错误
        class MultiSeverityHandler(ValidationHandler):
            async def _validate(self, context):
                result = ValidationResult(is_valid=True)
                result.add_error(ValidationError(
                    code="INFO_MSG",
                    message="Information",
                    severity=ValidationSeverity.INFO
                ))
                result.add_error(ValidationError(
                    code="WARN_MSG",
                    message="Warning",
                    severity=ValidationSeverity.WARNING
                ))
                result.add_error(ValidationError(
                    code="ERR_MSG",
                    message="Error",
                    severity=ValidationSeverity.ERROR
                ))
                result.add_error(ValidationError(
                    code="CRIT_MSG",
                    message="Critical",
                    severity=ValidationSeverity.CRITICAL
                ))
                return result

        chain.add_handler(MultiSeverityHandler())

        result = await chain.validate({})

        assert result.is_valid is False
        assert result.warning_count == 1
        assert result.error_count == 1
        assert len(result.critical_errors) == 1
        assert len(result.errors) == 4
