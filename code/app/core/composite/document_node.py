# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：文档树节点组合模式实现
内部逻辑：统一处理文件节点和文件夹节点，实现树形结构
设计模式：组合模式（Composite Pattern）
设计原则：SOLID - 开闭原则、里氏替换原则、接口隔离原则

使用场景：
- 文档目录树管理
- 权限树管理
- 分类层级结构
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Iterator, Callable, TYPE_CHECKING
from enum import Enum
from datetime import datetime
from loguru import logger

if TYPE_CHECKING:
    from typing import ForwardRef


class NodeType(Enum):
    """
    类级注释：节点类型枚举
    职责：定义树节点类型
    """
    FILE = "file"
    FOLDER = "folder"
    ROOT = "root"


@dataclass
class NodeStats:
    """
    类级注释：节点统计信息
    职责：存储节点的统计数据
    """
    file_count: int = 0  # 文件数量
    folder_count: int = 0  # 文件夹数量
    total_size: int = 0  # 总大小（字节）
    max_depth: int = 0  # 最大深度


class DocumentNode(ABC):
    """
    类级注释：文档节点抽象基类
    设计模式：组合模式（Composite Pattern）- 组件接口
    职责：
        1. 定义树节点的统一接口
        2. 声明文件和文件夹的公共操作
        3. 支持树形结构的遍历

    设计优势：
        - 统一处理单个节点和节点集合
        - 客户端无需区分文件和文件夹
        - 易于扩展新的节点类型
    """

    def __init__(
        self,
        node_id: str,
        name: str,
        node_type: NodeType,
        parent: Optional["FolderNode"] = None
    ):
        """
        函数级注释：初始化节点
        参数：
            node_id: 节点唯一标识
            name: 节点名称
            node_type: 节点类型
            parent: 父节点（仅文件夹可以有子节点）
        """
        self.node_id = node_id
        self.name = name
        self.node_type = node_type
        self._parent = parent
        self.created_at = datetime.now()
        self.metadata: Dict[str, Any] = {}

    @property
    def parent(self) -> Optional["FolderNode"]:
        """获取父节点"""
        return self._parent

    @parent.setter
    def parent(self, value: Optional["FolderNode"]) -> None:
        """设置父节点"""
        self._parent = value

    @property
    def path(self) -> str:
        """
        函数级注释：获取节点完整路径
        返回值：路径字符串
        """
        if self._parent is None:
            return f"/{self.name}"
        return f"{self._parent.path}/{self.name}".replace("//", "/")

    @abstractmethod
    def size(self) -> int:
        """
        函数级注释：获取节点大小
        返回值：大小（字节）
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """
        函数级注释：计算节点包含的文件数量
        返回值：文件数量
        """
        pass

    @abstractmethod
    def is_leaf(self) -> bool:
        """
        函数级注释：判断是否为叶子节点
        返回值：是否为叶子节点
        """
        pass

    def depth(self) -> int:
        """
        函数级注释：计算节点深度
        返回值：深度值（根节点为0）
        """
        if self._parent is None:
            return 0
        return self._parent.depth() + 1

    def ancestors(self) -> List["DocumentNode"]:
        """
        函数级注释：获取所有祖先节点
        返回值：祖先节点列表（从根到父）
        """
        if self._parent is None:
            return []
        return self._parent.ancestors() + [self._parent]

    def root(self) -> "DocumentNode":
        """
        函数级注释：获取根节点
        返回值：根节点
        """
        if self._parent is None:
            return self
        return self._parent.root()

    @abstractmethod
    def accept(self, visitor: "NodeVisitor") -> Any:
        """
        函数级注释：接受访问者
        设计模式：访问者模式
        参数：
            visitor: 节点访问者
        返回值：访问结果
        """
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        函数级注释：转换为字典
        返回值：节点信息字典
        """
        pass


