# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：LLM提供者服务测试集
内部逻辑：针对llm_provider.py编写全面测试
设计模式：单例模式、服务定位器模式测试
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.llm_provider import LLMProvider, llm_provider


# ============================================================================
# 测试 LLMProvider 单例模式
# ============================================================================
class TestLLMProviderSingleton:
    """类级注释：LLMProvider单例模式测试"""

    def test_singleton_pattern(self):
        """函数级注释：测试单例模式"""
        provider1 = LLMProvider()
        provider2 = LLMProvider()

        assert provider1 is provider2
        assert id(provider1) == id(provider2)

    def test_global_instance(self):
        """函数级注释：测试全局实例"""
        from app.services.llm_provider import LLMProvider

        provider = LLMProvider()
        assert llm_provider is provider

    def test_new_returns_same_instance(self):
        """函数级注释：测试__new__返回相同实例"""
        provider1 = LLMProvider()
        provider2 = LLMProvider.__new__(LLMProvider)

        assert provider1 is provider2


# ============================================================================
# 测试 LLMProvider 初始化
# ============================================================================
class TestLLMProviderInit:
    """类级注释：LLMProvider初始化测试"""

    def setup_method(self):
        """函数级注释：每个测试前重置单例状态"""
        if hasattr(LLMProvider, '_instance'):
            LLMProvider._instance = None

    def test_init_called_once(self):
        """函数级注释：测试初始化只执行一次"""
        provider1 = LLMProvider()
        provider2 = LLMProvider()

        assert provider1 is provider2
        assert provider1._initialized is True


# ============================================================================
# 测试 LLMProvider.get_llm
# ============================================================================
class TestLLMProviderGetLLM:
    """类级注释：获取LLM实例测试"""

    def setup_method(self):
        """函数级注释：每个测试前重置单例状态"""
        if hasattr(LLMProvider, '_instance'):
            LLMProvider._instance = None

    @pytest.mark.asyncio
    async def test_get_llm_with_default_config(self):
        """函数级注释：测试使用默认配置获取LLM"""
        provider = LLMProvider()
        mock_db = Mock(spec=AsyncSession)

        # Mock ModelConfigService.get_default_config返回None
        with patch('app.services.llm_provider.ModelConfigService.get_default_config') as mock_get_config:
            mock_get_config.return_value = None

            with patch('app.services.llm_provider.LLMFactory') as mock_factory:
                mock_llm = Mock()
                mock_factory.create_llm.return_value = mock_llm

                result = await provider.get_llm(mock_db, streaming=False)

                assert result == mock_llm
                mock_factory.create_llm.assert_called_once_with(streaming=False)

    @pytest.mark.asyncio
    async def test_get_llm_with_db_config(self):
        """函数级注释：测试使用数据库配置获取LLM"""
        provider = LLMProvider()
        mock_db = Mock(spec=AsyncSession)

        # Mock数据库配置
        mock_config = Mock()
        mock_config.provider_name = "ollama"
        mock_config.model_name = "llama2"

        with patch('app.services.llm_provider.ModelConfigService.get_default_config') as mock_get_config:
            mock_get_config.return_value = mock_config

            with patch('app.services.llm_provider.LLMFactory') as mock_factory:
                mock_llm = Mock()
                mock_factory.create_from_model_config.return_value = mock_llm

                result = await provider.get_llm(mock_db, streaming=True)

                assert result == mock_llm
                mock_factory.create_from_model_config.assert_called_once_with(
                    mock_config, streaming=True
                )

    @pytest.mark.asyncio
    async def test_get_llm_streaming(self):
        """函数级注释：测试获取流式LLM"""
        provider = LLMProvider()
        mock_db = Mock(spec=AsyncSession)

        with patch('app.services.llm_provider.ModelConfigService.get_default_config') as mock_get_config:
            mock_get_config.return_value = None

            with patch('app.services.llm_provider.LLMFactory') as mock_factory:
                mock_llm = Mock()
                mock_factory.create_llm.return_value = mock_llm

                result = await provider.get_llm(mock_db, streaming=True)

                mock_factory.create_llm.assert_called_once_with(streaming=True)


