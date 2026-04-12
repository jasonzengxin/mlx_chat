"""
Settings API 测试

测试内容:
- 获取设置
- 更新设置
- API Key 管理
- 远程 Provider 管理 (CRUD)
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch


class TestSettingsAPI:
    """设置 API 测试"""

    @pytest.mark.asyncio
    async def test_get_settings_requires_auth(self, api_client):
        response = await api_client.get("/api/v1/settings")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_settings_success(self, api_client, db_with_api_key):
        response = await api_client.get(
            "/api/v1/settings",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "cors_allow_origins" in data
        assert "default_model" in data

    @pytest.mark.asyncio
    async def test_update_settings_requires_auth(self, api_client):
        response = await api_client.patch(
            "/api/v1/settings",
            json={"default_model": "new-model"}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_cors_origins(self, api_client, db_with_api_key):
        response = await api_client.patch(
            "/api/v1/settings",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={
                "cors_allow_origins": [
                    "http://localhost:3000",
                    "chrome-extension://abc123"
                ]
            }
        )
        assert response.status_code == 200


class TestRemoteProvidersAPI:
    """远程 Provider CRUD 测试"""

    @pytest.mark.asyncio
    async def test_list_providers_requires_auth(self, api_client):
        response = await api_client.get("/api/v1/settings/remote/providers")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_providers_empty(self, api_client, db_with_api_key):
        response = await api_client.get(
            "/api/v1/settings/remote/providers",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_create_provider_success(self, api_client, db_with_api_key):
        response = await api_client.post(
            "/api/v1/settings/remote/providers",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={
                "name": "SiliconFlow",
                "provider_type": "siliconflow",
                "base_url": "https://api.siliconflow.cn/v1",
                "api_key": "sk-test-key",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "SiliconFlow"
        assert data["provider_type"] == "siliconflow"
        assert data["base_url"] == "https://api.siliconflow.cn/v1"
        assert data["has_api_key"] is True
        assert "api_key" not in data

    @pytest.mark.asyncio
    async def test_create_provider_duplicate_name(self, api_client, db_with_api_key):
        headers = {"Authorization": f"Bearer {db_with_api_key.key}"}
        await api_client.post(
            "/api/v1/settings/remote/providers",
            headers=headers,
            json={"name": "TestProvider", "base_url": "https://example.com"}
        )
        response = await api_client.post(
            "/api/v1/settings/remote/providers",
            headers=headers,
            json={"name": "TestProvider", "base_url": "https://example.com"}
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_update_provider(self, api_client, db_with_api_key):
        headers = {"Authorization": f"Bearer {db_with_api_key.key}"}
        create_resp = await api_client.post(
            "/api/v1/settings/remote/providers",
            headers=headers,
            json={"name": "P1", "base_url": "https://old.example.com/v1/"}
        )
        pid = create_resp.json()["id"]

        response = await api_client.patch(
            f"/api/v1/settings/remote/providers/{pid}",
            headers=headers,
            json={"base_url": "https://new.example.com/v1"}
        )
        assert response.status_code == 200
        assert response.json()["base_url"] == "https://new.example.com/v1"

    @pytest.mark.asyncio
    async def test_update_provider_trailing_slash_removed(self, api_client, db_with_api_key):
        headers = {"Authorization": f"Bearer {db_with_api_key.key}"}
        create_resp = await api_client.post(
            "/api/v1/settings/remote/providers",
            headers=headers,
            json={"name": "Slash", "base_url": "https://api.openai.com/v1"}
        )
        pid = create_resp.json()["id"]

        response = await api_client.patch(
            f"/api/v1/settings/remote/providers/{pid}",
            headers=headers,
            json={"base_url": "https://api.openai.com/v1/"}
        )
        assert response.json()["base_url"] == "https://api.openai.com/v1"

    @pytest.mark.asyncio
    async def test_delete_provider(self, api_client, db_with_api_key):
        headers = {"Authorization": f"Bearer {db_with_api_key.key}"}
        create_resp = await api_client.post(
            "/api/v1/settings/remote/providers",
            headers=headers,
            json={"name": "ToDelete", "base_url": "https://example.com"}
        )
        pid = create_resp.json()["id"]

        del_resp = await api_client.delete(
            f"/api/v1/settings/remote/providers/{pid}",
            headers=headers,
        )
        assert del_resp.status_code == 200

        list_resp = await api_client.get(
            "/api/v1/settings/remote/providers",
            headers=headers,
        )
        names = [p["name"] for p in list_resp.json()]
        assert "ToDelete" not in names

    @pytest.mark.asyncio
    async def test_validate_provider_success(self, api_client, db_with_api_key):
        headers = {"Authorization": f"Bearer {db_with_api_key.key}"}
        create_resp = await api_client.post(
            "/api/v1/settings/remote/providers",
            headers=headers,
            json={
                "name": "Validate",
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": "sk-openrouter-test",
            }
        )
        pid = create_resp.json()["id"]

        with patch("backend.routers.settings.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": [{"id": "openai/gpt-4o-mini"}]}
            mock_response.text = ""
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            response = await api_client.post(
                f"/api/v1/settings/remote/providers/{pid}/validate",
                headers=headers,
                json={},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["models_count"] == 1

    @pytest.mark.asyncio
    async def test_validate_provider_invalid_key(self, api_client, db_with_api_key):
        headers = {"Authorization": f"Bearer {db_with_api_key.key}"}
        create_resp = await api_client.post(
            "/api/v1/settings/remote/providers",
            headers=headers,
            json={
                "name": "BadKey",
                "base_url": "https://api.siliconflow.cn/v1",
                "api_key": "bad-key",
            }
        )
        pid = create_resp.json()["id"]

        with patch("backend.routers.settings.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_response.json.return_value = {"error": {"message": "Invalid API key"}}
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            response = await api_client.post(
                f"/api/v1/settings/remote/providers/{pid}/validate",
                headers=headers,
                json={},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["status_code"] == 401

    @pytest.mark.asyncio
    async def test_legacy_get_remote(self, api_client, db_with_api_key):
        """Legacy GET /remote still works"""
        response = await api_client.get(
            "/api/v1/settings/remote",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "providers" in data


class TestAPIKeysManagement:
    """API Key 管理测试"""

    @pytest.mark.asyncio
    async def test_list_api_keys_requires_auth(self, api_client):
        response = await api_client.get("/api/v1/settings/api-keys")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_api_keys_success(self, api_client, db_with_api_key):
        response = await api_client.get(
            "/api/v1/settings/api-keys",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "keys" in data
        assert isinstance(data["keys"], list)

    @pytest.mark.asyncio
    async def test_list_api_keys_no_sensitive_data(self, api_client, db_with_api_key):
        response = await api_client.get(
            "/api/v1/settings/api-keys",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        data = response.json()
        for key in data["keys"]:
            assert "key_hash" not in key
            assert "key" not in key

    @pytest.mark.asyncio
    async def test_create_api_key_requires_auth(self, api_client):
        response = await api_client.post(
            "/api/v1/settings/api-keys",
            json={"name": "Test Key"}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_api_key_success(self, api_client, db_with_api_key):
        response = await api_client.post(
            "/api/v1/settings/api-keys",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={"name": "Chrome Extension"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "key" in data
        assert data["key"].startswith("sk-")
        assert data["name"] == "Chrome Extension"

    @pytest.mark.asyncio
    async def test_create_api_key_missing_name(self, api_client, db_with_api_key):
        response = await api_client.post(
            "/api/v1/settings/api-keys",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={}
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_delete_api_key_requires_auth(self, api_client):
        response = await api_client.delete(
            "/api/v1/settings/api-keys/some-id"
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_api_key_success(self, api_client, db_with_two_api_keys):
        key_to_delete = db_with_two_api_keys[1]
        response = await api_client.delete(
            f"/api/v1/settings/api-keys/{key_to_delete.id}",
            headers={"Authorization": f"Bearer {db_with_two_api_keys[0].key}"}
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_api_key_not_found(self, api_client, db_with_api_key):
        response = await api_client.delete(
            "/api/v1/settings/api-keys/nonexistent",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_deleted_key_cannot_authenticate(self, api_client, db_with_two_api_keys, auth_service):
        key_to_delete = db_with_two_api_keys[1]
        await auth_service.delete_key(key_to_delete.id)
        response = await api_client.get(
            "/api/v1/sessions",
            headers={"Authorization": f"Bearer {key_to_delete.key}"}
        )
        assert response.status_code == 401
