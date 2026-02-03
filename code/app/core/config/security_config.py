# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：安全配置模块
内部逻辑：管理敏感信息过滤相关配置
设计模式：建造者模式
设计原则：单一职责原则
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SecurityConfig(BaseSettings):
    """
    类级注释：安全配置类

    配置优先级（从高到低）：
        1. 环境变量：系统环境变量或 docker run -e 注入
        2. Dockerfile ENV：Dockerfile 中定义的 ENV 指令
        3. 配置文件：.env.prod（生产）或 .env（开发）
        4. 代码默认值：本类属性定义的默认值

    职责：
        1. 管理敏感信息过滤开关
        2. 管理脱敏策略配置
        3. 管理各类敏感信息的过滤规则
    """

    # 内部逻辑：配置Settings，从环境变量读取配置
    model_config = SettingsConfigDict(case_sensitive=True, extra="ignore")

    # 是否启用敏感信息过滤
    ENABLE_SENSITIVE_DATA_FILTER: bool = True

    # 敏感信息脱敏策略（full=完全替换, partial=部分脱敏, hash=哈希替换）
    SENSITIVE_DATA_MASK_STRATEGY: str = "full"

    # 是否过滤手机号
    FILTER_MOBILE: bool = True

    # 是否过滤邮箱
    FILTER_EMAIL: bool = True

    @field_validator("SENSITIVE_DATA_MASK_STRATEGY")
    @classmethod
    def validate_mask_strategy(cls, v: str) -> str:
        """
        函数级注释：验证脱敏策略是否有效
        参数：v - 脱敏策略
        返回值：验证后的策略
        """
        valid_strategies = ["full", "partial", "hash"]
        if v not in valid_strategies:
            raise ValueError(f"无效的脱敏策略: {v}. 支持: {valid_strategies}")
        return v


# 内部变量：导出所有公共接口
__all__ = ['SecurityConfig']
