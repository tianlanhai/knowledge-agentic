# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：配置服务基类模块
内部逻辑：使用模板方法模式为配置服务提供通用流程
设计模式：模板方法模式（Template Method Pattern）
设计原则：SOLID - 开闭原则、里氏替换原则

@package app.services
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, Dict, Any, List, Type
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, ValidationError


# 内部变量：泛型类型
T = TypeVar('T', bound=BaseModel)
CreateT = TypeVar('CreateT', bound=BaseModel)
UpdateT = TypeVar('UpdateT', bound=BaseModel)
IDT = TypeVar('IDT')


class ConfigStatus(Enum):
    """
    类级注释：配置状态枚举
    内部逻辑：定义配置的生命周期状态
    """
    # 草稿
    DRAFT = "draft"
    # 激活
    ACTIVE = "active"
    # 归档
    ARCHIVED = "archived"
    # 已删除
    DELETED = "deleted"


@dataclass
class ValidationResult:
    """
    类级注释：验证结果数据类
    内部逻辑：封装验证结果信息
    """
    # 属性：是否通过
    is_valid: bool
    # 属性：错误信息
    errors: List[str] = field(default_factory=list)
    # 属性：警告信息
    warnings: List[str] = field(default_factory=list)

    def add_error(self, error: str) -> None:
        """添加错误"""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        """添加警告"""
        self.warnings.append(warning)


class ConfigValidator(Generic[T], ABC):
    """
    类级注释：配置验证器抽象
    内部逻辑：定义配置验证的接口
    设计模式：策略模式 - 验证策略
    """

    @abstractmethod
    async def validate(self, config: T) -> ValidationResult:
        """
        函数级注释：验证配置
        参数：
            config - 配置对象
        返回值：验证结果
        """
        pass


class DefaultConfigValidator(Generic[T], ConfigValidator[T]):
    """
    类级注释：默认配置验证器
    内部逻辑：使用 Pydantic 进行基础验证
    设计模式：策略模式 - 默认策略
    """

    async def validate(self, config: T) -> ValidationResult:
        """验证配置（使用 Pydantic）"""
        result = ValidationResult(is_valid=True)

        try:
            # 内部逻辑：Pydantic 模型会自动验证
            if hasattr(config, 'model_validate'):
                config.model_validate(config.model_dump())
        except ValidationError as e:
            result.is_valid = False
            for error in e.errors():
                result.add_error(f"{'.'.join(str(loc) for loc in error['loc'])}: {error['msg']}")

        return result


class ConfigRepository(Generic[T, IDT], ABC):
    """
    类级注释：配置仓储抽象接口
    内部逻辑：定义配置数据访问的接口
    设计模式：仓储模式（Repository Pattern）
    """

    @abstractmethod
    async def get_by_id(self, id: IDT) -> Optional[T]:
        """根据 ID 获取配置"""
        pass

    @abstractmethod
    async def get_all(
        self,
        status: Optional[ConfigStatus] = None,
        limit: int = 100
    ) -> List[T]:
        """获取所有配置"""
        pass

    @abstractmethod
    async def get_active(self) -> Optional[T]:
        """获取激活的配置"""
        pass

    @abstractmethod
    async def create(self, config: T) -> T:
        """创建配置"""
        pass

    @abstractmethod
    async def update(self, config: T) -> T:
        """更新配置"""
        pass

    @abstractmethod
    async def delete(self, id: IDT) -> bool:
        """删除配置"""
        pass

    @abstractmethod
    async def set_status(self, id: IDT, status: ConfigStatus) -> bool:
        """设置配置状态"""
        pass


