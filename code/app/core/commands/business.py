# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：业务命令模块
内部逻辑：实现具体的业务命令
设计模式：命令模式 - 具体命令
设计原则：单一职责原则
"""

from typing import Any, Dict, List, Optional
from loguru import logger

from app.core.commands import Command, CommandResult


class DeleteDocumentCommand(Command[Dict[str, Any]]):
    """
    类级注释：删除文档命令
    内部逻辑：封装文档删除操作，支持撤销（恢复）
    设计模式：命令模式 - 具体命令
    """

    def __init__(
        self,
        doc_id: int,
        delete_service: Any,
        backup_service: Optional[Any] = None,
        command_id: Optional[str] = None
    ):
        """
        函数级注释：初始化删除文档命令
        参数：
            doc_id - 文档ID
            delete_service - 删除服务
            backup_service - 备份服务（用于撤销）
            command_id - 命令ID
        """
        super().__init__(command_id)
        # 内部变量：文档ID
        self._doc_id = doc_id
        # 内部变量：删除服务
        self._delete_service = delete_service
        # 内部变量：备份服务
        self._backup_service = backup_service
        # 内部变量：文档备份数据
        self._backup: Optional[Dict[str, Any]] = None

    async def execute(self) -> CommandResult:
        """
        函数级注释：执行删除文档命令
        内部逻辑：备份文档 -> 删除记录 -> 返回结果
        返回值：命令执行结果
        """
        import time

        self._status = "running"
        start_time = time.time()

        try:
            # 内部逻辑：备份文档数据
            if self._backup_service:
                self._backup = await self._backup_service.backup_document(self._doc_id)

            # 内部逻辑：执行删除
            await self._delete_service.delete_document(self._doc_id)

            self._duration = time.time() - start_time
            self._status = "success"

            return CommandResult(
                success=True,
                data={"doc_id": self._doc_id, "message": "文档已删除"},
                duration=self._duration
            )

        except Exception as e:
            self._duration = time.time() - start_time
            self._status = "failed"
            self._error = str(e)

            return CommandResult(
                success=False,
                error=str(e),
                duration=self._duration
            )

    def can_undo(self) -> bool:
        """检查是否可以撤销"""
        return self._backup is not None

    async def undo(self) -> CommandResult:
        """
        函数级注释：撤销删除命令
        内部逻辑：使用备份数据恢复文档
        返回值：命令执行结果
        """
        if not self._backup:
            return CommandResult(
                success=False,
                error="无法撤销：没有备份数据"
            )

        try:
            # 内部逻辑：恢复文档
            await self._backup_service.restore_document(self._backup)
            self._status = "undone"

            return CommandResult(
                success=True,
                data=f"已恢复文档 {self._doc_id}"
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"恢复失败: {str(e)}"
            )


class UpdateConfigCommand(Command[Dict[str, Any]]):
    """
    类级注释：更新配置命令
    内部逻辑：封装配置更新操作，支持撤销
    设计模式：命令模式 - 具体命令
    """

    def __init__(
        self,
        config_service: Any,
        new_config: Dict[str, Any],
        command_id: Optional[str] = None
    ):
        """
        函数级注释：初始化更新配置命令
        参数：
            config_service - 配置服务
            new_config - 新配置
            command_id - 命令ID
        """
        super().__init__(command_id)
        # 内部变量：配置服务
        self._config_service = config_service
        # 内部变量：新配置
        self._new_config = new_config
        # 内部变量：旧配置（用于撤销）
        self._old_config: Optional[Dict[str, Any]] = None

    async def execute(self) -> CommandResult:
        """
        函数级注释：执行更新配置命令
        内部逻辑：保存旧配置 -> 更新配置 -> 返回结果
        返回值：命令执行结果
        """
        import time

        self._status = "running"
        start_time = time.time()

        try:
            # 内部逻辑：获取并保存当前配置
            self._old_config = await self._config_service.get_config()

            # 内部逻辑：更新配置
            await self._config_service.update_config(self._new_config)

            self._duration = time.time() - start_time
            self._status = "success"

            return CommandResult(
                success=True,
                data=self._new_config,
                duration=self._duration
            )

        except Exception as e:
            self._duration = time.time() - start_time
            self._status = "failed"
            self._error = str(e)

            return CommandResult(
                success=False,
                error=str(e),
                duration=self._duration
            )

    def can_undo(self) -> bool:
        """检查是否可以撤销"""
        return self._old_config is not None

    async def undo(self) -> CommandResult:
        """
        函数级注释：撤销更新配置命令
        内部逻辑：恢复旧配置
        返回值：命令执行结果
        """
        if not self._old_config:
            return CommandResult(
                success=False,
                error="无法撤销：没有保存的旧配置"
            )

        try:
            await self._config_service.update_config(self._old_config)
            self._status = "undone"

            return CommandResult(
                success=True,
                data="配置已恢复"
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"恢复配置失败: {str(e)}"
            )


class BatchDeleteCommand(Command[Dict[str, Any]]):
    """
    类级注释：批量删除命令
    内部逻辑：封装批量文档删除操作
    设计模式：命令模式 + 宏命令模式
    """

    def __init__(
        self,
        doc_ids: List[int],
        delete_service: Any,
        backup_service: Optional[Any] = None,
        command_id: Optional[str] = None
    ):
        """
        函数级注释：初始化批量删除命令
        参数：
            doc_ids - 文档ID列表
            delete_service - 删除服务
            backup_service - 备份服务
            command_id - 命令ID
        """
        super().__init__(command_id)
        # 内部变量：文档ID列表
        self._doc_ids = doc_ids
        # 内部变量：删除服务
        self._delete_service = delete_service
        # 内部变量：备份服务
        self._backup_service = backup_service
        # 内部变量：删除结果记录
        self._deleted_ids: List[int] = []
        # 内部变量：备份记录
        self._backups: List[Dict[str, Any]] = []

    async def execute(self) -> CommandResult:
        """
        函数级注释：执行批量删除命令
        内部逻辑：循环删除每个文档 -> 记录结果
        返回值：命令执行结果
        """
        import time

        self._status = "running"
        start_time = time.time()

        try:
            for doc_id in self._doc_ids:
                # 内部逻辑：备份文档
                if self._backup_service:
                    backup = await self._backup_service.backup_document(doc_id)
                    self._backups.append(backup)

                # 内部逻辑：删除文档
                await self._delete_service.delete_document(doc_id)
                self._deleted_ids.append(doc_id)

            self._duration = time.time() - start_time
            self._status = "success"

            return CommandResult(
                success=True,
                data={
                    "deleted_count": len(self._deleted_ids),
                    "deleted_ids": self._deleted_ids
                },
                duration=self._duration
            )

        except Exception as e:
            self._duration = time.time() - start_time
            self._status = "failed"
            self._error = str(e)

            return CommandResult(
                success=False,
                error=str(e),
                duration=self._duration,
                metadata={"partial_deleted": self._deleted_ids}
            )

    def can_undo(self) -> bool:
        """检查是否可以撤销"""
        return len(self._backups) > 0

    async def undo(self) -> CommandResult:
        """
        函数级注释：撤销批量删除命令
        内部逻辑：逆序恢复所有删除的文档
        返回值：命令执行结果
        """
        if not self._backups:
            return CommandResult(
                success=False,
                error="无法撤销：没有备份数据"
            )

        try:
            # 内部逻辑：逆序恢复
            restored_count = 0
            for backup in reversed(self._backups):
                await self._backup_service.restore_document(backup)
                restored_count += 1

            self._status = "undone"

            return CommandResult(
                success=True,
                data=f"已恢复 {restored_count} 个文档"
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"恢复失败: {str(e)}"
            )


# 内部变量：导出所有公共接口
__all__ = [
    'DeleteDocumentCommand',
    'UpdateConfigCommand',
    'BatchDeleteCommand',
]
