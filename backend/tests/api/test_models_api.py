"""
Models API 测试

测试内容:
- 获取模型列表
- 加载模型
- 获取当前模型
"""

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock


class TestModelsAPI:
    """模型 API 测试"""

    # === 获取模型列表 ===

    @pytest.mark.asyncio
    async def test_list_models_requires_auth(self, api_client):
        """测试获取模型列表需要认证"""
        response = await api_client.get("/api/v1/models")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_models_success(self, api_client, db_with_api_key):
        """测试成功获取模型列表"""
        response = await api_client.get(
            "/api/v1/models",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    # === 加载模型 ===

    @pytest.mark.asyncio
    async def test_load_model_requires_auth(self, api_client):
        """测试加载模型需要认证"""
        response = await api_client.post(
            "/api/v1/models/load",
            json={"model": "test-model"}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_load_model_missing_model(self, api_client, db_with_api_key):
        """测试缺少 model 参数"""
        response = await api_client.post(
            "/api/v1/models/load",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={}
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_load_model_success(self, api_client, db_with_api_key):
        """测试成功加载模型"""
        with patch("backend.services.mlx_service.mlx_lm.load") as mock_load:
            mock_load.return_value = (MagicMock(), MagicMock())

            response = await api_client.post(
                "/api/v1/models/load",
                headers={"Authorization": f"Bearer {db_with_api_key.key}"},
                json={"model": "mlx-community/Qwen3.5-27B"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "loaded"
            assert data["model"] == "mlx-community/Qwen3.5-27B"
            assert "load_time_seconds" in data

    @pytest.mark.asyncio
    async def test_load_model_not_found(self, api_client, db_with_api_key):
        """测试加载不存在的模型"""
        with patch("backend.services.mlx_service.mlx_lm.load") as mock_load:
            mock_load.side_effect = Exception("Model not found")

            response = await api_client.post(
                "/api/v1/models/load",
                headers={"Authorization": f"Bearer {db_with_api_key.key}"},
                json={"model": "nonexistent-model"}
            )

            assert response.status_code == 200  # 返回 200 但 status 为 error
            data = response.json()
            assert data["status"] == "error"

    # === 获取当前模型 ===

    @pytest.mark.asyncio
    async def test_get_current_model_requires_auth(self, api_client):
        """测试获取当前模型需要认证"""
        response = await api_client.get("/api/v1/models/current")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_model_none(self, api_client, db_with_api_key):
        """测试无模型时返回 null"""
        response = await api_client.get(
            "/api/v1/models/current",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["model"] is None

    @pytest.mark.asyncio
    async def test_get_current_model_loaded(self, api_client, db_with_api_key):
        """测试有模型时返回模型名"""
        with patch("backend.services.mlx_service.mlx_lm.load") as mock_load:
            mock_load.return_value = (MagicMock(), MagicMock())

            # 先加载模型
            await api_client.post(
                "/api/v1/models/load",
                headers={"Authorization": f"Bearer {db_with_api_key.key}"},
                json={"model": "test-model"}
            )

            # 获取当前模型
            response = await api_client.get(
                "/api/v1/models/current",
                headers={"Authorization": f"Bearer {db_with_api_key.key}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["model"] == "test-model"
