# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：Embedding配置服务
内部逻辑：提供Embedding模型配置的CRUD操作和热切换支持
设计模式：模板方法模式 - 继承 BaseConfigService
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from sqlalchemy.exc import IntegrityError
from app.models.model_config import EmbeddingConfig
from app.core.llm_constants import EMBEDDING_PROVIDERS, DEFAULT_MODEL_SETTINGS
from app.services.base_config_service import BaseConfigService
from loguru import logger
import uuid


class EmbeddingConfigService(BaseConfigService[EmbeddingConfig]):
    """
    类级注释：Embedding配置服务类
    设计模式：模板方法模式 - 继承 BaseConfigService
    职责：
        1. 继承配置服务的通用CRUD操作
        2. 实现Embedding特定的抽象方法
        3. 提供 EmbeddingConfig 特有的方法
    内部变量：
        继承自 BaseConfigService 的所有功能
    """

    # ==================== 实现抽象方法 ====================

    @classmethod
    def _get_config_model(cls) -> type:
        """
        函数级注释：获取配置模型类
        返回值：EmbeddingConfig 模型类
        """
        return EmbeddingConfig

    @classmethod
    def _get_config_type(cls) -> str:
        """
        函数级注释：获取配置类型名称
        返回值："Embedding"
        """
        return "Embedding"

    @classmethod
    async def _init_default_configs(cls, db: AsyncSession) -> List[EmbeddingConfig]:
        """
        函数级注释：初始化默认Embedding配置
        内部逻辑：先检查是否存在配置，为空则批量插入，捕获唯一约束冲突防止并发重复插入
        参数：
            db: 数据库会话
        返回值：初始化的配置列表
        """
        # 内部逻辑：先检查是否已有配置
        existing_result = await db.execute(select(EmbeddingConfig))
        existing_configs = existing_result.scalars().all()
        if existing_configs:
            logger.info(f"Embedding配置已存在 ({len(existing_configs)} 个)，跳过初始化")
            return list(existing_configs)

        # 内部变量：默认提供商（只有这个会被设为status=1）
        default_provider_id = "ollama"

        # 内部逻辑：批量插入所有配置
        configs_to_insert = []
        for provider in EMBEDDING_PROVIDERS:
            # 内部逻辑：确定设备配置，所有提供商都设置默认值
            device = "auto" if provider["id"] == "local" else "cpu"

            config_data = {
                "id": str(uuid.uuid4()),
                "provider_id": provider["id"],
                "provider_name": provider["name"],
                "endpoint": provider.get("default_endpoint", ""),
                "api_key": "",
                "model_id": provider["default_models"][0] if provider["default_models"] else "",
                "model_name": provider["default_models"][0] if provider["default_models"] else "",
                "device": device,
                "status": 1 if (provider["id"] == default_provider_id) else 0
            }
            configs_to_insert.append(EmbeddingConfig(**config_data))

        try:
            db.add_all(configs_to_insert)
            await db.commit()
            logger.info(f"初始化默认Embedding配置完成，共 {len(configs_to_insert)} 个提供商")
            return configs_to_insert
        except IntegrityError:
            # 内部逻辑：并发初始化时，捕获唯一约束冲突，回滚后重新查询已有配置
            await db.rollback()
            logger.info("检测到并发初始化，重新查询已有配置")
            result = await db.execute(select(EmbeddingConfig))
            configs = result.scalars().all()
            return list(configs)

    @classmethod
    async def _reload_config(cls, config: EmbeddingConfig) -> None:
        """
        函数级注释：触发热重载

        配置优先级说明：
            本方法将数据库中的配置注入到 EmbeddingFactory 运行时，
            使数据库配置拥有最高优先级（高于环境变量、.env 文件和代码默认值）。

        内部逻辑：更新EmbeddingFactory的运行时配置 -> 清除实例缓存
        参数：
            config: 配置对象（来自数据库 EmbeddingConfig 表）
        """
        try:
            from app.utils.embedding_factory import EmbeddingFactory

            # 内部变量：构建配置字典，用于运行时热重载
            config_dict = {
                "provider": config.provider_id,
                "model": config.model_name,
                "endpoint": config.endpoint,
                "api_key": config.api_key,
                "device": config.device
            }

            # 内部逻辑：添加详细日志，便于诊断配置更新问题
            logger.info(f"[热重载] 准备更新Embedding运行时配置: provider={config.provider_id}, endpoint={config.endpoint}")
            logger.info(f"[诊断] Embedding配置原始值: provider_id={config.provider_id}, device={repr(config.device)}, model={config.model_name}")

            EmbeddingFactory.set_runtime_config(config_dict)
            logger.info(f"Embedding运行时配置已热重载: {config.provider_name} - {config.model_name}, endpoint={config.endpoint}")
        except ImportError:
            logger.warning("EmbeddingFactory未找到，跳过热重载")
        except Exception as e:
            logger.error(f"热重载失败: {str(e)}")

    # ==================== EmbeddingConfig 特有方法 ====================

    @classmethod
    async def get_embedding_configs(cls, db: AsyncSession) -> List[EmbeddingConfig]:
        """
        函数级注释：获取所有Embedding配置（向后兼容的别名方法）
        内部逻辑：委托给基类的 get_configs 方法
        参数：
            db: 数据库会话
        返回值：Embedding配置列表
        """
        return await cls.get_configs(db)

    @classmethod
    async def save_embedding_config(
        cls,
        db: AsyncSession,
        config_data: Dict[str, Any]
    ) -> EmbeddingConfig:
        """
        函数级注释：保存或更新Embedding配置（EmbeddingConfig 特有方法）
        内部逻辑：有ID则更新，无ID则创建 -> 提交事务 -> 返回配置对象
        参数：
            db: 数据库会话
            config_data: 配置数据字典
        返回值：保存后的配置对象
        异常：
            ValueError: 当config_id存在但配置不存在时抛出异常
        """
        config_id = config_data.get("id")

        # 内部逻辑：根据是否有ID决定更新或创建
        if config_id:
            # 更新现有配置
            result = await db.execute(
                select(EmbeddingConfig).where(EmbeddingConfig.id == config_id)
            )
            config = result.scalar_one_or_none()

            # 内部逻辑：Guard Clauses - 配置不存在则抛出异常
            if not config:
                raise ValueError(f"配置不存在: {config_id}，无法更新。如需新增，请清除id字段。")

            # 更新配置字段（排除id字段，防止覆盖）
            for key, value in config_data.items():
                if hasattr(config, key) and key != 'id':
                    setattr(config, key, value)
        else:
            # 创建新配置
            if not config_data.get("id"):
                config_data["id"] = str(uuid.uuid4())
            config = EmbeddingConfig(**config_data)
            db.add(config)

        await db.commit()
        await db.refresh(config)

        # 内部逻辑：如果配置处于激活状态，触发热重载
        # 修复：之前保存配置后不会触发热重载，导致运行时配置不更新
        if config.status == 1:
            await cls._reload_config(config)

        logger.info(f"Embedding配置已保存: {config.provider_name} - {config.model_name}")
        return config
