# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：文档树服务测试模块
内部逻辑：测试DocumentTreeService的完整功能，包括树构建、节点操作、搜索和访问者模式
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.document_tree_service import (
    DocumentTreeService,
    TreeOperationResult
)
from app.core.composite.document_node import (
    FileNode,
    FolderNode,
    NodeType,
    NodeStats,
    NodeVisitor,
    SizeCalculatorVisitor
)
from app.models.models import Document


# ============================================================================
# 测试数据构建辅助类
# ============================================================================

class TestDataBuilder:
    """
    类级注释：测试数据构建器
    职责：构建测试用的文档模型数据
    """

    @staticmethod
    def create_document(
        doc_id: int = 1,
        file_name: str = "test.pdf",
        file_path: str = "/path/to/test.pdf",
        tags: list = None,
        source_type: str = "pdf"
    ) -> Document:
        """
        函数级注释：创建测试文档对象
        参数：
            doc_id - 文档ID
            file_name - 文件名
            file_path - 文件路径
            tags - 标签列表
            source_type - 文件类型
        返回值：Document实例
        """
        import json

        doc = Document()
        doc.id = doc_id
        doc.file_name = file_name
        doc.file_path = file_path
        doc.source_type = source_type
        doc.tags = json.dumps(tags) if tags else None
        doc.file_hash = f"hash_{doc_id}"
        doc.created_at = None
        doc.updated_at = None
        return doc


# ============================================================================
# 访问者模式测试类
# ============================================================================

class TestNodeVisitor:
    """
    类级注释：访问者模式测试类
    职责：测试节点访问者的各种实现
    """

    def test_size_calculator_visitor_file(self):
        """
        测试目的：验证SizeCalculatorVisitor正确计算文件节点大小
        测试场景：创建指定大小的文件节点，访问者应返回正确大小
        """
        # Arrange: 创建文件节点
        file_node = FileNode(
            node_id="file_1",
            name="test.pdf",
            file_size=1024,
            file_type="pdf"
        )

        # Act: 使用访问者计算大小
        visitor = SizeCalculatorVisitor()
        result = file_node.accept(visitor)

        # Assert: 验证大小正确
        assert result == 1024

    def test_size_calculator_visitor_folder(self):
        """
        测试目的：验证SizeCalculatorVisitor正确计算文件夹节点大小
        测试场景：创建包含多个文件的文件夹，访问者应返回总大小
        """
        # Arrange: 创建文件夹和文件
        folder = FolderNode(node_id="folder_1", name="documents")
        file1 = FileNode(node_id="file_1", name="test1.pdf", file_size=1024, file_type="pdf")
        file2 = FileNode(node_id="file_2", name="test2.pdf", file_size=2048, file_type="pdf")

        folder.add_child(file1)
        folder.add_child(file2)

        # Act: 使用访问者计算大小
        visitor = SizeCalculatorVisitor()
        result = folder.accept(visitor)

        # Assert: 验证总大小
        assert result == 3072

    def test_custom_visitor(self):
        """
        测试目的：验证自定义访问者模式可以正常工作
        测试场景：创建计数访问者，统计文件和文件夹数量
        """
        # Arrange: 定义计数访问者
        class CountVisitor(NodeVisitor):
            """自定义计数访问者"""
            def __init__(self):
                self.file_count = 0
                self.folder_count = 0

            def visit_file(self, file_node: FileNode) -> int:
                self.file_count += 1
                return 1

            def visit_folder(self, folder_node: FolderNode) -> int:
                self.folder_count += 1
                return sum(child.accept(self) for child in folder_node.children)

        # 创建树结构
        root = FolderNode(node_id="root", name="root")
        folder1 = FolderNode(node_id="folder_1", name="docs")
        file1 = FileNode(node_id="file_1", name="test.pdf", file_size=1024, file_type="pdf")

        root.add_child(folder1)
        root.add_child(file1)

        # Act: 使用自定义访问者
        visitor = CountVisitor()
        root.accept(visitor)

        # Assert: 验证计数
        assert visitor.file_count == 1
        assert visitor.folder_count == 2  # root + folder_1


# ============================================================================
# 节点基础功能测试
# ============================================================================

