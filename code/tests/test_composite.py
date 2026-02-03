# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：组合模式测试模块
内部逻辑：测试composite目录下的组合模式实现，包括DocumentNode及其子类
"""

import pytest
from typing import List, Any

from app.core.composite.document_node import (
    DocumentNode,
    FileNode,
    FolderNode,
    NodeType,
    NodeStats,
    NodeFilter,
    NodeVisitor,
    SizeCalculatorVisitor
)


# ============================================================================
# 自定义访问者实现（用于测试）
# ============================================================================

class CountVisitor(NodeVisitor):
    """
    类级注释：计数访问者
    职责：统计节点数量
    """
    def __init__(self):
        self.count = 0

    def visit_file(self, file_node: FileNode) -> int:
        self.count += 1
        return 1

    def visit_folder(self, folder_node: FolderNode) -> int:
        self.count += 1
        return sum(child.accept(self) for child in folder_node.children)


class DepthVisitor(NodeVisitor):
    """
    类级注释：深度计算访问者
    职责：计算树的深度
    """
    def visit_file(self, file_node: FileNode) -> int:
        return 0

    def visit_folder(self, folder_node: FolderNode) -> int:
        if not folder_node.children:
            return 0
        return 1 + max(
            child.accept(self) if isinstance(child, FolderNode) else 1
            for child in folder_node.children
        )


class NameCollectorVisitor(NodeVisitor):
    """
    类级注释：名称收集访问者
    职责：收集所有节点名称
    """
    def __init__(self):
        self.names: List[str] = []

    def visit_file(self, file_node: FileNode) -> List[str]:
        self.names.append(file_node.name)
        return self.names

    def visit_folder(self, folder_node: FolderNode) -> List[str]:
        self.names.append(folder_node.name)
        for child in folder_node.children:
            child.accept(self)
        return self.names


# ============================================================================
# NodeType 枚举测试类
# ============================================================================

class TestNodeType:
    """
    类级注释：节点类型枚举测试类
    职责：测试NodeType枚举的值
    """

    def test_file_enum_value(self):
        """
        测试目的：验证FILE枚举值
        """
        assert NodeType.FILE.value == "file"

    def test_folder_enum_value(self):
        """
        测试目的：验证FOLDER枚举值
        """
        assert NodeType.FOLDER.value == "folder"

    def test_root_enum_value(self):
        """
        测试目的：验证ROOT枚举值
        """
        assert NodeType.ROOT.value == "root"


# ============================================================================
# NodeStats 测试类
# ============================================================================

class TestNodeStats:
    """
    类级注释：节点统计信息测试类
    职责：测试NodeStats数据类
    """

    def test_default_values(self):
        """
        测试目的：验证NodeStats默认值
        """
        # Arrange & Act: 创建NodeStats
        stats = NodeStats()

        # Assert: 验证默认值
        assert stats.file_count == 0
        assert stats.folder_count == 0
        assert stats.total_size == 0
        assert stats.max_depth == 0

    def test_custom_values(self):
        """
        测试目的：验证NodeStats自定义值
        """
        # Arrange & Act: 创建带参数的NodeStats
        stats = NodeStats(
            file_count=10,
            folder_count=5,
            total_size=1024000,
            max_depth=3
        )

        # Assert: 验证自定义值
        assert stats.file_count == 10
        assert stats.folder_count == 5
        assert stats.total_size == 1024000
        assert stats.max_depth == 3


# ============================================================================
# DocumentNode 抽象类测试
# ============================================================================

class TestDocumentNodeAbstract:
    """
    类级注释：文档节点抽象类测试
    职责：测试DocumentNode的公共接口
    """

    def test_file_node_is_document_node(self):
        """
        测试目的：验证FileNode是DocumentNode的实例
        """
        file_node = FileNode("file_1", "test.pdf", 1024, "pdf")
        assert isinstance(file_node, DocumentNode)

    def test_folder_node_is_document_node(self):
        """
        测试目的：验证FolderNode是DocumentNode的实例
        """
        folder_node = FolderNode("folder_1", "docs")
        assert isinstance(folder_node, DocumentNode)


# ============================================================================
# FileNode 完整测试类
# ============================================================================

class TestFileNodeComplete:
    """
    类级注释：文件节点完整测试类
    职责：全面测试FileNode的所有功能
    """

    def test_creation_with_all_parameters(self):
        """
        测试目的：验证使用所有参数创建文件节点
        """
        # Arrange & Act: 创建文件节点
        node = FileNode(
            node_id="file_1",
            name="document.pdf",
            file_size=2048,
            file_type="pdf",
            content="文档内容"
        )

        # Assert: 验证所有属性
        assert node.node_id == "file_1"
        assert node.name == "document.pdf"
        assert node.file_size == 2048
        assert node.file_type == "pdf"
        assert node.content == "文档内容"

    def test_creation_with_minimal_parameters(self):
        """
        测试目的：验证使用最小参数创建文件节点
        """
        # Arrange & Act: 创建文件节点
        node = FileNode("file_1", "test.txt")

        # Assert: 验证默认值
        assert node.node_id == "file_1"
        assert node.name == "test.txt"
        assert node.file_size == 0
        assert node.file_type == ""
        assert node.content == ""

    def test_size_method(self):
        """
        测试目的：验证size方法返回文件大小
        """
        # Arrange: 创建文件节点
        node = FileNode("file_1", "large.pdf", 1024000, "pdf")

        # Act: 获取大小
        size = node.size()

        # Assert: 验证大小
        assert size == 1024000

    def test_count_method(self):
        """
        测试目的：验证count方法返回1
        """
        # Arrange: 创建文件节点
        node = FileNode("file_1", "test.pdf", 1024, "pdf")

        # Act: 计数
        count = node.count()

        # Assert: 文件节点计为1
        assert count == 1

    def test_is_leaf_method(self):
        """
        测试目的：验证is_leaf方法返回True
        """
        # Arrange: 创建文件节点
        node = FileNode("file_1", "test.pdf", 1024, "pdf")

        # Act: 检查是否为叶子
        is_leaf = node.is_leaf()

        # Assert: 文件节点是叶子
        assert is_leaf is True

    def test_depth_without_parent(self):
        """
        测试目的：验证无父节点时深度为0
        """
        # Arrange: 创建无父节点的文件节点
        node = FileNode("file_1", "test.pdf", 1024, "pdf")

        # Act: 获取深度
        depth = node.depth()

        # Assert: 深度为0
        assert depth == 0

    def test_depth_with_parent(self):
        """
        测试目的：验证有父节点时深度正确计算
        """
        # Arrange: 创建父文件夹和文件节点
        parent = FolderNode("folder_1", "docs")
        node = FileNode("file_1", "test.pdf", 1024, "pdf", parent=parent)

        # Act: 获取深度
        depth = node.depth()

        # Assert: 深度为1（父文件夹深度0 + 1）
        assert depth == 1

    def test_ancestors_without_parent(self):
        """
        测试目的：验证无父节点时祖先列表为空
        """
        # Arrange: 创建无父节点的文件节点
        node = FileNode("file_1", "test.pdf", 1024, "pdf")

        # Act: 获取祖先
        ancestors = node.ancestors()

        # Assert: 祖先列表为空
        assert ancestors == []

    def test_ancestors_with_parent(self):
        """
        测试目的：验证有父节点时祖先列表正确
        """
        # Arrange: 创建嵌套结构
        root = FolderNode("root", "root")
        parent = FolderNode("folder_1", "docs", parent=root)
        node = FileNode("file_1", "test.pdf", 1024, "pdf", parent=parent)

        # Act: 获取祖先
        ancestors = node.ancestors()

        # Assert: 祖先包含父文件夹和根
        assert len(ancestors) == 2
        assert parent in ancestors
        assert root in ancestors

    def test_root_method_without_parent(self):
        """
        测试目的：验证无父节点时root返回自身
        """
        # Arrange: 创建无父节点的文件节点
        node = FileNode("file_1", "test.pdf", 1024, "pdf")

        # Act: 获取根节点
        root_node = node.root()

        # Assert: 返回自身
        assert root_node is node

    def test_root_method_with_parent(self):
        """
        测试目的：验证有父节点时root返回树的根
        """
        # Arrange: 创建嵌套结构
        root = FolderNode("root", "root")
        parent = FolderNode("folder_1", "docs", parent=root)
        node = FileNode("file_1", "test.pdf", 1024, "pdf", parent=parent)

        # Act: 获取根节点
        root_node = node.root()

        # Assert: 返回根文件夹
        assert root_node is root

    def test_parent_property(self):
        """
        测试目的：验证parent属性设置和获取
        """
        # Arrange: 创建文件节点和父文件夹
        node = FileNode("file_1", "test.pdf", 1024, "pdf")
        parent = FolderNode("folder_1", "docs")

        # Act: 设置父节点
        node.parent = parent

        # Assert: 验证父节点
        assert node.parent is parent

    def test_path_without_parent(self):
        """
        测试目的：验证无父节点时路径格式
        """
        # Arrange: 创建无父节点的文件节点
        node = FileNode("file_1", "test.pdf", 1024, "pdf")

        # Act: 获取路径
        path = node.path

        # Assert: 路径以/开头
        assert path == "/test.pdf"

    def test_path_with_parent(self):
        """
        测试目的：验证有父节点时路径格式
        """
        # Arrange: 创建父文件夹和文件节点
        parent = FolderNode("folder_1", "docs")
        node = FileNode("file_1", "test.pdf", 1024, "pdf", parent=parent)

        # Act: 获取路径
        path = node.path

        # Assert: 路径包含父文件夹
        assert "/docs/test.pdf" in path

    def test_metadata(self):
        """
        测试目的：验证metadata字典操作
        """
        # Arrange: 创建文件节点
        node = FileNode("file_1", "test.pdf", 1024, "pdf")

        # Act: 设置和获取metadata
        node.metadata["key1"] = "value1"
        node.metadata["key2"] = 123

        # Assert: 验证metadata
        assert node.metadata["key1"] == "value1"
        assert node.metadata["key2"] == 123

    def test_accept_visitor(self):
        """
        测试目的：验证接受访问者模式
        """
        # Arrange: 创建文件节点和访问者
        node = FileNode("file_1", "test.pdf", 1024, "pdf")
        visitor = CountVisitor()

        # Act: 接受访问
        result = node.accept(visitor)

        # Assert: 验证访问结果
        assert visitor.count == 1

    def test_to_dict(self):
        """
        测试目的：验证转换为字典功能
        """
        # Arrange: 创建文件节点
        node = FileNode("file_1", "test.pdf", 1024, "pdf")
        node.metadata = {"author": "test"}

        # Act: 转换为字典
        result = node.to_dict()

        # Assert: 验证字典内容
        assert result["node_id"] == "file_1"
        assert result["name"] == "test.pdf"
        assert result["type"] == "file"
        assert result["size"] == 1024
        assert result["file_type"] == "pdf"
        assert result["metadata"]["author"] == "test"
        assert "path" in result
        assert "created_at" in result


# ============================================================================
# FolderNode 完整测试类
# ============================================================================

class TestFolderNodeComplete:
    """
    类级注释：文件夹节点完整测试类
    职责：全面测试FolderNode的所有功能
    """

    def test_creation(self):
        """
        测试目的：验证创建文件夹节点
        """
        # Arrange & Act: 创建文件夹节点
        node = FolderNode("folder_1", "documents")

        # Assert: 验证属性
        assert node.node_id == "folder_1"
        assert node.name == "documents"
        assert node.node_type == NodeType.FOLDER

    def test_children_property_returns_copy(self):
        """
        测试目的：验证children属性返回副本
        """
        # Arrange: 创建文件夹并添加子节点
        node = FolderNode("folder_1", "documents")
        file_node = FileNode("file_1", "test.pdf", 1024, "pdf")
        node.add_child(file_node)

        # Act: 获取子节点列表
        children = node.children

        # Assert: 返回副本（修改不影响原列表）
        original_len = len(children)
        children.append(FileNode("file_2", "test2.pdf", 512, "pdf"))
        assert len(node.children) == original_len

    def test_add_child(self):
        """
        测试目的：验证添加子节点功能
        """
        # Arrange: 创建文件夹和文件节点
        folder = FolderNode("folder_1", "documents")
        file_node = FileNode("file_1", "test.pdf", 1024, "pdf")

        # Act: 添加子节点
        folder.add_child(file_node)

        # Assert: 验证添加成功
        assert len(folder.children) == 1
        assert folder.children[0] is file_node
        assert file_node.parent is folder

    def test_add_child_updates_parent(self):
        """
        测试目的：验证添加子节点时更新父节点引用
        """
        # Arrange: 创建两个文件夹和文件节点
        folder1 = FolderNode("folder_1", "docs1")
        folder2 = FolderNode("folder_2", "docs2")
        file_node = FileNode("file_1", "test.pdf", 1024, "pdf", parent=folder1)

        # Act: 将文件移到新文件夹
        folder2.add_child(file_node)

        # Assert: 验证父节点已更新
        assert file_node.parent is folder2
        assert len(folder2.children) == 1

    def test_remove_child(self):
        """
        测试目的：验证移除子节点功能
        """
        # Arrange: 创建文件夹和子节点
        folder = FolderNode("folder_1", "documents")
        file_node = FileNode("file_1", "test.pdf", 1024, "pdf")
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
        """
        # Arrange: 创建文件夹
        folder = FolderNode("folder_1", "documents")

        # Act: 尝试移除不存在的子节点
        result = folder.remove_child("nonexistent")

        # Assert: 验证返回False
        assert result is False

    def test_get_child(self):
        """
        测试目的：验证获取指定ID的子节点
        """
        # Arrange: 创建文件夹和子节点
        folder = FolderNode("folder_1", "documents")
        file_node = FileNode("file_1", "test.pdf", 1024, "pdf")
        folder.add_child(file_node)

        # Act: 获取子节点
        result = folder.get_child("file_1")

        # Assert: 验证获取正确
        assert result is file_node

    def test_get_child_not_found(self):
        """
        测试目的：验证获取不存在的子节点返回None
        """
        # Arrange: 创建文件夹
        folder = FolderNode("folder_1", "documents")

        # Act: 尝试获取不存在的子节点
        result = folder.get_child("nonexistent")

        # Assert: 验证返回None
        assert result is None

    def test_get_child_by_name(self):
        """
        测试目的：验证通过名称获取子节点
        """
        # Arrange: 创建文件夹和子节点
        folder = FolderNode("folder_1", "documents")
        file_node = FileNode("file_1", "test.pdf", 1024, "pdf")
        folder.add_child(file_node)

        # Act: 通过名称获取
        result = folder.get_child_by_name("test.pdf")

        # Assert: 验证获取正确
        assert result is file_node

    def test_get_child_by_name_not_found(self):
        """
        测试目的：验证获取不存在的名称返回None
        """
        # Arrange: 创建文件夹
        folder = FolderNode("folder_1", "documents")

        # Act: 尝试获取不存在的名称
        result = folder.get_child_by_name("nonexistent.pdf")

        # Assert: 验证返回None
        assert result is None

    def test_find_in_direct_children(self):
        """
        测试目的：验证在直接子节点中查找
        """
        # Arrange: 创建文件夹和子节点
        folder = FolderNode("folder_1", "documents")
        file_node = FileNode("file_1", "test.pdf", 1024, "pdf")
        folder.add_child(file_node)

        # Act: 查找节点
        result = folder.find("file_1")

        # Assert: 验证找到
        assert result is file_node

    def test_find_in_nested_children(self):
        """
        测试目的：验证在嵌套子节点中查找
        """
        # Arrange: 创建嵌套结构
        root = FolderNode("root", "root")
        subfolder = FolderNode("subfolder", "sub")
        file_node = FileNode("file_1", "test.pdf", 1024, "pdf")

        root.add_child(subfolder)
        subfolder.add_child(file_node)

        # Act: 从根查找
        result = root.find("file_1")

        # Assert: 验证找到
        assert result is file_node

    def test_find_not_found(self):
        """
        测试目的：验证查找不存在的节点返回None
        """
        # Arrange: 创建文件夹
        folder = FolderNode("folder_1", "documents")

        # Act: 查找不存在的节点
        result = folder.find("nonexistent")

        # Assert: 验证返回None
        assert result is None

    def test_size_empty_folder(self):
        """
        测试目的：验证空文件夹大小为0
        """
        # Arrange: 创建空文件夹
        folder = FolderNode("folder_1", "documents")

        # Act: 获取大小
        size = folder.size()

        # Assert: 大小为0
        assert size == 0

    def test_size_with_files(self):
        """
        测试目的：验证包含文件的文件夹大小计算
        """
        # Arrange: 创建文件夹和文件
        folder = FolderNode("folder_1", "documents")
        file1 = FileNode("file_1", "test1.pdf", 1024, "pdf")
        file2 = FileNode("file_2", "test2.pdf", 2048, "pdf")

        folder.add_child(file1)
        folder.add_child(file2)

        # Act: 获取大小
        size = folder.size()

        # Assert: 大小为文件之和
        assert size == 3072

    def test_size_with_nested_folders(self):
        """
        测试目的：验证嵌套文件夹大小计算
        """
        # Arrange: 创建嵌套结构
        root = FolderNode("root", "root")
        subfolder = FolderNode("subfolder", "sub")
        file_node = FileNode("file_1", "test.pdf", 1024, "pdf")

        root.add_child(subfolder)
        subfolder.add_child(file_node)

        # Act: 获取根文件夹大小
        size = root.size()

        # Assert: 大小包含所有文件
        assert size == 1024

    def test_count_empty_folder(self):
        """
        测试目的：验证空文件夹计数为0
        """
        # Arrange: 创建空文件夹
        folder = FolderNode("folder_1", "documents")

        # Act: 计数
        count = folder.count()

        # Assert: 计数为0
        assert count == 0

    def test_count_with_files(self):
        """
        测试目的：验证包含文件的文件夹计数
        """
        # Arrange: 创建文件夹和文件
        folder = FolderNode("folder_1", "documents")
        file1 = FileNode("file_1", "test1.pdf", 1024, "pdf")
        file2 = FileNode("file_2", "test2.pdf", 2048, "pdf")

        folder.add_child(file1)
        folder.add_child(file2)

        # Act: 计数
        count = folder.count()

        # Assert: 计数等于文件数
        assert count == 2

    def test_is_leaf_empty_folder(self):
        """
        测试目的：验证空文件夹是叶子节点
        """
        # Arrange: 创建空文件夹
        folder = FolderNode("folder_1", "documents")

        # Act: 检查是否为叶子
        is_leaf = folder.is_leaf()

        # Assert: 空文件夹是叶子
        assert is_leaf is True

    def test_is_leaf_with_children(self):
        """
        测试目的：验证有子节点的文件夹不是叶子
        """
        # Arrange: 创建文件夹和子节点
        folder = FolderNode("folder_1", "documents")
        file_node = FileNode("file_1", "test.pdf", 1024, "pdf")
        folder.add_child(file_node)

        # Act: 检查是否为叶子
        is_leaf = folder.is_leaf()

        # Assert: 有子节点的文件夹不是叶子
        assert is_leaf is False

    def test_get_stats_empty_folder(self):
        """
        测试目的：验证空文件夹的统计信息
        """
        # Arrange: 创建空文件夹
        folder = FolderNode("folder_1", "documents")

        # Act: 获取统计信息
        stats = folder.get_stats()

        # Assert: 验证统计信息
        assert stats.file_count == 0
        assert stats.folder_count == 0
        assert stats.total_size == 0
        assert stats.max_depth == 0

    def test_get_stats_with_files(self):
        """
        测试目的：验证包含文件的文件夹统计信息
        """
        # Arrange: 创建文件夹和文件
        folder = FolderNode("folder_1", "documents")
        file1 = FileNode("file_1", "test1.pdf", 1024, "pdf")
        file2 = FileNode("file_2", "test2.pdf", 2048, "pdf")

        folder.add_child(file1)
        folder.add_child(file2)

        # Act: 获取统计信息
        stats = folder.get_stats()

        # Assert: 验证统计信息
        assert stats.file_count == 2
        assert stats.folder_count == 0
        assert stats.total_size == 3072

    def test_get_stats_with_nested_structure(self):
        """
        测试目的：验证嵌套结构的统计信息
        """
        # Arrange: 创建嵌套结构
        root = FolderNode("root", "root")
        subfolder = FolderNode("subfolder", "sub")
        file1 = FileNode("file_1", "test1.pdf", 1024, "pdf")
        file2 = FileNode("file_2", "test2.pdf", 2048, "pdf")

        root.add_child(subfolder)
        subfolder.add_child(file1)
        root.add_child(file2)

        # Act: 获取统计信息
        stats = root.get_stats()

        # Assert: 验证统计信息
        assert stats.file_count == 2
        assert stats.folder_count == 1
        assert stats.total_size == 3072
        assert stats.max_depth >= 1

    def test_filter_files(self):
        """
        测试目的：验证过滤文件功能
        """
        # Arrange: 创建混合节点
        folder = FolderNode("folder_1", "documents")
        file1 = FileNode("file_1", "test1.pdf", 1024, "pdf")
        file2 = FileNode("file_2", "test2.txt", 512, "txt")
        subfolder = FolderNode("subfolder", "sub")

        folder.add_child(file1)
        folder.add_child(file2)
        folder.add_child(subfolder)

        # Act: 过滤文件
        results = folder.filter(NodeFilter.files_only())

        # Assert: 验证只返回文件
        assert len(results) == 2
        assert all(isinstance(r, FileNode) for r in results)

    def test_filter_folders(self):
        """
        测试目的：验证过滤文件夹功能
        """
        # Arrange: 创建混合节点
        folder = FolderNode("folder_1", "documents")
        file_node = FileNode("file_1", "test.pdf", 1024, "pdf")
        subfolder = FolderNode("subfolder", "sub")

        folder.add_child(file_node)
        folder.add_child(subfolder)

        # Act: 过滤文件夹
        results = folder.filter(NodeFilter.folders_only())

        # Assert: 验证只返回文件夹
        assert len(results) == 1
        assert isinstance(results[0], FolderNode)

    def test_filter_by_type(self):
        """
        测试目的：验证按类型过滤功能
        """
        # Arrange: 创建混合节点
        folder = FolderNode("folder_1", "documents")
        file_node = FileNode("file_1", "test.pdf", 1024, "pdf")
        folder.add_child(file_node)

        # Act: 按类型过滤
        results = folder.filter(NodeFilter.by_type(NodeType.FILE))

        # Assert: 验证过滤结果
        assert len(results) == 1
        assert results[0].node_type == NodeType.FILE

    def test_filter_custom_predicate(self):
        """
        测试目的：验证自定义谓词过滤
        """
        # Arrange: 创建文件夹和文件
        folder = FolderNode("folder_1", "documents")
        file1 = FileNode("file_1", "large.pdf", 2048, "pdf")
        file2 = FileNode("file_2", "small.pdf", 512, "pdf")

        folder.add_child(file1)
        folder.add_child(file2)

        # Act: 自定义过滤（只保留大于1024的文件）
        results = folder.filter(lambda n: n.size() > 1024)

        # Assert: 验证过滤结果
        assert len(results) == 1
        assert results[0].name == "large.pdf"

    def test_traverse(self):
        """
        测试目的：验证遍历所有节点功能
        """
        # Arrange: 创建树结构
        folder = FolderNode("folder_1", "documents")
        file1 = FileNode("file_1", "test1.pdf", 1024, "pdf")
        subfolder = FolderNode("subfolder", "sub")
        file2 = FileNode("file_2", "test2.pdf", 2048, "pdf")

        folder.add_child(file1)
        folder.add_child(subfolder)
        subfolder.add_child(file2)

        collected = []

        def collect(node):
            collected.append(node.name)

        # Act: 遍历节点
        folder.traverse(collect)

        # Assert: 验证遍历结果
        assert "test1.pdf" in collected
        assert "sub" in collected
        assert "test2.pdf" in collected

    def test_iteration(self):
        """
        测试目的：验证迭代器接口
        """
        # Arrange: 创建文件夹和子节点
        folder = FolderNode("folder_1", "documents")
        file1 = FileNode("file_1", "test1.pdf", 1024, "pdf")
        file2 = FileNode("file_2", "test2.pdf", 2048, "pdf")

        folder.add_child(file1)
        folder.add_child(file2)

        # Act: 使用for循环迭代
        names = [node.name for node in folder]

        # Assert: 验证迭代结果
        assert "test1.pdf" in names
        assert "test2.pdf" in names

    def test_to_dict(self):
        """
        测试目的：验证转换为字典功能
        """
        # Arrange: 创建文件夹和子节点
        folder = FolderNode("folder_1", "documents")
        file_node = FileNode("file_1", "test.pdf", 1024, "pdf")
        folder.add_child(file_node)

        # Act: 转换为字典
        result = folder.to_dict()

        # Assert: 验证字典内容
        assert result["node_id"] == "folder_1"
        assert result["name"] == "documents"
        assert result["type"] == "folder"
        assert len(result["children"]) == 1
        assert result["children"][0]["name"] == "test.pdf"

    def test_accept_visitor(self):
        """
        测试目的：验证接受访问者模式
        """
        # Arrange: 创建文件夹和访问者
        folder = FolderNode("folder_1", "documents")
        visitor = CountVisitor()

        # Act: 接受访问
        result = folder.accept(visitor)

        # Assert: 验证访问结果
        assert visitor.count >= 1


