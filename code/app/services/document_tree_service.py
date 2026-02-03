# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：文档树服务模块
内部逻辑：集成组合模式实现文档层级结构管理
设计模式：组合模式（Composite Pattern）+ 单例模式
设计原则：单一职责原则、开闭原则

使用场景：
    - 文档文件夹管理
    - 文档分类目录
    - 文档权限树管理
"""

from typing import List, Dict, Any, Optional, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.composite.document_node import (
    DocumentNode,
    FileNode,
    FolderNode,
    NodeType,
    NodeStats,
    NodeFilter,
    NodeVisitor
)
from app.models.models import Document


@dataclass
class TreeOperationResult:
    """
    类级注释：树操作结果
    职责：封装树操作的结果和状态
    """
    success: bool
    message: str
    node_id: Optional[str] = None
    affected_nodes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class DocumentTreeService:
    """
    类级注释：文档树服务
    设计模式：组合模式 + 门面模式
    职责：
        1. 管理文档树形结构
        2. 提供树操作统一接口
        3. 与数据库模型集成

    使用场景：
        - 文件夹管理
        - 文档分类
        - 权限树管理
    """

    _instance: Optional["DocumentTreeService"] = None

    def __new__(cls):
        """实现单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初始化文档树服务"""
        if self._initialized:
            return

        self._initialized = True
        # 内部变量：根节点
        self._root: Optional[FolderNode] = None
        # 内部变量：节点ID到节点的映射
        self._node_map: Dict[str, DocumentNode] = {}
        # 内部变量：节点ID计数器
        self._node_id_counter = 0
        # 内部变量：文档ID到文件节点的映射
        self._document_node_map: Dict[int, FileNode] = {}

        logger.info("文档树服务初始化完成")

    @property
    def root(self) -> FolderNode:
        """
        函数级注释：获取根节点
        返回值：根文件夹节点
        """
        if self._root is None:
            self._root = FolderNode(
                node_id="root",
                name="知识库"
            )
            self._node_map["root"] = self._root
            logger.info("创建根节点: 知识库")
        return self._root

    def _generate_node_id(self, prefix: str = "node") -> str:
        """
        函数级注释：生成唯一节点ID
        内部逻辑：使用计数器保证唯一性
        参数：
            prefix - ID前缀
        返回值：唯一节点ID
        @private
        """
        self._node_id_counter += 1
        return f"{prefix}_{self._node_id_counter}_{datetime.now().timestamp()}"

    async def build_tree_from_documents(
        self,
        db: AsyncSession,
        tags: Optional[List[str]] = None
    ) -> FolderNode:
        """
        函数级注释：从数据库文档构建文档树
        内部逻辑：查询文档 -> 根据标签分组 -> 构建树形结构
        参数：
            db - 数据库会话
            tags - 过滤标签列表
        返回值：根节点
        """
        # 内部逻辑：清空现有树
        self._root = None
        self._node_map.clear()
        self._document_node_map.clear()
        self._node_id_counter = 0

        # 内部逻辑：查询文档
        query = select(Document)
        result = await db.execute(query)
        documents = result.scalars().all()

        logger.info(f"从数据库加载 {len(documents)} 个文档构建文档树")

        # 内部逻辑：按标签分组文档
        tag_folders: Dict[str, FolderNode] = {}

        for doc in documents:
            # 内部逻辑：解析标签
            doc_tags = []
            if doc.tags:
                import json
                try:
                    doc_tags = json.loads(doc.tags) if isinstance(doc.tags, str) else doc.tags
                except:
                    doc_tags = []

            # 内部逻辑：过滤标签
            if tags and not any(tag in doc_tags for tag in tags):
                continue

            # 内部逻辑：创建文件节点
            file_node = FileNode(
                node_id=f"doc_{doc.id}",
                name=doc.file_name,
                file_size=0,
                file_type=doc.file_path.split('.')[-1] if '.' in doc.file_path else '',
                content=doc.file_path  # 存储路径作为内容
            )
            file_node.metadata = {
                "document_id": doc.id,
                "source_type": doc.source_type,
                "tags": doc_tags
            }

            # 内部逻辑：根据标签决定父文件夹
            if doc_tags:
                # 内部逻辑：使用第一个标签作为分类
                primary_tag = doc_tags[0]
                if primary_tag not in tag_folders:
                    tag_folder = FolderNode(
                        node_id=f"tag_{primary_tag}",
                        name=primary_tag
                    )
                    self.root.add_child(tag_folder)
                    tag_folders[primary_tag] = tag_folder
                    self._node_map[tag_folder.node_id] = tag_folder

                tag_folders[primary_tag].add_child(file_node)
            else:
                # 内部逻辑：无标签文档直接放在根目录
                self.root.add_child(file_node)

            # 内部逻辑：记录映射
            self._node_map[file_node.node_id] = file_node
            self._document_node_map[doc.id] = file_node

        # 内部逻辑：记录日志（确保root存在）
        root = self.root  # 确保root被初始化
        file_count = root.count() if root else 0
        logger.info(f"文档树构建完成: {file_count} 个文件")
        return self.root

    def create_folder(
        self,
        name: str,
        parent_id: Optional[str] = None
    ) -> TreeOperationResult:
        """
        函数级注释：创建文件夹
        参数：
            name - 文件夹名称
            parent_id - 父节点ID（默认为根节点）
        返回值：操作结果
        """
        # 内部逻辑：确定父节点
        parent = self.root
        if parent_id:
            parent_node = self._node_map.get(parent_id)
            if not parent_node or not isinstance(parent_node, FolderNode):
                return TreeOperationResult(
                    success=False,
                    message=f"父节点不存在或不是文件夹: {parent_id}"
                )
            parent = parent_node

        # 内部逻辑：检查名称冲突
        if parent.get_child_by_name(name):
            return TreeOperationResult(
                success=False,
                message=f"文件夹 '{name}' 已存在"
            )

        # 内部逻辑：创建文件夹节点
        folder = FolderNode(
            node_id=self._generate_node_id("folder"),
            name=name
        )

        parent.add_child(folder)
        self._node_map[folder.node_id] = folder

        logger.info(f"创建文件夹: {folder.path}")
        return TreeOperationResult(
            success=True,
            message=f"文件夹 '{name}' 创建成功",
            node_id=folder.node_id
        )

    def add_document_to_folder(
        self,
        document_id: int,
        file_name: str,
        folder_id: Optional[str] = None,
        file_type: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> TreeOperationResult:
        """
        函数级注释：将文档添加到文件夹
        参数：
            document_id - 文档ID
            file_name - 文件名
            folder_id - 目标文件夹ID
            file_type - 文件类型
            metadata - 元数据
        返回值：操作结果
        """
        # 内部逻辑：确定父节点
        parent = self.root
        if folder_id:
            parent_node = self._node_map.get(folder_id)
            if not parent_node or not isinstance(parent_node, FolderNode):
                return TreeOperationResult(
                    success=False,
                    message=f"目标文件夹不存在: {folder_id}"
                )
            parent = parent_node

        # 内部逻辑：创建文件节点
        file_node = FileNode(
            node_id=f"doc_{document_id}",
            name=file_name,
            file_size=0,
            file_type=file_type
        )

        if metadata:
            file_node.metadata = metadata
        file_node.metadata["document_id"] = document_id

        parent.add_child(file_node)
        self._node_map[file_node.node_id] = file_node
        self._document_node_map[document_id] = file_node

        logger.info(f"添加文档到文件夹: {file_node.path}")
        return TreeOperationResult(
            success=True,
            message=f"文档 '{file_name}' 添加成功",
            node_id=file_node.node_id
        )

    def move_node(
        self,
        node_id: str,
        target_folder_id: Optional[str] = None
    ) -> TreeOperationResult:
        """
        函数级注释：移动节点到目标文件夹
        参数：
            node_id - 要移动的节点ID
            target_folder_id - 目标文件夹ID（None表示移到根目录）
        返回值：操作结果
        """
        # 内部逻辑：获取节点
        node = self._node_map.get(node_id)
        if not node:
            return TreeOperationResult(
                success=False,
                message=f"节点不存在: {node_id}"
            )

        # 内部逻辑：确定目标父节点
        target_parent = self.root
        if target_folder_id:
            target_parent = self._node_map.get(target_folder_id)
            if not target_parent or not isinstance(target_parent, FolderNode):
                return TreeOperationResult(
                    success=False,
                    message=f"目标文件夹不存在: {target_folder_id}"
                )

        # 内部逻辑：从原父节点移除
        old_parent = node.parent
        if old_parent:
            old_parent.remove_child(node_id)

        # 内部逻辑：添加到新父节点
        target_parent.add_child(node)

        logger.info(f"移动节点: {node.path}")
        return TreeOperationResult(
            success=True,
            message=f"节点移动成功",
            affected_nodes=1
        )

    def delete_node(self, node_id: str, recursive: bool = False) -> TreeOperationResult:
        """
        函数级注释：删除节点
        参数：
            node_id - 要删除的节点ID
            recursive - 是否递归删除子节点
        返回值：操作结果
        """
        node = self._node_map.get(node_id)
        if not node:
            return TreeOperationResult(
                success=False,
                message=f"节点不存在: {node_id}"
            )

        if node.node_id == "root":
            return TreeOperationResult(
                success=False,
                message="不能删除根节点"
            )

        # 内部逻辑：统计受影响的节点
        affected_count = 1
        if recursive and isinstance(node, FolderNode):
            affected_count = node.count() + len([n for n in node if isinstance(n, FolderNode)])

        # 内部逻辑：从父节点移除
        parent = node.parent
        if parent:
            parent.remove_child(node_id)

        # 内部逻辑：清理映射
        self._node_map.pop(node_id, None)
        if isinstance(node, FileNode):
            doc_id = node.metadata.get("document_id")
            if doc_id:
                self._document_node_map.pop(doc_id, None)

        # 内部逻辑：递归删除子节点映射
        if recursive and isinstance(node, FolderNode):
            for child in node.children:
                self._node_map.pop(child.node_id, None)

        logger.info(f"删除节点: {node_id}, 影响节点数: {affected_count}")
        return TreeOperationResult(
            success=True,
            message=f"节点删除成功",
            affected_nodes=affected_count
        )

    def find_node(self, node_id: str) -> Optional[DocumentNode]:
        """
        函数级注释：查找节点
        参数：
            node_id - 节点ID
        返回值：节点或None
        """
        return self._node_map.get(node_id)

    def find_by_document_id(self, document_id: int) -> Optional[FileNode]:
        """
        函数级注释：根据文档ID查找文件节点
        参数：
            document_id - 文档ID
        返回值：文件节点或None
        """
        return self._document_node_map.get(document_id)

    def search_nodes(
        self,
        keyword: str,
        node_type: Optional[NodeType] = None
    ) -> List[DocumentNode]:
        """
        函数级注释：搜索节点
        参数：
            keyword - 搜索关键词
            node_type - 节点类型过滤
        返回值：匹配的节点列表
        """
        results = []

        for node in self._node_map.values():
            # 内部逻辑：类型过滤
            if node_type and node.node_type != node_type:
                continue

            # 内部逻辑：关键词匹配
            if keyword.lower() in node.name.lower():
                results.append(node)

        return results

    def get_tree_stats(self) -> Dict[str, Any]:
        """
        函数级注释：获取树统计信息
        返回值：统计信息字典
        """
        stats = self.root.get_stats()

        return {
            "total_files": stats.file_count,
            "total_folders": stats.folder_count,
            "total_size": stats.total_size,
            "max_depth": stats.max_depth,
            "root_path": self.root.path,
            "node_count": len(self._node_map)
        }

    def get_subtree(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        函数级注释：获取子树结构
        参数：
            node_id - 根节点ID
        返回值：子树字典或None
        """
        node = self._node_map.get(node_id)
        if not node:
            return None
        return node.to_dict()

    def export_tree_structure(self) -> Dict[str, Any]:
        """
        函数级注释：导出完整树结构
        返回值：树结构字典
        """
        return self.root.to_dict()

    def apply_visitor(self, visitor: NodeVisitor, node_id: Optional[str] = None) -> Any:
        """
        函数级注释：应用访问者模式
        参数：
            visitor - 访问者对象
            node_id - 起始节点ID（None表示从根节点开始）
        返回值：访问结果
        """
        node = self.root
        if node_id:
            node = self._node_map.get(node_id)
            if not node:
                return None

        return node.accept(visitor)

    def filter_nodes(
        self,
        predicate_filter: callable,
        node_id: Optional[str] = None
    ) -> List[DocumentNode]:
        """
        函数级注释：过滤节点
        参数：
            predicate_filter - 谓词函数
            node_id - 起始节点ID
        返回值：符合条件的节点列表
        """
        start_node = self.root
        if node_id:
            start_node = self._node_map.get(node_id)
            if not start_node:
                return []

        if isinstance(start_node, FolderNode):
            return start_node.filter(predicate_filter)
        return [start_node] if predicate_filter(start_node) else []

    def get_node_path(self, node_id: str) -> Optional[str]:
        """
        函数级注释：获取节点路径
        参数：
            node_id - 节点ID
        返回值：完整路径字符串
        """
        node = self._node_map.get(node_id)
        return node.path if node else None

    def get_node_ancestors(self, node_id: str) -> List[Dict[str, Any]]:
        """
        函数级注释：获取节点的所有祖先
        参数：
            node_id - 节点ID
        返回值：祖先节点列表
        """
        node = self._node_map.get(node_id)
        if not node:
            return []

        ancestors = node.ancestors()
        return [ancestor.to_dict() for ancestor in ancestors]


# 内部变量：导出公共接口
__all__ = [
    'DocumentTreeService',
    'TreeOperationResult',
]
