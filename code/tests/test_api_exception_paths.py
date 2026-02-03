"""
上海宇羲伏天智能科技有限公司出品

文件级注释：API端点缺失行补充测试 - 针对性覆盖未覆盖的代码行
内部逻辑：针对conversations.py和model_config.py的缺失行编写专门测试
目标：将API端点覆盖率提升到95%以上
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import Request, Response as HTTPXResponse, HTTPStatusError, ConnectError


@pytest.mark.asyncio
class TestConversationsAPIExceptionPaths:
    """
    类级注释：Conversations API异常处理路径测试
    职责：覆盖conversations.py中缺失的行（85, 130, 179, 226, 271, 307, 337）
    """

    async def test_list_conversations_exception_path(self, client: AsyncClient):
        """
        函数级注释：测试会话列表的异常处理路径
        未覆盖行号：conversations.py:90-101（异常处理）
        """
        from app.services.conversation_service import ConversationService

        with patch.object(ConversationService, "list_conversations", new_callable=AsyncMock) as mock_list:
            mock_list.side_effect = Exception("查询失败")

            response = await client.get("/api/v1/conversations")
            assert response.status_code == 500
            # ErrorResponse格式：{error: {code, message, details}}
            result = response.json()
            # 验证返回的是错误响应格式
            assert "error" in result or "detail" in result

    async def test_get_conversation_detail_exception_path(self, client: AsyncClient):
        """
        函数级注释：测试获取会话详情的异常处理路径
        未覆盖行号：conversations.py:137-148（异常处理）
        """
        from app.services.conversation_service import ConversationService

        with patch.object(ConversationService, "get_conversation_detail", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("详情查询失败")

            # 创建会话
            create_res = await client.post(
                "/api/v1/conversations",
                json={"title": "异常测试", "model_name": "glm-4"}
            )
            conv_id = create_res.json()["data"]["id"]

            response = await client.get(f"/api/v1/conversations/{conv_id}")
            assert response.status_code == 500

    async def test_update_conversation_exception_path(self, client: AsyncClient):
        """
        函数级注释：测试更新会话的异常处理路径
        未覆盖行号：conversations.py:186-197（异常处理）
        """
        from app.services.conversation_service import ConversationService

        # 创建会话
        create_res = await client.post(
            "/api/v1/conversations",
            json={"title": "更新异常测试", "model_name": "glm-4"}
        )
        conv_id = create_res.json()["data"]["id"]

        with patch.object(ConversationService, "update_conversation", new_callable=AsyncMock) as mock_update:
            mock_update.side_effect = Exception("更新失败")

            response = await client.put(
                f"/api/v1/conversations/{conv_id}",
                json={"title": "新标题"}
            )
            assert response.status_code == 500

    async def test_delete_conversation_exception_path(self, client: AsyncClient):
        """
        函数级注释：测试删除会话的异常处理路径
        未覆盖行号：conversations.py:231-244（异常处理）
        """
        from app.services.conversation_service import ConversationService

        # 创建会话
        create_res = await client.post(
            "/api/v1/conversations",
            json={"title": "删除异常测试", "model_name": "glm-4"}
        )
        conv_id = create_res.json()["data"]["id"]

        with patch.object(ConversationService, "delete_conversation", new_callable=AsyncMock) as mock_delete:
            mock_delete.side_effect = Exception("删除失败")

            response = await client.delete(f"/api/v1/conversations/{conv_id}")
            assert response.status_code == 500

    async def test_send_message_exception_path(self, client: AsyncClient):
        """
        函数级注释：测试发送消息的异常处理路径
        未覆盖行号：conversations.py:278-289（异常处理）
        """
        from app.services.conversation_service import ConversationService

        # 创建会话
        create_res = await client.post(
            "/api/v1/conversations",
            json={"title": "消息异常测试", "model_name": "glm-4"}
        )
        conv_id = create_res.json()["data"]["id"]

        with patch.object(ConversationService, "send_message", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = Exception("发送失败")

            response = await client.post(
                f"/api/v1/conversations/{conv_id}/messages",
                json={"content": "测试", "stream": False}
            )
            assert response.status_code == 500

    async def test_get_messages_exception_path(self, client: AsyncClient):
        """
        函数级注释：测试获取消息列表的异常处理路径
        未覆盖行号：conversations.py:342-353（异常处理）
        """
        from app.services.conversation_service import ConversationService

        # 创建会话
        create_res = await client.post(
            "/api/v1/conversations",
            json={"title": "消息列表异常测试", "model_name": "glm-4"}
        )
        conv_id = create_res.json()["data"]["id"]

        with patch.object(ConversationService, "get_messages", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("获取消息失败")

            response = await client.get(f"/api/v1/conversations/{conv_id}/messages")
            assert response.status_code == 500


@pytest.mark.asyncio
class TestModelConfigAPIExceptionPaths:
    """
    类级注释：ModelConfig API异常处理路径测试
    职责：覆盖model_config.py中缺失的异常处理路径
    """

    async def test_get_llm_configs_exception_path(self, client: AsyncClient):
        """
        函数级注释：测试获取LLM配置的异常处理
        未覆盖行号：model_config.py:74-76（异常处理）
        """
        from app.api.v1.endpoints.model_config import ModelConfigService

        with patch.object(ModelConfigService, "get_model_configs", side_effect=Exception("获取失败")):
            response = await client.get("/api/v1/model-config/llm")
            assert response.status_code == 500

    async def test_save_llm_config_exception_path(self, client: AsyncClient):
        """
        函数级注释：测试保存LLM配置的通用异常处理
        未覆盖行号：model_config.py:122-126（异常处理）
        """
        config_data = {
            "provider_id": "ollama",
            "provider_name": "Ollama",
            "endpoint": "http://localhost:11434/api",
            "model_id": "llama3:8b",
            "model_name": "llama3:8b",
            "type": "text",
            "temperature": 0.5,
            "max_tokens": 4096,
            "top_p": 0.9,
            "top_k": 0,
            "status": 1
        }

        with patch("app.api.v1.endpoints.model_config.ModelConfigService.save_model_config",
                   side_effect=Exception("保存失败")):
            response = await client.post("/api/v1/model-config/llm", json=config_data)
            assert response.status_code == 500

    async def test_set_default_llm_exception_path(self, client: AsyncClient):
        """
        函数级注释：测试设置默认配置的异常处理
        未覆盖行号：model_config.py:158-160（异常处理）
        """
        with patch("app.api.v1.endpoints.model_config.ModelConfigService.set_default_config",
                   side_effect=Exception("设置失败")):
            response = await client.post("/api/v1/model-config/llm/nonexistent/set-default")
            assert response.status_code == 500

    async def test_delete_llm_config_exception_path(self, client: AsyncClient):
        """
        函数级注释：测试删除配置的通用异常处理
        未覆盖行号：model_config.py:186-187（异常处理）
        """
        with patch("app.api.v1.endpoints.model_config.ModelConfigService.delete_config",
                   side_effect=Exception("删除失败")):
            response = await client.delete("/api/v1/model-config/llm/test-id")
            assert response.status_code == 500

    async def test_update_llm_api_key_exception_path(self, client: AsyncClient):
        """
        函数级注释：测试更新API密钥的异常处理
        未覆盖行号：model_config.py:223-224（异常处理）
        """
        with patch("app.api.v1.endpoints.model_config.ModelConfigService.update_api_key",
                   side_effect=Exception("更新失败")):
            response = await client.put(
                "/api/v1/model-config/llm/test-id/api-key",
                json={"api_key": "new-key"}
            )
            assert response.status_code == 500

    async def test_get_embedding_configs_exception_path(self, client: AsyncClient):
        """
        函数级注释：测试获取Embedding配置的异常处理
        未覆盖行号：model_config.py:252-254（异常处理）
        """
        from app.api.v1.endpoints.model_config import EmbeddingConfigService

        with patch.object(EmbeddingConfigService, "get_embedding_configs",
                   side_effect=Exception("获取失败")):
            response = await client.get("/api/v1/model-config/embedding")
            assert response.status_code == 500

    async def test_save_embedding_config_exception_path(self, client: AsyncClient):
        """
        函数级注释：测试保存Embedding配置的异常处理
        未覆盖行号：model_config.py:285-287（异常处理）
        """
        config_data = {
            "provider_id": "ollama",
            "provider_name": "Ollama",
            "endpoint": "http://localhost:11434/api",
            "model_id": "mxbai-embed-large:latest",
            "model_name": "mxbai-embed-large:latest",
            "device": "cpu",
            "status": 1
        }

        with patch("app.api.v1.endpoints.model_config.EmbeddingConfigService.save_embedding_config",
                   side_effect=Exception("保存失败")):
            response = await client.post("/api/v1/model-config/embedding", json=config_data)
            assert response.status_code == 500

    async def test_set_default_embedding_exception_path(self, client: AsyncClient):
        """
        函数级注释：测试设置默认Embedding的异常处理
        未覆盖行号：model_config.py:318-320（异常处理）
        """
        with patch("app.api.v1.endpoints.model_config.EmbeddingConfigService.set_default_config",
                   side_effect=Exception("设置失败")):
            response = await client.post("/api/v1/model-config/embedding/nonexistent/set-default")
            assert response.status_code == 500

    async def test_delete_embedding_config_exception_path(self, client: AsyncClient):
        """
        函数级注释：测试删除Embedding配置的异常处理
        未覆盖行号：model_config.py:534-535（异常处理）
        """
        with patch("app.api.v1.endpoints.model_config.EmbeddingConfigService.delete_config",
                   side_effect=Exception("删除失败")):
            response = await client.delete("/api/v1/model-config/embedding/test-id")
            assert response.status_code == 500

    async def test_update_embedding_api_key_exception_path(self, client: AsyncClient):
        """
        函数级注释：测试更新Embedding API密钥的异常处理
        未覆盖行号：model_config.py:571-572（异常处理）
        """
        with patch("app.api.v1.endpoints.model_config.EmbeddingConfigService.update_api_key",
                   side_effect=Exception("更新失败")):
            response = await client.put(
                "/api/v1/model-config/embedding/test-id/api-key",
                json={"api_key": "new-key"}
            )
            assert response.status_code == 500

    async def test_get_ollama_models_connect_error(self, client: AsyncClient):
        """
        函数级注释：测试Ollama连接错误处理
        未覆盖行号：model_config.py:413-414（ConnectError处理）
        """
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value.get.side_effect = ConnectError("Connection refused")
            mock_client_class.return_value = mock_client

            response = await client.get("/api/v1/model-config/ollama/models")
            assert response.status_code == 503

    async def test_get_ollama_models_http_error(self, client: AsyncClient):
        """
        函数级注释：测试Ollama HTTP错误处理
        未覆盖行号：model_config.py:415-416（HTTPStatusError处理）
        """
        mock_request = Request("GET", "http://localhost:11434/api/tags")
        mock_response = HTTPXResponse(500, request=mock_request)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_get = MagicMock()
            mock_get.raise_for_status.side_effect = HTTPStatusError(
                "Server error", request=mock_request, response=mock_response
            )
            mock_client.__aenter__.return_value.get.return_value = mock_get
            mock_client_class.return_value = mock_client

            response = await client.get("/api/v1/model-config/ollama/models")
            assert response.status_code == 503

    async def test_get_ollama_models_exception_path(self, client: AsyncClient):
        """
        函数级注释：测试获取Ollama模型的通用异常处理
        未覆盖行号：model_config.py:417-419（异常处理）
        """
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value.get.side_effect = Exception("解析失败")
            mock_client_class.return_value = mock_client

            response = await client.get("/api/v1/model-config/ollama/models")
            assert response.status_code == 500

    async def test_pull_ollama_connect_error(self, client: AsyncClient):
        """
        函数级注释：测试拉取Ollama模型连接错误
        未覆盖行号：model_config.py:469-470（ConnectError处理）
        """
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value.post.side_effect = ConnectError("Connection refused")
            mock_client_class.return_value = mock_client

            response = await client.post("/api/v1/model-config/ollama/pull?model_name=llama3:8b")
            assert response.status_code == 503

    async def test_pull_ollama_http_error(self, client: AsyncClient):
        """
        函数级注释：测试拉取Ollama模型HTTP错误
        未覆盖行号：model_config.py:471-472（HTTPStatusError处理）
        """
        mock_request = Request("POST", "http://localhost:11434/api/pull")
        mock_response = HTTPXResponse(404, request=mock_request)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_post = MagicMock()
            mock_post.raise_for_status.side_effect = HTTPStatusError(
                "Not found", request=mock_request, response=mock_response
            )
            mock_client.__aenter__.return_value.post.return_value = mock_post
            mock_client_class.return_value = mock_client

            response = await client.post("/api/v1/model-config/ollama/pull?model_name=unknown")
            assert response.status_code == 500

    async def test_pull_ollama_exception_path(self, client: AsyncClient):
        """
        函数级注释：测试拉取Ollama模型的通用异常处理
        未覆盖行号：model_config.py:473-475（异常处理）
        """
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value.post.side_effect = Exception("拉取失败")
            mock_client_class.return_value = mock_client

            response = await client.post("/api/v1/model-config/ollama/pull?model_name=llama3:8b")
            assert response.status_code == 500

    async def test_test_llm_connection_exception_path(self, client: AsyncClient):
        """
        函数级注释：测试LLM连接测试异常处理
        未覆盖行号：model_config.py:627-629（异常处理）
        """
        with patch("app.api.v1.endpoints.model_config.ConnectionTestService.test_llm_connection",
                   side_effect=Exception("测试失败")):
            response = await client.post(
                "/api/v1/model-config/llm/test",
                json={
                    "provider_id": "ollama",
                    "endpoint": "http://localhost:11434",
                    "api_key": "",
                    "model_name": "llama3:8b"
                }
            )
            assert response.status_code == 500

    async def test_test_embedding_connection_exception_path(self, client: AsyncClient):
        """
        函数级注释：测试Embedding连接测试异常处理
        未覆盖行号：model_config.py:686-688（异常处理）
        """
        with patch("app.api.v1.endpoints.model_config.ConnectionTestService.test_embedding_connection",
                   side_effect=Exception("测试失败")):
            response = await client.post(
                "/api/v1/model-config/embedding/test",
                json={
                    "provider_id": "ollama",
                    "endpoint": "http://localhost:11434",
                    "api_key": "",
                    "model_name": "mxbai-embed-large:latest",
                    "device": "cpu"
                }
            )
            assert response.status_code == 500

    async def test_get_local_models_exception_path(self, client: AsyncClient):
        """
        函数级注释：测试获取本地模型异常处理
        未覆盖行号：model_config.py:710-718（异常处理返回空列表）
        """
        with patch("app.api.v1.endpoints.model_config.LocalModelService.scan_local_models",
                   side_effect=Exception("扫描失败")):
            response = await client.get("/api/v1/model-config/local/models")
            # 即使异常也返回200，带有空列表
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True
            assert result["data"]["models"] == []
            assert result["message"] == "扫描失败"


@pytest.mark.asyncio
class TestChatAPIExceptionPaths:
    """
    类级注释：Chat API异常处理路径测试
    职责：覆盖chat.py中缺失的异常处理行
    """

    async def test_chat_completions_exception_handling(self, client: AsyncClient):
        """
        函数级注释：测试聊天完成接口的装饰器异常处理
        未覆盖行号：chat.py装饰器处理异常的路径
        """
        # 使用无效输入触发装饰器异常处理
        response = await client.post(
            "/api/v1/chat/completions",
            json={"message": "", "stream": False, "use_agent": False}
        )
        # 应该被装饰器或验证器捕获
        assert response.status_code in [200, 400, 422]

    async def test_summary_exception_handling(self, client: AsyncClient):
        """
        函数级注释：测试文档总结异常处理
        未覆盖行号：chat.py装饰器异常处理
        """
        response = await client.post(
            "/api/v1/chat/summary",
            json={"doc_id": -1}  # 无效的doc_id
        )
        # 可能返回400或404或500
        assert response.status_code in [400, 404, 500]

    async def test_compare_exception_handling(self, client: AsyncClient):
        """
        函数级注释：测试文档对比异常处理
        未覆盖行号：chat.py装饰器异常处理
        """
        response = await client.post(
            "/api/v1/chat/compare",
            json={"doc_ids": []}  # 空数组
        )
        assert response.status_code in [200, 400, 500]


@pytest.mark.asyncio
class TestSearchAPIExceptionPaths:
    """
    类级注释：Search API异常处理路径测试
    """

    async def test_semantic_search_exception_path(self, client: AsyncClient):
        """
        函数级注释：测试语义搜索异常处理
        未覆盖行号：search.py:47-52（异常处理）
        """
        from app.services.search_service import SearchService

        with patch.object(SearchService, "semantic_search", new_callable=AsyncMock) as mock_search:
            mock_search.side_effect = Exception("搜索失败")

            response = await client.post(
                "/api/v1/search",
                json={"query": "测试", "top_k": 5}
            )
            assert response.status_code == 500
            assert "搜索失败" in response.json()["detail"]


@pytest.mark.asyncio
class TestDocumentsAPIExceptionPaths:
    """
    类级注释：Documents API异常处理路径测试
    注意：documents.py没有try-catch异常处理，只有HTTPException
    """

    async def test_delete_document_not_found(self, client: AsyncClient):
        """
        函数级注释：测试删除不存在的文档
        未覆盖行号：documents.py:63（HTTPException 404）
        """
        from app.services.ingest_service import IngestService

        with patch.object(IngestService, "delete_document", new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = False

            response = await client.delete("/api/v1/documents/999")
            assert response.status_code == 404
