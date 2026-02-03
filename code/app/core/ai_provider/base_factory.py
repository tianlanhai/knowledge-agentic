# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：AI提供商工厂基类模块
内部逻辑：使用模板方法模式提取参数处理的公共逻辑，消除代码重复
设计模式：模板方法模式（Template Method Pattern）
设计原则：DRY原则（Don't Repeat Yourself）、开闭原则

实现说明：
    - 提供 _build_params 模板方法，统一处理参数构建逻辑
    - 子类只需实现 _get_default_model 和特定逻辑
    - 支持 api_key、base_url、extra_params 的统一处理
"""

from abc import abstractmethod
from typing import Any, Dict, Optional
from loguru import logger

from app.core.ai_provider.base import AIProviderFactory, AIProviderType, AIComponentType
from app.core.ai_provider.config import AIProviderConfig


class BaseAIProviderFactory(AIProviderFactory):
    """
    类级注释：AI提供商工厂基类
    内部逻辑：定义参数处理的模板方法，子类只需实现特定逻辑
    设计模式：模板方法模式 - 抽象类
    职责：
        1. 提供统一的参数构建逻辑（_build_params）
        2. 提供统一的LLM创建流程（create_llm）
        3. 提供统一的Embedding创建流程（create_embeddings）
        4. 子类只需定义默认模型和具体类名

    使用示例：
        class MyProviderFactory(BaseAIProviderFactory):
            DEFAULT_LLM_MODEL = "my-model"
            DEFAULT_EMBEDDING_MODEL = "my-embedding"

            def _get_llm_class(self):
                from my_provider import MyLLM
                return MyLLM

            def _get_embedding_class(self):
                from my_provider import MyEmbedding
                return MyEmbedding
    """

    # 内部变量：默认模型配置（子类覆盖）
    DEFAULT_LLM_MODEL: Optional[str] = None
    DEFAULT_EMBEDDING_MODEL: Optional[str] = None

    # 内部变量：是否必须提供api_key
    REQUIRES_API_KEY: bool = False

    # 内部变量：是否必须提供base_url
    REQUIRES_BASE_URL: bool = False

    def create_llm(self, config: AIProviderConfig) -> Any:
        """
        函数级注释：创建LLM实例（模板方法）
        内部逻辑：构建参数 -> 获取类 -> 创建实例 -> 记录日志
        参数：
            config - 提供商配置
        返回值：LLM实例
        """
        # 内部逻辑：使用模板方法构建参数
        params = self._build_llm_params(config)

        # 内部逻辑：获取具体的LLM类
        llm_class = self._get_llm_class()

        # 内部逻辑：创建实例
        instance = llm_class(**params)

        logger.info(f"创建 {self.provider_type.value} LLM: model={params.get('model')}")
        return instance

    def create_embeddings(self, config: AIProviderConfig) -> Any:
        """
        函数级注释：创建Embedding实例（模板方法）
        内部逻辑：构建参数 -> 获取类 -> 创建实例 -> 记录日志
        参数：
            config - 提供商配置
        返回值：Embedding实例
        """
        # 内部逻辑：使用模板方法构建参数
        params = self._build_embedding_params(config)

        # 内部逻辑：获取具体的Embedding类
        embedding_class = self._get_embedding_class()

        # 内部逻辑：创建实例
        instance = embedding_class(**params)

        logger.info(f"创建 {self.provider_type.value} Embeddings: model={params.get('model')}")
        return instance

    # ===== 模板方法 - 子类可覆盖 =====

    def _build_llm_params(self, config: AIProviderConfig) -> Dict[str, Any]:
        """
        函数级注释：构建LLM参数（模板方法）
        内部逻辑：构建通用参数 -> 条件添加可选参数 -> 合并额外参数
        参数：
            config - 提供商配置
        返回值：参数字典
        """
        # 内部逻辑：基础参数
        params = {
            "model": config.model or self._get_default_llm_model(),
        }

        # 内部逻辑：条件添加 api_key
        if config.api_key:
            params["api_key"] = config.api_key

        # 内部逻辑：条件添加 base_url
        if config.base_url:
            params["base_url"] = config.base_url

        # 内部逻辑：合并额外参数
        params.update(config.extra_params)

        # 内部逻辑：子类特定处理（钩子方法）
        params = self._customize_llm_params(params, config)

        return params

    def _build_embedding_params(self, config: AIProviderConfig) -> Dict[str, Any]:
        """
        函数级注释：构建Embedding参数（模板方法）
        内部逻辑：构建通用参数 -> 条件添加可选参数 -> 合并额外参数
        参数：
            config - 提供商配置
        返回值：参数字典
        """
        # 内部逻辑：基础参数
        params = {
            "model": config.model or self._get_default_embedding_model(),
        }

        # 内部逻辑：条件添加 api_key
        if config.api_key:
            params["api_key"] = config.api_key

        # 内部逻辑：条件添加 base_url
        if config.base_url:
            params["base_url"] = config.base_url

        # 内部逻辑：合并额外参数
        params.update(config.extra_params)

        # 内部逻辑：子类特定处理（钩子方法）
        params = self._customize_embedding_params(params, config)

        return params

    def _customize_llm_params(self, params: Dict[str, Any], config: AIProviderConfig) -> Dict[str, Any]:
        """
        函数级注释：自定义LLM参数（钩子方法）
        内部逻辑：子类可覆盖此方法添加特定处理
        参数：
            params - 已构建的参数字典
            config - 提供商配置
        返回值：定制后的参数字典
        """
        return params

    def _customize_embedding_params(self, params: Dict[str, Any], config: AIProviderConfig) -> Dict[str, Any]:
        """
        函数级注释：自定义Embedding参数（钩子方法）
        内部逻辑：子类可覆盖此方法添加特定处理
        参数：
            params - 已构建的参数字典
            config - 提供商配置
        返回值：定制后的参数字典
        """
        return params

    def _get_default_llm_model(self) -> str:
        """
        函数级注释：获取默认LLM模型名称
        返回值：模型名称
        """
        return self.DEFAULT_LLM_MODEL or "default"

    def _get_default_embedding_model(self) -> str:
        """
        函数级注释：获取默认Embedding模型名称
        返回值：模型名称
        """
        return self.DEFAULT_EMBEDDING_MODEL or "default"

    # ===== 抽象方法 - 子类必须实现 =====

    @abstractmethod
    def _get_llm_class(self) -> type:
        """
        函数级注释：获取LLM类（抽象方法）
        内部逻辑：子类必须实现，返回具体的LLM类
        返回值：LLM类
        """
        pass

    @abstractmethod
    def _get_embedding_class(self) -> type:
        """
        函数级注释：获取Embedding类（抽象方法）
        内部逻辑：子类必须实现，返回具体的Embedding类
        返回值：Embedding类
        """
        pass


# 内部变量：导出所有公共接口
__all__ = [
    'BaseAIProviderFactory',
]
