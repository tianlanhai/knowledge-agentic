"""
文件级注释：Token 定价计算器测试
内部逻辑：测试各种模型的 Token 定价计算功能
"""

import pytest
from app.core.token_pricing import TokenPricingCalculator, ModelPricing
from decimal import Decimal


class TestTokenPricingCalculator:
    """
    类级注释：TokenPricingCalculator 测试类
    """

    def test_get_model_pricing_known_models(self):
        """
        函数级注释：测试获取已知模型的定价信息
        内部逻辑：验证智谱AI和Ollama模型的价格配置正确性
        """
        # 内部变量：测试智谱 AI 模型（glm-4）
        pricing = TokenPricingCalculator.get_model_pricing("glm-4")
        assert pricing is not None
        # 内部逻辑：验证返回的是ModelPricing对象，检查属性值
        assert isinstance(pricing, ModelPricing)
        assert pricing.prompt_price > 0
        assert pricing.completion_price > 0

        # 内部变量：测试 Ollama 模型（免费）
        pricing = TokenPricingCalculator.get_model_pricing("ollama/llama2")
        assert pricing is not None
        assert isinstance(pricing, ModelPricing)
        assert pricing.prompt_price == 0
        assert pricing.completion_price == 0

    def test_get_model_pricing_unknown_model(self):
        """
        函数级注释：测试获取未知模型的定价信息（应返回 None）
        """
        pricing = TokenPricingCalculator.get_model_pricing("unknown-model")
        # 内部逻辑：未知模型应返回 None
        assert pricing is None

    def test_calculate_cost(self):
        """
        函数级注释：测试计算 Token 成本
        内部逻辑：验证成本计算返回正确的字典结构
        """
        # 内部变量：测试智谱 AI 模型
        cost = TokenPricingCalculator.calculate_cost("glm-4", 1000, 500)
        # 内部逻辑：验证返回字典格式
        assert isinstance(cost, dict)
        assert "total_cost" in cost
        assert cost["total_cost"] > 0

        # 内部变量：测试 Ollama 模型（免费）
        cost = TokenPricingCalculator.calculate_cost("ollama/llama2", 1000, 500)
        assert cost["total_cost"] == 0

        # 内部变量：测试未知模型
        cost = TokenPricingCalculator.calculate_cost("unknown-model", 1000, 500)
        assert cost["total_cost"] == 0

    def test_calculate_cost_with_none_tokens(self):
        """
        函数级注释：测试Token数量为0时的成本计算
        """
        cost = TokenPricingCalculator.calculate_cost("glm-4", 0, 0)
        assert cost["total_cost"] == 0
        assert cost["total_tokens"] == 0

    def test_calculate_cost_with_large_tokens(self):
        """
        函数级注释：测试大Token数量的成本计算
        """
        cost = TokenPricingCalculator.calculate_cost("glm-4", 100000, 50000)
        assert cost["total_cost"] > 0
        assert cost["total_tokens"] == 150000

    def test_estimate_tokens_by_characters(self):
        """
        函数级注释：测试通过字符数估算 Token 数
        内部逻辑：验证中英文文本估算正确
        """
        # 内部变量：中文文本估算
        text = "这是一段测试文本，用于估算 Token 数量。"
        tokens = TokenPricingCalculator.estimate_tokens(text)
        assert tokens > 0

        # 内部变量：英文文本估算
        text = "This is a test text for estimating token count."
        tokens = TokenPricingCalculator.estimate_tokens(text)
        assert tokens > 0

    def test_estimate_tokens_with_empty_text(self):
        """
        函数级注释：测试空文本的Token估算
        """
        tokens = TokenPricingCalculator.estimate_tokens("")
        # 内部逻辑：空文本至少返回1
        assert tokens >= 1

    def test_estimate_tokens_with_short_text(self):
        """
        函数级注释：测试短文本的Token估算
        """
        text = "测试"
        tokens = TokenPricingCalculator.estimate_tokens(text)
        assert tokens >= 1

    def test_estimate_tokens_with_long_text(self):
        """
        函数级注释：测试长文本的Token估算
        """
        text = "这是一个很长的测试文本。" * 100
        tokens = TokenPricingCalculator.estimate_tokens(text)
        assert tokens > 100

    def test_model_pricing_database(self):
        """
        函数级注释：测试模型定价数据库的完整性
        """
        # 测试几个主要模型
        models = ["glm-4", "glm-3-turbo", "abab5.5-chat"]
        for model in models:
            pricing = TokenPricingCalculator.get_model_pricing(model)
            assert pricing is not None, f"Model {model} pricing not found"

    def test_mini_max_pricing(self):
        """
        函数级注释：测试 MiniMax 模型定价
        """
        pricing = TokenPricingCalculator.get_model_pricing("abab5.5-chat")
        assert pricing is not None
        assert pricing.prompt_price > 0
