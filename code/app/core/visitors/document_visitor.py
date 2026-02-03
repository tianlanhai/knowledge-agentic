# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：文档访问者模式抽象基类与数据结构
内部逻辑：定义可访问元素和访问者接口
设计模式：访问者模式（Visitor Pattern）
设计原则：SOLID - 开闭原则、依赖倒置原则
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class ExportResult:
    """
    类级注释：导出结果数据类
    职责：封装导出操作的结果
    """
    content: str  # 导出内容
    format: str  # 导出格式
    size: int  # 内容大小（字节）
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "content": self.content,
            "format": self.format,
            "size": self.size,
            "timestamp": self.timestamp.isoformat()
        }


class Visitable(ABC):
    """
    类级注释：可访问元素抽象基类
    设计模式：访问者模式（Visitor Pattern）- 元素接口
    职责：定义接受访问者的方法
    """

    @abstractmethod
    def accept(self, visitor: "DocumentVisitor") -> Any:
        """
        函数级注释：接受访问者
        内部逻辑：调用访问者的对应方法（双分派）
        参数：
            visitor: 文档访问者
        返回值：访问结果
        """
        pass


@dataclass
class Document(Visitable):
    """
    类级注释：文档数据类（可访问元素）
    设计模式：访问者模式（Visitor Pattern）- 具体元素
    职责：存储文档数据，接受访问者操作
    """
    id: int
    title: str
    content: str
    file_name: str
    file_type: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def accept(self, visitor: "DocumentVisitor") -> Any:
        """
        函数级注释：接受访问者访问
        内部逻辑：调用访问者的visit_document方法
        """
        return visitor.visit_document(self)


@dataclass
class DocumentChunk(Visitable):
    """
    类级注释：文档片段数据类（可访问元素）
    设计模式：访问者模式（Visitor Pattern）- 具体元素
    职责：存储文档片段数据，接受访问者操作
    """
    chunk_id: str
    document_id: int
    content: str
    chunk_index: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def accept(self, visitor: "DocumentVisitor") -> Any:
        """
        函数级注释：接受访问者访问
        内部逻辑：调用访问者的visit_chunk方法
        """
        return visitor.visit_chunk(self)


@dataclass
class DocumentCollection(Visitable):
    """
    类级注释：文档集合数据类（可访问元素）
    设计模式：访问者模式（Visitor Pattern）- 具体元素
    职责：存储文档列表，接受访问者批量操作
    """
    name: str
    documents: List[Document]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def accept(self, visitor: "DocumentVisitor") -> Any:
        """
        函数级注释：接受访问者访问
        内部逻辑：调用访问者的visit_collection方法
        """
        return visitor.visit_collection(self)

    def add_document(self, document: Document) -> None:
        """添加文档到集合"""
        self.documents.append(document)

    def remove_document(self, document_id: int) -> bool:
        """从集合中移除文档"""
        for i, doc in enumerate(self.documents):
            if doc.id == document_id:
                self.documents.pop(i)
                return True
        return False

    def get_document(self, document_id: int) -> Optional[Document]:
        """获取指定ID的文档"""
        for doc in self.documents:
            if doc.id == document_id:
                return doc
        return None


class DocumentVisitor(ABC):
    """
    类级注释：文档访问者抽象基类
    设计模式：访问者模式（Visitor Pattern）- 访问者接口
    职责：定义对各种可访问元素的操作

    设计优势：
        - 新增操作无需修改元素类（开闭原则）
        - 相关操作集中在访问者类中（单一职责）
        - 可以组合多个访问者实现复杂操作
    """

    @abstractmethod
    def visit_document(self, document: Document) -> Any:
        """
        函数级注释：访问文档
        内部逻辑：对文档执行操作
        参数：
            document: 文档对象
        返回值：操作结果
        """
        pass

    @abstractmethod
    def visit_chunk(self, chunk: DocumentChunk) -> Any:
        """
        函数级注释：访问文档片段
        内部逻辑：对文档片段执行操作
        参数：
            chunk: 文档片段对象
        返回值：操作结果
        """
        pass

    @abstractmethod
    def visit_collection(self, collection: DocumentCollection) -> Any:
        """
        函数级注释：访问文档集合
        内部逻辑：对文档集合执行批量操作
        参数：
            collection: 文档集合对象
        返回值：操作结果
        """
        pass


class VisitorRegistry:
    """
    类级注释：访问者注册表
    设计模式：注册表模式
    职责：管理所有导出访问者
    """

    # 内部类变量：格式名称到访问者类的映射
    _visitors: Dict[str, type] = {}

    @classmethod
    def register(cls, format_name: str, visitor_class: type) -> None:
        """
        函数级注释：注册访问者
        参数：
            format_name: 格式名称
            visitor_class: 访问者类
        """
        cls._visitors[format_name] = visitor_class

    @classmethod
    def get_visitor(cls, format_name: str, **kwargs) -> Optional[DocumentVisitor]:
        """
        函数级注释：获取访问者实例
        参数：
            format_name: 格式名称
            **kwargs: 访问者构造参数
        返回值：访问者实例或None
        """
        visitor_class = cls._visitors.get(format_name)
        if visitor_class:
            return visitor_class(**kwargs)
        return None

    @classmethod
    def get_supported_formats(cls) -> List[str]:
        """
        函数级注释：获取支持的导出格式
        返回值：格式名称列表
        """
        return list(cls._visitors.keys())
