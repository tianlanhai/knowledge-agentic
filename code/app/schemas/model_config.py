# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：模型配置Schema
内部逻辑：定义模型配置相关的Pydantic模型，用于请求验证和响应序列化
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Dict, Any


class ModelConfigBase(BaseModel):
    """
    类级注释：模型配置基础模型
    属性：
        provider_id: 提供商ID（ollama、zhipuai、openai等）
        provider_name: 提供商名称（可选，根据provider_id自动填充）
        endpoint: API端点地址
        api_key: API密钥
        model_id: 模型ID（可选，使用model_name作为值）
        model_name: 模型名称
        type: 模型类型（text、embedding）
        temperature: 温度参数（0-2）
        max_tokens: 最大生成token数
        top_p: nucleus采样参数
        top_k: top-k采样参数
        status: 状态（1启用 0禁用）
    """
    provider_id: str = Field(..., min_length=1, description="提供商ID")
    provider_name: str = Field("", description="提供商名称（可选，自动填充）")
    endpoint: str = Field("", description="API端点地址")
    api_key: str = Field("", description="API密钥")
    model_id: str = Field("", description="模型ID（可选，自动填充）")
    model_name: str = Field(..., min_length=1, description="模型名称")
    type: str = Field("text", description="模型类型(text/embedding)")
    temperature: float = Field(0.7, ge=0, le=2, description="温度参数")
    max_tokens: int = Field(8192, ge=1, description="最大token数")
    top_p: float = Field(0.9, ge=0, le=1, description="nucleus采样参数")
    top_k: int = Field(0, ge=0, description="top-k采样参数")
    device: str = Field("auto", description="运行设备(cpu/cuda/auto)")
    status: int = Field(1, ge=0, le=1, description="状态(1启用/0禁用)")

    # 属性：Pydantic v2 配置，允许使用 model_ 前缀的字段
    model_config = ConfigDict(protected_namespaces=())

    @field_validator('provider_name', mode='before')
    @classmethod
    def fill_llm_provider_name(cls, v: str, info) -> str:
        """
        函数级注释：自动补全提供商名称
        内部逻辑：如果provider_name为空，根据provider_id从常量中查找名称
        参数：
            v: 当前provider_name值
            info: Pydantic验证上下文
        返回值：提供商名称
        """
        if v:
            return v
        provider_id = info.data.get('provider_id')
        if provider_id:
            from app.core.llm_constants import PROVIDER_ID_MAP
            return PROVIDER_ID_MAP.get(provider_id, provider_id)
        return v

    @field_validator('model_id', mode='before')
    @classmethod
    def fill_llm_model_id(cls, v: str, info) -> str:
        """
        函数级注释：自动补全模型ID
        内部逻辑：如果model_id为空，使用model_name作为值
        参数：
            v: 当前model_id值
            info: Pydantic验证上下文
        返回值：模型ID
        """
        if v:
            return v
        return info.data.get('model_name', v)


class ModelConfigCreate(ModelConfigBase):
    """
    类级注释：创建模型配置请求模型
    属性：继承ModelConfigBase，额外包含id字段（可选）
    """
    id: Optional[str] = Field(None, description="配置ID，新建时为空")


class ModelConfigUpdate(BaseModel):
    """
    类级注释：更新模型配置请求模型
    属性：所有字段都是可选的，支持部分更新
    """
    provider_id: Optional[str] = Field(None, description="提供商ID")
    provider_name: Optional[str] = Field(None, description="提供商名称")
    endpoint: Optional[str] = Field(None, description="API端点地址")
    api_key: Optional[str] = Field(None, description="API密钥")
    model_id: Optional[str] = Field(None, description="模型ID")
    model_name: Optional[str] = Field(None, description="模型名称")
    type: Optional[str] = Field(None, description="模型类型")
    temperature: Optional[float] = Field(None, ge=0, le=2, description="温度参数")
    max_tokens: Optional[int] = Field(None, ge=1, description="最大token数")
    top_p: Optional[float] = Field(None, ge=0, le=1, description="nucleus采样参数")
    top_k: Optional[int] = Field(None, ge=0, description="top-k采样参数")
    device: Optional[str] = Field(None, description="运行设备")
    status: Optional[int] = Field(None, ge=0, le=1, description="状态")

    # 属性：Pydantic v2 配置，允许使用 model_ 前缀的字段
    model_config = ConfigDict(protected_namespaces=())


