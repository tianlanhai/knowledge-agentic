# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：模型配置数据模型
内部逻辑：定义LLM和Embedding模型配置的数据库表结构
参考项目：easy-dataset-file
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Index, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from app.utils.timezone_helper import get_local_time

# 内部变量：导入共享的Base类
from app.models.models import Base


class ModelConfig(Base):
    """
    类级注释：LLM模型配置表，存储不同提供商的模型配置信息
    属性：
        id: 主键，配置唯一标识（使用nanoid生成）
        provider_id: 提供商ID（ollama、zhipuai、openai等）
        provider_name: 提供商名称
        endpoint: API端点地址
        api_key: API密钥（加密存储）
        model_id: 模型ID
        model_name: 模型名称
        type: 模型类型（text、embedding）
        temperature: 温度参数（0-2）
        max_tokens: 最大生成token数
        top_p: nucleus采样参数
        top_k: top-k采样参数
        status: 状态（1启用且正在使用，同一时间只能有一个为1；0禁用）
        created_at: 创建时间
        updated_at: 更新时间
    索引：
        idx_model_config_provider: provider_id索引
        idx_model_config_status: status索引
    """
    __tablename__ = "model_config"

    # 属性：主键（使用字符串ID，兼容nanoid）
    id = Column(String(50), primary_key=True, comment="配置ID")

    # 属性：提供商信息
    provider_id = Column(String(50), nullable=False, index=True, comment="提供商ID")
    provider_name = Column(String(100), nullable=False, comment="提供商名称")

    # 属性：API配置
    endpoint = Column(String(500), nullable=False, comment="API端点地址")
    api_key = Column(String(500), nullable=True, comment="API密钥")

    # 属性：模型信息
    model_id = Column(String(100), nullable=False, comment="模型ID")
    model_name = Column(String(100), nullable=False, comment="模型名称")
    type = Column(String(20), nullable=False, default="text", comment="模型类型(text/embedding)")

    # 属性：模型参数
    temperature = Column(Float, nullable=False, default=0.7, comment="温度参数")
    max_tokens = Column(Integer, nullable=False, default=8192, comment="最大token数")
    top_p = Column(Float, nullable=False, default=0.9, comment="nucleus采样参数")
    top_k = Column(Integer, nullable=False, default=0, comment="top-k采样参数")

    # 属性：设备配置（本地模型如Ollama使用）
    device = Column(String(20), nullable=False, default="auto", comment="运行设备(cpu/cuda/auto)")

    # 属性：状态控制（status=1表示启用且正在使用，同时只能有一个；status=0表示禁用）
    status = Column(Integer, nullable=False, default=0, index=True, comment="状态(1启用使用中/0禁用)")

    # 属性：时间戳（本地时间）
    created_at = Column(DateTime, default=get_local_time, comment="创建时间(本地时间)")
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time, comment="更新时间(本地时间)")

    # 索引定义
    __table_args__ = (
        Index("idx_model_config_provider", "provider_id"),
        Index("idx_model_config_status", "status"),
        # 唯一约束：防止同一提供商的同一模型被重复插入
        UniqueConstraint("provider_id", "model_id", "type", name="uq_model_config_provider_model_type"),
    )

    def __repr__(self):
        """函数级注释：模型字符串表示"""
        return f"<ModelConfig(id={self.id}, provider={self.provider_id}, model={self.model_name})>"


class EmbeddingConfig(Base):
    """
    类级注释：Embedding模型配置表，存储向量化模型的配置信息
    属性：
        id: 主键，配置唯一标识
        provider_id: 提供商ID（ollama、zhipuai、local等）
        provider_name: 提供商名称
        endpoint: API端点地址
        api_key: API密钥（云端提供商需要）
        model_id: 模型ID
        model_name: 模型名称
        device: 运行设备（cpu、cuda、auto）
        status: 状态（1启用且正在使用，同一时间只能有一个为1；0禁用）
        created_at: 创建时间
        updated_at: 更新时间
    索引：
        idx_embedding_config_provider: provider_id索引
    """
    __tablename__ = "embedding_config"

    # 属性：主键
    id = Column(String(50), primary_key=True, comment="配置ID")

    # 属性：提供商信息
    provider_id = Column(String(50), nullable=False, index=True, comment="提供商ID")
    provider_name = Column(String(100), nullable=False, comment="提供商名称")

    # 属性：API配置
    endpoint = Column(String(500), nullable=True, comment="API端点地址")
    api_key = Column(String(500), nullable=True, comment="API密钥")

    # 属性：模型信息
    model_id = Column(String(100), nullable=False, comment="模型ID")
    model_name = Column(String(100), nullable=False, comment="模型名称")

    # 属性：设备配置（本地模型使用）
    device = Column(String(20), nullable=False, default="cpu", comment="运行设备(cpu/cuda/auto)")

    # 属性：状态控制（status=1表示启用且正在使用，同时只能有一个；status=0表示禁用）
    status = Column(Integer, nullable=False, default=0, comment="状态(1启用使用中/0禁用)")

    # 属性：时间戳（本地时间）
    created_at = Column(DateTime, default=get_local_time, comment="创建时间(本地时间)")
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time, comment="更新时间(本地时间)")

    # 索引定义
    __table_args__ = (
        Index("idx_embedding_config_provider", "provider_id"),
        # 唯一约束：防止同一提供商的同一模型被重复插入
        UniqueConstraint("provider_id", "model_id", name="uq_embedding_config_provider_model"),
    )

    def __repr__(self):
        """函数级注释：模型字符串表示"""
        return f"<EmbeddingConfig(id={self.id}, provider={self.provider_id}, model={self.model_name})>"
