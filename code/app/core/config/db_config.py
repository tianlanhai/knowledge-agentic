# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：数据库配置模块
内部逻辑：管理数据库相关配置
设计模式：建造者模式
设计原则：单一职责原则
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    """
    类级注释：数据库配置类

    配置优先级（从高到低）：
        1. 运行时配置：数据库模型配置（通过 set_runtime_config 注入）
        2. 环境变量：系统环境变量或 docker run -e 注入
        3. Dockerfile ENV：Dockerfile 中定义的 ENV 指令
        4. 配置文件：.env.prod（生产）或 .env（开发）
        5. 代码默认值：本类属性定义的默认值

    职责：
        1. 管理数据库提供商选择
        2. 管理PostgreSQL配置
        3. 管理SQLite配置
        4. 提供配置验证逻辑
    """

    # 内部逻辑：配置Settings，从环境变量读取配置
    model_config = SettingsConfigDict(case_sensitive=True, extra="ignore")

    # 数据库提供商（默认：postgresql）
    provider: str = "postgresql"

    # PostgreSQL配置
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "knowledge_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""

    # SQLite配置
    SQLITE_DB_PATH: str = "./data/metadata.db"

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """
        函数级注释：验证数据库提供商是否有效
        参数：v - 数据库提供商名称
        返回值：验证后的提供商名称
        """
        if not v:
            return "postgresql"  # 默认使用 PostgreSQL
        valid_providers = ["postgresql", "sqlite"]
        if v.lower() not in valid_providers:
            raise ValueError(
                f"不支持的数据库提供商: {v}. "
                f"支持的提供商: {valid_providers}"
            )
        return v.lower()

    @property
    def DATABASE_PROVIDER(self) -> str:
        """
        属性级注释：获取数据库提供商（向后兼容）
        返回值：数据库提供商名称
        """
        return self.provider


# 内部变量：导出所有公共接口
__all__ = ['DatabaseConfig']
