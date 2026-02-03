"""
上海宇羲伏天智能科技有限公司出品

文件级注释：健康检查接口实现
内部逻辑：提供系统和数据库健康状态的检查端点
设计原则：单一职责原则 - 仅处理健康检查相关逻辑
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_db
from app.schemas.response import SuccessResponse
from loguru import logger

# 变量：创建路由实例
router = APIRouter()


@router.get("/db", response_model=SuccessResponse[dict])
async def check_database_health(db: AsyncSession = Depends(get_db)):
    """
    函数级注释：检查数据库连接健康状态
    内部逻辑：执行简单的查询测试数据库连接是否正常
    参数：
        db: 数据库异步会话
    返回值：SuccessResponse[dict] - 包含健康状态和时间戳的响应
    """
    try:
        # 内部逻辑：执行简单查询测试连接
        result = await db.execute(text("SELECT 1"))
        result.scalar()

        # 内部逻辑：返回健康状态
        return SuccessResponse[dict](
            success=True,
            data={
                "status": "healthy",
                "database": "connected",
                "timestamp": datetime.utcnow().isoformat()
            },
            message="数据库连接正常"
        )
    except Exception as e:
        # 内部逻辑：数据库连接异常
        logger.error(f"数据库健康检查失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"数据库不可用: {str(e)}"
        )


@router.get("/", response_model=SuccessResponse[dict])
async def check_system_health():
    """
    函数级注释：检查系统整体健康状态
    内部逻辑：返回API服务的基本状态信息
    返回值：SuccessResponse[dict] - 包含系统状态信息的响应
    """
    logger.info("Health check endpoint called")
    return SuccessResponse[dict](
        success=True,
        data={
            "status": "healthy",
            "service": "knowledge-agentic-api",
            "timestamp": datetime.utcnow().isoformat()
        },
        message="系统运行正常"
    )
