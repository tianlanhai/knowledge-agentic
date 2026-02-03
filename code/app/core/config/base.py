# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：配置基类模块
内部逻辑：定义应用程序的核心配置基类
设计模式：建造者模式 + 工厂模式
设计原则：单一职责原则
"""

from typing import List
from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.config.api_config import APIConfig
from app.core.config.cors_config import CORSConfig
from app.core.config.llm_config import LLMConfig
from app.core.config.db_config import DatabaseConfig
from app.core.config.storage_config import StorageConfig
from app.core.config.security_config import SecurityConfig


class Settings(BaseSettings):
    """
    类级注释：全局配置类，管理应用程序的所有配置项
    设计模式：建造者模式 - 组合多个配置模块

    配置优先级（从高到低）：
        1. 运行时配置：数据库模型配置（通过 ModelConfigService._reload_config 注入）
           优先级：★★★★★
        2. 环境变量：系统环境变量或 docker run -e 注入
           优先级：★★★★☆
        3. Dockerfile ENV：Dockerfile 中定义的 ENV 指令
           优先级：★★★☆☆
        4. 配置文件：.env.prod（生产）或 .env（开发）
           优先级：★★☆☆☆
        5. 代码默认值：BaseSettings 类属性定义的默认值
           优先级：★☆☆☆☆

    职责：
        1. 提供统一的配置访问接口
        2. 组合各子配置模块
        3. 验证配置有效性
    """

    # 内部逻辑：移除env_file配置，改由main.py动态加载
    model_config = SettingsConfigDict(case_sensitive=True, extra="ignore")

    # API服务配置
    app_config: APIConfig = APIConfig()

    # CORS配置
    cors_config: CORSConfig = CORSConfig()

    # LLM配置
    llm_config: LLMConfig = LLMConfig()

    # 数据库配置
    db_config: DatabaseConfig = DatabaseConfig()

    # 存储配置（向量数据库和文件存储）
    storage_config: StorageConfig = StorageConfig()

    # 安全配置（敏感信息过滤）
    security_config: SecurityConfig = SecurityConfig()

    # 调试与Mock配置
    USE_MOCK: bool = False

    # 日志配置
    LOG_LEVEL: str = "INFO"

    # 时区配置
    TIMEZONE: str = "Asia/Shanghai"

    # ============================================================================
    # 属性访问器 - 提供简化的配置访问（向后兼容）
    # ============================================================================
    @property
    def APP_NAME(self) -> str:
        """获取应用名称"""
        return self.app_config.NAME

    @property
    def APP_VERSION(self) -> str:
        """获取应用版本"""
        return self.app_config.VERSION

    @property
    def APP_ENV(self) -> str:
        """获取运行环境"""
        return self.app_config.ENV

    @property
    def API_V1_STR(self) -> str:
        """获取API版本前缀"""
        return self.app_config.V1_STR

    @property
    def PORT(self) -> int:
        """获取服务端口"""
        return self.app_config.PORT

    @property
    def BACKEND_CORS_ORIGINS(self) -> List[AnyHttpUrl]:
        """获取跨域来源列表"""
        return self.cors_config.origins

    @property
    def LLM_PROVIDER(self) -> str:
        """获取LLM提供商"""
        return self.llm_config.provider

    @property
    def EMBEDDING_PROVIDER(self) -> str:
        """获取Embedding提供商"""
        return self.llm_config.embedding_provider

    @property
    def DATABASE_PROVIDER(self) -> str:
        """获取数据库提供商"""
        return self.db_config.provider

    # 存储配置属性访问器
    @property
    def CHROMA_DB_PATH(self) -> str:
        """获取向量数据库路径"""
        return self.storage_config.CHROMA_DB_PATH

    @property
    def CHROMA_COLLECTION_NAME(self) -> str:
        """获取向量数据库集合名称"""
        return self.storage_config.CHROMA_COLLECTION_NAME

    @property
    def UPLOAD_FILES_PATH(self) -> str:
        """获取文件上传路径"""
        return self.storage_config.UPLOAD_FILES_PATH

    @property
    def LOCAL_MODEL_DIR(self) -> str:
        """获取本地模型目录"""
        return self.storage_config.LOCAL_MODEL_DIR

    # 安全配置属性访问器
    @property
    def ENABLE_SENSITIVE_DATA_FILTER(self) -> bool:
        """获取是否启用敏感信息过滤"""
        return self.security_config.ENABLE_SENSITIVE_DATA_FILTER

    @property
    def SENSITIVE_DATA_MASK_STRATEGY(self) -> str:
        """获取敏感信息脱敏策略"""
        return self.security_config.SENSITIVE_DATA_MASK_STRATEGY

    @property
    def FILTER_MOBILE(self) -> bool:
        """获取是否过滤手机号"""
        return self.security_config.FILTER_MOBILE

    @property
    def FILTER_EMAIL(self) -> bool:
        """获取是否过滤邮箱"""
        return self.security_config.FILTER_EMAIL

    # LLM配置属性访问器（向后兼容）
    @property
    def OLLAMA_BASE_URL(self) -> str:
        """获取Ollama服务地址"""
        return self.llm_config.OLLAMA_BASE_URL

    @property
    def EMBEDDING_MODEL(self) -> str:
        """获取嵌入模型名称"""
        return self.llm_config.EMBEDDING_MODEL

    @property
    def CHAT_MODEL(self) -> str:
        """获取对话模型名称"""
        return self.llm_config.CHAT_MODEL

    @property
    def ZHIPUAI_API_KEY(self) -> str:
        """获取智谱AI API密钥"""
        return self.llm_config.ZHIPUAI_API_KEY

    @property
    def ZHIPUAI_BASE_URL(self) -> str:
        """获取智谱AI API基础地址"""
        return self.llm_config.ZHIPUAI_BASE_URL

    @property
    def ZHIPUAI_MODEL(self) -> str:
        """获取智谱AI模型名称"""
        return self.llm_config.ZHIPUAI_MODEL

    @property
    def ZHIPUAI_LLM_API_KEY(self) -> str:
        """获取智谱AI LLM专用API密钥"""
        return self.llm_config.zhipuai_llm_api_key

    @property
    def ZHIPUAI_LLM_BASE_URL(self) -> str:
        """获取智谱AI LLM专用API基础地址"""
        return self.llm_config.zhipuai_llm_base_url

    @property
    def zhipuai_llm_api_key(self) -> str:
        """获取智谱AI LLM专用API密钥（驼峰命名）"""
        return self.llm_config.zhipuai_llm_api_key

    @property
    def zhipuai_llm_base_url(self) -> str:
        """获取智谱AI LLM专用API基础地址（驼峰命名）"""
        return self.llm_config.zhipuai_llm_base_url

    @property
    def ZHIPUAI_EMBEDDING_MODEL(self) -> str:
        """获取智谱AI嵌入模型名称"""
        return self.llm_config.ZHIPUAI_EMBEDDING_MODEL

    @property
    def ZHIPUAI_EMBEDDING_API_KEY(self) -> str:
        """获取智谱AI Embedding专用API密钥"""
        return self.llm_config.zhipuai_embedding_api_key

    @property
    def ZHIPUAI_EMBEDDING_BASE_URL(self) -> str:
        """获取智谱AI Embedding专用API基础地址"""
        return self.llm_config.zhipuai_embedding_base_url

    @property
    def zhipuai_embedding_api_key(self) -> str:
        """获取智谱AI Embedding专用API密钥（驼峰命名）"""
        return self.llm_config.zhipuai_embedding_api_key

    @property
    def zhipuai_embedding_base_url(self) -> str:
        """获取智谱AI Embedding专用API基础地址（驼峰命名）"""
        return self.llm_config.zhipuai_embedding_base_url

    @property
    def MINIMAX_API_KEY(self) -> str:
        """获取MiniMax API密钥"""
        return self.llm_config.MINIMAX_API_KEY

    @property
    def MINIMAX_GROUP_ID(self) -> str:
        """获取MiniMax Group ID"""
        return self.llm_config.MINIMAX_GROUP_ID

    @property
    def MINIMAX_MODEL(self) -> str:
        """获取MiniMax模型名称"""
        return self.llm_config.MINIMAX_MODEL

    @property
    def MOONSHOT_API_KEY(self) -> str:
        """获取月之暗面API密钥"""
        return self.llm_config.MOONSHOT_API_KEY

    @property
    def MOONSHOT_MODEL(self) -> str:
        """获取月之暗面模型名称"""
        return self.llm_config.MOONSHOT_MODEL

    @property
    def OLLAMA_NUM_GPU(self) -> int:
        """获取Ollama GPU数量"""
        return self.llm_config.OLLAMA_NUM_GPU

    @property
    def OLLAMA_GPU_MEMORY_UTILIZATION(self) -> float:
        """获取Ollama GPU内存利用率"""
        return self.llm_config.OLLAMA_GPU_MEMORY_UTILIZATION

    @property
    def DEVICE(self) -> str:
        """获取设备类型"""
        return self.llm_config.DEVICE

    @property
    def USE_LOCAL_EMBEDDINGS(self) -> bool:
        """获取是否使用本地嵌入"""
        return self.llm_config.USE_LOCAL_EMBEDDINGS

    @property
    def LOCAL_EMBEDDING_MODEL_PATH(self) -> str:
        """获取本地嵌入模型路径"""
        return self.llm_config.LOCAL_EMBEDDING_MODEL_PATH

    @property
    def ENABLE_RERANKING(self) -> bool:
        """获取是否启用重排序"""
        return self.llm_config.ENABLE_RERANKING

    @property
    def RERANKING_MODEL(self) -> str:
        """获取重排序模型"""
        return self.llm_config.RERANKING_MODEL

    # 数据库配置属性访问器（向后兼容）
    @property
    def DB_HOST(self) -> str:
        """获取数据库主机"""
        return self.db_config.DB_HOST

    @property
    def DB_PORT(self) -> int:
        """获取数据库端口"""
        return self.db_config.DB_PORT

    @property
    def DB_NAME(self) -> str:
        """获取数据库名称"""
        return self.db_config.DB_NAME

    @property
    def DB_USER(self) -> str:
        """获取数据库用户"""
        return self.db_config.DB_USER

    @property
    def DB_PASSWORD(self) -> str:
        """获取数据库密码"""
        return self.db_config.DB_PASSWORD

    @property
    def SQLITE_DB_PATH(self) -> str:
        """获取SQLite数据库路径"""
        return self.db_config.SQLITE_DB_PATH


# 变量：实例化全局配置对象（单例模式）
settings = Settings()
