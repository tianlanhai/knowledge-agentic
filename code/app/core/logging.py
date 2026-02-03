"""
上海宇羲伏天智能科技有限公司出品

文件级注释：日志管理工具
内部逻辑：集成 loguru 提供格式化和持久化的日志记录功能
"""

import sys
from loguru import logger
from app.core.config import settings

def setup_logging():
    """
    函数级注释：配置全局日志记录器
    内部逻辑：移除默认处理器，添加标准输出处理器和文件处理器
    """
    # 内部逻辑：移除默认的日志处理
    logger.remove()

    # 内部逻辑：添加标准输出处理，包含彩色输出和自定义格式
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True
    )

    # 内部逻辑：添加文件日志记录，按天轮转
    logger.add(
        "logs/app.log",
        rotation="1 day",
        retention="7 days",
        level=settings.LOG_LEVEL,
        encoding="utf-8"
    )

# 变量：初始化日志配置
setup_logging()

# 导出 logger 供其他模块使用
__all__ = ["logger"]




