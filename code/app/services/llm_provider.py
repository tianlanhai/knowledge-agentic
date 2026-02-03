# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：LLM提供者服务
内部逻辑：统一管理LLM实例的创建和获取，消除各服务中的重复初始化代码
设计模式：服务定位器模式、单例模式
设计原则：单一职责原则、DRY（不重复）
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.language_models import BaseChatModel
from loguru import logger

from app.utils.llm_factory import LLMFactory
from app.services.model_config_service import ModelConfigService


class LLMProvider:
    """
    类级注释：LLM提供者类，统一管理LLM实例的获取
    设计模式：服务定位器模式、单例模式
    职责：
        1. 统一管理LLM实例的获取逻辑
        2. 处理默认配置回退
        3. 提供流式和非流式LLM实例
        4. 支持配置刷新

    单例模式：整个应用共享一个实例
    """

    # 内部类变量：单例实例
    _instance: Optional['LLMProvider'] = None

    def __new__(cls):
        """
        函数级注释：实现单例模式
        内部逻辑：检查是否已存在实例，不存在则创建
        返回值：LLMProvider实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # 内部变量：初始化实例状态
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """
        函数级注释：初始化实例（只执行一次）
        """
        if self._initialized:
            return
        self._initialized = True
        logger.debug("LLMProvider单例已初始化")

    async def get_llm(
        self,
        db: AsyncSession,
        streaming: bool = False
    ) -> BaseChatModel:
        """
        函数级注释：获取LLM实例
        内部逻辑：从数据库获取默认配置 -> 使用配置创建LLM -> 无配置则使用默认
        参数：
            db: 数据库会话
            streaming: 是否启用流式输出
        返回值：LLM实例
        """
        # 内部逻辑：从数据库获取启用的配置
        default_config = await ModelConfigService.get_default_config(db)

        if default_config:
            logger.debug(f"使用数据库配置创建LLM: {default_config.provider_name}")
            return LLMFactory.create_from_model_config(default_config, streaming=streaming)
        else:
            logger.debug("使用默认配置创建LLM")
            return LLMFactory.create_llm(streaming=streaming)

    async def refresh_config(self, db: AsyncSession) -> None:
        """
        函数级注释：刷新LLM配置
        内部逻辑：重新加载默认配置并触发热重载
        参数：
            db: 数据库会话
        """
        default_config = await ModelConfigService.get_default_config(db)
        if default_config:
            # 内部逻辑：设置运行时配置会自动清除缓存
            LLMFactory.create_from_model_config(default_config, streaming=False)
            logger.info("LLM配置已刷新")

    def get_llm_with_config(
        self,
        provider: str,
        model: str,
        api_key: str = "",
        endpoint: str = "",
        temperature: float = 0,
        streaming: bool = False
    ) -> BaseChatModel:
        """
        函数级注释：使用指定配置获取LLM实例
        内部逻辑：构造配置字典 -> 设置运行时配置 -> 创建LLM实例
        参数：
            provider: 提供商ID
            model: 模型名称
            api_key: API密钥
            endpoint: 端点地址
            temperature: 温度参数
            streaming: 是否启用流式输出
        返回值：LLM实例
        """
        config_dict = {
            "provider": provider,
            "model": model,
            "api_key": api_key,
            "endpoint": endpoint,
            "temperature": temperature
        }
        LLMFactory.set_runtime_config(config_dict)
        return LLMFactory.create_llm(streaming=streaming)


# 内部变量：导出全局LLM提供者实例（单例）
llm_provider = LLMProvider()
