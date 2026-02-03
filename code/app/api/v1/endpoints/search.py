"""
上海宇羲伏天智能科技有限公司出品

文件级注释：语义搜索接口实现
内部逻辑：提供纯向量检索接口，不调用大模型生成回答
"""

from fastapi import APIRouter, Body, HTTPException, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.search import SearchResult
from app.schemas.response import SuccessResponse
from app.services.search_service import SearchService
from app.db.session import get_db

# 变量：创建路由实例
router = APIRouter()

@router.post("", response_model=SuccessResponse[List[SearchResult]])
async def semantic_search(
    query: str = Body(..., embed=True),
    top_k: int = Body(5, embed=True),
    db: AsyncSession = Depends(get_db)
):
    """
    函数级注释：执行纯语义检索接口
    内部逻辑：接收查询词 -> 向量化 -> 在 ChromaDB 中寻找 Top K 最相似片段 -> 查询文件名
    参数：
        query: 搜索关键词字符串
        top_k: 需要返回的最相关结果数量
        db: 数据库会话（用于查询文件名）
    返回值：SuccessResponse[List[SearchResult]] - 统一格式响应
    """
    # 内部变量：保存查询关键词
    search_query = query

    try:
        # 内部逻辑：调用搜索服务获取结果（包含文件名）
        results = await SearchService.semantic_search(search_query, top_k, db=db)

        # 内部逻辑：返回统一格式的成功响应
        return SuccessResponse[List[SearchResult]](
            success=True,
            data=results,
            message="语义搜索成功"
        )
    except Exception as e:
        # 内部逻辑：错误处理
        raise HTTPException(
            status_code=500,
            detail=f"搜索失败: {str(e)}"
        )
