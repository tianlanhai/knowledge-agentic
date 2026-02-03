# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：配置优先级常量模块
内部逻辑：定义系统配置的优先级顺序，确保所有模块使用一致的优先级逻辑
设计原则：SOLID - 单一职责原则
用途：提供统一的配置优先级定义和说明
"""

from enum import IntEnum
from typing import Dict, Any


class ConfigPriority(IntEnum):
    """
    类级注释：配置优先级枚举

    数值越小，优先级越高（1 = 最高优先级）

    配置优先级（从高到低）：
        1. RUNTIME - 数据库模型配置（运行时注入）
           优先级：★★★★★
           说明：通过 ModelConfigService._reload_config 注入
           来源：数据库表（model_config、embedding_config）

        2. ENV_VAR - 环境变量（docker run -e）
           优先级：★★★★☆
           说明：系统环境变量或容器启动时注入
           来源：os.environ、docker run -e

        3. DOCKER_ENV - Dockerfile ENV
           优先级：★★★☆☆
           说明：Dockerfile 中定义的 ENV 指令
           来源：Dockerfile ENV 指令

        4. ENV_FILE - 配置文件
           优先级：★★☆☆☆
           说明：.env.prod（生产）或 .env（开发）
           来源：main.py 中的 load_dotenv 加载

        5. CODE_DEFAULT - 代码默认值
           优先级：★☆☆☆☆
           说明：BaseSettings 类属性定义的默认值
           来源：配置类（LLMConfig、DatabaseConfig 等）
    """

    # 数据库模型配置（运行时注入）- 最高优先级
    RUNTIME = 1

    # 环境变量（系统环境或 docker run -e）
    ENV_VAR = 2

    # Dockerfile ENV
    DOCKER_ENV = 3

    # 配置文件（.env.prod 或 .env）
    ENV_FILE = 4

    # 代码默认值（最低优先级）
    CODE_DEFAULT = 5


class ConfigPriorityInfo:
    """
    类级注释：配置优先级信息类
    职责：提供配置优先级的详细说明和文档
    """

    # 内部变量：优先级描述映射表
    _PRIORITY_DESCRIPTIONS: Dict[ConfigPriority, str] = {
        ConfigPriority.RUNTIME: "数据库模型配置（运行时注入）",
        ConfigPriority.ENV_VAR: "环境变量（docker run -e）",
        ConfigPriority.DOCKER_ENV: "Dockerfile ENV",
        ConfigPriority.ENV_FILE: "配置文件（.env.prod 或 .env）",
        ConfigPriority.CODE_DEFAULT: "代码默认值",
    }

    # 内部变量：优先级星级映射表
    _PRIORITY_STARS: Dict[ConfigPriority, str] = {
        ConfigPriority.RUNTIME: "★★★★★",
        ConfigPriority.ENV_VAR: "★★★★☆",
        ConfigPriority.DOCKER_ENV: "★★★☆☆",
        ConfigPriority.ENV_FILE: "★★☆☆☆",
        ConfigPriority.CODE_DEFAULT: "★☆☆☆☆",
    }

    # 内部变量：优先级来源映射表
    _PRIORITY_SOURCES: Dict[ConfigPriority, str] = {
        ConfigPriority.RUNTIME: "数据库表（model_config、embedding_config）",
        ConfigPriority.ENV_VAR: "os.environ、docker run -e",
        ConfigPriority.DOCKER_ENV: "Dockerfile ENV 指令",
        ConfigPriority.ENV_FILE: "main.py 中的 load_dotenv 加载",
        ConfigPriority.CODE_DEFAULT: "配置类（LLMConfig、DatabaseConfig 等）",
    }

    @classmethod
    def get_description(cls, priority: ConfigPriority) -> str:
        """
        函数级注释：获取优先级描述
        参数：
            priority: 配置优先级枚举
        返回值：优先级描述字符串
        """
        return cls._PRIORITY_DESCRIPTIONS.get(priority, "")

    @classmethod
    def get_stars(cls, priority: ConfigPriority) -> str:
        """
        函数级注释：获取优先级星级表示
        参数：
            priority: 配置优先级枚举
        返回值：星级字符串
        """
        return cls._PRIORITY_STARS.get(priority, "")

    @classmethod
    def get_source(cls, priority: ConfigPriority) -> str:
        """
        函数级注释：获取优先级来源说明
        参数：
            priority: 配置优先级枚举
        返回值：来源说明字符串
        """
        return cls._PRIORITY_SOURCES.get(priority, "")

    @classmethod
    def get_full_info(cls, priority: ConfigPriority) -> str:
        """
        函数级注释：获取优先级完整信息
        参数：
            priority: 配置优先级枚举
        返回值：包含描述、星级和来源的完整信息
        """
        return (
            f"{cls.get_stars(priority)} "
            f"{cls.get_description(priority)}\n"
            f"    来源: {cls.get_source(priority)}"
        )

    @classmethod
    def get_priority_chain(cls) -> str:
        """
        函数级注释：获取完整的配置优先级链说明
        返回值：多行字符串，包含所有优先级的完整说明
        """
        lines = ["配置优先级链（从高到低）：", ""]
        for priority in sorted(ConfigPriority, key=lambda x: x.value):
            lines.append(f"  {priority.value}. {cls.get_full_info(priority)}")
        return "\n".join(lines)


# 内部变量：导出所有公共接口
__all__ = [
    'ConfigPriority',
    'ConfigPriorityInfo',
]
