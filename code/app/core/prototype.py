# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：原型模式模块
内部逻辑：通过克隆创建对象，避免重复创建开销
设计模式：原型模式（Prototype Pattern）
设计原则：SOLID - DRY原则
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, TypeVar, Generic, Type, Optional
from copy import deepcopy
from loguru import logger

T = TypeVar('T')


class Prototype(ABC):
    """
    类级注释：原型抽象基类
    设计模式：原型模式（Prototype Pattern）- 原型接口
    职责：定义克隆接口

    设计优势：
        - 通过克隆创建对象，避免初始化开销
        - 动态获取对象状态
        - 简化对象创建
    """

    @abstractmethod
    def clone(self) -> "Prototype":
        """
        函数级注释：创建对象的副本
        内部逻辑：返回当前对象的深拷贝
        返回值：克隆的对象
        """
        pass

    @abstractmethod
    def shallow_clone(self) -> "Prototype":
        """
        函数级注释：创建对象的浅拷贝
        内部逻辑：返回当前对象的浅拷贝
        返回值：克隆的对象
        """
        pass


@dataclass
class DocumentPrototype(Prototype):
    """
    类级注释：文档原型类
    设计模式：原型模式（Prototype Pattern）- 具体原型
    职责：提供文档的克隆功能

    设计优势：
        - 快速创建相似文档
        - 保留模板结构
        - 修改不影响原对象
    """

    id: Optional[int] = None
    title: str = ""
    content: str = ""
    file_name: str = ""
    file_type: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def clone(self) -> "DocumentPrototype":
        """
        函数级注释：创建文档的深拷贝
        内部逻辑：使用deepcopy复制所有字段
        返回值：克隆的文档对象
        """
        cloned = DocumentPrototype(
            id=None,  # 内部逻辑：克隆时不复制ID
            title=self.title,
            content=deepcopy(self.content),
            file_name=self.file_name,
            file_type=self.file_type,
            metadata=deepcopy(self.metadata)
        )
        logger.debug(f"克隆文档: {self.title}")
        return cloned

    def shallow_clone(self) -> "DocumentPrototype":
        """
        函数级注释：创建文档的浅拷贝
        内部逻辑：复制字段，metadata共享引用
        返回值：浅拷贝的文档对象
        """
        cloned = DocumentPrototype(
            id=None,
            title=self.title,
            content=self.content,
            file_name=self.file_name,
            file_type=self.file_type,
            metadata=self.metadata  # 内部逻辑：共享引用
        )
        return cloned

    def with_changes(self, **kwargs) -> "DocumentPrototype":
        """
        函数级注释：克隆并修改指定字段
        内部逻辑：先克隆，再修改字段（链式调用）
        参数：
            **kwargs: 要修改的字段和值
        返回值：修改后的克隆对象
        """
        cloned = self.clone()
        for key, value in kwargs.items():
            if hasattr(cloned, key):
                setattr(cloned, key, value)
        return cloned


@dataclass
class ChatConfigPrototype(Prototype):
    """
    类级注释：聊天配置原型类
    设计模式：原型模式（Prototype Pattern）- 具体原型
    职责：提供聊天配置的克隆功能

    使用场景：
        - 保存用户配置模板
        - 快速切换配置
        - 配置版本管理
    """

    provider: str = "ollama"
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 2000
    streaming: bool = True
    system_prompt: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def clone(self) -> "ChatConfigPrototype":
        """
        函数级注释：创建配置的深拷贝
        """
        return ChatConfigPrototype(
            provider=self.provider,
            model=deepcopy(self.model),
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            streaming=self.streaming,
            system_prompt=deepcopy(self.system_prompt),
            metadata=deepcopy(self.metadata)
        )

    def shallow_clone(self) -> "ChatConfigPrototype":
        """
        函数级注释：创建配置的浅拷贝
        """
        return ChatConfigPrototype(
            provider=self.provider,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            streaming=self.streaming,
            system_prompt=self.system_prompt,
            metadata=self.metadata
        )

    def with_temperature(self, temperature: float) -> "ChatConfigPrototype":
        """修改温度参数并返回新配置"""
        cloned = self.clone()
        cloned.temperature = temperature
        return cloned

    def with_model(self, model: str) -> "ChatConfigPrototype":
        """修改模型并返回新配置"""
        cloned = self.clone()
        cloned.model = model
        return cloned