class ModelConfigResponse(ModelConfigBase):
    """
    类级注释：模型配置响应模型
    属性：继承ModelConfigBase，额外包含id字段
    """
    id: str = Field(..., description="配置ID")

    # 属性：Pydantic v2 配置，继承父类配置并添加 from_attributes
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)


class ModelConfigResponseSafe(BaseModel):
    """
    类级注释：模型配置响应模型（安全版本，不包含完整API Key）
    属性：api_key_masked 脱敏显示的密钥（格式如 sk-****1234）
    """
    provider_id: str = Field(..., min_length=1, description="提供商ID")
    provider_name: str = Field("", description="提供商名称")
    endpoint: str = Field("", description="API端点地址")
    api_key_masked: str = Field("", description="API密钥脱敏显示")
    model_id: str = Field("", description="模型ID")
    model_name: str = Field(..., min_length=1, description="模型名称")
    type: str = Field("text", description="模型类型(text/embedding)")
    temperature: float = Field(0.7, ge=0, le=2, description="温度参数")
    max_tokens: int = Field(8192, ge=1, description="最大token数")
    top_p: float = Field(0.9, ge=0, le=1, description="nucleus采样参数")
    top_k: int = Field(0, ge=0, description="top-k采样参数")
    device: Optional[str] = Field(None, description="运行设备")
    status: int = Field(1, ge=0, le=1, description="状态(1启用/0禁用)")
    id: str = Field(..., description="配置ID")

    # 属性：Pydantic v2 配置，允许使用 model_ 前缀的字段
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)


class APIKeyUpdateRequest(BaseModel):
    """
    类级注释：更新API密钥请求模型
    属性：仅包含 api_key 字段，用于单独更新密钥
    """
    api_key: str = Field(..., description="新的API密钥", min_length=1)


class APIKeyUpdateResponse(BaseModel):
    """
    类级注释：更新API密钥响应模型
    属性：返回脱敏后的密钥
    """
    api_key_masked: str = Field(..., description="更新后的API密钥脱敏显示")
    message: str = Field(default="API密钥已更新", description="操作结果消息")


class EmbeddingConfigBase(BaseModel):
    """
    类级注释：Embedding配置基础模型
    属性：
        provider_id: 提供商ID（ollama、zhipuai、local等）
        provider_name: 提供商名称（可选，根据provider_id自动填充）
        endpoint: API端点地址
        api_key: API密钥
        model_id: 模型ID（可选，使用model_name作为值）
        model_name: 模型名称
        device: 运行设备（cpu、cuda、auto）
        status: 状态（1启用 0禁用）
    """
    provider_id: str = Field(..., min_length=1, description="提供商ID")
    provider_name: str = Field("", description="提供商名称（可选，自动填充）")
    endpoint: str = Field("", description="API端点地址")
    api_key: str = Field("", description="API密钥")
    model_id: str = Field("", description="模型ID（可选，自动填充）")
    model_name: str = Field(..., min_length=1, description="模型名称")
    device: str = Field("cpu", description="运行设备(cpu/cuda/auto)")
    status: int = Field(1, ge=0, le=1, description="状态(1启用/0禁用)")

    # 属性：Pydantic v2 配置，允许使用 model_ 前缀的字段
    model_config = ConfigDict(protected_namespaces=())

    @field_validator('provider_name', mode='before')
    @classmethod
    def fill_embedding_provider_name(cls, v: str, info) -> str:
        """
        函数级注释：自动补全提供商名称
        内部逻辑：如果provider_name为空，根据provider_id从常量中查找名称
        参数：
            v: 当前provider_name值
            info: Pydantic验证上下文
        返回值：提供商名称
        """
        if v:
            return v
        provider_id = info.data.get('provider_id')
        if provider_id:
            from app.core.llm_constants import PROVIDER_ID_MAP
            return PROVIDER_ID_MAP.get(provider_id, provider_id)
        return v

    @field_validator('model_id', mode='before')
    @classmethod
    def fill_embedding_model_id(cls, v: str, info) -> str:
        """
        函数级注释：自动补全模型ID
        内部逻辑：如果model_id为空，使用model_name作为值
        参数：
            v: 当前model_id值
            info: Pydantic验证上下文
        返回值：模型ID
        """
        if v:
            return v
        return info.data.get('model_name', v)


