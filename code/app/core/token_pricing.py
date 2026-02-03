"""
上海宇羲伏天智能科技有限公司出品

文件级注释：Token价格配置和成本计算模块
内部逻辑：定义各LLM模型的Token价格，提供成本计算工具类
"""

from decimal import Decimal
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class ModelPricing:
    """
    类级注释：模型价格配置数据类
    属性：
        prompt_price: 输入价格（元/1K tokens）
        completion_price: 输出价格（元/1K tokens）
        currency: 货币单位（默认CNY）
    """
    prompt_price: Decimal  # 输入价格（元/1K tokens）
    completion_price: Decimal  # 输出价格（元/1K tokens）
    currency: str = "CNY"  # 货币单位


# ============================================================================
# 模型价格配置表
# 内部逻辑：维护各模型提供商的Token价格，单位为元/1K tokens
# 价格来源：官方定价（2025年1月）
# ============================================================================

TOKEN_PRICING: Dict[str, ModelPricing] = {
    # ============================================================================
    # 智谱AI (ZhipuAI)
    # 官网：https://open.bigmodel.cn/pricing
    # ============================================================================
    "glm-4": ModelPricing(
        prompt_price=Decimal("0.1"),      # 0.1元/1K tokens
        completion_price=Decimal("0.1")   # 0.1元/1K tokens
    ),
    "glm-4-air": ModelPricing(
        prompt_price=Decimal("0.01"),     # 0.01元/1K tokens
        completion_price=Decimal("0.01")  # 0.01元/1K tokens
    ),
    "glm-4-flash": ModelPricing(
        prompt_price=Decimal("0.001"),    # 0.001元/1K tokens
        completion_price=Decimal("0.001") # 0.001元/1K tokens
    ),
    "glm-4-plus": ModelPricing(
        prompt_price=Decimal("0.05"),     # 0.05元/1K tokens
        completion_price=Decimal("0.05")  # 0.05元/1K tokens
    ),
    "glm-3-turbo": ModelPricing(
        prompt_price=Decimal("0.005"),    # 0.005元/1K tokens
        completion_price=Decimal("0.005") # 0.005元/1K tokens
    ),
    "glm-4v": ModelPricing(
        prompt_price=Decimal("0.05"),     # 0.05元/1K tokens
        completion_price=Decimal("0.05")  # 0.05元/1K tokens
    ),

    # ============================================================================
    # MiniMax
    # 官网：https://api.minimax.chat/document/price
    # ============================================================================
    "abab5.5-chat": ModelPricing(
        prompt_price=Decimal("0.015"),    # 0.015元/1K tokens
        completion_price=Decimal("0.03")  # 0.03元/1K tokens
    ),
    "abab5.5s-chat": ModelPricing(
        prompt_price=Decimal("0.005"),    # 0.005元/1K tokens
        completion_price=Decimal("0.005") # 0.005元/1K tokens
    ),

    # ============================================================================
    # 月之暗面 (Moonshot)
    # 官网：https://platform.moonshot.cn/docs/pricing
    # ============================================================================
    "moonshot-v1-8k": ModelPricing(
        prompt_price=Decimal("0.012"),    # 0.012元/1K tokens
        completion_price=Decimal("0.012") # 0.012元/1K tokens
    ),
    "moonshot-v1-32k": ModelPricing(
        prompt_price=Decimal("0.024"),    # 0.024元/1K tokens
        completion_price=Decimal("0.024") # 0.024元/1K tokens
    ),
    "moonshot-v1-128k": ModelPricing(
        prompt_price=Decimal("0.06"),     # 0.06元/1K tokens
        completion_price=Decimal("0.06")  # 0.06元/1K tokens
    ),

    # ============================================================================
    # Ollama (本地部署，免费)
    # ============================================================================
    # 所有Ollama模型都是本地运行，无API调用费用
    "ollama": ModelPricing(
        prompt_price=Decimal("0"),
        completion_price=Decimal("0")
    ),
    # Ollama常用模型别名
    "llama2": ModelPricing(
        prompt_price=Decimal("0"),
        completion_price=Decimal("0")
    ),
    "llama3": ModelPricing(
        prompt_price=Decimal("0"),
        completion_price=Decimal("0")
    ),
    "deepseek-r1": ModelPricing(
        prompt_price=Decimal("0"),
        completion_price=Decimal("0")
    ),
    "qwen": ModelPricing(
        prompt_price=Decimal("0"),
        completion_price=Decimal("0")
    ),
    "mistral": ModelPricing(
        prompt_price=Decimal("0"),
        completion_price=Decimal("0")
    ),
    "gemma": ModelPricing(
        prompt_price=Decimal("0"),
        completion_price=Decimal("0")
    ),
    "phi": ModelPricing(
        prompt_price=Decimal("0"),
        completion_price=Decimal("0")
    ),
}