class FileNode(DocumentNode):
    """
    类级注释：文件节点类
    设计模式：组合模式（Composite Pattern）- 叶子节点
    职责：表示文档树中的文件节点

    设计优势：
        - 封装文件相关属性和操作
        - 与文件夹节点统一接口
        - 不可包含子节点
    """

    def __init__(
        self,
        node_id: str,
        name: str,
        file_size: int = 0,
        file_type: str = "",
        content: str = "",
        parent: Optional["FolderNode"] = None
    ):
        """
        函数级注释：初始化文件节点
        参数：
            node_id: 节点ID
            name: 文件名
            file_size: 文件大小
            file_type: 文件类型
            content: 文件内容
            parent: 父文件夹
        """
        super().__init__(node_id, name, NodeType.FILE, parent)
        self.file_size = file_size
        self.file_type = file_type
        self.content = content

    def size(self) -> int:
        """获取文件大小"""
        return self.file_size

    def count(self) -> int:
        """文件节点计为1"""
        return 1

    def is_leaf(self) -> bool:
        """文件节点是叶子节点"""
        return True

    def accept(self, visitor: "NodeVisitor") -> Any:
        """接受访问者"""
        return visitor.visit_file(self)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "node_id": self.node_id,
            "name": self.name,
            "type": "file",
            "size": self.file_size,
            "file_type": self.file_type,
            "path": self.path,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }


class FolderNode(DocumentNode):
    """
    类级注释：文件夹节点类
    设计模式：组合模式（Composite Pattern）- 组合节点
    职责：表示文档树中的文件夹节点

    设计优势：
        - 可以包含子节点
        - 统一的节点操作接口
        - 支持树形结构操作
    """

    def __init__(
        self,
        node_id: str,
        name: str,
        parent: Optional["FolderNode"] = None
    ):
        """
        函数级注释：初始化文件夹节点
        参数：
            node_id: 节点ID
            name: 文件夹名
            parent: 父文件夹
        """
        super().__init__(node_id, name, NodeType.FOLDER, parent)
        self._children: List["DocumentNode"] = []

    @property
    def children(self) -> List["DocumentNode"]:
        """获取子节点列表"""
        return self._children.copy()

    def add_child(self, child: DocumentNode) -> None:
        """
        函数级注释：添加子节点
        参数：
            child: 要添加的子节点
        """
        child.parent = self
        self._children.append(child)
        logger.debug(f"添加子节点: {self.path}/{child.name}")

    def remove_child(self, child_id: str) -> bool:
        """
        函数级注释：移除子节点
        参数：
            child_id: 子节点ID
        返回值：是否成功移除
        """
        for i, child in enumerate(self._children):
            if child.node_id == child_id:
                removed = self._children.pop(i)
                removed.parent = None
                logger.debug(f"移除子节点: {self.path}/{removed.name}")
                return True
        return False

    def get_child(self, child_id: str) -> Optional[DocumentNode]:
        """
        函数级注释：获取指定ID的子节点
        参数：
            child_id: 子节点ID
        返回值：子节点或None
        """
        for child in self._children:
            if child.node_id == child_id:
                return child
        return None

    def get_child_by_name(self, name: str) -> Optional[DocumentNode]:
        """
        函数级注释：根据名称获取子节点
        参数：
            name: 子节点名称
        返回值：子节点或None
        """
        for child in self._children:
            if child.name == name:
                return child
        return None

    def find(self, node_id: str) -> Optional[DocumentNode]:
        """
        函数级注释：递归查找节点
        参数：
            node_id: 节点ID
        返回值：找到的节点或None
        """
        # 内部逻辑：检查当前子节点
        for child in self._children:
            if child.node_id == node_id:
                return child

        # 内部逻辑：递归查找子文件夹
        for child in self._children:
            if isinstance(child, FolderNode):
                found = child.find(node_id)
                if found:
                    return found

        return None

    def size(self) -> int:
        """
        函数级注释：计算文件夹总大小
        返回值：所有文件的大小之和
        """
        return sum(child.size() for child in self._children)

    def count(self) -> int:
        """
        函数级注释：计算包含的文件总数
        返回值：文件数量
        """
        return sum(child.count() for child in self._children)

    def is_leaf(self) -> bool:
        """文件夹不是叶子节点"""
        return len(self._children) == 0

    def get_stats(self) -> NodeStats:
        """
        函数级注释：获取节点统计信息
        返回值：统计信息对象
        """
        stats = NodeStats()
        stats.max_depth = 0

        for child in self._children:
            if isinstance(child, FileNode):
                stats.file_count += 1
                stats.total_size += child.size()
            elif isinstance(child, FolderNode):
                stats.folder_count += 1
                child_stats = child.get_stats()
                stats.file_count += child_stats.file_count
                stats.folder_count += child_stats.folder_count
                stats.total_size += child_stats.total_size
                stats.max_depth = max(stats.max_depth, child_stats.max_depth + 1)

        return stats

    def filter(self, predicate: Callable[["DocumentNode"], bool]) -> List["DocumentNode"]:
        """
        函数级注释：过滤节点
        参数：
            predicate: 谓词函数
        返回值：符合条件的节点列表
        """
        results = []

        for child in self._children:
            if predicate(child):
                results.append(child)
            if isinstance(child, FolderNode):
                results.extend(child.filter(predicate))

        return results

    def traverse(self, visitor: Callable[[DocumentNode], None]) -> None:
        """
        函数级注释：遍历所有节点
        参数：
            visitor: 访问函数
        """
        for child in self._children:
            visitor(child)
            if isinstance(child, FolderNode):
                child.traverse(visitor)

    def __iter__(self) -> Iterator["DocumentNode"]:
        """
        函数级注释：迭代器接口
        返回值：子节点迭代器
        """
        return iter(self._children)

    def accept(self, visitor: "NodeVisitor") -> Any:
        """接受访问者"""
        return visitor.visit_folder(self)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "node_id": self.node_id,
            "name": self.name,
            "type": "folder",
            "path": self.path,
            "children": [child.to_dict() for child in self._children],
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }


