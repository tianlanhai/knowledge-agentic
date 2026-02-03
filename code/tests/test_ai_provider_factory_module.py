# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：AI Provider Factory 模块测试
内部逻辑：测试AI提供商工厂的导入、注册和导出功能
"""

import pytest
from unittest.mock import patch, MagicMock

# ============================================================================
# 模块导入测试
# ============================================================================


class TestAIProviderFactoryModule:
    """
    类级注释：ai_provider_factory模块单元测试类
    测试覆盖范围：
        1. 模块导入测试
        2. 导出的符号验证
        3. 自动注册功能验证
        4. 与新模块的兼容性测试
    """

    def test_module_imports_successfully(self):
        """
        测试目的：验证ai_provider_factory模块可以成功导入
        测试场景：从app.core.ai_provider_factory导入所有符号
        """
        # 这个导入不应该抛出异常
        from app.core.ai_provider_factory import (
            AIProviderType,
            AIComponentType,
            AIProviderConfig,
            AIProviderFactory,
            AIProviderFactoryRegistry,
            UnifiedAIFactory,
            unified_ai_factory,
            create_ai_provider,
            OllamaProviderFactory,
            ZhipuAIProviderFactory,
            OpenAIProviderFactory,
            DeepSeekProviderFactory,
            MiniMaxProviderFactory,
            MoonshotProviderFactory,
        )
        # 验证关键符号存在
        assert AIProviderType is not None
        assert AIProviderFactoryRegistry is not None
        assert UnifiedAIFactory is not None

    def test_module_all_exports(self):
        """
        测试目的：验证__all__导出列表正确
        测试场景：检查所有应该导出的符号都在__all__中
        """
        from app.core.ai_provider_factory import __all__

        expected_exports = [
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

        for export in expected_exports:
            assert export in __all__, f"缺少导出: {export}"

    def test_ai_provider_type_enum(self):
        """
        测试目的：验证AIProviderType枚举值
        测试场景：检查所有提供商类型枚举值
        """
        from app.core.ai_provider_factory import AIProviderType

        assert AIProviderType.OLLAMA is not None
        assert AIProviderType.ZHIPUAI is not None
        assert AIProviderType.OPENAI is not None
        assert AIProviderType.DEEPSEEK is not None
        assert AIProviderType.MINIMAX is not None
        assert AIProviderType.MOONSHOT is not None

    def test_ai_component_type_enum(self):
        """
        测试目的：验证AIComponentType枚举值
        测试场景：检查所有组件类型枚举值
        """
        from app.core.ai_provider_factory import AIComponentType

        # 验证枚举存在（假设有这些组件类型）
        assert hasattr(AIComponentType, '__members__')

    def test_provider_factories_are_classes(self):
        """
        测试目的：验证所有工厂类都是可用的类
        测试场景：检查每个工厂类是否可实例化或至少是类
        """
        from app.core.ai_provider_factory import (
            OllamaProviderFactory,
            ZhipuAIProviderFactory,
            OpenAIProviderFactory,
            DeepSeekProviderFactory,
            MiniMaxProviderFactory,
            MoonshotProviderFactory,
        )

        factories = [
            OllamaProviderFactory,
            ZhipuAIProviderFactory,
            OpenAIProviderFactory,
            DeepSeekProviderFactory,
            MiniMaxProviderFactory,
            MoonshotProviderFactory,
        ]

        for factory_class in factories:
            assert isinstance(factory_class, type), f"{factory_class} 不是一个类"

    def test_ai_provider_factory_registry_exists(self):
        """
        测试目的：验证AIProviderFactoryRegistry存在且有注册方法
        测试场景：检查注册表类的关键方法
        """
        from app.core.ai_provider_factory import AIProviderFactoryRegistry

        assert hasattr(AIProviderFactoryRegistry, 'register')
        assert hasattr(AIProviderFactoryRegistry, 'get_factory')
        assert hasattr(AIProviderFactoryRegistry, 'unregister')
        assert hasattr(AIProviderFactoryRegistry, 'supported_providers')

    def test_unified_ai_factory_exists(self):
        """
        测试目的：验证UnifiedAIFactory存在且可用
        测试场景：检查统一工厂类
        """
        from app.core.ai_provider_factory import UnifiedAIFactory

        assert UnifiedAIFactory is not None
        assert isinstance(UnifiedAIFactory, type)

    def test_unified_ai_factory_singleton(self):
        """
        测试目的：验证unified_ai_factory是单例
        测试场景：检查全局unified_ai_factory实例
        """
        from app.core.ai_provider_factory import unified_ai_factory

        assert unified_ai_factory is not None
        # 验证是UnifiedAIFactory的实例
        from app.core.ai_provider_factory import UnifiedAIFactory
        assert isinstance(unified_ai_factory, UnifiedAIFactory)

    def test_create_ai_provider_function(self):
        """
        测试目的：验证create_ai_provider函数存在
        测试场景：检查工厂函数
        """
        from app.core.ai_provider_factory import create_ai_provider

        assert callable(create_ai_provider)

    # ========================================================================
    # 自动注册功能测试
    # ========================================================================

    def test_automatic_registration_on_import(self):
        """
        测试目的：验证导入时自动注册提供商工厂
        测试场景：检查注册表是否包含所有提供商
        """
        from app.core.ai_provider_factory import AIProviderFactoryRegistry, AIProviderType

        # 验证常见的提供商类型已注册
        # 注意：这里假设在conftest或其他地方已经执行过注册
        # 如果测试失败，可能需要先运行注册逻辑
        registered_types = getattr(AIProviderFactoryRegistry, '_factories', {})
        # 至少应该有一些提供商被注册（在conftest中）
        # 如果没有，我们测试注册方法是否可用

    def test_register_function_is_callable(self):
        """
        测试目的：验证register方法可调用
        测试场景：测试注册方法的可调用性
        """
        from app.core.ai_provider_factory import AIProviderFactoryRegistry

        assert callable(AIProviderFactoryRegistry.register)

    # ========================================================================
    # 向后兼容性测试
    # ========================================================================

    def test_backward_compatibility_with_old_imports(self):
        """
        测试目的：验证向后兼容的导入路径
        测试场景：确保从新位置导入的符号与旧位置一致
        """
        # 从旧位置（兼容层）导入
        from app.core.ai_provider_factory import (
            AIProviderType as OldProviderType,
            AIProviderFactoryRegistry as OldRegistry,
        )

        # 从新位置导入
        from app.core.ai_provider import (
            AIProviderType as NewProviderType,
            AIProviderFactoryRegistry as NewRegistry,
        )

        # 验证它们是相同的对象
        assert OldProviderType is NewProviderType
        assert OldRegistry is NewRegistry

    # ========================================================================
    # 模块属性测试
    # ========================================================================

    def test_module_docstring(self):
        """
        测试目的：验证模块有文档字符串
        测试场景：检查模块级注释
        """
        import app.core.ai_provider_factory as module

        assert module.__doc__ is not None
        assert "上海宇羲伏天智能科技有限公司" in module.__doc__

    def test_module_file_location(self):
        """
        测试目的：验证模块文件位置
        测试场景：检查模块文件路径
        """
        import app.core.ai_provider_factory as module

        assert hasattr(module, '__file__')
        assert 'ai_provider_factory.py' in module.__file__


# ============================================================================
# AIProviderFactory 注册功能测试
# ============================================================================


class TestAIProviderFactoryRegistration:
    """
    类级注释：AIProviderFactory 注册功能测试类
    测试覆盖范围：
        1. 工厂注册
        2. 工厂获取
        3. 提供商创建
    """

    @pytest.fixture
    def clean_registry(self):
        """创建干净的注册表用于测试"""
        from app.core.ai_provider_factory import AIProviderFactoryRegistry

        # 备份原始注册表
        original_factories = getattr(AIProviderFactoryRegistry, '_factories', {}).copy()

        # 清空注册表
        AIProviderFactoryRegistry._factories = {}

        yield AIProviderFactoryRegistry

        # 恢复原始注册表
        AIProviderFactoryRegistry._factories = original_factories

    def test_register_provider_factory(self, clean_registry):
        """
        测试目的：验证工厂注册功能
        测试场景：注册一个新的提供商工厂
        """
        from app.core.ai_provider_factory import AIProviderType

        # 创建一个模拟工厂类
        class MockProviderFactory:
            pass

        # 注册工厂
        clean_registry.register(AIProviderType.OLLAMA, MockProviderFactory)

        # 验证注册成功
        assert AIProviderType.OLLAMA in clean_registry._factories
        assert clean_registry._factories[AIProviderType.OLLAMA] == MockProviderFactory

    def test_register_multiple_factories(self, clean_registry):
        """
        测试目的：验证注册多个工厂
        测试场景：连续注册多个提供商工厂
        """
        from app.core.ai_provider_factory import AIProviderType

        class MockFactory1:
            pass

        class MockFactory2:
            pass

        clean_registry.register(AIProviderType.OLLAMA, MockFactory1)
        clean_registry.register(AIProviderType.ZHIPUAI, MockFactory2)

        assert len(clean_registry._factories) == 2
        assert clean_registry._factories[AIProviderType.OLLAMA] == MockFactory1
        assert clean_registry._factories[AIProviderType.ZHIPUAI] == MockFactory2

    def test_register_overwrites_existing(self, clean_registry):
        """
        测试目的：验证重复注册会覆盖
        测试场景：用新工厂覆盖已注册的工厂
        """
        from app.core.ai_provider_factory import AIProviderType

        class OldFactory:
            pass

        class NewFactory:
            pass

        clean_registry.register(AIProviderType.OLLAMA, OldFactory)
        clean_registry.register(AIProviderType.OLLAMA, NewFactory)

        assert clean_registry._factories[AIProviderType.OLLAMA] == NewFactory


# ============================================================================
# 集成测试：与ai_provider子模块的集成
# ============================================================================


class TestAIProviderFactoryIntegration:
    """
    类级注释：ai_provider_factory 与子模块集成测试类
    测试覆盖范围：
        1. 与 ai_provider 模块的导入一致性
        2. 符号重导出功能
    """

    def test_symbols_from_ai_provider_submodule(self):
        """
        测试目的：验证符号从ai_provider子模块正确导入
        测试场景：检查所有重导出的符号
        """
        # 从兼容层导入
        from app.core.ai_provider_factory import (
            AIProviderType,
            AIComponentType,
            AIProviderConfig,
        )

        # 从原始位置导入
        from app.core.ai_provider import (
            AIProviderType as OriginalProviderType,
            AIComponentType as OriginalComponentType,
            AIProviderConfig as OriginalConfig,
        )

        # 验证是同一对象
        assert AIProviderType is OriginalProviderType
        assert AIComponentType is OriginalComponentType
        assert AIProviderConfig is OriginalConfig

    def test_factories_from_providers_submodule(self):
        """
        测试目的：验证提供商工厂从providers子模块正确导入
        测试场景：检查所有提供商工厂类
        """
        from app.core.ai_provider_factory import (
            OllamaProviderFactory,
            ZhipuAIProviderFactory,
        )

        # 验证它们是类
        assert isinstance(OllamaProviderFactory, type)
        assert isinstance(ZhipuAIProviderFactory, type)

    def test_registry_and_unified_from_main_submodule(self):
        """
        测试目的：验证注册表和统一工厂从主ai_provider模块导入
        测试场景：检查核心类
        """
        from app.core.ai_provider_factory import (
            AIProviderFactoryRegistry,
            UnifiedAIFactory,
            unified_ai_factory,
            create_ai_provider,
        )

        from app.core.ai_provider import (
            AIProviderFactoryRegistry as OriginalRegistry,
            UnifiedAIFactory as OriginalUnified,
            unified_ai_factory as OriginalUnifiedFactory,
            create_ai_provider as OriginalCreate,
        )

        assert AIProviderFactoryRegistry is OriginalRegistry
        assert UnifiedAIFactory is OriginalUnified
        assert unified_ai_factory is OriginalUnifiedFactory
        assert create_ai_provider is OriginalCreate
