"""
模型注册 API 测试

测试内容:
- 模型列表
- 添加模型
- 更新模型
- 删除模型
"""

import pytest


class TestModelRegistryAPI:
    """模型注册 API 测试"""

    # === 列出模型 ===

    @pytest.mark.asyncio
    async def test_list_models_requires_auth(self, api_client):
        """测试列出模型需要认证"""
        response = await api_client.get("/api/v1/model-registry")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_models_success(self, api_client, db_with_api_key):
        """测试列出模型成功"""
        response = await api_client.get(
            "/api/v1/model-registry",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    # === 添加模型 ===

    @pytest.mark.asyncio
    async def test_add_model_requires_auth(self, api_client):
        """测试添加模型需要认证"""
        response = await api_client.post(
            "/api/v1/model-registry",
            json={
                "name": "Test Model",
                "model_id": "test-org/test-model"
            }
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_add_model_success(self, api_client, db_with_api_key):
        """测试添加模型成功"""
        response = await api_client.post(
            "/api/v1/model-registry",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={
                "name": "Test Model",
                "model_id": "test-org/test-model",
                "description": "A test model",
                "params_count": "7B",
                "quantization": "4bit"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Model"
        assert data["model_id"] == "test-org/test-model"
        assert data["params_count"] == "7B"

    @pytest.mark.asyncio
    async def test_add_model_invalid_format(self, api_client, db_with_api_key):
        """测试无效的模型 ID 格式"""
        response = await api_client.post(
            "/api/v1/model-registry",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={
                "name": "Test Model",
                "model_id": "invalid-format"
            }
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_add_model_duplicate(self, api_client, db_with_api_key):
        """测试重复添加模型"""
        # 第一次添加
        await api_client.post(
            "/api/v1/model-registry",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={
                "name": "Test Model",
                "model_id": "test-org/test-model"
            }
        )

        # 第二次添加相同模型
        response = await api_client.post(
            "/api/v1/model-registry",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={
                "name": "Another Model",
                "model_id": "test-org/test-model"
            }
        )

        assert response.status_code == 409

    # === 获取模型 ===

    @pytest.mark.asyncio
    async def test_get_model_success(self, api_client, db_with_api_key):
        """测试获取模型详情"""
        # 先添加模型
        add_response = await api_client.post(
            "/api/v1/model-registry",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={
                "name": "Test Model",
                "model_id": "test-org/test-model"
            }
        )
        model_id = add_response.json()["id"]

        # 获取模型
        response = await api_client.get(
            f"/api/v1/model-registry/{model_id}",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Test Model"

    @pytest.mark.asyncio
    async def test_get_model_by_model_id(self, api_client, db_with_api_key):
        """测试通过 ID 获取模型"""
        # 先添加模型
        add_response = await api_client.post(
            "/api/v1/model-registry",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={
                "name": "Test Model",
                "model_id": "test-org/test-model"
            }
        )
        model_id = add_response.json()["id"]

        # 通过 ID 获取
        response = await api_client.get(
            f"/api/v1/model-registry/{model_id}",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )

        assert response.status_code == 200
        assert response.json()["model_id"] == "test-org/test-model"

    # === 更新模型 ===

    @pytest.mark.asyncio
    async def test_update_model_success(self, api_client, db_with_api_key):
        """测试更新模型"""
        # 先添加模型
        add_response = await api_client.post(
            "/api/v1/model-registry",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={
                "name": "Test Model",
                "model_id": "test-org/test-model"
            }
        )
        model_id = add_response.json()["id"]

        # 更新模型
        response = await api_client.patch(
            f"/api/v1/model-registry/{model_id}",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={
                "name": "Updated Model",
                "description": "Updated description"
            }
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Updated Model"

    # === 删除模型 ===

    @pytest.mark.asyncio
    async def test_delete_model_success(self, api_client, db_with_api_key):
        """测试删除模型"""
        # 先添加模型
        add_response = await api_client.post(
            "/api/v1/model-registry",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={
                "name": "Test Model",
                "model_id": "test-org/test-model"
            }
        )
        model_id = add_response.json()["id"]

        # 删除模型
        response = await api_client.delete(
            f"/api/v1/model-registry/{model_id}",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )

        assert response.status_code == 200

        # 验证已删除 (不在默认列表中)
        list_response = await api_client.get(
            "/api/v1/model-registry?active_only=true",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        models = list_response.json()
        assert not any(m["id"] == model_id for m in models)


class TestModelsAPIWithRegistry:
    """模型 API 与注册表集成测试"""

    @pytest.mark.asyncio
    async def test_list_models_includes_registry(self, api_client, db_with_api_key):
        """测试模型列表包含注册表中的模型"""
        response = await api_client.get(
            "/api/v1/models",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # 默认模型应该已初始化
        assert len(data) > 0