class NodeFilter:
    """
    类级注释：节点过滤器
    设计模式：策略模式
    职责：提供常用的节点过滤策略

    设计优势：
        - 封装过滤逻辑
        - 支持链式组合
        - 可复用
    """

    @staticmethod
    def by_type(node_type: NodeType) -> Callable[[DocumentNode], bool]:
        """按类型过滤"""
        return lambda node: node.node_type == node_type

    @staticmethod
    def by_name(pattern: str) -> Callable[[DocumentNode], bool]:
        """按名称模式过滤"""
        return lambda node: pattern.lower() in node.name.lower()

    @staticmethod
    def by_extension(extension: str) -> Callable[[DocumentNode], bool]:
        """按文件扩展名过滤"""
        return lambda node: (
            isinstance(node, FileNode) and
            node.file_type.lower() == extension.lower()
        )

    @staticmethod
    def by_size(max_size: int) -> Callable[[DocumentNode], bool]:
        """按文件大小过滤"""
        return lambda node: node.size() <= max_size

    @staticmethod
    def files_only() -> Callable[[DocumentNode], bool]:
        """只过滤文件"""
        return lambda node: isinstance(node, FileNode)

    @staticmethod
    def folders_only() -> Callable[[DocumentNode], bool]:
        """只过滤文件夹"""
        return lambda node: isinstance(node, FolderNode)

    @staticmethod
    def combine(*predicates: Callable[[DocumentNode], bool]) -> Callable[[DocumentNode], bool]:
        """组合多个过滤条件（AND）"""
        return lambda node: all(p(node) for p in predicates)

    @staticmethod
    def any_of(*predicates: Callable[[DocumentNode], bool]) -> Callable[[DocumentNode], bool]:
        """组合多个过滤条件（OR）"""
        return lambda node: any(p(node) for p in predicates)


# 访问者模式支持
class NodeVisitor(ABC):
    """
    类级注释：节点访问者抽象类
    设计模式：访问者模式
    职责：定义对节点的操作
    """

    @abstractmethod
    def visit_file(self, file_node: FileNode) -> Any:
        """访问文件节点"""
        pass

    @abstractmethod
    def visit_folder(self, folder_node: FolderNode) -> Any:
        """访问文件夹节点"""
        pass


class SizeCalculatorVisitor(NodeVisitor):
    """
    类级注释：大小计算访问者
    设计模式：访问者模式
    职责：计算节点总大小
    """

    def visit_file(self, file_node: FileNode) -> int:
        return file_node.size()

    def visit_folder(self, folder_node: FolderNode) -> int:
        return sum(child.accept(self) for child in folder_node.children)
