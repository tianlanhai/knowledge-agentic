"""
文件级注释：数据库初始化脚本
内部逻辑：创建数据库表结构，符合数据库三原则
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine
from app.models.models import Base
from app.core.config import settings


async def init_database():
    """
    函数级注释：异步初始化数据库表结构
    参数：无
    返回值：无
    内部逻辑：
        1. 创建异步数据库引擎
        2. 使用 SQLAlchemy Base 类创建所有表
        3. 关闭引擎连接
    """
    # 变量：数据库连接 URL
    database_url = f"sqlite+aiosqlite:///{settings.SQLITE_DB_PATH.lstrip('./')}"

    # 内部逻辑：创建异步引擎
    engine = create_async_engine(database_url, echo=True)

    # 内部逻辑：创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 内部逻辑：关闭引擎
    await engine.dispose()

    print(f"数据库初始化成功: {settings.SQLITE_DB_PATH}")


if __name__ == "__main__":
    # 入口：运行异步初始化
    asyncio.run(init_database())
