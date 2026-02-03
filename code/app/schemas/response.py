"""
上海宇羲伏天智能科技有限公司出品

文件级注释：统一API响应模型
内部逻辑：定义符合文档规范的统一响应格式，确保所有接口返回格式一致
"""

from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional, Any, List

# 类型变量：泛型数据类型
T = TypeVar('T')

class SuccessResponse(BaseModel, Generic[T]):
    """
    类级注释：统一成功响应模型
    属性：
        success: 成功标识(固定为true)
        data: 返回的具体数据
        message: 操作提示信息
    """
    success: bool = Field(True, description="操作成功标识")
    data: T = Field(..., description="返回的具体数据")
    message: str = Field("操作成功", description="操作提示信息")


class ErrorDetail(BaseModel):
    """
    类级注释：错误详情模型
    属性：
        code: 错误代码
        message: 错误信息
        details: 错误详情(可选)
    """
    code: int = Field(..., description="错误代码(HTTP状态码)")
    message: str = Field(..., description="错误信息")
    details: Optional[str] = Field(None, description="错误详情")


class ErrorResponse(BaseModel):
    """
    类级注释：统一错误响应模型
    属性：
        success: 失败标识(固定为false)
        error: 错误详情对象
    """
    success: bool = Field(False, description="操作失败标识")
    error: ErrorDetail = Field(..., description="错误详情")


class PaginationData(BaseModel):
    """
    类级注释：分页数据模型
    属性：
        items: 数据项列表
        total: 总记录数
        skip: 跳过数量
        limit: 返回限制
    """
    items: List[Any] = Field(..., description="数据项列表")
    total: int = Field(..., description="总记录数")
    skip: int = Field(0, description="跳过数量")
    limit: int = Field(10, description="返回限制")


class ListResponse(BaseModel, Generic[T]):
    """
    类级注释：列表响应模型(带分页)
    属性：
        success: 成功标识
        data: 分页数据
        message: 操作提示信息
    """
    success: bool = Field(True, description="操作成功标识")
    data: PaginationData = Field(..., description="分页数据")
    message: str = Field("查询成功", description="操作提示信息")