class BaseConfigService(Generic[T, CreateT, UpdateT, IDT], ABC):
    """
    类级注释：配置服务基类
    内部逻辑：定义配置服务的通用流程
    设计模式：模板方法模式
    职责：
        1. 定义配置管理的通用流程
        2. 提供钩子方法供子类扩展
        3. 实现通用的业务逻辑

    使用场景：
        - 模型配置服务
        - 嵌入配置服务
        - 其他配置类服务
    """

    def __init__(
        self,
        repository: ConfigRepository[T, IDT],
        validator: Optional[ConfigValidator[T]] = None
    ):
        """
        函数级注释：初始化配置服务
        参数：
            repository - 配置仓储
            validator - 配置验证器
        """
        self._repository = repository
        self._validator = validator or DefaultConfigValidator[T]()
        logger.info(f"[{self.__class__.__name__}] 初始化完成")

    async def get_by_id(self, id: IDT) -> Optional[T]:
        """
        函数级注释：根据 ID 获取配置
        参数：
            id - 配置 ID
        返回值：配置对象或 None
        """
        return await self._repository.get_by_id(id)

    async def get_all(
        self,
        status: Optional[ConfigStatus] = None,
        limit: int = 100
    ) -> List[T]:
        """
        函数级注释：获取所有配置
        参数：
            status - 状态过滤
            limit - 返回数量限制
        返回值：配置列表
        """
        return await self._repository.get_all(status, limit)

    async def get_active(self) -> Optional[T]:
        """
        函数级注释：获取激活的配置
        返回值：激活的配置或 None
        """
        return await self._repository.get_active()

    async def create_config(
        self,
        db: AsyncSession,
        data: CreateT,
        auto_activate: bool = False
    ) -> T:
        """
        函数级注释：创建配置（模板方法）
        内部逻辑：执行完整的创建流程
        参数：
            db - 数据库会话
            data - 创建数据
            auto_activate - 是否自动激活
        返回值：创建的配置对象
        """
        logger.info(f"[{self.__class__.__name__}] 开始创建配置")

        # 步骤1：验证前钩子
        await self._before_validate(data)

        # 步骤2：验证数据
        validation_result = await self._validate_create_data(data)
        if not validation_result.is_valid:
            logger.warning(
                f"[{self.__class__.__name__}] 验证失败: {validation_result.errors}"
            )
            raise ValueError(f"配置验证失败: {'; '.join(validation_result.errors)}")

        # 步骤3：验证后钩子
        await self._after_validate(data)

        # 步骤4：转换数据
        entity = await self._to_entity(data)

        # 步骤5：保存前钩子
        await self._before_create(db, entity)

        # 步骤6：保存到数据库
        result = await self._repository.create(entity)

        # 步骤7：保存后钩子
        await self._after_create(db, result)

        # 步骤8：自动激活
        if auto_activate:
            await self.activate_config(db, result.id)

        logger.info(
            f"[{self.__class__.__name__}] 配置创建成功: {result.id if hasattr(result, 'id') else 'N/A'}"
        )

        return result

    async def update_config(
        self,
        db: AsyncSession,
        id: IDT,
        data: UpdateT
    ) -> T:
        """
        函数级注释：更新配置（模板方法）
        内部逻辑：执行完整的更新流程
        参数：
            db - 数据库会话
            id - 配置 ID
            data - 更新数据
        返回值：更新后的配置对象
        """
        logger.info(f"[{self.__class__.__name__}] 开始更新配置: {id}")

        # 步骤1：获取现有配置
        existing = await self._repository.get_by_id(id)
        if not existing:
            raise ValueError(f"配置不存在: {id}")

        # 步骤2：验证前钩子
        await self._before_update_validate(db, existing, data)

        # 步骤3：验证数据
        validation_result = await self._validate_update_data(existing, data)
        if not validation_result.is_valid:
            raise ValueError(f"配置验证失败: {'; '.join(validation_result.errors)}")

        # 步骤4：更新数据
        updated = await self._merge_update_data(existing, data)

        # 步骤5：更新前钩子
        await self._before_update(db, updated)

        # 步骤6：保存更新
        result = await self._repository.update(updated)

        # 步骤7：更新后钩子
        await self._after_update(db, result)

        logger.info(f"[{self.__class__.__name__}] 配置更新成功: {id}")

        return result

    async def delete_config(
        self,
        db: AsyncSession,
        id: IDT,
        soft_delete: bool = True
    ) -> bool:
        """
        函数级注释：删除配置（模板方法）
        内部逻辑：执行完整的删除流程
        参数：
            db - 数据库会话
            id - 配置 ID
            soft_delete - 是否软删除
        返回值：是否删除成功
        """
        logger.info(f"[{self.__class__.__name__}] 开始删除配置: {id}")

        # 步骤1：删除前钩子
        await self._before_delete(db, id)

        if soft_delete:
            result = await self._repository.set_status(id, ConfigStatus.DELETED)
        else:
            result = await self._repository.delete(id)

        if result:
            # 步骤2：删除后钩子
            await self._after_delete(db, id)
            logger.info(f"[{self.__class__.__name__}] 配置删除成功: {id}")

        return result

    async def activate_config(
        self,
        db: AsyncSession,
        id: IDT,
        deactivate_others: bool = True
    ) -> bool:
        """
        函数级注释：激活配置
        内部逻辑：设置配置为激活状态，可选择停用其他配置
        参数：
            db - 数据库会话
            id - 配置 ID
            deactivate_others - 是否停用其他配置
        返回值：是否激活成功
        """
        logger.info(f"[{self.__class__.__name__}] 开始激活配置: {id}")

        # 步骤1：激活前钩子
        await self._before_activate(db, id)

        # 步骤2：停用其他配置
        if deactivate_others:
            all_configs = await self._repository.get_all()
            for config in all_configs:
                if hasattr(config, 'id') and config.id != id:
                    await self._repository.set_status(config.id, ConfigStatus.ARCHIVED)

        # 步骤3：激活目标配置
        result = await self._repository.set_status(id, ConfigStatus.ACTIVE)

        if result:
            # 步骤4：激活后钩子
            await self._after_activate(db, id)
            logger.info(f"[{self.__class__.__name__}] 配置激活成功: {id}")

        return result

    # ==================== 钩子方法 ====================

    async def _before_validate(self, data: CreateT) -> None:
        """
        函数级注释：验证前钩子（子类可覆盖）
        参数：
            data - 创建数据
        """
        pass

    async def _after_validate(self, data: CreateT) -> None:
        """
        函数级注释：验证后钩子（子类可覆盖）
        参数：
            data - 创建数据
        """
        pass

    async def _before_create(self, db: AsyncSession, entity: T) -> None:
        """
        函数级注释：创建前钩子（子类可覆盖）
        参数：
            db - 数据库会话
            entity - 待创建的实体
        """
        pass

    async def _after_create(self, db: AsyncSession, entity: T) -> None:
        """
        函数级注释：创建后钩子（子类可覆盖）
        参数：
            db - 数据库会话
            entity - 已创建的实体
        """
        pass

    async def _before_update_validate(
        self,
        db: AsyncSession,
        existing: T,
        data: UpdateT
    ) -> None:
        """
        函数级注释：更新验证前钩子（子类可覆盖）
        """
        pass

    async def _before_update(self, db: AsyncSession, entity: T) -> None:
        """更新前钩子"""
        pass

    async def _after_update(self, db: AsyncSession, entity: T) -> None:
        """更新后钩子"""
        pass

    async def _before_delete(self, db: AsyncSession, id: IDT) -> None:
        """删除前钩子"""
        pass

    async def _after_delete(self, db: AsyncSession, id: IDT) -> None:
        """删除后钩子"""
        pass

    async def _before_activate(self, db: AsyncSession, id: IDT) -> None:
        """激活前钩子"""
        pass

    async def _after_activate(self, db: AsyncSession, id: IDT) -> None:
        """激活后钩子"""
        pass

    # ==================== 抽象方法 ====================

    async def _validate_create_data(self, data: CreateT) -> ValidationResult:
        """
        函数级注释：验证创建数据（子类可覆盖）
        参数：
            data - 创建数据
        返回值：验证结果
        """
        if hasattr(data, 'model_validate'):
            return await self._validator.validate(data)
        return ValidationResult(is_valid=True)

    async def _validate_update_data(
        self,
        existing: T,
        data: UpdateT
    ) -> ValidationResult:
        """
        函数级注释：验证更新数据（子类可覆盖）
        参数：
            existing - 现有配置
            data - 更新数据
        返回值：验证结果
        """
        return ValidationResult(is_valid=True)

    @abstractmethod
    async def _to_entity(self, data: CreateT) -> T:
        """
        函数级注释：转换为实体（子类必须实现）
        参数：
            data - 创建数据
        返回值：实体对象
        """
        pass

    async def _merge_update_data(self, existing: T, data: UpdateT) -> T:
        """
        函数级注释：合并更新数据（子类可覆盖）
        参数：
            existing - 现有配置
            data - 更新数据
        返回值：合并后的实体
        """
        # 内部逻辑：默认使用 dataclass 合并策略
        if hasattr(data, 'model_dump'):
            update_dict = data.model_dump(exclude_unset=True)
            for key, value in update_dict.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
        return existing


