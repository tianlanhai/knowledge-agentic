"""
文件级注释：模型层单元测试
内部逻辑：测试 IngestTask 模型和 TaskStatus 枚举
"""

import pytest
from datetime import datetime
from app.models.models import IngestTask, TaskStatus
from app.utils.timezone_helper import get_local_time

@pytest.mark.asyncio
async def test_ingest_task_creation():
    """
    函数级注释：测试 IngestTask 模型创建
    内部逻辑：验证模型可以正确创建实例
    """
    task = IngestTask(
        id=1,
        file_name="test.pdf",
        file_path="/data/files/test.pdf",
        file_hash="abc123",
        source_type="FILE",
        tags='["tag1", "tag2"]',
        status=TaskStatus.PENDING,
        progress=0,
        error_message=None,
        document_id=None,
        created_at=get_local_time(),
        updated_at=get_local_time()
    )
    
    # 内部逻辑：验证所有字段
    assert task.id == 1
    assert task.file_name == "test.pdf"
    assert task.file_path == "/data/files/test.pdf"
    assert task.file_hash == "abc123"
    assert task.source_type == "FILE"
    assert task.tags == '["tag1", "tag2"]'
    assert task.status == TaskStatus.PENDING
    assert task.progress == 0
    assert task.error_message is None
    assert task.document_id is None

@pytest.mark.asyncio
async def test_ingest_task_with_progress():
    """
    函数级注释：测试任务进度更新
    内部逻辑：验证进度字段可以正确更新
    """
    task = IngestTask(
        id=2,
        file_name="test.docx",
        source_type="FILE",
        status=TaskStatus.PROCESSING,
        progress=50,
        created_at=get_local_time(),
        updated_at=get_local_time()
    )
    
    assert task.progress == 50
    assert task.status == TaskStatus.PROCESSING

@pytest.mark.asyncio
async def test_ingest_task_with_error():
    """
    函数级注释：测试任务失败状态
    内部逻辑：验证错误信息可以正确设置
    """
    task = IngestTask(
        id=3,
        file_name="failed.pdf",
        source_type="FILE",
        status=TaskStatus.FAILED,
        progress=0,
        error_message="处理失败：文件格式不支持",
        created_at=get_local_time(),
        updated_at=get_local_time()
    )
    
    assert task.status == TaskStatus.FAILED
    assert task.error_message == "处理失败：文件格式不支持"

@pytest.mark.asyncio
async def test_ingest_task_completed():
    """
    函数级注释：测试任务完成状态
    内部逻辑：验证完成状态和文档ID可以正确设置
    """
    task = IngestTask(
        id=4,
        file_name="completed.pdf",
        source_type="FILE",
        status=TaskStatus.COMPLETED,
        progress=100,
        document_id=123,
        created_at=get_local_time(),
        updated_at=get_local_time()
    )
    
    assert task.status == TaskStatus.COMPLETED
    assert task.progress == 100
    assert task.document_id == 123

@pytest.mark.asyncio
async def test_task_status_enum():
    """
    函数级注释：测试 TaskStatus 枚举
    内部逻辑：验证所有状态值
    """
    # 内部逻辑：验证枚举值
    assert TaskStatus.PENDING.value == "pending"
    assert TaskStatus.PROCESSING.value == "processing"
    assert TaskStatus.COMPLETED.value == "completed"
    assert TaskStatus.FAILED.value == "failed"

@pytest.mark.asyncio
async def test_ingest_task_without_tags():
    """
    函数级注释：测试无标签的任务
    内部逻辑：验证 tags 字段可以为 None
    """
    task = IngestTask(
        id=5,
        file_name="notags.pdf",
        source_type="FILE",
        tags=None,
        status=TaskStatus.PENDING,
        created_at=get_local_time(),
        updated_at=get_local_time()
    )
    
    assert task.tags is None

@pytest.mark.asyncio
async def test_ingest_task_web_source():
    """
    函数级注释：测试网页来源任务
    内部逻辑：验证 WEB 类型任务
    """
    task = IngestTask(
        id=6,
        file_name="https://example.com",
        source_type="WEB",
        status=TaskStatus.PROCESSING,
        progress=30,
        created_at=get_local_time(),
        updated_at=get_local_time()
    )
    
    assert task.source_type == "WEB"
    assert task.file_name == "https://example.com"

@pytest.mark.asyncio
async def test_ingest_task_db_source():
    """
    函数级注释：测试数据库来源任务
    内部逻辑：验证 DB 类型任务
    """
    task = IngestTask(
        id=7,
        file_name="db:users",
        source_type="DB",
        status=TaskStatus.COMPLETED,
        progress=100,
        document_id=456,
        created_at=get_local_time(),
        updated_at=get_local_time()
    )
    
    assert task.source_type == "DB"
    assert task.file_name == "db:users"
