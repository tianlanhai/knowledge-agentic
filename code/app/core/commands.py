# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：命令模式模块
内部逻辑：封装操作为命令对象，支持撤销/重做、操作审计和批量执行
设计模式：命令模式（Command Pattern）
设计原则：开闭原则、单一职责原则
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
from datetime import datetime
import asyncio
from functools import wraps

# 内部变量：泛型类型
T = TypeVar('T')


class CommandStatus(str, Enum):
    """
    类级注释：命令状态枚举
    内部逻辑：定义命令的执行状态
    """
    # 未执行
    PENDING = "pending"
    # 执行中
    RUNNING = "running"
    # 执行成功
    SUCCESS = "success"
    # 执行失败
    FAILED = "failed"
    # 已撤销
    UNDONE = "undone"
    # 已重做
    REDONE = "redone"
    # 取消中
    CANCELLING = "cancelling"
    # 已取消
    CANCELLED = "cancelled"


@dataclass
class CommandResult:
    """
    类级注释：命令执行结果
    内部逻辑：封装命令执行的结果信息
    """
    # 属性：是否成功
    success: bool
    # 属性：返回数据
    data: Any = None
    # 属性：错误信息
    error: Optional[str] = None
    # 属性：执行时长（秒）
    duration: float = 0.0
    # 属性：额外元数据
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CommandLog:
    """
    类级注释：命令执行日志
    内部逻辑：记录命令的完整执行历史
    """
    # 属性：命令 ID
    command_id: str
    # 属性：命令类型
    command_type: str
    # 属性：用户 ID
    user_id: Optional[str] = None
    # 属性：会话 ID
    session_id: Optional[str] = None
    # 属性：执行时间
    executed_at: datetime = field(default_factory=datetime.now)
    # 属性：执行状态
    status: CommandStatus = CommandStatus.PENDING
    # 属性：执行时长
    duration: float = 0.0
    # 属性：输入参数（脱敏后）
    input_params: Dict[str, Any] = field(default_factory=dict)
    # 属性：输出结果
    output: Any = None
    # 属性：错误信息
    error: Optional[str] = None


class Command(ABC, Generic[T]):
    """
    类级注释：命令抽象基类
    内部逻辑：定义命令的统一接口
    设计模式：命令模式 - 抽象命令接口
    """

    def __init__(self, command_id: Optional[str] = None):
        """
        函数级注释：初始化命令
        参数：
            command_id - 命令 ID，为 None 时自动生成
        """
        # 内部变量：命令 ID
        self._id = command_id or self._generate_id()
        # 内部变量：执行状态
        self._status = CommandStatus.PENDING
        # 内部变量：执行时间
        self._executed_at: Optional[datetime] = None
        # 内部变量：执行时长
        self._duration: float = 0.0
        # 内部变量：结果数据
        self._result: Optional[T] = None
        # 内部变量：错误信息
        self._error: Optional[str] = None
        # 内部变量：用于撤销的数据
        self._memento: Optional[Any] = None

    @property
    def id(self) -> str:
        """
        函数级注释：获取命令 ID
        返回值：命令 ID
        """
        return self._id

    @property
    def status(self) -> CommandStatus:
        """
        函数级注释：获取命令状态
        返回值：命令状态
        """
        return self._status

    @property
    def result(self) -> Optional[T]:
        """
        函数级注释：获取执行结果
        返回值：执行结果
        """
        return self._result

    @property
    def error(self) -> Optional[str]:
        """
        函数级注释：获取错误信息
        返回值：错误信息
        """
        return self._error

    @staticmethod
    def _generate_id() -> str:
        """
        函数级注释：生成命令 ID
        返回值：唯一 ID
        """
        import uuid
        return f"cmd_{uuid.uuid4().hex[:12]}"

    @abstractmethod
    async def execute(self) -> CommandResult:
        """
        函数级注释：执行命令（抽象方法）
        内部逻辑：由子类实现具体的执行逻辑
        返回值：命令执行结果
        """
        pass

    async def undo(self) -> CommandResult:
        """
        函数级注释：撤销命令
        内部逻辑：默认实现不支持撤销，子类可覆盖
        返回值：命令执行结果
        异常：NotImplementedError - 不支持撤销时抛出
        """
        raise NotImplementedError(f"命令 {self.__class__.__name__} 不支持撤销")

    async def redo(self) -> CommandResult:
        """
        函数级注释：重做命令
        内部逻辑：默认实现为重新执行
        返回值：命令执行结果
        """
        return await self.execute()

    def can_undo(self) -> bool:
        """
        函数级注释：检查是否可以撤销
        返回值：是否支持撤销
        """
        return False

    def get_description(self) -> str:
        """
        函数级注释：获取命令描述
        返回值：命令描述字符串
        """
        return f"{self.__class__.__name__}({self._id})"

    def to_log(self) -> CommandLog:
        """
        函数级注释：转换为日志对象
        返回值：命令日志
        """
        return CommandLog(
            command_id=self._id,
            command_type=self.__class__.__name__,
            status=self._status,
            duration=self._duration,
            output=self._result,
            error=self._error
        )