class ConfigServiceFactory(Generic[T, CreateT, UpdateT, IDT]):
    """
    类级注释：配置服务工厂
    内部逻辑：统一创建配置服务实例
    设计模式：工厂模式 + 抽象工厂模式
    """

    _instances: Dict[str, 'BaseConfigService'] = {}

    @classmethod
    def create(
        cls,
        service_class: Type['BaseConfigService[T, CreateT, UpdateT, IDT]'],
        repository: ConfigRepository[T, IDT],
        validator: Optional[ConfigValidator[T]] = None
    ) -> 'BaseConfigService[T, CreateT, UpdateT, IDT]':
        """
        函数级注释：创建配置服务实例
        参数：
            service_class - 服务类
            repository - 配置仓储
            validator - 配置验证器
        返回值：配置服务实例
        """
        key = f"{service_class.__name__}"
        if key not in cls._instances:
            cls._instances[key] = service_class(repository, validator)
        return cls._instances[key]

    @classmethod
    def get_instance(cls, key: str) -> Optional['BaseConfigService']:
        """获取已创建的服务实例"""
        return cls._instances.get(key)

    @classmethod
    def clear_instances(cls) -> None:
        """清空所有实例"""
        cls._instances.clear()


# 内部变量：导出所有公共接口
__all__ = [
    # 枚举
    'ConfigStatus',
    # 数据类
    'ValidationResult',
    # 验证器
    'ConfigValidator',
    'DefaultConfigValidator',
    # 仓储
    'ConfigRepository',
    # 服务基类
    'BaseConfigService',
    # 工厂
    'ConfigServiceFactory',
]