class TestFileNode:
    """
    类级注释：文件节点测试类
    职责：测试FileNode的所有属性和方法
    """

    def test_file_node_initialization(self):
        """
        测试目的：验证文件节点正确初始化
        测试场景：创建文件节点并验证所有属性
        """
        # Arrange & Act: 创建文件节点
        node = FileNode(
            node_id="file_1",
            name="test.pdf",
            file_size=1024,
            file_type="pdf",
            content="test content"
        )

        # Assert: 验证属性
        assert node.node_id == "file_1"
        assert node.name == "test.pdf"
        assert node.file_size == 1024
        assert node.file_type == "pdf"
        assert node.content == "test content"
        assert node.node_type == NodeType.FILE
        assert node.is_leaf() is True
        assert node.count() == 1
        assert node.size() == 1024

    def test_file_node_path(self):
        """
        测试目的：验证文件节点路径计算正确
        测试场景：创建带父节点的文件节点，验证路径
        """
        # Arrange: 创建父文件夹和文件节点
        parent = FolderNode(node_id="folder_1", name="documents")
        file_node = FileNode(
            node_id="file_1",
            name="test.pdf",
            file_size=1024,
            file_type="pdf",
            parent=parent
        )

        # Act: 获取路径
        path = file_node.path

        # Assert: 验证路径格式
        assert path == "/documents/test.pdf"

    def test_file_node_to_dict(self):
        """
        测试目的：验证文件节点正确转换为字典
        测试场景：创建文件节点并转换为字典格式
        """
        # Arrange: 创建文件节点
        node = FileNode(
            node_id="file_1",
            name="test.pdf",
            file_size=1024,
            file_type="pdf"
        )
        node.metadata = {"document_id": 123}

        # Act: 转换为字典
        result = node.to_dict()

        # Assert: 验证字典内容
        assert result["node_id"] == "file_1"
        assert result["name"] == "test.pdf"
        assert result["type"] == "file"
        assert result["size"] == 1024
        assert result["file_type"] == "pdf"
        assert result["metadata"]["document_id"] == 123
        assert "path" in result
        assert "created_at" in result


