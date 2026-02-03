# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：AI 提供商抽象工厂模块（向后兼容入口）
内部逻辑：从新模块导入所有内容，提供统一的接口
设计模式：抽象工厂模式（Abstract Factory Pattern）+ 工厂模式
设计原则：开闭原则、依赖倒置原则

注意：此文件保留用于向后兼容，实际实现已迁移到 ai_provider/ 目录
"""

# ============================================================================
# 内部逻辑：从新模块导入所有内容，提供统一的接口
# ============================================================================
from app.core.ai_provider import (
    # 基础类型
    AIProviderType,
    AIComponentType,
    # 配置
    AIProviderConfig,
    # 抽象工厂
    AIProviderFactory,
    # 注册表
    AIProviderFactoryRegistry,
    # 统一工厂
    UnifiedAIFactory,
    unified_ai_factory,
    create_ai_provider,
    # 提供商工厂
    OllamaProviderFactory,
    ZhipuAIProviderFactory,
    OpenAIProviderFactory,
    DeepSeekProviderFactory,
    MiniMaxProviderFactory,
    MoonshotProviderFactory,
)

# ============================================================================
# 内部逻辑：自动注册所有提供商工厂到注册表
# ============================================================================
# 内部逻辑：确保所有工厂已注册
for provider_type, factory_class in [
    (AIProviderType.OLLAMA, OllamaProviderFactory),
    (AIProviderType.ZHIPUAI, ZhipuAIProviderFactory),
    (AIProviderType.OPENAI, OpenAIProviderFactory),
    (AIProviderType.DEEPSEEK, DeepSeekProviderFactory),
    (AIProviderType.MINIMAX, MiniMaxProviderFactory),
    (AIProviderType.MOONSHOT, MoonshotProviderFactory),
]:
    AIProviderFactoryRegistry.register(provider_type, factory_class)

# ============================================================================
# 内部变量：导出所有公共接口（保持向后兼容）
# ============================================================================
__all__ = [
    'AIProviderType',
    'AIComponentType',
    'AIProviderConfig',
    'AIProviderFactory',
    'UnifiedAIFactory',
    'AIProviderFactoryRegistry',
    'unified_ai_factory',
    'create_ai_provider',
    'OllamaProviderFactory',
    'ZhipuAIProviderFactory',
    'OpenAIProviderFactory',
    'DeepSeekProviderFactory',
    'MiniMaxProviderFactory',
    'MoonshotProviderFactory',
]
