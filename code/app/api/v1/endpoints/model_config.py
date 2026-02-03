# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：模型配置API端点
内部逻辑：提供LLM和Embedding模型配置的CRUD接口
参考项目：easy-dataset-file
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.schemas.response import SuccessResponse, ErrorResponse
from app.schemas.model_config import (
    ModelConfigCreate,
    ModelConfigResponse,
    ModelConfigResponseSafe,
    ModelConfigListResponse,
    APIKeyUpdateRequest,
    APIKeyUpdateResponse,
    ProvidersResponse,
    OllamaModelsResponse,
    EmbeddingConfigCreate,
    EmbeddingConfigResponse,
    EmbeddingConfigResponseSafe,
    ConnectionTestRequest,
    ConnectionTestResponse,
    EmbeddingConnectionTestRequest,
    EmbeddingConnectionTestResponse,
    LocalModelsResponse,
)
from app.services.model_config_service import ModelConfigService
from app.services.embedding_config_service import EmbeddingConfigService
from app.services.connection_test_service import ConnectionTestService
from app.services.local_model_service import LocalModelService
from app.models.model_config import ModelConfig
from app.core.llm_constants import LLM_PROVIDERS, EMBEDDING_PROVIDERS
from app.core.response_builders import ConfigResponseBuilderUtils
from app.db.session import get_db
import httpx
from loguru import logger
from app.core.config import settings

# 变量：创建路由实例
router = APIRouter()


