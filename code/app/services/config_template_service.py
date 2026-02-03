# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：配置模板服务模块
内部逻辑：集成原型模式实现配置模板管理
设计模式：原型模式（Prototype Pattern）+ 工厂模式
设计原则：单一职责原则、DRY原则

使用场景：
    - 配置模板保存和复用
    - 快速切换配置
    - 配置版本管理
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger
import json

from app.core.prototype import (
    Prototype,
    PrototypeRegistry,
    ChatConfigPrototype,
    DocumentPrototype,
    PrototypeBuilder
)


@dataclass
class ConfigTemplate:
    """
    类级注释：配置模板数据类
    职责：封装配置模板的完整信息
    """
    name: str  # 模板名称
    category: str  # 模板分类（chat/document/system）
    description: str = ""  # 模板描述
    is_default: bool = False  # 是否为默认模板
    is_system: bool = False  # 是否为系统模板
    created_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None  # 创建者
    tags: List[str] = field(default_factory=list)  # 标签

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "is_default": self.is_default,
            "is_system": self.is_system,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "tags": self.tags
        }


@dataclass
class ConfigInstance:
    """
    类级注释：配置实例数据类
    职责：封装从模板创建的配置实例
    """
    template_name: str  # 来源模板名称
    config: Dict[str, Any]  # 配置数据
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "template_name": self.template_name,
            "config": self.config,
            "created_at": self.created_at.isoformat()
        }


