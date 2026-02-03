# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：Agent工具注册表模块
内部逻辑：统一管理Agent工具，支持动态注册和获取
设计模式：注册表模式（Registry Pattern）+ 单例模式（Singleton Pattern）
设计原则：开闭原则、依赖倒置原则

实现说明：
    - 支持工具实例的注册和获取
    - 支持延迟初始化（通过构建器函数）
    - 提供单例访问
"""

from typing import Dict, List, Callable, Any, Optional
from langchain_core.tools import BaseTool
from loguru import logger


class ToolRegistry:
    """
    类级注释：工具注册表
    设计模式：注册表模式 + 单例模式
    职责：
        1. 管理工具注册
        2. 提供工具查找
        3. 支持动态扩展
    """

    # 内部变量：单例实例
    _instance: Optional['ToolRegistry'] = None

    # 内部变量：工具实例注册表
    _tools: Dict[str, BaseTool] = {}

    # 内部变量：工具构建器注册表（延迟初始化）
    _tool_builders: Dict[str, Callable[[], BaseTool]] = {}

    # 内部变量：工具依赖
    _dependencies: Dict[str, Any] = {}

    def __new__(cls):
        """
        函数级注释：实现单例模式
        返回值：唯一实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        函数级注释：初始化注册表（单例模式下只执行一次）
        """
        pass

    @classmethod
    def set_dependencies(cls, **kwargs) -> None:
        """
        函数级注释：设置依赖项
        内部逻辑：注入工具需要的依赖（如 vector_db）
        参数：
            **kwargs - 依赖项字典
        """
        cls._dependencies = kwargs
        logger.debug(f"设置工具依赖: {list(kwargs.keys())}")

    @classmethod
    def register(cls, name: str, tool: BaseTool) -> None:
        """
        函数级注释：注册工具实例
        内部逻辑：将工具实例注册到注册表
        参数：
            name - 工具名称
            tool - 工具实例
        """
        cls._tools[name] = tool
        logger.info(f"注册工具实例: {name}")

    @classmethod
    def register_builder(cls, name: str, builder: Callable[[], BaseTool]) -> None:
        """
        函数级注释：注册工具构建器（延迟初始化）
        内部逻辑：注册构建函数，首次获取时才创建实例
        参数：
            name - 工具名称
            builder - 工具构建函数
        """
        cls._tool_builders[name] = builder
        logger.info(f"注册工具构建器: {name}")

    @classmethod
    def get(cls, name: str) -> BaseTool:
        """
        函数级注释：获取工具
        内部逻辑：先查找已注册的工具，再尝试通过构建器创建
        参数：
            name - 工具名称
        返回值：工具实例
        异常：ValueError - 工具未注册时抛出
        """
        # 内部逻辑：先查找已注册的工具
        if name in cls._tools:
            return cls._tools[name]

        # 内部逻辑：尝试通过构建器创建
        if name in cls._tool_builders:
            tool = cls._tool_builders[name]()
            cls._tools[name] = tool
            return tool

        raise ValueError(f"工具未注册: {name}")

    @classmethod
    def get_all(cls) -> List[BaseTool]:
        """
        函数级注释：获取所有工具
        内部逻辑：初始化所有延迟工具，返回完整列表
        返回值：工具列表
        """
        # 内部逻辑：初始化所有延迟工具
        for name, builder in cls._tool_builders.items():
            if name not in cls._tools:
                cls._tools[name] = builder()

        return list(cls._tools.values())

    @classmethod
    def get_tools_map(cls) -> Dict[str, BaseTool]:
        """
        函数级注释：获取工具名称到工具的映射字典
        内部逻辑：返回 {tool.name: tool} 格式的字典
        返回值：工具映射字典
        """
        tools = cls.get_all()
        return {tool.name: tool for tool in tools}

    @classmethod
    def clear(cls) -> None:
        """
        函数级注释：清空注册表
        内部逻辑：主要用于测试场景
        """
        cls._tools.clear()
        cls._tool_builders.clear()
        cls._dependencies.clear()
        logger.info("清空工具注册表")

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """
        函数级注释：检查工具是否已注册
        参数：
            name - 工具名称
        返回值：是否已注册
        """
        return name in cls._tools or name in cls._tool_builders


# 内部变量：全局注册表实例
tool_registry = ToolRegistry()


# 内部逻辑：定义默认工具创建函数
def _create_retrieve_knowledge_tool() -> BaseTool:
    """
    函数级注释：创建知识检索工具
    返回值：检索工具实例
    """
    from langchain_core.tools import tool

    @tool
    def retrieve_knowledge(query: str) -> str:
        """
        函数级注释：从本地知识库中检索相关信息
        参数：query - 检索关键词
        返回值：检索到的文本片段拼接字符串
        """
        vector_db = tool_registry._dependencies.get('vector_db')
        if not vector_db:
            return "向量数据库未初始化"

        docs = vector_db.similarity_search(query, k=3)
        from app.services.agent_service import AgentService
        AgentService._last_retrieved_ids = [doc.metadata.get("doc_id", 0) for doc in docs]
        return "\n\n".join([doc.page_content for doc in docs])

    return retrieve_knowledge


def _create_search_files_tool() -> BaseTool:
    """
    函数级注释：创建文件搜索工具
    返回值：搜索工具实例
    """
    from langchain_core.tools import tool

    @tool
    def search_local_files(directory: str, pattern: str = "*") -> str:
        """
        函数级注释：在本地目录中搜索文件
        参数：
            directory: 要搜索的目录路径
            pattern: 文件名匹配模式 (如 *.pdf)
        返回值：找到的文件列表
        """
        import glob
        import os
        try:
            files = glob.glob(os.path.join(directory, pattern))
            if not files:
                return f"在目录 {directory} 中未找到匹配 {pattern} 的文件。"
            return "找到以下文件：\n" + "\n".join(files)
        except Exception as e:
            return f"搜索文件时出错: {str(e)}"

    return search_local_files


def _create_calculate_tool() -> BaseTool:
    """
    函数级注释：创建计算工具
    返回值：计算工具实例
    """
    from langchain_core.tools import tool

    @tool
    def calculate(expression: str) -> str:
        """
        函数级注释：执行简单的 Python 数学计算
        参数：expression - 数学表达式 (如 "123 * 456")
        返回值：计算结果或错误信息
        """
        try:
            allowed_names = {"__builtins__": None}
            result = eval(expression, allowed_names, {})
            return f"计算结果: {result}"
        except Exception as e:
            return f"计算出错: {str(e)}"

    return calculate


def _create_query_db_tool() -> BaseTool:
    """
    函数级注释：创建数据库查询工具
    返回值：查询工具实例
    """
    from langchain_core.tools import tool

    @tool
    def query_metadata_db(sql_query: str) -> str:
        """
        函数级注释：查询本地 SQLite 元数据数据库
        参数：sql_query - 标准 SQL 查询语句
        返回值：查询结果的字符串表示
        """
        import sqlite3
        from app.core.config import settings

        try:
            conn = sqlite3.connect(settings.SQLITE_DB_PATH)
            cursor = conn.cursor()
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            conn.close()
            if not rows:
                return "未查询到相关数据。"
            return f"查询结果：\n{str(rows)}"
        except Exception as e:
            return f"数据库查询失败: {str(e)}"

    return query_metadata_db


# 内部逻辑：注册默认工具
def _register_default_tools():
    """
    函数级注释：注册默认工具集
    内部逻辑：延迟加载工具，避免循环导入
    """
    ToolRegistry.register_builder("retrieve_knowledge", _create_retrieve_knowledge_tool)
    ToolRegistry.register_builder("search_local_files", _create_search_files_tool)
    ToolRegistry.register_builder("calculate", _create_calculate_tool)
    ToolRegistry.register_builder("query_metadata_db", _create_query_db_tool)


# 内部逻辑：模块加载时注册默认工具
_register_default_tools()


# 内部变量：导出所有公共接口
__all__ = [
    'ToolRegistry',
    'tool_registry',
]
