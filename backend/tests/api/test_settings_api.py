"""
Settings API 测试

测试内容:
- 获取设置
- 更新设置
- API Key 管理
"""

import pytest
import pytest_asyncio


class TestSettingsAPI:
    """设置 API 测试"""

    # === 获取设置 ===

    @pytest.mark.asyncio
    async def test_get_settings_requires_auth(self, api_client):
        """测试获取设置需要认证"""
        response = await api_client.get("/api/v1/settings")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_settings_success(self, api_client, db_with_api_key):
        """测试成功获取设置"""
        response = await api_client.get(
            "/api/v1/settings",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "cors_allow_origins" in data
        assert "default_model" in data

    # === 更新设置 ===

    @pytest.mark.asyncio
    async def test_update_settings_requires_auth(self, api_client):
        """测试更新设置需要认证"""
        response = await api_client.patch(
            "/api/v1/settings",
            json={"default_model": "new-model"}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_cors_origins(self, api_client, db_with_api_key):
        """测试更新 CORS 配置"""
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


class TestAPIKeysManagement:
    """API Key 管理测试"""

    @pytest.mark.asyncio
    async def test_list_api_keys_requires_auth(self, api_client):
        """测试列出 API Keys 需要认证"""
        response = await api_client.get("/api/v1/settings/api-keys")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_api_keys_success(self, api_client, db_with_api_key):
        """测试成功列出 API Keys"""
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
        """测试 API Keys 不暴露敏感数据"""
        response = await api_client.get(
            "/api/v1/settings/api-keys",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )

        data = response.json()
        for key in data["keys"]:
            assert "key_hash" not in key
            assert "key" not in key  # 不应该返回明文

    @pytest.mark.asyncio
    async def test_create_api_key_requires_auth(self, api_client):
        """测试创建 API Key 需要认证"""
        response = await api_client.post(
            "/api/v1/settings/api-keys",
            json={"name": "Test Key"}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_api_key_success(self, api_client, db_with_api_key):
        """测试成功创建 API Key"""
        response = await api_client.post(
            "/api/v1/settings/api-keys",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={"name": "Chrome Extension"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "key" in data  # 创建时返回明文
        assert data["key"].startswith("sk-")
        assert data["name"] == "Chrome Extension"

    @pytest.mark.asyncio
    async def test_create_api_key_missing_name(self, api_client, db_with_api_key):
        """测试创建 API Key 缺少名称"""
        response = await api_client.post(
            "/api/v1/settings/api-keys",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={}
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_delete_api_key_requires_auth(self, api_client):
        """测试删除 API Key 需要认证"""
        response = await api_client.delete(
            "/api/v1/settings/api-keys/some-id"
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_api_key_success(self, api_client, db_with_two_api_keys):
        """测试成功删除 API Key"""
        key_to_delete = db_with_two_api_keys[1]

        response = await api_client.delete(
            f"/api/v1/settings/api-keys/{key_to_delete.id}",
            headers={"Authorization": f"Bearer {db_with_two_api_keys[0].key}"}
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_api_key_not_found(self, api_client, db_with_api_key):
        """测试删除不存在的 API Key"""
        response = await api_client.delete(
            "/api/v1/settings/api-keys/nonexistent",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_deleted_key_cannot_authenticate(self, api_client, db_with_two_api_keys, auth_service):
        """测试删除后的 Key 无法认证"""
        key_to_delete = db_with_two_api_keys[1]

        # 删除 Key
        await auth_service.delete_key(key_to_delete.id)

        # 使用已删除的 Key
        response = await api_client.get(
            "/api/v1/sessions",
            headers={"Authorization": f"Bearer {key_to_delete.key}"}
        )

        assert response.status_code == 401
