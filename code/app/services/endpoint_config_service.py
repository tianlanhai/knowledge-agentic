# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：Endpoint配置服务
内部逻辑：统一管理提供商endpoint配置的查询，消除重复代码
设计模式：服务层模式、模板方法模式
设计原则：DRY（不重复）、单一职责原则
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.model_config import ModelConfig, EmbeddingConfig
from loguru import logger


class EndpointConfigService:
    """
    类级注释：Endpoint配置服务类
    设计模式：服务层模式
    职责：
        1. 统一查询用户配置的provider endpoint
        2. 消除在API端点中重复的查询逻辑
        3. 提供默认值回退机制
    """

    @staticmethod
    async def get_llm_provider_endpoint(
        db: AsyncSession,
        provider_id: str,
        default_endpoint: str
    ) -> str:
        """
        函数级注释：获取LLM提供商的endpoint配置
        内部逻辑：查询用户配置的endpoint -> 如果为空则使用默认值 -> 记录日志 -> 返回endpoint
        参数：
            db: 数据库异步会话
            provider_id: 提供商ID（如 ollama）
            default_endpoint: 默认的endpoint地址
        返回值：用户配置的endpoint或默认endpoint
        """
        try:
            result = await db.execute(
                select(ModelConfig).where(
                    (ModelConfig.provider_id == provider_id) &
                    (ModelConfig.endpoint.isnot(None)) &
                    (ModelConfig.endpoint != "")
                ).order_by(ModelConfig.status.desc()).limit(1)
            )
            config = result.scalar_one_or_none()
            if config and config.endpoint:
                logger.info(f"使用用户配置的 {provider_id} endpoint: {config.endpoint}")
                return config.endpoint
        except Exception as e:
            logger.warning(f"查询 {provider_id} 配置失败，使用默认值: {str(e)}")

        return default_endpoint

    @staticmethod
    async def get_embedding_provider_endpoint(
        db: AsyncSession,
        provider_id: str,
        default_endpoint: str
    ) -> str:
        """
        函数级注释：获取Embedding提供商的endpoint配置
        内部逻辑：查询用户配置的endpoint -> 如果为空则使用默认值 -> 记录日志 -> 返回endpoint
        参数：
            db: 数据库异步会话
            provider_id: 提供商ID（如 ollama）
            default_endpoint: 默认的endpoint地址
        返回值：用户配置的endpoint或默认endpoint
        """
        try:
            result = await db.execute(
                select(EmbeddingConfig).where(
                    (EmbeddingConfig.provider_id == provider_id) &
                    (EmbeddingConfig.endpoint.isnot(None)) &
                    (EmbeddingConfig.endpoint != "")
                ).order_by(EmbeddingConfig.status.desc()).limit(1)
            )
            config = result.scalar_one_or_none()
            if config and config.endpoint:
                logger.info(f"使用用户配置的 {provider_id} endpoint: {config.endpoint}")
                return config.endpoint
        except Exception as e:
            logger.warning(f"查询 {provider_id} 配置失败，使用默认值: {str(e)}")

        return default_endpoint

    @staticmethod
    async def get_provider_endpoint(
        db: AsyncSession,
        provider_id: str,
        default_endpoint: str,
        config_type: str = "llm"
    ) -> str:
        """
        函数级注释：通用的获取提供商endpoint配置方法（模板方法）
        内部逻辑：根据配置类型分发到具体的查询方法
        参数：
            db: 数据库异步会话
            provider_id: 提供商ID
            default_endpoint: 默认的endpoint地址
            config_type: 配置类型（llm 或 embedding）
        返回值：用户配置的endpoint或默认endpoint
        """
        if config_type == "embedding":
            return await EndpointConfigService.get_embedding_provider_endpoint(
                db, provider_id, default_endpoint
            )
        return await EndpointConfigService.get_llm_provider_endpoint(
            db, provider_id, default_endpoint
        )

    @staticmethod
    async def get_ollama_endpoint(
        db: AsyncSession,
        default_endpoint: str,
        config_type: str = "llm"
    ) -> str:
        """
        函数级注释：便捷方法：获取Ollama endpoint
        内部逻辑：调用通用方法查询ollama提供商的endpoint
        参数：
            db: 数据库异步会话
            default_endpoint: 默认的endpoint地址
            config_type: 配置类型（llm 或 embedding）
        返回值：用户配置的Ollama endpoint或默认endpoint
        """
        return await EndpointConfigService.get_provider_endpoint(
            db, "ollama", default_endpoint, config_type
        )
