"""
上海宇羲伏天智能科技有限公司出品

文件级注释：对话服务模块
内部逻辑：组织对话相关的服务组件，提供统一的对外接口
设计模式：外观模式 - 隐藏内部复杂性，提供简单接口
"""

# 内部逻辑：从各个子模块导出主要类和函数
from .orchestrator import ChatOrchestrator
from .strategies import ChatStrategy, RAGStrategy, AgentStrategy, ChatStrategyFactory
from .sources_processor import SourcesProcessor
from .document_formatter import DocumentFormatter

# 内部变量：定义模块公开接口
__all__ = [
    'ChatOrchestrator',
    'ChatStrategy',
    'RAGStrategy',
    'AgentStrategy',
    'ChatStrategyFactory',
    'SourcesProcessor',
    'DocumentFormatter',
]
