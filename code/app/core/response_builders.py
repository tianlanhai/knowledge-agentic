# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：配置响应建造者模块
内部逻辑：使用建造者模式统一构建配置响应对象，消除重复代码
设计模式：建造者模式
设计原则：DRY（不重复）、单一职责原则、开闭原则
"""

from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field


@dataclass
class LLMConfigResponse:
    """
    类级注释：LLM配置响应数据类
    属性：LLM配置的所有字段
    """
    id: str = ""
    provider_id: str = ""
    provider_name: str = ""
    endpoint: str = ""
    api_key_masked: str = ""
    model_id: str = ""
    model_name: str = ""
    type: str = ""
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    device: Optional[str] = None
    status: int = 0


@dataclass
class EmbeddingConfigResponse:
    """
    类级注释：Embedding配置响应数据类
    属性：Embedding配置的所有字段
    """
    id: str = ""
    provider_id: str = ""
    provider_name: str = ""
    endpoint: str = ""
    api_key_masked: str = ""
    model_id: str = ""
    model_name: str = ""
    batch_size: Optional[int] = None
    device: Optional[str] = None
    status: int = 0


class ConfigResponseBuilder:
    """
    类级注释：配置响应建造者类
    设计模式：建造者模式
    职责：
        1. 提供链式调用的方式构建配置响应
        2. 统一处理API密钥脱敏
        3. 支持LLM和Embedding两种配置类型
    """

    def __init__(self):
        """内部变量：初始化构建数据"""
        self._data: Dict[str, Any] = {}

    def with_id(self, id: str) -> 'ConfigResponseBuilder':
        """
        函数级注释：设置配置ID
        参数：
            id: 配置ID
        返回值：当前建造者实例（支持链式调用）
        """
        self._data['id'] = id
        return self

    def with_provider(self, provider_id: str, provider_name: str) -> 'ConfigResponseBuilder':
        """
        函数级注释：设置提供商信息
        参数：
            provider_id: 提供商ID
            provider_name: 提供商名称
        返回值：当前建造者实例
        """
        self._data['provider_id'] = provider_id
        self._data['provider_name'] = provider_name
        return self

    def with_endpoint(self, endpoint: Optional[str]) -> 'ConfigResponseBuilder':
        """
        函数级注释：设置端点地址
        参数：
            endpoint: 端点地址
        返回值：当前建造者实例
        """
        self._data['endpoint'] = endpoint or ""
        return self

    def with_masked_api_key(
        self,
        api_key: Optional[str],
        mask_func: Optional[Callable[[str], str]] = None
    ) -> 'ConfigResponseBuilder':
        """
        函数级注释：设置脱敏后的API密钥
        参数：
            api_key: 原始API密钥
            mask_func: 脱敏函数（可选，不传则使用默认逻辑）
        返回值：当前建造者实例
        """
        if mask_func:
            self._data['api_key_masked'] = mask_func(api_key)
        else:
            # 默认脱敏逻辑
            if not api_key:
                self._data['api_key_masked'] = ""
            elif len(api_key) <= 8:
                self._data['api_key_masked'] = "****"
            else:
                self._data['api_key_masked'] = f"{api_key[:4]}****{api_key[-4:]}"
        return self

    def with_model(self, model_id: str, model_name: str) -> 'ConfigResponseBuilder':
        """
        函数级注释：设置模型信息
        参数：
            model_id: 模型ID
            model_name: 模型名称
        返回值：当前建造者实例
        """
        self._data['model_id'] = model_id
        self._data['model_name'] = model_name
        return self

    def with_type(self, config_type: str) -> 'ConfigResponseBuilder':
        """
        函数级注释：设置配置类型（LLM专用）
        参数：
            config_type: 配置类型
        返回值：当前建造者实例
        """
        self._data['type'] = config_type
        return self

    def with_llm_params(
        self,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None
    ) -> 'ConfigResponseBuilder':
        """
        函数级注释：设置LLM参数（LLM专用）
        参数：
            temperature: 温度参数
            max_tokens: 最大token数
            top_p: top_p采样参数
            top_k: top_k采样参数
        返回值：当前建造者实例
        """
        self._data['temperature'] = temperature
        self._data['max_tokens'] = max_tokens
        self._data['top_p'] = top_p
        self._data['top_k'] = top_k
        return self

    def with_device(self, device: Optional[str]) -> 'ConfigResponseBuilder':
        """
        函数级注释：设置设备信息
        参数：
            device: 设备类型
        返回值：当前建造者实例
        """
        self._data['device'] = device
        return self

    def with_status(self, status: int) -> 'ConfigResponseBuilder':
        """
        函数级注释：设置状态
        参数：
            status: 状态值（0=未启用，1=启用）
        返回值：当前建造者实例
        """
        self._data['status'] = status
        return self

    def with_embedding_params(
        self,
        batch_size: Optional[int] = None,
        device: Optional[str] = None
    ) -> 'ConfigResponseBuilder':
        """
        函数级注释：设置Embedding参数（Embedding专用）
        参数：
            batch_size: 批处理大小
            device: 设备类型
        返回值：当前建造者实例
        """
        self._data['batch_size'] = batch_size
        self._data['device'] = device
        return self

    def build(self) -> Dict[str, Any]:
        """
        函数级注释：构建配置响应字典
        返回值：配置响应字典
        """
        return self._data.copy()

    def build_llm_response(self) -> LLMConfigResponse:
        """
        函数级注释：构建LLM配置响应对象
        返回值：LLMConfigResponse实例
        """
        return LLMConfigResponse(**self._data)

    def build_embedding_response(self) -> EmbeddingConfigResponse:
        """
        函数级注释：构建Embedding配置响应对象
        返回值：EmbeddingConfigResponse实例
        """
        return EmbeddingConfigResponse(**self._data)


class ConfigResponseBuilderUtils:
    """
    类级注释：配置响应构建工具类
    职责：提供便捷的静态方法快速构建配置响应
    """

    @staticmethod
    def build_from_model_config(
        config: Any,
        mask_func: Callable[[str], str]
    ) -> Dict[str, Any]:
        """
        函数级注释：从模型配置对象构建响应字典
        内部逻辑：提取配置对象的属性 -> 脱敏API密钥 -> 返回字典
        参数：
            config: ModelConfig或EmbeddingConfig实例
            mask_func: API密钥脱敏函数
        返回值：配置响应字典
        """
        builder = ConfigResponseBuilder()
        builder.with_id(config.id)
        builder.with_provider(config.provider_id, config.provider_name)
        builder.with_endpoint(config.endpoint)
        builder.with_masked_api_key(config.api_key, mask_func)
        builder.with_model(config.model_id, config.model_name)
        builder.with_status(config.status)

        # 处理LLM特有属性
        if hasattr(config, 'type'):
            builder.with_type(config.type)
        if hasattr(config, 'temperature'):
            builder.with_llm_params(
                temperature=config.temperature,
                max_tokens=getattr(config, 'max_tokens', None),
                top_p=getattr(config, 'top_p', None),
                top_k=getattr(config, 'top_k', None)
            )
        if hasattr(config, 'device'):
            builder.with_device(config.device)

        # 处理Embedding特有属性
        if hasattr(config, 'batch_size'):
            builder.with_embedding_params(
                batch_size=config.batch_size,
                device=config.device
            )

        return builder.build()
