# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：LLM配置模块
内部逻辑：管理大语言模型相关配置
设计模式：建造者模式
设计原则：单一职责原则
"""

from typing import Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMConfig(BaseSettings):
    """
    类级注释：LLM配置类

    配置优先级（从高到低）：
        1. 运行时配置：数据库模型配置（通过 set_runtime_config 注入）
        2. 环境变量：系统环境变量或 docker run -e 注入
        3. Dockerfile ENV：Dockerfile 中定义的 ENV 指令
        4. 配置文件：.env.prod（生产）或 .env（开发）
        5. 代码默认值：本类属性定义的默认值

    职责：
        1. 管理LLM提供商选择
        2. 管理各提供商的配置
        3. 提供配置验证逻辑
    """

    # 内部逻辑：配置Settings，从环境变量读取配置
    model_config = SettingsConfigDict(case_sensitive=True, extra="ignore")

    # LLM提供商选择
    provider: str = "ollama"

    # Embeddings提供商选择
    embedding_provider: str = "ollama"

    # Ollama配置
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    EMBEDDING_MODEL: str = "mxbai-embed-large:latest"
    CHAT_MODEL: str = "deepseek-r1:8b"

    # 智谱AI通用配置
    ZHIPUAI_API_KEY: str = ""
    ZHIPUAI_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"
    ZHIPUAI_MODEL: str = "glm-4.5-air"
    ZHIPUAI_EMBEDDING_MODEL: str = "embedding-3"

    # 智谱AI LLM独立配置
    ZHIPUAI_LLM_API_KEY: str = ""
    ZHIPUAI_LLM_BASE_URL: str = ""

    # 智谱AI Embedding独立配置
    ZHIPUAI_EMBEDDING_API_KEY: str = ""
    ZHIPUAI_EMBEDDING_BASE_URL: str = ""

    # MiniMax配置
    MINIMAX_API_KEY: str = ""
    MINIMAX_GROUP_ID: str = ""
    MINIMAX_MODEL: str = "abab5.5-chat"

    # 月之暗面配置
    MOONSHOT_API_KEY: str = ""
    MOONSHOT_MODEL: str = "moonshot-v1-8k"

    # GPU配置
    OLLAMA_NUM_GPU: int = 1
    OLLAMA_GPU_MEMORY_UTILIZATION: float = 0.9

    # 本地模型配置
    DEVICE: str = "auto"
    USE_LOCAL_EMBEDDINGS: bool = False
    LOCAL_EMBEDDING_MODEL_PATH: str = "BAAI/bge-large-zh-v1.5"
    LOCAL_MODEL_DIR: str = "./models"

    # 重排序配置
    ENABLE_RERANKING: bool = True
    RERANKING_MODEL: str = "BAAI/bge-reranker-large"

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """
        函数级注释：验证LLM提供商是否有效
        参数：v - LLM提供商名称
        返回值：验证后的提供商名称
        """
        valid_providers = ["ollama", "zhipuai", "minimax", "moonshot", "openai", "deepseek"]
        if v.lower() not in valid_providers:
            raise ValueError(f"无效的LLM提供商: {v}. 支持: {valid_providers}")
        return v.lower()

    @field_validator("OLLAMA_GPU_MEMORY_UTILIZATION")
    @classmethod
    def validate_gpu_memory(cls, v: float) -> float:
        """
        函数级注释：验证GPU内存利用率
        参数：v - 利用率值（0-1之间）
        返回值：验证后的值
        """
        if not 0 <= v <= 1:
            raise ValueError(f"GPU内存利用率必须在0-1之间: {v}")
        return v

    # ========================================================================
    # 智谱AI配置计算属性（实现配置分离与回退逻辑）
    # ========================================================================

    @property
    def zhipuai_llm_api_key(self) -> str:
        """
        属性级注释：获取智谱AI LLM专用API密钥
        内部逻辑：优先返回独立配置，为空时回退到通用配置
        返回值：LLM专用API密钥
        """
        return self.ZHIPUAI_LLM_API_KEY or self.ZHIPUAI_API_KEY

    @property
    def zhipuai_llm_base_url(self) -> str:
        """
        属性级注释：获取智谱AI LLM专用API基础地址
        内部逻辑：优先返回独立配置，为空时回退到通用配置
        返回值：LLM专用API基础地址
        """
        return self.ZHIPUAI_LLM_BASE_URL or self.ZHIPUAI_BASE_URL

    @property
    def zhipuai_embedding_api_key(self) -> str:
        """
        属性级注释：获取智谱AI Embedding专用API密钥
        内部逻辑：优先返回独立配置，为空时回退到通用配置
        返回值：Embedding专用API密钥
        """
        return self.ZHIPUAI_EMBEDDING_API_KEY or self.ZHIPUAI_API_KEY

    @property
    def zhipuai_embedding_base_url(self) -> str:
        """
        属性级注释：获取智谱AI Embedding专用API基础地址
        内部逻辑：优先返回独立配置，为空时回退到通用配置
        返回值：Embedding专用API基础地址
        """
        return self.ZHIPUAI_EMBEDDING_BASE_URL or self.ZHIPUAI_BASE_URL


# 内部变量：导出所有公共接口
__all__ = ['LLMConfig']
