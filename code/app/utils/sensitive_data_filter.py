"""
上海宇羲伏天智能科技有限公司出品

文件级注释：敏感信息过滤工具类
内部逻辑：使用正则表达式识别并过滤文本中的敏感信息（手机号、邮箱）
设计原则：单一职责、开闭原则、依赖倒置
"""

import re
from typing import Dict, List, Optional, Tuple
from enum import Enum
from loguru import logger


class SensitiveDataType(str, Enum):
    """
    类级注释：敏感信息类型枚举
    属性：
        MOBILE: 手机号
        EMAIL: 邮箱
    """
    MOBILE = "mobile"
    EMAIL = "email"


class MaskStrategy(str, Enum):
    """
    类级注释：脱敏策略枚举
    属性：
        FULL: 完全替换为占位符
        PARTIAL: 部分脱敏（如：138****1234）
        HASH: 替换为哈希值
    """
    FULL = "full"        # 完全替换：[已隐藏手机号]
    PARTIAL = "partial"  # 部分脱敏：138****1234
    HASH = "hash"        # 哈希替换


class SensitiveDataFilter:
    """
    类级注释：敏感信息过滤器
    设计模式：策略模式、单例模式

    功能：
        1. 识别中国大陆手机号（11位，1开头）
        2. 识别邮箱地址
    """

    # 内部常量：正则表达式模式
    # 手机号：1开头，第二位3-9，共11位数字
    _MOBILE_PATTERN = re.compile(
        r'(?<!\d)(1[3-9]\d{9})(?!\d)',
        re.IGNORECASE
    )

    # 邮箱：标准格式 username@domain.extension
    # 内部逻辑：不使用 \b 边界，因为中文字符环境下 \b 不工作
    _EMAIL_PATTERN = re.compile(
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        re.IGNORECASE
    )

    def __init__(
        self,
        mask_strategy: MaskStrategy = MaskStrategy.FULL,
        enable_mobile_filter: bool = True,
        enable_email_filter: bool = True,
        custom_placeholder: Optional[Dict[SensitiveDataType, str]] = None
    ):
        """
        函数级注释：初始化过滤器
        参数：
            mask_strategy: 脱敏策略，默认完全替换
            enable_mobile_filter: 是否启用手机号过滤
            enable_email_filter: 是否启用邮箱过滤
            custom_placeholder: 自定义占位符
        """
        self.mask_strategy = mask_strategy
        self.enable_mobile_filter = enable_mobile_filter
        self.enable_email_filter = enable_email_filter

        # 内部变量：占位符配置
        self.placeholders = custom_placeholder or {
            SensitiveDataType.MOBILE: "[已隐藏手机号]",
            SensitiveDataType.EMAIL: "[已隐藏邮箱]",
        }

    def filter_mobile(self, text: str) -> Tuple[str, int]:
        """
        函数级注释：过滤手机号
        内部逻辑：使用正则表达式匹配手机号 -> 根据策略脱敏 -> 返回结果
        参数：
            text: 待过滤文本
        返回值：Tuple[过滤后文本, 替换数量]
        """
        if not self.enable_mobile_filter:
            return text, 0

        count = 0

        def replace_mobile(match: re.Match) -> str:
            nonlocal count
            count += 1
            mobile = match.group(1)

            if self.mask_strategy == MaskStrategy.FULL:
                return self.placeholders[SensitiveDataType.MOBILE]
            elif self.mask_strategy == MaskStrategy.PARTIAL:
                return f"{mobile[:3]}****{mobile[7:]}"
            else:  # HASH
                return f"[手机号:{hash(mobile) % 10000:04d}]"

        result = self._MOBILE_PATTERN.sub(replace_mobile, text)
        return result, count

    def filter_email(self, text: str) -> Tuple[str, int]:
        """
        函数级注释：过滤邮箱地址
        内部逻辑：使用正则表达式匹配邮箱 -> 根据策略脱敏 -> 返回结果
        参数：
            text: 待过滤文本
        返回值：Tuple[过滤后文本, 替换数量]
        """
        if not self.enable_email_filter:
            return text, 0

        count = 0

        def replace_email(match: re.Match) -> str:
            nonlocal count
            count += 1
            email = match.group(0)

            if self.mask_strategy == MaskStrategy.FULL:
                return self.placeholders[SensitiveDataType.EMAIL]
            elif self.mask_strategy == MaskStrategy.PARTIAL:
                # user@domain.com -> u***@domain.com
                parts = email.split('@')
                username = parts[0]
                masked_username = username[0] + '***' if len(username) > 1 else '***'
                return f"{masked_username}@{parts[1]}"
            else:  # HASH
                return f"[邮箱:{hash(email) % 10000:04d}]"

        result = self._EMAIL_PATTERN.sub(replace_email, text)
        return result, count

    def filter_all(self, text: str) -> Tuple[str, Dict[SensitiveDataType, int]]:
        """
        函数级注释：综合过滤所有敏感信息
        内部逻辑：依次应用各类过滤器 -> 统计结果 -> 记录日志
        参数：
            text: 待过滤文本
        返回值：Tuple[过滤后文本, 各类型替换统计]
        """
        stats = {
            SensitiveDataType.MOBILE: 0,
            SensitiveDataType.EMAIL: 0
        }
        result = text

        # 内部逻辑：按优先级依次过滤
        result, mobile_count = self.filter_mobile(result)
        stats[SensitiveDataType.MOBILE] = mobile_count

        result, email_count = self.filter_email(result)
        stats[SensitiveDataType.EMAIL] = email_count

        # 内部逻辑：记录过滤日志
        total_filtered = sum(stats.values())
        if total_filtered > 0:
            logger.info(
                f"敏感信息过滤完成: 手机号={mobile_count}, "
                f"邮箱={email_count}"
            )

        return result, stats

    def is_sensitive(self, text: str) -> bool:
        """
        函数级注释：检测文本是否包含敏感信息
        参数：
            text: 待检测文本
        返回值：bool - 是否包含敏感信息
        """
        if self.enable_mobile_filter and self._MOBILE_PATTERN.search(text):
            return True
        if self.enable_email_filter and self._EMAIL_PATTERN.search(text):
            return True
        return False


