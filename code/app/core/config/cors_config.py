# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：CORS配置模块
内部逻辑：管理跨域资源共享配置
设计模式：建造者模式
设计原则：单一职责原则
"""

from typing import List, Union
from pydantic import field_validator, AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def assemble_cors_origins(v: Union[str, List[str]]) -> Union[List[str], str]:
    """
    函数级注释：处理跨域来源字符串，将其转换为列表
    参数：v - 原始输入数据
    返回值：处理后的列表或原始值
    """
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, (list, str)):
        return v
    raise ValueError(v)


class CORSConfig(BaseSettings):
    """
    类级注释：CORS配置类

    配置优先级（从高到低）：
        1. 环境变量：系统环境变量或 docker run -e 注入
        2. Dockerfile ENV：Dockerfile 中定义的 ENV 指令
        3. 配置文件：.env.prod（生产）或 .env（开发）
        4. 代码默认值：本类属性定义的默认值

    职责：
        1. 管理允许的跨域来源
        2. 提供CORS验证逻辑
    设计模式：建造者模式
    设计原则：单一职责原则
    """

    # 内部逻辑：配置Settings，从环境变量读取配置
    model_config = SettingsConfigDict(case_sensitive=True, extra="ignore")

    # 允许的跨域来源列表（使用Field定义，使其成为正式字段）
    origins_input: Union[str, List[str]] = Field(default=[], alias="_origins")

    @property
    def origins(self) -> List[AnyHttpUrl]:
        """
        属性级注释：获取跨域来源列表
        返回值：跨域来源列表
        内部逻辑：将字符串或列表输入转换为AnyHttpUrl对象列表
        """
        # 内部变量：处理origins_input，确保它是列表格式
        if isinstance(self.origins_input, str):
            processed = assemble_cors_origins(self.origins_input)
        else:
            processed = self.origins_input
        # 返回 AnyHttpUrl 对象列表
        return [AnyHttpUrl(url) for url in (processed if isinstance(processed, list) else [processed])]

    @field_validator("origins_input", mode="before")
    @classmethod
    def validate_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """
        函数级注释：验证并处理跨域来源
        参数：v - 原始输入数据（字符串或列表）
        返回值：处理后的URL列表
        内部逻辑：支持JSON格式字符串和逗号分隔字符串
        """
        if isinstance(v, str):
            if v.startswith("["):
                # JSON格式
                import json
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # 逗号分隔格式
            return [i.strip() for i in v.split(",") if i.strip()]
        return v if isinstance(v, list) else [v]


# 内部变量：导出所有公共接口
__all__ = ['CORSConfig', 'assemble_cors_origins']
