"""
Chat API 测试

测试内容:
- 认证要求
- 请求验证
- 响应格式
"""

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import json


class TestChatAPI:
    """聊天 API 测试"""

    @pytest.mark.asyncio
    async def test_chat_requires_auth(self, api_client, db_with_session):
        """测试聊天接口需要认证"""
        response = await api_client.post(
            "/api/v1/chat",
            json={
                "session_id": db_with_session.id,
                "message": "你好"
            }
        )

        assert response.status_code == 401
        assert "Missing Authorization" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_chat_with_invalid_key(self, api_client, db_with_session):
        """测试无效 API Key"""
        response = await api_client.post(
            "/api/v1/chat",
            headers={"Authorization": "Bearer sk-invalid"},
            json={
                "session_id": db_with_session.id,
                "message": "你好"
            }
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_chat_with_valid_key(self, api_client, db_with_api_key, db_with_session):
        """测试有效 API Key"""
        response = await api_client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={
                "session_id": db_with_session.id,
                "message": "你好"
            }
        )

        # 应该返回 200 或其他业务错误，不应该是 401
        assert response.status_code != 401

    @pytest.mark.asyncio
    async def test_chat_missing_session_id(self, api_client, db_with_api_key):
        """测试缺少 session_id"""
        response = await api_client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={
                "message": "你好"
            }
        )

        assert response.status_code == 422  # 验证错误

    @pytest.mark.asyncio
    async def test_chat_missing_message(self, api_client, db_with_api_key, db_with_session):
        """测试缺少 message"""
        response = await api_client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={
                "session_id": db_with_session.id
            }
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_chat_empty_message(self, api_client, db_with_api_key, db_with_session):
        """测试空 message"""
        response = await api_client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={
                "session_id": db_with_session.id,
                "message": ""
            }
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_chat_session_not_found(self, api_client, db_with_api_key):
        """测试会话不存在"""
        response = await api_client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={
                "session_id": "nonexistent-session",
                "message": "你好"
            }
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_chat_wrong_scheme(self, api_client, db_with_api_key, db_with_session):
        """测试错误的认证方式"""
        response = await api_client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Basic {db_with_api_key.key}"},
            json={
                "session_id": db_with_session.id,
                "message": "你好"
            }
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_chat_with_temperature(self, api_client, db_with_api_key, db_with_session):
        """测试带 temperature 参数"""
        response = await api_client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={
                "session_id": db_with_session.id,
                "message": "你好",
                "temperature": 1.0
            }
        )

        # 应该接受参数
        assert response.status_code != 422

    @pytest.mark.asyncio
    async def test_chat_with_max_tokens(self, api_client, db_with_api_key, db_with_session):
        """测试带 max_tokens 参数"""
        response = await api_client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={
                "session_id": db_with_session.id,
                "message": "你好",
                "max_tokens": 100
            }
        )

        assert response.status_code != 422

    @pytest.mark.asyncio
    async def test_chat_with_system_prompt(self, api_client, db_with_api_key, db_with_session):
        """测试带 system_prompt 参数"""
        response = await api_client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={
                "session_id": db_with_session.id,
                "message": "你好",
                "system_prompt": "你是一个有帮助的助手"
            }
        )

        assert response.status_code != 422
