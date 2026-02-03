"""
上海宇羲伏天智能科技有限公司出品

文件级注释：搜索服务层实现
内部逻辑：执行纯向量库检索及可选重排序（仅本地embedding时启用）
"""

from typing import List, Optional
from app.schemas.search import SearchResult
from app.core.config import settings
from langchain_community.embeddings import OllamaEmbeddings, HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from app.services.ingest_service import IngestService
from loguru import logger
import os

class SearchService:
    """
    类级注释：搜索服务类，提供基于向量库的语义检索及重排序功能
    """

    @staticmethod
    def _check_reranker_model_cached() -> bool:
        """
        函数级注释：检查重排序模型是否已缓存
        内部逻辑：检查 HuggingFace 缓存目录中是否存在模型文件
        返回值：bool - 模型是否已缓存
        """
        try:
            # 内部变量：获取 HuggingFace 缓存目录
            # 说明：通常在 ~/.cache/huggingface/hub/ 或通过 HF_HOME 环境变量指定
            cache_dir = os.environ.get("HF_HOME", os.path.expanduser("~/.cache/huggingface"))
            model_cache_path = os.path.join(cache_dir, "hub", "models--BAAI--bge-reranker-large")

            # 内部逻辑：检查模型缓存目录是否存在且不为空
            if os.path.exists(model_cache_path):
                # 内部逻辑：检查是否有模型文件（snapshot 或 safetensors）
                for item in os.listdir(model_cache_path):
                    if "snapshots" in item:
                        snapshot_dir = os.path.join(model_cache_path, item, "snapshots")
                        if os.path.exists(snapshot_dir):
                            snapshots = os.listdir(snapshot_dir)
                            if snapshots:
                                logger.debug(f"重排序模型已缓存: {snapshots[0]}")
                                return True

            logger.debug("重排序模型未缓存，将跳过重排序")
            return False
        except Exception as e:
            logger.warning(f"检查重排序模型缓存时出错: {str(e)}")
            return False

    @staticmethod
    def _should_use_reranking() -> bool:
        """
        函数级注释：判断是否应该使用重排序
        内部逻辑：使用本地 embedding（Ollama/local）时启用轻量级重排序
        返回值：bool - 是否启用重排序
        """
        # 内部逻辑：Guard Clause - 如果配置禁用了重排序
        if not settings.ENABLE_RERANKING:
            return False

        # 内部逻辑：检查是否使用本地 embedding 提供商
        # 说明：Ollama 和 local 都使用本地模型，可以用 embedding 做轻量级重排序
        # 云端提供商（zhipuai, openai）使用 API，不建议用本地 embedding 对云端结果重排序
        try:
            from app.utils.embedding_factory import EmbeddingFactory
            current_provider = EmbeddingFactory.get_current_provider()

            # 内部逻辑：只有本地模型提供商才考虑重排序
            if current_provider not in ["ollama", "local"]:
                logger.debug(f"当前 embedding 提供商为 {current_provider}（云端），跳过重排序")
                return False

            logger.debug(f"当前 embedding 提供商为 {current_provider}（本地），将使用 embedding 做轻量级重排序")
        except Exception:
            # 内部逻辑：如果无法获取提供商，保守起见跳过重排序
            logger.debug("无法获取 embedding 提供商，跳过重排序")
            return False

        return True

    @staticmethod
    def _rerank_with_embeddings(query: str, initial_results: list, embeddings) -> list:
        """
        函数级注释：使用 embedding 模型做轻量级重排序
        内部逻辑：计算 query 与每个 document 的向量相似度，按相似度重新排序
        参数：
            query: 查询文本
            initial_results: 初始搜索结果列表
            embeddings: embedding 模型实例
        返回值：重排序后的结果列表
        """
        import numpy as np

        try:
            # 内部变量：获取 query 的向量（embed_query 接受单个字符串，返回 List[float]）
            query_vector = embeddings.embed_query(query)

            # 内部逻辑：为每个 document 计算向量
            documents = [r["content"] for r in initial_results]
            doc_vectors = embeddings.embed_documents(documents)

            # 内部逻辑：计算 query 与每个 document 的余弦相似度
            rerank_scores = []
            for doc_vector in doc_vectors:
                # 内部逻辑：余弦相似度 = (A · B) / (||A|| * ||B||)
                similarity = float(np.dot(query_vector, doc_vector) / (
                    np.linalg.norm(query_vector) * np.linalg.norm(doc_vector)
                ))
                rerank_scores.append(similarity)

            # 内部逻辑：将重排序分数归一化到 0-1 范围
            min_score = min(rerank_scores)
            max_score = max(rerank_scores)
            score_range = max_score - min_score

            for i, raw_score in enumerate(rerank_scores):
                # 内部变量：归一化后的分数（0-1 范围）
                if score_range > 0:
                    normalized_score = (raw_score - min_score) / score_range
                else:
                    # 内部逻辑：如果所有分数相同，保持原分数
                    normalized_score = 0.5
                initial_results[i]["rerank_score"] = normalized_score

            # 内部逻辑：按重排序分数排序
            initial_results.sort(key=lambda x: x["rerank_score"], reverse=True)

            logger.info(f"Embedding重排序完成，相似度范围: [{min_score:.4f}, {max_score:.4f}]")
            return initial_results

        except Exception as e:
            # 内部逻辑：embedding 重排序失败时使用原始结果
            logger.warning(f"Embedding 重排序失败，使用原始结果: {str(e)}")
            return initial_results

    @staticmethod
    def _get_reranker():
        """
        函数级注释：获取重排序模型实例（已弃用，改用 embedding 重排序）
        内部逻辑：直接返回 None，使用 embedding 模型做轻量级重排序
        返回值：None（始终返回 None，改用 embedding 重排序）
        """
        # 内部逻辑：不再使用专门的重排序模型，改用 embedding 模型
        logger.debug("使用 embedding 模型做轻量级重排序（无需额外下载模型）")
        return None

    @staticmethod
    async def semantic_search(
        query: str,
        top_k: int = 5,
        enable_reranking: bool = True,
        db = None
    ) -> List[SearchResult]:
        """
        函数级注释：执行语义搜索逻辑（可选重排序）
        内部逻辑：初始化向量库 -> 执行相似度搜索 -> 可选重排序 -> 查询文件名 -> 转换结果格式
        参数：
            query: 搜索关键词
            top_k: 返回结果数量
            enable_reranking: 是否启用重排序（默认 True）
            db: 数据库会话（用于查询文件名，可选）
        返回值：List[SearchResult]
        """
        # 内部变量：记录搜索开始时间
        import time
        from sqlalchemy.future import select
        start_time = time.time()

        try:
            # 内部变量：初始化嵌入模型
            embeddings = IngestService.get_embeddings()

            # 内部逻辑：记录嵌入模型信息（用于诊断）
            try:
                from app.utils.embedding_factory import EmbeddingFactory
                current_provider = EmbeddingFactory.get_current_provider()
                current_model = EmbeddingFactory.get_current_model()
                logger.info(f"[搜索诊断] 使用 EmbeddingFactory - 提供商: {current_provider}, 模型: {current_model}")
            except Exception:
                logger.info(f"[搜索诊断] 使用 IngestService 直接获取 Embeddings")

            # 内部变量：加载向量库
            vector_db = Chroma(
                persist_directory=settings.CHROMA_DB_PATH,
                embedding_function=embeddings,
                collection_name=settings.CHROMA_COLLECTION_NAME
            )

            # 内部逻辑：记录向量库信息（用于诊断）
            logger.debug(f"[搜索诊断] 向量库路径: {settings.CHROMA_DB_PATH}, 集合名: {settings.CHROMA_COLLECTION_NAME}")

            # 内部逻辑：执行初始检索（获取更多候选结果用于重排序）
            # 内部变量：检索到的文档及其评分
            # 内部逻辑：如果启用重排序，获取更多候选结果（如 top_k * 2）
            initial_k = top_k * 2 if enable_reranking else top_k
            logger.debug(f"[搜索诊断] 搜索查询: '{query}', 请求结果数: {initial_k}")

            results = vector_db.similarity_search_with_score(query, k=initial_k)

            # 内部逻辑：记录搜索结果数量
            logger.debug(f"[搜索诊断] 实际检索到 {len(results)} 个结果")

            # 内部逻辑：Guard Clause - 如果没搜到则返回空列表，并记录诊断信息
            if not results:
                logger.warning(f"""
[搜索诊断] 搜索结果为空！可能的原因：
1. 向量库中没有任何数据（请先上传文件）
2. 嵌入模型不匹配（保存时和搜索时使用的模型不同）
3. 查询关键词与向量库中的内容语义差异较大

搜索参数：
  - 查询词: {query}
  - 向量库路径: {settings.CHROMA_DB_PATH}
  - 集合名: {settings.CHROMA_COLLECTION_NAME}
  - 请求结果数: {initial_k}
                """)
                return []

            # 内部逻辑：收集所有文档ID，用于批量查询文件名
            doc_ids = set()
            initial_results = []
            for doc, score in results:
                doc_id = doc.metadata.get("doc_id", 0)
                doc_ids.add(doc_id)
                initial_results.append({
                    "doc": doc,
                    "content": doc.page_content,
                    "doc_id": doc_id,
                    "score": 1.0 - score  # Chroma 返回的是距离，此处转换为相关度分值
                })

            # 内部变量：存储文档ID到文件名的映射
            doc_info_map = {}
            if db and doc_ids:
                try:
                    from app.models.models import Document
                    # 内部逻辑：批量查询文档信息
                    doc_result = await db.execute(
                        select(Document).where(Document.id.in_(list(doc_ids)))
                    )
                    documents = doc_result.scalars().all()
                    # 内部逻辑：构建ID到文件名的映射
                    for doc in documents:
                        doc_info_map[doc.id] = {
                            "file_name": doc.file_name,
                            "source_type": doc.source_type
                        }
                    logger.debug(f"[搜索诊断] 查询到 {len(doc_info_map)} 个文档的文件名")
                except Exception as e:
                    logger.warning(f"[搜索诊断] 查询文件名失败: {str(e)}")

            # 内部逻辑：将文件名信息添加到搜索结果中
            for result in initial_results:
                doc_info = doc_info_map.get(result["doc_id"])
                if doc_info:
                    result["file_name"] = doc_info["file_name"]
                    result["source_type"] = doc_info["source_type"]
                else:
                    result["file_name"] = None
                    result["source_type"] = None

            # 内部逻辑：如果启用重排序，则使用 embedding 模型做轻量级重排序
            if enable_reranking:
                if SearchService._should_use_reranking():
                    # 内部逻辑：使用 embedding 模型做轻量级重排序
                    # 说明：不需要额外下载重排序模型，直接用已有的 embedding 模型计算相似度
                    initial_results = SearchService._rerank_with_embeddings(query, initial_results, embeddings)
                    # 内部逻辑：只返回 top_k 个结果
                    initial_results = initial_results[:top_k]
                else:
                    # 内部逻辑：不满足重排序条件，使用原始结果
                    initial_results = initial_results[:top_k]
            else:
                # 内部逻辑：未启用重排序时，直接返回原始结果
                initial_results = initial_results[:top_k]

            # 内部逻辑：记录搜索耗时
            elapsed_time = time.time() - start_time
            logger.info(f"[搜索诊断] 搜索完成，返回 {len(initial_results)} 个结果，耗时: {elapsed_time:.2f}秒")

            # 内部逻辑：格式化最终输出
            return [
                SearchResult(
                    doc_id=r["doc_id"],
                    file_name=r.get("file_name"),
                    source_type=r.get("source_type"),
                    content=r["content"],
                    score=r.get("rerank_score", r["score"])  # 优先使用重排序分数
                )
                for r in initial_results
            ]

        except Exception as e:
            # 内部逻辑：捕获并记录异常，便于诊断
            logger.error(f"""
[搜索诊断] 搜索过程发生异常！
  - 查询词: {query}
  - 异常类型: {type(e).__name__}
  - 异常信息: {str(e)}
            """)
            # 内部逻辑：重新抛出异常，让上层处理
            raise
