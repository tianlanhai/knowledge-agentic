# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：时区助手模块测试
内部逻辑：测试timezone_helper模块的功能
"""

import pytest
from datetime import datetime
from zoneinfo import ZoneInfo

from app.utils.timezone_helper import get_local_time, get_timezone


class TestTimezoneHelperCoverage:
    """
    类级注释：时区助手覆盖率补充测试
    """

    def test_get_local_time(self):
        """测试目的：覆盖get_local_time函数"""
        result = get_local_time()

        assert isinstance(result, datetime)
        # 返回的是naive datetime(没有时区信息)
        assert result.tzinfo is None

    def test_get_timezone(self):
        """测试目的：覆盖get_timezone函数"""
        result = get_timezone()

        assert isinstance(result, ZoneInfo)

    def test_get_local_time_is_recent(self):
        """测试目的：验证返回的时间是最近的"""
        before = datetime.now()
        result = get_local_time()
        after = datetime.now()

        # 结果应该在当前时间前后一小段时间内
        assert before <= result <= after