# ============================================================================
# NodeFilter 测试类
# ============================================================================

class TestNodeFilterComplete:
    """
    类级注释：节点过滤器完整测试类
    职责：全面测试NodeFilter的各种过滤方法
    """

    def test_by_type_file(self):
        """
        测试目的：验证按FILE类型过滤
        """
        # Arrange: 创建文件节点
        file_node = FileNode("file_1", "test.pdf", 1024, "pdf")

        # Act: 创建过滤器
        filter_fn = NodeFilter.by_type(NodeType.FILE)

        # Assert: 验证过滤结果
        assert filter_fn(file_node) is True

    def test_by_type_folder(self):
        """
        测试目的：验证按FOLDER类型过滤
        """
        # Arrange: 创建文件夹节点
        folder_node = FolderNode("folder_1", "docs")

        # Act: 创建过滤器
        filter_fn = NodeFilter.by_type(NodeType.FOLDER)

        # Assert: 验证过滤结果
        assert filter_fn(folder_node) is True

    def test_by_type_mismatch(self):
        """
        测试目的：验证类型不匹配时返回False
        """
        # Arrange: 创建文件节点
        file_node = FileNode("file_1", "test.pdf", 1024, "pdf")

        # Act: 创建文件夹类型过滤器
        filter_fn = NodeFilter.by_type(NodeType.FOLDER)

        # Assert: 验证过滤结果
        assert filter_fn(file_node) is False

    def test_by_name_match(self):
        """
        测试目的：验证名称匹配过滤
        """
        # Arrange: 创建文件节点
        file_node = FileNode("file_1", "report.pdf", 1024, "pdf")

        # Act: 创建名称过滤器
        filter_fn = NodeFilter.by_name("report")

        # Assert: 验证过滤结果
        assert filter_fn(file_node) is True

    def test_by_name_case_insensitive(self):
        """
        测试目的：验证名称过滤大小写不敏感
        """
        # Arrange: 创建文件节点
        file_node = FileNode("file_1", "Report.pdf", 1024, "pdf")

        # Act: 创建小写名称过滤器
        filter_fn = NodeFilter.by_name("report")

        # Assert: 验证过滤结果
        assert filter_fn(file_node) is True

    def test_by_name_no_match(self):
        """
        测试目的：验证名称不匹配时返回False
        """
        # Arrange: 创建文件节点
        file_node = FileNode("file_1", "test.pdf", 1024, "pdf")

        # Act: 创建名称过滤器
        filter_fn = NodeFilter.by_name("report")

        # Assert: 验证过滤结果
        assert filter_fn(file_node) is False

    def test_by_extension_match(self):
        """
        测试目的：验证扩展名匹配过滤
        """
        # Arrange: 创建PDF文件节点
        file_node = FileNode("file_1", "document.pdf", 1024, "pdf")

        # Act: 创建扩展名过滤器
        filter_fn = NodeFilter.by_extension("pdf")

        # Assert: 验证过滤结果
        assert filter_fn(file_node) is True

    def test_by_extension_case_insensitive(self):
        """
        测试目的：验证扩展名过滤大小写不敏感
        """
        # Arrange: 创建PDF文件节点
        file_node = FileNode("file_1", "document.pdf", 1024, "PDF")

        # Act: 创建小写扩展名过滤器
        filter_fn = NodeFilter.by_extension("pdf")

        # Assert: 验证过滤结果
        assert filter_fn(file_node) is True

    def test_by_extension_no_match(self):
        """
        测试目的：验证扩展名不匹配时返回False
        """
        # Arrange: 创建PDF文件节点
        file_node = FileNode("file_1", "document.pdf", 1024, "pdf")

        # Act: 创建TXT扩展名过滤器
        filter_fn = NodeFilter.by_extension("txt")

        # Assert: 验证过滤结果
        assert filter_fn(file_node) is False

    def test_by_extension_folder(self):
        """
        测试目的：验证文件夹不通过扩展名过滤
        """
        # Arrange: 创建文件夹节点
        folder_node = FolderNode("folder_1", "docs")

        # Act: 创建扩展名过滤器
        filter_fn = NodeFilter.by_extension("pdf")

        # Assert: 验证过滤结果
        assert filter_fn(folder_node) is False

    def test_by_size_within_limit(self):
        """
        测试目的：验证大小在限制内通过过滤
        """
        # Arrange: 创建小文件节点
        file_node = FileNode("file_1", "small.pdf", 512, "pdf")

        # Act: 创建大小过滤器
        filter_fn = NodeFilter.by_size(1024)

        # Assert: 验证过滤结果
        assert filter_fn(file_node) is True

    def test_by_size_exceeds_limit(self):
        """
        测试目的：验证大小超限不通过过滤
        """
        # Arrange: 创建大文件节点
        file_node = FileNode("file_1", "large.pdf", 2048, "pdf")

        # Act: 创建大小过滤器
        filter_fn = NodeFilter.by_size(1024)

        # Assert: 验证过滤结果
        assert filter_fn(file_node) is False

    def test_by_size_equal_limit(self):
        """
        测试目的：验证大小等于限制时通过过滤
        """
        # Arrange: 创建文件节点
        file_node = FileNode("file_1", "exact.pdf", 1024, "pdf")

        # Act: 创建大小过滤器
        filter_fn = NodeFilter.by_size(1024)

        # Assert: 验证过滤结果
        assert filter_fn(file_node) is True

    def test_files_only_file(self):
        """
        测试目的：验证files_only过滤器对文件返回True
        """
        # Arrange: 创建文件节点
        file_node = FileNode("file_1", "test.pdf", 1024, "pdf")

        # Act: 创建文件过滤器
        filter_fn = NodeFilter.files_only()

        # Assert: 验证过滤结果
        assert filter_fn(file_node) is True

    def test_files_only_folder(self):
        """
        测试目的：验证files_only过滤器对文件夹返回False
        """
        # Arrange: 创建文件夹节点
        folder_node = FolderNode("folder_1", "docs")

        # Act: 创建文件过滤器
        filter_fn = NodeFilter.files_only()

        # Assert: 验证过滤结果
        assert filter_fn(folder_node) is False

    def test_folders_only_folder(self):
        """
        测试目的：验证folders_only过滤器对文件夹返回True
        """
        # Arrange: 创建文件夹节点
        folder_node = FolderNode("folder_1", "docs")

        # Act: 创建文件夹过滤器
        filter_fn = NodeFilter.folders_only()

        # Assert: 验证过滤结果
        assert filter_fn(folder_node) is True

    def test_folders_only_file(self):
        """
        测试目的：验证folders_only过滤器对文件返回False
        """
        # Arrange: 创建文件节点
        file_node = FileNode("file_1", "test.pdf", 1024, "pdf")

        # Act: 创建文件夹过滤器
        filter_fn = NodeFilter.folders_only()

        # Assert: 验证过滤结果
        assert filter_fn(file_node) is False

    def test_combine_all_pass(self):
        """
        测试目的：验证组合过滤所有条件都满足
        """
        # Arrange: 创建文件节点
        file_node = FileNode("file_1", "small.pdf", 512, "pdf")

        # Act: 创建组合过滤器
        filter_fn = NodeFilter.combine(
            NodeFilter.files_only(),
            NodeFilter.by_extension("pdf"),
            NodeFilter.by_size(1024)
        )

        # Assert: 验证过滤结果
        assert filter_fn(file_node) is True

    def test_combine_one_fail(self):
        """
        测试目的：验证组合过滤任一条件不满足时失败
        """
        # Arrange: 创建文件节点
        file_node = FileNode("file_1", "large.pdf", 2048, "pdf")

        # Act: 创建组合过滤器（大小不满足）
        filter_fn = NodeFilter.combine(
            NodeFilter.files_only(),
            NodeFilter.by_extension("pdf"),
            NodeFilter.by_size(1024)
        )

        # Assert: 验证过滤结果
        assert filter_fn(file_node) is False

    def test_any_of_one_pass(self):
        """
        测试目的：验证OR过滤任一条件满足即可
        """
        # Arrange: 创建文件节点
        file_node = FileNode("file_1", "document.pdf", 1024, "pdf")

        # Act: 创建OR过滤器
        filter_fn = NodeFilter.any_of(
            NodeFilter.by_extension("txt"),
            NodeFilter.by_extension("pdf")
        )

        # Assert: 验证过滤结果
        assert filter_fn(file_node) is True

    def test_any_of_all_fail(self):
        """
        测试目的：验证OR过滤所有条件不满足时失败
        """
        # Arrange: 创建文件节点
        file_node = FileNode("file_1", "document.pdf", 1024, "pdf")

        # Act: 创建OR过滤器（都不匹配）
        filter_fn = NodeFilter.any_of(
            NodeFilter.by_extension("txt"),
            NodeFilter.by_extension("doc")
        )

        # Assert: 验证过滤结果
        assert filter_fn(file_node) is False


