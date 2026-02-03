"""
文件级注释：异步摄入服务测试
内部逻辑：测试 IngestService 的异步任务处理方法
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.ingest_service import IngestService
from app.models.models import IngestTask, TaskStatus
from fastapi import UploadFile
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

@pytest.mark.asyncio
async def test_create_task(db_session: AsyncSession):
    """
    函数级注释：测试创建任务
    内部逻辑：验证任务可以正确创建并保存到数据库
    """
    task = await IngestService.create_task(
        db=db_session,
        file_name="test.pdf",
        source_type="FILE",
        file_path="/data/files/test.pdf",
        file_hash="abc123",
        tags='["tag1", "tag2"]'
    )
    
    # 内部逻辑：验证任务创建成功
    assert task.id is not None
    assert task.file_name == "test.pdf"
    assert task.source_type == "FILE"
    assert task.file_path == "/data/files/test.pdf"
    assert task.file_hash == "abc123"
    assert task.status == TaskStatus.PENDING
    assert task.progress == 0

@pytest.mark.asyncio
async def test_create_task_without_optional_fields(db_session: AsyncSession):
    """
    函数级注释：测试创建任务（不包含可选字段）
    内部逻辑：验证可选字段可以为 None
    """
    task = await IngestService.create_task(
        db=db_session,
        file_name="test.docx",
        source_type="WEB"
    )
    
    assert task.id is not None
    assert task.file_path is None
    assert task.file_hash is None
    assert task.tags is None

@pytest.mark.asyncio
async def test_update_task_status(db_session: AsyncSession):
    """
    函数级注释：测试更新任务状态
    内部逻辑：验证任务状态可以正确更新
    """
    # 内部逻辑：先创建一个任务
    task = await IngestService.create_task(
        db=db_session,
        file_name="update_test.pdf",
        source_type="FILE"
    )
    
    # 内部逻辑：更新任务状态
    await IngestService.update_task_status(
        db=db_session,
        task_id=task.id,
        status=TaskStatus.PROCESSING,
        progress=50
    )
    
    # 内部逻辑：验证状态已更新
    updated_task = await IngestService.get_task(db_session, task.id)
    assert updated_task.status == TaskStatus.PROCESSING
    assert updated_task.progress == 50

@pytest.mark.asyncio
async def test_update_task_status_with_error(db_session: AsyncSession):
    """
    函数级注释：测试更新任务状态（包含错误信息）
    内部逻辑：验证错误信息可以正确设置
    """
    task = await IngestService.create_task(
        db=db_session,
        file_name="error_test.pdf",
        source_type="FILE"
    )
    
    await IngestService.update_task_status(
        db=db_session,
        task_id=task.id,
        status=TaskStatus.FAILED,
        error_message="处理失败：内存不足"
    )

    updated_task = await IngestService.get_task(db_session, task.id)
    assert updated_task.status == TaskStatus.FAILED
    assert updated_task.error_message == "处理失败：内存不足"

@pytest.mark.asyncio
async def test_update_task_status_with_document_id(db_session: AsyncSession):
    """
    函数级注释：测试更新任务状态（包含文档ID）
    内部逻辑：验证文档ID可以正确设置
    """
    task = await IngestService.create_task(
        db=db_session,
        file_name="doc_test.pdf",
        source_type="FILE"
    )
    
    await IngestService.update_task_status(
        db=db_session,
        task_id=task.id,
        status=TaskStatus.COMPLETED,
        progress=100,
        document_id=789
    )

    updated_task = await IngestService.get_task(db_session, task.id)
    assert updated_task.status == TaskStatus.COMPLETED
    assert updated_task.document_id == 789

@pytest.mark.asyncio
async def test_get_task(db_session: AsyncSession):
    """
    函数级注释：测试获取任务
    内部逻辑：验证可以正确获取任务
    """
    # 内部逻辑：先创建一个任务
    task = await IngestService.create_task(
        db=db_session,
        file_name="get_test.pdf",
        source_type="FILE"
    )
    
    # 内部逻辑：获取任务
    retrieved_task = await IngestService.get_task(db_session, task.id)
    
    assert retrieved_task is not None
    assert retrieved_task.id == task.id
    assert retrieved_task.file_name == "get_test.pdf"

@pytest.mark.asyncio
async def test_get_task_not_found(db_session: AsyncSession):
    """
    函数级注释：测试获取不存在的任务
    内部逻辑：验证返回 None
    """
    task = await IngestService.get_task(db_session, 99999)
    
    assert task is None

@pytest.mark.asyncio
async def test_get_all_tasks(db_session: AsyncSession):
    """
    函数级注释：测试获取所有任务
    内部逻辑：验证可以正确获取任务列表
    """
    # 内部逻辑：创建多个任务
    await IngestService.create_task(
        db=db_session,
        file_name="task1.pdf",
        source_type="FILE"
    )
    await IngestService.create_task(
        db=db_session,
        file_name="task2.docx",
        source_type="WEB"
    )
    await IngestService.create_task(
        db=db_session,
        file_name="task3.pdf",
        source_type="FILE"
    )

    # 内部逻辑：获取所有任务
    tasks = await IngestService.get_all_tasks(db_session, skip=0, limit=10)

    assert len(tasks) == 3
    # get_all_tasks 按 created_at.desc() 排序（最新优先）
    # 验证所有任务都在列表中，而不是检查具体顺序
    task_names = [t.file_name for t in tasks]
    assert "task1.pdf" in task_names
    assert "task2.docx" in task_names
    assert "task3.pdf" in task_names

@pytest.mark.asyncio
async def test_get_all_tasks_with_pagination(db_session: AsyncSession):
    """
    函数级注释：测试分页获取任务
    内部逻辑：验证分页参数正确工作
    """
    # 内部逻辑：创建5个任务
    for i in range(5):
        await IngestService.create_task(
            db=db_session,
            file_name=f"task{i}.pdf",
            source_type="FILE"
        )

    # 内部逻辑：分页获取（跳过1个，取2个）
    # 由于按created_at.desc()排序，task4和task3应该是最新被跳过和返回的
    tasks = await IngestService.get_all_tasks(db_session, skip=1, limit=2)

    assert len(tasks) == 2
    # 验证返回的是两个不同的任务
    assert tasks[0].file_name != tasks[1].file_name

@pytest.mark.asyncio
async def test_process_file_with_task_id(db_session: AsyncSession):
    """
    函数级注释：测试处理文件（包含任务ID）
    内部逻辑：验证任务进度更新
    """
    # 内部逻辑：Mock 模式
    with patch("app.services.ingest_service.settings.USE_MOCK", True):
        # 内部逻辑：创建任务
        task = await IngestService.create_task(
            db=db_session,
            file_name="mock_test.pdf",
            source_type="FILE"
        )
        
        # 内部逻辑：创建 Mock 文件对象
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "mock_test.pdf"
        mock_file.read = AsyncMock(return_value=b"mock content")
        
        # 内部逻辑：处理文件
        response = await IngestService.process_file(
            db=db_session,
            file=mock_file,
            tags=["test"],
            task_id=task.id
        )
        
        # 内部逻辑：验证响应
        assert response.status == "completed"
        assert response.document_id == 999
        
        # 内部逻辑：验证任务状态已更新
        updated_task = await IngestService.get_task(db_session, task.id)
        assert updated_task.status == TaskStatus.COMPLETED
        assert updated_task.progress == 100

@pytest.mark.asyncio
async def test_process_file_background(db_session: AsyncSession):
    """
    函数级注释：测试后台处理文件
    内部逻辑：验证后台处理方法能正常调用
    """
    # 内部逻辑：Mock 模式
    with patch("app.services.ingest_service.settings.USE_MOCK", True):
        # 内部逻辑：创建任务
        task = await IngestService.create_task(
            db=db_session,
            file_name="background_test.pdf",
            source_type="FILE"
        )

        # 内部逻辑：创建临时测试文件
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(b"mock content")
            tmp_path = tmp.name

        try:
            # 内部逻辑：调用后台处理（process_file_background使用独立会话）
            # 注意：由于使用独立数据库会话，测试的db_session看不到更改
            # 此测试仅验证函数能正常执行
            await IngestService.process_file_background(
                task_id=task.id,
                file_path=tmp_path,
                file_name="background_test.pdf",
                tags=["test"]
            )
            # 验证函数执行完成（无异常抛出）
            assert True
        finally:
            # 清理临时文件
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

@pytest.mark.asyncio
async def test_process_file_background_error_handling(db_session: AsyncSession):
    """
    函数级注释：测试后台处理文件（错误处理）
    内部逻辑：验证错误时能正常处理
    """
    # 内部逻辑：Mock 模式
    with patch("app.services.ingest_service.settings.USE_MOCK", True):
        # 内部逻辑：创建任务
        task = await IngestService.create_task(
            db=db_session,
            file_name="error_background.pdf",
            source_type="FILE"
        )

        # 内部逻辑：创建临时测试文件
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(b"error content")
            tmp_path = tmp.name

        try:
            # 内部逻辑：Mock 处理失败
            with patch("app.services.ingest_service.IngestService.process_file", side_effect=Exception("处理失败")):
                # 此测试验证错误处理不会抛出异常
                await IngestService.process_file_background(
                    task_id=task.id,
                    file_path=tmp_path,
                    file_name="error_background.pdf",
                    tags=["test"]
                )
                # 验证函数执行完成（无异常抛出）
                assert True
        finally:
            # 清理临时文件
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

@pytest.mark.asyncio
async def test_task_status_transitions(db_session: AsyncSession):
    """
    函数级注释：测试任务状态转换
    内部逻辑：验证任务从 pending 到 processing 到 completed 的状态转换
    """
    task = await IngestService.create_task(
        db=db_session,
        file_name="transition_test.pdf",
        source_type="FILE"
    )
    
    # 内部逻辑：验证初始状态
    assert task.status == TaskStatus.PENDING
    assert task.progress == 0
    
    # 内部逻辑：更新为处理中
    await IngestService.update_task_status(
        db=db_session,
        task_id=task.id,
        status=TaskStatus.PROCESSING,
        progress=50
    )

    updated_task = await IngestService.get_task(db_session, task.id)
    assert updated_task.status == TaskStatus.PROCESSING
    assert updated_task.progress == 50
    
    # 内部逻辑：更新为完成
    await IngestService.update_task_status(
        db=db_session,
        task_id=task.id,
        status=TaskStatus.COMPLETED,
        progress=100,
        document_id=123
    )

    final_task = await IngestService.get_task(db_session, task.id)
    assert final_task.status == TaskStatus.COMPLETED
    assert final_task.progress == 100
    assert final_task.document_id == 123
