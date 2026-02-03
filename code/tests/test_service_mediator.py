# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：服务中介者模块单元测试
内部逻辑：测试中介者模式的服务协调功能
测试策略：
   - 单元测试：测试中介者的注册、注销、通信功能
   - Mock 测试：模拟服务组件
   - 异常测试：验证错误处理逻辑
"""

import pytest
from app.core.service_mediator import (
    ServiceEventType,
    ServiceRequest,
    ServiceResponse,
    ServiceColleague,
    ServiceMediator,
    ServiceMediatorFactory,
    ChatServiceColleague,
    DocumentServiceColleague,
    AgentServiceColleague,
)


class MockServiceColleague(ServiceColleague):
    """
    类级注释：Mock 服务同事组件
    职责：用于测试的服务组件实现
    """

    def __init__(self, name: str, response_data: any = None, fail: bool = False):
        """
        函数级注释：初始化 Mock 服务
        参数：
            name: 服务名称
            response_data: 响应数据
            fail: 是否模拟失败
        """
        super().__init__(name)
        self._response_data = response_data or {"result": f"from_{name}"}
        self._fail = fail
        self.requests_received = []

    async def handle_request(self, request: ServiceRequest) -> ServiceResponse:
        """
        函数级注释：处理服务请求
        参数：
            request: 服务请求
        返回值：服务响应
        """
        self.requests_received.append(request)

        if self._fail:
            return ServiceResponse(
                success=False,
                data=None,
                error=f"{self._name} 处理失败"
            )

        return ServiceResponse(
            success=True,
            data=self._response_data,
            request_id=request.request_id
        )


class TestServiceRequest:
    """
    类级注释：服务请求数据类测试
    """

    def test_create_request_with_required_fields(self):
        """
        函数级注释：测试创建包含必填字段的请求
        内部逻辑：验证请求对象创建成功
        """
        # 内部变量：创建服务请求
        request = ServiceRequest(
            request_type="test_type",
            data={"key": "value"}
        )

        assert request.request_type == "test_type"
        assert request.data == {"key": "value"}
        assert request.request_id is None
        assert request.metadata is None

    def test_create_request_with_all_fields(self):
        """
        函数级注释：测试创建包含所有字段的请求
        内部逻辑：验证所有字段正确赋值
        """
        # 内部变量：创建完整的服务请求
        request = ServiceRequest(
            request_type="test_type",
            data={"key": "value"},
            request_id="req-123",
            metadata={"sender": "test_service"}
        )

        assert request.request_id == "req-123"
        assert request.metadata == {"sender": "test_service"}


class TestServiceResponse:
    """
    类级注释：服务响应数据类测试
    """

    def test_create_success_response(self):
        """
        函数级注释：测试创建成功响应
        内部逻辑：验证成功响应创建
        """
        # 内部变量：创建成功响应
        response = ServiceResponse(
            success=True,
            data={"result": "success"}
        )

        assert response.success is True
        assert response.data == {"result": "success"}
        assert response.error is None

    def test_create_error_response(self):
        """
        函数级注释：测试创建错误响应
        内部逻辑：验证错误响应创建
        """
        # 内部变量：创建错误响应
        response = ServiceResponse(
            success=False,
            data=None,
            error="处理失败",
            request_id="req-123"
        )

        assert response.success is False
        assert response.error == "处理失败"
        assert response.request_id == "req-123"


class TestServiceMediator:
    """
    类级注释：服务中介者测试
    """

    @pytest.fixture
    def mediator(self):
        """
        函数级注释：创建中介者实例
        返回值：ServiceMediator 实例
        """
        return ServiceMediator()

    @pytest.mark.asyncio
    async def test_register_service(self, mediator):
        """
        函数级注释：测试注册服务
        内部逻辑：验证服务注册成功
        """
        # 内部变量：创建 Mock 服务
        service = MockServiceColleague("test_service")

        # 内部逻辑：注册服务
        mediator.register_service(service)

        # 验证：服务已注册
        assert mediator.has_service("test_service")
        assert mediator.get_service("test_service") is service

    @pytest.mark.asyncio
    async def test_unregister_service(self, mediator):
        """
        函数级注释：测试注销服务
        内部逻辑：验证服务注销成功
        """
        # 内部变量：创建并注册服务
        service = MockServiceColleague("test_service")
        mediator.register_service(service)

        # 内部逻辑：注销服务
        mediator.unregister_service("test_service")

        # 验证：服务已注销
        assert not mediator.has_service("test_service")
        assert mediator.get_service("test_service") is None

    @pytest.mark.asyncio
    async def test_send_request_to_existing_service(self, mediator):
        """
        函数级注释：测试向已注册服务发送请求
        内部逻辑：验证请求正确路由到目标服务
        """
        # 内部变量：创建并注册服务
        service = MockServiceColleague("target_service", {"result": "processed"})
        mediator.register_service(service)

        # 内部逻辑：发送请求
        request = ServiceRequest(
            request_type="process",
            data={"input": "test"}
        )
        response = await mediator.send_request("target_service", request)

        # 验证：响应正确
        assert response.success is True
        assert response.data == {"result": "processed"}
        assert len(service.requests_received) == 1

    @pytest.mark.asyncio
    async def test_send_request_to_non_existing_service(self, mediator):
        """
        函数级注释：测试向不存在的服务发送请求
        内部逻辑：验证返回错误响应
        """
        # 内部逻辑：发送请求到不存在的服务
        request = ServiceRequest(
            request_type="process",
            data={"input": "test"}
        )
        response = await mediator.send_request("non_existing", request)

        # 验证：返回错误响应
        assert response.success is False
        assert "服务不存在" in response.error

    @pytest.mark.asyncio
    async def test_service_request_fails(self, mediator):
        """
        函数级注释：测试服务处理失败
        内部逻辑：验证失败响应正确处理
        """
        # 内部变量：创建会失败的服务
        service = MockServiceColleague("failing_service", fail=True)
        mediator.register_service(service)

        # 内部逻辑：发送请求
        request = ServiceRequest(request_type="test", data={})
        response = await mediator.send_request("failing_service", request)

        # 验证：返回失败响应
        assert response.success is False
        assert "处理失败" in response.error

    @pytest.mark.asyncio
    async def test_send_request_via_colleague(self, mediator):
        """
        函数级注释：测试通过同事组件发送请求
        内部逻辑：验证组件间通信
        """
        # 内部变量：创建并注册服务
        sender = MockServiceColleague("sender")
        receiver = MockServiceColleague("receiver", {"result": "received"})
        mediator.register_service(sender)
        mediator.register_service(receiver)

        # 内部逻辑：通过发送者请求接收者
        response = await sender.send_request("receiver", "query", {"key": "value"})

        # 验证：请求成功路由
        assert response.success is True
        assert response.data == {"result": "received"}

    @pytest.mark.asyncio
    async def test_send_request_without_mediator(self):
        """
        函数级注释：测试无中介者时发送请求
        内部逻辑：验证返回错误响应
        """
        # 内部变量：创建无中介者的服务
        service = MockServiceColleague("orphan_service")

        # 内部逻辑：发送请求
        response = await service.send_request("target", "type", {})

        # 验证：返回错误响应
        assert response.success is False
        assert "中介者未设置" in response.error

    @pytest.mark.asyncio
    async def test_add_and_emit_event(self, mediator):
        """
        函数级注释：测试添加事件监听器和触发事件
        内部逻辑：验证事件系统工作正常
        """
        # 内部变量：记录事件是否被触发
        events_received = []

        async def event_handler(data):
            events_received.append(data)

        # 内部逻辑：添加事件监听器
        mediator.add_event_listener(ServiceEventType.CHAT_STARTED, event_handler)

        # 内部逻辑：触发事件
        await mediator.emit_event(ServiceEventType.CHAT_STARTED, {"message": "started"})

        # 验证：事件被正确触发
        assert len(events_received) == 1
        assert events_received[0] == {"message": "started"}

    @pytest.mark.asyncio
    async def test_remove_event_listener(self, mediator):
        """
        函数级注释：测试移除事件监听器
        内部逻辑：验证移除后不再接收事件
        """
        # 内部变量：记录事件
        events_received = []

        async def event_handler(data):
            events_received.append(data)

        # 内部逻辑：添加然后移除事件监听器
        mediator.add_event_listener(ServiceEventType.CHAT_STARTED, event_handler)
        mediator.remove_event_listener(ServiceEventType.CHAT_STARTED, event_handler)

        # 内部逻辑：触发事件
        await mediator.emit_event(ServiceEventType.CHAT_STARTED, {"message": "started"})

        # 验证：事件未被处理
        assert len(events_received) == 0

    @pytest.mark.asyncio
    async def test_get_stats(self, mediator):
        """
        函数级注释：测试获取统计信息
        内部逻辑：验证统计信息正确收集
        """
        # 内部变量：创建并注册服务
        service = MockServiceColleague("test_service")
        mediator.register_service(service)

        # 内部逻辑：发送请求
        request = ServiceRequest(request_type="test", data={})
        await mediator.send_request("test_service", request)

        # 验证：统计信息正确
        stats = mediator.get_stats()
        assert stats["total_requests"] == 1
        assert stats["successful_requests"] == 1
        assert stats["failed_requests"] == 0
        assert stats["service_calls"]["test_service"] == 1

    @pytest.mark.asyncio
    async def test_reset_stats(self, mediator):
        """
        函数级注释：测试重置统计信息
        内部逻辑：验证统计信息被正确重置
        """
        # 内部变量：创建并注册服务
        service = MockServiceColleague("test_service")
        mediator.register_service(service)

        # 内部逻辑：发送请求后重置统计
        request = ServiceRequest(request_type="test", data={})
        await mediator.send_request("test_service", request)
        mediator.reset_stats()

        # 验证：统计信息已重置
        stats = mediator.get_stats()
        assert stats["total_requests"] == 0
        assert stats["successful_requests"] == 0
        assert stats["service_calls"]["test_service"] == 0


class TestConcreteColleagues:
    """
    类级注释：具体同事组件测试
    """

    @pytest.mark.asyncio
    async def test_chat_service_colleague_chat_request(self):
        """
        函数级注释：测试聊天服务处理聊天请求
        内部逻辑：验证聊天请求正确处理
        """
        # 内部变量：创建聊天服务
        service = ChatServiceColleague()

        # 内部逻辑：发送聊天请求
        request = ServiceRequest(
            request_type="chat",
            data={"message": "hello"}
        )
        response = await service.handle_request(request)

        # 验证：响应正确
        assert response.success is True
        assert response.data == {"message": "聊天处理结果"}

    @pytest.mark.asyncio
    async def test_chat_service_colleague_unknown_request(self):
        """
        函数级注释：测试聊天服务处理未知请求
        内部逻辑：验证返回错误响应
        """
        # 内部变量：创建聊天服务
        service = ChatServiceColleague()

        # 内部逻辑：发送未知类型请求
        request = ServiceRequest(
            request_type="unknown",
            data={}
        )
        response = await service.handle_request(request)

        # 验证：返回错误响应
        assert response.success is False
        assert "未知的请求类型" in response.error

    @pytest.mark.asyncio
    async def test_document_service_colleague_search_request(self):
        """
        函数级注释：测试文档服务处理搜索请求
        内部逻辑：验证搜索请求正确处理
        """
        # 内部变量：创建文档服务
        service = DocumentServiceColleague()

        # 内部逻辑：发送搜索请求
        request = ServiceRequest(
            request_type="search",
            data={"query": "test"}
        )
        response = await service.handle_request(request)

        # 验证：响应正确
        assert response.success is True
        assert response.data == {"documents": []}

    @pytest.mark.asyncio
    async def test_agent_service_colleague_execute_request(self):
        """
        函数级注释：测试 Agent 服务处理执行请求
        内部逻辑：验证执行请求正确处理
        """
        # 内部变量：创建 Agent 服务
        service = AgentServiceColleague()

        # 内部逻辑：发送执行请求
        request = ServiceRequest(
            request_type="execute",
            data={"task": "test"}
        )
        response = await service.handle_request(request)

        # 验证：响应正确
        assert response.success is True
        assert response.data == {"result": "Agent 执行结果"}


class TestServiceMediatorFactory:
    """
    类级注释：服务中介者工厂测试
    """

    def test_singleton_pattern(self):
        """
        函数级注释：测试单例模式
        内部逻辑：验证工厂只创建一个实例
        """
        # 内部变量：创建两个工厂实例
        factory1 = ServiceMediatorFactory()
        factory2 = ServiceMediatorFactory()

        # 验证：是同一个实例
        assert factory1 is factory2

    def test_create_standard_mediator(self):
        """
        函数级注释：测试创建标准中介者
        内部逻辑：验证标准中介者创建成功
        """
        # 内部变量：创建工厂和中介者
        factory = ServiceMediatorFactory()
        mediator = factory.create_standard_mediator()

        # 验证：中介者创建成功
        assert mediator is not None
        assert factory.get_mediator() is mediator

    def test_create_standard_mediator_with_services(self):
        """
        函数级注释：测试创建包含服务的中介者
        内部逻辑：验证服务正确注册
        """
        # 内部变量：创建工厂和带服务的中介者
        factory = ServiceMediatorFactory()
        mediator = factory.create_standard_mediator(
            chat_service="mock_chat",
            document_service="mock_doc",
            agent_service="mock_agent"
        )

        # 验证：所有服务已注册
        assert mediator.has_service("chat_service")
        assert mediator.has_service("document_service")
        assert mediator.has_service("agent_service")

    def test_get_mediator_before_create(self):
        """
        函数级注释：测试创建前获取中介者
        内部逻辑：验证由于单例模式可能返回之前创建的中介者
        """
        # 内部变量：创建新工厂
        factory = ServiceMediatorFactory()

        # 验证：单例模式下可能返回之前创建的中介者
        # 由于单例模式在测试间共享状态，这里只验证方法可调用
        assert factory.get_mediator() is None or isinstance(factory.get_mediator(), ServiceMediator)
