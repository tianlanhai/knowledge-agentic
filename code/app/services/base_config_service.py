# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：配置服务基类
内部逻辑：提取配置服务的公共逻辑，消除 ModelConfigService 和 EmbeddingConfigService 的重复代码
设计模式：模板方法模式（Template Method Pattern）
设计原则：DRY（不重复）、SOLID（开闭原则）
"""

from abc import ABC, abstractmethod
from typing import List, Optional, TypeVar, Generic, Type, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

# 泛型类型：配置模型类型
T = TypeVar('T')


class BaseConfigService(ABC, Generic[T]):
    """
    类级注释：配置服务基类
    设计模式：模板方法模式
    职责：
        1. 定义配置服务的通用操作模板
        2. 提供公共的 CRUD 逻辑
        3. 子类只需实现模型特定的抽象方法
    内部变量：
        _config_model: 配置模型类（由子类提供）
    """

    @classmethod
    def mask_api_key(cls, api_key: Optional[str]) -> str:
        """
        函数级注释：对API密钥进行脱敏处理
        内部逻辑：使用统一的脱敏工具类
        参数：
            api_key: 原始API密钥（可能为空）
        返回值：脱敏后的密钥字符串，格式如 sk-****1234
        """
        from app.core.mask_strategy import MaskUtils
        return MaskUtils.mask_api_key(api_key)

    @classmethod
    async def update_api_key(
        cls,
        db: AsyncSession,
        config_id: str,
        new_api_key: str
    ) -> T:
        """
        函数级注释：更新指定配置的API密钥
        内部逻辑：查询配置 -> 更新api_key -> 触发热重载（如果启用）
        参数：
            db: 数据库会话
            config_id: 配置ID
            new_api_key: 新的API密钥
        返回值：更新后的配置对象
        异常：
            ValueError: 配置不存在
        """
        # 内部逻辑：查询配置
        config_model = cls._get_config_model()
        result = await db.execute(
            select(config_model).where(config_model.id == config_id)
        )
        config = result.scalar_one_or_none()

        # 内部逻辑：Guard Clauses - 配置不存在
        if not config:
            raise ValueError(f"配置不存在: {config_id}")

        # 内部逻辑：更新API密钥
        config.api_key = new_api_key
        await db.commit()
        await db.refresh(config)

        # 内部逻辑：如果配置处于启用状态，触发热重载
        if config.status == 1:
            await cls._reload_config(config)

        logger.info(f"{cls._get_config_type()} API密钥已更新: {config.provider_name} - {config.model_name}")
        return config

    @classmethod
    async def get_configs(cls, db: AsyncSession) -> List[T]:
        """
        函数级注释：获取所有配置（首次访问自动初始化）
        内部逻辑：查询数据库 -> 如果为空则初始化默认配置 -> 返回配置列表
        参数：
            db: 数据库会话
        返回值：配置列表
        """
        # 内部逻辑：查询所有配置，按修改时间倒序排列
        config_model = cls._get_config_model()
        result = await db.execute(
            select(config_model).order_by(config_model.updated_at.desc())
        )
        configs = result.scalars().all()

        # 内部逻辑：Guard Clauses - 如果没有配置，初始化默认配置
        if not configs:
            logger.info(f"未找到{cls._get_config_type()}配置，开始初始化默认配置")
            configs = await cls._init_default_configs(db)

        return configs

    @classmethod
    async def get_default_config(cls, db: AsyncSession) -> Optional[T]:
        """
        函数级注释：获取当前启用的配置
        内部逻辑：查询status=1的配置，处理多行数据修复
        参数：
            db: 数据库会话
        返回值：启用中的配置对象，未找到返回None
        """
        config_model = cls._get_config_model()
        # 内部逻辑：先获取所有status=1的配置
        result = await db.execute(
            select(config_model).where(
                config_model.status == 1
            ).order_by(config_model.created_at)
        )
        active_configs = result.scalars().all()

        # 内部逻辑：Guard Clauses - 没有启用的配置
        if not active_configs:
            return None

        # 内部逻辑：如果只有一个启用配置，直接返回
        if len(active_configs) == 1:
            return active_configs[0]

        # 内部逻辑：数据修复 - 如果有多个status=1，保留第一个或优先保留有api_key的
        return await cls._fix_multiple_active_configs(db, active_configs)

    @classmethod
    async def get_config_by_id(cls, db: AsyncSession, config_id: str) -> Optional[T]:
        """
        函数级注释：根据ID获取配置
        参数：
            db: 数据库会话
            config_id: 配置ID
        返回值：配置对象，未找到返回None
        """
        config_model = cls._get_config_model()
        result = await db.execute(
            select(config_model).where(config_model.id == config_id)
        )
        return result.scalar_one_or_none()

    @classmethod
    async def set_default_config(cls, db: AsyncSession, config_id: str) -> T:
        """
        函数级注释：设置启用的配置（触发热重载）
        内部逻辑：取消其他配置启用状态 -> 设置新配置为启用 -> 提交事务 -> 触发热重载
        参数：
            db: 数据库会话
            config_id: 配置ID
        返回值：更新后的配置对象
        异常：
            ValueError: 配置不存在
        """
        config_model = cls._get_config_model()

        # 内部逻辑：取消所有其他配置的启用状态（status设为0）
        result = await db.execute(select(config_model))
        all_configs = result.scalars().all()
        for config in all_configs:
            config.status = 0

        # 内部逻辑：设置新的启用配置（status设为1）
        result = await db.execute(
            select(config_model).where(config_model.id == config_id)
        )
        config = result.scalar_one_or_none()

        # 内部逻辑：Guard Clauses - 配置不存在则抛出异常
        if not config:
            raise ValueError(f"配置不存在: {config_id}")

        config.status = 1

        await db.commit()
        await db.refresh(config)

        # 内部逻辑：触发热重载
        await cls._reload_config(config)

        logger.info(f"已启用{cls._get_config_type()}: {config.provider_name} - {config.model_name}")
        return config

    @classmethod
    async def delete_config(cls, db: AsyncSession, config_id: str) -> bool:
        """
        函数级注释：删除配置
        内部逻辑：不能删除启用的配置 -> 删除指定配置 -> 提交事务
        参数：
            db: 数据库会话
            config_id: 配置ID
        返回值：删除成功返回True，失败返回False
        异常：
            ValueError: 不能删除启用的配置
        """
        config_model = cls._get_config_model()
        result = await db.execute(
            select(config_model).where(config_model.id == config_id)
        )
        config = result.scalar_one_or_none()

        # 内部逻辑：Guard Clauses - 配置不存在
        if not config:
            return False

        # 内部逻辑：Guard Clauses - 不能删除启用的配置
        if config.status == 1:
            raise ValueError("不能删除启用的配置，请先启用其他配置")

        await db.delete(config)
        await db.commit()
        logger.info(f"{cls._get_config_type()}配置已删除: {config_id}")
        return True

    # ==================== 抽象方法（子类实现） ====================

    @classmethod
    @abstractmethod
    def _get_config_model(cls) -> Type[T]:
        """
        函数级注释：获取配置模型类
        返回值：ModelConfig 或 EmbeddingConfig 类
        """
        pass

    @classmethod
    @abstractmethod
    def _get_config_type(cls) -> str:
        """
        函数级注释：获取配置类型名称
        返回值：如 "模型" 或 "Embedding"
        """
        pass

    @classmethod
    @abstractmethod
    async def _init_default_configs(cls, db: AsyncSession) -> List[T]:
        """
        函数级注释：初始化默认配置
        内部逻辑：子类实现具体的初始化逻辑
        参数：
            db: 数据库会话
        返回值：初始化的配置列表
        """
        pass

    @classmethod
    @abstractmethod
    async def _reload_config(cls, config: T) -> None:
        """
        函数级注释：触发热重载
        内部逻辑：子类实现具体的热重载逻辑
        参数：
            config: 配置对象
        """
        pass

    # ==================== 私有辅助方法 ====================

    @classmethod
    async def _fix_multiple_active_configs(cls, db: AsyncSession, active_configs: List[T]) -> T:
        """
        函数级注释：修复多个启用配置的数据
        内部逻辑：优先选择有 api_key 的配置，如果都没有则保留第一个
        参数：
            db: 数据库会话
            active_configs: 启用状态的配置列表
        返回值：保留的配置对象
        """
        # 内部逻辑：优先选择有 api_key 的配置
        for config in active_configs:
            if config.api_key:
                logger.warning(
                    f"发现 {len(active_configs)} 个启用{cls._get_config_type()}配置，"
                    f"选择有API密钥的: {config.provider_name}"
                )
                # 内部逻辑：数据修复 - 将其他配置的status设为0
                for other in active_configs:
                    if other.id != config.id:
                        other.status = 0
                await db.commit()
                logger.info(f"已修复启用{cls._get_config_type()}配置，保留: {config.provider_name} - {config.model_name}")
                return config

        # 内部逻辑：如果都没有 api_key，保留第一个
        logger.warning(f"发现 {len(active_configs)} 个启用{cls._get_config_type()}配置且都没有API密钥，保留第一个")
        keep_config = active_configs[0]
        for config in active_configs[1:]:
            config.status = 0

        await db.commit()
        logger.info(f"已修复启用{cls._get_config_type()}配置，保留: {keep_config.provider_name} - {keep_config.model_name}")
        return keep_config
