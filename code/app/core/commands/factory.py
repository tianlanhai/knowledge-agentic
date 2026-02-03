# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：命令工厂模块
内部逻辑：提供创建命令的工厂方法
设计模式：工厂模式 + 建造者模式
设计原则：开闭原则、单一职责原则
"""

from typing import Any, Optional, Dict, List
from loguru import logger

from app.core.commands import Command, CommandInvoker, MacroCommand
from app.core.commands.business import (
    DeleteDocumentCommand,
    UpdateConfigCommand,
    BatchDeleteCommand,
)


class CommandFactory:
    """
    类级注释：命令工厂
    内部逻辑：统一创建各类命令的工厂方法
    设计模式：工厂模式 + 建造者模式
    职责：
        1. 创建聊天命令
        2. 创建文档操作命令
        3. 创建配置命令
        4. 创建宏命令

    使用场景：
        - API端点将请求转换为命令
        - 业务逻辑封装为命令
        - 支持操作审计和回滚
    """

    @staticmethod
    def create_chat_command(
        request: Any,
        db: Any,
        chat_service: Any,
        command_id: Optional[str] = None
    ) -> Command:
        """
        函数级注释：创建聊天命令
        参数：
            request - 聊天请求
            db - 数据库会话
            chat_service - 聊天服务
            command_id - 命令ID
        返回值：聊天命令实例

        @example
        ```python
        command = CommandFactory.create_chat_command(request, db, chat_service)
        result = await invoker.execute(command)
        ```
        """
        from app.core.commands import ChatCommand

        return ChatCommand(
            request=request,
            db=db,
            chat_service=chat_service,
            command_id=command_id
        )

    @staticmethod
    def create_ingest_command(
        file_path: str,
        ingest_service: Any,
        command_id: Optional[str] = None
    ) -> Command:
        """
        函数级注释：创建文档摄入命令
        参数：
            file_path - 文件路径
            ingest_service - 摄入服务
            command_id - 命令ID
        返回值：文档摄入命令实例
        """
        from app.core.commands import IngestDocumentCommand

        return IngestDocumentCommand(
            file_path=file_path,
            ingest_service=ingest_service,
            command_id=command_id
        )

    @staticmethod
    def create_delete_command(
        doc_id: int,
        delete_service: Any,
        backup_service: Optional[Any] = None,
        command_id: Optional[str] = None
    ) -> Command:
        """
        函数级注释：创建删除文档命令
        参数：
            doc_id - 文档ID
            delete_service - 删除服务
            backup_service - 备份服务
            command_id - 命令ID
        返回值：删除文档命令实例
        """
        return DeleteDocumentCommand(
            doc_id=doc_id,
            delete_service=delete_service,
            backup_service=backup_service,
            command_id=command_id
        )

    @staticmethod
    def create_batch_delete_command(
        doc_ids: List[int],
        delete_service: Any,
        backup_service: Optional[Any] = None,
        command_id: Optional[str] = None
    ) -> Command:
        """
        函数级注释：创建批量删除命令
        参数：
            doc_ids - 文档ID列表
            delete_service - 删除服务
            backup_service - 备份服务
            command_id - 命令ID
        返回值：批量删除命令实例
        """
        return BatchDeleteCommand(
            doc_ids=doc_ids,
            delete_service=delete_service,
            backup_service=backup_service,
            command_id=command_id
        )

    @staticmethod
    def create_update_config_command(
        config_service: Any,
        new_config: Dict[str, Any],
        command_id: Optional[str] = None
    ) -> Command:
        """
        函数级注释：创建更新配置命令
        参数：
            config_service - 配置服务
            new_config - 新配置
            command_id - 命令ID
        返回值：更新配置命令实例
        """
        return UpdateConfigCommand(
            config_service=config_service,
            new_config=new_config,
            command_id=command_id
        )

    @staticmethod
    def create_macro_command(
        commands: List[Command],
        command_id: Optional[str] = None,
        stop_on_error: bool = False
    ) -> MacroCommand:
        """
        函数级注释：创建宏命令
        参数：
            commands - 子命令列表
            command_id - 命令ID
            stop_on_error - 遇到错误是否停止
        返回值：宏命令实例

        @example
        ```python
        # 创建批量处理命令
        commands = [
            CommandFactory.create_ingest_command("file1.pdf", ingest_service),
            CommandFactory.create_ingest_command("file2.pdf", ingest_service),
            CommandFactory.create_ingest_command("file3.pdf", ingest_service),
        ]
        macro = CommandFactory.create_macro_command(commands)
        result = await invoker.execute(macro)
        ```
        """
        macro = MacroCommand(command_id)

        for cmd in commands:
            macro.add_command(cmd)

        return macro

    @staticmethod
    def create_function_command(
        func: callable,
        *args,
        command_id: Optional[str] = None,
        **kwargs
    ) -> Command:
        """
        函数级注释：创建函数命令
        内部逻辑：将任意函数包装为命令
        参数：
            func - 要执行的函数
            args - 位置参数
            command_id - 命令ID
            kwargs - 关键字参数
        返回值：函数命令实例
        """
        class FunctionCommand(Command):
            async def execute(self) -> CommandResult:
                import time
                start_time = time.time()

                try:
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)

                    duration = time.time() - start_time
                    self._duration = duration
                    self._result = result
                    self._status = "success"

                    return CommandResult(
                        success=True,
                        data=result,
                        duration=duration
                    )
                except Exception as e:
                    duration = time.time() - start_time
                    self._duration = duration
                    self._status = "failed"
                    self._error = str(e)

                    return CommandResult(
                        success=False,
                        error=str(e),
                        duration=duration
                    )

        return FunctionCommand(command_id)


class CommandBuilder:
    """
    类级注释：命令建造者
    内部逻辑：使用流式API构建复杂命令
    设计模式：建造者模式
    职责：提供流式API构建命令

    @example
    ```python
    command = (CommandBuilder()
        .with_type("chat")
        .with_request(request)
        .with_db(db)
        .with_service(chat_service)
        .build())
    ```
    """

    def __init__(self):
        """
        函数级注释：初始化命令建造者
        """
        # 内部变量：命令类型
        self._command_type: Optional[str] = None
        # 内部变量：命令参数
        self._params: Dict[str, Any] = {}

    def with_type(self, command_type: str) -> 'CommandBuilder':
        """
        函数级注释：设置命令类型
        参数：
            command_type - 命令类型
        返回值：建造者自身
        """
        self._command_type = command_type
        return self

    def with_request(self, request: Any) -> 'CommandBuilder':
        """
        函数级注释：设置请求参数
        参数：
            request - 请求对象
        返回值：建造者自身
        """
        self._params['request'] = request
        return self

    def with_db(self, db: Any) -> 'CommandBuilder':
        """
        函数级注释：设置数据库会话
        参数：
            db - 数据库会话
        返回值：建造者自身
        """
        self._params['db'] = db
        return self

    def with_service(self, service: Any) -> 'CommandBuilder':
        """
        函数级注释：设置服务对象
        参数：
            service - 服务实例
        返回值：建造者自身
        """
        self._params['service'] = service
        return self

    def with_id(self, command_id: str) -> 'CommandBuilder':
        """
        函数级注释：设置命令ID
        参数：
            command_id - 命令ID
        返回值：建造者自身
        """
        self._params['command_id'] = command_id
        return self

    def build(self) -> Command:
        """
        函数级注释：构建命令
        返回值：命令实例
        异常：ValueError - 命令类型未设置时抛出
        """
        if not self._command_type:
            raise ValueError("必须指定命令类型")

        if self._command_type == "chat":
            return CommandFactory.create_chat_command(
                request=self._params.get('request'),
                db=self._params.get('db'),
                chat_service=self._params.get('service'),
                command_id=self._params.get('command_id')
            )
        elif self._command_type == "ingest":
            return CommandFactory.create_ingest_command(
                file_path=self._params.get('file_path'),
                ingest_service=self._params.get('service'),
                command_id=self._params.get('command_id')
            )
        elif self._command_type == "delete":
            return CommandFactory.create_delete_command(
                doc_id=self._params.get('doc_id'),
                delete_service=self._params.get('service'),
                backup_service=self._params.get('backup_service'),
                command_id=self._params.get('command_id')
            )
        else:
            raise ValueError(f"不支持的命令类型: {self._command_type}")


# 内部变量：导出所有公共接口
__all__ = [
    'CommandFactory',
    'CommandBuilder',
]