class MacroCommand(Command[T]):
    """
    类级注释：宏命令
    内部逻辑：组合多个命令，批量执行
    设计模式：命令模式 + 组合模式
    """

    def __init__(self, command_id: Optional[str] = None):
        """
        函数级注释：初始化宏命令
        参数：
            command_id - 命令 ID
        """
        super().__init__(command_id)
        # 内部变量：子命令列表
        self._commands: List[Command] = []
        # 内部变量：执行到哪个命令
        self._executed_index: int = -1

    def add_command(self, command: Command) -> 'MacroCommand':
        """
        函数级注释：添加子命令
        参数：
            command - 子命令
        返回值：自身（支持链式调用）
        """
        self._commands.append(command)
        return self

    def add_commands(self, commands: List[Command]) -> 'MacroCommand':
        """
        函数级注释：批量添加子命令
        参数：
            commands - 子命令列表
        返回值：自身（支持链式调用）
        """
        self._commands.extend(commands)
        return self

    async def execute(self) -> CommandResult:
        """
        函数级注释：执行所有子命令
        内部逻辑：顺序执行所有子命令 -> 收集结果 -> 失败时可选择停止或继续
        返回值：命令执行结果
        """
        import time

        self._status = CommandStatus.RUNNING
        start_time = time.time()

        # 内部变量：收集结果
        results: List[CommandResult] = []
        errors: List[str] = []

        logger.info(f"宏命令开始执行: {self._id}, 子命令数: {len(self._commands)}")

        for i, command in enumerate(self._commands):
            self._executed_index = i

            try:
                logger.debug(f"执行子命令 {i + 1}/{len(self._commands)}: {command.get_description()}")
                result = await command.execute()
                results.append(result)

                if not result.success:
                    error_msg = f"子命令 {i + 1} 失败: {result.error}"
                    errors.append(error_msg)
                    logger.warning(error_msg)

                    # 内部逻辑：默认遇到错误继续执行
                    # 子类可覆盖此行为

            except Exception as e:
                error_msg = f"子命令 {i + 1} 异常: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
                results.append(CommandResult(success=False, error=str(e)))

        # 内部逻辑：计算执行时长
        self._duration = time.time() - start_time

        # 内部逻辑：确定整体成功状态
        success = len(errors) == 0

        if success:
            self._status = CommandStatus.SUCCESS
            self._result = [r.data for r in results]
        else:
            self._status = CommandStatus.FAILED
            self._error = "; ".join(errors)

        logger.info(
            f"宏命令执行完成: {self._id}, "
            f"成功={success}, 用时={self._duration:.2f}s"
        )

        return CommandResult(
            success=success,
            data=self._result,
            error=self._error,
            duration=self._duration,
            metadata={"command_results": results, "error_count": len(errors)}
        )

    async def undo(self) -> CommandResult:
        """
        函数级注释：撤销所有已执行的子命令
        内部逻辑：逆序撤销所有已执行的子命令
        返回值：命令执行结果
        """
        import time

        if self._executed_index < 0:
            return CommandResult(success=True, data="无需撤销")

        start_time = time.time()
        results: List[CommandResult] = []
        errors: List[str] = []

        logger.info(f"宏命令开始撤销: {self._id}")

        # 内部逻辑：逆序撤销
        for i in range(self._executed_index, -1, -1):
            command = self._commands[i]

            if command.can_undo():
                try:
                    result = await command.undo()
                    results.append(result)

                    if not result.success:
                        errors.append(f"撤销子命令 {i} 失败: {result.error}")

                except Exception as e:
                    errors.append(f"撤销子命令 {i} 异常: {str(e)}")
            else:
                logger.warning(f"子命令 {i} 不支持撤销，跳过")

        self._duration = time.time() - start_time
        success = len(errors) == 0

        if success:
            self._status = CommandStatus.UNDONE
        else:
            self._error = "; ".join(errors)

        return CommandResult(
            success=success,
            error=self._error if not success else None,
            duration=self._duration
        )

    def can_undo(self) -> bool:
        """
        函数级注释：检查是否可以撤销
        返回值：是否至少有一个子命令可以撤销
        """
        return any(cmd.can_undo() for cmd in self._commands)


