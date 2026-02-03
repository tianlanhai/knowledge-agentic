"""
上海宇羲伏天智能科技有限公司出品

文件级注释：来源信息处理模块
内部逻辑：处理对话回答中的来源信息，验证文档存在性，构建来源详情
设计模式：单一职责原则 - 专注于来源数据处理
"""

from typing import List, Dict, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from loguru import logger

from app.schemas.chat import SourceInfo
from app.models.models import Document, VectorMapping


class SourcesProcessor:
    """
    类级注释：来源信息处理器
    内部逻辑：统一处理RAG和Agent模式下的来源信息
    设计模式：单一职责原则 - 专注于来源数据处理
    职责：验证文档存在性、格式化来源信息、计算相关度评分
    """

    async def process(
        self,
        doc_ids: List[int],
        db: AsyncSession,
        documents: List = None
    ) -> List[SourceInfo]:
        """
        函数级注释：处理来源信息
        内部逻辑：验证文档存在性 -> 格式化来源信息 -> 计算评分
        参数：
            doc_ids - 文档ID列表
            db - 数据库异步会话
            documents - 可选的文档对象列表（用于RAG模式）
        返回值：List[SourceInfo] - 来源信息列表
        """
        # Guard Clauses：无文档ID时返回空列表
        if not doc_ids:
            return []

        # 内部逻辑：批量查询文档信息
        file_names = {}
        valid_doc_ids = set()  # 内部变量：记录存在的文档ID

        if doc_ids:
            doc_result = await db.execute(
                select(Document.id, Document.file_name).where(
                    Document.id.in_(doc_ids)
                )
            )
            for row in doc_result.all():
                file_names[row[0]] = row[1]
                valid_doc_ids.add(row[0])

        # 内部逻辑：记录被过滤掉的无效文档ID
        invalid_doc_ids = set(doc_ids) - valid_doc_ids
        if invalid_doc_ids:
            logger.warning(
                f"检测到已删除文档的向量引用: {invalid_doc_ids}，已过滤"
            )

        # 内部逻辑：构建来源信息列表
        sources = []

        # 内部逻辑：RAG模式使用documents参数
        if documents:
            for idx, doc in enumerate(documents):
                doc_id = doc.metadata.get("doc_id", 0)

                # Guard Clauses：跳过无效文档ID
                if doc_id not in valid_doc_ids:
                    logger.debug(
                        f"跳过无效文档ID: {doc_id}（文档已被删除）"
                    )
                    continue

                # 内部逻辑：计算相关度评分
                score = 1.0 - (idx * 0.1)

                sources.append(SourceInfo(
                    doc_id=doc_id,
                    file_name=file_names.get(doc_id, "未知文档"),
                    text_segment=doc.page_content[:200] + "...",
                    score=score
                ))
        else:
            # 内部逻辑：Agent模式需要额外查询内容
            doc_info = {}
            if doc_ids:
                doc_result = await db.execute(
                    select(
                        Document.id,
                        Document.file_name,
                        VectorMapping.chunk_content
                    )
                    .join(VectorMapping, Document.id == VectorMapping.document_id)
                    .where(Document.id.in_(doc_ids))
                )
                for row in doc_result.all():
                    doc_info[row[0]] = {
                        "file_name": row[1],
                        "content": row[2]
                    }

            for idx, doc_id in enumerate(doc_ids):
                # Guard Clauses：跳过无效文档ID
                if doc_id not in valid_doc_ids:
                    logger.debug(
                        f"跳过无效文档ID: {doc_id}（文档已被删除）"
                    )
                    continue

                info = doc_info.get(
                    doc_id,
                    {"file_name": "未知文档", "content": "无片段内容"}
                )
                segment = info.get("content", "无片段内容")
                score = 1.0 - (idx * 0.1)

                sources.append(SourceInfo(
                    doc_id=doc_id,
                    file_name=info.get("file_name", "未知文档"),
                    text_segment=segment[:200] + "...",
                    score=score
                ))

        return sources
