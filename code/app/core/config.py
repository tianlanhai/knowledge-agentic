# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：核心配置文件（主入口）
内部逻辑：使用 Pydantic BaseSettings 加载环境变量并提供类型安全的配置访问
设计模式：建造者模式 + 工厂模式

注意：此文件保留作为主配置入口，模块化配置已迁移到 config/ 子目录
      - config/base.py - 配置基类
      - config/api_config.py - API服务配置
      - config/cors_config.py - CORS配置
      - config/llm_config.py - LLM相关配置
      - config/db_config.py - 数据库配置
      - config/validators.py - 配置验证器
"""

# ============================================================================
# 新模块化配置（可选使用）
# ============================================================================
# from app.core.config import Settings, settings
# from app.core.config.api_config import APIConfig
# from app.core.config.llm_config import LLMConfig
# ============================================================================

from typing import List, Optional, Union
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    类级注释：全局配置类，管理应用程序的所有配置项

    配置优先级（从高到低）：
        1. 运行时配置：数据库模型配置（通过 ModelConfigService._reload_config 注入）
           优先级：★★★★★
           说明：数据库中存储的配置通过 set_runtime_config 方法注入到工厂类
        2. 环境变量：系统环境变量或 docker run -e 注入
           优先级：★★★★☆
           说明：系统环境变量始终优先于 .env 文件
        3. Dockerfile ENV：Dockerfile 中定义的 ENV 指令
           优先级：★★★☆☆
           说明：容器构建时定义的环境变量
        4. 配置文件：.env.prod（生产）或 .env（开发）
           优先级：★★☆☆☆
           说明：通过 main.py 中的 load_dotenv 加载，使用 override=False
        5. 代码默认值：BaseSettings 类属性定义的默认值
           优先级：★☆☆☆☆
           说明：本类中定义的属性默认值

    属性：
        APP_NAME: 应用程序名称
        APP_VERSION: 应用程序版本
        APP_ENV: 运行环境（空=本地开发、prod=Docker部署）
        API_V1_STR: API 版本前缀
        PORT: 服务运行端口
        LLM_PROVIDER: LLM模型提供商（ollama/zhipuai/minimax/moonshot）
        OLLAMA_BASE_URL: Ollama 服务地址
        EMBEDDING_MODEL: 嵌入模型名称
        CHAT_MODEL: 对话模型名称
        ZHIPUAI_API_KEY: 智谱AI API密钥
        ZHIPUAI_MODEL: 智谱AI模型名称
        MINIMAX_API_KEY: MiniMax API密钥
        MINIMAX_GROUP_ID: MiniMax Group ID
        MINIMAX_MODEL: MiniMax模型名称
        MOONSHOT_API_KEY: 月之暗面API密钥
        MOONSHOT_MODEL: 月之暗面模型名称
        SQLITE_DB_PATH: SQLite 数据库路径
        CHROMA_DB_PATH: ChromaDB 存储路径
        LOG_LEVEL: 日志级别
        BACKEND_CORS_ORIGINS: 允许的跨域来源列表
    """
    # 内部逻辑：移除env_file配置，改由main.py动态加载
    model_config = SettingsConfigDict(case_sensitive=True, extra="ignore")

    # API 服务配置
    APP_NAME: str = "Knowledge-Agentic"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = ""  # 可选值: 空(本地开发)、prod(Docker部署)
    API_V1_STR: str = "/api/v1"
    PORT: int = 8010

    # CORS 配置
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """
        函数级注释：处理跨域来源字符串，将其转换为列表
        参数：v - 原始输入数据
        返回值：处理后的列表或原始值
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @validator("DATABASE_PROVIDER", pre=True)
    def validate_database_provider(cls, v: str) -> str:
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

    @validator("LLM_PROVIDER")
    def validate_llm_provider(cls, v: str) -> str:
        """
        函数级注释：验证LLM提供商是否有效
        参数：v - LLM提供商名称
        返回值：验证后的提供商名称
        """
        valid_providers = ["ollama", "zhipuai", "minimax", "moonshot"]
        if v.lower() not in valid_providers:
            raise ValueError(f"Invalid LLM_PROVIDER: {v}. Must be one of: {valid_providers}")
        return v.lower()

    # LLM 提供商选择
    LLM_PROVIDER: str = "ollama"  # 可选值：ollama、zhipuai、minimax、moonshot

    # Embeddings 提供商选择
    EMBEDDING_PROVIDER: str = "ollama"  # 可选值：ollama、zhipuai、local

    # Ollama 配置
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    EMBEDDING_MODEL: str = "mxbai-embed-large:latest"
    CHAT_MODEL: str = "deepseek-r1:8b"

    # 智谱AI LLM 配置
    ZHIPUAI_LLM_API_KEY: str = ""
    ZHIPUAI_LLM_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"
    ZHIPUAI_MODEL: str = "glm-4.5-air"

    # 智谱AI Embedding 配置
    ZHIPUAI_EMBEDDING_API_KEY: str = ""
    ZHIPUAI_EMBEDDING_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"
    ZHIPUAI_EMBEDDING_MODEL: str = "embedding-3"

    # MiniMax 配置
    MINIMAX_API_KEY: str = ""
    MINIMAX_GROUP_ID: str = ""
    MINIMAX_MODEL: str = "abab5.5-chat"

    # 月之暗面配置
    MOONSHOT_API_KEY: str = ""
    MOONSHOT_MODEL: str = "moonshot-v1-8k"

    # ============================================================================
    # 数据库配置（多供应商支持）
    # ============================================================================
    # 数据库提供商（默认：postgresql）
    # 可选值：postgresql（推荐生产环境）、sqlite（开发环境）
    DATABASE_PROVIDER: str = "postgresql"

    # PostgreSQL 配置
    DB_HOST: str = "localhost"       # 数据库主机地址（Docker部署时使用 host.docker.internal）
    DB_PORT: int = 5432              # 数据库端口
    DB_NAME: str = "knowledge_db"    # 数据库名称
    DB_USER: str = "postgres"        # 数据库用户名
    DB_PASSWORD: str = ""            # 数据库密码

    # SQLite 配置（兼容旧配置）
    SQLITE_DB_PATH: str = "./data/metadata.db"

    # ============================================================================
    # GPU 与本地模型配置
    # ============================================================================
    # Ollama GPU 配置
    OLLAMA_NUM_GPU: int = 1  # 使用的GPU数量，0表示使用CPU
    OLLAMA_GPU_MEMORY_UTILIZATION: float = 0.9  # GPU内存利用率（0-1之间），默认90%

    # GPU 与本地模型配置
    DEVICE: str = "auto"  # 设备类型：cpu、cuda、auto（自动检测）
    USE_LOCAL_EMBEDDINGS: bool = False  # 是否使用 sentence-transformers 本地向量化
    LOCAL_EMBEDDING_MODEL_PATH: str = "BAAI/bge-large-zh-v1.5" # 本地模型路径或 HuggingFace 模型标识
    LOCAL_MODEL_DIR: str = "./models"  # 本地模型存储目录（用于扫描本地模型）

    # ============================================================================
    # OpenAI 配置
    # ============================================================================
    OPENAI_API_KEY: str = ""  # OpenAI API 密钥
    OPENAI_MODEL: str = "gpt-4o"  # OpenAI 模型名称

    # ============================================================================
    # DeepSeek 配置
    # ============================================================================
    DEEPSEEK_API_KEY: str = ""  # DeepSeek API 密钥
    DEEPSEEK_MODEL: str = "deepseek-chat"  # DeepSeek 模型名称
    
    # 重排序配置
    ENABLE_RERANKING: bool = True  # 是否启用重排序功能
    RERANKING_MODEL: str = "BAAI/bge-reranker-large"  # 重排序模型名称

    # ============================================================================
    # 向量数据库与文件存储配置
    # ============================================================================
    CHROMA_DB_PATH: str = "./data/chroma_db"
    CHROMA_COLLECTION_NAME: str = "knowledge_base"
    UPLOAD_FILES_PATH: str = "./data/files"  # 上传文件存储路径

    # 调试与 Mock 配置
    USE_MOCK: bool = False

    # 日志配置
    LOG_LEVEL: str = "INFO"

    # ============================================================================
    # 时区配置
    # ============================================================================
    # 应用时区（默认为北京时间 Asia/Shanghai）
    TIMEZONE: str = "Asia/Shanghai"

    @validator("TIMEZONE", pre=True)
    def validate_timezone(cls, v: str) -> str:
        """
        函数级注释：验证时区配置是否有效
        参数：v - 时区字符串（如 Asia/Shanghai）
        返回值：验证后的时区字符串
        """
        if not v:
            return "Asia/Shanghai"

        # 内部逻辑：验证时区是否有效
        try:
            from zoneinfo import ZoneInfo
            ZoneInfo(v)
        except Exception as e:
            raise ValueError(
                f"无效的时区配置: {v}. "
                f"请使用IANA时区标识符，如: Asia/Shanghai, UTC, America/New_York"
            )
        return v

    # ============================================================================
    # 敏感信息过滤配置
    # ============================================================================
    # 是否启用敏感信息过滤
    ENABLE_SENSITIVE_DATA_FILTER: bool = True

    # 敏感信息过滤策略（full=完全替换, partial=部分脱敏, hash=哈希替换）
    SENSITIVE_DATA_MASK_STRATEGY: str = "full"

    # 是否过滤手机号
    FILTER_MOBILE: bool = True

    # 是否过滤邮箱
    FILTER_EMAIL: bool = True

    # ============================================================================
    # 智谱AI 配置计算属性（向后兼容属性访问）
    # ============================================================================

    @property
    def zhipuai_llm_api_key(self) -> str:
        """
        函数级注释：获取智谱AI LLM专用API密钥
        返回值：str - LLM专用API密钥
        """
        return self.ZHIPUAI_LLM_API_KEY

    @property
    def zhipuai_llm_base_url(self) -> str:
        """
        函数级注释：获取智谱AI LLM专用API基础地址
        返回值：str - LLM专用API基础地址
        """
        return self.ZHIPUAI_LLM_BASE_URL

    @property
    def zhipuai_embedding_api_key(self) -> str:
        """
        函数级注释：获取智谱AI Embedding专用API密钥
        返回值：str - Embedding专用API密钥
        """
        return self.ZHIPUAI_EMBEDDING_API_KEY

    @property
    def zhipuai_embedding_base_url(self) -> str:
        """
        函数级注释：获取智谱AI Embedding专用API基础地址
        返回值：str - Embedding专用API基础地址
        """
        return self.ZHIPUAI_EMBEDDING_BASE_URL


# 变量：实例化全局配置对象
settings = Settings()


# ========================================================================
# 配置构建器模块导入（建造者模式）
# ========================================================================
# 内部逻辑：导入配置构建器，提供更灵活的配置构建方式
# 设计原则：单一职责原则 - 将配置构建逻辑分离到专门的构建器类

from app.core.config_builders import (
    DatabaseConfigBuilder,
    LLMConfigBuilder,
    SensitiveDataConfigBuilder,
    build_database_config,
    build_llm_config,
    build_sensitive_data_config,
    DatabaseProviderValidator,
    LLMProviderValidator,
    TimezoneValidator,
)


# 便捷工厂函数
def create_settings_with_validators() -> Settings:
    """
    函数级注释：使用验证链创建配置实例
    内部逻辑：创建配置 -> 通过责任链验证 -> 返回验证后的配置
    返回值：Settings实例
    """
    # 内部逻辑：创建验证链
    validator_chain = DatabaseProviderValidator(
        next_validator=LLMProviderValidator(
            next_validator=TimezoneValidator()
        )
    )

    # 内部逻辑：创建配置实例
    # 注意：Settings 的验证器已经通过 @validator 装饰器处理
    # 这里提供额外的验证链作为扩展点
    settings_instance = Settings()

    return settings_instance

