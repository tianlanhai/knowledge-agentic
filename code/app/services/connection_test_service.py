# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：模型连接测试服务
内部逻辑：提供LLM和Embedding配置的连接验证功能
设计模式：策略模式（根据提供商类型选择测试策略）
"""

import time
import httpx
from typing import Dict, Any
from loguru import logger


class ConnectionTestService:
    """
    类级注释：连接测试服务类
    设计模式：策略模式（根据提供商类型选择测试策略）
    """

    # 内部常量：云端API提供商列表
    CLOUD_PROVIDERS = ["zhipuai", "openai", "minimax", "moonshot", "deepseek"]

    @staticmethod
    async def test_llm_connection(
        provider_id: str,
        endpoint: str,
        api_key: str,
        model_name: str = ""
    ) -> Dict[str, Any]:
        """
        函数级注释：测试LLM模型连接
        内部逻辑：根据提供商类型执行对应的测试策略
        参数：
            provider_id: 提供商ID
            endpoint: API端点地址
            api_key: API密钥
            model_name: 模型名称
        返回值：测试结果字典
        """
        # 内部变量：记录开始时间
        start_time = time.time()

        try:
            # 内部逻辑：根据提供商类型分发测试
            if provider_id == "ollama":
                result = await ConnectionTestService._test_ollama(endpoint)
            elif provider_id in ConnectionTestService.CLOUD_PROVIDERS:
                result = await ConnectionTestService._test_cloud_api(
                    provider_id, endpoint, api_key
                )
            else:
                result = {
                    "success": False,
                    "error": f"不支持的提供商: {provider_id}"
                }

            # 内部逻辑：计算延迟
            latency_ms = round((time.time() - start_time) * 1000, 2)
            result["latency_ms"] = latency_ms
            result["provider_id"] = provider_id

            return result

        except httpx.ConnectError as e:
            # 内部逻辑：处理连接错误
            logger.error(f"测试LLM连接失败 ({provider_id}): 连接错误 {str(e)}")
            return {
                "success": False,
                "provider_id": provider_id,
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "error": "无法连接到服务，请检查端点地址"
            }
        except httpx.HTTPStatusError as e:
            # 内部逻辑：处理HTTP状态错误
            logger.error(f"测试LLM连接失败 ({provider_id}): HTTP状态错误 {e.response.status_code}")
            if e.response.status_code == 401:
                return {
                    "success": False,
                    "provider_id": provider_id,
                    "latency_ms": round((time.time() - start_time) * 1000, 2),
                    "error": "API密钥无效或权限不足"
                }
            return {
                "success": False,
                "provider_id": provider_id,
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "error": f"HTTP错误: {e.response.status_code}"
            }
        except httpx.TimeoutException:
            # 内部逻辑：处理超时错误
            logger.error(f"测试LLM连接失败 ({provider_id}): 连接超时")
            return {
                "success": False,
                "provider_id": provider_id,
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "error": "连接超时，请检查网络或稍后重试"
            }
        except Exception as e:
            # 内部逻辑：处理其他异常
            logger.error(f"测试LLM连接失败 ({provider_id}): {str(e)}")
            return {
                "success": False,
                "provider_id": provider_id,
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "error": str(e)
            }

    @staticmethod
    async def test_embedding_connection(
        provider_id: str,
        endpoint: str,
        api_key: str,
        model_name: str = "",
        device: str = "cpu"
    ) -> Dict[str, Any]:
        """
        函数级注释：测试Embedding模型连接
        内部逻辑：根据提供商类型执行对应的测试策略
        参数：
            provider_id: 提供商ID
            endpoint: API端点地址
            api_key: API密钥
            model_name: 模型名称
            device: 运行设备
        返回值：测试结果字典
        """
        # 内部变量：记录开始时间
        start_time = time.time()

        try:
            # 内部逻辑：根据提供商类型分发测试
            if provider_id == "local":
                result = await ConnectionTestService._test_local_embedding(device)
            elif provider_id == "ollama":
                result = await ConnectionTestService._test_ollama(endpoint)
            elif provider_id in ConnectionTestService.CLOUD_PROVIDERS:
                result = await ConnectionTestService._test_cloud_api(
                    provider_id, endpoint, api_key
                )
            else:
                result = {
                    "success": False,
                    "error": f"不支持的提供商: {provider_id}"
                }

            # 内部逻辑：计算延迟
            latency_ms = round((time.time() - start_time) * 1000, 2)
            result["latency_ms"] = latency_ms
            result["provider_id"] = provider_id

            return result

        except httpx.ConnectError as e:
            # 内部逻辑：处理连接错误
            logger.error(f"测试Embedding连接失败 ({provider_id}): 连接错误 {str(e)}")
            return {
                "success": False,
                "provider_id": provider_id,
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "error": "无法连接到服务，请检查端点地址"
            }
        except httpx.HTTPStatusError as e:
            # 内部逻辑：处理HTTP状态错误
            logger.error(f"测试Embedding连接失败 ({provider_id}): HTTP状态错误 {e.response.status_code}")
            if e.response.status_code == 401:
                return {
                    "success": False,
                    "provider_id": provider_id,
                    "latency_ms": round((time.time() - start_time) * 1000, 2),
                    "error": "API密钥无效或权限不足"
                }
            return {
                "success": False,
                "provider_id": provider_id,
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "error": f"HTTP错误: {e.response.status_code}"
            }
        except httpx.TimeoutException:
            # 内部逻辑：处理超时错误
            logger.error(f"测试Embedding连接失败 ({provider_id}): 连接超时")
            return {
                "success": False,
                "provider_id": provider_id,
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "error": "连接超时，请检查网络或稍后重试"
            }
        except Exception as e:
            # 内部逻辑：处理其他异常
            logger.error(f"测试Embedding连接失败 ({provider_id}): {str(e)}")
            return {
                "success": False,
                "provider_id": provider_id,
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "error": str(e)
            }

    @staticmethod
    async def _test_ollama(endpoint: str) -> Dict[str, Any]:
        """
        函数级注释：测试Ollama服务连接
        内部逻辑：调用Ollama的 /api/tags 接口验证服务可用性
        参数：
            endpoint: Ollama服务端点
        返回值：测试结果字典
        """
        # 内部逻辑：规范化endpoint，移除末尾的 /api 或 /
        # Ollama API 格式：http://host:port/api/tags，所以 base 应该是 http://host:port
        base_url = endpoint.rstrip('/').rstrip('/api')

        async with httpx.AsyncClient(timeout=10.0) as client:
            # 内部逻辑：处理 endpoint 路径，确保格式正确
            api_url = f"{base_url.rstrip('/')}/api/tags"
            response = await client.get(api_url)
            response.raise_for_status()

            # 内部逻辑：解析响应数据
            data = response.json()
            models_data = data.get("models", [])
            model_count = len(models_data)

            # 内部逻辑：提取模型名称列表
            model_names = [m.get("name", "") for m in models_data if m.get("name")]

            return {
                "success": True,
                "message": f"连接成功，检测到 {model_count} 个模型",
                "models": model_names
            }

    @staticmethod
    async def _test_cloud_api(
        provider_id: str,
        endpoint: str,
        api_key: str
    ) -> Dict[str, Any]:
        """
        函数级注释：测试云端API连接
        内部逻辑：调用提供商的 /models 接口验证API密钥和服务可用性
        参数：
            provider_id: 提供商ID
            endpoint: API端点地址
            api_key: API密钥
        返回值：测试结果字典
        """
        # 内部逻辑：Guard Clauses - 验证API密钥
        if not api_key:
            return {
                "success": False,
                "error": f"{provider_id} 需要配置API密钥"
            }

        # 内部逻辑：规范化endpoint
        url = endpoint.rstrip('/') + '/models'

        # 内部变量：请求头
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)

            # 内部逻辑：验证响应状态码
            if response.status_code == 401:
                return {
                    "success": False,
                    "error": "API密钥无效"
                }

            response.raise_for_status()

            # 内部逻辑：解析响应，获取可用模型列表
            data = response.json()
            model_list = []
            model_count = 0

            if "data" in data and isinstance(data["data"], list):
                model_list = [m.get("id", m.get("name", "")) for m in data["data"] if m.get("id") or m.get("name")]
                model_count = len(model_list)

            return {
                "success": True,
                "message": f"连接成功，检测到 {model_count} 个可用模型",
                "models": model_list
            }

    @staticmethod
    async def _test_local_embedding(device: str) -> Dict[str, Any]:
        """
        函数级注释：测试本地Embedding环境
        内部逻辑：验证torch和依赖是否可用
        参数：
            device: 运行设备
        返回值：测试结果字典
        """
        try:
            import torch
        except ImportError:
            return {
                "success": False,
                "error": "本地Embedding需要安装torch依赖"
            }

        # 内部逻辑：验证CUDA可用性（如果指定）
        if device == "cuda":
            if not torch.cuda.is_available():
                return {
                    "success": False,
                    "error": "CUDA不可用，请检查GPU驱动或选择CPU模式"
                }

        return {
            "success": True,
            "message": f"本地环境检测通过 (设备: {device})"
        }
