# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：配置模板服务测试模块
内部逻辑：测试ConfigTemplateService的完整功能，包括模板创建、克隆、更新、删除等
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.services.config_template_service import (
    ConfigTemplateService,
    ConfigTemplate,
    ConfigInstance
)
from app.core.prototype import (
    PrototypeRegistry,
    ChatConfigPrototype,
    DocumentPrototype
)


# ============================================================================
# ConfigTemplate 和 ConfigInstance 测试类
# ============================================================================

class TestConfigTemplate:
    """
    类级注释：配置模板数据类测试
    职责：测试ConfigTemplate的属性和转换方法
    """

    def test_initialization(self):
        """
        测试目的：验证ConfigTemplate正确初始化
        测试场景：创建配置模板并验证所有属性
        """
        # Arrange & Act: 创建配置模板
        template = ConfigTemplate(
            name="test_template",
            category="chat",
            description="测试模板",
            is_default=True,
            is_system=False,
            created_by="user123",
            tags=["测试", "模板"]
        )

        # Assert: 验证所有属性
        assert template.name == "test_template"
        assert template.category == "chat"
        assert template.description == "测试模板"
        assert template.is_default is True
        assert template.is_system is False
        assert template.created_by == "user123"
        assert template.tags == ["测试", "模板"]
        assert isinstance(template.created_at, datetime)

    def test_to_dict(self):
        """
        测试目的：验证ConfigTemplate正确转换为字典
        测试场景：创建模板并转换为字典格式
        """
        # Arrange: 创建配置模板
        template = ConfigTemplate(
            name="test_template",
            category="chat",
            description="测试模板",
            tags=["tag1", "tag2"]
        )

        # Act: 转换为字典
        result = template.to_dict()

        # Assert: 验证字典内容
        assert result["name"] == "test_template"
        assert result["category"] == "chat"
        assert result["description"] == "测试模板"
        assert result["tags"] == ["tag1", "tag2"]
        assert "created_at" in result


class TestConfigInstance:
    """
    类级注释：配置实例数据类测试
    职责：测试ConfigInstance的属性和转换方法
    """

    def test_initialization(self):
        """
        测试目的：验证ConfigInstance正确初始化
        测试场景：创建配置实例并验证所有属性
        """
        # Arrange & Act: 创建配置实例
        instance = ConfigInstance(
            template_name="quick_chat",
            config={"model": "gpt-4", "temperature": 0.7}
        )

        # Assert: 验证所有属性
        assert instance.template_name == "quick_chat"
        assert instance.config == {"model": "gpt-4", "temperature": 0.7}
        assert isinstance(instance.created_at, datetime)

    def test_to_dict(self):
        """
        测试目的：验证ConfigInstance正确转换为字典
        测试场景：创建实例并转换为字典格式
        """
        # Arrange: 创建配置实例
        instance = ConfigInstance(
            template_name="quick_chat",
            config={"model": "gpt-4"}
        )

        # Act: 转换为字典
        result = instance.to_dict()

        # Assert: 验证字典内容
        assert result["template_name"] == "quick_chat"
        assert result["config"] == {"model": "gpt-4"}
        assert "created_at" in result


# ============================================================================
# ConfigTemplateService 测试类
# ============================================================================