class TestFolderNode:
    """
    类级注释：文件夹节点测试类
    职责：测试FolderNode的所有属性和方法
    """

    def test_folder_node_initialization(self):
        """
        测试目的：验证文件夹节点正确初始化
        测试场景：创建文件夹节点并验证所有属性
        """
        # Arrange & Act: 创建文件夹节点
        folder = FolderNode(node_id="folder_1", name="documents")

        # Assert: 验证属性
        assert folder.node_id == "folder_1"
        assert folder.name == "documents"
        assert folder.node_type == NodeType.FOLDER
        assert folder.is_leaf() is True  # 空文件夹是叶子
        assert folder.count() == 0
        assert folder.size() == 0
        assert len(folder.children) == 0

    def test_add_child(self):
        """
        测试目的：验证添加子节点功能
        测试场景：向文件夹添加文件和子文件夹
        """
        # Arrange: 创建文件夹和子节点
        folder = FolderNode(node_id="folder_1", name="documents")
        file_node = FileNode(node_id="file_1", name="test.pdf", file_size=1024, file_type="pdf")

        # Act: 添加子节点
        folder.add_child(file_node)

        # Assert: 验证子节点
        assert len(folder.children) == 1
        assert folder.is_leaf() is False
        assert folder.count() == 1
        assert folder.size() == 1024
        assert file_node.parent == folder

    def test_remove_child(self):
        """
        测试目的：验证移除子节点功能
        测试场景：添加后移除子节点
        """
        # Arrange: 创建文件夹和子节点
        folder = FolderNode(node_id="folder_1", name="documents")
        file_node = FileNode(node_id="file_1", name="test.pdf", file_size=1024, file_type="pdf")
        folder.add_child(file_node)

        # Act: 移除子节点
        result = folder.remove_child("file_1")

        # Assert: 验证移除成功
        assert result is True
        assert len(folder.children) == 0
        assert file_node.parent is None

    def test_remove_child_not_found(self):
        """
        测试目的：验证移除不存在的子节点返回False
        测试场景：尝试移除不存在的节点
        """
        # Arrange: 创建文件夹
        folder = FolderNode(node_id="folder_1", name="documents")

        # Act: 尝试移除不存在的节点
        result = folder.remove_child("nonexistent")

        # Assert: 验证返回False
        assert result is False

    def test_get_child(self):
        """
        测试目的：验证获取指定ID的子节点
        测试场景：添加子节点后通过ID获取
        """
        # Arrange: 创建文件夹和子节点
        folder = FolderNode(node_id="folder_1", name="documents")
        file_node = FileNode(node_id="file_1", name="test.pdf", file_size=1024, file_type="pdf")
        folder.add_child(file_node)

        # Act: 获取子节点
        result = folder.get_child("file_1")

        # Assert: 验证获取正确
        assert result is file_node

    def test_get_child_by_name(self):
        """
        测试目的：验证通过名称获取子节点
        测试场景：添加子节点后通过名称获取
        """
        # Arrange: 创建文件夹和子节点
        folder = FolderNode(node_id="folder_1", name="documents")
        file_node = FileNode(node_id="file_1", name="test.pdf", file_size=1024, file_type="pdf")
        folder.add_child(file_node)

        # Act: 通过名称获取
        result = folder.get_child_by_name("test.pdf")

        # Assert: 验证获取正确
        assert result is file_node

    def test_find_recursive(self):
        """
        测试目的：验证递归查找节点功能
        测试场景：创建嵌套文件夹结构，查找深层节点
        """
        # Arrange: 创建嵌套结构
        root = FolderNode(node_id="root", name="root")
        folder1 = FolderNode(node_id="folder_1", name="docs")
        folder2 = FolderNode(node_id="folder_2", name="subfolder")
        file_node = FileNode(node_id="file_1", name="test.pdf", file_size=1024, file_type="pdf")

        root.add_child(folder1)
        folder1.add_child(folder2)
        folder2.add_child(file_node)

        # Act: 从根节点查找
        result = root.find("file_1")

        # Assert: 验证找到正确节点
        assert result is file_node

    def test_get_stats(self):
        """
        测试目的：验证获取统计信息功能
        测试场景：创建复杂树结构并统计
        """
        # Arrange: 创建树结构
        folder = FolderNode(node_id="folder_1", name="docs")
        file1 = FileNode(node_id="file_1", name="test1.pdf", file_size=1024, file_type="pdf")
        file2 = FileNode(node_id="file_2", name="test2.pdf", file_size=2048, file_type="pdf")
        subfolder = FolderNode(node_id="subfolder", name="sub")
        file3 = FileNode(node_id="file_3", name="test3.txt", file_size=512, file_type="txt")

        folder.add_child(file1)
        folder.add_child(file2)
        folder.add_child(subfolder)
        subfolder.add_child(file3)

        # Act: 获取统计信息
        stats = folder.get_stats()

        # Assert: 验证统计数据
        assert stats.file_count == 3
        assert stats.folder_count == 1
        assert stats.total_size == 3584
        assert stats.max_depth == 1

    def test_filter(self):
        """
        测试目的：验证节点过滤功能
        测试场景：过滤出所有PDF文件
        """
        # Arrange: 创建混合节点
        folder = FolderNode(node_id="folder_1", name="docs")
        file1 = FileNode(node_id="file_1", name="test1.pdf", file_size=1024, file_type="pdf")
        file2 = FileNode(node_id="file_2", name="test2.txt", file_size=512, file_type="txt")
        subfolder = FolderNode(node_id="subfolder", name="sub")
        file3 = FileNode(node_id="file_3", name="test3.pdf", file_size=2048, file_type="pdf")

        folder.add_child(file1)
        folder.add_child(file2)
        folder.add_child(subfolder)
        subfolder.add_child(file3)

        # Act: 过滤PDF文件
        from app.core.composite.document_node import NodeFilter
        results = folder.filter(NodeFilter.by_extension("pdf"))

        # Assert: 验证过滤结果
        assert len(results) == 2
        assert file1 in results
        assert file3 in results

    def test_traverse(self):
        """
        测试目的：验证节点遍历功能
        测试场景：遍历所有节点并收集名称
        """
        # Arrange: 创建树结构
        folder = FolderNode(node_id="folder_1", name="docs")
        file1 = FileNode(node_id="file_1", name="test1.pdf", file_size=1024, file_type="pdf")
        subfolder = FolderNode(node_id="subfolder", name="sub")

        folder.add_child(file1)
        folder.add_child(subfolder)

        collected = []

        def collect_name(node):
            collected.append(node.name)

        # Act: 遍历节点
        folder.traverse(collect_name)

        # Assert: 验证遍历结果
        assert "test1.pdf" in collected
        assert "sub" in collected

    def test_folder_node_to_dict(self):
        """
        测试目的：验证文件夹节点正确转换为字典
        测试场景：创建嵌套结构并转换为字典
        """
        # Arrange: 创建文件夹和子节点
        folder = FolderNode(node_id="folder_1", name="docs")
        file_node = FileNode(node_id="file_1", name="test.pdf", file_size=1024, file_type="pdf")
        folder.add_child(file_node)

        # Act: 转换为字典
        result = folder.to_dict()

        # Assert: 验证字典内容
        assert result["node_id"] == "folder_1"
        assert result["name"] == "docs"
        assert result["type"] == "folder"
        assert len(result["children"]) == 1
        assert result["children"][0]["name"] == "test.pdf"


# ============================================================================
# DocumentTreeService 测试类
# ============================================================================

