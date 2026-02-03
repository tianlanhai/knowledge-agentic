# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：安全错误消息处理模块
内部逻辑：根据环境返回安全的错误消息，防止敏感信息泄露
设计原则：最小权限原则、防御性编程
职责：统一处理 API 错误响应，确保生产环境不泄露系统内部信息
"""

from typing import Optional
from functools import lru_cache
from loguru import logger

from app.core.config import settings


class SecurityErrorHandler:
    """
    类级注释：安全错误消息处理器
    设计模式：单例模式（通过 lru_cache 实现）
    职责：
        1. 根据环境返回不同详细程度的错误消息
        2. 记录详细错误日志用于排查
        3. 返回安全的通用错误消息给客户端

    使用示例：
        handler = get_security_handler()
        safe_message = handler.get_safe_message(exception)
    """

    # 内部变量：生产环境通用错误消息
    PRODUCTION_MESSAGES = {
        "database": "数据库操作失败，请稍后重试",
        "validation": "请求数据格式不正确",
        "authentication": "身份验证失败",
        "authorization": "权限不足",
        "not_found": "请求的资源不存在",
        "external_service": "外部服务调用失败",
        "default": "系统错误，请稍后重试"
    }

    # 内部变量：不需要脱敏的异常类型白名单
    SAFE_EXCEPTION_TYPES = (
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        IndexError,
        # 自定义的业务异常可以添加到这里
    )

    def __init__(self):
        """
        函数级注释：初始化安全错误处理器
        内部变量：is_development - 是否为开发环境
        """
        # 内部变量：根据 DEBUG 配置判断是否为开发环境
        self.is_development = getattr(settings, 'DEBUG', False)

    def get_safe_message(
        self,
        error: Exception,
        error_type: str = "default",
        include_log: bool = True
    ) -> str:
        """
        函数级注释：获取安全的错误消息
        内部逻辑：开发环境返回详细错误 / 生产环境返回通用消息
        参数：
            error - 原始异常对象
            error_type - 错误类型（用于选择通用消息）
            include_log - 是否记录详细日志
        返回值：安全的错误消息字符串

        使用示例：
            try:
                # 业务逻辑
            except Exception as e:
                message = handler.get_safe_message(e, "database")
                raise HTTPException(status_code=500, detail=message)
        """
        # 内部逻辑：记录详细错误日志（包含堆栈信息）
        if include_log:
            logger.error(f"业务异常: {type(error).__name__}: {str(error)}", exc_info=True)

        # 内部逻辑：开发环境返回详细错误信息
        if self.is_development:
            return f"{error_type.upper() if error_type != 'default' else 'ERROR'}: {str(error)}"

        # 内部逻辑：生产环境返回安全的通用消息
        # 对于安全的异常类型（如 ValueError），可以返回具体消息
        if isinstance(error, self.SAFE_EXCEPTION_TYPES) and error_type == "validation":
            return str(error)

        # 内部变量：获取通用错误消息
        message = self.PRODUCTION_MESSAGES.get(
            error_type,
            self.PRODUCTION_MESSAGES["default"]
        )
        return message

    def get_safe_detail(
        self,
        error: Exception,
        error_type: str = "default",
        error_code: Optional[str] = None
    ) -> dict:
        """
        函数级注释：获取安全的错误详情（结构化）
        内部逻辑：返回包含错误码和消息的结构化数据
        参数：
            error - 原始异常对象
            error_type - 错误类型
            error_code - 业务错误码（可选）
        返回值：包含 message 和可选 code 的字典

        使用示例：
            detail = handler.get_safe_detail(e, "database", "DB_001")
            raise HTTPException(status_code=500, detail=detail)
        """
        detail = {
            "message": self.get_safe_message(error, error_type)
        }

        # 内部逻辑：如果有错误码，添加到响应中
        if error_code:
            detail["code"] = error_code

        # 内部逻辑：开发环境添加更多调试信息
        if self.is_development:
            detail["error_type"] = type(error).__name__
            detail["original_message"] = str(error)

        return detail

    def create_http_exception_detail(
        self,
        error: Exception,
        status_code: int = 500,
        error_type: str = "default",
        error_code: Optional[str] = None
    ) -> str:
        """
        函数级注释：创建 HTTPException 的 detail 参数
        内部逻辑：返回字符串形式的错误详情
        参数：
            error - 原始异常对象
            status_code - HTTP 状态码（用于推断错误类型）
            error_type - 错误类型（覆盖自动推断）
            error_code - 业务错误码
        返回值：错误详情字符串

        使用示例：
            detail = handler.create_http_exception_detail(e, status_code=500)
            raise HTTPException(status_code=500, detail=detail)
        """
        # 内部逻辑：根据状态码自动推断错误类型
        if error_type == "default":
            error_type_map = {
                400: "validation",
                401: "authentication",
                403: "authorization",
                404: "not_found",
                500: "default",
                502: "external_service",
                503: "external_service",
            }
            error_type = error_type_map.get(status_code, "default")

        # 内部逻辑：获取结构化详情
        detail_dict = self.get_safe_detail(error, error_type, error_code)

        # 内部逻辑：转换为 JSON 字符串（适用于 FastAPI）
        import json
        return json.dumps(detail_dict, ensure_ascii=False)


# 内部变量：单例实例缓存
@lru_cache(maxsize=1)
def get_security_handler() -> SecurityErrorHandler:
    """
    函数级注释：获取安全错误处理器单例
    设计模式：单例模式 + 缓存优化
    返回值：SecurityErrorHandler 实例

    使用示例：
        handler = get_security_handler()
        message = handler.get_safe_message(exception)
    """
    return SecurityErrorHandler()


# 导出公共接口
__all__ = [
    'SecurityErrorHandler',
    'get_security_handler',
]