class ConfigTemplateService:
    """
    类级注释：配置模板服务
    设计模式：原型模式 + 门面模式
    职责：
        1. 管理配置模板
        2. 基于原型创建配置实例
        3. 配置版本和切换管理

    使用场景：
        - 保存用户配置偏好
        - 快速切换不同配置
        - 配置模板分享
    """

    def __init__(self):
        """初始化配置模板服务"""
        # 内部变量：模板元数据映射
        self._template_metadata: Dict[str, ConfigTemplate] = {}
        # 内部变量：用户模板列表
        self._user_templates: Dict[str, List[str]] = {}  # user_id -> [template_names]

        # 内部逻辑：初始化默认模板
        self._init_default_templates()

        logger.info("配置模板服务初始化完成")

    def _init_default_templates(self) -> None:
        """
        函数级注释：初始化默认配置模板
        内部逻辑：创建系统默认模板并注册
        @private
        """
        # 内部逻辑：默认聊天配置 - 快速响应
        quick_chat = ChatConfigPrototype(
            provider="ollama",
            model="deepseek-r1:8b",
            temperature=0.3,
            max_tokens=1000,
            streaming=True,
            system_prompt="你是一个简洁的AI助手，请用简短的语言回答问题。"
        )
        PrototypeRegistry.register("quick_chat", quick_chat)
        self._template_metadata["quick_chat"] = ConfigTemplate(
            name="quick_chat",
            category="chat",
            description="快速响应模式 - 适合简单问答",
            is_default=True,
            is_system=True,
            tags=["快速", "简洁"]
        )

        # 内部逻辑：默认聊天配置 - 创意模式
        creative_chat = ChatConfigPrototype(
            provider="ollama",
            model="deepseek-r1:8b",
            temperature=0.9,
            max_tokens=2000,
            streaming=True,
            system_prompt="你是一个富有创造力的AI助手，请提供多样化、富有想象力的回答。"
        )
        PrototypeRegistry.register("creative_chat", creative_chat)
        self._template_metadata["creative_chat"] = ConfigTemplate(
            name="creative_chat",
            category="chat",
            description="创意模式 - 适合头脑风暴和创意写作",
            is_system=True,
            tags=["创意", "多样化"]
        )

        # 内部逻辑：默认聊天配置 - 代码助手
        code_chat = ChatConfigPrototype(
            provider="ollama",
            model="deepseek-r1:8b",
            temperature=0.2,
            max_tokens=2000,
            streaming=True,
            system_prompt="你是一个专业的编程助手，请提供准确、简洁的代码建议和解决方案。"
        )
        PrototypeRegistry.register("code_chat", code_chat)
        self._template_metadata["code_chat"] = ConfigTemplate(
            name="code_chat",
            category="chat",
            description="代码助手模式 - 适合编程相关问题",
            is_system=True,
            tags=["代码", "技术"]
        )

        # 内部逻辑：默认聊天配置 - 精确模式
        precise_chat = ChatConfigPrototype(
            provider="zhipuai",
            model="glm-4.5-air",
            temperature=0.1,
            max_tokens=4000,
            streaming=True,
            system_prompt="你是一个严谨的AI助手，请提供准确、详细、有据可查的回答。"
        )
        PrototypeRegistry.register("precise_chat", precise_chat)
        self._template_metadata["precise_chat"] = ConfigTemplate(
            name="precise_chat",
            category="chat",
            description="精确模式 - 适合需要准确性的复杂问题",
            is_system=True,
            tags=["精确", "详细"]
        )

        logger.info(f"初始化 {len(self._template_metadata)} 个默认配置模板")

    def create_chat_template(
        self,
        name: str,
        provider: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        streaming: bool = True,
        system_prompt: str = "",
        description: str = "",
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        函数级注释：创建聊天配置模板
        内部逻辑：创建原型 -> 注册到注册表 -> 保存元数据
        参数：
            name - 模板名称
            provider - AI提供商
            model - 模型名称
            temperature - 温度参数
            max_tokens - 最大token数
            streaming - 是否流式
            system_prompt - 系统提示词
            description - 模板描述
            user_id - 创建用户ID
            tags - 标签列表
        返回值：创建结果
        """
        # 内部逻辑：检查名称是否存在
        if PrototypeRegistry.get_original(name):
            return {
                "success": False,
                "message": f"模板名称 '{name}' 已存在"
            }

        # 内部逻辑：创建原型
        prototype = ChatConfigPrototype(
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=streaming,
            system_prompt=system_prompt
        )

        # 内部逻辑：注册原型
        PrototypeRegistry.register(name, prototype)

        # 内部逻辑：保存元数据
        metadata = ConfigTemplate(
            name=name,
            category="chat",
            description=description,
            is_default=False,
            is_system=False,
            created_by=user_id,
            tags=tags or []
        )
        self._template_metadata[name] = metadata

        # 内部逻辑：记录用户模板
        if user_id:
            if user_id not in self._user_templates:
                self._user_templates[user_id] = []
            self._user_templates[user_id].append(name)

        logger.info(f"创建聊天配置模板: {name}")
        return {
            "success": True,
            "message": f"模板 '{name}' 创建成功",
            "template": metadata.to_dict()
        }

    def clone_template(
        self,
        source_name: str,
        new_name: str,
        modifications: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        函数级注释：克隆模板
        内部逻辑：获取原型 -> 克隆 -> 应用修改 -> 注册新模板
        参数：
            source_name - 源模板名称
            new_name - 新模板名称
            modifications - 要修改的字段
            user_id - 创建用户ID
        返回值：克隆结果
        """
        # 内部逻辑：获取源原型
        source = PrototypeRegistry.get_original(source_name)
        if not source:
            return {
                "success": False,
                "message": f"源模板 '{source_name}' 不存在"
            }

        # 内部逻辑：克隆原型
        cloned = source.clone()

        # 内部逻辑：应用修改
        if modifications:
            for key, value in modifications.items():
                if hasattr(cloned, key):
                    setattr(cloned, key, value)

        # 内部逻辑：注册新原型
        PrototypeRegistry.register(new_name, cloned)

        # 内部逻辑：复制元数据
        source_metadata = self._template_metadata.get(source_name)
        metadata = ConfigTemplate(
            name=new_name,
            category=source_metadata.category if source_metadata else "chat",
            description=f"克隆自 {source_name}",
            is_default=False,
            is_system=False,
            created_by=user_id,
            tags=source_metadata.tags.copy() if source_metadata else []
        )
        self._template_metadata[new_name] = metadata

        # 内部逻辑：记录用户模板
        if user_id:
            if user_id not in self._user_templates:
                self._user_templates[user_id] = []
            self._user_templates[user_id].append(new_name)

        logger.info(f"克隆模板: {source_name} -> {new_name}")
        return {
            "success": True,
            "message": f"模板克隆成功",
            "template": metadata.to_dict()
        }

    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """
        函数级注释：获取模板配置
        参数：
            name - 模板名称
        返回值：模板配置字典或None
        """
        prototype = PrototypeRegistry.get_original(name)
        if not prototype:
            return None

        metadata = self._template_metadata.get(name)
        result = {
            "name": name,
            "metadata": metadata.to_dict() if metadata else {}
        }

        # 内部逻辑：根据类型添加配置
        if isinstance(prototype, ChatConfigPrototype):
            result.update({
                "category": "chat",
                "config": {
                    "provider": prototype.provider,
                    "model": prototype.model,
                    "temperature": prototype.temperature,
                    "max_tokens": prototype.max_tokens,
                    "streaming": prototype.streaming,
                    "system_prompt": prototype.system_prompt
                }
            })

        return result

    def create_instance(
        self,
        template_name: str,
        modifications: Optional[Dict[str, Any]] = None
    ) -> Optional[ConfigInstance]:
        """
        函数级注释：从模板创建配置实例
        内部逻辑：获取原型 -> 克隆 -> 应用修改 -> 返回实例
        参数：
            template_name - 模板名称
            modifications - 实例修改
        返回值：配置实例或None
        """
        prototype = PrototypeRegistry.get(template_name)
        if not prototype:
            logger.error(f"模板不存在: {template_name}")
            return None

        # 内部逻辑：应用实例修改
        if modifications:
            if isinstance(prototype, ChatConfigPrototype):
                for key, value in modifications.items():
                    if hasattr(prototype, key):
                        setattr(prototype, key, value)

        # 内部逻辑：转换为字典
        config_dict = {}
        if isinstance(prototype, ChatConfigPrototype):
            config_dict = {
                "provider": prototype.provider,
                "model": prototype.model,
                "temperature": prototype.temperature,
                "max_tokens": prototype.max_tokens,
                "streaming": prototype.streaming,
                "system_prompt": prototype.system_prompt
            }

        instance = ConfigInstance(
            template_name=template_name,
            config=config_dict
        )

        logger.debug(f"从模板 {template_name} 创建配置实例")
        return instance

    def list_templates(
        self,
        category: Optional[str] = None,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        函数级注释：列出模板
        参数：
            category - 分类过滤
            user_id - 用户过滤
            tags - 标签过滤
        返回值：模板列表
        """
        templates = []

        for name, metadata in self._template_metadata.items():
            # 内部逻辑：分类过滤
            if category and metadata.category != category:
                continue

            # 内部逻辑：用户过滤（系统模板+用户模板）
            if user_id and not metadata.is_system:
                if user_id not in self._user_templates or name not in self._user_templates[user_id]:
                    continue

            # 内部逻辑：标签过滤
            if tags and not any(tag in metadata.tags for tag in tags):
                continue

            templates.append(metadata.to_dict())

        return templates

    def update_template(
        self,
        name: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        函数级注释：更新模板
        参数：
            name - 模板名称
            updates - 更新内容
        返回值：更新结果
        """
        prototype = PrototypeRegistry.get_original(name)
        if not prototype:
            return {
                "success": False,
                "message": f"模板 '{name}' 不存在"
            }

        metadata = self._template_metadata.get(name)
        if metadata and metadata.is_system:
            return {
                "success": False,
                "message": "不能修改系统模板"
            }

        # 内部逻辑：更新原型
        for key, value in updates.items():
            if key in ["description", "tags"]:
                # 内部逻辑：更新元数据
                if metadata:
                    setattr(metadata, key, value)
            elif hasattr(prototype, key):
                setattr(prototype, key, value)

        logger.info(f"更新模板: {name}")
        return {
            "success": True,
            "message": f"模板 '{name}' 更新成功"
        }

    def delete_template(self, name: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        函数级注释：删除模板
        参数：
            name - 模板名称
            user_id - 用户ID（验证权限）
        返回值：删除结果
        """
        metadata = self._template_metadata.get(name)
        if not metadata:
            return {
                "success": False,
                "message": f"模板 '{name}' 不存在"
            }

        if metadata.is_system:
            return {
                "success": False,
                "message": "不能删除系统模板"
            }

        # 内部逻辑：验证权限
        if user_id and metadata.created_by != user_id:
            return {
                "success": False,
                "message": "无权删除此模板"
            }

        # 内部逻辑：删除原型和元数据
        PrototypeRegistry.unregister(name)
        del self._template_metadata[name]

        # 内部逻辑：从用户列表中移除
        if user_id and user_id in self._user_templates:
            self._user_templates[user_id] = [
                t for t in self._user_templates[user_id] if t != name
            ]

        logger.info(f"删除模板: {name}")
        return {
            "success": True,
            "message": f"模板 '{name}' 删除成功"
        }

    def set_default_template(self, name: str, category: str = "chat") -> Dict[str, Any]:
        """
        函数级注释：设置默认模板
        参数：
            name - 模板名称
            category - 分类
        返回值：操作结果
        """
        metadata = self._template_metadata.get(name)
        if not metadata:
            return {
                "success": False,
                "message": f"模板 '{name}' 不存在"
            }

        # 内部逻辑：清除同分类的其他默认模板
        for meta in self._template_metadata.values():
            if meta.category == category:
                meta.is_default = False

        # 内部逻辑：设置新默认模板
        metadata.is_default = True

        logger.info(f"设置默认模板: {name} (分类: {category})")
        return {
            "success": True,
            "message": f"已将 '{name}' 设为默认{category}模板"
        }

    def get_default_template(self, category: str = "chat") -> Optional[str]:
        """
        函数级注释：获取默认模板名称
        参数：
            category - 分类
        返回值：默认模板名称或None
        """
        for name, metadata in self._template_metadata.items():
            if metadata.category == category and metadata.is_default:
                return name
        return None

    def import_templates(
        self,
        templates_data: List[Dict[str, Any]],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        函数级注释：批量导入模板
        参数：
            templates_data - 模板数据列表
            user_id - 用户ID
        返回值：导入结果
        """
        imported = 0
        failed = 0

        for template_data in templates_data:
            try:
                name = template_data.get("name")
                category = template_data.get("category", "chat")

                if category == "chat":
                    result = self.create_chat_template(
                        name=name,
                        provider=template_data.get("provider", "ollama"),
                        model=template_data.get("model", ""),
                        temperature=template_data.get("temperature", 0.7),
                        max_tokens=template_data.get("max_tokens", 2000),
                        streaming=template_data.get("streaming", True),
                        system_prompt=template_data.get("system_prompt", ""),
                        description=template_data.get("description", ""),
                        user_id=user_id,
                        tags=template_data.get("tags", [])
                    )
                    if result.get("success"):
                        imported += 1
                    else:
                        failed += 1

            except Exception as e:
                logger.error(f"导入模板失败: {e}")
                failed += 1

        return {
            "success": True,
            "imported": imported,
            "failed": failed,
            "message": f"导入完成：成功 {imported} 个，失败 {failed} 个"
        }

    def export_templates(
        self,
        names: Optional[List[str]] = None,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        函数级注释：导出模板
        参数：
            names - 模板名称列表（None表示全部）
            user_id - 用户ID
        返回值：模板数据列表
        """
        if names:
            templates_to_export = [n for n in names if n in self._template_metadata]
        else:
            templates_to_export = list(self._template_metadata.keys())

        result = []
        for name in templates_to_export:
            template_info = self.get_template(name)
            if template_info:
                result.append(template_info)

        return result


# 内部变量：导出公共接口
__all__ = [
    'ConfigTemplateService',
    'ConfigTemplate',
    'ConfigInstance',
]