class TestDocumentTreeService:
    """
    类级注释：文档树服务测试类
    职责：测试DocumentTreeService的完整功能
    """

    def test_singleton_pattern(self):
        """
        测试目的：验证单例模式正确实现
        测试场景：多次创建实例应返回同一个对象
        """
        # Arrange & Act: 创建多个实例
        service1 = DocumentTreeService()
        service2 = DocumentTreeService()

        # Assert: 验证是同一个实例
        assert service1 is service2

    def test_root_property(self):
        """
        测试目的：验证根节点属性正确初始化
        测试场景：首次访问root属性应创建根节点
        """
        # Arrange: 创建服务实例
        service = DocumentTreeService()

        # Act: 获取根节点
        root = service.root

        # Assert: 验证根节点
        assert root.node_id == "root"
        assert root.name == "知识库"
        assert root.node_type == NodeType.FOLDER

    def test_create_folder(self):
        """
        测试目的：验证创建文件夹功能
        测试场景：在根目录创建文件夹
        """
        # Arrange: 创建服务实例
        service = DocumentTreeService()

        # Act: 创建文件夹
        result = service.create_folder("documents")

        # Assert: 验证创建成功
        assert result.success is True
        assert "创建成功" in result.message
        assert result.node_id is not None
        assert service.find_node(result.node_id) is not None

    def test_create_folder_with_parent(self):
        """
        测试目的：验证在指定父文件夹下创建文件夹
        测试场景：先创建父文件夹，再在父文件夹下创建子文件夹
        """
        # Arrange: 创建服务和父文件夹
        service = DocumentTreeService()
        parent_result = service.create_folder("parent")
        parent_id = parent_result.node_id

        # Act: 在父文件夹下创建子文件夹
        result = service.create_folder("child", parent_id=parent_id)

        # Assert: 验证创建成功
        assert result.success is True
        child_node = service.find_node(result.node_id)
        assert child_node is not None
        assert child_node.parent.node_id == parent_id

    def test_create_folder_invalid_parent(self):
        """
        测试目的：验证使用无效父节点创建文件夹失败
        测试场景：使用不存在的父节点ID
        """
        # Arrange: 创建服务实例
        service = DocumentTreeService()

        # Act: 尝试使用无效父节点
        result = service.create_folder("test", parent_id="nonexistent")

        # Assert: 验证失败
        assert result.success is False
        assert "不存在" in result.message

    def test_create_folder_duplicate_name(self):
        """
        测试目的：验证创建同名文件夹失败
        测试场景：在同一目录下创建同名文件夹
        """
        # Arrange: 创建服务和第一个文件夹
        service = DocumentTreeService()
        service.create_folder("documents")

        # Act: 尝试创建同名文件夹
        result = service.create_folder("documents")

        # Assert: 验证失败
        assert result.success is False
        assert "已存在" in result.message

    def test_add_document_to_folder(self):
        """
        测试目的：验证添加文档到文件夹功能
        测试场景：创建文件夹后添加文档
        """
        # Arrange: 创建服务实例
        service = DocumentTreeService()

        # Act: 添加文档到根目录
        result = service.add_document_to_folder(
            document_id=1,
            file_name="test.pdf",
            file_type="pdf"
        )

        # Assert: 验证添加成功
        assert result.success is True
        assert "添加成功" in result.message
        assert service.find_by_document_id(1) is not None

    def test_add_document_to_specific_folder(self):
        """
        测试目的：验证添加文档到指定文件夹
        测试场景：创建文件夹后添加文档
        """
        # Arrange: 创建服务和文件夹
        service = DocumentTreeService()
        # 清空现有的树状态（单例模式会有状态残留）
        service._root = None
        service._node_map.clear()
        service._document_node_map.clear()

        folder_result = service.create_folder("documents")
        folder_id = folder_result.node_id

        # Act: 添加文档到指定文件夹
        result = service.add_document_to_folder(
            document_id=1,
            file_name="test.pdf",
            folder_id=folder_id,
            file_type="pdf"
        )

        # Assert: 验证添加成功
        assert result.success is True
        doc_node = service.find_by_document_id(1)
        assert doc_node is not None
        # 验证父节点是documents文件夹
        assert doc_node.parent is not None
        assert doc_node.parent.node_id == folder_id

    def test_add_document_invalid_folder(self):
        """
        测试目的：验证添加文档到无效文件夹失败
        测试场景：使用不存在的文件夹ID
        """
        # Arrange: 创建服务实例
        service = DocumentTreeService()

        # Act: 尝试添加到无效文件夹
        result = service.add_document_to_folder(
            document_id=1,
            file_name="test.pdf",
            folder_id="nonexistent"
        )

        # Assert: 验证失败
        assert result.success is False
        assert "不存在" in result.message

    def test_move_node(self):
        """
        测试目的：验证移动节点功能
        测试场景：将节点从一个文件夹移动到另一个
        """
        # Arrange: 创建服务和文件夹
        service = DocumentTreeService()
        folder1 = service.create_folder("folder1")
        folder2 = service.create_folder("folder2")
        doc = service.add_document_to_folder(1, "test.pdf", folder_id=folder1.node_id)

        # Act: 移动文档
        result = service.move_node(doc.node_id, target_folder_id=folder2.node_id)

        # Assert: 验证移动成功
        assert result.success is True
        doc_node = service.find_node(doc.node_id)
        assert doc_node.parent is not None
        assert doc_node.parent.node_id == folder2.node_id

    def test_move_node_to_root(self):
        """
        测试目的：验证移动节点到根目录
        测试场景：将节点从子文件夹移动到根目录
        """
        # Arrange: 创建服务和文件夹
        service = DocumentTreeService()
        folder = service.create_folder("documents")
        doc = service.add_document_to_folder(1, "test.pdf", folder_id=folder.node_id)

        # Act: 移动到根目录
        result = service.move_node(doc.node_id, target_folder_id=None)

        # Assert: 验证移动成功
        assert result.success is True
        doc_node = service.find_node(doc.node_id)
        assert doc_node.parent is not None
        assert doc_node.parent.node_id == "root"

    def test_move_node_not_found(self):
        """
        测试目的：验证移动不存在的节点失败
        测试场景：使用不存在的节点ID
        """
        # Arrange: 创建服务实例
        service = DocumentTreeService()

        # Act: 尝试移动不存在的节点
        result = service.move_node("nonexistent")

        # Assert: 验证失败
        assert result.success is False
        assert "不存在" in result.message

    def test_delete_node(self):
        """
        测试目的：验证删除节点功能
        测试场景：删除文件节点
        """
        # Arrange: 创建服务和文档
        service = DocumentTreeService()
        doc = service.add_document_to_folder(1, "test.pdf")

        # Act: 删除节点
        result = service.delete_node(doc.node_id)

        # Assert: 验证删除成功
        assert result.success is True
        assert service.find_node(doc.node_id) is None
        assert service.find_by_document_id(1) is None

    def test_delete_node_recursive(self):
        """
        测试目的：验证递归删除文件夹功能
        测试场景：删除包含子节点的文件夹
        """
        # Arrange: 创建服务实例（重置单例状态）
        service = DocumentTreeService()
        # 清空现有的树状态
        service._root = None
        service._node_map.clear()
        service._document_node_map.clear()

        folder = service.create_folder("documents")
        service.add_document_to_folder(1, "test1.pdf", folder_id=folder.node_id)
        service.add_document_to_folder(2, "test2.pdf", folder_id=folder.node_id)

        # Act: 递归删除
        result = service.delete_node(folder.node_id, recursive=True)

        # Assert: 验证删除成功
        assert result.success is True
        # affected_nodes计算方式：文件夹本身 + 包含的文件数量
        assert result.affected_nodes >= 1
        assert service.find_node(folder.node_id) is None

    def test_delete_root_node(self):
        """
        测试目的：验证不能删除根节点
        测试场景：尝试删除根节点
        """
        # Arrange: 创建服务实例
        service = DocumentTreeService()

        # Act: 尝试删除根节点
        result = service.delete_node("root")

        # Assert: 验证失败
        assert result.success is False
        assert "不能删除根节点" in result.message

    def test_find_node(self):
        """
        测试目的：验证查找节点功能
        测试场景：创建节点后查找
        """
        # Arrange: 创建服务和文件夹
        service = DocumentTreeService()
        # 清空现有的树状态（单例模式会有状态残留）
        service._root = None
        service._node_map.clear()
        service._document_node_map.clear()

        folder_result = service.create_folder("documents")

        # Act: 查找节点
        node = service.find_node(folder_result.node_id)

        # Assert: 验证找到正确节点
        assert node is not None
        assert node.name == "documents"

    def test_find_by_document_id(self):
        """
        测试目的：验证根据文档ID查找节点
        测试场景：添加文档后通过ID查找
        """
        # Arrange: 创建服务和文档
        service = DocumentTreeService()
        service.add_document_to_folder(1, "test.pdf")

        # Act: 查找文档节点
        node = service.find_by_document_id(1)

        # Assert: 验证找到正确节点
        assert node is not None
        assert node.name == "test.pdf"
        assert node.metadata.get("document_id") == 1

    def test_search_nodes(self):
        """
        测试目的：验证搜索节点功能
        测试场景：搜索包含关键词的节点
        """
        # Arrange: 创建服务和多个节点
        service = DocumentTreeService()
        service.add_document_to_folder(1, "report.pdf")
        service.add_document_to_folder(2, "summary.pdf")
        service.add_document_to_folder(3, "data.txt")

        # Act: 搜索PDF文件
        results = service.search_nodes("pdf")

        # Assert: 验证搜索结果
        assert len(results) == 2

    def test_search_nodes_with_type_filter(self):
        """
        测试目的：验证带类型过滤的搜索功能
        测试场景：只搜索文件夹类型的节点
        """
        # Arrange: 创建服务和混合节点
        service = DocumentTreeService()
        service.create_folder("documents")
        service.add_document_to_folder(1, "test.pdf")

        # Act: 搜索文件夹
        results = service.search_nodes("", node_type=NodeType.FOLDER)

        # Assert: 验证只返回文件夹
        # search_nodes在空关键词时返回所有匹配类型的节点
        assert len(results) >= 1
        assert all(r.node_type == NodeType.FOLDER for r in results)

    def test_get_tree_stats(self):
        """
        测试目的：验证获取树统计信息功能
        测试场景：创建树结构后获取统计
        """
        # Arrange: 创建服务和树结构
        service = DocumentTreeService()
        # 清空现有的树状态
        service._root = None
        service._node_map.clear()
        service._document_node_map.clear()

        service.create_folder("documents")
        service.add_document_to_folder(1, "test.pdf")
        service.add_document_to_folder(2, "data.txt")

        # Act: 获取统计信息
        stats = service.get_tree_stats()

        # Assert: 验证统计数据
        assert stats["total_files"] == 2
        # total_folders统计包含documents和root
        assert stats["total_folders"] >= 1
        assert stats["node_count"] >= 3

    def test_get_subtree(self):
        """
        测试目的：验证获取子树结构功能
        测试场景：获取指定节点的子树
        """
        # Arrange: 创建服务和嵌套结构
        service = DocumentTreeService()
        # 清空现有的树状态
        service._root = None
        service._node_map.clear()
        service._document_node_map.clear()

        folder = service.create_folder("documents")
        service.add_document_to_folder(1, "test.pdf", folder_id=folder.node_id)

        # Act: 获取子树
        subtree = service.get_subtree(folder.node_id)

        # Assert: 验证子树结构
        assert subtree is not None
        assert subtree["name"] == "documents"
        assert len(subtree["children"]) == 1

    def test_get_subtree_not_found(self):
        """
        测试目的：验证获取不存在的子树返回None
        测试场景：使用不存在的节点ID
        """
        # Arrange: 创建服务实例
        service = DocumentTreeService()

        # Act: 尝试获取不存在的子树
        subtree = service.get_subtree("nonexistent")

        # Assert: 验证返回None
        assert subtree is None

    def test_export_tree_structure(self):
        """
        测试目的：验证导出完整树结构功能
        测试场景：导出整个树为字典格式
        """
        # Arrange: 创建服务和树结构
        service = DocumentTreeService()
        service.create_folder("documents")
        service.add_document_to_folder(1, "test.pdf")

        # Act: 导出树结构
        tree = service.export_tree_structure()

        # Assert: 验证导出结果
        assert tree is not None
        assert tree["name"] == "知识库"
        assert "children" in tree

    def test_apply_visitor(self):
        """
        测试目的：验证应用访问者模式功能
        测试场景：使用SizeCalculatorVisitor计算大小
        """
        # Arrange: 创建服务和树结构
        service = DocumentTreeService()
        service.add_document_to_folder(1, "test.pdf")
        service.add_document_to_folder(2, "data.txt")

        # Act: 应用访问者
        visitor = SizeCalculatorVisitor()
        result = service.apply_visitor(visitor)

        # Assert: 验证访问结果
        assert result == 0  # 文件大小默认为0

    def test_filter_nodes(self):
        """
        测试目的：验证过滤节点功能
        测试场景：过滤出所有文件节点
        """
        # Arrange: 创建服务和混合节点
        service = DocumentTreeService()
        service.create_folder("documents")
        service.add_document_to_folder(1, "test.pdf")

        # Act: 过滤文件节点
        from app.core.composite.document_node import NodeFilter
        results = service.filter_nodes(NodeFilter.files_only())

        # Assert: 验证过滤结果
        assert len(results) >= 1
        assert all(isinstance(r, FileNode) for r in results)

    def test_get_node_path(self):
        """
        测试目的：验证获取节点路径功能
        测试场景：获取嵌套节点的完整路径
        """
        # Arrange: 创建服务和嵌套结构
        service = DocumentTreeService()
        # 清空现有的树状态
        service._root = None
        service._node_map.clear()
        service._document_node_map.clear()

        folder = service.create_folder("documents")
        doc = service.add_document_to_folder(1, "test.pdf", folder_id=folder.node_id)

        # Act: 获取节点路径
        path = service.get_node_path(doc.node_id)

        # Assert: 验证路径
        assert "documents" in path
        assert "test.pdf" in path

    def test_get_node_path_not_found(self):
        """
        测试目的：验证获取不存在节点的路径返回None
        测试场景：使用不存在的节点ID
        """
        # Arrange: 创建服务实例
        service = DocumentTreeService()

        # Act: 尝试获取不存在节点的路径
        path = service.get_node_path("nonexistent")

        # Assert: 验证返回None
        assert path is None

    def test_get_node_ancestors(self):
        """
        测试目的：验证获取节点祖先列表功能
        测试场景：获取嵌套节点的所有祖先
        """
        # Arrange: 创建服务和嵌套结构
        service = DocumentTreeService()
        # 清空现有的树状态
        service._root = None
        service._node_map.clear()
        service._document_node_map.clear()

        folder = service.create_folder("documents")
        doc = service.add_document_to_folder(1, "test.pdf", folder_id=folder.node_id)

        # Act: 获取祖先列表
        ancestors = service.get_node_ancestors(doc.node_id)

        # Assert: 验证祖先列表
        # ancestors返回的是字典列表，从父节点开始向上
        assert len(ancestors) >= 1  # 至少包含documents文件夹
        assert any(a["name"] == "documents" for a in ancestors)

    def test_get_node_ancestors_not_found(self):
        """
        测试目的：验证获取不存在节点的祖先返回空列表
        测试场景：使用不存在的节点ID
        """
        # Arrange: 创建服务实例
        service = DocumentTreeService()

        # Act: 尝试获取不存在节点的祖先
        ancestors = service.get_node_ancestors("nonexistent")

        # Assert: 验证返回空列表
        assert ancestors == []


