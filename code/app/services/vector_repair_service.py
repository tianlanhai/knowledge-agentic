"""
上海宇羲伏天智能科技有限公司出品

文件级注释：向量库数据修复服务
内部逻辑：修复向量库中chunk元数据的doc_id，确保与数据库同步
"""

from sqlalchemy import select
from loguru import logger
from typing import Dict, List
from app.models.models import Document, VectorMapping
from app.core.config import settings
from langchain_community.vectorstores import Chroma
from app.services.ingest_service import IngestService


class VectorRepairService:
    """
    类级注释：向量库修复服务类，用于同步数据库和向量库的元数据
    """

    @staticmethod
    async def repair_vector_metadata(db) -> Dict[str, any]:
        """
        函数级注释：修复向量库中的文档元数据
        内部逻辑：获取数据库所有文档 -> 获取向量库所有chunk -> 更新元数据中的doc_id
        参数：
            db: 数据库会话
        返回值：Dict - 修复结果统计
        """
        # 内部变量：统计修复结果
        result = {
            "total_documents": 0,
            "total_chunks": 0,
            "fixed_chunks": 0,
            "errors": []
        }

        try:
            # 内部逻辑：获取数据库中所有文档
            doc_result = await db.execute(select(Document))
            documents = doc_result.scalars().all()
            result["total_documents"] = len(documents)

            if not documents:
                logger.warning("[向量库修复] 数据库中没有文档")
                return result

            logger.info(f"[向量库修复] 找到 {len(documents)} 个文档")

            # 内部逻辑：初始化向量库
            embeddings = IngestService.get_embeddings()
            vector_db = Chroma(
                persist_directory=settings.CHROMA_DB_PATH,
                embedding_function=embeddings,
                collection_name=settings.CHROMA_COLLECTION_NAME
            )

            # 内部逻辑：获取向量库中的所有数据
            all_data = vector_db.get()
            result["total_chunks"] = len(all_data["ids"])

            if not all_data["ids"]:
                logger.warning("[向量库修复] 向量库中没有数据")
                return result

            logger.info(f"[向量库修复] 向量库中有 {len(all_data['ids'])} 个chunk")

            # 内部逻辑：构建doc_id到文档的映射
            doc_map = {doc.id: doc for doc in documents}

            # 内部变量：需要更新的chunk IDs和对应的新元数据
            ids_to_update = []
            metadatas_to_update = []

            # 内部逻辑：遍历所有chunk，检查并修复元数据
            for i, chunk_id in enumerate(all_data["ids"]):
                current_metadata = all_data["metadatas"][i] if all_data["metadatas"] else {}
                current_doc_id = current_metadata.get("doc_id")

                # 内部逻辑：检查chunk的VectorMapping记录
                # 说明：通过VectorMapping表可以找到chunk应该属于哪个文档
                mapping_result = await db.execute(
                    select(VectorMapping).where(VectorMapping.chunk_id == chunk_id)
                )
                mapping = mapping_result.scalar_one_or_none()

                if mapping:
                    # 内部逻辑：找到了映射关系，检查doc_id是否正确
                    correct_doc_id = mapping.document_id
                    if current_doc_id != correct_doc_id:
                        # 内部逻辑：doc_id不匹配，需要修复
                        new_metadata = current_metadata.copy()
                        new_metadata["doc_id"] = correct_doc_id

                        # 内部逻辑：添加文件名信息（如果数据库中存在该文档）
                        if correct_doc_id in doc_map:
                            doc = doc_map[correct_doc_id]
                            new_metadata["file_name"] = doc.file_name
                            new_metadata["source_type"] = doc.source_type

                        ids_to_update.append(chunk_id)
                        metadatas_to_update.append(new_metadata)
                        result["fixed_chunks"] += 1

                        logger.debug(f"[向量库修复] 修复chunk {chunk_id}: doc_id {current_doc_id} -> {correct_doc_id}")
                else:
                    # 内部逻辑：没有找到映射关系，记录警告
                    if current_doc_id and current_doc_id in doc_map:
                        # 内部逻辑：元数据中有doc_id，但没有VectorMapping记录
                        # 这种情况下，我们假设元数据是正确的
                        doc = doc_map[current_doc_id]
                        new_metadata = current_metadata.copy()
                        new_metadata["file_name"] = doc.file_name
                        new_metadata["source_type"] = doc.source_type

                        ids_to_update.append(chunk_id)
                        metadatas_to_update.append(new_metadata)
                        result["fixed_chunks"] += 1

                        logger.debug(f"[向量库修复] 更新chunk {chunk_id} 的文件名信息")
                    else:
                        logger.warning(f"[向量库修复] chunk {chunk_id} 没有找到对应的文档映射")

            # 内部逻辑：批量更新元数据
            if ids_to_update:
                vector_db.update_metadata(
                    ids=ids_to_update,
                    metadatas=metadatas_to_update
                )
                vector_db.persist()
                logger.info(f"[向量库修复] 成功修复 {len(ids_to_update)} 个chunk的元数据")

            return result

        except Exception as e:
            logger.error(f"[向量库修复] 修复过程出错: {str(e)}")
            result["errors"].append(str(e))
            return result

    @staticmethod
    async def get_vector_status(db) -> Dict[str, any]:
        """
        函数级注释：获取向量库状态信息
        内部逻辑：统计数据库和向量库的数据情况，用于诊断
        参数：
            db: 数据库会话
        返回值：Dict - 状态信息
        """
        # 内部变量：状态信息
        status = {
            "database_documents": 0,
            "database_chunks": 0,
            "vector_chunks": 0,
            "doc_id_distribution": {}
        }

        try:
            # 内部逻辑：统计数据库文档数
            doc_result = await db.execute(select(Document))
            documents = doc_result.scalars().all()
            status["database_documents"] = len(documents)

            # 内部逻辑：统计数据库chunk数
            chunk_result = await db.execute(select(VectorMapping))
            chunks = chunk_result.scalars().all()
            status["database_chunks"] = len(chunks)

            # 内部逻辑：统计向量库chunk数
            embeddings = IngestService.get_embeddings()
            vector_db = Chroma(
                persist_directory=settings.CHROMA_DB_PATH,
                embedding_function=embeddings,
                collection_name=settings.CHROMA_COLLECTION_NAME
            )
            all_data = vector_db.get()
            status["vector_chunks"] = len(all_data["ids"])

            # 内部逻辑：统计doc_id分布
            if all_data["metadatas"]:
                for metadata in all_data["metadatas"]:
                    doc_id = metadata.get("doc_id", 0)
                    status["doc_id_distribution"][str(doc_id)] = \
                        status["doc_id_distribution"].get(str(doc_id), 0) + 1

            return status

        except Exception as e:
            logger.error(f"[向量库状态] 获取状态失败: {str(e)}")
            status["error"] = str(e)
            return status
