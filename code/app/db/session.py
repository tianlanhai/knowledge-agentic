"""
上海宇羲伏天智能科技有限公司出品

文件级注释：数据库连接与会话管理
内部逻辑：使用工厂模式获取引擎，支持多数据库供应商
设计模式：依赖注入模式
"""

from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker
from loguru import logger

from app.db.factory import DatabaseFactory

# 变量：会话工厂（延迟初始化）
AsyncSessionLocal: sessionmaker = None


async def init_session_factory():
    """
    函数级注释：初始化会话工厂
    内部逻辑：获取引擎 -> 创建会话工厂
    返回值：无
    """
    global AsyncSessionLocal

    # 内部变量：获取数据库引擎
    engine: AsyncEngine = await DatabaseFactory.get_engine()

    # 内部逻辑：创建会话工厂
    AsyncSessionLocal = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )

    logger.info("会话工厂初始化完成")


async def get_db():
    """
    函数级注释：获取数据库会话的依赖项
    内部逻辑：确保会话工厂已初始化 -> 创建会话 -> yield会话 -> 关闭会话
    内部变量：session - 数据库异步会话
    返回值：AsyncSession - 数据库异步会话
    """
    # 内部逻辑：确保会话工厂已初始化
    global AsyncSessionLocal
    if AsyncSessionLocal is None:
        await init_session_factory()

    # 内部逻辑：使用依赖注入模式，添加异常处理
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            # 内部逻辑：发生错误时回滚事务
            await session.rollback()
            # 内部逻辑：使用 opt 方法避免异常消息中的花括号被格式化
            logger.opt(exception=e).error("数据库会话异常")
            raise
        finally:
            # 内部逻辑：确保会话被关闭
            await session.close()


async def get_engine() -> AsyncEngine:
    """
    函数级注释：获取数据库引擎（用于初始化表结构）
    返回值：AsyncEngine - 数据库异步引擎
    """
    return await DatabaseFactory.get_engine()