class EmbeddingConfigCreate(EmbeddingConfigBase):
    """
    类级注释：创建Embedding配置请求模型
    属性：继承EmbeddingConfigBase，额外包含id字段（可选）
    """
    id: Optional[str] = Field(None, description="配置ID，新建时为空")


class EmbeddingConfigUpdate(BaseModel):
    """
    类级注释：更新Embedding配置请求模型
    属性：所有字段都是可选的，支持部分更新
    """
    provider_id: Optional[str] = Field(None, description="提供商ID")
    provider_name: Optional[str] = Field(None, description="提供商名称")
    endpoint: Optional[str] = Field(None, description="API端点地址")
    api_key: Optional[str] = Field(None, description="API密钥")
    model_id: Optional[str] = Field(None, description="模型ID")
    model_name: Optional[str] = Field(None, description="模型名称")
    device: Optional[str] = Field(None, description="运行设备")
    status: Optional[int] = Field(None, ge=0, le=1, description="状态")

    # 属性：Pydantic v2 配置，允许使用 model_ 前缀的字段
    model_config = ConfigDict(protected_namespaces=())


class EmbeddingConfigResponse(EmbeddingConfigBase):
    """
    类级注释：Embedding配置响应模型
    属性：继承EmbeddingConfigBase，额外包含id字段
    """
    id: str = Field(..., description="配置ID")

    # 属性：Pydantic v2 配置，继承父类配置并添加 from_attributes
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)


class EmbeddingConfigResponseSafe(BaseModel):
    """
    类级注释：Embedding配置响应模型（安全版本，不包含完整API Key）
    属性：api_key_masked 脱敏显示的密钥（格式如 sk-****1234）
    """
    provider_id: str = Field(..., min_length=1, description="提供商ID")
    provider_name: str = Field("", description="提供商名称")
    endpoint: str = Field("", description="API端点地址")
    api_key_masked: str = Field("", description="API密钥脱敏显示")
    model_id: str = Field("", description="模型ID")
    model_name: str = Field(..., min_length=1, description="模型名称")
    batch_size: int = Field(32, ge=1, description="批处理大小")
    device: str = Field("cpu", description="运行设备(cpu/cuda/auto)")
    status: int = Field(1, ge=0, le=1, description="状态(1启用/0禁用)")
    id: str = Field(..., description="配置ID")

    # 属性：Pydantic v2 配置，允许使用 model_ 前缀的字段
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)


class ProviderInfo(BaseModel):
    """
    类级注释：提供商信息模型
    属性：
        value: 提供商ID
        label: 提供商显示名称
        default_endpoint: 默认端点地址
        default_models: 默认模型列表
        type: 类型（text/embedding）
    """
    value: str = Field(..., description="提供商ID")
    label: str = Field(..., description="提供商显示名称")
    default_endpoint: str = Field(..., description="默认端点地址")
    default_models: list[str] = Field(default_factory=list, description="默认模型列表")
    type: str = Field(..., description="类型(text/embedding)")


class OllamaModelInfo(BaseModel):
    """
    类级注释：Ollama模型信息模型
    属性：
        name: 模型名称
        size: 模型大小（字节）
        modified_at: 修改时间
    """
    name: str = Field(..., description="模型名称")
    size: int = Field(..., description="模型大小")
    modified_at: Optional[str] = Field(None, description="修改时间")


