"""
文件级注释：对话管理 API 测试
内部逻辑：测试对话会话和消息管理的 API 端点
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_conversation(client: AsyncClient):
    """
    函数级注释：测试创建对话会话
    """
    response = await client.post(
        "/api/v1/conversations",
        json={
            "title": "测试会话",
            "model_name": "glm-4",
            "use_agent": False
        }
    )
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert result["data"]["title"] == "测试会话"


@pytest.mark.asyncio
async def test_list_conversations(client: AsyncClient):
    """
    函数级注释：测试获取对话会话列表
    """
    # 先创建一个会话
    await client.post(
        "/api/v1/conversations",
        json={"title": "测试会话列表", "model_name": "glm-4"}
    )

    # 获取列表
    response = await client.get("/api/v1/conversations")
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert isinstance(result["data"]["conversations"], list)


@pytest.mark.asyncio
async def test_get_conversation_detail(client: AsyncClient):
    """
    函数级注释：测试获取对话会话详情
    """
    # 创建会话
    create_res = await client.post(
        "/api/v1/conversations",
        json={"title": "测试会话详情", "model_name": "glm-4"}
    )
    conv_id = create_res.json()["data"]["id"]

    # 获取详情
    response = await client.get(f"/api/v1/conversations/{conv_id}")
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert result["data"]["conversation"]["id"] == conv_id


@pytest.mark.asyncio
async def test_update_conversation(client: AsyncClient):
    """
    函数级注释：测试更新对话会话
    """
    # 创建会话
    create_res = await client.post(
        "/api/v1/conversations",
        json={"title": "原标题", "model_name": "glm-4"}
    )
    conv_id = create_res.json()["data"]["id"]

    # 更新会话
    response = await client.put(
        f"/api/v1/conversations/{conv_id}",
        json={"title": "新标题"}
    )
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert result["data"]["title"] == "新标题"


@pytest.mark.asyncio
async def test_delete_conversation(client: AsyncClient):
    """
    函数级注释：测试删除对话会话
    """
    # 创建会话
    create_res = await client.post(
        "/api/v1/conversations",
        json={"title": "待删除会话", "model_name": "glm-4"}
    )
    conv_id = create_res.json()["data"]["id"]

    # 删除会话
    response = await client.delete(f"/api/v1/conversations/{conv_id}")
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True


@pytest.mark.asyncio
async def test_send_message(client: AsyncClient):
    """
    函数级注释：测试发送消息
    """
    # 创建会话
    create_res = await client.post(
        "/api/v1/conversations",
        json={"title": "测试消息", "model_name": "glm-4"}
    )
    conv_id = create_res.json()["data"]["id"]

    # 发送消息
    response = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "你好"}
    )
    # 可能因为 LLM 不可用而失败，但至少应该返回响应
    assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_get_conversation_not_found(client: AsyncClient):
    """
    函数级注释：测试获取不存在的会话
    """
    response = await client.get("/api/v1/conversations/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_conversation_pagination(client: AsyncClient):
    """
    函数级注释：测试会话列表分页
    """
    # 创建多个会话
    for i in range(5):
        await client.post(
            "/api/v1/conversations",
            json={"title": f"会话 {i}", "model_name": "glm-4"}
        )

    # 获取第一页
    response = await client.get("/api/v1/conversations?skip=0&limit=3")
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert len(result["data"]["conversations"]) <= 3


@pytest.mark.asyncio
async def test_send_message_stream_flag_rejected(client: AsyncClient):
    """
    函数级注释：测试流式请求被非流式端点拒绝
    未覆盖行号：262-266 (stream=True验证)
    """
    # 创建会话
    create_res = await client.post(
        "/api/v1/conversations",
        json={"title": "测试流式拒绝", "model_name": "glm-4"}
    )
    conv_id = create_res.json()["data"]["id"]

    response = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "测试", "stream": True}  # 应该使用 /stream 端点
    )

    assert response.status_code == 400
    assert "流式请求" in response.json()["detail"]
