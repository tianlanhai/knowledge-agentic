# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：模型配置服务
内部逻辑：提供LLM模型配置的CRUD操作、自动初始化和热切换支持
设计模式：模板方法模式 - 继承 BaseConfigService
参考项目：easy-dataset-file
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update
from sqlalchemy.exc import IntegrityError
from app.models.model_config import ModelConfig
from app.core.llm_constants import LLM_PROVIDERS, DEFAULT_MODEL_SETTINGS
from app.core.version_config import VersionConfig
from app.services.base_config_service import BaseConfigService
from loguru import logger
import uuid


class ModelConfigService(BaseConfigService[ModelConfig]):
    """
    类级注释：模型配置服务类
    设计模式：模板方法模式 - 继承 BaseConfigService
    职责：
        1. 继承配置服务的通用CRUD操作
        2. 实现模型特定的抽象方法
        3. 提供 ModelConfig 特有的方法（如版本验证的保存方法）
    内部变量：
        继承自 BaseConfigService 的所有功能
    """

    # ==================== 实现抽象方法 ====================

    @classmethod
    def _get_config_model(cls) -> type:
        """
        函数级注释：获取配置模型类
        返回值：ModelConfig 模型类
        """
        return ModelConfig

    @classmethod
    def _get_config_type(cls) -> str:
        """
        函数级注释：获取配置类型名称
        返回值："模型"
        """
        return "模型"

    @classmethod
    async def _init_default_configs(cls, db: AsyncSession) -> List[ModelConfig]:
        """
        函数级注释：初始化默认模型配置
        内部逻辑：先检查是否存在配置，为空则批量插入，利用唯一约束防止重复
        参数：
            db: 数据库会话
        返回值：初始化的配置列表
        """
        # 内部逻辑：先检查是否已有配置
        existing_result = await db.execute(select(ModelConfig))
        existing_configs = existing_result.scalars().all()
        if existing_configs:
            logger.info(f"模型配置已存在 ({len(existing_configs)} 个)，跳过初始化")
            return existing_configs

        # 内部变量：默认提供商（只有这个会被设为status=1）
        default_provider_id = "ollama"

        # 内部逻辑：批量插入所有配置
        configs_to_insert = []
        for provider in LLM_PROVIDERS:
            config_data = {
                "id": str(uuid.uuid4()),
                "provider_id": provider["id"],
                "provider_name": provider["name"],
                "endpoint": provider["default_endpoint"],
                "api_key": "",
                "model_id": provider["default_models"][0] if provider["default_models"] else "",
                "model_name": provider["default_models"][0] if provider["default_models"] else "",
                "type": provider["type"],
                "temperature": DEFAULT_MODEL_SETTINGS["temperature"],
                "max_tokens": DEFAULT_MODEL_SETTINGS["max_tokens"],
                "top_p": DEFAULT_MODEL_SETTINGS["top_p"],
                "top_k": DEFAULT_MODEL_SETTINGS["top_k"],
                "device": "auto",
                "status": 1 if (provider["id"] == default_provider_id) else 0
            }
            configs_to_insert.append(ModelConfig(**config_data))

        db.add_all(configs_to_insert)
        await db.commit()

        logger.info(f"初始化默认模型配置完成，共 {len(configs_to_insert)} 个提供商")
        return configs_to_insert

    @classmethod
    async def _reload_config(cls, config: ModelConfig) -> None:
        """
        函数级注释：触发热重载

        配置优先级说明：
            本方法将数据库中的配置注入到 LLMFactory 运行时，
            使数据库配置拥有最高优先级（高于环境变量、.env 文件和代码默认值）。

        内部逻辑：更新LLMFactory的运行时配置 -> 清除实例缓存
        参数：
            config: 配置对象（来自数据库 ModelConfig 表）
        """
        try:
            from app.utils.llm_factory import LLMFactory

            # 内部逻辑：构造配置字典，优先使用 model_name，回退到 model_id
            # 这样可以兼容某些情况下 model_name 为空的场景
            config_dict = {
                "provider": config.provider_id,
                "model": config.model_name or config.model_id or "",
                "endpoint": config.endpoint or "",
                "api_key": config.api_key or "",
                "device": getattr(config, "device", "auto"),
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
                "top_p": config.top_p
            }

            # 内部逻辑：添加详细日志，便于诊断配置更新问题
            logger.info(f"[热重载] 准备更新LLM运行时配置: provider={config.provider_id}, endpoint={config.endpoint}")

            LLMFactory.set_runtime_config(config_dict)
            logger.info(f"LLM运行时配置已热重载: {config.provider_name} - {config.model_name}, endpoint={config.endpoint}")
        except ImportError:
            logger.warning("LLMFactory未找到，跳过热重载")
        except Exception as e:
            logger.error(f"热重载失败: {str(e)}")

    # ==================== ModelConfig 特有方法 ====================

    @classmethod
    async def get_model_configs(cls, db: AsyncSession) -> List[ModelConfig]:
        """
        函数级注释：获取所有模型配置（向后兼容的别名方法）
        内部逻辑：委托给基类的 get_configs 方法
        参数：
            db: 数据库会话
        返回值：模型配置列表
        """
        return await cls.get_configs(db)

    @classmethod
    async def save_model_config(
        cls,
        db: AsyncSession,
        config_data: Dict[str, Any]
    ) -> ModelConfig:
        """
        函数级注释：保存或更新模型配置（ModelConfig 特有方法）
        内部逻辑：补充缺失字段 -> 验证版本兼容性 -> 有ID则更新，无ID则创建 -> 提交事务 -> 返回配置对象
        参数：
            db: 数据库会话
            config_data: 配置数据字典
        返回值：保存后的配置对象
        异常：
            ValueError: LLM提供商不被当前镜像版本支持
        """
        # 内部变量：获取提供商ID
        provider_id = config_data.get("provider_id", "")

        # 内部逻辑：补充缺失的字段（从 LLM_PROVIDERS 常量中获取）
        # 解决前端提交数据时 provider_name 和 model_id 可能为空的问题
        if provider_id and not config_data.get("provider_name"):
            for provider in LLM_PROVIDERS:
                if provider["id"] == provider_id:
                    config_data["provider_name"] = provider["name"]
                    # 如果 model_id 也为空，从默认模型中获取
                    if not config_data.get("model_id") and provider.get("default_models"):
                        config_data["model_id"] = provider["default_models"][0]
                    break

        # 内部逻辑：版本验证 - 检查LLM提供商是否与镜像版本兼容
        if provider_id:
            is_valid = VersionConfig.is_llm_provider_supported(provider_id)
            if not is_valid:
                supported = ", ".join(VersionConfig.get_supported_llm_providers())
                raise ValueError(
                    f"当前镜像版本不支持 {provider_id}。"
                    f"支持的LLM提供商: {supported}"
                )
            logger.info(f"LLM提供商 {provider_id} 通过版本验证")

        config_id = config_data.get("id")

        # 内部逻辑：根据是否有ID决定更新或创建
        if config_id:
            # 更新现有配置
            result = await db.execute(
                select(ModelConfig).where(ModelConfig.id == config_id)
            )
            config = result.scalar_one_or_none()

            # 内部逻辑：Guard Clauses - 配置不存在则创建
            if config:
                for key, value in config_data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
            else:
                config = ModelConfig(**config_data)
                db.add(config)
        else:
            # 内部逻辑：没有id时，先检查是否存在相同 (provider_id, model_id, type) 的配置
            provider_id = config_data.get("provider_id", "")
            model_id = config_data.get("model_id", "")
            config_type = config_data.get("type", "text")

            if provider_id and model_id:
                # 查询是否存在相同组合的配置
                result = await db.execute(
                    select(ModelConfig).where(
                        (ModelConfig.provider_id == provider_id) &
                        (ModelConfig.model_id == model_id) &
                        (ModelConfig.type == config_type)
                    )
                )
                config = result.scalar_one_or_none()

                if config:
                    # 内部逻辑：配置已存在，执行更新
                    logger.info(f"配置已存在，执行更新: {provider_id}/{model_id}")
                    for key, value in config_data.items():
                        if hasattr(config, key) and key != "id":
                            setattr(config, key, value)
                else:
                    # 内部逻辑：配置不存在，创建新配置
                    if not config_data.get("id"):
                        config_data["id"] = str(uuid.uuid4())
                    config = ModelConfig(**config_data)
                    db.add(config)
            else:
                # 内部逻辑：缺少必要字段，直接创建新配置
                if not config_data.get("id"):
                    config_data["id"] = str(uuid.uuid4())
                config = ModelConfig(**config_data)
                db.add(config)

        await db.commit()
        await db.refresh(config)

        # 内部逻辑：如果配置处于激活状态，触发热重载
        # 修复：之前保存配置后不会触发热重载，导致运行时配置不更新
        if config.status == 1:
            await cls._reload_config(config)

        logger.info(f"模型配置已保存: {config.provider_name} - {config.model_name}")
        return config
