# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：配置端点基类模块
内部逻辑：封装 LLM 和 Embedding 配置的通用 CRUD 操作，消除代码重复
设计模式：模板方法模式（Template Method Pattern）+ 泛型设计
设计原则：DRY原则（Don't Repeat Yourself）、开闭原则、依赖倒置原则
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, TypeVar, Generic, Type, Callable
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.schemas.response import SuccessResponse, ErrorResponse


# 泛型类型定义
ConfigCreateType = TypeVar('ConfigCreateType')
ConfigResponseType = TypeVar('ConfigResponseType')
ConfigResponseTypeSafe = TypeVar('ConfigResponseTypeSafe')
ConfigModelType = TypeVar('ConfigModelType')
ServiceType = TypeVar('ServiceType')


class BaseConfigEndpoint(ABC, Generic[
    ConfigCreateType,
    ConfigResponseType,
    ConfigResponseTypeSafe,
    ConfigModelType,
    ServiceType
]):
    """
    类级注释：配置端点基类
    设计模式：模板方法模式 + 泛型设计
    职责：
        1. 封装通用的配置 CRUD 操作
        2. 提供统一的错误处理
        3. 提供统一的响应格式化

    使用场景：
        - LLM 配置端点
        - Embedding 配置端点
        - 其他配置端点

    泛型参数：
        ConfigCreateType: 创建配置的请求类型
        ConfigResponseType: 完整配置响应类型
        ConfigResponseTypeSafe: 脱敏配置响应类型
        ConfigModelType: 配置模型类型
        ServiceType: 服务类型
    """

    # ========================================================================
    # 抽象方法 - 子类必须实现
    # ========================================================================

    @abstractmethod
    def get_service_class(self) -> Type[ServiceType]:
        """
        函数级注释：获取服务类（抽象方法）
        子类必须实现，返回对应的服务类
        返回值：服务类
        """
        pass

    @abstractmethod
    def get_create_schema_class(self) -> Type[ConfigCreateType]:
        """
        函数级注释：获取创建配置的 Schema 类（抽象方法）
        子类必须实现
        返回值：创建配置的 Schema 类
        """
        pass

    @abstractmethod
    def get_response_schema_safe_class(self) -> Type[ConfigResponseTypeSafe]:
        """
        函数级注释：获取脱敏响应的 Schema 类（抽象方法）
        子类必须实现
        返回值：脱敏响应的 Schema 类
        """
        pass

    @abstractmethod
    def get_config_type_name(self) -> str:
        """
        函数级注释：获取配置类型名称（抽象方法）
        用于日志和错误消息
        返回值：配置类型名称（如 "LLM"、"Embedding"）
        """
        pass

    @abstractmethod
    def get_response_builder_utils(self):
        """
        函数级注释：获取响应构建工具类（抽象方法）
        返回值：包含 build_from_model_config 等方法的工具类
        """
        pass

    # ========================================================================
    # 内部辅助方法
    # ========================================================================

    def _get_service(self) -> ServiceType:
        """
        函数级注释：获取服务实例
        返回值：服务实例
        """
        return self.get_service_class()

    def _get_mask_function(self, service: ServiceType) -> Callable:
        """
        函数级注释：获取脱敏函数
        参数：
            service: 服务实例
        返回值：脱敏函数
        """
        return service.mask_api_key

    def _format_config_response(
        self,
        config_model: ConfigModelType,
        service: ServiceType,
        response_class: Type[ConfigResponseTypeSafe]
    ) -> ConfigResponseTypeSafe:
        """
        函数级注释：格式化配置响应（脱敏）
        设计模式：策略模式 - 使用不同的脱敏策略
        参数：
            config_model: 配置模型实例
            service: 服务实例
            response_class: 响应 Schema 类
        返回值：脱敏后的配置响应
        """
        # 内部逻辑：使用响应构建工具类构造脱敏响应
        builder_utils = self.get_response_builder_utils()
        mask_func = self._get_mask_function(service)

        config_dict = builder_utils.build_from_model_config(
            config_model,
            mask_func
        )

        return response_class(**config_dict)

    def _format_config_list_response(
        self,
        configs: list,
        service: ServiceType,
        response_class: Type[ConfigResponseTypeSafe]
    ) -> list:
        """
        函数级注释：格式化配置列表响应（脱敏）
        参数：
            configs: 配置模型列表
            service: 服务实例
            response_class: 响应 Schema 类
        返回值：脱敏后的配置响应列表
        """
        return [
            self._format_config_response(c, service, response_class)
            for c in configs
        ]

    # ========================================================================
    # 模板方法 - 通用的 CRUD 操作
    # ========================================================================

    async def get_configs(
        self,
        db: AsyncSession
    ) -> SuccessResponse[Dict[str, list]]:
        """
        函数级注释：获取所有配置（模板方法）
        内部逻辑：调用服务获取配置 -> 格式化响应 -> 返回
        参数：
            db: 数据库会话
        返回值：配置列表响应
        """
        config_type = self.get_config_type_name()
        try:
            service = self._get_service()

            # 内部逻辑：获取配置列表
            configs = await service.get_model_configs(db)

            # 内部逻辑：转换为脱敏响应
            response_class = self.get_response_schema_safe_class()
            config_responses = self._format_config_list_response(
                configs,
                service,
                response_class
            )

            return SuccessResponse(
                data={"configs": config_responses}
            )
        except Exception as e:
            logger.error(f"获取{config_type}配置失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")

    async def save_config(
        self,
        config_data: ConfigCreateType,
        db: AsyncSession
    ) -> SuccessResponse[ConfigResponseTypeSafe]:
        """
        函数级注释：保存配置（模板方法）
        内部逻辑：验证数据 -> 保存到数据库 -> 返回脱敏响应
        参数：
            config_data: 配置数据
            db: 数据库会话
        返回值：保存后的配置响应
        """
        config_type = self.get_config_type_name()
        try:
            service = self._get_service()

            # 内部逻辑：保存配置
            config = await service.save_model_config(db, config_data.model_dump())

            # 内部逻辑：格式化脱敏响应
            response_class = self.get_response_schema_safe_class()
            config_response = self._format_config_response(
                config,
                service,
                response_class
            )

            return SuccessResponse(
                data=config_response,
                message="配置已保存"
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"保存{config_type}配置失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")

    async def set_default_config(
        self,
        config_id: str,
        db: AsyncSession
    ) -> SuccessResponse[ConfigResponseTypeSafe]:
        """
        函数级注释：启用配置（模板方法）
        内部逻辑：取消其他启用状态 -> 设置新配置为启用 -> 返回脱敏响应
        参数：
            config_id: 配置ID
            db: 数据库会话
        返回值：更新后的配置响应
        """
        config_type = self.get_config_type_name()
        try:
            service = self._get_service()

            config = await service.set_default_config(db, config_id)

            # 内部逻辑：格式化脱敏响应
            response_class = self.get_response_schema_safe_class()
            config_response = self._format_config_response(
                config,
                service,
                response_class
            )

            return SuccessResponse(
                data=config_response,
                message=f"{config_type}配置已启用并生效"
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"启用{config_type}配置失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"设置失败: {str(e)}")

    async def delete_config(
        self,
        config_id: str,
        db: AsyncSession
    ) -> SuccessResponse[Dict[str, bool]]:
        """
        函数级注释：删除配置（模板方法）
        内部逻辑：验证非默认配置 -> 删除配置 -> 返回成功
        参数：
            config_id: 配置ID
            db: 数据库会话
        返回值：删除成功响应
        """
        config_type = self.get_config_type_name()
        try:
            service = self._get_service()
            success = await service.delete_config(db, config_id)

            if not success:
                raise HTTPException(status_code=404, detail="配置不存在")

            return SuccessResponse(
                data={"deleted": True},
                message="配置已删除"
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"删除{config_type}配置失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

    async def update_api_key(
        self,
        config_id: str,
        api_key: str,
        db: AsyncSession,
        response_class: Type[ConfigResponseTypeSafe]
    ) -> SuccessResponse:
        """
        函数级注释：更新API密钥（模板方法）
        内部逻辑：验证配置存在 -> 更新API密钥 -> 返回脱敏结果
        参数：
            config_id: 配置ID
            api_key: 新的API密钥
            db: 数据库会话
            response_class: 响应 Schema 类
        返回值：脱敏后的密钥响应
        """
        config_type = self.get_config_type_name()
        try:
            service = self._get_service()
            config = await service.update_api_key(db, config_id, api_key)

            from app.schemas.model_config import APIKeyUpdateResponse
            return SuccessResponse(
                data=APIKeyUpdateResponse(
                    api_key_masked=service.mask_api_key(config.api_key),
                    message="API密钥已更新"
                ),
                message="API密钥已更新"
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"更新{config_type} API密钥失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


# 内部变量：导出所有公共接口
__all__ = [
    'BaseConfigEndpoint',
]
