# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：配置模块
内部逻辑：应用程序配置的模块化管理
设计模式：建造者模式 + 工厂模式
设计原则：单一职责原则、开闭原则
"""

# 内部逻辑：从各子模块导入配置
from app.core.config.base import Settings, settings
from app.core.config.api_config import APIConfig
from app.core.config.cors_config import CORSConfig
from app.core.config.llm_config import LLMConfig
from app.core.config.db_config import DatabaseConfig
from app.core.config.storage_config import StorageConfig
from app.core.config.security_config import SecurityConfig
from app.core.config.validators import (
    DatabaseProviderValidator,
    LLMProviderValidator,
    TimezoneValidator,
    assemble_cors_origins,
    validate_timezone,
)

# 内部变量：导出所有公共接口
__all__ = [
    # 主配置
    'Settings',
    'settings',
    # 子配置
    'APIConfig',
    'CORSConfig',
    'LLMConfig',
    'DatabaseConfig',
    'StorageConfig',
    'SecurityConfig',
    # 验证器
    'DatabaseProviderValidator',
    'LLMProviderValidator',
    'TimezoneValidator',
    'assemble_cors_origins',
    'validate_timezone',
]
