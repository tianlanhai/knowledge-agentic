"""
上海宇羲伏天智能科技有限公司出品

文件级注释：知识摄入接口实现
内部逻辑：提供文件上传、网页 URL 抓取及文档列表查询的 API 端点
"""

import json
from fastapi import APIRouter, UploadFile, File, Body, Form, Depends, BackgroundTasks
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.ingest import IngestResponse, DBIngestRequest, URLIngestRequest, TaskResponse, TaskListResponse
from app.schemas.response import SuccessResponse
from app.services.ingest_service import IngestService

# 变量：创建路由实例
router = APIRouter()

@router.post("/db", response_model=SuccessResponse[TaskResponse])
async def ingest_db(
    request: DBIngestRequest,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
):
    """
    函数级注释：从数据库同步结构化知识（异步处理）
    内部逻辑：创建任务 -> 后台处理 -> 返回任务ID
    参数：
        request: 数据库同步配置信息
        background_tasks: FastAPI 后台任务
        db: 数据库异步会话，用于持久化元数据
    返回值：SuccessResponse[TaskResponse] - 统一格式响应，包含任务ID
    """
    # 内部变量：生成任务文件名
    task_name = f"DB:{request.table_name}"
    
    # 内部逻辑：创建任务记录
    task = await IngestService.create_task(
        db=db,
        file_name=task_name,
        source_type="DB",
        file_path=request.connection_uri,
        tags=None
    )
    
    # 内部逻辑：添加后台任务
    background_tasks.add_task(
        IngestService.process_db_background,
        task.id,
        request
    )
    
    # 内部逻辑：返回任务信息
    return SuccessResponse[TaskResponse](
        success=True,
        data=TaskResponse(
            id=task.id,
            file_name=task.file_name,
            status=task.status.value,
            progress=task.progress,
            error_message=task.error_message,
            document_id=task.document_id,
            created_at=task.created_at,
            updated_at=task.updated_at
        ),
        message="数据库同步任务已创建，正在后台处理"
    )

@router.post("/file", response_model=SuccessResponse[TaskResponse])
async def ingest_file(
    file: UploadFile = File(...),
    tags: Optional[List[str]] = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
):
    """
    函数级注释：上传并处理本地文件（异步处理）
    内部逻辑：创建任务 -> 保存文件 -> 后台处理 -> 返回任务ID
    参数：
        file: 通过 Multipart 上传的文件对象
        tags: 可选的元数据标签，用于分类
        background_tasks: FastAPI 后台任务
        db: 数据库异步会话，用于持久化元数据
    返回值：SuccessResponse[TaskResponse] - 统一格式响应，包含任务ID
    """
    import uuid
    import os
    from app.core.config import settings
    
    # 内部变量：读取文件内容
    content = await file.read()
    
    # 内部逻辑：确保上传目录存在
    os.makedirs(settings.UPLOAD_FILES_PATH, exist_ok=True)
    
    # 内部变量：生成唯一文件名
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    save_path = os.path.join(settings.UPLOAD_FILES_PATH, unique_filename)
    
    # 内部逻辑：保存文件到磁盘
    with open(save_path, "wb") as f:
        f.write(content)
    
    # 内部逻辑：创建任务记录
    task = await IngestService.create_task(
        db=db,
        file_name=file.filename,
        source_type="FILE",
        file_path=save_path,
        tags=json.dumps(tags) if tags else None
    )
    
    # 内部逻辑：添加后台任务
    background_tasks.add_task(
        IngestService.process_file_background,
        task.id,
        save_path,
        file.filename,
        tags
    )
    
    # 内部逻辑：返回任务信息
    return SuccessResponse[TaskResponse](
        success=True,
        data=TaskResponse(
            id=task.id,
            file_name=task.file_name,
            status=task.status.value,
            progress=task.progress,
            error_message=task.error_message,
            document_id=task.document_id,
            created_at=task.created_at,
            updated_at=task.updated_at
        ),
        message="文件上传成功，正在后台处理"
    )