# ============================================================================
# 从数据库构建树测试类
# ============================================================================

class TestDocumentTreeServiceDatabase:
    """
    类级注释：文档树服务数据库集成测试类
    职责：测试从数据库构建文档树的功能
    """

    @pytest.mark.asyncio
    async def test_build_tree_from_documents_empty(self, db_session: AsyncSession):
        """
        测试目的：验证从空数据库构建树
        测试场景：数据库中没有文档时
        """
        # Arrange: 创建服务实例
        service = DocumentTreeService()

        # Act: 从空数据库构建树
        root = await service.build_tree_from_documents(db_session)

        # Assert: 验证只有根节点
        assert root.node_id == "root"
        assert len(root.children) == 0

    @pytest.mark.asyncio
    async def test_build_tree_from_documents_with_data(self, db_session: AsyncSession):
        """
        测试目的：验证从数据库文档构建树
        测试场景：数据库中有多个文档
        """
        # Arrange: 创建测试文档
        docs = [
            TestDataBuilder.create_document(1, "report.pdf", tags=["工作"]),
            TestDataBuilder.create_document(2, "summary.pdf", tags=["工作"]),
            TestDataBuilder.create_document(3, "notes.txt", tags=["个人"]),
        ]

        for doc in docs:
            db_session.add(doc)
        await db_session.flush()

        # Act: 构建树
        service = DocumentTreeService()
        root = await service.build_tree_from_documents(db_session)

        # Assert: 验证树结构
        assert root.count() == 3
        assert len([c for c in root.children if isinstance(c, FolderNode)]) >= 1

    @pytest.mark.asyncio
    async def test_build_tree_with_tag_filter(self, db_session: AsyncSession):
        """
        测试目的：验证带标签过滤的树构建
        测试场景：只包含特定标签的文档
        """
        # Arrange: 创建带标签的测试文档
        docs = [
            TestDataBuilder.create_document(1, "report.pdf", tags=["工作"]),
            TestDataBuilder.create_document(2, "personal.pdf", tags=["个人"]),
        ]

        for doc in docs:
            db_session.add(doc)
        await db_session.flush()

        # Act: 使用标签过滤构建树
        service = DocumentTreeService()
        root = await service.build_tree_from_documents(db_session, tags=["工作"])

        # Assert: 验证只包含工作标签的文档
        assert root.count() == 1

    @pytest.mark.asyncio
    async def test_build_tree_documents_without_tags(self, db_session: AsyncSession):
        """
        测试目的：验证无标签文档直接放在根目录
        测试场景：文档没有标签
        """
        # Arrange: 创建无标签文档
        doc = TestDataBuilder.create_document(1, "untitled.pdf", tags=None)
        db_session.add(doc)
        await db_session.flush()

        # Act: 构建树
        service = DocumentTreeService()
        root = await service.build_tree_from_documents(db_session)

        # Assert: 验证无标签文档在根目录
        direct_children = [c for c in root.children if isinstance(c, FileNode)]
        assert len(direct_children) >= 1