class TokenPricingCalculator:
    """
    类级注释：Token成本计算工具类
    内部逻辑：根据模型名称和Token使用量计算成本
    """

    @staticmethod
    def get_model_pricing(model_name: str) -> Optional[ModelPricing]:
        """
        函数级注释：获取模型价格配置
        内部逻辑：先精确匹配，再模糊匹配，支持模型别名
        参数：
            model_name: 模型名称（如 glm-4, deepseek-r1:8b, ollama）
        返回值：ModelPricing 或 None
        """
        # 内部逻辑：去除版本号后缀，提取核心模型名
        base_model = model_name.split(":")[0].split("-")[0].lower()

        # 内部逻辑：精确匹配
        if model_name in TOKEN_PRICING:
            return TOKEN_PRICING[model_name]

        # 内部逻辑：模糊匹配（匹配模型前缀）
        for key, pricing in TOKEN_PRICING.items():
            if base_model in key.lower() or key.lower() in base_model:
                return pricing

        # 内部逻辑：Ollama 模型默认免费
        if "ollama" in base_model or base_model in ["llama", "deepseek", "qwen", "mistral", "gemma", "phi"]:
            return ModelPricing(
                prompt_price=Decimal("0"),
                completion_price=Decimal("0")
            )

        # 内部逻辑：未找到价格配置
        return None

    @staticmethod
    def calculate_cost(
        model_name: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0
    ) -> Dict[str, Decimal]:
        """
        函数级注释：计算Token使用成本
        内部逻辑：根据模型价格配置计算总成本
        参数：
            model_name: 模型名称
            prompt_tokens: 输入Token数量
            completion_tokens: 输出Token数量
        返回值：包含各成本项的字典
        """
        # 内部逻辑：获取模型价格配置
        pricing = TokenPricingCalculator.get_model_pricing(model_name)

        # Guard Clause：未找到价格配置
        if pricing is None:
            return {
                "prompt_cost": Decimal("0"),
                "completion_cost": Decimal("0"),
                "total_cost": Decimal("0"),
                "total_tokens": prompt_tokens + completion_tokens,
                "currency": "CNY"
            }

        # 内部逻辑：计算成本（元/1K tokens * tokens / 1000）
        prompt_cost = pricing.prompt_price * Decimal(prompt_tokens) / Decimal("1000")
        completion_cost = pricing.completion_price * Decimal(completion_tokens) / Decimal("1000")
        total_cost = prompt_cost + completion_cost

        return {
            "prompt_cost": prompt_cost.quantize(Decimal("0.000001")),  # 保留6位小数
            "completion_cost": completion_cost.quantize(Decimal("0.000001")),
            "total_cost": total_cost.quantize(Decimal("0.000001")),
            "total_tokens": prompt_tokens + completion_tokens,
            "currency": pricing.currency
        }

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        函数级注释：估算文本的Token数量
        内部逻辑：使用简单启发式方法，1个Token约等于1.5个中文字或0.75个英文单词
        参数：
            text: 输入文本
        返回值：估算的Token数量
        """
        # 内部变量：初始化计数
        chinese_chars = 0
        english_words = 0

        # 内部逻辑：遍历文本字符
        i = 0
        while i < len(text):
            char = text[i]

            # 内部逻辑：判断是否为中文字符
            if '\u4e00' <= char <= '\u9fff':
                chinese_chars += 1
                i += 1
            # 内部逻辑：英文和数字
            elif char.isalnum() or char in "_-":
                # 内部逻辑：统计完整单词
                word_start = i
                while i < len(text) and (text[i].isalnum() or text[i] in "_-"):
                    i += 1
                if i > word_start:
                    english_words += 1
            else:
                i += 1

        # 内部逻辑：按比例估算Token
        # 中文：1 Token ≈ 1.5 字
        # 英文：1 Token ≈ 0.75 词
        estimated_tokens = int(chinese_chars / 1.5 + english_words / 0.75)

        return max(estimated_tokens, 1)  # 至少1个Token


# ============================================================================
# 便捷函数
# ============================================================================

def calculate_token_cost(
    model_name: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0
) -> Dict[str, Decimal]:
    """
    函数级注释：计算Token成本的便捷函数
    内部逻辑：调用 TokenPricingCalculator.calculate_cost()
    参数：
        model_name: 模型名称
        prompt_tokens: 输入Token数量
        completion_tokens: 输出Token数量
    返回值：包含各成本项的字典
    """
    return TokenPricingCalculator.calculate_cost(
        model_name=model_name,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens
    )


def get_model_price(model_name: str) -> Optional[ModelPricing]:
    """
    函数级注释：获取模型价格的便捷函数
    内部逻辑：调用 TokenPricingCalculator.get_model_pricing()
    参数：
        model_name: 模型名称
    返回值：ModelPricing 或 None
    """
    return TokenPricingCalculator.get_model_pricing(model_name)
