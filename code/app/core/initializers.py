# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：应用启动初始化模块
内部逻辑：集中管理应用启动时需要预加载的配置和数据
设计原则：SOLID - 单一职责原则
设计模式：工厂模式 - 统一管理各类初始化操作
"""

from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from app.services.model_config_service import ModelConfigService
from app.services.embedding_config_service import EmbeddingConfigService


async def init_default_configs(db: AsyncSession) -> None:
    """
    函数级注释：初始化默认模型配置并加载到运行时

    配置优先级说明：
        本方法将数据库中标记为 status=1 的配置加载到运行时，
        确保数据库配置拥有最高优先级。

        配置优先级（从高到低）：
            1. 数据库模型配置（运行时注入）- 通过本方法加载
            2. 环境变量（docker run -e）
            3. .env.prod（生产）或 .env（开发）
            4. 代码默认值

    内部逻辑：预加载LLM配置和Embedding配置 -> 加载启用的配置到运行时 -> 确保应用启动时配置就绪
    参数：
        db: 数据库会话
    返回值：无
    异常：
        Exception: 配置初始化失败时抛出异常
    """
    try:
        # 内部逻辑：预加载LLM模型配置
        llm_configs = await ModelConfigService.get_model_configs(db)
        logger.info(f"LLM模型配置已加载: {len(llm_configs)} 个提供商")

        # 内部逻辑：加载当前启用的LLM配置到运行时
        # 这样可以确保应用重启后，LLM工厂使用正确的配置
        default_llm_config = await ModelConfigService.get_default_config(db)
        if default_llm_config:
            await ModelConfigService._reload_config(default_llm_config)
            logger.info(f"已加载启用的LLM配置到运行时: {default_llm_config.provider_name}")
        else:
            logger.warning("未找到启用的LLM配置，将使用环境变量默认配置")

        # 内部逻辑：预加载Embedding配置
        embedding_configs = await EmbeddingConfigService.get_embedding_configs(db)
        logger.info(f"Embedding配置已加载: {len(embedding_configs)} 个提供商")

        # 内部逻辑：加载当前启用的Embedding配置到运行时
        # 这样可以确保应用重启后，Embedding工厂使用正确的配置
        default_embedding_config = await EmbeddingConfigService.get_default_config(db)
        if default_embedding_config:
            await EmbeddingConfigService._reload_config(default_embedding_config)
            logger.info(f"已加载启用的Embedding配置到运行时: {default_embedding_config.provider_name} - {default_embedding_config.model_name}")
        else:
            logger.warning("未找到启用的Embedding配置，将使用环境变量默认配置")

    except Exception as e:
        # 内部逻辑：异常处理 - 记录错误并重新抛出
        logger.error(f"配置初始化失败: {str(e)}")
        raise
