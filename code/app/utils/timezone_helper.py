"""
上海宇羲伏天智能科技有限公司出品

文件级注释：时区处理工具模块
内部逻辑：提供统一的本地时间获取函数，支持配置化时区管理
设计原则：单一职责原则 - 仅处理时区转换相关逻辑
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from app.core.config import settings


def get_local_time() -> datetime:
    """
    函数级注释：获取当前本地时间（北京时间）
    内部逻辑：读取配置的时区 -> 创建带时区的时间对象 -> 返回naive datetime用于存储

    返回值：datetime - 不带时区信息的本地时间（直接存储到数据库）

    注意事项：
        - 返回naive datetime（无时区信息），因为数据库字段不带时区
        - 由配置决定使用的时区，默认为Asia/Shanghai
    """
    # 内部变量：从配置获取时区
    tz_name = settings.TIMEZONE

    # 内部逻辑：使用zoneinfo创建时区对象（Python 3.9+）
    tz = ZoneInfo(tz_name)

    # 内部逻辑：获取当前带时区的时间
    now_with_tz = datetime.now(tz)

    # 内部逻辑：返回naive datetime（去掉时区信息）用于数据库存储
    # 这样存储的时间就是配置的本地时间
    return now_with_tz.replace(tzinfo=None)


def get_timezone() -> ZoneInfo:
    """
    函数级注释：获取配置的时区对象

    返回值：ZoneInfo - 配置的时区对象
    """
    # 内部变量：从配置获取时区名称
    tz_name = settings.TIMEZONE

    # 返回值：ZoneInfo时区对象
    return ZoneInfo(tz_name)
