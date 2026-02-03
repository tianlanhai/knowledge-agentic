"""
上海宇羲伏天智能科技有限公司出品

文件级注释：文档管理接口实现
内部逻辑：提供已摄入文档的查询功能
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.document import DocumentListResponse
from app.schemas.response import SuccessResponse
from app.services.ingest_service import IngestService

# 变量：创建路由实例
router = APIRouter()

@router.get("", response_model=SuccessResponse[DocumentListResponse])
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: str = Query(None, description="搜索关键词"),
    db: AsyncSession = Depends(get_db)
):
    """
    函数级注释：获取已摄入的文档列表
    内部逻辑：调用服务层查询文档列表
    参数：
        skip: 分页跳过数量
        limit: 分页返回限制数量
        search: 搜索关键词（可选）
        db: 数据库异步会话
    返回值：SuccessResponse[DocumentListResponse] - 统一格式响应
    """
    # 内部逻辑：调用服务层查询文档列表
    result = await IngestService.get_documents(db, skip, limit, search)

    # 内部逻辑：返回统一格式的成功响应
    return SuccessResponse[DocumentListResponse](
        success=True,
        data=result,
        message="查询文档列表成功"
    )

@router.delete("/{doc_id}", response_model=SuccessResponse[dict])
async def delete_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    函数级注释：删除指定 ID 的文档及其关联向量
    内部逻辑：调用 IngestService 执行物理与逻辑删除
    参数：
        doc_id: 文档 ID
        db: 数据库异步会话
    返回值：SuccessResponse[dict] - 统一格式响应
    """
    # 内部逻辑：执行删除操作
    success = await IngestService.delete_document(db, doc_id)
    
    # 内部逻辑：Guard Clause - 删除失败处理
    if not success:
        raise HTTPException(status_code=404, detail="文档未找到或删除失败")
    
    # 内部逻辑：返回统一格式的成功响应
    return SuccessResponse[dict](
        success=True,
        data={"doc_id": doc_id},
        message=f"文档 {doc_id} 已成功删除"
    )

