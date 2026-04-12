"""
远程模型端到端测试

测试完整的远程模型调用流程:
1. 创建远程 Provider (DB-backed)
2. 添加远程模型 (从 Provider 复制 credentials)
3. 创建使用远程模型的 session
4. 发送聊天消息 (mock 远程 API)
"""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx


class TestRemoteModelE2E:
    """远程模型端到端测试"""

    @pytest.mark.asyncio
    async def test_remote_model_chat_flow(self, api_client, db_with_api_key):
        """测试完整的远程模型聊天流程"""
        headers = {"Authorization": f"Bearer {db_with_api_key.key}"}

        # Step 1: 创建 Provider
        provider_resp = await api_client.post(
            "/api/v1/settings/remote/providers",
            headers=headers,
            json={
                "name": "TestProvider",
                "provider_type": "custom",
                "base_url": "https://api.test-provider.com/v1",
                "api_key": "test-api-key-12345",
            },
        )
        assert provider_resp.status_code == 200
        provider_id = provider_resp.json()["id"]

        # Step 2: 添加远程模型 (从 Provider 复制 credentials)
        model_response = await api_client.post(
            "/api/v1/model-registry",
            headers=headers,
            json={
                "name": "Test GPT Model",
                "model_id": "test-gpt-4",
                "description": "Test remote model",
                "model_type": "remote",
                "endpoint": "/chat/completions",
                "provider_id": provider_id,
            },
        )
        assert model_response.status_code == 200
        model_data = model_response.json()
        assert model_data["model_type"] == "remote"
        assert model_data["remote_base_url"] == "https://api.test-provider.com/v1"
        assert model_data["has_remote_api_key"] is True

        # Step 3: 创建 session 使用远程模型
        session_response = await api_client.post(
            "/api/v1/sessions",
            headers=headers,
            json={"name": "Remote Chat Session", "model": "test-gpt-4"},
        )
        assert session_response.status_code == 201
        session_id = session_response.json()["id"]

        # Step 4: Mock 远程 API 并发送聊天消息
        async def mock_stream_response(*args, **kwargs):
            yield f'data: {json.dumps({"choices": [{"delta": {"content": "Hello! "}}]})}\n\n'
            yield f'data: {json.dumps({"choices": [{"delta": {"content": "Response."}}]})}\n\n'
            yield "data: [DONE]\n\n"

        with patch("backend.routers.chat.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.aiter_lines = mock_stream_response
            mock_response.raise_for_status = MagicMock()
            mock_client.stream = MagicMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            chat_response = await api_client.post(
                "/api/v1/chat",
                headers=headers,
                json={"session_id": session_id, "message": "Hello, can you help me?"},
            )
            assert chat_response.status_code == 200
            assert chat_response.headers["content-type"] == "text/event-stream; charset=utf-8"

    @pytest.mark.asyncio
    async def test_remote_model_chat_without_config(self, api_client, db_with_api_key):
        """测试远程模型未配置 credentials 时返回错误"""
        headers = {"Authorization": f"Bearer {db_with_api_key.key}"}

        # Add remote model without provider (no credentials)
        model_response = await api_client.post(
            "/api/v1/model-registry",
            headers=headers,
            json={
                "name": "Unconfigured Remote",
                "model_id": "unconfigured-model-2",
                "model_type": "remote",
            },
        )
        assert model_response.status_code == 200

        session_response = await api_client.post(
            "/api/v1/sessions",
            headers=headers,
            json={"name": "Test Session", "model": "unconfigured-model-2"},
        )
        session_id = session_response.json()["id"]

        chat_response = await api_client.post(
            "/api/v1/chat",
            headers=headers,
            json={"session_id": session_id, "message": "Hello"},
        )
        assert chat_response.status_code == 200
        content = chat_response.text
        assert "event: error" in content or "missing credentials" in content.lower()

    @pytest.mark.asyncio
    async def test_local_model_still_works(self, api_client, db_with_api_key):
        """测试本地模型仍然正常工作"""
        session_response = await api_client.post(
            "/api/v1/sessions",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={"name": "Local Chat Session", "model": "test-local-model-2"},
        )
        assert session_response.status_code == 201


class TestModelTypeRouting:
    """模型类型路由测试"""

    @pytest.mark.asyncio
    async def test_local_model_routing(self, api_client, db_with_api_key):
        headers = {"Authorization": f"Bearer {db_with_api_key.key}"}
        add_response = await api_client.post(
            "/api/v1/model-registry",
            headers=headers,
            json={
                "name": "Local Test Model",
                "model_id": "org/local-test-model-2",
                "model_type": "local",
            },
        )
        assert add_response.status_code == 200
        model_id = add_response.json()["id"]

        model_info = await api_client.get(
            f"/api/v1/model-registry/{model_id}", headers=headers
        )
        assert model_info.status_code == 200
        assert model_info.json()["model_type"] == "local"

    @pytest.mark.asyncio
    async def test_remote_model_routing(self, api_client, db_with_api_key):
        headers = {"Authorization": f"Bearer {db_with_api_key.key}"}

        # Create provider first
        provider_resp = await api_client.post(
            "/api/v1/settings/remote/providers",
            headers=headers,
            json={
                "name": "RoutingTest",
                "base_url": "https://api.test.com/v1",
                "api_key": "test-key",
            },
        )
        provider_id = provider_resp.json()["id"]

        model_response = await api_client.post(
            "/api/v1/model-registry",
            headers=headers,
            json={
                "name": "Remote Test Model",
                "model_id": "remote-test-model-2",
                "model_type": "remote",
                "endpoint": "/chat/completions",
                "provider_id": provider_id,
            },
        )
        assert model_response.status_code == 200
        model_id = model_response.json()["id"]

        model_info = await api_client.get(
            f"/api/v1/model-registry/{model_id}", headers=headers
        )
        assert model_info.status_code == 200
        assert model_info.json()["model_type"] == "remote"
        assert model_info.json()["endpoint"] == "/chat/completions"


class TestRemoteSettingsSecurity:
    """远程设置安全测试"""

    @pytest.mark.asyncio
    async def test_api_key_not_exposed_in_provider(self, api_client, db_with_api_key):
        """Provider listing never exposes the actual api_key"""
        headers = {"Authorization": f"Bearer {db_with_api_key.key}"}
        await api_client.post(
            "/api/v1/settings/remote/providers",
            headers=headers,
            json={
                "name": "SecretProvider",
                "base_url": "https://api.test.com/v1",
                "api_key": "super-secret-key-12345",
            },
        )

        response = await api_client.get(
            "/api/v1/settings/remote/providers", headers=headers
        )
        providers = response.json()
        p = next(x for x in providers if x["name"] == "SecretProvider")
        assert p["has_api_key"] is True
        assert "api_key" not in p

    @pytest.mark.asyncio
    async def test_model_api_key_not_exposed(self, api_client, db_with_api_key):
        """Model listing never exposes the remote_api_key"""
        headers = {"Authorization": f"Bearer {db_with_api_key.key}"}
        # Create provider and model
        pr = await api_client.post(
            "/api/v1/settings/remote/providers",
            headers=headers,
            json={
                "name": "KeyTest",
                "base_url": "https://api.test.com/v1",
                "api_key": "super-secret-key",
            },
        )
        await api_client.post(
            "/api/v1/model-registry",
            headers=headers,
            json={
                "name": "KeyModel",
                "model_id": "key-model-test",
                "model_type": "remote",
                "provider_id": pr.json()["id"],
            },
        )

        list_resp = await api_client.get("/api/v1/model-registry", headers=headers)
        models = list_resp.json()
        remote_model = next(m for m in models if m["model_id"] == "key-model-test")
        assert remote_model.get("has_remote_api_key") is True
        assert "remote_api_key" not in remote_model

    @pytest.mark.asyncio
    async def test_delete_provider_doesnt_affect_model(self, api_client, db_with_api_key):
        """Deleting a provider doesn't affect models that were created from it"""
        headers = {"Authorization": f"Bearer {db_with_api_key.key}"}

        pr = await api_client.post(
            "/api/v1/settings/remote/providers",
            headers=headers,
            json={
                "name": "Ephemeral",
                "base_url": "https://api.test.com/v1",
                "api_key": "sk-ephemeral",
            },
        )
        pid = pr.json()["id"]

        await api_client.post(
            "/api/v1/model-registry",
            headers=headers,
            json={
                "name": "Survivor",
                "model_id": "survive-model",
                "model_type": "remote",
                "provider_id": pid,
            },
        )

        # Delete provider
        await api_client.delete(
            f"/api/v1/settings/remote/providers/{pid}", headers=headers
        )

        # Model still has credentials
        model_resp = await api_client.get(
            "/api/v1/model-registry/survive-model", headers=headers
        )
        assert model_resp.status_code == 200
        model = model_resp.json()
        assert model["remote_base_url"] == "https://api.test.com/v1"
        assert model["has_remote_api_key"] is True