class PrototypeRegistry:
    """
    类级注释：原型注册表
    设计模式：注册表模式 + 原型模式
    职责：管理和提供原型对象

    设计优势：
        - 集中管理原型
        - 通过名称获取原型
        - 支持动态注册
    """

    # 内部类变量：原型注册表
    _prototypes: Dict[str, Prototype] = {}

    @classmethod
    def register(cls, name: str, prototype: Prototype) -> None:
        """
        函数级注释：注册原型
        参数：
            name: 原型名称
            prototype: 原型对象
        """
        cls._prototypes[name] = prototype
        logger.info(f"注册原型: {name}")

    @classmethod
    def unregister(cls, name: str) -> None:
        """
        函数级注释：注销原型
        参数：
            name: 原型名称
        """
        if name in cls._prototypes:
            del cls._prototypes[name]
            logger.info(f"注销原型: {name}")

    @classmethod
    def get(cls, name: str) -> Optional[Prototype]:
        """
        函数级注释：获取原型克隆
        内部逻辑：查找原型 -> 调用clone方法 -> 返回克隆
        参数：
            name: 原型名称
        返回值：克隆的原型对象或None
        """
        prototype = cls._prototypes.get(name)
        if prototype:
            return prototype.clone()
        return None

    @classmethod
    def get_original(cls, name: str) -> Optional[Prototype]:
        """
        函数级注释：获取原始原型（不克隆）
        参数：
            name: 原型名称
        返回值：原始原型对象或None
        """
        return cls._prototypes.get(name)

    @classmethod
    def list_prototypes(cls) -> list[str]:
        """
        函数级注释：列出所有已注册的原型名称
        返回值：原型名称列表
        """
        return list(cls._prototypes.keys())

    @classmethod
    def clear(cls) -> None:
        """
        函数级注释：清除所有注册的原型
        """
        cls._prototypes.clear()


class PrototypeBuilder(Generic[T]):
    """
    类级注释：原型构建器
    设计模式：建造者模式 + 原型模式
    职责：通过链式调用构建原型对象

    设计优势：
        - 流式API
        - 支持链式调用
        - 灵活构建
    """

    def __init__(self, prototype_class: Type[T]):
        """
        函数级注释：初始化构建器
        参数：
            prototype_class: 原型类
        """
        self._prototype_class = prototype_class
        self._params: Dict[str, Any] = {}

    def set_param(self, key: str, value: Any) -> "PrototypeBuilder[T]":
        """
        函数级注释：设置参数
        参数：
            key: 参数名
            value: 参数值
        返回值：构建器自身（支持链式调用）
        """
        self._params[key] = value
        return self

    def set_params(self, **kwargs) -> "PrototypeBuilder[T]":
        """
        函数级注释：批量设置参数
        参数：
            **kwargs: 参数字典
        返回值：构建器自身
        """
        self._params.update(kwargs)
        return self

    def build(self) -> T:
        """
        函数级注释：构建原型对象
        返回值：原型对象
        """
        return self._prototype_class(**self._params)

    def build_and_register(self, name: str) -> T:
        """
        函数级注释：构建并注册原型
        参数：
            name: 注册名称
        返回值：原型对象
        """
        prototype = self.build()
        PrototypeRegistry.register(name, prototype)
        return prototype


# 内部逻辑：预注册常用原型
def _init_default_prototypes():
    """初始化默认原型"""
    # 内部逻辑：注册默认文档模板
    default_doc = DocumentPrototype(
        title="新文档",
        content="请输入内容...",
        file_type="txt",
        metadata={"template": True}
    )
    PrototypeRegistry.register("default_document", default_doc)

    # 内部逻辑：注册默认聊天配置
    default_chat = ChatConfigPrototype(
        provider="ollama",
        model="llama2",
        temperature=0.7,
        streaming=True
    )
    PrototypeRegistry.register("default_chat_config", default_chat)


# 内部逻辑：模块导入时初始化默认原型
_init_default_prototypes()