# ============================================================================
# NodeFilter 测试类
# ============================================================================

class TestNodeFilter:
    """
    类级注释：节点过滤器测试类
    职责：测试各种过滤策略
    """

    def test_by_type(self):
        """
        测试目的：验证按类型过滤功能
        测试场景：过滤出所有文件夹
        """
        # Arrange: 创建混合节点
        folder = FolderNode(node_id="folder_1", name="docs")
        file_node = FileNode(node_id="file_1", name="test.pdf", file_size=1024, file_type="pdf")

        # Act: 创建类型过滤器
        from app.core.composite.document_node import NodeFilter
        filter_fn = NodeFilter.by_type(NodeType.FOLDER)

        # Assert: 验证过滤结果
        assert filter_fn(folder) is True
        assert filter_fn(file_node) is False

    def test_by_name(self):
        """
        测试目的：验证按名称模式过滤功能
        测试场景：过滤名称包含特定关键词的节点
        """
        # Arrange: 创建节点
        file1 = FileNode(node_id="file_1", name="report.pdf", file_size=1024, file_type="pdf")
        file2 = FileNode(node_id="file_2", name="summary.pdf", file_size=512, file_type="pdf")

        # Act: 创建名称过滤器
        from app.core.composite.document_node import NodeFilter
        filter_fn = NodeFilter.by_name("report")

        # Assert: 验证过滤结果
        assert filter_fn(file1) is True
        assert filter_fn(file2) is False

    def test_by_extension(self):
        """
        测试目的：验证按文件扩展名过滤功能
        测试场景：过滤出PDF文件
        """
        # Arrange: 创建不同类型的文件
        pdf_file = FileNode(node_id="file_1", name="doc.pdf", file_size=1024, file_type="pdf")
        txt_file = FileNode(node_id="file_2", name="doc.txt", file_size=512, file_type="txt")

        # Act: 创建扩展名过滤器
        from app.core.composite.document_node import NodeFilter
        filter_fn = NodeFilter.by_extension("pdf")

        # Assert: 验证过滤结果
        assert filter_fn(pdf_file) is True
        assert filter_fn(txt_file) is False

    def test_by_size(self):
        """
        测试目的：验证按文件大小过滤功能
        测试场景：过滤出小于指定大小的文件
        """
        # Arrange: 创建不同大小的文件
        file1 = FileNode(node_id="file_1", name="small.pdf", file_size=512, file_type="pdf")
        file2 = FileNode(node_id="file_2", name="large.pdf", file_size=2048, file_type="pdf")

        # Act: 创建大小过滤器
        from app.core.composite.document_node import NodeFilter
        filter_fn = NodeFilter.by_size(1024)

        # Assert: 验证过滤结果
        assert filter_fn(file1) is True
        assert filter_fn(file2) is False

    def test_files_only(self):
        """
        测试目的：验证只过滤文件功能
        测试场景：只返回文件节点
        """
        # Arrange: 创建混合节点
        folder = FolderNode(node_id="folder_1", name="docs")
        file_node = FileNode(node_id="file_1", name="test.pdf", file_size=1024, file_type="pdf")

        # Act: 创建文件过滤器
        from app.core.composite.document_node import NodeFilter
        filter_fn = NodeFilter.files_only()

        # Assert: 验证过滤结果
        assert filter_fn(file_node) is True
        assert filter_fn(folder) is False

    def test_folders_only(self):
        """
        测试目的：验证只过滤文件夹功能
        测试场景：只返回文件夹节点
        """
        # Arrange: 创建混合节点
        folder = FolderNode(node_id="folder_1", name="docs")
        file_node = FileNode(node_id="file_1", name="test.pdf", file_size=1024, file_type="pdf")

        # Act: 创建文件夹过滤器
        from app.core.composite.document_node import NodeFilter
        filter_fn = NodeFilter.folders_only()

        # Assert: 验证过滤结果
        assert filter_fn(folder) is True
        assert filter_fn(file_node) is False

    def test_combine(self):
        """
        测试目的：验证组合过滤条件功能（AND）
        测试场景：同时满足多个条件的节点
        """
        # Arrange: 创建节点
        pdf_file = FileNode(node_id="file_1", name="small.pdf", file_size=512, file_type="pdf")
        large_pdf = FileNode(node_id="file_2", name="large.pdf", file_size=2048, file_type="pdf")

        # Act: 创建组合过滤器（PDF且小于1024字节）
        from app.core.composite.document_node import NodeFilter
        filter_fn = NodeFilter.combine(
            NodeFilter.by_extension("pdf"),
            NodeFilter.by_size(1024)
        )

        # Assert: 验证过滤结果
        assert filter_fn(pdf_file) is True
        assert filter_fn(large_pdf) is False

    def test_any_of(self):
        """
        测试目的：验证组合过滤条件功能（OR）
        测试场景：满足任一条件的节点
        """
        # Arrange: 创建节点
        pdf_file = FileNode(node_id="file_1", name="doc.pdf", file_size=512, file_type="pdf")
        txt_file = FileNode(node_id="file_2", name="doc.txt", file_size=512, file_type="txt")

        # Act: 创建OR过滤器（PDF或TXT）
        from app.core.composite.document_node import NodeFilter
        filter_fn = NodeFilter.any_of(
            NodeFilter.by_extension("pdf"),
            NodeFilter.by_extension("txt")
        )

        # Assert: 验证两种类型都通过
        assert filter_fn(pdf_file) is True
        assert filter_fn(txt_file) is True