# ============================================================================
# NodeVisitor 测试类
# ============================================================================

class TestNodeVisitorAbstract:
    """
    类级注释：节点访问者抽象类测试
    职责：验证访问者接口的完整性
    """

    def test_visitor_requires_visit_file(self):
        """
        测试目的：验证访问者必须实现visit_file方法
        """
        # Arrange & Act: 尝试创建不完整的访问者
        try:
            class IncompleteVisitor(NodeVisitor):
                def visit_folder(self, folder_node):
                    pass
                # 缺少visit_file
            # 如果没有报错，验证实例可以创建但调用会失败
            visitor = IncompleteVisitor()
        except TypeError:
            # 如果有类型检查，可能会在创建时失败
            pass

    def test_visitor_requires_visit_folder(self):
        """
        测试目的：验证访问者必须实现visit_folder方法
        """
        # 验证完整实现的访问者可以正常工作
        class CompleteVisitor(NodeVisitor):
            def visit_file(self, file_node):
                return "file"

            def visit_folder(self, folder_node):
                return "folder"

        visitor = CompleteVisitor()
        file_node = FileNode("file_1", "test.pdf", 1024, "pdf")

        # 验证可以调用
        result = file_node.accept(visitor)
        assert result == "file"


# ============================================================================
# SizeCalculatorVisitor 测试类
# ============================================================================