@router.get("/llm", response_model=SuccessResponse[dict])
async def get_llm_configs(db: AsyncSession = Depends(get_db)):
    """
    函数级注释：获取所有LLM模型配置（首次访问自动初始化）
    内部逻辑：查询配置 -> 为空则初始化 -> 转换为脱敏响应 -> 返回配置列表
    参数：
        db: 数据库异步会话
    返回值：配置列表响应（status=1的配置为正在使用，API密钥已脱敏）
    """
    try:
        # 内部逻辑：获取配置列表（自动初始化）
        configs = await ModelConfigService.get_model_configs(db)

        # 内部逻辑：使用统一的响应构建工具类转换为脱敏响应
        config_responses = [
            ModelConfigResponseSafe(**ConfigResponseBuilderUtils.build_from_model_config(
                c, ModelConfigService.mask_api_key
            ))
            for c in configs
        ]

        return SuccessResponse(
            data={
                "configs": config_responses
            }
        )
    except Exception as e:
        logger.error(f"获取LLM配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.post("/llm", response_model=SuccessResponse[ModelConfigResponseSafe])
async def save_llm_config(
    config_data: ModelConfigCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    函数级注释：保存或更新LLM模型配置
    内部逻辑：验证数据 -> status=1时取消其他配置启用状态 -> 保存到数据库 -> 返回脱敏配置对象
    参数：
        config_data: 配置数据
        db: 数据库异步会话
    返回值：保存后的配置响应（API密钥已脱敏）
    """
    try:
        # 内部逻辑：如果保存的配置status=1，先取消其他配置的启用状态
        # 这样可以确保同一时间只有一个配置处于启用状态
        if config_data.status == 1:
            from sqlalchemy import update
            config_id = config_data.id or ""
            await db.execute(
                update(ModelConfig)
                .where(
                    (ModelConfig.provider_id == config_data.provider_id) &
                    (ModelConfig.id != config_id)  # 排除当前配置（如果是更新）
                )
                .values(status=0)
            )
            await db.commit()

        # 内部逻辑：保存配置
        config = await ModelConfigService.save_model_config(db, config_data.model_dump())

        # 内部逻辑：使用统一的响应构建工具类构造脱敏响应
        config_response = ModelConfigResponseSafe(
            **ConfigResponseBuilderUtils.build_from_model_config(
                config, ModelConfigService.mask_api_key
            )
        )

        return SuccessResponse(
            data=config_response,
            message="配置已保存"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"保存LLM配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")


@router.post("/llm/{config_id}/set-default", response_model=SuccessResponse[ModelConfigResponseSafe])
async def set_default_llm_config(
    config_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    函数级注释：启用LLM模型（触发热切换）
    内部逻辑：取消其他启用状态 -> 设置新配置为启用 -> 触发热重载 -> 返回脱敏配置对象
    参数：
        config_id: 配置ID
        db: 数据库异步会话
    返回值：更新后的配置响应（API密钥已脱敏）
    """
    try:
        config = await ModelConfigService.set_default_config(db, config_id)

        # 内部逻辑：使用统一的响应构建工具类构造脱敏响应
        config_response = ModelConfigResponseSafe(
            **ConfigResponseBuilderUtils.build_from_model_config(
                config, ModelConfigService.mask_api_key
            )
        )

        return SuccessResponse(
            data=config_response,
            message="配置已启用并生效"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"启用LLM配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"设置失败: {str(e)}")


@router.delete("/llm/{config_id}", response_model=SuccessResponse[dict])
async def delete_llm_config(
    config_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    函数级注释：删除LLM模型配置
    内部逻辑：验证非默认配置 -> 删除配置 -> 返回成功
    参数：
        config_id: 配置ID
        db: 数据库异步会话
    返回值：删除成功响应
    """
    try:
        success = await ModelConfigService.delete_config(db, config_id)
        if not success:
            raise HTTPException(status_code=404, detail="配置不存在")
        return SuccessResponse(data={"deleted": True}, message="配置已删除")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除LLM配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.put("/llm/{config_id}/api-key",
            response_model=SuccessResponse[APIKeyUpdateResponse],
            summary="更新LLM配置的API密钥")
async def update_llm_api_key(
    config_id: str,
    key_data: APIKeyUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    函数级注释：更新指定LLM配置的API密钥
    内部逻辑：
        1. 验证配置存在
        2. 更新API密钥
        3. 如果配置处于启用状态则触发热重载
        4. 返回脱敏结果
    参数：
        config_id: 配置ID
        key_data: 包含新API密钥的请求体
        db: 数据库异步会话
    返回值：脱敏后的密钥
    """
    try:
        config = await ModelConfigService.update_api_key(db, config_id, key_data.api_key)
        return SuccessResponse(
            data=APIKeyUpdateResponse(
                api_key_masked=ModelConfigService.mask_api_key(config.api_key),
                message="API密钥已更新"
            ),
            message="API密钥已更新"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新LLM API密钥失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.get("/embedding", response_model=SuccessResponse[dict])
async def get_embedding_configs(db: AsyncSession = Depends(get_db)):
    """
    函数级注释：获取所有Embedding配置
    内部逻辑：查询配置 -> 为空则初始化 -> 转换为脱敏响应 -> 返回配置列表
    参数：
        db: 数据库异步会话
    返回值：配置列表响应（status=1的配置为正在使用，API密钥已脱敏）
    """
    try:
        configs = await EmbeddingConfigService.get_embedding_configs(db)

        # 内部逻辑：使用统一的响应构建工具类转换为脱敏响应
        config_responses = [
            EmbeddingConfigResponseSafe(**ConfigResponseBuilderUtils.build_from_model_config(
                c, EmbeddingConfigService.mask_api_key
            ))
            for c in configs
        ]

        return SuccessResponse(
            data={
                "configs": config_responses
            }
        )
    except Exception as e:
        logger.error(f"获取Embedding配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.post("/embedding", response_model=SuccessResponse[EmbeddingConfigResponseSafe])
async def save_embedding_config(
    config_data: EmbeddingConfigCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    函数级注释：保存或更新Embedding配置
    参数：
        config_data: 配置数据
        db: 数据库异步会话
    返回值：保存后的配置响应（API密钥已脱敏）
    """
    try:
        config = await EmbeddingConfigService.save_embedding_config(db, config_data.model_dump())

        # 内部逻辑：使用统一的响应构建工具类构造脱敏响应
        config_response = EmbeddingConfigResponseSafe(
            **ConfigResponseBuilderUtils.build_from_model_config(
                config, EmbeddingConfigService.mask_api_key
            )
        )

        return SuccessResponse(
            data=config_response,
            message="配置已保存"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"保存Embedding配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")


@router.post("/embedding/{config_id}/set-default", response_model=SuccessResponse[EmbeddingConfigResponseSafe])
async def set_default_embedding_config(
    config_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    函数级注释：启用Embedding（触发热切换）
    参数：
        config_id: 配置ID
        db: 数据库异步会话
    返回值：更新后的配置响应（API密钥已脱敏）
    """
    try:
        config = await EmbeddingConfigService.set_default_config(db, config_id)

        # 内部逻辑：使用统一的响应构建工具类构造脱敏响应
        config_response = EmbeddingConfigResponseSafe(
            **ConfigResponseBuilderUtils.build_from_model_config(
                config, EmbeddingConfigService.mask_api_key
            )
        )

        return SuccessResponse(
            data=config_response,
            message="Embedding配置已启用并生效"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"启用Embedding配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"设置失败: {str(e)}")


@router.get("/providers", response_model=SuccessResponse[ProvidersResponse])
async def get_providers():
    """
    函数级注释：获取支持的提供商列表
    返回值：提供商列表响应
    """
    # 内部逻辑：转换为ProviderInfo模型
    llm_providers = [
        {
            "value": p["id"],
            "label": p["name"],
            "default_endpoint": p["default_endpoint"],
            "default_models": p["default_models"],
            "type": p["type"]
        }
        for p in LLM_PROVIDERS
    ]

    embedding_providers = [
        {
            "value": p["id"],
            "label": p["name"],
            "default_endpoint": p.get("default_endpoint", ""),
            "default_models": p["default_models"],
            "type": p["type"]
        }
        for p in EMBEDDING_PROVIDERS
    ]

    return SuccessResponse(
        data=ProvidersResponse(
            llm_providers=llm_providers,
            embedding_providers=embedding_providers
        )
    )


@router.get("/ollama/models", response_model=SuccessResponse[OllamaModelsResponse])
async def get_ollama_models(db: AsyncSession = Depends(get_db)):
    """
    函数级注释：获取Ollama可用模型列表
    内部逻辑：从数据库读取用户配置的endpoint -> 调用Ollama API -> 解析模型列表 -> 返回
    参数：
        db: 数据库异步会话
    返回值：模型列表响应
    """
    # 内部变量：Ollama 服务地址，优先使用用户配置
    ollama_base_url = settings.OLLAMA_BASE_URL

    # 内部逻辑：查询用户配置的 Ollama endpoint
    try:
        result = await db.execute(
            select(ModelConfig).where(
                (ModelConfig.provider_id == "ollama") &
                (ModelConfig.endpoint.isnot(None)) &
                (ModelConfig.endpoint != "")
            ).order_by(ModelConfig.status.desc()).limit(1)
        )
        ollama_config = result.scalar_one_or_none()
        if ollama_config and ollama_config.endpoint:
            ollama_base_url = ollama_config.endpoint
            logger.info(f"使用用户配置的 Ollama endpoint: {ollama_base_url}")
    except Exception as e:
        logger.warning(f"查询 Ollama 配置失败，使用默认值: {str(e)}")

    # 内部逻辑：规范化 endpoint，移除末尾的 /api 或 /，确保正确拼接 API 路径
    # Ollama API 格式：http://host:port/api/tags，所以 base 应该是 http://host:port
    ollama_base_url = ollama_base_url.rstrip('/').rstrip('/api')

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 内部逻辑：处理 endpoint 路径，确保格式正确
            api_url = f"{ollama_base_url.rstrip('/')}/api/tags"
            response = await client.get(api_url)
            response.raise_for_status()
            data = response.json()

            # 内部逻辑：转换为模型信息
            models = [
                {
                    "name": m["name"],
                    "size": m.get("size", 0),
                    "modified_at": m.get("modified_at", "")
                }
                for m in data.get("models", [])
            ]

            return SuccessResponse(
                data=OllamaModelsResponse(models=models)
            )
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail=f"无法连接Ollama服务 ({ollama_base_url})，请检查Ollama是否运行")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=503, detail=f"Ollama服务返回错误: {e.response.status_code}")
    except Exception as e:
        logger.error(f"获取Ollama模型列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")


@router.post("/ollama/pull", response_model=SuccessResponse[dict])
async def pull_ollama_model(model_name: str, db: AsyncSession = Depends(get_db)):
    """
    函数级注释：拉取Ollama模型
    内部逻辑：从数据库读取用户配置的endpoint -> 调用Ollama API -> 异步拉取模型 -> 返回结果
    参数：
        model_name: 模型名称（如 llama3:8b）
        db: 数据库异步会话
    返回值：拉取结果响应
    """
    # 内部变量：Ollama 服务地址，优先使用用户配置
    ollama_base_url = settings.OLLAMA_BASE_URL

    # 内部逻辑：查询用户配置的 Ollama endpoint
    try:
        result = await db.execute(
            select(ModelConfig).where(
                (ModelConfig.provider_id == "ollama") &
                (ModelConfig.endpoint.isnot(None)) &
                (ModelConfig.endpoint != "")
            ).order_by(ModelConfig.status.desc()).limit(1)
        )
        ollama_config = result.scalar_one_or_none()
        if ollama_config and ollama_config.endpoint:
            ollama_base_url = ollama_config.endpoint
            logger.info(f"使用用户配置的 Ollama endpoint: {ollama_base_url}")
    except Exception as e:
        logger.warning(f"查询 Ollama 配置失败，使用默认值: {str(e)}")

    # 内部逻辑：规范化 endpoint，移除末尾的 /api 或 /，确保正确拼接 API 路径
    # Ollama API 格式：http://host:port/api/tags，所以 base 应该是 http://host:port
    ollama_base_url = ollama_base_url.rstrip('/').rstrip('/api')

    try:
        async with httpx.AsyncClient(timeout=600.0) as client:
            # 内部逻辑：处理 endpoint 路径，确保格式正确
            api_url = f"{ollama_base_url.rstrip('/')}/api/pull"
            response = await client.post(
                api_url,
                json={"name": model_name, "stream": False}
            )
            response.raise_for_status()

            return SuccessResponse(
                data={"model_name": model_name},
                message=f"模型 {model_name} 拉取成功"
            )
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail=f"无法连接Ollama服务 ({ollama_base_url})")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=f"拉取模型失败: {e.response.status_code}")
    except Exception as e:
        logger.error(f"拉取Ollama模型失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"拉取模型失败: {str(e)}")


@router.post("/validate", response_model=SuccessResponse[dict])
async def validate_config(config: ModelConfigCreate):
    """
    函数级注释：验证配置有效性
    内部逻辑：检查必填字段 -> 验证提供商特定要求 -> 返回验证结果
    参数：
        config: 待验证的配置
    返回值：验证结果响应
    """
    # 内部逻辑：验证云端API提供商需要API密钥
    cloud_providers = ["zhipuai", "openai", "minimax", "moonshot", "deepseek"]
    if config.provider_id in cloud_providers and not config.api_key:
        return SuccessResponse(
            data={"valid": False, "field": "api_key"},
            message=f"{config.provider_name}需要配置API密钥"
        )

    # 内部逻辑：验证本地Embedding需要检查torch可用性
    if config.provider_id == "local":
        try:
            import torch
        except ImportError:
            return SuccessResponse(
                data={"valid": False, "field": "provider_id"},
                message="本地Embedding需要安装torch依赖"
            )

    return SuccessResponse(
        data={"valid": True},
        message="配置验证通过"
    )


@router.delete("/embedding/{config_id}", response_model=SuccessResponse[dict])
async def delete_embedding_config(
    config_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    函数级注释：删除Embedding模型配置
    内部逻辑：验证非默认配置 -> 删除配置 -> 返回成功
    参数：
        config_id: 配置ID
        db: 数据库异步会话
    返回值：删除成功响应
    """
    try:
        success = await EmbeddingConfigService.delete_config(db, config_id)
        if not success:
            raise HTTPException(status_code=404, detail="配置不存在")
        return SuccessResponse(data={"deleted": True}, message="配置已删除")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除Embedding配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.put("/embedding/{config_id}/api-key",
            response_model=SuccessResponse[APIKeyUpdateResponse],
            summary="更新Embedding配置的API密钥")
async def update_embedding_api_key(
    config_id: str,
    key_data: APIKeyUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    函数级注释：更新指定Embedding配置的API密钥
    内部逻辑：
        1. 验证配置存在
        2. 更新API密钥
        3. 如果配置处于启用状态则触发热重载
        4. 返回脱敏结果
    参数：
        config_id: 配置ID
        key_data: 包含新API密钥的请求体
        db: 数据库异步会话
    返回值：脱敏后的密钥
    """
    try:
        config = await EmbeddingConfigService.update_api_key(db, config_id, key_data.api_key)
        return SuccessResponse(
            data=APIKeyUpdateResponse(
                api_key_masked=EmbeddingConfigService.mask_api_key(config.api_key),
                message="API密钥已更新"
            ),
            message="API密钥已更新"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新Embedding API密钥失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.post("/llm/test", response_model=SuccessResponse[ConnectionTestResponse])
async def test_llm_connection(
    request: ConnectionTestRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    函数级注释：测试LLM配置连接
    内部逻辑：
        1. 如果提供了 config_id，从数据库获取真实密钥
        2. 否则使用请求中的 api_key
        3. 调用测试服务 -> 验证连接 -> 返回测试结果
    参数：
        request: 连接测试请求
        db: 数据库异步会话
    返回值：测试结果响应
    """
    try:
        # 内部变量：实际使用的API密钥
        api_key_to_use = request.api_key

        # 内部逻辑：如果提供了 config_id，从数据库获取真实密钥
        if request.config_id:
            from sqlalchemy import select
            result = await db.execute(
                select(ModelConfig).where(ModelConfig.id == request.config_id)
            )
            config = result.scalar_one_or_none()
            if config:
                api_key_to_use = config.api_key
            else:
                raise HTTPException(status_code=404, detail=f"配置不存在: {request.config_id}")

        result = await ConnectionTestService.test_llm_connection(
            provider_id=request.provider_id,
            endpoint=request.endpoint,
            api_key=api_key_to_use,
            model_name=request.model_name
        )

        response_data = ConnectionTestResponse(
            success=result["success"],
            provider_id=result["provider_id"],
            latency_ms=result.get("latency_ms", 0),
            message=result.get("message", "测试失败" if not result["success"] else ""),
            error=result.get("error"),
            models=result.get("models", [])
        )

        return SuccessResponse(
            data=response_data,
            message="测试完成"
        )
    except Exception as e:
        logger.error(f"测试LLM连接异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"测试失败: {str(e)}")


@router.post("/embedding/test", response_model=SuccessResponse[EmbeddingConnectionTestResponse])
async def test_embedding_connection(
    request: EmbeddingConnectionTestRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    函数级注释：测试Embedding配置连接
    内部逻辑：
        1. 如果提供了 config_id，从数据库获取真实密钥
        2. 否则使用请求中的 api_key
        3. 调用测试服务 -> 验证连接 -> 返回测试结果
    参数：
        request: 连接测试请求
        db: 数据库异步会话
    返回值：测试结果响应
    """
    try:
        # 内部变量：实际使用的API密钥
        api_key_to_use = request.api_key

        # 内部逻辑：如果提供了 config_id，从数据库获取真实密钥
        if request.config_id:
            from app.models.model_config import EmbeddingConfig
            from sqlalchemy import select
            result = await db.execute(
                select(EmbeddingConfig).where(EmbeddingConfig.id == request.config_id)
            )
            config = result.scalar_one_or_none()
            if config:
                api_key_to_use = config.api_key
            else:
                raise HTTPException(status_code=404, detail=f"配置不存在: {request.config_id}")

        result = await ConnectionTestService.test_embedding_connection(
            provider_id=request.provider_id,
            endpoint=request.endpoint,
            api_key=api_key_to_use,
            model_name=request.model_name,
            device=request.device
        )

        response_data = EmbeddingConnectionTestResponse(
            success=result["success"],
            provider_id=result["provider_id"],
            latency_ms=result.get("latency_ms", 0),
            message=result.get("message", "测试失败" if not result["success"] else ""),
            error=result.get("error"),
            models=result.get("models", [])
        )

        return SuccessResponse(
            data=response_data,
            message="测试完成"
        )
    except Exception as e:
        logger.error(f"测试Embedding连接异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"测试失败: {str(e)}")


@router.get("/local/models", response_model=SuccessResponse[LocalModelsResponse])
async def get_local_models():
    """
    函数级注释：获取本地Embedding模型列表
    内部逻辑：扫描本地模型目录 -> 识别有效模型 -> 返回模型列表
    返回值：本地模型列表响应
    """
    try:
        # 内部逻辑：调用本地模型服务扫描模型目录
        result = LocalModelService.scan_local_models()

        return SuccessResponse(
            data=LocalModelsResponse(
                models=result.get("models", []),
                base_dir=result.get("base_dir", "")
            ),
            message=f"扫描完成，发现 {len(result.get('models', []))} 个本地模型"
        )
    except Exception as e:
        logger.error(f"扫描本地模型失败: {str(e)}")
        # 内部逻辑：即使出错也返回空列表，保证前端正常展示
        return SuccessResponse(
            data=LocalModelsResponse(
                models=[],
                base_dir=settings.LOCAL_MODEL_DIR
            ),
            message="扫描失败"
        )