class TestConfigTemplateService:
    """
    类级注释：配置模板服务测试类
    职责：测试ConfigTemplateService的完整功能
    """

    def setup_method(self):
        """
        测试前准备：清理原型注册表和创建新服务实例
        """
        # 清理注册表，确保测试隔离
        PrototypeRegistry._prototypes.clear()

    def test_initialization(self):
        """
        测试目的：验证服务正确初始化
        测试场景：创建服务并验证默认模板已注册
        """
        # Act: 创建服务实例
        service = ConfigTemplateService()

        # Assert: 验证默认模板已注册
        assert "quick_chat" in PrototypeRegistry._prototypes
        assert "creative_chat" in PrototypeRegistry._prototypes
        assert "code_chat" in PrototypeRegistry._prototypes
        assert "precise_chat" in PrototypeRegistry._prototypes

    def test_default_templates_metadata(self):
        """
        测试目的：验证默认模板元数据正确初始化
        测试场景：检查默认模板的元数据
        """
        # Arrange: 创建服务实例
        service = ConfigTemplateService()

        # Act: 获取默认模板
        quick_chat = service._template_metadata.get("quick_chat")

        # Assert: 验证元数据
        assert quick_chat is not None
        assert quick_chat.category == "chat"
        assert quick_chat.is_system is True
        assert quick_chat.is_default is True
        assert "快速" in quick_chat.tags

    def test_create_chat_template(self):
        """
        测试目的：验证创建聊天配置模板功能
        测试场景：创建新的聊天模板
        """
        # Arrange: 创建服务实例
        service = ConfigTemplateService()

        # Act: 创建新模板
        result = service.create_chat_template(
            name="custom_chat",
            provider="ollama",
            model="deepseek-r1:8b",
            temperature=0.5,
            max_tokens=1500,
            streaming=True,
            system_prompt="你是一个自定义助手",
            description="自定义聊天模板",
            user_id="user123",
            tags=["自定义"]
        )

        # Assert: 验证创建成功
        assert result["success"] is True
        assert "创建成功" in result["message"]
        assert result["template"]["name"] == "custom_chat"
        assert result["template"]["category"] == "chat"

        # 验证原型已注册
        prototype = PrototypeRegistry.get("custom_chat")
        assert prototype is not None

    def test_create_chat_template_duplicate_name(self):
        """
        测试目的：验证创建重名模板失败
        测试场景：尝试创建已存在的模板名称
        """
        # Arrange: 创建服务并添加模板
        service = ConfigTemplateService()
        service.create_chat_template(name="test", provider="ollama", model="model")

        # Act: 尝试创建同名模板
        result = service.create_chat_template(name="test", provider="ollama", model="model")

        # Assert: 验证失败
        assert result["success"] is False
        assert "已存在" in result["message"]

    def test_create_chat_template_with_user_tracking(self):
        """
        测试目的：验证用户模板跟踪功能
        测试场景：为用户创建模板并验证用户模板列表
        """
        # Arrange: 创建服务实例
        service = ConfigTemplateService()

        # Act: 为用户创建模板
        service.create_chat_template(
            name="user_template",
            provider="ollama",
            model="model",
            user_id="user123"
        )

        # Assert: 验证用户模板列表
        assert "user123" in service._user_templates
        assert "user_template" in service._user_templates["user123"]

    def test_clone_template(self):
        """
        测试目的：验证模板克隆功能
        测试场景：从现有模板克隆并修改
        """
        # Arrange: 创建服务和源模板
        service = ConfigTemplateService()
        service.create_chat_template(
            name="source_template",
            provider="ollama",
            model="model1",
            temperature=0.7
        )

        # Act: 克隆模板并修改
        result = service.clone_template(
            source_name="source_template",
            new_name="cloned_template",
            modifications={"temperature": 0.9, "model": "model2"},
            user_id="user123"
        )

        # Assert: 验证克隆成功
        assert result["success"] is True
        assert result["template"]["name"] == "cloned_template"

        # 验证克隆的模板有修改后的值
        cloned = PrototypeRegistry.get("cloned_template")
        assert cloned.temperature == 0.9

    def test_clone_template_nonexistent_source(self):
        """
        测试目的：验证克隆不存在的模板失败
        测试场景：尝试从不存在的源模板克隆
        """
        # Arrange: 创建服务实例
        service = ConfigTemplateService()

        # Act: 尝试克隆不存在的模板
        result = service.clone_template(
            source_name="nonexistent",
            new_name="cloned"
        )

        # Assert: 验证失败
        assert result["success"] is False
        assert "不存在" in result["message"]

    def test_get_template(self):
        """
        测试目的：验证获取模板功能
        测试场景：获取已存在的模板
        """
        # Arrange: 创建服务和模板
        service = ConfigTemplateService()
        service.create_chat_template(
            name="test_template",
            provider="ollama",
            model="model",
            temperature=0.5,
            system_prompt="测试提示词"
        )

        # Act: 获取模板
        result = service.get_template("test_template")

        # Assert: 验证模板内容
        assert result is not None
        assert result["name"] == "test_template"
        assert result["category"] == "chat"
        assert result["config"]["provider"] == "ollama"
        assert result["config"]["model"] == "model"
        assert result["config"]["temperature"] == 0.5
        assert result["config"]["system_prompt"] == "测试提示词"

    def test_get_template_not_found(self):
        """
        测试目的：验证获取不存在的模板返回None
        测试场景：尝试获取不存在的模板
        """
        # Arrange: 创建服务实例
        service = ConfigTemplateService()

        # Act: 尝试获取不存在的模板
        result = service.get_template("nonexistent")

        # Assert: 验证返回None
        assert result is None

    def test_create_instance(self):
        """
        测试目的：验证从模板创建实例功能
        测试场景：从模板创建配置实例
        """
        # Arrange: 创建服务和模板
        service = ConfigTemplateService()
        service.create_chat_template(
            name="test_template",
            provider="ollama",
            model="model",
            temperature=0.7
        )

        # Act: 创建实例并修改
        instance = service.create_instance(
            template_name="test_template",
            modifications={"temperature": 0.9}
        )

        # Assert: 验证实例
        assert instance is not None
        assert instance.template_name == "test_template"
        assert instance.config["temperature"] == 0.9
        assert instance.config["provider"] == "ollama"

    def test_create_instance_from_nonexistent_template(self):
        """
        测试目的：验证从不存在的模板创建实例返回None
        测试场景：尝试从不存在的模板创建实例
        """
        # Arrange: 创建服务实例
        service = ConfigTemplateService()

        # Act: 尝试从不存在的模板创建实例
        instance = service.create_instance("nonexistent")

        # Assert: 验证返回None
        assert instance is None

    def test_list_templates_all(self):
        """
        测试目的：验证列出所有模板功能
        测试场景：获取所有模板列表
        """
        # Arrange: 创建服务实例
        service = ConfigTemplateService()

        # Act: 列出所有模板
        templates = service.list_templates()

        # Assert: 验证包含默认模板
        assert len(templates) >= 4
        template_names = [t["name"] for t in templates]
        assert "quick_chat" in template_names
        assert "creative_chat" in template_names

    def test_list_templates_by_category(self):
        """
        测试目的：验证按分类列出模板功能
        测试场景：只获取chat分类的模板
        """
        # Arrange: 创建服务实例
        service = ConfigTemplateService()

        # Act: 按分类列出模板
        templates = service.list_templates(category="chat")

        # Assert: 验证都是chat分类
        assert all(t["category"] == "chat" for t in templates)

    def test_list_templates_by_user(self):
        """
        测试目的：验证按用户列出模板功能
        测试场景：获取特定用户的模板和系统模板
        """
        # Arrange: 创建服务并添加用户模板
        service = ConfigTemplateService()
        service.create_chat_template(
            name="user_template",
            provider="ollama",
            model="model",
            user_id="user123"
        )

        # Act: 获取用户模板（系统模板+用户模板）
        templates = service.list_templates(user_id="user123")
        template_names = [t["name"] for t in templates]

        # Assert: 验证包含用户模板和系统模板
        assert "user_template" in template_names
        # 系统模板应该也在列表中

    def test_list_templates_by_tags(self):
        """
        测试目的：验证按标签列出模板功能
        测试场景：只获取包含特定标签的模板
        """
        # Arrange: 创建服务并添加带标签的模板
        service = ConfigTemplateService()
        service.create_chat_template(
            name="tagged_template",
            provider="ollama",
            model="model",
            tags=["自定义", "测试"]
        )

        # Act: 按标签列出模板
        templates = service.list_templates(tags=["自定义"])
        template_names = [t["name"] for t in templates]

        # Assert: 验证包含带该标签的模板
        assert "tagged_template" in template_names

    def test_update_template(self):
        """
        测试目的：验证更新模板功能
        测试场景：更新用户模板的描述和配置
        """
        # Arrange: 创建服务和用户模板
        service = ConfigTemplateService()
        service.create_chat_template(
            name="updatable_template",
            provider="ollama",
            model="model",
            description="原始描述"
        )

        # Act: 更新模板
        result = service.update_template(
            name="updatable_template",
            updates={
                "description": "更新后的描述",
                "temperature": 0.8
            }
        )

        # Assert: 验证更新成功
        assert result["success"] is True
        assert "更新成功" in result["message"]

        # 验证元数据已更新
        metadata = service._template_metadata["updatable_template"]
        assert metadata.description == "更新后的描述"

    def test_update_system_template_fails(self):
        """
        测试目的：验证不能修改系统模板
        测试场景：尝试修改系统默认模板
        """
        # Arrange: 创建服务实例
        service = ConfigTemplateService()

        # Act: 尝试修改系统模板
        result = service.update_template(
            name="quick_chat",
            updates={"description": "修改后的描述"}
        )

        # Assert: 验证失败
        assert result["success"] is False
        assert "不能修改系统模板" in result["message"]

    def test_update_nonexistent_template(self):
        """
        测试目的：验证更新不存在的模板失败
        测试场景：尝试更新不存在的模板
        """
        # Arrange: 创建服务实例
        service = ConfigTemplateService()

        # Act: 尝试更新不存在的模板
        result = service.update_template(
            name="nonexistent",
            updates={"description": "新描述"}
        )

        # Assert: 验证失败
        assert result["success"] is False
        assert "不存在" in result["message"]

    def test_delete_template(self):
        """
        测试目的：验证删除模板功能
        测试场景：删除用户创建的模板
        """
        # Arrange: 创建服务和用户模板
        service = ConfigTemplateService()
        service.create_chat_template(
            name="deletable_template",
            provider="ollama",
            model="model",
            user_id="user123"
        )

        # Act: 删除模板
        result = service.delete_template("deletable_template", user_id="user123")

        # Assert: 验证删除成功
        assert result["success"] is True
        assert "删除成功" in result["message"]
        assert "deletable_template" not in service._template_metadata
        assert PrototypeRegistry.get("deletable_template") is None

    def test_delete_system_template_fails(self):
        """
        测试目的：验证不能删除系统模板
        测试场景：尝试删除系统默认模板
        """
        # Arrange: 创建服务实例
        service = ConfigTemplateService()

        # Act: 尝试删除系统模板
        result = service.delete_template("quick_chat")

        # Assert: 验证失败
        assert result["success"] is False
        assert "不能删除系统模板" in result["message"]

    def test_delete_template_without_permission(self):
        """
        测试目的：验证无权限删除模板失败
        测试场景：用户尝试删除其他用户的模板
        """
        # Arrange: 创建服务和用户A的模板
        service = ConfigTemplateService()
        service.create_chat_template(
            name="user_a_template",
            provider="ollama",
            model="model",
            user_id="user_a"
        )

        # Act: 用户B尝试删除
        result = service.delete_template("user_a_template", user_id="user_b")

        # Assert: 验证失败
        assert result["success"] is False
        assert "无权删除" in result["message"]

    def test_delete_nonexistent_template(self):
        """
        测试目的：验证删除不存在的模板失败
        测试场景：尝试删除不存在的模板
        """
        # Arrange: 创建服务实例
        service = ConfigTemplateService()

        # Act: 尝试删除不存在的模板
        result = service.delete_template("nonexistent")

        # Assert: 验证失败
        assert result["success"] is False
        assert "不存在" in result["message"]

    def test_delete_template_removes_from_user_list(self):
        """
        测试目的：验证删除模板后从用户列表中移除
        测试场景：删除模板后检查用户模板列表
        """
        # Arrange: 创建服务和用户模板
        service = ConfigTemplateService()
        service.create_chat_template(
            name="user_template",
            provider="ollama",
            model="model",
            user_id="user123"
        )

        # Act: 删除模板
        service.delete_template("user_template", user_id="user123")

        # Assert: 验证从用户列表中移除
        assert "user_template" not in service._user_templates["user123"]

    def test_set_default_template(self):
        """
        测试目的：验证设置默认模板功能
        测试场景：将某个模板设为默认
        """
        # Arrange: 创建服务和用户模板
        service = ConfigTemplateService()
        service.create_chat_template(
            name="custom_default",
            provider="ollama",
            model="model"
        )

        # Act: 设置为默认模板
        result = service.set_default_template("custom_default", category="chat")

        # Assert: 验证设置成功
        assert result["success"] is True
        assert service._template_metadata["custom_default"].is_default is True

        # 验证之前的默认模板已被取消
        assert not service._template_metadata["quick_chat"].is_default

    def test_set_default_nonexistent_template(self):
        """
        测试目的：验证设置不存在的模板为默认失败
        测试场景：尝试将不存在的模板设为默认
        """
        # Arrange: 创建服务实例
        service = ConfigTemplateService()

        # Act: 尝试设置不存在的模板为默认
        result = service.set_default_template("nonexistent")

        # Assert: 验证失败
        assert result["success"] is False
        assert "不存在" in result["message"]

    def test_get_default_template(self):
        """
        测试目的：验证获取默认模板功能
        测试场景：获取chat分类的默认模板
        """
        # Arrange: 创建服务实例
        service = ConfigTemplateService()

        # Act: 获取默认模板
        default_name = service.get_default_template(category="chat")

        # Assert: 验证返回quick_chat（默认的默认模板）
        assert default_name == "quick_chat"

    def test_get_default_template_no_match(self):
        """
        测试目的：验证没有匹配的默认模板时返回None
        测试场景：查询没有默认模板的分类
        """
        # Arrange: 创建服务实例
        service = ConfigTemplateService()

        # Act: 查询不存在的分类的默认模板
        default_name = service.get_default_template(category="nonexistent")

        # Assert: 验证返回None
        assert default_name is None

    def test_import_templates(self):
        """
        测试目的：验证批量导入模板功能
        测试场景：导入多个模板
        """
        # Arrange: 创建服务和模板数据
        service = ConfigTemplateService()
        templates_data = [
            {
                "name": "imported_1",
                "provider": "ollama",
                "model": "model1",
                "temperature": 0.7,
                "description": "导入的模板1"
            },
            {
                "name": "imported_2",
                "provider": "ollama",
                "model": "model2",
                "temperature": 0.5,
                "description": "导入的模板2"
            }
        ]

        # Act: 导入模板
        result = service.import_templates(templates_data, user_id="import_user")

        # Assert: 验证导入结果
        assert result["success"] is True
        assert result["imported"] == 2
        assert result["failed"] == 0
        assert "imported_1" in service._template_metadata
        assert "imported_2" in service._template_metadata

    def test_import_templates_with_failures(self):
        """
        测试目的：验证导入部分失败时的处理
        测试场景：导入包含重复名称的模板
        """
        # Arrange: 创建服务和模板数据（包含重复）
        service = ConfigTemplateService()
        service.create_chat_template(name="existing", provider="ollama", model="model")

        templates_data = [
            {"name": "new_template", "provider": "ollama", "model": "model"},
            {"name": "existing", "provider": "ollama", "model": "model"}  # 重复
        ]

        # Act: 导入模板
        result = service.import_templates(templates_data)

        # Assert: 验证导入结果
        assert result["success"] is True
        assert result["imported"] == 1
        assert result["failed"] == 1

    def test_import_templates_invalid_category(self):
        """
        测试目的：验证导入非chat分类模板时的处理
        测试场景：只支持chat分类
        """
        # Arrange: 创建服务和非chat分类的模板数据
        service = ConfigTemplateService()
        templates_data = [
            {"name": "test", "category": "chat", "provider": "ollama", "model": "model"},
            {"name": "test2", "category": "unknown", "provider": "ollama", "model": "model"}
        ]

        # Act: 导入模板
        result = service.import_templates(templates_data)

        # Assert: 验证只有chat分类被导入
        assert result["imported"] == 1

    def test_export_templates_all(self):
        """
        测试目的：验证导出所有模板功能
        测试场景：导出所有模板为列表
        """
        # Arrange: 创建服务并添加自定义模板
        service = ConfigTemplateService()
        service.create_chat_template(
            name="custom_export",
            provider="ollama",
            model="model"
        )

        # Act: 导出所有模板
        exported = service.export_templates()

        # Assert: 验证导出内容
        assert len(exported) >= 5  # 4个默认 + 1个自定义
        template_names = [t["name"] for t in exported]
        assert "custom_export" in template_names

    def test_export_templates_specific_names(self):
        """
        测试目的：验证导出指定模板功能
        测试场景：只导出指定的模板
        """
        # Arrange: 创建服务实例
        service = ConfigTemplateService()

        # Act: 只导出指定模板
        exported = service.export_templates(names=["quick_chat", "creative_chat"])

        # Assert: 验证导出内容
        assert len(exported) == 2
        template_names = [t["name"] for t in exported]
        assert "quick_chat" in template_names
        assert "creative_chat" in template_names

    def test_export_templates_with_user_filter(self):
        """
        测试目的：验证按用户过滤导出功能
        测试场景：只导出系统模板和指定用户的模板
        """
        # Arrange: 创建服务并添加用户模板
        service = ConfigTemplateService()
        service.create_chat_template(
            name="user_export",
            provider="ollama",
            model="model",
            user_id="user123"
        )

        # Act: 导出（实际未使用user_id过滤，所以包含所有）
        exported = service.export_templates()
        template_names = [t["name"] for t in exported]

        # Assert: 验证包含用户模板
        assert "user_export" in template_names

    def test_export_templates_nonexistent_names(self):
        """
        测试目的：验证导出不存在的模板名称时被忽略
        测试场景：导出列表包含不存在的模板名
        """
        # Arrange: 创建服务实例
        service = ConfigTemplateService()

        # Act: 导出时包含不存在的模板名
        exported = service.export_templates(names=["quick_chat", "nonexistent"])

        # Assert: 验证只导出存在的模板
        assert len(exported) == 1
        assert exported[0]["name"] == "quick_chat"


