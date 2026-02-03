# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：ZhipuAI Embeddings 模块测试
内部逻辑：测试智谱AI Embeddings API的封装功能
"""

import pytest
from typing import List
from unittest.mock import MagicMock, patch, Mock
from requests import Response

from app.utils.zhipuai_embeddings import ZhipuAIEmbeddings


# ============================================================================
# 测试辅助类
# ============================================================================


class MockResponse:
    """Mock响应类，用于模拟requests.Response"""

    def __init__(self, json_data: dict, status_code: int = 200):
        """
        函数级注释：初始化Mock响应
        参数：
            json_data - 返回的JSON数据
            status_code - HTTP状态码
        """
        self.json_data = json_data
        self.status_code = status_code
        self.text = str(json_data)

    def json(self):
        """返回JSON数据"""
        return self.json_data

    def raise_for_status(self):
        """如果状态码不是200，抛出异常"""
        if self.status_code >= 400:
            from requests.exceptions import HTTPError
            raise HTTPError(f"HTTP {self.status_code} Error", response=self)


# ============================================================================
# 初始化测试
# ============================================================================


class TestZhipuAIEmbeddingsInitialization:
    """
    类级注释：ZhipuAI Embeddings初始化测试
    测试场景：
        1. 使用传入参数初始化
        2. 从配置读取API密钥
        3. API密钥缺失时抛出异常
        4. api_base规范化处理
    """

    def test_initialization_with_provided_params(self):
        """
        测试目的：验证使用传入参数初始化
        测试场景：直接传入api_key、model和api_base
        """
        with patch("app.utils.zhipuai_embeddings.settings") as mock_settings:
            mock_settings.zhipuai_embedding_api_key = ""
            mock_settings.zhipuai_embedding_base_url = ""

            embeddings = ZhipuAIEmbeddings(
                api_key="test_key",
                model="embedding-2",
                api_base="https://api.example.com"
            )

            assert embeddings.api_key == "test_key"
            assert embeddings.model == "embedding-2"
            # 内部逻辑：api_base会自动添加/embeddings后缀
            assert embeddings.api_base == "https://api.example.com/embeddings"

    def test_initialization_with_api_base_trailing_slash(self):
        """
        测试目的：验证api_base末尾斜杠处理
        测试场景：api_base末尾已有斜杠时的规范化
        """
        with patch("app.utils.zhipuai_embeddings.settings") as mock_settings:
            mock_settings.zhipuai_embedding_api_key = ""
            mock_settings.zhipuai_embedding_base_url = ""

            embeddings = ZhipuAIEmbeddings(
                api_key="test_key",
                api_base="https://api.example.com/"
            )

            # 内部逻辑：会先去除末尾斜杠，再添加/embeddings
            assert embeddings.api_base == "https://api.example.com/embeddings"

    def test_initialization_with_api_base_already_has_embeddings(self):
        """
        测试目的：验证api_base已有embeddings路径时不重复添加
        测试场景：传入完整路径的api_base
        """
        with patch("app.utils.zhipuai_embeddings.settings") as mock_settings:
            mock_settings.zhipuai_embedding_api_key = ""
            mock_settings.zhipuai_embedding_base_url = ""

            embeddings = ZhipuAIEmbeddings(
                api_key="test_key",
                api_base="https://api.example.com/v1/embeddings"
            )

            # 内部逻辑：已有/embeddings时不重复添加
            assert embeddings.api_base == "https://api.example.com/v1/embeddings"

    def test_initialization_from_settings(self):
        """
        测试目的：验证从配置读取API密钥
        测试场景：不传api_key时从settings读取
        """
        with patch("app.utils.zhipuai_embeddings.settings") as mock_settings:
            mock_settings.zhipuai_embedding_api_key = "config_key"
            mock_settings.zhipuai_embedding_base_url = "https://api.example.com"

            embeddings = ZhipuAIEmbeddings()

            assert embeddings.api_key == "config_key"
            # 内部逻辑：从配置读取的base_url也会添加/embeddings
            assert embeddings.api_base == "https://api.example.com/embeddings"

    def test_initialization_missing_api_key_raises_error(self):
        """
        测试目的：验证API密钥缺失时抛出异常
        测试场景：既不传api_key，配置中也没有
        """
        with patch("app.utils.zhipuai_embeddings.settings") as mock_settings:
            mock_settings.zhipuai_embedding_api_key = ""
            mock_settings.zhipuai_embedding_base_url = "https://api.example.com"

            with pytest.raises(ValueError) as exc_info:
                ZhipuAIEmbeddings()

            assert "ZHIPUAI_EMBEDDING_API_KEY" in str(exc_info.value)

    def test_initialization_default_model(self):
        """
        测试目的：验证默认模型名称
        测试场景：不传model参数时的默认值
        """
        with patch("app.utils.zhipuai_embeddings.settings") as mock_settings:
            mock_settings.zhipuai_embedding_api_key = "test_key"
            mock_settings.zhipuai_embedding_base_url = "https://api.example.com"

            embeddings = ZhipuAIEmbeddings()

            assert embeddings.model == "embedding-3"


# ============================================================================
# embed_documents 测试
# ============================================================================


class TestZhipuAIEmbeddingsEmbedDocuments:
    """
    类级注释：embed_documents方法测试
    测试场景：
        1. 成功批量嵌入文档
        2. API调用失败时抛出异常
        3. API返回格式错误时抛出异常
        4. 空文本列表处理
    """

    @pytest.mark.asyncio
    async def test_embed_documents_success(self):
        """
        测试目的：验证成功嵌入文档
        测试场景：正常API调用返回向量数据

        注意：实际实现是逐个调用API（每次只处理一个文本）
        """
        with patch("app.utils.zhipuai_embeddings.settings") as mock_settings:
            mock_settings.zhipuai_embedding_api_key = "test_key"
            mock_settings.zhipuai_embedding_base_url = "https://api.example.com"

            # 内部逻辑：Mock API响应 - 每次调用返回不同的向量
            call_count = [0]

            def mock_post_func(*args, **kwargs):
                mock_resp = Mock()
                call_count[0] += 1
                # 内部逻辑：根据调用次数返回不同的向量
                if call_count[0] == 1:
                    mock_resp.json.return_value = {"data": [{"embedding": [0.1, 0.2, 0.3]}]}
                else:
                    mock_resp.json.return_value = {"data": [{"embedding": [0.4, 0.5, 0.6]}]}
                mock_resp.raise_for_status = Mock()
                return mock_resp

            with patch("requests.post", side_effect=mock_post_func) as mock_post:
                embeddings = ZhipuAIEmbeddings()
                result = embeddings.embed_documents(["text1", "text2"])

                # 内部逻辑：验证返回的向量
                assert len(result) == 2
                assert result[0] == [0.1, 0.2, 0.3]
                assert result[1] == [0.4, 0.5, 0.6]

                # 内部逻辑：验证API被调用两次（逐个文本调用）
                assert mock_post.call_count == 2

    @pytest.mark.asyncio
    async def test_embed_documents_api_error(self):
        """
        测试目的：验证API错误处理
        测试场景：API返回非200状态码
        """
        with patch("app.utils.zhipuai_embeddings.settings") as mock_settings:
            mock_settings.zhipuai_embedding_api_key = "test_key"
            mock_settings.zhipuai_embedding_base_url = "https://api.example.com"

            mock_response = Mock()
            mock_response.raise_for_status.side_effect = Exception("API Error")

            with patch("requests.post", return_value=mock_response):
                embeddings = ZhipuAIEmbeddings()

                with pytest.raises(Exception) as exc_info:
                    embeddings.embed_documents(["test"])

                assert "API Error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_embed_documents_invalid_response_format(self):
        """
        测试目的：验证无效响应格式处理
        测试场景：API返回的数据格式不符合预期
        """
        with patch("app.utils.zhipuai_embeddings.settings") as mock_settings:
            mock_settings.zhipuai_embedding_api_key = "test_key"
            mock_settings.zhipuai_embedding_base_url = "https://api.example.com"

            # 内部逻辑：Mock返回无效格式
            mock_response = Mock()
            mock_response.json.return_value = {"error": "Invalid request"}
            mock_response.raise_for_status = Mock()

            with patch("requests.post", return_value=mock_response):
                embeddings = ZhipuAIEmbeddings()

                with pytest.raises(ValueError) as exc_info:
                    embeddings.embed_documents(["test"])

                assert "智谱AI API 返回格式错误" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_embed_documents_empty_data(self):
        """
        测试目的：验证空data字段处理
        测试场景：API返回data为空列表
        """
        with patch("app.utils.zhipuai_embeddings.settings") as mock_settings:
            mock_settings.zhipuai_embedding_api_key = "test_key"
            mock_settings.zhipuai_embedding_base_url = "https://api.example.com"

            mock_response = Mock()
            mock_response.json.return_value = {"data": []}
            mock_response.raise_for_status = Mock()

            with patch("requests.post", return_value=mock_response):
                embeddings = ZhipuAIEmbeddings()

                with pytest.raises(ValueError) as exc_info:
                    embeddings.embed_documents(["test"])

                assert "智谱AI API 返回格式错误" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_embed_documents_single_text(self):
        """
        测试目的：验证单个文本嵌入
        测试场景：只嵌入一个文本
        """
        with patch("app.utils.zhipuai_embeddings.settings") as mock_settings:
            mock_settings.zhipuai_embedding_api_key = "test_key"
            mock_settings.zhipuai_embedding_base_url = "https://api.example.com"

            mock_response = Mock()
            mock_response.json.return_value = {
                "data": [{"embedding": [0.1, 0.2, 0.3]}]
            }
            mock_response.raise_for_status = Mock()

            with patch("requests.post", return_value=mock_response):
                embeddings = ZhipuAIEmbeddings()
                result = embeddings.embed_documents(["single text"])

                assert len(result) == 1
                assert result[0] == [0.1, 0.2, 0.3]


# ============================================================================
# embed_query 测试
# ============================================================================


class TestZhipuAIEmbeddingsEmbedQuery:
    """
    类级注释：embed_query方法测试
    测试场景：
        1. 成功嵌入查询文本
        2. 返回单个向量而非列表
    """

    @pytest.mark.asyncio
    async def test_embed_query_success(self):
        """
        测试目的：验证成功嵌入查询
        测试场景：正常嵌入单个查询文本
        """
        with patch("app.utils.zhipuai_embeddings.settings") as mock_settings:
            mock_settings.zhipuai_embedding_api_key = "test_key"
            mock_settings.zhipuai_embedding_base_url = "https://api.example.com"

            mock_response = Mock()
            mock_response.json.return_value = {
                "data": [{"embedding": [0.1, 0.2, 0.3]}]
            }
            mock_response.raise_for_status = Mock()

            with patch("requests.post", return_value=mock_response):
                embeddings = ZhipuAIEmbeddings()
                result = embeddings.embed_query("query text")

                # 内部逻辑：返回单个向量而非列表
                assert result == [0.1, 0.2, 0.3]
                assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_embed_query_delegates_to_embed_documents(self):
        """
        测试目的：验证embed_query委托给embed_documents
        测试场景：确认内部方法调用关系
        """
        with patch("app.utils.zhipuai_embeddings.settings") as mock_settings:
            mock_settings.zhipuai_embedding_api_key = "test_key"
            mock_settings.zhipuai_embedding_base_url = "https://api.example.com"

            mock_response = Mock()
            mock_response.json.return_value = {
                "data": [{"embedding": [0.5, 0.6, 0.7]}]
            }
            mock_response.raise_for_status = Mock()

            with patch("requests.post", return_value=mock_response):
                embeddings = ZhipuAIEmbeddings()

                # 内部逻辑：使用_embed_documents方法
                with patch.object(embeddings, "_embed_documents", wraps=embeddings._embed_documents) as mock_embed:
                    embeddings.embed_query("test")

                    # 内部逻辑：验证_embed_documents被调用
                    mock_embed.assert_called_once_with(["test"])


# ============================================================================
# 边界条件测试
# ============================================================================


class TestZhipuAIEmbeddingsEdgeCases:
    """
    类级注释：边界条件测试
    测试场景：
        1. API超时处理
        2. 大批量文本处理
        3. 特殊字符文本
    """

    @pytest.mark.asyncio
    async def test_embed_documents_timeout(self):
        """
        测试目的：验证超时处理
        测试场景：API调用超时
        """
        import requests

        with patch("app.utils.zhipuai_embeddings.settings") as mock_settings:
            mock_settings.zhipuai_embedding_api_key = "test_key"
            mock_settings.zhipuai_embedding_base_url = "https://api.example.com"

            with patch("requests.post", side_effect=requests.Timeout("Connection timeout")):
                embeddings = ZhipuAIEmbeddings()

                with pytest.raises(requests.Timeout):
                    embeddings.embed_documents(["test"])

    @pytest.mark.asyncio
    async def test_embed_documents_with_special_characters(self):
        """
        测试目的：验证特殊字符处理
        测试场景：包含特殊字符的文本

        注意：每次调用只处理一个文本
        """
        with patch("app.utils.zhipuai_embeddings.settings") as mock_settings:
            mock_settings.zhipuai_embedding_api_key = "test_key"
            mock_settings.zhipuai_embedding_base_url = "https://api.example.com"

            call_count = [0]
            inputs = []

            def mock_post_func(*args, **kwargs):
                mock_resp = Mock()
                # 内部逻辑：记录请求的输入
                inputs.append(kwargs.get("json", {}).get("input", ""))
                mock_resp.json.return_value = {"data": [{"embedding": [0.1, 0.2]}]}
                mock_resp.raise_for_status = Mock()
                return mock_resp

            with patch("requests.post", side_effect=mock_post_func) as mock_post:
                embeddings = ZhipuAIEmbeddings()
                result = embeddings.embed_documents(["中文\n\t\r", "emoji \U0001f600"])

                assert len(result) == 2
                assert result[0] == [0.1, 0.2]
                assert result[1] == [0.1, 0.2]

                # 内部逻辑：验证两个输入都被处理
                assert inputs[0] == "中文\n\t\r"
                assert inputs[1] == "emoji \U0001f600"

    @pytest.mark.asyncio
    async def test_embed_documents_empty_string(self):
        """
        测试目的：验证空字符串处理
        测试场景：空字符串作为输入
        """
        with patch("app.utils.zhipuai_embeddings.settings") as mock_settings:
            mock_settings.zhipuai_embedding_api_key = "test_key"
            mock_settings.zhipuai_embedding_base_url = "https://api.example.com"

            mock_response = Mock()
            mock_response.json.return_value = {
                "data": [{"embedding": [0.0, 0.0, 0.0]}]
            }
            mock_response.raise_for_status = Mock()

            with patch("requests.post", return_value=mock_response):
                embeddings = ZhipuAIEmbeddings()
                result = embeddings.embed_documents([""])

                assert len(result) == 1
                assert result[0] == [0.0, 0.0, 0.0]

    @pytest.mark.asyncio
    async def test_embed_documents_multiple_texts(self):
        """
        测试目的：验证多文本批量处理
        测试场景：多个文本依次处理（因为实现是逐个调用）
        """
        with patch("app.utils.zhipuai_embeddings.settings") as mock_settings:
            mock_settings.zhipuai_embedding_api_key = "test_key"
            mock_settings.zhipuai_embedding_base_url = "https://api.example.com"

            # 内部逻辑：为每个文本返回不同的向量
            def mock_post_func(*args, **kwargs):
                mock_resp = Mock()
                text = kwargs["json"]["input"]
                # 内部逻辑：根据文本生成不同的向量
                embedding = [[0.1] * 3, [0.2] * 3, [0.3] * 3, [0.4] * 3, [0.5] * 3][
                    ["first", "second", "third", "fourth", "fifth"].index(text) % 5
                ]
                mock_resp.json.return_value = {"data": [{"embedding": embedding}]}
                mock_resp.raise_for_status = Mock()
                return mock_resp

            with patch("requests.post", side_effect=mock_post_func) as mock_post:
                embeddings = ZhipuAIEmbeddings()
                texts = ["first", "second", "third", "fourth", "fifth"]
                result = embeddings.embed_documents(texts)

                # 内部逻辑：验证每个文本都被处理
                assert len(result) == 5
                assert result[0] == [0.1, 0.1, 0.1]
                assert result[4] == [0.5, 0.5, 0.5]

                # 内部逻辑：验证API被调用5次（逐个调用）
                assert mock_post.call_count == 5
