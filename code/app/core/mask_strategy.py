# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：脱敏策略模块
内部逻辑：提供可复用的数据脱敏策略，支持多种脱敏方式
设计模式：策略模式、单例模式
设计原则：DRY（不重复）、开闭原则（对扩展开放）、SOLID（依赖倒置）
"""

from abc import ABC, abstractmethod
from typing import Optional
from enum import Enum


class MaskType(str, Enum):
    """
    类级注释：脱敏类型枚举
    属性：
        FULL: 完全脱敏，显示为 ****
        PARTIAL: 部分脱敏，显示前4后4
        EMAIL: 邮箱脱敏，如 a***@example.com
        MOBILE: 手机号脱敏，如 138****1234
    """
    FULL = "full"
    PARTIAL = "partial"
    EMAIL = "email"
    MOBILE = "mobile"


class MaskStrategy(ABC):
    """
    类级注释：脱敏策略抽象基类
    设计模式：策略模式
    职责：定义脱敏策略的接口
    """

    @abstractmethod
    def mask(self, value: str) -> str:
        """
        函数级注释：执行脱敏操作（抽象方法）
        参数：
            value: 待脱敏的原始值
        返回值：脱敏后的值
        """
        pass


class FullMaskStrategy(MaskStrategy):
    """
    类级注释：完全脱敏策略
    职责：将敏感数据完全替换为星号
    """

    def mask(self, value: str) -> str:
        """
        函数级注释：完全脱敏
        内部逻辑：如果值为空返回空字符串，否则返回固定长度的星号
        参数：
            value: 待脱敏的原始值
        返回值：脱敏后的值（****）
        """
        return "****" if value else ""


class PartialMaskStrategy(MaskStrategy):
    """
    类级注释：部分脱敏策略
    职责：显示前4位和后4位，中间用星号替换
    """

    def mask(self, value: str) -> str:
        """
        函数级注释：部分脱敏
        内部逻辑：显示前4位和后4位，中间用星号替换
        参数：
            value: 待脱敏的原始值
        返回值：脱敏后的值（如 sk-****1234）
        """
        if not value:
            return ""
        if len(value) <= 8:
            return "****"
        # 保留前4位和后4位，中间用4个星号替换
        return f"{value[:4]}****{value[-4:]}"


class EmailMaskStrategy(MaskStrategy):
    """
    类级注释：邮箱脱敏策略
    职责：保留邮箱前缀首字符和域名，中间用星号替换
    """

    def mask(self, value: str) -> str:
        """
        函数级注释：邮箱脱敏
        内部逻辑：保留邮箱前缀首字符和域名，中间用星号替换
        参数：
            value: 待脱敏的邮箱地址
        返回值：脱敏后的值（如 a***@example.com）
        """
        if not value or "@" not in value:
            return ""
        local, domain = value.split("@", 1)
        return f"{local[0]}***@{domain}"


class MobileMaskStrategy(MaskStrategy):
    """
    类级注释：手机号脱敏策略
    职责：显示前3位和后4位，中间用星号替换
    """

    def mask(self, value: str) -> str:
        """
        函数级注释：手机号脱敏
        内部逻辑：显示前3位和后4位，中间用星号替换
        参数：
            value: 待脱敏的手机号
        返回值：脱敏后的值（如 138****1234）
        """
        if not value or len(value) < 7:
            return ""
        return f"{value[:3]}****{value[-4:]}"


class MaskUtils:
    """
    类级注释：脱敏工具类
    设计模式：策略模式、单例模式
    职责：
        1. 管理脱敏策略实例
        2. 提供统一的脱敏方法接口
        3. 支持运行时切换脱敏策略
    """

    # 内部类变量：默认脱敏策略
    _default_strategy: MaskStrategy = PartialMaskStrategy()

    # 内部类变量：策略类型到策略实例的映射
    _strategies: dict = {
        MaskType.FULL: FullMaskStrategy(),
        MaskType.PARTIAL: PartialMaskStrategy(),
        MaskType.EMAIL: EmailMaskStrategy(),
        MaskType.MOBILE: MobileMaskStrategy(),
    }

    @classmethod
    def set_default_strategy(cls, strategy: MaskStrategy) -> None:
        """
        函数级注释：设置默认脱敏策略
        参数：
            strategy: 新的默认策略
        """
        cls._default_strategy = strategy

    @classmethod
    def set_default_mask_type(cls, mask_type: MaskType) -> None:
        """
        函数级注释：通过枚举类型设置默认脱敏策略
        参数：
            mask_type: 脱敏类型枚举
        """
        strategy = cls._strategies.get(mask_type)
        if strategy:
            cls._default_strategy = strategy

    @classmethod
    def mask_api_key(cls, api_key: Optional[str], mask_type: Optional[MaskType] = None) -> str:
        """
        函数级注释：API密钥脱敏
        内部逻辑：使用指定的或默认的脱敏策略对API密钥进行脱敏
        参数：
            api_key: 待脱敏的API密钥
            mask_type: 可选的脱敏类型，不传则使用默认策略
        返回值：脱敏后的API密钥
        """
        if not api_key:
            return ""
        if mask_type:
            strategy = cls._strategies.get(mask_type, cls._default_strategy)
            return strategy.mask(api_key)
        return cls._default_strategy.mask(api_key)

    @classmethod
    def mask_email(cls, email: Optional[str]) -> str:
        """
        函数级注释：邮箱脱敏
        参数：
            email: 待脱敏的邮箱地址
        返回值：脱敏后的邮箱
        """
        return cls._strategies[MaskType.EMAIL].mask(email)

    @classmethod
    def mask_mobile(cls, mobile: Optional[str]) -> str:
        """
        函数级注释：手机号脱敏
        参数：
            mobile: 待脱敏的手机号
        返回值：脱敏后的手机号
        """
        return cls._strategies[MaskType.MOBILE].mask(mobile)

    @classmethod
    def mask_full(cls, value: Optional[str]) -> str:
        """
        函数级注释：完全脱敏
        参数：
            value: 待脱敏的值
        返回值：完全脱敏的结果
        """
        return cls._strategies[MaskType.FULL].mask(value)

    @classmethod
    def mask_partial(cls, value: Optional[str]) -> str:
        """
        函数级注释：部分脱敏
        参数：
            value: 待脱敏的值
        返回值：部分脱敏的结果
        """
        return cls._strategies[MaskType.PARTIAL].mask(value)
