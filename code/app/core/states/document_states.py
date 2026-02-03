# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：文档处理状态模式模块
内部逻辑：使用状态模式管理文档处理流程（上传→解析→分块→向量化→完成）
设计模式：状态模式（State Pattern）
设计原则：开闭原则、单一职责原则

状态转换图：
    UploadedState
         ↓ (验证成功)
    ParsingState
         ↓ (解析成功)
    ChunkingState
         ↓ (分块完成)
    VectorizingState
         ↓ (向量化完成)
    CompletedState
         ↓ (任何失败)
    FailedState
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
import time


class DocumentProcessingException(Exception):
    """
    类级注释：文档处理异常
    内部逻辑：封装文档处理过程中的错误信息
    """
    def __init__(self, message: str, current_state: str, error_code: str = "PROCESSING_ERROR"):
        self.message = message
        self.current_state = current_state
        self.error_code = error_code
        super().__init__(message)


class ProcessingStage(str, Enum):
    """
    类级注释：处理阶段枚举
    内部逻辑：定义文档处理的所有阶段
    """
    # 已上传
    UPLOADED = "uploaded"
    # 解析中
    PARSING = "parsing"
    # 分块中
    CHUNKING = "chunking"
    # 向量化中
    VECTORIZING = "vectorizing"
    # 已完成
    COMPLETED = "completed"
    # 失败
    FAILED = "failed"


@dataclass
class ProcessingResult:
    """
    类级注释：处理结果数据类
    内部逻辑：封装每个阶段的处理结果
    """
    # 属性：是否成功
    success: bool
    # 属性：结果数据
    data: Any = None
    # 属性：错误信息
    error: Optional[str] = None
    # 属性：处理时长
    duration: float = 0.0
    # 属性：元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def stage_info(self) -> str:
        """获取阶段信息"""
        if self.success:
            return f"成功: 处理了 {self.data if isinstance(self.data, (int, str)) else '数据'}"
        return f"失败: {self.error}"

    @property
    def is_valid(self) -> bool:
        """
        函数级注释：检查结果是否有效
        返回值：是否成功且无错误
        """
        return self.success and self.error is None


class DocumentState(ABC):
    """
    类级注释：文档处理状态抽象基类
    内部逻辑：定义所有状态的统一接口
    设计模式：状态模式 - 抽象状态
    """

    @property
    def stage(self) -> ProcessingStage:
        """
        函数级注释：获取当前处理阶段
        返回值：处理阶段枚举
        """
        return ProcessingStage.UPLOADED

    @abstractmethod
    async def next(self, context: 'DocumentContext') -> 'DocumentState':
        """
        函数级注释：转换到下一个状态
        内部逻辑：由子类实现具体的状态转换逻辑
        参数：
            context - 文档上下文对象
        返回值：下一个状态对象
        """
        pass

    @abstractmethod
    def can_process(self) -> bool:
        """
        函数级注释：检查当前状态是否可以进行处理
        返回值：是否可以处理
        """
        pass

    @abstractmethod
    def can_retry(self) -> bool:
        """
        函数级注释：检查是否可以重试
        返回值：是否可以重试
        """
        pass

    @abstractmethod
    def is_terminal(self) -> bool:
        """
        函数级注释：检查是否为终止状态
        返回值：是否为终止状态
        """
        pass

    def get_description(self) -> str:
        """
        函数级注释：获取状态描述
        返回值：状态描述字符串
        """
        return f"{self.__class__.__name__}"