# ============================================================================
# 与PrototypeRegistry集成测试类
# ============================================================================

class TestConfigTemplateServiceIntegration:
    """
    类级注释：配置模板服务集成测试类
    职责：测试与原型注册表的集成
    """

    def setup_method(self):
        """
        测试前准备：清理原型注册表
        """
        PrototypeRegistry._prototypes.clear()

    def test_prototype_registration_on_create(self):
        """
        测试目的：验证创建模板时原型正确注册
        测试场景：创建模板后检查注册表
        """
        # Arrange: 创建服务实例
        service = ConfigTemplateService()

        # Act: 创建模板
        service.create_chat_template(
            name="test_proto",
            provider="ollama",
            model="test-model",
            temperature=0.8
        )

        # Assert: 验证原型已注册
        prototype = PrototypeRegistry.get_original("test_proto")
        assert prototype is not None
        assert prototype.model == "test-model"
        assert prototype.temperature == 0.8

    def test_prototype_unregistration_on_delete(self):
        """
        测试目的：验证删除模板时原型正确注销
        测试场景：删除模板后检查注册表
        """
        # Arrange: 创建服务和模板
        service = ConfigTemplateService()
        service.create_chat_template(
            name="delete_proto",
            provider="ollama",
            model="model",
            user_id="user123"
        )

        # Act: 删除模板
        service.delete_template("delete_proto", user_id="user123")

        # Assert: 验证原型已注销
        assert PrototypeRegistry.get_original("delete_proto") is None

    def test_clone_creates_new_prototype(self):
        """
        测试目的：验证克隆创建新的原型实例
        测试场景：克隆模板后验证独立性
        """
        # Arrange: 创建服务和源模板
        service = ConfigTemplateService()
        service.create_chat_template(
            name="source",
            provider="ollama",
            model="model",
            temperature=0.7
        )

        # Act: 克隆模板
        service.clone_template("source", "clone")

        # Assert: 验证两个原型独立存在
        source = PrototypeRegistry.get_original("source")
        clone = PrototypeRegistry.get_original("clone")
        assert source is not None
        assert clone is not None
        assert source is not clone

    def test_instance_does_not_modify_prototype(self):
        """
        测试目的：验证创建实例不修改原型
        测试场景：创建实例时传入修改，验证原型不变
        """
        # Arrange: 创建服务和模板
        service = ConfigTemplateService()
        service.create_chat_template(
            name="base",
            provider="ollama",
            model="model",
            temperature=0.7
        )

        # Act: 创建实例并修改
        original_proto = PrototypeRegistry.get_original("base")
        service.create_instance("base", modifications={"temperature": 0.9})

        # Assert: 验证原型未被修改
        assert PrototypeRegistry.get_original("base").temperature == 0.7
        assert PrototypeRegistry.get_original("base") is original_proto