class StreamingSensitiveFilter:
    """
    类级注释：流式敏感信息过滤器
    内部逻辑：维护滑动窗口，处理跨chunk敏感信息
    """

    def __init__(self, filter_instance: SensitiveDataFilter, window_size: int = 20):
        """
        函数级注释：初始化流式过滤器
        参数：
            filter_instance: 基础过滤器实例
            window_size: 缓冲窗口大小（字符数）
        """
        self.filter = filter_instance
        self.window_size = window_size
        self.buffer = ""  # 内部变量：缓冲区

    def process(self, chunk: str) -> str:
        """
        函数级注释：处理单个chunk
        内部逻辑：添加到缓冲 -> 检测完整敏感信息 -> 输出安全部分
        参数：
            chunk: 输入文本块
        返回值：过滤后的安全文本
        """
        # 内部逻辑：将新chunk加入缓冲区
        self.buffer += chunk

        # 内部逻辑：当缓冲区足够大时，输出前面部分
        if len(self.buffer) > self.window_size * 2:
            # 输出前面部分（保留末尾作为重叠区）
            output_part = self.buffer[:-self.window_size]
            # 过滤输出部分
            filtered_output, _ = self.filter.filter_all(output_part)
            # 更新缓冲区，保留末尾
            self.buffer = self.buffer[-self.window_size:]
            return filtered_output

        # 缓冲区未满，暂不输出
        return ""

    def flush(self) -> str:
        """
        函数级注释：刷新缓冲区，输出剩余内容
        返回值：过滤后的剩余文本
        """
        if not self.buffer:
            return ""

        result, _ = self.filter.filter_all(self.buffer)
        self.buffer = ""
        return result


# 内部变量：默认过滤器实例（懒加载单例模式）
_default_filter: Optional[SensitiveDataFilter] = None


def get_filter() -> SensitiveDataFilter:
    """
    函数级注释：获取默认过滤器实例
    内部逻辑：懒加载单例模式，根据配置创建实例
    返回值：SensitiveDataFilter实例
    """
    global _default_filter
    if _default_filter is None:
        from app.core.config import settings

        # 内部逻辑：根据配置确定脱敏策略
        strategy_map = {
            "full": MaskStrategy.FULL,
            "partial": MaskStrategy.PARTIAL,
            "hash": MaskStrategy.HASH,
        }
        strategy = strategy_map.get(
            settings.SENSITIVE_DATA_MASK_STRATEGY.lower(),
            MaskStrategy.FULL
        )

        _default_filter = SensitiveDataFilter(
            mask_strategy=strategy,
            enable_mobile_filter=settings.FILTER_MOBILE,
            enable_email_filter=settings.FILTER_EMAIL,
        )
    return _default_filter


def reset_filter():
    """
    函数级注释：重置过滤器实例
    内部逻辑：清除缓存的单例实例，用于配置变更时重新初始化
    """
    global _default_filter
    _default_filter = None
