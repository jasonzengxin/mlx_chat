"""
OpenAI 兼容 API 测试

测试内容:
- chat/completions 端点
- 流式和非流式响应
- OpenAI 格式兼容
"""

import pytest
from unittest.mock import MagicMock, patch


class TestChatCompletionsAPI:
    """Chat Completions API 测试"""

    # === 认证测试 ===

    @pytest.mark.asyncio
    async def test_chat_completions_requires_auth(self, api_client):
        """测试 chat/completions 需要认证"""
        response = await api_client.post(
            "/v1/chat/completions",
            json={
                "model": "test-model",
                "messages": [{"role": "user", "content": "你好"}]
            }
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_chat_completions_invalid_key(self, api_client):
        """测试无效 API Key"""
        response = await api_client.post(
            "/v1/chat/completions",
            headers={"Authorization": "Bearer invalid-key"},
            json={
                "model": "test-model",
                "messages": [{"role": "user", "content": "你好"}]
            }
        )

        assert response.status_code == 401

    # === 请求验证 ===

    @pytest.mark.asyncio
    async def test_chat_completions_missing_model(self, api_client, db_with_api_key):
        """测试缺少 model 参数"""
        response = await api_client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={
                "messages": [{"role": "user", "content": "你好"}]
            }
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_chat_completions_missing_messages(self, api_client, db_with_api_key):
        """测试缺少 messages 参数"""
        response = await api_client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={
                "model": "test-model"
            }
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_chat_completions_empty_messages(self, api_client, db_with_api_key):
        """测试空消息列表"""
        response = await api_client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={
                "model": "test-model",
                "messages": []
            }
        )

        assert response.status_code == 422

    # === 非流式响应 ===

    @pytest.mark.asyncio
    async def test_chat_completions_non_stream_success(self, api_client, db_with_api_key):
        """测试非流式响应成功"""
        async def mock_stream(*args, **kwargs):
            for token in ["你", "好", "！"]:
                yield token

        with patch("backend.routers.openai.get_mlx_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_stream = mock_stream
            mock_get_service.return_value = mock_service

            response = await api_client.post(
                "/v1/chat/completions",
                headers={"Authorization": f"Bearer {db_with_api_key.key}"},
                json={
                    "model": "test-model",
                    "messages": [{"role": "user", "content": "你好"}],
                    "stream": False
                }
            )

            assert response.status_code == 200
            data = response.json()
            # OpenAI 格式验证
            assert "id" in data
            assert data["object"] == "chat.completion"
            assert "created" in data
            assert data["model"] == "test-model"
            assert "choices" in data
            assert len(data["choices"]) == 1
            assert data["choices"][0]["message"]["role"] == "assistant"
            assert "content" in data["choices"][0]["message"]
            assert "usage" in data
            assert "prompt_tokens" in data["usage"]
            assert "completion_tokens" in data["usage"]
            assert "total_tokens" in data["usage"]

    @pytest.mark.asyncio
    async def test_chat_completions_with_system_message(self, api_client, db_with_api_key):
        """测试包含系统消息"""
        async def mock_stream(*args, **kwargs):
            yield "O"
            yield "K"

        with patch("backend.routers.openai.get_mlx_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_stream = mock_stream
            mock_get_service.return_value = mock_service

            response = await api_client.post(
                "/v1/chat/completions",
                headers={"Authorization": f"Bearer {db_with_api_key.key}"},
                json={
                    "model": "test-model",
                    "messages": [
                        {"role": "system", "content": "你是一个助手"},
                        {"role": "user", "content": "你好"}
                    ],
                    "stream": False
                }
            )

            assert response.status_code == 200

    # === 流式响应 ===

    @pytest.mark.asyncio
    async def test_chat_completions_stream_success(self, api_client, db_with_api_key):
        """测试流式响应成功"""
        async def mock_stream(*args, **kwargs):
            for token in ["你", "好", "！"]:
                yield token

        with patch("backend.routers.openai.get_mlx_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_stream = mock_stream
            mock_get_service.return_value = mock_service

            response = await api_client.post(
                "/v1/chat/completions",
                headers={"Authorization": f"Bearer {db_with_api_key.key}"},
                json={
                    "model": "test-model",
                    "messages": [{"role": "user", "content": "你好"}],
                    "stream": True
                }
            )

            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")

            # 读取流式内容
            content = await response.aread()
            text = content.decode("utf-8")

            # 验证 SSE 格式
            assert "data:" in text
            assert "[DONE]" in text

    # === 参数测试 ===

    @pytest.mark.asyncio
    async def test_chat_completions_with_temperature(self, api_client, db_with_api_key):
        """测试 temperature 参数"""
        async def mock_stream(*args, **kwargs):
            yield "测"
            yield "试"

        with patch("backend.routers.openai.get_mlx_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_stream = mock_stream
            mock_get_service.return_value = mock_service

            response = await api_client.post(
                "/v1/chat/completions",
                headers={"Authorization": f"Bearer {db_with_api_key.key}"},
                json={
                    "model": "test-model",
                    "messages": [{"role": "user", "content": "你好"}],
                    "temperature": 0.5
                }
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_chat_completions_with_max_tokens(self, api_client, db_with_api_key):
        """测试 max_tokens 参数"""
        async def mock_stream(*args, **kwargs):
            yield "测"
            yield "试"

        with patch("backend.routers.openai.get_mlx_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_stream = mock_stream
            mock_get_service.return_value = mock_service

            response = await api_client.post(
                "/v1/chat/completions",
                headers={"Authorization": f"Bearer {db_with_api_key.key}"},
                json={
                    "model": "test-model",
                    "messages": [{"role": "user", "content": "你好"}],
                    "max_tokens": 100
                }
            )

            assert response.status_code == 200


class TestModelsEndpoint:
    """OpenAI 兼容 Models 端点测试"""

    @pytest.mark.asyncio
    async def test_list_models_requires_auth(self, api_client):
        """测试列出模型需要认证"""
        response = await api_client.get("/v1/models")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_models_success(self, api_client, db_with_api_key):
        """测试列出模型成功"""
        response = await api_client.get(
            "/v1/models",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "object" in data
        assert data["object"] == "list"
        assert "data" in data
        assert isinstance(data["data"], list)
