# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：API服务配置模块
内部逻辑：管理API服务相关配置
设计模式：建造者模式 - 配置构建
设计原则：单一职责原则
"""

from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class APIConfig(BaseSettings):
    """
    类级注释：API服务配置类

    配置优先级（从高到低）：
        1. 环境变量：系统环境变量或 docker run -e 注入
        2. Dockerfile ENV：Dockerfile 中定义的 ENV 指令
        3. 配置文件：.env.prod（生产）或 .env（开发）
        4. 代码默认值：本类属性定义的默认值

    职责：
        1. 管理应用名称和版本
        2. 管理API路由配置
        3. 管理服务端口配置
    """

    # 内部逻辑：配置Settings，从环境变量读取配置
    model_config = SettingsConfigDict(case_sensitive=True, extra="ignore")

    # 应用名称
    NAME: str = "Knowledge-Agentic"
    # 应用版本
    VERSION: str = "0.1.0"
    # 运行环境（空=本地开发、prod=Docker部署）
    ENV: str = ""
    # API版本前缀
    V1_STR: str = "/api/v1"
    # 服务运行端口
    PORT: int = 8010

    @field_validator("ENV")
    @classmethod
    def validate_env(cls, v: str) -> str:
        """
        函数级注释：验证运行环境配置
        参数：v - 环境标识
        返回值：验证后的环境标识
        """
        valid_envs = ["", "dev", "prod", "test"]
        if v not in valid_envs:
            raise ValueError(f"无效的运行环境: {v}. 支持: {valid_envs}")
        return v


# 内部变量：导出所有公共接口
__all__ = ['APIConfig']
