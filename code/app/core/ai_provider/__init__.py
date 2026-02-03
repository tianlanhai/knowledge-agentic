# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：AI提供商模块
内部逻辑：统一 LLM 和 Embedding 的创建接口
设计模式：抽象工厂模式（Abstract Factory Pattern）
设计原则：开闭原则、依赖倒置原则

模块结构：
    base.py - 抽象工厂基类和枚举类型
    config.py - 配置类
    registry.py - 工厂注册表
    unified.py - 统一工厂
    providers/ - 各个提供商的具体工厂实现
"""

# 内部逻辑：从各子模块导入，保持向后兼容
from app.core.ai_provider.base import (
    AIProviderType,
    AIComponentType,
    AIProviderFactory,
)
from app.core.ai_provider.config import AIProviderConfig
from app.core.ai_provider.registry import AIProviderFactoryRegistry
from app.core.ai_provider.unified import (
    UnifiedAIFactory,
    unified_ai_factory,
    create_ai_provider,
)

# 内部逻辑：导入所有提供商工厂
from app.core.ai_provider.providers.ollama import OllamaProviderFactory
from app.core.ai_provider.providers.zhipuai import ZhipuAIProviderFactory
from app.core.ai_provider.providers.openai import OpenAIProviderFactory
from app.core.ai_provider.providers.deepseek import DeepSeekProviderFactory
from app.core.ai_provider.providers.minimax import MiniMaxProviderFactory
from app.core.ai_provider.providers.moonshot import MoonshotProviderFactory

# ============================================================================
# 内部逻辑：自动注册所有提供商工厂到注册表
# 设计说明：在模块级别执行注册，确保首次导入时所有提供商已注册
# 设计模式：注册表模式 + 懒加载初始化
# ============================================================================

def _register_providers():
    """
    函数级注释：注册所有提供商工厂
    内部逻辑：遍历所有工厂类并注册到 AIProviderFactoryRegistry
    设计模式：注册表模式 + 懒加载初始化
    返回值：无
    """
    from app.core.ai_provider.registry import AIProviderFactoryRegistry

    # 内部逻辑：检查是否已注册（避免重复注册）
    already_registered = AIProviderFactoryRegistry.supported_providers()
    if already_registered:
        return

    # 内部逻辑：注册所有提供商工厂
    for provider_type, factory_class in [
        (AIProviderType.OLLAMA, OllamaProviderFactory),
        (AIProviderType.ZHIPUAI, ZhipuAIProviderFactory),
        (AIProviderType.OPENAI, OpenAIProviderFactory),
        (AIProviderType.DEEPSEEK, DeepSeekProviderFactory),
        (AIProviderType.MINIMAX, MiniMaxProviderFactory),
        (AIProviderType.MOONSHOT, MoonshotProviderFactory),
    ]:
        AIProviderFactoryRegistry.register(provider_type, factory_class)


# 内部逻辑：模块导入时立即执行注册
_register_providers()

# 内部变量：导出所有公共接口（保持向后兼容）
__all__ = [
    # 基础类型
    'AIProviderType',
    'AIComponentType',
    # 配置
    'AIProviderConfig',
    # 抽象工厂
    'AIProviderFactory',
    # 注册表
    'AIProviderFactoryRegistry',
    # 统一工厂
    'UnifiedAIFactory',
    'unified_ai_factory',
    'create_ai_provider',
    # 提供商工厂
    'OllamaProviderFactory',
    'ZhipuAIProviderFactory',
    'OpenAIProviderFactory',
    'DeepSeekProviderFactory',
    'MiniMaxProviderFactory',
    'MoonshotProviderFactory',
]
