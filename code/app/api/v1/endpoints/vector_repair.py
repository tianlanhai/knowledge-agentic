"""
上海宇羲伏天智能科技有限公司出品

文件级注释：向量库数据修复接口实现
内部逻辑：提供向量库元数据修复功能
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.response import SuccessResponse
from app.services.vector_repair_service import VectorRepairService
from app.db.session import get_db
from typing import Dict, Any

# 变量：创建路由实例
router = APIRouter()


@router.post("", response_model=SuccessResponse[Dict[str, Any]])
async def repair_vector_metadata(
    db: AsyncSession = Depends(get_db)
):
    """
    函数级注释：执行向量库元数据修复
    内部逻辑：调用修复服务，同步数据库和向量库的元数据
    参数：
        db: 数据库会话
    返回值：SuccessResponse[Dict] - 修复结果统计
    """
    result = await VectorRepairService.repair_vector_metadata(db)

    return SuccessResponse[Dict[str, Any]](
        success=True,
        data=result,
        message="向量库修复完成"
    )


@router.get("/status", response_model=SuccessResponse[Dict[str, Any]])
async def get_vector_status(
    db: AsyncSession = Depends(get_db)
):
    """
    函数级注释：获取向量库状态信息
    内部逻辑：查询数据库和向量库的数据统计
    参数：
        db: 数据库会话
    返回值：SuccessResponse[Dict] - 状态信息
    """
    status = await VectorRepairService.get_vector_status(db)

    return SuccessResponse[Dict[str, Any]](
        success=True,
        data=status,
        message="获取状态成功"
    )