class CommandInvoker:
    """
    类级注释：命令调用器
    内部逻辑：管理命令的执行、撤销、重做
    设计模式：命令模式 - 调用者
    职责：
        1. 执行命令
        2. 管理命令历史
        3. 支持撤销/重做
        4. 记录审计日志
    """

    def __init__(self, max_history: int = 100):
        """
        函数级注释：初始化命令调用器
        参数：
            max_history - 最大历史记录数
        """
        # 内部变量：命令历史
        self._history: List[Command] = []

        # 内部变量：撤销栈
        self._undo_stack: List[Command] = []

        # 内部变量：重做栈
        self._redo_stack: List[Command] = []

        # 内部变量：最大历史记录数
        self._max_history = max_history

        # 内部变量：审计日志
        self._audit_logs: List[CommandLog] = []

        # 内部变量：统计信息
        self._stats = {
            "total_executed": 0,
            "total_undone": 0,
            "total_redone": 0,
            "total_failed": 0
        }

        logger.info("命令调用器初始化完成")

    async def execute(self, command: Command) -> CommandResult:
        """
        函数级注释：执行命令
        内部逻辑：执行命令 -> 记录历史 -> 清空重做栈
        参数：
            command - 要执行的命令
        返回值：命令执行结果
        """
        logger.info(f"执行命令: {command.get_description()}")

        # 内部逻辑：执行命令
        raw_result = await command.execute()

        # 内部逻辑：处理不同类型的返回值
        # 如果命令返回的是CommandResult，直接使用；否则包装成CommandResult
        if isinstance(raw_result, CommandResult):
            result = raw_result
        else:
            # 非CommandResult类型（如字符串、数字等），包装成成功结果
            result = CommandResult(success=True, data=raw_result)

        # 内部逻辑：更新统计
        self._stats["total_executed"] += 1
        if not result.success:
            self._stats["total_failed"] += 1

        # 内部逻辑：记录到历史
        self._history.append(command)
        if len(self._history) > self._max_history:
            self._history.pop(0)

        # 内部逻辑：记录审计日志
        self._audit_logs.append(command.to_log())

        # 内部逻辑：如果成功且可撤销，加入撤销栈
        if result.success and command.can_undo():
            self._undo_stack.append(command)

        # 内部逻辑：执行新命令后清空重做栈
        self._redo_stack.clear()

        return result

    async def undo(self, steps: int = 1) -> CommandResult:
        """
        函数级注释：撤销命令
        内部逻辑：从撤销栈弹出命令 -> 执行撤销 -> 加入重做栈
        参数：
            steps - 撤销步数
        返回值：撤销结果
        """
        if not self._undo_stack:
            return CommandResult(
                success=False,
                error="没有可撤销的命令"
            )

        import time
        start_time = time.time()
        results: List[CommandResult] = []

        # 内部逻辑：撤销指定步数
        for _ in range(min(steps, len(self._undo_stack))):
            command = self._undo_stack.pop()

            if command.can_undo():
                logger.info(f"撤销命令: {command.get_description()}")
                result = await command.undo()
                results.append(result)

                if result.success:
                    self._redo_stack.append(command)
                    self._stats["total_undone"] += 1

        return CommandResult(
            success=all(r.success for r in results),
            data=f"撤销了 {len(results)} 个命令",
            duration=time.time() - start_time
        )

    async def redo(self, steps: int = 1) -> CommandResult:
        """
        函数级注释：重做命令
        内部逻辑：从重做栈弹出命令 -> 重新执行 -> 加入撤销栈
        参数：
            steps - 重做步数
        返回值：重做结果
        """
        if not self._redo_stack:
            return CommandResult(
                success=False,
                error="没有可重做的命令"
            )

        import time
        start_time = time.time()
        results: List[CommandResult] = []

        # 内部逻辑：重做指定步数
        for _ in range(min(steps, len(self._redo_stack))):
            command = self._redo_stack.pop()

            logger.info(f"重做命令: {command.get_description()}")
            result = await command.redo()
            results.append(result)

            if result.success:
                self._undo_stack.append(command)
                self._stats["total_redone"] += 1

        return CommandResult(
            success=all(r.success for r in results),
            data=f"重做了 {len(results)} 个命令",
            duration=time.time() - start_time
        )

    def can_undo(self) -> bool:
        """
        函数级注释：检查是否可以撤销
        返回值：是否有可撤销的命令
        """
        return len(self._undo_stack) > 0

    def can_redo(self) -> bool:
        """
        函数级注释：检查是否可以重做
        返回值：是否有可重做的命令
        """
        return len(self._redo_stack) > 0

    def get_history(self, limit: int = 50) -> List[Command]:
        """
        函数级注释：获取命令历史
        参数：
            limit - 最大返回条数
        返回值：命令列表
        """
        return self._history[-limit:]

    def get_audit_logs(
        self,
        limit: int = 100,
        command_type: Optional[str] = None
    ) -> List[CommandLog]:
        """
        函数级注释：获取审计日志
        参数：
            limit - 最大返回条数
            command_type - 过滤命令类型
        返回值：审计日志列表
        """
        logs = self._audit_logs

        if command_type:
            logs = [log for log in logs if log.command_type == command_type]

        return logs[-limit:][::-1]

    def get_stats(self) -> Dict[str, Any]:
        """
        函数级注释：获取统计信息
        返回值：统计信息字典
        """
        stats = self._stats.copy()
        stats["undo_stack_size"] = len(self._undo_stack)
        stats["redo_stack_size"] = len(self._redo_stack)
        stats["history_size"] = len(self._history)
        stats["audit_log_size"] = len(self._audit_logs)
        return stats

    def clear(self) -> None:
        """
        函数级注释：清空所有历史和栈
        """
        self._history.clear()
        self._undo_stack.clear()
        self._redo_stack.clear()
        logger.info("命令调用器已清空")