class UploadedState(DocumentState):
    """
    类级注释：已上传状态
    内部逻辑：文件上传后的初始状态，进行验证
    设计模式：状态模式 - 具体状态
    """

    def __init__(self, validation_func: Optional[Callable] = None):
        """
        函数级注释：初始化已上传状态
        参数：
            validation_func - 自定义验证函数
        """
        self._validation_func = validation_func

    @property
    def stage(self) -> ProcessingStage:
        return ProcessingStage.UPLOADED

    async def next(self, context: 'DocumentContext') -> DocumentState:
        """
        函数级注释：验证文件并转换到下一个状态
        内部逻辑：执行验证 -> 成功则进入解析状态 -> 失败则进入失败状态
        """
        logger.info(f"[{context.document_id}] 开始验证文件")

        # 内部逻辑：执行验证
        try:
            if self._validation_func:
                is_valid = await self._validation_func(context)
            else:
                is_valid = await self._default_validation(context)

            if not is_valid:
                logger.warning(f"[{context.document_id}] 文件验证失败")
                return FailedState("文件验证失败")

            logger.info(f"[{context.document_id}] 文件验证成功，进入解析阶段")
            return ParsingState()

        except Exception as e:
            logger.error(f"[{context.document_id}] 验证过程异常: {str(e)}")
            return FailedState(f"验证异常: {str(e)}")

    async def _default_validation(self, context: 'DocumentContext') -> bool:
        """
        函数级注释：默认验证逻辑
        内部逻辑：检查文件大小、格式等
        """
        # 内部变量：最大文件大小 (100MB)
        MAX_FILE_SIZE = 100 * 1024 * 1024

        file_info = context.get_data('file_info', {})
        file_size = file_info.get('size', 0)

        if file_size > MAX_FILE_SIZE:
            raise DocumentProcessingException(
                f"文件过大: {file_size} bytes",
                self.get_description(),
                "FILE_TOO_LARGE"
            )

        # 内部逻辑：检查支持的文件类型
        supported_types = ['.pdf', '.docx', '.txt', '.md', '.json']
        file_name = file_info.get('name', '')
        if not any(file_name.endswith(ext) for ext in supported_types):
            raise DocumentProcessingException(
                f"不支持的文件类型: {file_name}",
                self.get_description(),
                "UNSUPPORTED_FILE_TYPE"
            )

        return True

    def can_process(self) -> bool:
        return False

    def can_retry(self) -> bool:
        return True

    def is_terminal(self) -> bool:
        return False


class ParsingState(DocumentState):
    """
    类级注释：解析中状态
    内部逻辑：执行文档解析，提取文本内容
    设计模式：状态模式 - 具体状态
    """

    def __init__(self, parser_func: Optional[Callable] = None):
        """
        函数级注释：初始化解析状态
        参数：
            parser_func - 自定义解析函数
        """
        self._parser_func = parser_func

    @property
    def stage(self) -> ProcessingStage:
        return ProcessingStage.PARSING

    async def next(self, context: 'DocumentContext') -> DocumentState:
        """
        函数级注释：解析文档内容
        内部逻辑：执行解析 -> 成功则进入分块状态 -> 失败则进入失败状态
        """
        logger.info(f"[{context.document_id}] 开始解析文档")

        start_time = time.time()

        try:
            if self._parser_func:
                content = await self._parser_func(context)
            else:
                content = await self._default_parse(context)

            duration = time.time() - start_time

            # 内部逻辑：保存解析结果
            context.set_data('parsed_content', content)
            context.add_result(ProcessingResult(
                success=True,
                data=len(content) if isinstance(content, str) else 0,
                duration=duration,
                metadata={"stage": "parsing"}
            ))

            logger.info(f"[{context.document_id}] 文档解析成功，内容长度: {len(content) if isinstance(content, str) else 0}")
            return ChunkingState()

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"[{context.document_id}] 文档解析失败: {str(e)}")

            context.add_result(ProcessingResult(
                success=False,
                error=str(e),
                duration=duration,
                metadata={"stage": "parsing"}
            ))

            return FailedState(f"解析失败: {str(e)}")

    async def _default_parse(self, context: 'DocumentContext') -> str:
        """
        函数级注释：默认解析逻辑
        内部逻辑：使用 LangChain 文档加载器解析
        """
        file_path = context.get_data('file_path')

        # 内部逻辑：根据文件类型选择加载器
        if file_path.endswith('.pdf'):
            from langchain_community.document_loaders import PyPDFLoader
            loader = PyPDFLoader(file_path)
        elif file_path.endswith('.docx'):
            from langchain_community.document_loaders import Docx2txtLoader
            loader = Docx2txtLoader(file_path)
        else:
            from langchain_community.document_loaders import TextLoader
            loader = TextLoader(file_path, encoding='utf-8')

        documents = loader.load()
        content = "\n\n".join([doc.page_content for doc in documents])

        return content

    def can_process(self) -> bool:
        return True

    def can_retry(self) -> bool:
        return True

    def is_terminal(self) -> bool:
        return False