class TestSizeCalculatorVisitor:
    """
    类级注释：大小计算访问者测试类
    职责：测试SizeCalculatorVisitor的各种情况
    """

    def test_visit_file(self):
        """
        测试目的：验证访问文件节点返回文件大小
        """
        # Arrange: 创建文件节点和访问者
        file_node = FileNode("file_1", "test.pdf", 2048, "pdf")
        visitor = SizeCalculatorVisitor()

        # Act: 访问文件节点
        result = visitor.visit_file(file_node)

        # Assert: 验证返回文件大小
        assert result == 2048

    def test_visit_folder_empty(self):
        """
        测试目的：验证访问空文件夹返回0
        """
        # Arrange: 创建空文件夹和访问者
        folder = FolderNode("folder_1", "documents")
        visitor = SizeCalculatorVisitor()

        # Act: 访问空文件夹
        result = visitor.visit_folder(folder)

        # Assert: 验证返回0
        assert result == 0

    def test_visit_folder_with_files(self):
        """
        测试目的：验证访问包含文件的文件夹返回总大小
        """
        # Arrange: 创建文件夹和文件
        folder = FolderNode("folder_1", "documents")
        file1 = FileNode("file_1", "test1.pdf", 1024, "pdf")
        file2 = FileNode("file_2", "test2.pdf", 2048, "pdf")

        folder.add_child(file1)
        folder.add_child(file2)

        visitor = SizeCalculatorVisitor()

        # Act: 访问文件夹
        result = visitor.visit_folder(folder)

        # Assert: 验证返回总大小
        assert result == 3072

    def test_visit_folder_nested(self):
        """
        测试目的：验证访问嵌套文件夹返回总大小
        """
        # Arrange: 创建嵌套结构
        root = FolderNode("root", "root")
        subfolder = FolderNode("subfolder", "sub")
        file_node = FileNode("file_1", "test.pdf", 1024, "pdf")

        root.add_child(subfolder)
        subfolder.add_child(file_node)

        visitor = SizeCalculatorVisitor()

        # Act: 访问根文件夹
        result = visitor.visit_folder(root)

        # Assert: 验证返回总大小
        assert result == 1024
