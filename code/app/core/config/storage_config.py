# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：存储配置模块
内部逻辑：管理向量数据库和文件存储相关配置
设计模式：建造者模式
设计原则：单一职责原则
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class StorageConfig(BaseSettings):
    """
    类级注释：存储配置类

    配置优先级（从高到低）：
        1. 环境变量：系统环境变量或 docker run -e 注入
        2. Dockerfile ENV：Dockerfile 中定义的 ENV 指令
        3. 配置文件：.env.prod（生产）或 .env（开发）
        4. 代码默认值：本类属性定义的默认值

    职责：
        1. 管理向量数据库配置
        2. 管理文件存储路径配置
    """

    # 内部逻辑：配置Settings，从环境变量读取配置
    model_config = SettingsConfigDict(case_sensitive=True, extra="ignore")

    # 向量数据库配置
    CHROMA_DB_PATH: str = "./data/chroma_db"
    CHROMA_COLLECTION_NAME: str = "knowledge_base"

    # 文件上传存储配置
    UPLOAD_FILES_PATH: str = "./data/files"

    # 本地模型存储目录
    LOCAL_MODEL_DIR: str = "./models"


# 内部变量：导出所有公共接口
__all__ = ['StorageConfig']
