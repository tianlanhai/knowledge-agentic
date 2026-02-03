"""
文件级注释：数据库迁移脚本
内部逻辑：创建 ingest_tasks 表，用于支持异步文件上传处理
"""

import asyncio
from sqlalchemy import text
from app.db.session import engine
from app.models.models import Base
from loguru import logger

async def create_ingest_tasks_table():
    """
    函数级注释：创建 ingest_tasks 表
    内部逻辑：使用 SQLAlchemy 创建所有表，包括新增的 ingest_tasks 表
    """
    try:
        # 内部逻辑：创建所有表（包括 ingest_tasks）
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("数据库表创建成功")
        
        # 内部逻辑：验证表是否创建成功
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='ingest_tasks'"))
            table_exists = result.fetchone()
            
            if table_exists:
                logger.info("ingest_tasks 表已成功创建")
            else:
                logger.warning("ingest_tasks 表创建失败")
                
    except Exception as e:
        logger.error(f"创建数据库表失败: {str(e)}")
        raise

async def migrate():
    """
    函数级注释：执行数据库迁移
    内部逻辑：创建所有必要的表
    """
    logger.info("开始数据库迁移...")
    
    # 内部逻辑：创建表
    await create_ingest_tasks_table()
    
    logger.info("数据库迁移完成")

if __name__ == "__main__":
    # 内部逻辑：运行迁移
    asyncio.run(migrate())
