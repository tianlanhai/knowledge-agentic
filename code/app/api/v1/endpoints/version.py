# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：镜像版本信息API端点
内部逻辑：提供当前镜像版本的能力信息查询接口
"""

from fastapi import APIRouter
from app.schemas.response import SuccessResponse
from app.core.version_config import VersionConfig, ImageVersion
from loguru import logger

# 变量：创建路由实例
router = APIRouter()


@router.get("/info", response_model=SuccessResponse[dict])
async def get_version_info():
    """
    函数级注释：获取当前镜像版本信息
    内部逻辑：读取环境变量 -> 获取版本能力 -> 返回版本信息
    返回值：包含版本、描述、支持的提供商等信息的字典
    """
    try:
        # 内部逻辑：获取当前版本能力
        capability = VersionConfig.get_version_capability()

        # 内部逻辑：转换为API响应格式
        response_data = {
            **capability.to_dict(),
            "is_cloud_llm": VersionConfig.is_cloud_llm_version(),
            "is_local_llm": VersionConfig.is_local_llm_version(),
        }

        logger.info(f"当前镜像版本: {capability.version.value}")

        return SuccessResponse(data=response_data)

    except Exception as e:
        logger.error(f"获取版本信息失败: {str(e)}")
        # 返回默认版本信息（兜底）
        default_capability = VersionConfig.get_version_capability(ImageVersion.V1)
        return SuccessResponse(
            data={
                **default_capability.to_dict(),
                "is_cloud_llm": True,
                "is_local_llm": False,
                "error": str(e),
            }
        )


@router.get("/capabilities", response_model=SuccessResponse[dict])
async def get_all_version_capabilities():
    """
    函数级注释：获取所有镜像版本的能力信息（用于文档和对比）
    内部逻辑：遍历所有版本 -> 收集能力信息 -> 返回完整列表
    返回值：包含所有版本能力的字典
    """
    try:
        # 内部逻辑：收集所有版本的能力
        all_capabilities = {}
        for version in ImageVersion:
            capability = VersionConfig.get_version_capability(version)
            all_capabilities[version.value] = capability.to_dict()

        # 内部逻辑：添加当前版本标识
        current_version = VersionConfig.get_current_version().value

        return SuccessResponse(
            data={
                "current_version": current_version,
                "all_versions": all_capabilities,
            }
        )

    except Exception as e:
        logger.error(f"获取版本能力列表失败: {str(e)}")
        raise


@router.get("/validate", response_model=SuccessResponse[dict])
async def validate_config(
    llm_provider: str = None,
    embedding_provider: str = None,
):
    """
    函数级注释：验证配置是否与当前镜像版本兼容
    内部逻辑：检查LLM和Embedding提供商 -> 返回验证结果
    参数：
        llm_provider: LLM提供商名称（可选）
        embedding_provider: Embedding提供商名称（可选）
    返回值：包含验证结果和错误信息的字典
    """
    try:
        # 内部逻辑：如果未提供参数，返回当前支持的提供商列表
        if llm_provider is None and embedding_provider is None:
            return SuccessResponse(
                data={
                    "valid": True,
                    "supported_llm_providers": VersionConfig.get_supported_llm_providers(),
                    "supported_embedding_providers": VersionConfig.get_supported_embedding_providers(),
                    "message": "未提供配置参数，返回当前版本支持的提供商列表",
                }
            )

        # 内部逻辑：验证配置
        is_valid, error_message = VersionConfig.validate_config(
            llm_provider=llm_provider or "",
            embedding_provider=embedding_provider or ""
        )

        return SuccessResponse(
            data={
                "valid": is_valid,
                "message": error_message if not is_valid else "配置与当前镜像版本兼容",
                "current_version": VersionConfig.get_current_version().value,
            }
        )

    except Exception as e:
        logger.error(f"验证配置失败: {str(e)}")
        return SuccessResponse(
            data={
                "valid": False,
                "message": f"验证过程出错: {str(e)}",
            }
        )