# ============================================================================
# 测试 LLMProvider.refresh_config
# ============================================================================
class TestLLMProviderRefreshConfig:
    """类级注释：刷新配置测试"""

    def setup_method(self):
        """函数级注释：每个测试前重置单例状态"""
        if hasattr(LLMProvider, '_instance'):
            LLMProvider._instance = None

    @pytest.mark.asyncio
    async def test_refresh_config_with_default(self):
        """函数级注释：测试刷新有默认配置"""
        provider = LLMProvider()
        mock_db = Mock(spec=AsyncSession)

        mock_config = Mock()
        mock_config.provider_name = "zhipuai"

        with patch('app.services.llm_provider.ModelConfigService.get_default_config') as mock_get_config:
            mock_get_config.return_value = mock_config

            with patch('app.services.llm_provider.LLMFactory') as mock_factory:
                await provider.refresh_config(mock_db)

                # 验证调用
                mock_factory.create_from_model_config.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_config_without_default(self):
        """函数级注释：测试刷新无默认配置"""
        provider = LLMProvider()
        mock_db = Mock(spec=AsyncSession)

        with patch('app.services.llm_provider.ModelConfigService.get_default_config') as mock_get_config:
            mock_get_config.return_value = None

            # 不应该抛出异常
            await provider.refresh_config(mock_db)


# ============================================================================
# 测试 LLMProvider.get_llm_with_config
# ============================================================================
class TestLLMProviderGetLLMWithConfig:
    """类级注释：使用指定配置获取LLM测试"""

    def setup_method(self):
        """函数级注释：每个测试前重置单例状态"""
        if hasattr(LLMProvider, '_instance'):
            LLMProvider._instance = None

    def test_get_llm_with_config_basic(self):
        """函数级注释：测试基本配置获取LLM"""
        provider = LLMProvider()

        with patch('app.services.llm_provider.LLMFactory') as mock_factory:
            mock_llm = Mock()
            mock_factory.create_llm.return_value = mock_llm

            result = provider.get_llm_with_config(
                provider="ollama",
                model="llama2",
                api_key="test-key",
                streaming=False
            )

            assert result == mock_llm
            mock_factory.set_runtime_config.assert_called_once()
            mock_factory.create_llm.assert_called_once_with(streaming=False)

    def test_get_llm_with_config_all_params(self):
        """函数级注释：测试完整参数"""
        provider = LLMProvider()

        with patch('app.services.llm_provider.LLMFactory') as mock_factory:
            mock_llm = Mock()
            mock_factory.create_llm.return_value = mock_llm

            result = provider.get_llm_with_config(
                provider="zhipuai",
                model="chatglm",
                api_key="api-123",
                endpoint="https://api.example.com",
                temperature=0.8,
                streaming=True
            )

            # 验证set_runtime_config被调用
            call_args = mock_factory.set_runtime_config.call_args
            config = call_args[0][0]

            assert config["provider"] == "zhipuai"
            assert config["model"] == "chatglm"
            assert config["api_key"] == "api-123"
            assert config["endpoint"] == "https://api.example.com"
            assert config["temperature"] == 0.8

    def test_get_llm_with_config_minimal(self):
        """函数级注释：测试最小参数"""
        provider = LLMProvider()

        with patch('app.services.llm_provider.LLMFactory') as mock_factory:
            mock_llm = Mock()
            mock_factory.create_llm.return_value = mock_llm

            result = provider.get_llm_with_config(
                provider="ollama",
                model="llama2"
            )

            assert result == mock_llm

    def test_get_llm_with_config_zero_temperature(self):
        """函数级注释：测试零温度参数"""
        provider = LLMProvider()

        with patch('app.services.llm_provider.LLMFactory') as mock_factory:
            mock_llm = Mock()
            mock_factory.create_llm.return_value = mock_llm

            result = provider.get_llm_with_config(
                provider="ollama",
                model="llama2",
                temperature=0.0
            )

            assert result == mock_llm
            call_args = mock_factory.set_runtime_config.call_args[0][0]
            assert call_args["temperature"] == 0.0


# ============================================================================
# 测试全局实例
# ============================================================================
class TestGlobalLLMProvider:
    """类级注释：全局LLMProvider实例测试"""

    def setup_method(self):
        """函数级注释：每个测试前重置单例状态"""
        if hasattr(LLMProvider, '_instance'):
            LLMProvider._instance = None

    def test_global_llm_provider_singleton(self):
        """函数级注释：测试全局实例是单例"""
        from app.services.llm_provider import llm_provider as provider1

        # 再次导入
        from app.services.llm_provider import llm_provider as provider2

        assert provider1 is provider2

    def test_global_llm_provider_attributes(self):
        """函数级注释：测试全局实例属性"""
        assert hasattr(llm_provider, '_initialized')
        assert hasattr(llm_provider, 'get_llm')
        assert hasattr(llm_provider, 'refresh_config')
        assert hasattr(llm_provider, 'get_llm_with_config')


# ============================================================================
# 运行测试
# ============================================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