class ChunkingState(DocumentState):
    """
    类级注释：分块状态
    内部逻辑：将文档内容分割成适合向量化的块
    设计模式：状态模式 - 具体状态
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        chunker_func: Optional[Callable] = None
    ):
        """
        函数级注释：初始化分块状态
        参数：
            chunk_size - 块大小
            chunk_overlap - 重叠大小
            chunker_func - 自定义分块函数
        """
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._chunker_func = chunker_func

    @property
    def stage(self) -> ProcessingStage:
        return ProcessingStage.CHUNKING

    async def next(self, context: 'DocumentContext') -> DocumentState:
        """
        函数级注释：分割文档内容
        内部逻辑：执行分块 -> 成功则进入向量化状态 -> 失败则进入失败状态
        """
        logger.info(f"[{context.document_id}] 开始分块文档")

        start_time = time.time()

        try:
            content = context.get_data('parsed_content')

            if not content:
                raise DocumentProcessingException(
                    "没有可分块的内容",
                    self.get_description(),
                    "NO_CONTENT"
                )

            if self._chunker_func:
                chunks = await self._chunker_func(content)
            else:
                chunks = await self._default_chunk(content)

            duration = time.time() - start_time

            # 内部逻辑：保存分块结果
            context.set_data('chunks', chunks)
            context.add_result(ProcessingResult(
                success=True,
                data=len(chunks),
                duration=duration,
                metadata={"stage": "chunking", "chunk_count": len(chunks)}
            ))

            logger.info(f"[{context.document_id}] 文档分块成功，块数: {len(chunks)}")
            return VectorizingState()

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"[{context.document_id}] 文档分块失败: {str(e)}")

            context.add_result(ProcessingResult(
                success=False,
                error=str(e),
                duration=duration,
                metadata={"stage": "chunking"}
            ))

            return FailedState(f"分块失败: {str(e)}")

    async def _default_chunk(self, content: str) -> List[str]:
        """
        函数级注释：默认分块逻辑
        内部逻辑：使用 LangChain 递归字符分割器
        """
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
        )

        chunks = splitter.split_text(content)
        return chunks

    def can_process(self) -> bool:
        return True

    def can_retry(self) -> bool:
        return True

    def is_terminal(self) -> bool:
        return False


class VectorizingState(DocumentState):
    """
    类级注释：向量化状态
    内部逻辑：将文本块转换为向量并存储
    设计模式：状态模式 - 具体状态
    """

    def __init__(self, vectorizer_func: Optional[Callable] = None):
        """
        函数级注释：初始化向量化状态
        参数：
            vectorizer_func - 自定义向量化函数
        """
        self._vectorizer_func = vectorizer_func

    @property
    def stage(self) -> ProcessingStage:
        return ProcessingStage.VECTORIZING

    async def next(self, context: 'DocumentContext') -> DocumentState:
        """
        函数级注释：向量化文档块
        内部逻辑：执行向量化 -> 成功则进入完成状态 -> 失败则进入失败状态
        """
        logger.info(f"[{context.document_id}] 开始向量化文档")

        start_time = time.time()

        try:
            chunks = context.get_data('chunks')

            if not chunks:
                raise DocumentProcessingException(
                    "没有可向量化的块",
                    self.get_description(),
                    "NO_CHUNKS"
                )

            if self._vectorizer_func:
                vector_ids = await self._vectorizer_func(chunks, context)
            else:
                vector_ids = await self._default_vectorize(chunks, context)

            duration = time.time() - start_time

            # 内部逻辑：保存向量化结果
            context.set_data('vector_ids', vector_ids)
            context.add_result(ProcessingResult(
                success=True,
                data=len(vector_ids),
                duration=duration,
                metadata={"stage": "vectorizing", "vector_count": len(vector_ids)}
            ))

            logger.info(f"[{context.document_id}] 文档向量化成功，向量数: {len(vector_ids)}")
            return CompletedState()

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"[{context.document_id}] 文档向量化失败: {str(e)}")

            context.add_result(ProcessingResult(
                success=False,
                error=str(e),
                duration=duration,
                metadata={"stage": "vectorizing"}
            ))

            return FailedState(f"向量化失败: {str(e)}")

    async def _default_vectorize(
        self,
        chunks: List[str],
        context: 'DocumentContext'
    ) -> List[str]:
        """
        函数级注释：默认向量化逻辑
        内部逻辑：使用嵌入模型生成向量并存储到向量数据库
        """
        from app.services.ingest_service import IngestService

        # 内部逻辑：获取嵌入函数
        embeddings = IngestService.get_embeddings()

        # 内部逻辑：存储到向量数据库
        from app.core.config import settings
        from langchain_community.vectorstores import Chroma

        vector_store = Chroma(
            persist_directory=settings.CHROMA_DB_PATH,
            embedding_function=embeddings,
            collection_name=settings.CHROMA_COLLECTION_NAME
        )

        # 内部逻辑：生成文档 ID
        vector_ids = [f"{context.document_id}_{i}" for i in range(len(chunks))]

        # 内部逻辑：添加到向量数据库
        vector_store.add_texts(
            texts=chunks,
            ids=vector_ids,
            metadatas=[{"doc_id": context.document_id, "chunk_index": i} for i in range(len(chunks))]
        )

        return vector_ids

    def can_process(self) -> bool:
        return True

    def can_retry(self) -> bool:
        return True

    def is_terminal(self) -> bool:
        return False


class CompletedState(DocumentState):
    """
    类级注释：完成状态
    内部逻辑：文档处理完成的终止状态
    设计模式：状态模式 - 终止状态
    """

    @property
    def stage(self) -> ProcessingStage:
        return ProcessingStage.COMPLETED

    async def next(self, context: 'DocumentContext') -> DocumentState:
        """
        函数级注释：终止状态，不进行转换
        内部逻辑：返回自身，保持完成状态
        """
        return self

    def can_process(self) -> bool:
        return False

    def can_retry(self) -> bool:
        return False

    def is_terminal(self) -> bool:
        return True


class FailedState(DocumentState):
    """
    类级注释：失败状态
    内部逻辑：文档处理失败的终止状态
    设计模式：状态模式 - 终止状态
    """

    def __init__(self, error_message: str):
        """
        函数级注释：初始化失败状态
        参数：
            error_message - 错误信息
        """
        self._error_message = error_message

    @property
    def stage(self) -> ProcessingStage:
        return ProcessingStage.FAILED

    @property
    def error_message(self) -> str:
        """获取错误信息"""
        return self._error_message

    async def next(self, context: 'DocumentContext') -> DocumentState:
        """
        函数级注释：终止状态，不进行转换
        内部逻辑：返回自身，保持失败状态
        """
        return self

    def can_process(self) -> bool:
        return False

    def can_retry(self) -> bool:
        return True

    def is_terminal(self) -> bool:
        return True


class DocumentContext:
    """
    类级注释：文档上下文
    内部逻辑：维护文档处理的上下文数据和状态
    设计模式：状态模式 - 上下文角色
    职责：
        1. 维护当前状态
        2. 存储处理过程中的数据
        3. 提供状态转换接口
        4. 记录处理历史
    """

    def __init__(
        self,
        document_id: str,
        initial_state: Optional[DocumentState] = None,
        max_retries: int = 3
    ):
        """
        函数级注释：初始化文档上下文
        参数：
            document_id - 文档 ID
            initial_state - 初始状态
            max_retries - 最大重试次数
        """
        # 内部变量：文档 ID
        self.document_id = document_id

        # 内部变量：当前状态
        self._state = initial_state or UploadedState()

        # 内部变量：状态历史
        self._state_history: List[DocumentState] = [self._state]

        # 内部变量：处理数据存储
        self._data: Dict[str, Any] = {}

        # 内部变量：处理结果历史
        self._results: List[ProcessingResult] = []

        # 内部变量：重试计数
        self._retry_count = 0

        # 内部变量：最大重试次数
        self._max_retries = max_retries

        # 内部变量：是否已处理完成
        self._is_finished = False

        logger.info(f"[{self.document_id}] 文档上下文初始化完成，初始状态: {self._state.get_description()}")

    @property
    def current_state(self) -> DocumentState:
        """获取当前状态"""
        return self._state

    @property
    def current_stage(self) -> ProcessingStage:
        """获取当前处理阶段"""
        return self._state.stage

    @property
    def is_finished(self) -> bool:
        """检查是否已完成处理"""
        return self._is_finished

    @property
    def is_failed(self) -> bool:
        """检查是否处理失败"""
        return isinstance(self._state, FailedState)

    @property
    def retry_count(self) -> int:
        """获取重试次数"""
        return self._retry_count

    async def advance(self) -> DocumentState:
        """
        函数级注释：推进到下一个状态
        内部逻辑：调用当前状态的 next 方法 -> 更新状态 -> 记录历史
        返回值：新的状态对象

        @example
        ```python
        context = DocumentContext("doc_123")
        while not context.is_finished:
            await context.advance()
        ```
        """
        if self._is_finished:
            logger.warning(f"[{self.document_id}] 文档处理已完成，无法继续推进")
            return self._state

        # 内部逻辑：转换到下一个状态
        new_state = await self._state.next(self)
        self._state = new_state
        self._state_history.append(new_state)

        logger.info(
            f"[{self.document_id}] 状态转换: "
            f"{self._state_history[-2].get_description()} -> {new_state.get_description()}"
        )

        # 内部逻辑：检查是否为终止状态
        if new_state.is_terminal():
            self._is_finished = True
            if isinstance(new_state, FailedState):
                logger.error(f"[{self.document_id}] 文档处理失败: {new_state.error_message}")
            else:
                logger.info(f"[{self.document_id}] 文档处理完成")

        return new_state

    async def advance_to_completion(self) -> DocumentState:
        """
        函数级注释：持续推进直到完成
        内部逻辑：循环调用 advance 直到到达终止状态
        返回值：最终的状态对象

        @example
        ```python
        context = DocumentContext("doc_123")
        final_state = await context.advance_to_completion()
        ```
        """
        while not self._is_finished:
            await self.advance()

        return self._state

    async def retry(self) -> DocumentState:
        """
        函数级注释：重试处理
        内部逻辑：重置到上一个可重试的状态 -> 重新处理
        返回值：新的状态对象
        异常：DocumentProcessingException - 无法重试时抛出
        """
        if not self._state.can_retry():
            raise DocumentProcessingException(
                f"当前状态 {self._state.get_description()} 不支持重试",
                self.current_stage.value,
                "RETRY_NOT_SUPPORTED"
            )

        if self._retry_count >= self._max_retries:
            raise DocumentProcessingException(
                f"已达到最大重试次数 ({self._max_retries})",
                self.current_stage.value,
                "MAX_RETRIES_EXCEEDED"
            )

        self._retry_count += 1

        # 内部逻辑：重置到上传状态重新开始
        self._state = UploadedState()
        self._is_finished = False

        logger.info(f"[{self.document_id}] 开始第 {self._retry_count} 次重试")

        return await self.advance_to_completion()

    def get_data(self, key: str, default: Any = None) -> Any:
        """
        函数级注释：获取上下文数据
        参数：
            key - 数据键
            default - 默认值
        返回值：存储的数据
        """
        return self._data.get(key, default)

    def set_data(self, key: str, value: Any) -> None:
        """
        函数级注释：设置上下文数据
        参数：
            key - 数据键
            value - 数据值
        """
        self._data[key] = value

    def add_result(self, result: ProcessingResult) -> None:
        """
        函数级注释：添加处理结果
        参数：
            result - 处理结果对象
        """
        self._results.append(result)

    def get_results(self) -> List[ProcessingResult]:
        """获取所有处理结果"""
        return self._results.copy()

    def get_state_history(self) -> List[DocumentState]:
        """获取状态历史"""
        return self._state_history.copy()

    def get_summary(self) -> Dict[str, Any]:
        """
        函数级注释：获取处理摘要
        返回值：包含处理统计信息的字典
        """
        successful_stages = sum(1 for r in self._results if r.success)
        failed_stages = sum(1 for r in self._results if not r.success)
        total_duration = sum(r.duration for r in self._results)

        return {
            "document_id": self.document_id,
            "current_state": self._state.get_description(),
            "current_stage": self._state.stage.value,
            "is_finished": self._is_finished,
            "is_failed": self.is_failed,
            "retry_count": self._retry_count,
            "successful_stages": successful_stages,
            "failed_stages": failed_stages,
            "total_duration": total_duration,
            "state_history": [s.get_description() for s in self._state_history],
        }


class DocumentStateMachine:
    """
    类级注释：文档处理状态机
    内部逻辑：封装文档处理的完整流程
    设计模式：状态模式 + 外观模式
    职责：
        1. 简化状态机的使用
        2. 提供高级处理接口
        3. 支持自定义处理函数

    使用场景：
        - 文档摄入流程
        - 批量文档处理
        - 异步文档处理任务
    """

    def __init__(
        self,
        validation_func: Optional[Callable] = None,
        parser_func: Optional[Callable] = None,
        chunker_func: Optional[Callable] = None,
        vectorizer_func: Optional[Callable] = None,
        max_retries: int = 3
    ):
        """
        函数级注释：初始化文档处理状态机
        参数：
            validation_func - 自定义验证函数
            parser_func - 自定义解析函数
            chunker_func - 自定义分块函数
            vectorizer_func - 自定义向量化函数
            max_retries - 最大重试次数
        """
        self._validation_func = validation_func
        self._parser_func = parser_func
        self._chunker_func = chunker_func
        self._vectorizer_func = vectorizer_func
        self._max_retries = max_retries

    async def process_document(
        self,
        document_id: str,
        file_path: str,
        file_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        函数级注释：处理单个文档
        内部逻辑：创建上下文 -> 配置初始状态 -> 推进到完成
        参数：
            document_id - 文档 ID
            file_path - 文件路径
            file_info - 文件信息
        返回值：处理摘要

        @example
        ```python
        state_machine = DocumentStateMachine()
        result = await state_machine.process_document("doc_123", "/path/to/file.pdf")
        ```
        """
        # 内部逻辑：创建初始状态
        initial_state = UploadedState(validation_func=self._validation_func)

        # 内部逻辑：创建上下文
        context = DocumentContext(
            document_id=document_id,
            initial_state=initial_state,
            max_retries=self._max_retries
        )

        # 内部逻辑：设置初始数据
        context.set_data('file_path', file_path)
        if file_info:
            context.set_data('file_info', file_info)

        # 内部逻辑：配置处理函数
        if self._parser_func:
            context.set_data('_parser_func', self._parser_func)
        if self._chunker_func:
            context.set_data('_chunker_func', self._chunker_func)
        if self._vectorizer_func:
            context.set_data('_vectorizer_func', self._vectorizer_func)

        # 内部逻辑：推进到完成
        final_state = await context.advance_to_completion()

        return context.get_summary()

    async def process_batch(
        self,
        documents: List[Dict[str, Any]],
        progress_callback: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        函数级注释：批量处理文档
        内部逻辑：循环处理每个文档 -> 收集结果
        参数：
            documents - 文档信息列表，每项包含 document_id 和 file_path
            progress_callback - 进度回调函数
        返回值：处理摘要列表

        @example
        ```python
        documents = [
            {"document_id": "doc_1", "file_path": "/path/to/file1.pdf"},
            {"document_id": "doc_2", "file_path": "/path/to/file2.pdf"},
        ]
        results = await state_machine.process_batch(documents)
        ```
        """
        results = []
        total = len(documents)

        for i, doc_info in enumerate(documents):
            logger.info(f"处理文档 {i + 1}/{total}: {doc_info['document_id']}")

            try:
                result = await self.process_document(
                    document_id=doc_info['document_id'],
                    file_path=doc_info['file_path'],
                    file_info=doc_info.get('file_info')
                )
                results.append(result)

                # 内部逻辑：报告进度
                if progress_callback:
                    await progress_callback(i + 1, total, result)

            except Exception as e:
                logger.error(f"文档 {doc_info['document_id']} 处理异常: {str(e)}")
                results.append({
                    "document_id": doc_info['document_id'],
                    "is_failed": True,
                    "error": str(e)
                })

        return results


# 内部变量：导出所有公共接口
__all__ = [
    # 基础类
    'DocumentState',
    'DocumentContext',
    'DocumentStateMachine',
    'ProcessingStage',
    'ProcessingResult',
    'DocumentProcessingException',
    # 具体状态
    'UploadedState',
    'ParsingState',
    'ChunkingState',
    'VectorizingState',
    'CompletedState',
    'FailedState',
]
