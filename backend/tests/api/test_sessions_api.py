"""
Sessions API 测试

测试内容:
- 会话 CRUD
- 认证要求
- 响应格式
"""

import pytest
import pytest_asyncio


class TestSessionsAPI:
    """会话 API 测试"""

    # === 创建会话 ===

    @pytest.mark.asyncio
    async def test_create_session_success(self, api_client, db_with_api_key):
        """测试成功创建会话"""
        response = await api_client.post(
            "/api/v1/sessions",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={"name": "新会话"}
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == "新会话"

    @pytest.mark.asyncio
    async def test_create_session_with_all_params(self, api_client, db_with_api_key):
        """测试带完整参数创建会话"""
        response = await api_client.post(
            "/api/v1/sessions",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={
                "name": "完整参数会话",
                "model": "qwen3.5",
                "temperature": 1.0,
                "max_tokens": 8192,
                "system_prompt": "你是一个诗人"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["model"] == "qwen3.5"
        assert data["temperature"] == 1.0
        assert data["max_tokens"] == 8192
        assert data["system_prompt"] == "你是一个诗人"

    @pytest.mark.asyncio
    async def test_create_session_default_params(self, api_client, db_with_api_key):
        """测试使用默认参数创建会话"""
        response = await api_client.post(
            "/api/v1/sessions",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["temperature"] == 0.7
        assert data["max_tokens"] == 4096

    @pytest.mark.asyncio
    async def test_create_session_requires_auth(self, api_client):
        """测试创建会话需要认证"""
        response = await api_client.post(
            "/api/v1/sessions",
            json={"name": "新会话"}
        )

        assert response.status_code == 401

    # === 列出会话 ===

    @pytest.mark.asyncio
    async def test_list_sessions_success(self, api_client, db_with_api_key, db_with_sessions):
        """测试成功列出会话"""
        response = await api_client.get(
            "/api/v1/sessions",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3

    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, api_client, db_with_api_key):
        """测试空会话列表"""
        response = await api_client.get(
            "/api/v1/sessions",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_sessions_requires_auth(self, api_client):
        """测试列出会话需要认证"""
        response = await api_client.get("/api/v1/sessions")

        assert response.status_code == 401

    # === 获取会话 ===

    @pytest.mark.asyncio
    async def test_get_session_success(self, api_client, db_with_api_key, db_with_session):
        """测试成功获取会话"""
        response = await api_client.get(
            f"/api/v1/sessions/{db_with_session.id}",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == db_with_session.id

    @pytest.mark.asyncio
    async def test_get_session_with_messages(self, api_client, db_with_api_key, db_with_messages):
        """测试获取会话包含消息"""
        response = await api_client.get(
            f"/api/v1/sessions/{db_with_messages.id}",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert len(data["messages"]) == 5

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, api_client, db_with_api_key):
        """测试获取不存在的会话"""
        response = await api_client.get(
            "/api/v1/sessions/nonexistent",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_session_requires_auth(self, api_client, db_with_session):
        """测试获取会话需要认证"""
        response = await api_client.get(f"/api/v1/sessions/{db_with_session.id}")

        assert response.status_code == 401

    # === 更新会话 ===

    @pytest.mark.asyncio
    async def test_update_session_success(self, api_client, db_with_api_key, db_with_session):
        """测试成功更新会话"""
        response = await api_client.patch(
            f"/api/v1/sessions/{db_with_session.id}",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={"name": "新名称"}
        )

        assert response.status_code == 200
        assert response.json()["name"] == "新名称"

    @pytest.mark.asyncio
    async def test_update_session_multiple_fields(self, api_client, db_with_api_key, db_with_session):
        """测试更新多个字段"""
        response = await api_client.patch(
            f"/api/v1/sessions/{db_with_session.id}",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={
                "name": "新名称",
                "model": "new-model",
                "temperature": 1.0
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "新名称"
        assert data["model"] == "new-model"
        assert data["temperature"] == 1.0

    @pytest.mark.asyncio
    async def test_update_session_not_found(self, api_client, db_with_api_key):
        """测试更新不存在的会话"""
        response = await api_client.patch(
            "/api/v1/sessions/nonexistent",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={"name": "新名称"}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_session_requires_auth(self, api_client, db_with_session):
        """测试更新会话需要认证"""
        response = await api_client.patch(
            f"/api/v1/sessions/{db_with_session.id}",
            json={"name": "新名称"}
        )

        assert response.status_code == 401

    # === 删除会话 ===

    @pytest.mark.asyncio
    async def test_delete_session_success(self, api_client, db_with_api_key, db_with_session):
        """测试成功删除会话"""
        response = await api_client.delete(
            f"/api/v1/sessions/{db_with_session.id}",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_session_not_found(self, api_client, db_with_api_key):
        """测试删除不存在的会话"""
        response = await api_client.delete(
            "/api/v1/sessions/nonexistent",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_session_requires_auth(self, api_client, db_with_session):
        """测试删除会话需要认证"""
        response = await api_client.delete(f"/api/v1/sessions/{db_with_session.id}")

        assert response.status_code == 401