@router.post("/url", response_model=SuccessResponse[TaskResponse])
async def ingest_url(
    request: URLIngestRequest,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
):
    """
    函数级注释：抓取并解析网页内容（异步处理）
    内部逻辑：创建任务 -> 后台处理 -> 返回任务ID
    参数：
        request: 网页抓取请求对象，包含 URL 和可选标签
        background_tasks: FastAPI 后台任务
        db: 数据库异步会话，用于持久化元数据
    返回值：SuccessResponse[TaskResponse] - 统一格式响应，包含任务ID
    """
    # 内部变量：保存目标 URL 和标签
    target_url = request.url
    tags = request.tags
    
    # 内部逻辑：创建任务记录
    task = await IngestService.create_task(
        db=db,
        file_name=target_url,
        source_type="WEB",
        file_path=target_url,
        tags=json.dumps(tags) if tags else None
    )
    
    # 内部逻辑：添加后台任务
    background_tasks.add_task(
        IngestService.process_url_background,
        task.id,
        target_url,
        tags
    )
    
    # 内部逻辑：返回任务信息
    return SuccessResponse[TaskResponse](
        success=True,
        data=TaskResponse(
            id=task.id,
            file_name=task.file_name,
            status=task.status.value,
            progress=task.progress,
            error_message=task.error_message,
            document_id=task.document_id,
            created_at=task.created_at,
            updated_at=task.updated_at
        ),
        message="网页抓取任务已创建，正在后台处理"
    )

@router.get("/tasks/{task_id}", response_model=SuccessResponse[TaskResponse])
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    函数级注释：获取任务详情
    参数：
        task_id: 任务ID
        db: 数据库异步会话
    返回值：SuccessResponse[TaskResponse] - 任务详情
    """
    # 内部逻辑：查询任务
    task = await IngestService.get_task(db, task_id)
    
    # 内部逻辑：Guard Clause - 任务不存在
    if not task:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 内部逻辑：返回任务信息
    return SuccessResponse[TaskResponse](
        success=True,
        data=TaskResponse(
            id=task.id,
            file_name=task.file_name,
            status=task.status.value,
            progress=task.progress,
            error_message=task.error_message,
            document_id=task.document_id,
            created_at=task.created_at,
            updated_at=task.updated_at
        ),
        message="获取任务成功"
    )

@router.get("/tasks", response_model=SuccessResponse[TaskListResponse])
async def get_all_tasks(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    函数级注释：获取所有任务列表
    参数：
        skip: 跳过数量（用于分页）
        limit: 返回数量
        db: 数据库异步会话
    返回值：SuccessResponse[TaskListResponse] - 任务列表
    """
    # 内部逻辑：查询任务列表
    tasks = await IngestService.get_all_tasks(db, skip, limit)
    
    # 内部逻辑：转换为响应模型
    task_items = [
        TaskResponse(
            id=task.id,
            file_name=task.file_name,
            status=task.status.value,
            progress=task.progress,
            error_message=task.error_message,
            document_id=task.document_id,
            created_at=task.created_at,
            updated_at=task.updated_at
        )
        for task in tasks
    ]
    
    # 内部逻辑：返回任务列表
    return SuccessResponse[TaskListResponse](
        success=True,
        data=TaskListResponse(
            items=task_items,
            total=len(task_items)
        ),
        message="获取任务列表成功"
    )

@router.delete("/tasks/{task_id}", response_model=SuccessResponse[dict])
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    函数级注释：删除指定任务记录
    内部逻辑：调用服务层删除任务，仅删除任务记录，不影响已生成的文档
    参数：
        task_id: 任务ID
        db: 数据库异步会话
    返回值：SuccessResponse[dict] - 统一格式响应
    """
    from fastapi import HTTPException

    # 内部逻辑：调用服务层删除任务
    success = await IngestService.delete_task(db, task_id)

    # 内部逻辑：Guard Clause - 删除失败处理
    if not success:
        raise HTTPException(status_code=404, detail="任务未找到或删除失败")

    # 内部逻辑：返回统一格式的成功响应
    return SuccessResponse[dict](
        success=True,
        data={"task_id": task_id},
        message=f"任务 {task_id} 已成功删除"
    )

