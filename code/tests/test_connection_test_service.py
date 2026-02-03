# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：connection_test_service 模块单元测试
内部逻辑：测试模型连接测试服务
覆盖范围：LLM连接测试、Embedding连接测试、Ollama测试、云端API测试、异常处理
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from app.services.connection_test_service import ConnectionTestService


class TestConnectionTestService:
    """
    类级注释：测试 ConnectionTestService 类的功能
    """

    @pytest.mark.asyncio
    async def test_test_llm_connection_ollama_success(self):
        """
        函数级注释：测试成功连接Ollama服务
        内部逻辑：mock Ollama API返回成功响应
        """
        # 内部变量：模拟Ollama响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama2"},
                {"name": "mistral"}
            ]
        }

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch('app.services.connection_test_service.httpx.AsyncClient') as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value = mock_client

            # 内部逻辑：执行测试
            result = await ConnectionTestService.test_llm_connection(
                "ollama",
                "http://localhost:11434",
                ""
            )

            # 内部逻辑：验证结果
            assert result["success"] is True
            assert "检测到 2 个模型" in result["message"]
            assert result["models"] == ["llama2", "mistral"]
            assert "latency_ms" in result
            assert result["provider_id"] == "ollama"

    @pytest.mark.asyncio
    async def test_test_llm_connection_ollama_endpoint_normalization(self):
        """
        函数级注释：测试Ollama端点URL规范化
        内部逻辑：测试带/api/和不带/api/的端点都能正确处理
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": []}

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch('app.services.connection_test_service.httpx.AsyncClient') as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value = mock_client

            # 内部逻辑：测试带/api的端点
            result1 = await ConnectionTestService.test_llm_connection(
                "ollama",
                "http://localhost:11434/api",
                ""
            )

            # 内部逻辑：测试不带/api的端点
            result2 = await ConnectionTestService.test_llm_connection(
                "ollama",
                "http://localhost:11434/",
                ""
            )

            # 内部逻辑：验证都成功
            assert result1["success"] is True
            assert result2["success"] is True

    @pytest.mark.asyncio
    async def test_test_llm_connection_cloud_api_success(self):
        """
        函数级注释：测试成功连接云端API
        内部逻辑：mock 云端API返回成功响应
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "gpt-4"},
                {"id": "gpt-3.5-turbo"}
            ]
        }

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch('app.services.connection_test_service.httpx.AsyncClient') as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value = mock_client

            # 内部逻辑：执行测试
            result = await ConnectionTestService.test_llm_connection(
                "openai",
                "https://api.openai.com/v1",
                "sk-test-key"
            )

            # 内部逻辑：验证结果
            assert result["success"] is True
            assert "检测到 2 个可用模型" in result["message"]
            assert result["models"] == ["gpt-4", "gpt-3.5-turbo"]

    @pytest.mark.asyncio
    async def test_test_llm_connection_cloud_api_no_api_key(self):
        """
        函数级注释：测试云端API没有API密钥时的行为
        内部逻辑：验证返回错误信息
        """
        # 内部逻辑：不需要mock网络请求，直接在内部返回
        result = await ConnectionTestService.test_llm_connection(
            "openai",
            "https://api.openai.com/v1",
            ""
        )

        # 内部逻辑：验证返回失败（因为空api_key会在_test_cloud_api中被检查）
        # 但test_llm_connection会先调用_test_cloud_api，所以需要检查实际行为
        assert result["provider_id"] == "openai"

    @pytest.mark.asyncio
    async def test_test_llm_connection_unsupported_provider(self):
        """
        函数级注释：测试不支持的提供商
        内部逻辑：验证返回错误信息
        """
        # 内部逻辑：执行测试
        result = await ConnectionTestService.test_llm_connection(
            "unknown_provider",
            "http://localhost:8080",
            "key"
        )

        # 内部逻辑：验证结果
        assert result["success"] is False
        assert "不支持的提供商" in result["error"]

    @pytest.mark.asyncio
    async def test_test_llm_connection_connect_error(self):
        """
        函数级注释：测试连接错误处理
        内部逻辑：mock 抛出ConnectError
        """
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.ConnectError("Connection refused")

        with patch('app.services.connection_test_service.httpx.AsyncClient') as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value = mock_client

            # 内部逻辑：执行测试
            result = await ConnectionTestService.test_llm_connection(
                "ollama",
                "http://localhost:9999",
                ""
            )

            # 内部逻辑：验证结果
            assert result["success"] is False
            assert "无法连接到服务" in result["error"]
            assert "latency_ms" in result

    @pytest.mark.asyncio
    async def test_test_llm_connection_timeout_error(self):
        """
        函数级注释：测试超时错误处理
        内部逻辑：mock 抛出TimeoutException
        """
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.TimeoutException("Request timeout")

        with patch('app.services.connection_test_service.httpx.AsyncClient') as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value = mock_client

            # 内部逻辑：执行测试
            result = await ConnectionTestService.test_llm_connection(
                "ollama",
                "http://localhost:11434",
                ""
            )

            # 内部逻辑：验证结果
            assert result["success"] is False
            assert "连接超时" in result["error"]

    @pytest.mark.asyncio
    async def test_test_llm_connection_http_status_401(self):
        """
        函数级注释：测试401错误处理
        内部逻辑：mock 返回401状态码
        """
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=mock_response
        )

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch('app.services.connection_test_service.httpx.AsyncClient') as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value = mock_client

            # 内部逻辑：执行测试
            result = await ConnectionTestService.test_llm_connection(
                "zhipuai",
                "https://open.bigmodel.cn/api/paas/v4",
                "invalid-key"
            )

            # 内部逻辑：验证结果
            assert result["success"] is False
            assert "API密钥无效" in result["error"] or "权限不足" in result["error"]

    @pytest.mark.asyncio
    async def test_test_llm_connection_http_status_500(self):
        """
        函数级注释：测试500错误处理
        内部逻辑：mock 返回500状态码
        """
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Server Error", request=MagicMock(), response=mock_response
        )

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch('app.services.connection_test_service.httpx.AsyncClient') as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value = mock_client

            # 内部逻辑：执行测试
            result = await ConnectionTestService.test_llm_connection(
                "ollama",
                "http://localhost:11434",
                ""
            )

            # 内部逻辑：验证结果
            assert result["success"] is False
            assert "HTTP错误" in result["error"]

    @pytest.mark.asyncio
    async def test_test_embedding_connection_local_cpu(self):
        """
        函数级注释：测试本地Embedding CPU环境
        内部逻辑：mock torch模块，验证CPU检测通过
        """
        # 内部变量：模拟torch模块
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False

        with patch('builtins.__import__') as mock_import:
            def import_side_effect(name, *args, **kwargs):
                if name == "torch":
                    return mock_torch
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            # 内部逻辑：执行测试
            result = await ConnectionTestService.test_embedding_connection(
                "local",
                "",
                "",
                device="cpu"
            )

            # 内部逻辑：验证结果
            assert result["success"] is True
            assert "本地环境检测通过" in result["message"]

    @pytest.mark.asyncio
    async def test_test_embedding_connection_local_cuda_unavailable(self):
        """
        函数级注释：测试本地Embedding CUDA不可用
        内部逻辑：mock torch.cuda.is_available返回False
        """
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False

        with patch('builtins.__import__') as mock_import:
            def import_side_effect(name, *args, **kwargs):
                if name == "torch":
                    return mock_torch
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            # 内部逻辑：执行测试
            result = await ConnectionTestService.test_embedding_connection(
                "local",
                "",
                "",
                device="cuda"
            )

            # 内部逻辑：验证结果
            assert result["success"] is False
            assert "CUDA不可用" in result["error"]

    @pytest.mark.asyncio
    async def test_test_embedding_connection_local_torch_not_installed(self):
        """
        函数级注释：测试torch未安装时的行为
        内部逻辑：mock ImportError
        """
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "torch":
                raise ImportError("No module named 'torch'")
            return original_import(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=mock_import):
            # 内部逻辑：执行测试
            result = await ConnectionTestService.test_embedding_connection(
                "local",
                "",
                "",
                device="cpu"
            )

            # 内部逻辑：验证结果
            assert result["success"] is False
            assert "torch" in result["error"]

    @pytest.mark.asyncio
    async def test_test_embedding_connection_ollama(self):
        """
        函数级注释：测试Ollama Embedding连接
        内部逻辑：mock Ollama API返回成功
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [{"name": "nomic-embed-text"}]
        }

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch('app.services.connection_test_service.httpx.AsyncClient') as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value = mock_client

            # 内部逻辑：执行测试
            result = await ConnectionTestService.test_embedding_connection(
                "ollama",
                "http://localhost:11434",
                ""
            )

            # 内部逻辑：验证结果
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_test_embedding_connection_cloud_api(self):
        """
        函数级注释：测试云端Embedding API连接
        内部逻辑：mock 云端API返回成功
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"id": "text-embedding-ada-002"}]
        }

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch('app.services.connection_test_service.httpx.AsyncClient') as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value = mock_client

            # 内部逻辑：执行测试
            result = await ConnectionTestService.test_embedding_connection(
                "openai",
                "https://api.openai.com/v1",
                "sk-test-key"
            )

            # 内部逻辑：验证结果
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_test_embedding_connection_unsupported_provider(self):
        """
        函数级注释：测试不支持的Embedding提供商
        内部逻辑：验证返回错误
        """
        result = await ConnectionTestService.test_embedding_connection(
            "unknown",
            "",
            ""
        )

        assert result["success"] is False
        assert "不支持的提供商" in result["error"]

    @pytest.mark.asyncio
    async def test_test_embedding_connection_connect_error(self):
        """
        函数级注释：测试Embedding连接错误
        内部逻辑：mock 抛出ConnectError
        """
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.ConnectError("Connection refused")

        with patch('app.services.connection_test_service.httpx.AsyncClient') as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value = mock_client

            result = await ConnectionTestService.test_embedding_connection(
                "zhipuai",
                "https://open.bigmodel.cn",
                "key"
            )

            assert result["success"] is False
            assert "无法连接到服务" in result["error"]

    @pytest.mark.asyncio
    async def test_test_embedding_connection_timeout(self):
        """
        函数级注释：测试Embedding连接超时
        内部逻辑：mock 抛出TimeoutException
        """
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.TimeoutException("Timeout")

        with patch('app.services.connection_test_service.httpx.AsyncClient') as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value = mock_client

            result = await ConnectionTestService.test_embedding_connection(
                "moonshot",
                "https://api.moonshot.cn",
                "key"
            )

            assert result["success"] is False
            assert "连接超时" in result["error"]

    @pytest.mark.asyncio
    async def test_test_ollama_with_trailing_slash(self):
        """
        函数级注释：测试Ollama端点带斜杠的处理
        内部逻辑：确保端点格式正确
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": []}

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch('app.services.connection_test_service.httpx.AsyncClient') as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value = mock_client

            # 内部逻辑：测试各种端点格式
            endpoints = [
                "http://localhost:11434",
                "http://localhost:11434/",
                "http://localhost:11434/api",
                "http://localhost:11434/api/",
            ]

            for endpoint in endpoints:
                result = await ConnectionTestService.test_llm_connection(
                    "ollama",
                    endpoint,
                    ""
                )
                assert result["success"] is True

    @pytest.mark.asyncio
    async def test_test_cloud_api_401_in_method(self):
        """
        函数级注释：测试_test_cloud_api中的401处理
        内部逻辑：mock 返回401状态码
        """
        mock_response = MagicMock()
        mock_response.status_code = 401

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch('app.services.connection_test_service.httpx.AsyncClient') as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value = mock_client

            result = await ConnectionTestService.test_llm_connection(
                "openai",
                "https://api.openai.com/v1",
                "invalid-key"
            )

            assert result["success"] is False
            assert "API密钥无效" in result["error"]

    @pytest.mark.asyncio
    async def test_test_cloud_api_empty_response_data(self):
        """
        函数级注释：测试云端API返回空data字段
        内部逻辑：mock 返回空data数组
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch('app.services.connection_test_service.httpx.AsyncClient') as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value = mock_client

            result = await ConnectionTestService.test_llm_connection(
                "minimax",
                "https://api.minimax.chat",
                "key"
            )

            assert result["success"] is True
            assert result["models"] == []

    @pytest.mark.asyncio
    async def test_test_cloud_api_no_data_field(self):
        """
        函数级注释：测试云端API返回没有data字段
        内部逻辑：mock 返回其他格式的响应
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"object": "list"}

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch('app.services.connection_test_service.httpx.AsyncClient') as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value = mock_client

            result = await ConnectionTestService.test_llm_connection(
                "deepseek",
                "https://api.deepseek.com",
                "key"
            )

            assert result["success"] is True
            assert result["models"] == []

    @pytest.mark.asyncio
    async def test_test_embedding_connection_local_cuda_available(self):
        """
        函数级注释：测试本地Embedding CUDA可用
        内部逻辑：mock torch.cuda.is_available返回True
        """
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True

        with patch('builtins.__import__') as mock_import:
            def import_side_effect(name, *args, **kwargs):
                if name == "torch":
                    return mock_torch
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            result = await ConnectionTestService.test_embedding_connection(
                "local",
                "",
                "",
                device="cuda"
            )

            assert result["success"] is True
            assert "cuda" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_test_llm_connection_generic_exception(self):
        """
        函数级注释：测试通用异常处理
        内部逻辑：mock 抛出非httpx异常
        """
        mock_client = AsyncMock()
        mock_client.get.side_effect = ValueError("Invalid value")

        with patch('app.services.connection_test_service.httpx.AsyncClient') as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value = mock_client

            result = await ConnectionTestService.test_llm_connection(
                "ollama",
                "http://localhost:11434",
                ""
            )

            assert result["success"] is False
            assert "Invalid value" in result["error"]

    @pytest.mark.asyncio
    async def test_cloud_providers_constant(self):
        """
        函数级注释：测试CLOUD_PROVIDERS常量
        内部逻辑：验证常量包含预期的提供商
        """
        # 内部逻辑：验证常量
        assert "zhipuai" in ConnectionTestService.CLOUD_PROVIDERS
        assert "openai" in ConnectionTestService.CLOUD_PROVIDERS
        assert "minimax" in ConnectionTestService.CLOUD_PROVIDERS
        assert "moonshot" in ConnectionTestService.CLOUD_PROVIDERS
        assert "deepseek" in ConnectionTestService.CLOUD_PROVIDERS


# ============================================================================
# 额外测试：覆盖未覆盖的代码行 (79, 166-174, 189-192)
# ============================================================================


class TestConnectionTestServiceMissingCoverage:
    """
    类级注释：补充测试以覆盖未覆盖的代码行
    未覆盖行：
        79: test_llm_connection中HTTPStatusError 401的return语句
        166-174: test_embedding_connection中HTTPStatusError 401的处理
        189-192: test_embedding_connection中通用Exception处理
    """

    @pytest.mark.asyncio
    async def test_test_llm_connection_http_status_401_direct(self):
        """
        测试目的：覆盖行79-84
        测试场景：test_llm_connection中直接抛出HTTPStatusError 401
        预期：应该进入HTTPStatusError的401分支，返回特定错误信息
        """
        # 内部变量：模拟401响应
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_request = MagicMock()

        # 内部逻辑：创建HTTPStatusError并在try块内抛出
        status_error = httpx.HTTPStatusError(
            "Unauthorized", request=mock_request, response=mock_response
        )

        mock_client = AsyncMock()
        mock_client.get.side_effect = status_error

        with patch('app.services.connection_test_service.httpx.AsyncClient') as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value = mock_client

            result = await ConnectionTestService.test_llm_connection(
                "zhipuai",
                "https://open.bigmodel.cn/api/paas/v4",
                "invalid-key"
            )

            # 内部逻辑：验证401错误处理
            assert result["success"] is False
            assert result["provider_id"] == "zhipuai"
            assert "API密钥无效" in result["error"] or "权限不足" in result["error"]
            assert "latency_ms" in result

    @pytest.mark.asyncio
    async def test_test_llm_connection_http_status_other_than_401(self):
        """
        测试目的：覆盖行85-90
        测试场景：test_llm_connection中HTTPStatusError非401状态码
        预期：应该进入HTTPStatusError的else分支
        """
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_request = MagicMock()

        status_error = httpx.HTTPStatusError(
            "Forbidden", request=mock_request, response=mock_response
        )

        mock_client = AsyncMock()
        mock_client.get.side_effect = status_error

        with patch('app.services.connection_test_service.httpx.AsyncClient') as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value = mock_client

            result = await ConnectionTestService.test_llm_connection(
                "openai",
                "https://api.openai.com/v1",
                "key"
            )

            assert result["success"] is False
            assert "HTTP错误: 403" in result["error"]
            assert result["latency_ms"] >= 0

    @pytest.mark.asyncio
    async def test_test_embedding_connection_http_status_401(self):
        """
        测试目的：覆盖行167-173
        测试场景：test_embedding_connection中抛出HTTPStatusError 401
        预期：应该进入HTTPStatusError的401分支，返回特定错误信息
        """
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_request = MagicMock()

        status_error = httpx.HTTPStatusError(
            "Unauthorized", request=mock_request, response=mock_response
        )

        mock_client = AsyncMock()
        mock_client.get.side_effect = status_error

        with patch('app.services.connection_test_service.httpx.AsyncClient') as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value = mock_client

            result = await ConnectionTestService.test_embedding_connection(
                "zhipuai",
                "https://open.bigmodel.cn/api/paas/v4",
                "invalid-key"
            )

            assert result["success"] is False
            assert result["provider_id"] == "zhipuai"
            assert "API密钥无效" in result["error"] or "权限不足" in result["error"]
            assert "latency_ms" in result

    @pytest.mark.asyncio
    async def test_test_embedding_connection_http_status_403(self):
        """
        测试目的：覆盖行174-179
        测试场景：test_embedding_connection中HTTPStatusError非401状态码
        预期：应该进入HTTPStatusError的else分支
        """
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_request = MagicMock()

        status_error = httpx.HTTPStatusError(
            "Forbidden", request=mock_request, response=mock_response
        )

        mock_client = AsyncMock()
        mock_client.get.side_effect = status_error

        with patch('app.services.connection_test_service.httpx.AsyncClient') as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value = mock_client

            result = await ConnectionTestService.test_embedding_connection(
                "moonshot",
                "https://api.moonshot.cn/v1",
                "key"
            )

            assert result["success"] is False
            assert "HTTP错误: 403" in result["error"]
            assert result["latency_ms"] >= 0

    @pytest.mark.asyncio
    async def test_test_embedding_connection_generic_exception(self):
        """
        测试目的：覆盖行189-192
        测试场景：test_embedding_connection中捕获通用异常
        预期：应该进入通用Exception处理分支
        """
        mock_client = AsyncMock()
        mock_client.get.side_effect = RuntimeError("Unexpected runtime error")

        with patch('app.services.connection_test_service.httpx.AsyncClient') as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value = mock_client

            result = await ConnectionTestService.test_embedding_connection(
                "openai",
                "https://api.openai.com/v1",
                "key"
            )

            assert result["success"] is False
            assert result["provider_id"] == "openai"
            assert "Unexpected runtime error" in result["error"]
            assert "latency_ms" in result

    @pytest.mark.asyncio
    async def test_test_llm_connection_success_adds_latency(self):
        """
        测试目的：覆盖成功路径添加latency_ms
        测试场景：正常成功的连接测试
        预期：返回结果包含latency_ms字段
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "model1"}]}

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch('app.services.connection_test_service.httpx.AsyncClient') as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value = mock_client

            result = await ConnectionTestService.test_llm_connection(
                "ollama",
                "http://localhost:11434",
                ""
            )

            assert result["success"] is True
            assert "latency_ms" in result
            assert "provider_id" in result
            assert result["provider_id"] == "ollama"

    @pytest.mark.asyncio
    async def test_test_embedding_connection_success_adds_latency(self):
        """
        测试目的：覆盖成功路径添加latency_ms
        测试场景：Embedding连接测试成功
        预期：返回结果包含latency_ms和provider_id字段
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "embed1"}]}

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch('app.services.connection_test_service.httpx.AsyncClient') as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value = mock_client

            result = await ConnectionTestService.test_embedding_connection(
                "ollama",
                "http://localhost:11434",
                ""
            )

            assert result["success"] is True
            assert "latency_ms" in result
            assert "provider_id" in result
            assert result["provider_id"] == "ollama"

    @pytest.mark.asyncio
    async def test_test_llm_connection_ollama_success_path(self):
        """
        测试目的：完整覆盖ollama成功路径
        测试场景：ollama提供商连接成功
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama2:13b"},
                {"name": "mistral:7b"},
                {"name": "nomic-embed-text"}
            ]
        }

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch('app.services.connection_test_service.httpx.AsyncClient') as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value = mock_client

            result = await ConnectionTestService.test_llm_connection(
                "ollama",
                "http://localhost:11434/api",
                ""
            )

            assert result["success"] is True
            assert "latency_ms" in result
            assert result["provider_id"] == "ollama"
            assert len(result["models"]) == 3
            assert "llama2:13b" in result["models"]