# ==================== 具体命令实现 ====================

class ChatCommand(Command[Dict[str, Any]]):
    """
    类级注释：聊天命令
    内部逻辑：封装聊天操作
    设计模式：命令模式 - 具体命令
    """

    def __init__(
        self,
        request: Any,
        db: Any,
        chat_service: Any,
        command_id: Optional[str] = None
    ):
        """
        函数级注释：初始化聊天命令
        参数：
            request - 聊天请求
            db - 数据库会话
            chat_service - 聊天服务
            command_id - 命令 ID
        """
        super().__init__(command_id)
        # 内部变量：聊天请求
        self._request = request
        # 内部变量：数据库会话
        self._db = db
        # 内部变量：聊天服务
        self._chat_service = chat_service

    async def execute(self) -> CommandResult:
        """
        函数级注释：执行聊天命令
        内部逻辑：调用聊天服务 -> 返回结果
        返回值：命令执行结果
        """
        import time

        self._status = CommandStatus.RUNNING
        start_time = time.time()

        try:
            # 内部逻辑：保存当前消息状态用于撤销
            if hasattr(self._request, 'history'):
                self._memento = {
                    'history': list(self._request.history) if self._request.history else []
                }

            # 内部逻辑：调用聊天服务
            result = await self._chat_service.chat_completion(
                self._db,
                self._request
            )

            self._duration = time.time() - start_time
            self._status = CommandStatus.SUCCESS
            self._result = result

            return CommandResult(
                success=True,
                data=result,
                duration=self._duration
            )

        except Exception as e:
            self._duration = time.time() - start_time
            self._status = CommandStatus.FAILED
            self._error = str(e)

            logger.error(f"聊天命令执行失败: {str(e)}")

            return CommandResult(
                success=False,
                error=str(e),
                duration=self._duration
            )

    def can_undo(self) -> bool:
        """
        函数级注释：检查是否可以撤销
        返回值：是否支持撤销
        """
        return self._memento is not None

    async def undo(self) -> CommandResult:
        """
        函数级注释：撤销聊天命令
        内部逻辑：恢复消息历史（模拟撤销，实际可能需要删除数据库记录）
        返回值：命令执行结果
        """
        if not self._memento:
            return CommandResult(
                success=False,
                error="无法撤销：没有保存的初始状态"
            )

        # 内部逻辑：恢复历史
        if hasattr(self._request, 'history'):
            self._request.history = self._memento['history']

        self._status = CommandStatus.UNDONE

        return CommandResult(
            success=True,
            data="已恢复消息历史"
        )


