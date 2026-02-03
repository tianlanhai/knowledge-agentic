"""
上海宇羲伏天智能科技有限公司出品

文件级注释：知识摄入服务层实现
内部逻辑：处理文件解析、向量化及元数据持久化
"""

import hashlib
import json
import os
import uuid
from typing import List, Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.ingest import IngestResponse
from app.schemas.document import DocumentListResponse, DocumentRead
from app.models.models import Document, VectorMapping, IngestTask, TaskStatus
from sqlalchemy.future import select
from sqlalchemy import func
from app.core.config import settings
from loguru import logger

# 内部逻辑：集成 LangChain 相关组件
# 说明：使用轻量级文档加载器，避免 unstructured 依赖（体积约 4-5GB）
from langchain_community.document_loaders import (
    PyPDFLoader,           # PDF 文档加载器
    Docx2txtLoader,        # DOCX 文档加载器
    TextLoader,            # 文本文件加载器
    WebBaseLoader,         # 网页加载器
    SQLDatabaseLoader      # 数据库加载器
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings, HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.utilities import SQLDatabase
from app.schemas.ingest import IngestResponse, DBIngestRequest

# 说明：智谱AI Embeddings（生产环境使用，无需本地模型）
from app.utils.zhipuai_embeddings import ZhipuAIEmbeddings

class IngestService:
    """
    类级注释：摄入服务类，提供文档解析、向量化及持久化核心逻辑
    """

    @staticmethod
    async def create_task(
        db: AsyncSession,
        file_name: str,
        source_type: str,
        file_path: str = None,
        file_hash: str = None,
        tags: str = None
    ) -> IngestTask:
        """
        函数级注释：创建新的摄入任务
        参数：
            db: 数据库异步会话
            file_name: 文件名
            source_type: 来源类型
            file_path: 文件路径（可选）
            file_hash: 文件哈希（可选）
            tags: 标签（可选）
        返回值：IngestTask - 创建的任务对象
        """
        # 内部逻辑：创建新任务
        task = IngestTask(
            file_name=file_name,
            file_path=file_path,
            file_hash=file_hash,
            source_type=source_type,
            tags=tags,
            status=TaskStatus.PENDING,
            progress=0
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task

    @staticmethod
    async def update_task_status(
        db: AsyncSession,
        task_id: int,
        status: TaskStatus,
        progress: int = None,
        error_message: str = None,
        document_id: int = None
    ):
        """
        函数级注释：更新任务状态
        参数：
            db: 数据库异步会话
            task_id: 任务ID
            status: 新状态
            progress: 进度（可选）
            error_message: 错误信息（可选）
            document_id: 关联文档ID（可选）
        """
        # 内部逻辑：查询任务
        result = await db.execute(select(IngestTask).where(IngestTask.id == task_id))
        task = result.scalar_one_or_none()
        
        # 内部逻辑：更新任务状态
        if task:
            task.status = status
            if progress is not None:
                task.progress = progress
            if error_message is not None:
                task.error_message = error_message
            if document_id is not None:
                task.document_id = document_id
            await db.commit()

    @staticmethod
    async def get_task(db: AsyncSession, task_id: int) -> IngestTask:
        """
        函数级注释：获取任务详情
        参数：
            db: 数据库异步会话
            task_id: 任务ID
        返回值：IngestTask - 任务对象
        """
        # 内部逻辑：查询任务
        result = await db.execute(select(IngestTask).where(IngestTask.id == task_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_tasks(db: AsyncSession, skip: int = 0, limit: int = 10) -> list:
        """
        函数级注释：获取所有任务列表
        内部逻辑：查询任务列表，按更新时间倒序排列，添加异常处理
        参数：
            db: 数据库异步会话
            skip: 跳过数量
            limit: 返回数量
        返回值：list - 任务列表
        """
        try:
            # 内部逻辑：查询任务列表，按更新时间倒序排列
            result = await db.execute(
                select(IngestTask)
                .offset(skip)
                .limit(limit)
                .order_by(IngestTask.updated_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            # 内部逻辑：捕获查询异常并记录日志
            logger.error(f"获取任务列表失败: {str(e)}", exc_info=True)
            raise

    @staticmethod
    async def delete_task(db: AsyncSession, task_id: int) -> bool:
        """
        函数级注释：删除指定任务记录
        内部逻辑：仅删除任务记录，不影响已生成的文档和相关向量数据
        参数：
            db: 数据库异步会话
            task_id: 任务ID
        返回值：bool - 删除是否成功
        """
        try:
            # 内部逻辑：查询任务是否存在
            result = await db.execute(select(IngestTask).where(IngestTask.id == task_id))
            task = result.scalar_one_or_none()

            # 内部逻辑：Guard Clause - 任务不存在
            if task is None:
                return False

            # 内部逻辑：删除任务记录
            await db.delete(task)
            await db.commit()
            return True
        except Exception as e:
            # 内部逻辑：发生异常时回滚事务
            await db.rollback()
            logger.error(f"删除任务失败: {str(e)}", exc_info=True)
            return False

    @staticmethod
    def _get_document_loader(file_path: str):
        """
        函数级注释：根据文件扩展名获取合适的文档加载器
        参数：file_path - 文件路径
        返回值：DocumentLoader 实例
        """
        # 获取文件扩展名（小写）
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        # 根据扩展名选择加载器
        if ext == '.pdf':
            return PyPDFLoader(file_path)
        elif ext in ['.docx', '.doc']:
            return Docx2txtLoader(file_path)
        elif ext in ['.pptx', '.ppt']:
            # PPTX 使用 python-pptx 手动解析
            from app.utils.pptx_loader import PPTXLoader
            return PPTXLoader(file_path)
        elif ext in ['.xlsx', '.xls']:
            # Excel 使用 openpyxl 手动解析
            from app.utils.excel_loader import ExcelLoader
            return ExcelLoader(file_path)
        elif ext in ['.txt', '.md']:
            # 文本文件直接读取
            from langchain_community.document_loaders import TextLoader
            return TextLoader(file_path, encoding='utf-8')
        else:
            # 默认尝试作为文本文件
            from langchain_community.document_loaders import TextLoader
            return TextLoader(file_path, encoding='utf-8')

    @staticmethod
    async def _calculate_hash(content: bytes) -> str:
        """
        函数级注释：计算文件内容的 SHA256 哈希值
        参数：content - 文件二进制内容
        返回值：str - 哈希值字符串
        """
        # 内部逻辑：使用 hashlib 生成 SHA256
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def get_embeddings():
        """
        函数级注释：根据配置获取 Embedding 实例
        内部逻辑：优先使用 EmbeddingFactory 运行时配置，支持热切换
        返回值：Embedding实例
        """
        # 内部逻辑：添加诊断日志 - 追踪方法调用
        logger.info(f"[诊断] >>> IngestService.get_embeddings 被调用")

        # 内部逻辑：优先使用 EmbeddingFactory，支持运行时配置热切换
        # 说明：这样可以保证搜索、对话和摄入使用相同的嵌入模型配置
        try:
            from app.utils.embedding_factory import EmbeddingFactory

            logger.info(f"[诊断] EmbeddingFactory 导入成功")

            # 内部逻辑：检查是否有运行时配置
            current_provider = EmbeddingFactory.get_current_provider()
            current_model = EmbeddingFactory.get_current_model()

            logger.info(f"[诊断] 使用 EmbeddingFactory 获取 Embeddings，提供商: {current_provider}，模型: {current_model}")
            logger.info(f"使用 EmbeddingFactory 获取 Embeddings，提供商: {current_provider}，模型: {current_model}")
            return EmbeddingFactory.create_embeddings()
        except ImportError as e:
            # 内部逻辑：降级到原来的实现（当 EmbeddingFactory 不可用时）
            logger.warning(f"[诊断] EmbeddingFactory 导入失败: {e}")
            logger.warning("EmbeddingFactory 不可用，降级到直接创建 Embeddings 实例")
            return IngestService._create_embeddings_fallback()
        except Exception as e:
            # 内部逻辑：捕获其他异常
            logger.error(f"[诊断] 获取 Embeddings 时发生异常: {e}")
            raise

    @staticmethod
    def _create_embeddings_fallback():
        """
        函数级注释：降级方法：直接创建 Embedding 实例
        内部逻辑：根据 EMBEDDING_PROVIDER 选择对应的 Embedding 服务（备用方案）
        返回值：Embedding实例
        说明：仅在 EmbeddingFactory 不可用时使用
        """
        provider = settings.EMBEDDING_PROVIDER.lower()

        # 内部逻辑：根据提供商选择 Embedding 实现
        if provider == "zhipuai":
            # 说明：使用智谱AI Embeddings API（生产环境推荐，无需本地模型）
            logger.info(f"[降级] 使用智谱AI Embeddings，模型: {settings.ZHIPUAI_EMBEDDING_MODEL}")
            return ZhipuAIEmbeddings(
                api_key=settings.ZHIPUAI_API_KEY,
                model=settings.ZHIPUAI_EMBEDDING_MODEL
            )
        elif provider == "local":
            # 说明：使用本地 HuggingFace 模型（需要 torch/sentence-transformers）
            model_kwargs = {'device': settings.DEVICE if settings.DEVICE != "auto" else "cpu"}
            try:
                import torch
                if settings.DEVICE == "auto":
                    model_kwargs['device'] = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                model_kwargs['device'] = "cpu"

            # 内部逻辑：设置离线模式环境变量，替代 local_files_only 参数
            import os
            os.environ['TRANSFORMERS_OFFLINE'] = '1'

            return HuggingFaceEmbeddings(
                model_name=settings.LOCAL_EMBEDDING_MODEL_PATH,
                model_kwargs=model_kwargs,
                encode_kwargs={'normalize_embeddings': True}
            )
        else:  # ollama 或默认
            # 说明：使用 Ollama Embeddings API
            logger.info(f"[降级] 使用 Ollama Embeddings，模型: {settings.EMBEDDING_MODEL}")
            return OllamaEmbeddings(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.EMBEDDING_MODEL
            )

    @staticmethod
    async def process_file(
        db: AsyncSession, 
        file: UploadFile, 
        tags: Optional[List[str]] = None,
        task_id: int = None
    ) -> IngestResponse:
        """
        函数级注释：处理文件上传逻辑（支持异步任务）
        内部逻辑：计算哈希 -> 查重 -> 解析内容 -> 切分文本 -> 生成向量 -> 存入数据库
        参数：
            db: 数据库异步会话
            file: 上传的文件对象
            tags: 标签列表
            task_id: 任务ID（可选，用于异步处理）
        返回值：IngestResponse
        """
        # 内部逻辑：更新任务状态为处理中
        if task_id:
            await IngestService.update_task_status(db, task_id, TaskStatus.PROCESSING, progress=10)
        
        # 内部逻辑：Mock 模式处理 (Guard Clause)
        if settings.USE_MOCK:
            logger.info(f"Mock 模式下模拟处理文件: {file.filename}")
            if task_id:
                await IngestService.update_task_status(db, task_id, TaskStatus.COMPLETED, progress=100)
            return IngestResponse(
                document_id=999, 
                status="completed", 
                chunk_count=10
            )

        # 内部变量：读取文件内容用于计算哈希
        content = await file.read()
        file_hash = await IngestService._calculate_hash(content)
        
        # 内部逻辑：更新任务进度
        if task_id:
            await IngestService.update_task_status(db, task_id, TaskStatus.PROCESSING, progress=20)
        
        # 内部逻辑：检查数据库中是否已存在相同哈希的文档 (Guard Clause)
        existing_doc_query = await db.execute(select(Document).where(Document.file_hash == file_hash))
        existing_doc = existing_doc_query.scalar_one_or_none()
        
        if existing_doc:
            logger.info(f"文件已存在，跳过处理: {file.filename}")
            if task_id:
                await IngestService.update_task_status(db, task_id, TaskStatus.COMPLETED, progress=100, document_id=existing_doc.id)
            return IngestResponse(
                document_id=existing_doc.id,
                status="completed",
                chunk_count=0
            )

        # 内部逻辑：确保上传目录存在
        os.makedirs(settings.UPLOAD_FILES_PATH, exist_ok=True)

        # 内部变量：生成唯一文件名，防止同名文件覆盖
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        save_path = os.path.join(settings.UPLOAD_FILES_PATH, unique_filename)

        # 内部逻辑：保存文件到指定目录
        with open(save_path, "wb") as f:
            f.write(content)
        
        # 内部逻辑：更新任务进度
        if task_id:
            await IngestService.update_task_status(db, task_id, TaskStatus.PROCESSING, progress=30)

        try:
            # 内部逻辑：使用轻量级文档加载器解析文档（避免 unstructured）
            loader = IngestService._get_document_loader(save_path)
            docs = loader.load()
            
            # 内部逻辑：更新任务进度
            if task_id:
                await IngestService.update_task_status(db, task_id, TaskStatus.PROCESSING, progress=50)

            # 内部逻辑：文本切分
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            chunks = text_splitter.split_documents(docs)

            # 内部逻辑：保存元数据到 SQLite
            new_doc = Document(
                file_name=file.filename,
                file_path=save_path,  # 保存实际存储路径
                file_hash=file_hash,
                source_type="FILE",
                tags=json.dumps(tags) if tags else None
            )
            db.add(new_doc)
            await db.flush()  # 获取 ID，用于元数据追踪

            # 内部逻辑：更新任务进度
            if task_id:
                await IngestService.update_task_status(db, task_id, TaskStatus.PROCESSING, progress=60, document_id=new_doc.id)

            # 内部逻辑：为每个 chunk 添加 document_id 元数据，确保 RAG 溯源准确
            for chunk in chunks:
                chunk.metadata["doc_id"] = new_doc.id

            # 内部逻辑：向量化并存入 ChromaDB
            embeddings = IngestService.get_embeddings()

            vector_db = Chroma.from_documents(
                documents=chunks,
                embedding=embeddings,
                persist_directory=settings.CHROMA_DB_PATH,
                collection_name=settings.CHROMA_COLLECTION_NAME
            )
            vector_db.persist()
            
            # 内部逻辑：更新任务进度
            if task_id:
                await IngestService.update_task_status(db, task_id, TaskStatus.PROCESSING, progress=80)

            # 内部逻辑：保存向量映射关系
            for i, chunk in enumerate(chunks):
                mapping = VectorMapping(
                    document_id=new_doc.id,
                    chunk_id=f"{new_doc.id}_{i}",
                    chunk_content=chunk.page_content
                )
                db.add(mapping)

            await db.commit()
            
            # 内部逻辑：更新任务状态为完成
            if task_id:
                await IngestService.update_task_status(db, task_id, TaskStatus.COMPLETED, progress=100)

            logger.info(f"文件处理成功: {file.filename} -> {save_path}")
            return IngestResponse(
                document_id=new_doc.id,
                status="completed",
                chunk_count=len(chunks)
            )

        except Exception as e:
            logger.error(f"处理文件失败: {str(e)}")
            await db.rollback()
            
            # 内部逻辑：处理失败时删除已保存的文件
            if os.path.exists(save_path):
                os.remove(save_path)
            
            # 内部逻辑：更新任务状态为失败
            if task_id:
                await IngestService.update_task_status(db, task_id, TaskStatus.FAILED, error_message=str(e))
            
            raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")

    @staticmethod
    async def process_url(
        db: AsyncSession,
        url: str,
        tags: Optional[List[str]] = None,
        task_id: int | None = None
    ) -> IngestResponse:
        """
        函数级注释：处理网页抓取逻辑
        内部逻辑：抓取网页 -> 正文提取 -> 向量化 -> 存入数据库
        参数：
            db: 数据库异步会话
            url: 目标 URL
            tags: 可选标签
            task_id: 任务ID（可选，用于异步处理时更新任务状态）
        返回值：IngestResponse
        """
        # 内部逻辑：更新任务状态为处理中
        if task_id:
            await IngestService.update_task_status(db, task_id, TaskStatus.PROCESSING, progress=10)

        # 内部逻辑：Mock 模式处理 (Guard Clause)
        if settings.USE_MOCK:
            logger.info(f"Mock 模式下模拟抓取 URL: {url}")
            if task_id:
                await IngestService.update_task_status(db, task_id, TaskStatus.COMPLETED, progress=100)
            return IngestResponse(
                document_id=888,
                status="completed",
                chunk_count=5
            )

        # 内部变量：使用 URL 生成哈希用于查重
        url_hash = hashlib.sha256(url.encode()).hexdigest()
        
        # 内部逻辑：查重 (Guard Clause)
        existing_doc_query = await db.execute(select(Document).where(Document.file_hash == url_hash))
        existing_doc = existing_doc_query.scalar_one_or_none()

        if existing_doc:
            logger.info(f"URL 已存在，跳过处理: {url}")
            if task_id:
                await IngestService.update_task_status(db, task_id, TaskStatus.COMPLETED, progress=100, document_id=existing_doc.id)
            return IngestResponse(document_id=existing_doc.id, status="completed", chunk_count=0)

        try:
            # 内部逻辑：使用 WebBaseLoader 抓取网页（轻量级替代方案）
            loader = WebBaseLoader(url)
            docs = loader.load()
            
            # 内部逻辑：尝试提取网页标题作为文件名
            page_title = url
            if docs and docs[0].metadata.get("title"):
                page_title = docs[0].metadata["title"]
            elif docs and docs[0].metadata.get("source"):
                page_title = os.path.basename(docs[0].metadata["source"])

            # 内部逻辑：文本切分
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = text_splitter.split_documents(docs)
            
            # 内部逻辑：保存元数据
            new_doc = Document(
                file_name=page_title,
                file_path=url,
                file_hash=url_hash,
                source_type="WEB",
                tags=json.dumps(tags) if tags else None
            )
            db.add(new_doc)
            await db.flush() # 获取 ID 用于追踪

            # 内部逻辑：更新任务进度并写入 document_id
            if task_id:
                await IngestService.update_task_status(db, task_id, TaskStatus.PROCESSING, progress=60, document_id=new_doc.id)

            # 内部逻辑：为 chunk 添加 doc_id 元数据
            for chunk in chunks:
                chunk.metadata["doc_id"] = new_doc.id

            # 内部逻辑：向量化
            embeddings = IngestService.get_embeddings()

            vector_db = Chroma.from_documents(
                documents=chunks,
                embedding=embeddings,
                persist_directory=settings.CHROMA_DB_PATH,
                collection_name=settings.CHROMA_COLLECTION_NAME
            )
            vector_db.persist()

            # 内部逻辑：保存向量映射
            for i, chunk in enumerate(chunks):
                mapping = VectorMapping(
                    document_id=new_doc.id,
                    chunk_id=f"{new_doc.id}_{i}",
                    chunk_content=chunk.page_content
                )
                db.add(mapping)

            await db.commit()

            # 内部逻辑：更新任务状态为完成
            if task_id:
                await IngestService.update_task_status(db, task_id, TaskStatus.COMPLETED, progress=100)

            return IngestResponse(
                document_id=new_doc.id,
                status="completed",
                chunk_count=len(chunks)
            )
            
        except Exception as e:
            logger.error(f"处理 URL 失败: {str(e)}")
            await db.rollback()

            # 内部逻辑：更新任务状态为失败
            if task_id:
                await IngestService.update_task_status(db, task_id, TaskStatus.FAILED, error_message=str(e))

            raise HTTPException(status_code=500, detail=f"URL 处理失败: {str(e)}")

    @staticmethod
    async def process_db(
        db: AsyncSession,
        request: DBIngestRequest,
        task_id: int | None = None
    ) -> IngestResponse:
        """
        函数级注释：处理数据库记录摄入逻辑
        内部逻辑：连接库 -> 执行查询 -> 转换为文档 -> 向量化存储
        参数：
            db: 数据库异步会话
            request: 包含连接信息和表名的请求对象
            task_id: 任务ID（可选，用于异步处理时更新任务状态）
        返回值：IngestResponse
        """
        # 内部逻辑：更新任务状态为处理中
        if task_id:
            await IngestService.update_task_status(db, task_id, TaskStatus.PROCESSING, progress=10)

        # 内部逻辑：Mock 模式处理 (Guard Clause)
        if settings.USE_MOCK:
            logger.info(f"Mock 模式下模拟同步数据库: {request.table_name}")
            if task_id:
                await IngestService.update_task_status(db, task_id, TaskStatus.COMPLETED, progress=100)
            return IngestResponse(
                document_id=777,
                status="completed",
                chunk_count=20
            )

        # 内部变量：使用连接字符串和表名生成哈希，用于幂等校验
        db_hash = hashlib.sha256(f"{request.connection_uri}_{request.table_name}".encode()).hexdigest()
        
        # 内部逻辑：查重 (Guard Clause)
        existing_doc_query = await db.execute(select(Document).where(Document.file_hash == db_hash))
        existing_doc = existing_doc_query.scalar_one_or_none()

        if existing_doc:
            logger.info(f"数据库同步配置已存在，跳过处理: {request.table_name}")
            if task_id:
                await IngestService.update_task_status(db, task_id, TaskStatus.COMPLETED, progress=100, document_id=existing_doc.id)
            return IngestResponse(document_id=existing_doc.id, status="completed", chunk_count=0)

        try:
            # 内部逻辑：配置 SQL 加载器
            engine = SQLDatabase.from_uri(request.connection_uri)
            loader = SQLDatabaseLoader(
                query=f"SELECT * FROM {request.table_name}",
                db=engine,
                source_columns=[request.content_column]
            )
            docs = loader.load()
            
            # 内部逻辑：文本切分 (针对长记录)
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = text_splitter.split_documents(docs)
            
            # 内部逻辑：保存元数据到 SQLite 提前获取 ID
            new_doc = Document(
                file_name=f"DB:{request.table_name}",
                file_path=request.connection_uri,
                file_hash=db_hash,
                source_type="DB"
            )
            db.add(new_doc)
            await db.flush()

            # 内部逻辑：更新任务进度并写入 document_id
            if task_id:
                await IngestService.update_task_status(db, task_id, TaskStatus.PROCESSING, progress=60, document_id=new_doc.id)

            # 内部逻辑：为 chunk 添加 doc_id 元数据
            for chunk in chunks:
                chunk.metadata["doc_id"] = new_doc.id

            # 内部逻辑：向量化
            embeddings = IngestService.get_embeddings()

            vector_db = Chroma.from_documents(
                documents=chunks,
                embedding=embeddings,
                persist_directory=settings.CHROMA_DB_PATH,
                collection_name=settings.CHROMA_COLLECTION_NAME
            )
            vector_db.persist()

            # 内部逻辑：保存映射关系
            for i, chunk in enumerate(chunks):
                mapping = VectorMapping(
                    document_id=new_doc.id,
                    chunk_id=f"{new_doc.id}_{i}",
                    chunk_content=chunk.page_content
                )
                db.add(mapping)

            await db.commit()

            # 内部逻辑：更新任务状态为完成
            if task_id:
                await IngestService.update_task_status(db, task_id, TaskStatus.COMPLETED, progress=100)

            return IngestResponse(
                document_id=new_doc.id,
                status="completed",
                chunk_count=len(chunks)
            )
            
        except Exception as e:
            logger.error(f"处理数据库同步失败: {str(e)}")
            await db.rollback()

            # 内部逻辑：更新任务状态为失败
            if task_id:
                await IngestService.update_task_status(db, task_id, TaskStatus.FAILED, error_message=str(e))

            raise HTTPException(status_code=500, detail=f"数据库同步失败: {str(e)}")

    @staticmethod
    async def get_documents(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 10,
        search: str = None
    ) -> DocumentListResponse:
        """
        函数级注释：获取已摄入文档的分页列表
        内部逻辑：查询数据库总记录数 -> 执行分页查询 -> 统计每个文档的片段数量 -> 转换为响应模型
        参数：
            db: 数据库异步会话
            skip: 跳过记录数（用于分页）
            limit: 返回记录限制数
            search: 搜索关键词（可选）
        返回值：DocumentListResponse
        """
        try:
            # 内部逻辑：构建基础查询
            base_query = select(Document)

            # 内部逻辑：如果提供了搜索关键词，添加过滤条件
            if search:
                # 内部逻辑：在文件名中搜索
                search_pattern = f"%{search}%"
                base_query = base_query.where(Document.file_name.like(search_pattern))

            # 内部逻辑：查询文档总数
            total_query = await db.execute(select(func.count()).select_from(base_query.subquery()))
            total = total_query.scalar() or 0

            # 内部逻辑：按修改时间倒序分页查询
            # 内部变量：执行分页 select 查询
            result = await db.execute(
                base_query.offset(skip).limit(limit).order_by(Document.updated_at.desc())
            )
            documents = result.scalars().all()

            # 内部逻辑：批量查询所有文档的片段数量（避免 N+1 查询问题）
            document_ids = [doc.id for doc in documents]
            chunk_count_result = await db.execute(
                select(VectorMapping.document_id, func.count(VectorMapping.id))
                .group_by(VectorMapping.document_id)
                .where(VectorMapping.document_id.in_(document_ids))
            )
            # 内部变量：构建文档ID到片段数量的映射字典
            chunk_count_dict = {row[0]: row[1] for row in chunk_count_result.all()}

            # 内部逻辑：构建文档列表
            document_list = []
            for doc in documents:
                # 内部变量：从字典获取片段数量，不存在则为0
                chunk_count = chunk_count_dict.get(doc.id, 0)

                # 内部变量：构建文档对象
                # 内部逻辑：解析tags字段，如果是JSON字符串则转换为列表
                tags_value = doc.tags
                if tags_value and isinstance(tags_value, str):
                    try:
                        import json
                        tags_value = json.loads(tags_value)
                    except (json.JSONDecodeError, TypeError):
                        tags_value = None

                document_dict = {
                    "id": doc.id,
                    "file_name": doc.file_name,
                    "source_type": doc.source_type,
                    "tags": tags_value,
                    "created_at": doc.created_at,
                    "chunk_count": chunk_count
                }

                # 内部逻辑：转换为 Pydantic 对象
                document_list.append(DocumentRead.model_validate(document_dict))

            # 内部逻辑：返回包含片段数量的文档列表
            return DocumentListResponse(
                items=document_list,
                total=total,
                skip=skip,
                limit=limit
            )

        except Exception as e:
            # 内部逻辑：捕获异常并记录详细错误日志
            logger.error(f"查询文档列表失败: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"查询文档列表失败: {str(e)}")

    @staticmethod
    async def process_file_background(
        task_id: int,
        file_path: str,
        file_name: str,
        tags: Optional[List[str]] = None
    ):
        """
        函数级注释：后台处理文件（用于异步任务）
        参数：
            task_id: 任务ID
            file_path: 文件路径
            file_name: 文件名
            tags: 标签列表
        """
        import app.db.session as session_module

        logger.info(f"开始后台处理文件任务: {task_id}, 文件: {file_name}")

        # 内部逻辑：确保会话工厂已初始化
        if session_module.AsyncSessionLocal is None:
            await session_module.init_session_factory()

        # 内部逻辑：使用会话工厂直接创建会话，确保后台任务有独立的数据库连接
        async with session_module.AsyncSessionLocal() as db:
            try:
                # 内部逻辑：创建临时文件对象
                class TempFile:
                    def __init__(self, path, name):
                        self.filename = name
                        self.path = path
                    
                    async def read(self):
                        with open(self.path, 'rb') as f:
                            return f.read()
                
                temp_file = TempFile(file_path, file_name)
                
                # 内部逻辑：调用处理方法
                await IngestService.process_file(db, temp_file, tags, task_id)
                
                logger.info(f"后台处理文件任务完成: {task_id}")
                
            except Exception as e:
                logger.error(f"后台处理文件失败: {task_id}, 错误: {str(e)}")
                # 再次获取会话以防万一
                try:
                    await IngestService.update_task_status(db, task_id, TaskStatus.FAILED, error_message=str(e))
                    await db.commit()
                except Exception as update_error:
                    logger.error(f"更新任务失败状态时出错: {str(update_error)}")
                await db.rollback()

    @staticmethod
    async def delete_document(db: AsyncSession, doc_id: int) -> bool:
        """
        函数级注释：删除文档及其关联的所有向量索引和映射
        内部逻辑：校验文档是否存在 -> 从 ChromaDB 删除索引 -> 从 SQLite 级联删除记录
        参数：
            db: 数据库异步会话
            doc_id: 文档唯一标识 ID
        返回值：bool - 是否删除成功
        """
        # 内部逻辑：查询文档是否存在
        # 内部变量：执行 select 查询获取文档对象
        result = await db.execute(select(Document).where(Document.id == doc_id))
        doc = result.scalar_one_or_none()
        
        # 内部逻辑：Guard Clause - 若文档不存在则返回失败
        if not doc:
            logger.warning(f"尝试删除不存在的文档: {doc_id}")
            return False

        try:
            # 内部逻辑：从 ChromaDB 中删除对应的向量
            # 内部变量：获取关联的所有 chunk_id
            mapping_result = await db.execute(select(VectorMapping.chunk_id).where(VectorMapping.document_id == doc_id))
            chunk_ids = mapping_result.scalars().all()
            
            if chunk_ids and not settings.USE_MOCK:
                embeddings = IngestService.get_embeddings()
                vector_db = Chroma(
                    persist_directory=settings.CHROMA_DB_PATH,
                    embedding_function=embeddings,
                    collection_name=settings.CHROMA_COLLECTION_NAME
                )
                # 内部逻辑：先获取匹配的向量 IDs，再删除（更可靠，避免 where 子句解析问题）
                result = vector_db.get(where={"doc_id": doc_id})
                if result["ids"]:
                    vector_db.delete(ids=result["ids"])
                    vector_db.persist()
                    logger.info(f"从 ChromaDB 删除了 {len(result['ids'])} 个向量")
                else:
                    logger.warning(f"ChromaDB 中未找到 doc_id={doc_id} 的向量")

            # 内部逻辑：从 SQLite 中删除文档记录 (级联删除会自动处理 VectorMapping)
            await db.delete(doc)
            await db.commit()
            
            logger.info(f"成功删除文档 ID: {doc_id}, 文件名: {doc.file_name}")
            return True
            
        except Exception as e:
            logger.error(f"删除文档失败: {str(e)}")
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"删除文档失败: {str(e)}")

    @staticmethod
    async def process_url_background(
        task_id: int,
        url: str,
        tags: Optional[List[str]] = None
    ):
        """
        函数级注释：后台处理网页抓取（用于异步任务）
        参数：
            task_id: 任务ID
            url: 网页URL
            tags: 标签列表
        """
        import app.db.session as session_module

        logger.info(f"开始后台处理网页抓取任务: {task_id}, URL: {url}")

        # 内部逻辑：确保会话工厂已初始化
        if session_module.AsyncSessionLocal is None:
            await session_module.init_session_factory()

        # 内部逻辑：使用会话工厂直接创建会话，确保后台任务有独立的数据库连接
        async with session_module.AsyncSessionLocal() as db:
            try:
                # 内部逻辑：调用处理方法（使用关键字参数，避免位置参数顺序问题）
                await IngestService.process_url(db=db, url=url, tags=tags, task_id=task_id)

                logger.info(f"后台处理网页抓取任务完成: {task_id}")

            except Exception as e:
                logger.error(f"后台处理网页抓取失败: {task_id}, 错误: {str(e)}")
                # 更新任务状态为失败
                try:
                    await IngestService.update_task_status(db, task_id, TaskStatus.FAILED, error_message=str(e))
                    await db.commit()
                except Exception as update_error:
                    logger.error(f"更新任务失败状态时出错: {str(update_error)}")
                await db.rollback()

    @staticmethod
    async def process_db_background(
        task_id: int,
        request: DBIngestRequest
    ):
        """
        函数级注释：后台处理数据库同步（用于异步任务）
        参数：
            task_id: 任务ID
            request: 数据库同步请求对象
        """
        import app.db.session as session_module

        logger.info(f"开始后台处理数据库同步任务: {task_id}, 表: {request.table_name}")

        # 内部逻辑：确保会话工厂已初始化
        if session_module.AsyncSessionLocal is None:
            await session_module.init_session_factory()

        # 内部逻辑：使用会话工厂直接创建会话，确保后台任务有独立的数据库连接
        async with session_module.AsyncSessionLocal() as db:
            try:
                # 内部逻辑：调用处理方法（使用关键字参数，避免位置参数顺序问题）
                await IngestService.process_db(db=db, request=request, task_id=task_id)
                logger.info(f"后台处理数据库同步任务完成: {task_id}")
            except Exception as e:
                logger.error(f"后台处理数据库同步失败: {task_id}, 错误: {str(e)}")
                # 更新任务状态为失败
                try:
                    await IngestService.update_task_status(db, task_id, TaskStatus.FAILED, error_message=str(e))
                    await db.commit()
                except Exception as update_error:
                    logger.error(f"更新任务失败状态时出错: {str(update_error)}")
                await db.rollback()