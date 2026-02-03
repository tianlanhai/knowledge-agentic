# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：AI提供商工厂实现模块
内部逻辑：各个AI提供商的具体工厂实现
设计模式：抽象工厂模式 - 具体工厂
"""

# 内部逻辑：导入所有提供商工厂
from app.core.ai_provider.providers.ollama import OllamaProviderFactory
from app.core.ai_provider.providers.zhipuai import ZhipuAIProviderFactory
from app.core.ai_provider.providers.openai import OpenAIProviderFactory
from app.core.ai_provider.providers.deepseek import DeepSeekProviderFactory
from app.core.ai_provider.providers.minimax import MiniMaxProviderFactory
from app.core.ai_provider.providers.moonshot import MoonshotProviderFactory

# 内部逻辑：导出所有提供商工厂
__all__ = [
    'OllamaProviderFactory',
    'ZhipuAIProviderFactory',
    'OpenAIProviderFactory',
    'DeepSeekProviderFactory',
    'MiniMaxProviderFactory',
    'MoonshotProviderFactory',
]