class IngestDocumentCommand(Command[Dict[str, Any]]):
    """
    类级注释：文档摄入命令
    内部逻辑：封装文档上传和处理操作
    设计模式：命令模式 - 具体命令
    """

    def __init__(
        self,
        file_path: str,
        ingest_service: Any,
        command_id: Optional[str] = None
    ):
        """
        函数级注释：初始化文档摄入命令
        参数：
            file_path - 文件路径
            ingest_service - 摄入服务
            command_id - 命令 ID
        """
        super().__init__(command_id)
        # 内部变量：文件路径
        self._file_path = file_path
        # 内部变量：摄入服务
        self._ingest_service = ingest_service
        # 内部变量：创建的文档 ID（用于撤销）
        self._created_doc_ids: List[int] = []

    async def execute(self) -> CommandResult:
        """
        函数级注释：执行文档摄入命令
        返回值：命令执行结果
        """
        import time

        self._status = CommandStatus.RUNNING
        start_time = time.time()

        try:
            # 内部逻辑：调用摄入服务
            result = await self._ingest_service.ingest_file(self._file_path)

            # 内部逻辑：记录创建的文档 ID
            if isinstance(result, dict) and 'document_ids' in result:
                self._created_doc_ids = result['document_ids']

            self._duration = time.time() - start_time
            self._status = CommandStatus.SUCCESS
            self._result = result

            return CommandResult(
                success=True,
                data=result,
                duration=self._duration
            )

        except Exception as e:
            self._duration = time.time() - start_time
            self._status = CommandStatus.FAILED
            self._error = str(e)

            return CommandResult(
                success=False,
                error=str(e),
                duration=self._duration
            )

    def can_undo(self) -> bool:
        """
        函数级注释：检查是否可以撤销
        返回值：是否支持撤销
        """
        return len(self._created_doc_ids) > 0

    async def undo(self) -> CommandResult:
        """
        函数级注释：撤销文档摄入命令
        内部逻辑：删除创建的文档记录
        返回值：命令执行结果
        """
        if not self._created_doc_ids:
            return CommandResult(
                success=False,
                error="无法撤销：没有记录的文档 ID"
            )

        try:
            # 内部逻辑：删除文档
            for doc_id in self._created_doc_ids:
                await self._ingest_service.delete_document(doc_id)

            self._status = CommandStatus.UNDONE

            return CommandResult(
                success=True,
                data=f"已删除 {len(self._created_doc_ids)} 个文档"
            )

        except Exception as e:
            return CommandResult(
                success=False,
                error=f"撤销失败: {str(e)}"
            )


# ==================== 装饰器 ====================

def command_audit(invoker: CommandInvoker):
    """
    函数级注释：命令审计装饰器
    内部逻辑：自动将函数调用包装为命令并记录
    设计模式：装饰器模式 + 命令模式
    参数：
        invoker - 命令调用器
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 内部逻辑：创建简单命令包装函数调用
            class FunctionCommand(Command):
                async def execute(self):
                    return await func(*args, **kwargs)

            command = FunctionCommand()
            return await invoker.execute(command)

        return wrapper
    return decorator


# ==================== 全局调用器 ====================

# 内部变量：全局命令调用器
global_command_invoker = CommandInvoker()


# 内部变量：导出所有公共接口
__all__ = [
    # 基础类
    'Command',
    'CommandStatus',
    'CommandResult',
    'CommandLog',
    'MacroCommand',
    'CommandInvoker',
    # 具体命令
    'ChatCommand',
    'IngestDocumentCommand',
    # 装饰器
    'command_audit',
    # 全局调用器
    'global_command_invoker',
]

# ============================================================================
# 新增：命令工厂和业务命令（向后兼容）
# ============================================================================
# 使用示例：
# from app.core.commands.factory import CommandFactory, CommandBuilder
# command = CommandFactory.create_chat_command(request, db, chat_service)
# result = await global_command_invoker.execute(command)
# ============================================================================
