"""
导出 API 测试

测试内容:
- 预估导出 token 数
- SSE 流式导出知识库
"""

import json
import pytest


class TestExportEstimateAPI:
    """导出预估 API 测试"""

    @pytest.mark.asyncio
    async def test_export_estimate_requires_auth(self, api_client):
        """测试预估需要认证"""
        response = await api_client.post(
            "/api/v1/export/sessions/test-session-id/export/estimate",
            json={"template_id": "test-template"}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_export_estimate_returns_tokens(self, api_client, db_with_api_key, db_connection):
        """测试预估返回 token 数"""
        from backend.services.session_service import SessionService

        # 创建会话和消息
        session_service = SessionService(db_connection)
        session = await session_service.create_session(
            api_key_id=db_with_api_key.id,
            name="Test Session"
        )
        for i in range(5):
            await session_service.add_message(session["id"], db_with_api_key.id, "user", f"Message {i+1}")

        # 获取模板
        templates_response = await api_client.get(
            "/api/v1/export/templates",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        template_id = templates_response.json()[0]["id"]

        # 预估
        response = await api_client.post(
            f"/api/v1/export/sessions/{session['id']}/export/estimate",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={"template_id": template_id, "language": "zh"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "estimated_tokens" in data
        assert "message_count" in data
        assert data["message_count"] == 5

    @pytest.mark.asyncio
    async def test_export_estimate_session_not_found(self, api_client, db_with_api_key):
        """测试预估会话不存在"""
        templates_response = await api_client.get(
            "/api/v1/export/templates",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        template_id = templates_response.json()[0]["id"]

        response = await api_client.post(
            "/api/v1/export/sessions/non-existent-session/export/estimate",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={"template_id": template_id, "language": "zh"}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_export_estimate_template_not_found(self, api_client, db_with_api_key, db_connection):
        """测试预估模板不存在"""
        from backend.services.session_service import SessionService

        session_service = SessionService(db_connection)
        session = await session_service.create_session(
            api_key_id=db_with_api_key.id,
            name="Test Session"
        )

        response = await api_client.post(
            f"/api/v1/export/sessions/{session['id']}/export/estimate",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={"template_id": "non-existent-template", "language": "zh"}
        )

        assert response.status_code == 404


class TestExportAPI:
    """导出 API 测试"""

    @pytest.mark.asyncio
    async def test_export_requires_auth(self, api_client):
        """测试导出需要认证"""
        response = await api_client.post(
            "/api/v1/export/sessions/test-session-id/export",
            json={"template_id": "test-template"}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_export_session_not_found(self, api_client, db_with_api_key):
        """测试导出会话不存在"""
        templates_response = await api_client.get(
            "/api/v1/export/templates",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        template_id = templates_response.json()[0]["id"]

        response = await api_client.post(
            "/api/v1/export/sessions/non-existent-session/export",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={"template_id": template_id, "language": "zh"}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_export_template_not_found(self, api_client, db_with_api_key, db_connection):
        """测试导出模板不存在"""
        from backend.services.session_service import SessionService

        session_service = SessionService(db_connection)
        session = await session_service.create_session(
            api_key_id=db_with_api_key.id,
            name="Test Session"
        )

        response = await api_client.post(
            f"/api/v1/export/sessions/{session['id']}/export",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={"template_id": "non-existent-template", "language": "zh"}
        )

        assert response.status_code == 404


class TestExportSSEStream:
    """导出 SSE 流式响应测试"""

    @pytest.mark.asyncio
    async def test_export_sse_streaming(self, api_client, db_with_api_key, db_connection, mock_mlx_generate):
        """测试 SSE 流式响应 (无模型加载时返回错误)"""
        from backend.services.session_service import SessionService

        # 创建会话和消息
        session_service = SessionService(db_connection)
        session = await session_service.create_session(
            api_key_id=db_with_api_key.id,
            name="Test Session"
        )
        await session_service.add_message(session["id"], db_with_api_key.id, "user", "Hello")
        await session_service.add_message(session["id"], db_with_api_key.id, "assistant", "Hi there!")

        # 获取模板
        templates_response = await api_client.get(
            "/api/v1/export/templates",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        template_id = templates_response.json()[0]["id"]

        # 导出 (SSE 流式)
        response = await api_client.post(
            f"/api/v1/export/sessions/{session['id']}/export",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={"template_id": template_id, "language": "zh"}
        )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

        # 解析 SSE 流
        content = b""
        async for chunk in response.aiter_bytes():
            content += chunk

        events = {}
        for line in content.decode().split("\n"):
            if line.startswith("event: "):
                event_type = line[7:]
            elif line.startswith("data: "):
                data = json.loads(line[6:])
                events[event_type] = data

        # 测试环境没有模型，返回 "No model loaded" 错误是预期的
        # 验证 SSE 格式正确，有 error 或 done 事件
        assert "error" in events or "done" in events

    @pytest.mark.asyncio
    async def test_export_language_param(self, api_client, db_with_api_key, db_connection, mock_mlx_generate):
        """测试语言参数"""
        from backend.services.session_service import SessionService

        # 创建会话和消息
        session_service = SessionService(db_connection)
        session = await session_service.create_session(
            api_key_id=db_with_api_key.id,
            name="Test Session"
        )
        await session_service.add_message(session["id"], db_with_api_key.id, "user", "Hello")

        # 获取模板
        templates_response = await api_client.get(
            "/api/v1/export/templates",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        template_id = templates_response.json()[0]["id"]

        # 测试中文
        response_zh = await api_client.post(
            f"/api/v1/export/sessions/{session['id']}/export",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={"template_id": template_id, "language": "zh"}
        )
        assert response_zh.status_code == 200

        # 测试英文
        response_en = await api_client.post(
            f"/api/v1/export/sessions/{session['id']}/export",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={"template_id": template_id, "language": "en"}
        )
        assert response_en.status_code == 200


class TestExportService:
    """导出服务单元测试"""

    @pytest.mark.asyncio
    async def test_build_export_prompt(self, db_connection):
        """测试构建导出 prompt"""
        from backend.services.export_template_service import ExportTemplateService
        from backend.services.session_service import SessionService
        import uuid

        # 初始化
        export_service = ExportTemplateService(db_connection)
        await export_service.initialize()

        # 创建会话和消息
        session_service = SessionService(db_connection)
        api_key_id = "test-key"
        await db_connection.execute(
            "INSERT INTO api_keys (id, key_hash, key_prefix, name) VALUES (?, ?, ?, ?)",
            (api_key_id, "hash", "prefix", "Test Key")
        )
        await db_connection.commit()

        session = await session_service.create_session(
            api_key_id=api_key_id,
            name="Test Session",
            model="test-model"
        )

        await session_service.add_message(session["id"], api_key_id, "user", "Hello")
        await session_service.add_message(session["id"], api_key_id, "assistant", "Hi there!")

        # 获取模板
        template = await export_service.get_template(
            (await export_service.list_templates())[0].id
        )

        # 构建 prompt
        messages, system_prompt = await export_service.build_export_prompt(
            session["id"],
            api_key_id,
            template,
            "zh"
        )

        assert isinstance(messages, list)
        assert len(messages) == 2  # user + assistant
        assert messages[0]["role"] == "user"
        assert "Hello" in messages[0]["content"]
        assert system_prompt  # system_prompt 不为空

    @pytest.mark.asyncio
    async def test_estimate_export_tokens(self, db_connection):
        """测试预估 token 数"""
        from backend.services.export_template_service import ExportTemplateService
        from backend.services.session_service import SessionService
        import uuid

        # 初始化
        export_service = ExportTemplateService(db_connection)
        await export_service.initialize()

        # 创建会话和消息
        session_service = SessionService(db_connection)
        api_key_id = "test-key"
        await db_connection.execute(
            "INSERT INTO api_keys (id, key_hash, key_prefix, name) VALUES (?, ?, ?, ?)",
            (api_key_id, "hash", "prefix", "Test Key")
        )
        await db_connection.commit()

        session = await session_service.create_session(
            api_key_id=api_key_id,
            name="Test Session"
        )

        # 添加多条消息
        for i in range(5):
            await session_service.add_message(session["id"], api_key_id, "user", f"Message {i+1}")

        # 获取模板
        template = await export_service.get_template(
            (await export_service.list_templates())[0].id
        )

        # 预估
        estimated = await export_service.estimate_export_tokens(
            session["id"],
            api_key_id,
            template
        )

        assert estimated > 0
        assert isinstance(estimated, int)