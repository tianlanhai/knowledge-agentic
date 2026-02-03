# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：智谱AI提供商工厂模块
设计模式：抽象工厂模式 + 模板方法模式 - 具体工厂
设计原则：单一职责原则、DRY原则
"""

from typing import Any, Dict
from loguru import logger

from app.core.ai_provider.base import AIProviderType
from app.core.ai_provider.base_factory import BaseAIProviderFactory
from app.core.ai_provider.config import AIProviderConfig
from app.core.endpoint_utils import EndpointUtils


class ZhipuAIProviderFactory(BaseAIProviderFactory):
    """
    类级注释：智谱 AI 提供商工厂
    设计模式：模板方法模式 - 具体实现
    职责：
        1. 创建智谱AI LLM 实例
        2. 创建智谱AI Embeddings 实例
        3. 定义默认模型名称
    """

    provider_type = AIProviderType.ZHIPUAI

    # 内部变量：默认模型配置
    DEFAULT_LLM_MODEL = "glm-4"
    DEFAULT_EMBEDDING_MODEL = "embedding-2"

    # 内部变量：智谱AI需要api_key
    REQUIRES_API_KEY = True

    def _get_llm_class(self) -> type:
        """
        函数级注释：获取智谱AI LLM类
        返回值：ChatZhipuAI类或ZhipuAI类
        """
        try:
            from langchain_community.chat_models import ChatZhipuAI
            return ChatZhipuAI
        except ImportError:
            # 内部逻辑：返回备用的ZhipuAI类（用于直接创建）
            from zhipuai import ZhipuAI
            return ZhipuAI

    def _get_embedding_class(self) -> type:
        """
        函数级注释：获取智谱AI Embedding类
        返回值：ZhipuAIEmbeddings类
        """
        from app.utils.zhipuai_embeddings import ZhipuAIEmbeddings
        return ZhipuAIEmbeddings

    def _customize_llm_params(self, params: Dict[str, Any], config: AIProviderConfig) -> Dict[str, Any]:
        """
        函数级注释：自定义LLM参数（智谱AI特定）
        内部逻辑：将通用参数名转换为智谱AI特定的参数名，并规范化端点路径
        参数：
            params - 已构建的参数字典
            config - 提供商配置
        返回值：定制后的参数字典
        """
        # 内部逻辑：智谱AI使用特定的参数名
        # ChatZhipuAI 期望: zhipuai_api_key, zhipuai_api_base, model_name
        # 而基类传递的是: api_key, base_url, model

        # 内部逻辑：使用 EndpointUtils 规范化智谱AI端点，自动补全 /chat/completions 路径
        # 支持用户只配置 base URL（如 https://open.bigmodel.cn/api/paas/v4）
        # 或完整路径（如 https://open.bigmodel.cn/api/paas/v4/chat/completions）
        if 'base_url' in params:
            params['base_url'] = EndpointUtils.normalize_zhipuai_endpoint(params['base_url'], "/chat/completions")
            logger.debug(f"智谱AI端点已规范化: {params['base_url']}")

        # 内部逻辑：api_key -> zhipuai_api_key
        if 'api_key' in params:
            params['zhipuai_api_key'] = params.pop('api_key')

        # 内部逻辑：base_url -> zhipuai_api_base
        if 'base_url' in params:
            params['zhipuai_api_base'] = params.pop('base_url')

        # 内部逻辑：model -> model_name
        if 'model' in params:
            params['model_name'] = params.pop('model')

        return params

    def create_llm(self, config: AIProviderConfig) -> Any:
        """
        函数级注释：创建智谱AI LLM实例（覆盖基类方法）
        内部逻辑：智谱AI有特殊的导入处理逻辑
        参数：
            config - 提供商配置
        返回值：LLM实例
        """
        try:
            from langchain_community.chat_models import ChatZhipuAI
        except ImportError:
            from zhipuai import ZhipuAI
            return ZhipuAI(api_key=config.api_key, model=config.model or "glm-4")

        # 内部逻辑：使用模板方法构建参数
        params = self._build_llm_params(config)
        return ChatZhipuAI(**params)


__all__ = ['ZhipuAIProviderFactory']
