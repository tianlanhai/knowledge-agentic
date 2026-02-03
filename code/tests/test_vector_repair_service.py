# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：vector_repair_service 模块单元测试
内部逻辑：测试向量库数据修复服务
覆盖范围：元数据修复、状态查询、异常处理
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.vector_repair_service import VectorRepairService
from app.models.models import Document, VectorMapping


class TestVectorRepairService:
    """
    类级注释：测试 VectorRepairService 类的功能
    """

    @pytest.mark.asyncio
    async def test_repair_vector_metadata_no_documents(self, db_session: AsyncSession, monkeypatch):
        """
        函数级注释：测试数据库中没有文档时的行为
        内部逻辑：mock 查询返回空列表，验证返回空结果
        参数：
            db_session: 测试数据库会话
            monkeypatch: pytest monkeypatch fixture
        """
        # 内部逻辑：mock 数据库查询返回空列表
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = []

        async def mock_execute(query):
            return mock_result

        db_session.execute = mock_execute

        # 内部逻辑：执行修复
        result = await VectorRepairService.repair_vector_metadata(db_session)

        # 内部逻辑：验证结果
        assert result["total_documents"] == 0
        assert result["fixed_chunks"] == 0

    @pytest.mark.asyncio
    async def test_repair_vector_metadata_with_documents(self, db_session: AsyncSession, monkeypatch):
        """
        函数级注释：测试有文档但向量库为空时的行为
        内部逻辑：mock 文档存在但向量库为空，验证正确处理
        参数：
            db_session: 测试数据库会话
            monkeypatch: pytest monkeypatch fixture
        """
        # 内部变量：模拟文档
        mock_doc = MagicMock(spec=Document)
        mock_doc.id = 1
        mock_doc.file_name = "test.pdf"
        mock_doc.source_type = "pdf"

        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [mock_doc]

        async def mock_execute(query):
            return mock_result

        db_session.execute = mock_execute

        # 内部变量：模拟空向量库
        mock_vector_db = MagicMock()
        mock_vector_db.get.return_value = {"ids": [], "metadatas": []}

        # 内部逻辑：mock IngestService.get_embeddings 和 Chroma
        with patch('app.services.vector_repair_service.IngestService') as mock_ingest, \
             patch('app.services.vector_repair_service.Chroma') as mock_chroma:

            mock_ingest.get_embeddings.return_value = MagicMock()
            mock_chroma.return_value = mock_vector_db

            # 内部逻辑：执行修复
            result = await VectorRepairService.repair_vector_metadata(db_session)

            # 内部逻辑：验证结果
            assert result["total_documents"] == 1
            assert result["total_chunks"] == 0
            assert result["fixed_chunks"] == 0

    @pytest.mark.asyncio
    async def test_repair_vector_metadata_with_chunks_no_mapping(self, db_session: AsyncSession, monkeypatch):
        """
        函数级注释：测试有chunk但没有VectorMapping记录时的行为
        内部逻辑：mock chunk存在但无映射，记录警告
        参数：
            db_session: 测试数据库会话
            monkeypatch: pytest monkeypatch fixture
        """
        # 内部变量：模拟文档
        mock_doc = MagicMock(spec=Document)
        mock_doc.id = 1
        mock_doc.file_name = "test.pdf"
        mock_doc.source_type = "pdf"

        mock_doc_result = MagicMock()
        mock_doc_result.scalars().all.return_value = [mock_doc]

        # 内部变量：模拟VectorMapping查询返回None
        mock_mapping_result = MagicMock()
        mock_mapping_result.scalar_one_or_none.return_value = None

        # 内部逻辑：根据查询类型返回不同结果
        execute_calls = {"doc": False, "mapping": 0}

        async def mock_execute(query):
            if not execute_calls["doc"]:
                execute_calls["doc"] = True
                return mock_doc_result
            else:
                execute_calls["mapping"] += 1
                return mock_mapping_result

        db_session.execute = mock_execute

        # 内部变量：模拟向量库数据
        mock_vector_db = MagicMock()
        mock_vector_db.get.return_value = {
            "ids": ["chunk1"],
            "metadatas": [{"doc_id": 1}]
        }

        with patch('app.services.vector_repair_service.IngestService') as mock_ingest, \
             patch('app.services.vector_repair_service.Chroma') as mock_chroma:

            mock_ingest.get_embeddings.return_value = MagicMock()
            mock_chroma.return_value = mock_vector_db

            # 内部逻辑：执行修复
            result = await VectorRepairService.repair_vector_metadata(db_session)

            # 内部逻辑：验证结果（无映射时，如果元数据中有doc_id，会更新文件名信息）
            assert result["total_documents"] == 1
            assert result["total_chunks"] == 1

    @pytest.mark.asyncio
    async def test_repair_vector_metadata_with_mapping_mismatch(self, db_session: AsyncSession):
        """
        函数级注释：测试元数据doc_id与VectorMapping不匹配时的修复
        内部逻辑：mock 元数据doc_id=2，VectorMapping doc_id=1，验证修复
        参数：
            db_session: 测试数据库会话
        """
        # 内部变量：模拟文档
        mock_doc = MagicMock(spec=Document)
        mock_doc.id = 1
        mock_doc.file_name = "test.pdf"
        mock_doc.source_type = "pdf"

        # 内部变量：模拟VectorMapping
        mock_mapping = MagicMock(spec=VectorMapping)
        mock_mapping.document_id = 1
        mock_mapping.chunk_id = "chunk1"

        mock_doc_result = MagicMock()
        mock_doc_result.scalars().all.return_value = [mock_doc]

        mock_mapping_result = MagicMock()
        mock_mapping_result.scalar_one_or_none.return_value = mock_mapping

        execute_calls = {"doc": False}

        async def mock_execute(query):
            if not execute_calls["doc"]:
                execute_calls["doc"] = True
                return mock_doc_result
            return mock_mapping_result

        db_session.execute = mock_execute

        # 内部变量：模拟向量库数据（元数据中doc_id=2，但VectorMapping显示应该是1）
        mock_vector_db = MagicMock()
        mock_vector_db.get.return_value = {
            "ids": ["chunk1"],
            "metadatas": [{"doc_id": 2, "file_name": "old.pdf"}]
        }

        with patch('app.services.vector_repair_service.IngestService') as mock_ingest, \
             patch('app.services.vector_repair_service.Chroma') as mock_chroma:

            mock_ingest.get_embeddings.return_value = MagicMock()
            mock_chroma.return_value = mock_vector_db

            # 内部逻辑：执行修复
            result = await VectorRepairService.repair_vector_metadata(db_session)

            # 内部逻辑：验证修复了1个chunk
            assert result["total_documents"] == 1
            assert result["total_chunks"] == 1
            assert result["fixed_chunks"] == 1
            # 验证调用了update_metadata
            mock_vector_db.update_metadata.assert_called_once()

    @pytest.mark.asyncio
    async def test_repair_vector_metadata_exception_handling(self, db_session: AsyncSession):
        """
        函数级注释：测试异常处理
        内部逻辑：mock 抛出异常，验证错误被记录
        参数：
            db_session: 测试数据库会话
        """
        # 内部逻辑：mock 抛出异常
        async def mock_execute_error(query):
            raise RuntimeError("数据库错误")

        db_session.execute = mock_execute_error

        # 内部逻辑：执行修复，捕获异常
        result = await VectorRepairService.repair_vector_metadata(db_session)

        # 内部逻辑：验证错误被记录
        assert "errors" in result
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_get_vector_status_success(self, db_session: AsyncSession):
        """
        函数级注释：测试成功获取向量库状态
        内部逻辑：mock 数据库和向量库查询，验证返回状态
        参数：
            db_session: 测试数据库会话
        """
        # 内部变量：模拟文档
        mock_doc = MagicMock(spec=Document)
        mock_mapping = MagicMock(spec=VectorMapping)

        mock_doc_result = MagicMock()
        mock_doc_result.scalars().all.return_value = [mock_doc]

        mock_chunk_result = MagicMock()
        mock_chunk_result.scalars().all.return_value = [mock_mapping, mock_mapping]

        execute_calls = {"doc": False}

        async def mock_execute(query):
            if not execute_calls["doc"]:
                execute_calls["doc"] = True
                return mock_doc_result
            return mock_chunk_result

        db_session.execute = mock_execute

        # 内部变量：模拟向量库数据
        mock_vector_db = MagicMock()
        mock_vector_db.get.return_value = {
            "ids": ["chunk1", "chunk2"],
            "metadatas": [{"doc_id": 1}, {"doc_id": 1}]
        }

        with patch('app.services.vector_repair_service.IngestService') as mock_ingest, \
             patch('app.services.vector_repair_service.Chroma') as mock_chroma:

            mock_ingest.get_embeddings.return_value = MagicMock()
            mock_chroma.return_value = mock_vector_db

            # 内部逻辑：获取状态
            status = await VectorRepairService.get_vector_status(db_session)

            # 内部逻辑：验证状态
            assert status["database_documents"] == 1
            assert status["database_chunks"] == 2
            assert status["vector_chunks"] == 2
            assert "doc_id_distribution" in status

    @pytest.mark.asyncio
    async def test_get_vector_status_exception_handling(self, db_session: AsyncSession):
        """
        函数级注释：测试获取状态时的异常处理
        内部逻辑：mock 抛出异常，验证错误被记录
        参数：
            db_session: 测试数据库会话
        """
        async def mock_execute_error(query):
            raise RuntimeError("连接失败")

        db_session.execute = mock_execute_error

        # 内部逻辑：获取状态
        status = await VectorRepairService.get_vector_status(db_session)

        # 内部逻辑：验证错误被记录
        assert "error" in status

    @pytest.mark.asyncio
    async def test_repair_vector_metadata_persists_after_update(self, db_session: AsyncSession):
        """
        函数级注释：测试修复后调用persist
        内部逻辑：mock 有需要修复的chunk，验证persist被调用
        参数：
            db_session: 测试数据库会话
        """
        # 内部变量：模拟文档和映射
        mock_doc = MagicMock(spec=Document)
        mock_doc.id = 1
        mock_doc.file_name = "test.pdf"
        mock_doc.source_type = "pdf"

        mock_mapping = MagicMock(spec=VectorMapping)
        mock_mapping.document_id = 1
        mock_mapping.chunk_id = "chunk1"

        mock_doc_result = MagicMock()
        mock_doc_result.scalars().all.return_value = [mock_doc]

        mock_mapping_result = MagicMock()
        mock_mapping_result.scalar_one_or_none.return_value = mock_mapping

        execute_calls = {"doc": False}

        async def mock_execute(query):
            if not execute_calls["doc"]:
                execute_calls["doc"] = True
                return mock_doc_result
            return mock_mapping_result

        db_session.execute = mock_execute

        # 内部变量：模拟向量库数据（元数据doc_id不匹配）
        mock_vector_db = MagicMock()
        mock_vector_db.get.return_value = {
            "ids": ["chunk1"],
            "metadatas": [{"doc_id": 99}]  # 不匹配，需要修复
        }

        with patch('app.services.vector_repair_service.IngestService') as mock_ingest, \
             patch('app.services.vector_repair_service.Chroma') as mock_chroma:

            mock_ingest.get_embeddings.return_value = MagicMock()
            mock_chroma.return_value = mock_vector_db

            # 内部逻辑：执行修复
            result = await VectorRepairService.repair_vector_metadata(db_session)

            # 内部逻辑：验证persist被调用
            assert result["fixed_chunks"] == 1
            mock_vector_db.persist.assert_called_once()

    @pytest.mark.asyncio
    async def test_repair_vector_metadata_no_fixes_needed(self, db_session: AsyncSession):
        """
        函数级注释：测试不需要修复时的行为
        内部逻辑：mock 元数据doc_id与VectorMapping一致，验证不调用更新
        参数：
            db_session: 测试数据库会话
        """
        mock_doc = MagicMock(spec=Document)
        mock_doc.id = 1

        mock_mapping = MagicMock(spec=VectorMapping)
        mock_mapping.document_id = 1
        mock_mapping.chunk_id = "chunk1"

        mock_doc_result = MagicMock()
        mock_doc_result.scalars().all.return_value = [mock_doc]

        mock_mapping_result = MagicMock()
        mock_mapping_result.scalar_one_or_none.return_value = mock_mapping

        execute_calls = {"doc": False}

        async def mock_execute(query):
            if not execute_calls["doc"]:
                execute_calls["doc"] = True
                return mock_doc_result
            return mock_mapping_result

        db_session.execute = mock_execute

        # 内部变量：模拟向量库数据（元数据doc_id=1，与VectorMapping一致）
        mock_vector_db = MagicMock()
        mock_vector_db.get.return_value = {
            "ids": ["chunk1"],
            "metadatas": [{"doc_id": 1}]
        }

        with patch('app.services.vector_repair_service.IngestService') as mock_ingest, \
             patch('app.services.vector_repair_service.Chroma') as mock_chroma:

            mock_ingest.get_embeddings.return_value = MagicMock()
            mock_chroma.return_value = mock_vector_db

            # 内部逻辑：执行修复
            result = await VectorRepairService.repair_vector_metadata(db_session)

            # 内部逻辑：验证不需要修复
            assert result["fixed_chunks"] == 0
            mock_vector_db.update_metadata.assert_not_called()

    @pytest.mark.asyncio
    async def test_repair_vector_metadata_multiple_chunks(self, db_session: AsyncSession):
        """
        函数级注释：测试多个chunk的批量修复
        内部逻辑：mock 多个chunk需要修复，验证批量更新
        参数：
            db_session: 测试数据库会话
        """
        mock_doc = MagicMock(spec=Document)
        mock_doc.id = 1
        mock_doc.file_name = "test.pdf"
        mock_doc.source_type = "pdf"

        mock_mapping1 = MagicMock(spec=VectorMapping)
        mock_mapping1.document_id = 1
        mock_mapping1.chunk_id = "chunk1"

        mock_mapping2 = MagicMock(spec=VectorMapping)
        mock_mapping2.document_id = 1
        mock_mapping2.chunk_id = "chunk2"

        # 内部变量：创建正确的mock scalars结果
        mock_scalars_doc = MagicMock()
        mock_scalars_doc.all.return_value = [mock_doc]

        mock_doc_result = MagicMock()
        mock_doc_result.scalars.return_value = mock_scalars_doc

        # 内部逻辑：根据调用顺序返回不同mapping
        mapping_calls = [mock_mapping1, mock_mapping2]
        mapping_index = [0]

        def wrapped_scalar_one():
            if mapping_index[0] < len(mapping_calls):
                result = mapping_calls[mapping_index[0]]
                mapping_index[0] += 1
                return result
            return None

        mock_mapping_result = MagicMock()
        mock_mapping_result.scalar_one_or_none.side_effect = wrapped_scalar_one

        execute_calls = {"doc": False}

        async def mock_execute(query):
            if not execute_calls["doc"]:
                execute_calls["doc"] = True
                return mock_doc_result
            return mock_mapping_result

        db_session.execute = mock_execute

        # 内部变量：模拟多个chunk需要修复
        mock_vector_db = MagicMock()
        mock_vector_db.get.return_value = {
            "ids": ["chunk1", "chunk2"],
            "metadatas": [{"doc_id": 99}, {"doc_id": 88}]
        }

        with patch('app.services.vector_repair_service.IngestService') as mock_ingest, \
             patch('app.services.vector_repair_service.Chroma') as mock_chroma:

            mock_ingest.get_embeddings.return_value = MagicMock()
            mock_chroma.return_value = mock_vector_db

            # 内部逻辑：执行修复
            result = await VectorRepairService.repair_vector_metadata(db_session)

            # 内部逻辑：验证修复了2个chunk
            assert result["fixed_chunks"] == 2
            # 验证批量更新被调用
            mock_vector_db.update_metadata.assert_called_once()
            call_args = mock_vector_db.update_metadata.call_args
            assert len(call_args[1]["ids"]) == 2

    @pytest.mark.asyncio
    async def test_get_vector_status_doc_id_distribution(self, db_session: AsyncSession):
        """
        函数级注释：测试doc_id分布统计
        内部逻辑：mock 不同doc_id的chunk，验证统计正确
        参数：
            db_session: 测试数据库会话
        """
        mock_doc_result = MagicMock()
        mock_doc_result.scalars().all.return_value = []

        mock_chunk_result = MagicMock()
        mock_chunk_result.scalars().all.return_value = []

        execute_calls = {"doc": False}

        async def mock_execute(query):
            if not execute_calls["doc"]:
                execute_calls["doc"] = True
                return mock_doc_result
            return mock_chunk_result

        db_session.execute = mock_execute

        # 内部变量：模拟不同doc_id的chunk
        mock_vector_db = MagicMock()
        mock_vector_db.get.return_value = {
            "ids": ["chunk1", "chunk2", "chunk3", "chunk4"],
            "metadatas": [
                {"doc_id": 1},
                {"doc_id": 1},
                {"doc_id": 2},
                {"doc_id": 2}
            ]
        }

        with patch('app.services.vector_repair_service.IngestService') as mock_ingest, \
             patch('app.services.vector_repair_service.Chroma') as mock_chroma:

            mock_ingest.get_embeddings.return_value = MagicMock()
            mock_chroma.return_value = mock_vector_db

            # 内部逻辑：获取状态
            status = await VectorRepairService.get_vector_status(db_session)

            # 内部逻辑：验证doc_id分布
            assert status["doc_id_distribution"]["1"] == 2
            assert status["doc_id_distribution"]["2"] == 2

    @pytest.mark.asyncio
    async def test_repair_vector_metadata_updates_file_info(self, db_session: AsyncSession):
        """
        函数级注释：测试修复时更新文件名信息
        内部逻辑：mock 修复时更新file_name和source_type
        参数：
            db_session: 测试数据库会话
        """
        mock_doc = MagicMock(spec=Document)
        mock_doc.id = 1
        mock_doc.file_name = "updated.pdf"
        mock_doc.source_type = "pdf"

        mock_mapping = MagicMock(spec=VectorMapping)
        mock_mapping.document_id = 1
        mock_mapping.chunk_id = "chunk1"

        mock_doc_result = MagicMock()
        mock_doc_result.scalars().all.return_value = [mock_doc]

        mock_mapping_result = MagicMock()
        mock_mapping_result.scalar_one_or_none.return_value = mock_mapping

        execute_calls = {"doc": False}

        async def mock_execute(query):
            if not execute_calls["doc"]:
                execute_calls["doc"] = True
                return mock_doc_result
            return mock_mapping_result

        db_session.execute = mock_execute

        # 内部变量：模拟需要更新的chunk
        mock_vector_db = MagicMock()
        mock_vector_db.get.return_value = {
            "ids": ["chunk1"],
            "metadatas": [{"doc_id": 99}]
        }

        with patch('app.services.vector_repair_service.IngestService') as mock_ingest, \
             patch('app.services.vector_repair_service.Chroma') as mock_chroma:

            mock_ingest.get_embeddings.return_value = MagicMock()
            mock_chroma.return_value = mock_vector_db

            # 内部逻辑：执行修复
            result = await VectorRepairService.repair_vector_metadata(db_session)

            # 内部逻辑：验证修复成功
            assert result["fixed_chunks"] == 1
            # 验证update_metadata被调用
            mock_vector_db.update_metadata.assert_called_once()
            # 验证元数据包含文件信息
            call_args = mock_vector_db.update_metadata.call_args
            updated_metadata = call_args[1]["metadatas"][0]
            assert updated_metadata["doc_id"] == 1
            assert updated_metadata["file_name"] == "updated.pdf"
            assert updated_metadata["source_type"] == "pdf"

    @pytest.mark.asyncio
    async def test_get_vector_status_empty_vector_db(self, db_session: AsyncSession):
        """
        函数级注释：测试向量库为空时的状态获取
        内部逻辑：mock 向量库返回空数据
        参数：
            db_session: 测试数据库会话
        """
        mock_doc_result = MagicMock()
        mock_doc_result.scalars().all.return_value = []

        mock_chunk_result = MagicMock()
        mock_chunk_result.scalars().all.return_value = []

        execute_calls = {"doc": False}

        async def mock_execute(query):
            if not execute_calls["doc"]:
                execute_calls["doc"] = True
                return mock_doc_result
            return mock_chunk_result

        db_session.execute = mock_execute

        mock_vector_db = MagicMock()
        mock_vector_db.get.return_value = {
            "ids": [],
            "metadatas": []
        }

        with patch('app.services.vector_repair_service.IngestService') as mock_ingest, \
             patch('app.services.vector_repair_service.Chroma') as mock_chroma:

            mock_ingest.get_embeddings.return_value = MagicMock()
            mock_chroma.return_value = mock_vector_db

            # 内部逻辑：获取状态
            status = await VectorRepairService.get_vector_status(db_session)

            # 内部逻辑：验证状态
            assert status["vector_chunks"] == 0
            assert status["doc_id_distribution"] == {}