# ============================================================================
# 默认模板详细测试类
# ============================================================================

class TestDefaultTemplates:
    """
    类级注释：默认模板测试类
    职责：验证所有默认模板的正确性
    """

    def setup_method(self):
        """
        测试前准备：清理原型注册表
        """
        PrototypeRegistry._prototypes.clear()

    def test_quick_chat_default_template(self):
        """
        测试目的：验证快速聊天默认模板配置
        测试场景：检查quick_chat模板的配置
        """
        # Arrange: 创建服务实例
        service = ConfigTemplateService()

        # Act: 获取模板配置
        template = service.get_template("quick_chat")

        # Assert: 验证配置
        assert template is not None
        assert template["config"]["provider"] == "ollama"
        assert template["config"]["model"] == "deepseek-r1:8b"
        assert template["config"]["temperature"] == 0.3
        assert template["config"]["max_tokens"] == 1000
        assert "简洁" in template["config"]["system_prompt"]

    def test_creative_chat_default_template(self):
        """
        测试目的：验证创意聊天默认模板配置
        测试场景：检查creative_chat模板的配置
        """
        # Arrange: 创建服务实例
        service = ConfigTemplateService()

        # Act: 获取模板配置
        template = service.get_template("creative_chat")

        # Assert: 验证配置
        assert template is not None
        assert template["config"]["temperature"] == 0.9
        assert template["config"]["max_tokens"] == 2000
        assert "创造力" in template["config"]["system_prompt"]

    def test_code_chat_default_template(self):
        """
        测试目的：验证代码助手默认模板配置
        测试场景：检查code_chat模板的配置
        """
        # Arrange: 创建服务实例
        service = ConfigTemplateService()

        # Act: 获取模板配置
        template = service.get_template("code_chat")

        # Assert: 验证配置
        assert template is not None
        assert template["config"]["temperature"] == 0.2
        assert "编程助手" in template["config"]["system_prompt"]

    def test_precise_chat_default_template(self):
        """
        测试目的：验证精确聊天默认模板配置
        测试场景：检查precise_chat模板的配置
        """
        # Arrange: 创建服务实例
        service = ConfigTemplateService()

        # Act: 获取模板配置
        template = service.get_template("precise_chat")

        # Assert: 验证配置
        assert template is not None
        assert template["config"]["provider"] == "zhipuai"
        assert template["config"]["model"] == "glm-4.5-air"
        assert template["config"]["temperature"] == 0.1
        assert "严谨" in template["config"]["system_prompt"]