class ProvidersResponse(BaseModel):
    """
    类级注释：提供商列表响应模型
    属性：
        llm_providers: LLM提供商列表
        embedding_providers: Embedding提供商列表
    """
    llm_providers: list[ProviderInfo] = Field(default_factory=list, description="LLM提供商列表")
    embedding_providers: list[ProviderInfo] = Field(default_factory=list, description="Embedding提供商列表")


class ModelConfigListResponse(BaseModel):
    """
    类级注释：模型配置列表响应模型
    属性：
        configs: 配置列表（status=1的配置为正在使用）
    """
    configs: list[ModelConfigResponse] = Field(default_factory=list, description="配置列表")


class OllamaModelsResponse(BaseModel):
    """
    类级注释：Ollama模型列表响应模型
    属性：
        models: 模型信息列表
    """
    models: list[OllamaModelInfo] = Field(default_factory=list, description="模型信息列表")


class ConnectionTestRequest(BaseModel):
    """
    类级注释：连接测试请求模型
    属性：
        provider_id: 提供商ID
        endpoint: API端点地址
        api_key: API密钥
        model_name: 模型名称（可选）
        config_id: 配置ID（可选，用于从数据库获取真实密钥）
    """
    provider_id: str = Field(..., min_length=1, description="提供商ID")
    endpoint: str = Field("", description="API端点地址")
    api_key: str = Field("", description="API密钥")
    model_name: str = Field("", description="模型名称（可选）")
    config_id: Optional[str] = Field(None, description="配置ID（可选，用于从数据库获取真实密钥）")


class ConnectionTestResponse(BaseModel):
    """
    类级注释：连接测试响应模型
    属性：
        success: 是否连接成功
        provider_id: 提供商ID
        latency_ms: 延迟（毫秒）
        message: 结果消息
        error: 错误详情（测试失败时）
        models: 获取到的模型列表（测试成功时）
    """
    success: bool = Field(..., description="是否连接成功")
    provider_id: str = Field(..., description="提供商ID")
    latency_ms: float = Field(..., description="延迟（毫秒）")
    message: str = Field(..., description="结果消息")
    error: Optional[str] = Field(None, description="错误详情")
    models: list[str] = Field(default_factory=list, description="获取到的模型列表")


class EmbeddingConnectionTestRequest(BaseModel):
    """
    类级注释：Embedding连接测试请求模型
    属性：
        provider_id: 提供商ID
        endpoint: API端点地址
        api_key: API密钥
        model_name: 模型名称
        device: 运行设备
        config_id: 配置ID（可选，用于从数据库获取真实密钥）
    """
    provider_id: str = Field(..., min_length=1, description="提供商ID")
    endpoint: str = Field("", description="API端点地址")
    api_key: str = Field("", description="API密钥")
    model_name: str = Field("", description="模型名称")
    device: str = Field("cpu", description="运行设备")
    config_id: Optional[str] = Field(None, description="配置ID（可选，用于从数据库获取真实密钥）")


class EmbeddingConnectionTestResponse(BaseModel):
    """
    类级注释：Embedding连接测试响应模型
    属性：
        success: 是否连接成功
        provider_id: 提供商ID
        latency_ms: 延迟（毫秒）
        message: 结果消息
        error: 错误详情（测试失败时）
        models: 获取到的模型列表（测试成功时）
    """
    success: bool = Field(..., description="是否连接成功")
    provider_id: str = Field(..., description="提供商ID")
    latency_ms: float = Field(..., description="延迟（毫秒）")
    message: str = Field(..., description="结果消息")
    error: Optional[str] = Field(None, description="错误详情")
    models: list[str] = Field(default_factory=list, description="获取到的模型列表")


class LocalModelsResponse(BaseModel):
    """
    类级注释：本地模型列表响应模型
    属性：
        models: 本地模型名称列表
        base_dir: 模型基础目录路径
    """
    models: list[str] = Field(default_factory=list, description="本地模型名称列表")
    base_dir: str = Field(..., description="模型基础目录路径")
