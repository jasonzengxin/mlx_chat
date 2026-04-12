"""
API 端到端测试

测试多个 API 协作的完整流程:
1. Usage E2E: 记录用量的完整查询流程
2. Export template lifecycle: 模板 CRUD 完整流程
3. Export full flow: 会话 + 模板 + 导出/预估
4. Settings CORS: CORS 配置 CRUD
"""

import pytest


class TestUsageE2E:
    """用量统计 E2E 测试"""

    @pytest.mark.asyncio
    async def test_usage_initially_zero(self, api_client, db_with_api_key):
        """新 API Key 初始用量为 0"""
        response = await api_client.get(
            "/api/v1/usage",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_requests"] == 0
        assert data["total_input_tokens"] == 0
        assert data["total_output_tokens"] == 0

    @pytest.mark.asyncio
    async def test_usage_after_manual_record(self, api_client, db_with_api_key, usage_service):
        """通过 usage_service 记录后可以查询到"""
        from backend.services.usage_service import UsageRecord

        await usage_service.record_usage(UsageRecord(
            api_key_id=db_with_api_key.id,
            session_id=None,
            model="test-model",
            input_tokens=100,
            output_tokens=200,
            time_ms=1000
        ))

        response = await api_client.get(
            "/api/v1/usage",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_requests"] == 1
        assert data["total_input_tokens"] == 100
        assert data["total_output_tokens"] == 200
        assert data["total_time_ms"] == 1000

    @pytest.mark.asyncio
    async def test_usage_period_filter(self, api_client, db_with_api_key, usage_service):
        """用量统计支持按月份筛选"""
        from datetime import datetime
        from backend.services.usage_service import UsageRecord

        current_period = datetime.now().strftime("%Y-%m")

        await usage_service.record_usage(UsageRecord(
            api_key_id=db_with_api_key.id,
            session_id=None,
            model="test",
            input_tokens=50,
            output_tokens=50,
            time_ms=500
        ))

        # 全量查询
        all_usage = (await api_client.get(
            "/api/v1/usage",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )).json()
        assert all_usage["total_requests"] >= 1

        # 按月查询
        month_usage = (await api_client.get(
            f"/api/v1/usage?period={current_period}",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )).json()
        assert month_usage["period"] == current_period
        assert month_usage["total_requests"] >= 1

    @pytest.mark.asyncio
    async def test_usage_key_isolation(self, api_client, db_with_two_api_keys, usage_service):
        """不同 API Key 之间的用量隔离"""
        from backend.services.usage_service import UsageRecord

        # Key A 记录用量
        await usage_service.record_usage(UsageRecord(
            api_key_id=db_with_two_api_keys[0].id,
            session_id=None,
            model="test",
            input_tokens=100,
            output_tokens=200,
            time_ms=1000
        ))

        # Key B 查询看不到 Key A 的用量
        response_b = await api_client.get(
            "/api/v1/usage",
            headers={"Authorization": f"Bearer {db_with_two_api_keys[1].key}"}
        )
        assert response_b.status_code == 200
        assert response_b.json()["total_requests"] == 0

        # Key A 查询看到自己的用量
        response_a = await api_client.get(
            "/api/v1/usage",
            headers={"Authorization": f"Bearer {db_with_two_api_keys[0].key}"}
        )
        assert response_a.json()["total_requests"] == 1

    @pytest.mark.asyncio
    async def test_usage_accumulation(self, api_client, db_with_api_key, usage_service):
        """多次记录累加"""
        from backend.services.usage_service import UsageRecord

        for i in range(3):
            await usage_service.record_usage(UsageRecord(
                api_key_id=db_with_api_key.id,
                session_id=None,
                model="test",
                input_tokens=10,
                output_tokens=20,
                time_ms=100
            ))

        response = await api_client.get(
            "/api/v1/usage",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        data = response.json()
        assert data["total_requests"] == 3
        assert data["total_input_tokens"] == 30
        assert data["total_output_tokens"] == 60


class TestExportTemplateLifecycle:
    """模板完整生命周期 E2E 测试"""

    @pytest.mark.asyncio
    async def test_template_lifecycle(self, api_client, db_with_api_key):
        """模板完整生命周期: 列表 → 创建 → 更新 → 删除"""
        # 1. 列表 (含 4 个预置)
        list_resp = await api_client.get(
            "/api/v1/export/templates",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        assert list_resp.status_code == 200
        builtin_count = len(list_resp.json())

        # 2. 创建自定义模板
        create_resp = await api_client.post(
            "/api/v1/export/templates",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={
                "name": "E2E Test Template",
                "description": "Test description",
                "language": "zh",
                "template_content": "# {{session_name}}\n\n{{content}}",
                "system_prompt": "Summarize the conversation.",
            }
        )
        assert create_resp.status_code == 200
        tpl = create_resp.json()
        tpl_id = tpl["id"]
        assert tpl["name"] == "E2E Test Template"
        assert tpl["is_builtin"] is False

        # 3. 列表应该 +1
        list_resp2 = await api_client.get(
            "/api/v1/export/templates",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        assert len(list_resp2.json()) == builtin_count + 1

        # 4. 更新自定义模板
        update_resp = await api_client.patch(
            f"/api/v1/export/templates/{tpl_id}",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={"name": "Updated E2E Template", "description": "Updated desc"}
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["name"] == "Updated E2E Template"

        # 5. 获取单个模板详情
        get_resp = await api_client.get(
            f"/api/v1/export/templates/{tpl_id}",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["name"] == "Updated E2E Template"

        # 6. 删除自定义模板
        del_resp = await api_client.delete(
            f"/api/v1/export/templates/{tpl_id}",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        assert del_resp.status_code == 200

        # 7. 列表应该恢复原数
        list_resp3 = await api_client.get(
            "/api/v1/export/templates",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        assert len(list_resp3.json()) == builtin_count

    @pytest.mark.asyncio
    async def test_export_estimate_with_session(self, api_client, db_with_api_key, db_connection):
        """导出预估与会话消息关联"""
        from backend.services.session_service import SessionService

        # 创建会话 + 消息
        session_service = SessionService(db_connection)
        session = await session_service.create_session(db_with_api_key.id, "Export Test Session")
        for i in range(3):
            await session_service.add_message(session["id"], db_with_api_key.id, "user", f"User msg {i+1}")
            await session_service.add_message(session["id"], db_with_api_key.id, "assistant", f"Assistant msg {i+1}")

        # 获取模板
        templates_resp = await api_client.get(
            "/api/v1/export/templates",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        template_id = templates_resp.json()[0]["id"]

        # 预估
        est_resp = await api_client.post(
            f"/api/v1/export/sessions/{session['id']}/export/estimate",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={"template_id": template_id, "language": "zh"}
        )
        assert est_resp.status_code == 200
        est = est_resp.json()
        assert est["message_count"] == 6  # 3 user + 3 assistant
        assert est["estimated_tokens"] > 0


class TestSettingsCORS:
    """设置 API 和 CORS 配置 E2E 测试"""

    @pytest.mark.asyncio
    async def test_get_settings(self, api_client, db_with_api_key):
        """获取设置应该返回默认值"""
        response = await api_client.get(
            "/api/v1/settings",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "cors_allow_origins" in data
        assert "default_model" in data
        assert "default_temperature" in data
        assert isinstance(data["cors_allow_origins"], list)

    @pytest.mark.asyncio
    async def test_update_cors_origins(self, api_client, db_with_api_key):
        """更新 CORS 配置"""
        new_origins = [
            "http://localhost:3000",
            "http://localhost:8000",
            "https://example.com",
        ]

        response = await api_client.patch(
            "/api/v1/settings",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={"cors_allow_origins": new_origins}
        )
        assert response.status_code == 200

        # 验证更新生效
        get_resp = await api_client.get(
            "/api/v1/settings",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        assert get_resp.json()["cors_allow_origins"] == new_origins

    @pytest.mark.asyncio
    async def test_update_default_model(self, api_client, db_with_api_key):
        """更新默认模型"""
        response = await api_client.patch(
            "/api/v1/settings",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={"default_model": "mlx-community/Llama-3-8B"}
        )
        assert response.status_code == 200

        get_resp = await api_client.get(
            "/api/v1/settings",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        assert get_resp.json()["default_model"] == "mlx-community/Llama-3-8B"

    @pytest.mark.asyncio
    async def test_settings_requires_auth(self, api_client):
        """设置 API 需要认证"""
        response = await api_client.get("/api/v1/settings")
        assert response.status_code == 401

        patch_resp = await api_client.patch("/api/v1/settings", json={})
        assert patch_resp.status_code == 401


class TestExportFullFlowE2E:
    """导出完整流程 E2E 测试"""

    @pytest.mark.asyncio
    async def test_export_builtin_template_protection(self, api_client, db_with_api_key):
        """预置模板不可修改/删除"""
        # 获取预置模板
        templates_resp = await api_client.get(
            "/api/v1/export/templates",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        builtin = templates_resp.json()[0]

        # 尝试更新 → 403
        update_resp = await api_client.patch(
            f"/api/v1/export/templates/{builtin['id']}",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={"name": "Hacked"}
        )
        assert update_resp.status_code == 403

        # 尝试删除 → 403
        del_resp = await api_client.delete(
            f"/api/v1/export/templates/{builtin['id']}",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        assert del_resp.status_code == 403

        # 验证预置模板仍在列表中
        templates_resp2 = await api_client.get(
            "/api/v1/export/templates",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        ids = [t["id"] for t in templates_resp2.json()]
        assert builtin["id"] in ids

    @pytest.mark.asyncio
    async def test_export_api_requires_auth(self, api_client, db_with_api_key, db_connection):
        """导出 API 端点需要认证"""
        from backend.services.session_service import SessionService

        session_service = SessionService(db_connection)
        session = await session_service.create_session(db_with_api_key.id, "Test")

        templates_resp = await api_client.get(
            "/api/v1/export/templates",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        template_id = templates_resp.json()[0]["id"]

        # 无认证
        r1 = await api_client.post(
            f"/api/v1/export/sessions/{session['id']}/export/estimate",
            json={"template_id": template_id}
        )
        assert r1.status_code == 401

        r2 = await api_client.post(
            f"/api/v1/export/sessions/{session['id']}/export",
            json={"template_id": template_id}
        )
        assert r2.status_code == 401

    @pytest.mark.asyncio
    async def test_export_session_not_found(self, api_client, db_with_api_key):
        """导出会话不存在时返回 404"""
        templates_resp = await api_client.get(
            "/api/v1/export/templates",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        template_id = templates_resp.json()[0]["id"]

        response = await api_client.post(
            "/api/v1/export/sessions/nonexistent-id/export/estimate",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={"template_id": template_id, "language": "zh"}
        )
        assert response.status_code == 404

        export_resp = await api_client.post(
            "/api/v1/export/sessions/nonexistent-id/export",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={"template_id": template_id, "language": "zh"}
        )
        assert export_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_export_template_not_found(self, api_client, db_with_api_key, db_connection):
        """导出模板不存在时返回 404"""
        from backend.services.session_service import SessionService

        session_service = SessionService(db_connection)
        session = await session_service.create_session(db_with_api_key.id, "Test")

        response = await api_client.post(
            f"/api/v1/export/sessions/{session['id']}/export/estimate",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={"template_id": "nonexistent-template-id", "language": "zh"}
        )
        assert response.status_code == 404

        export_resp = await api_client.post(
            f"/api/v1/export/sessions/{session['id']}/export",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={"template_id": "nonexistent-template-id", "language": "zh"}
        )
        assert export_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_export_estimate_and_export_flow(self, api_client, db_with_api_key, db_connection):
        """预估 → 导出完整流程 (无模型加载，验证 SSE 格式)"""
        import json
        from backend.services.session_service import SessionService

        # 创建会话 + 消息
        session_service = SessionService(db_connection)
        session = await session_service.create_session(db_with_api_key.id, "E2E Flow Test")
        await session_service.add_message(session["id"], db_with_api_key.id, "user", "What is MLX?")
        await session_service.add_message(session["id"], db_with_api_key.id, "assistant", "MLX is Apple's ML framework.")

        # 获取模板
        templates_resp = await api_client.get(
            "/api/v1/export/templates",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        template_id = templates_resp.json()[0]["id"]

        # Step 1: 预估
        est_resp = await api_client.post(
            f"/api/v1/export/sessions/{session['id']}/export/estimate",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={"template_id": template_id, "language": "zh"}
        )
        assert est_resp.status_code == 200
        est = est_resp.json()
        assert est["estimated_tokens"] > 0
        assert est["message_count"] == 2

        # Step 2: 导出 (无模型加载 → 应返回 error 事件)
        export_resp = await api_client.post(
            f"/api/v1/export/sessions/{session['id']}/export",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={"template_id": template_id, "language": "zh"}
        )
        assert export_resp.status_code == 200
        assert "text/event-stream" in export_resp.headers.get("content-type", "")

        # 消费 SSE 流
        content = b""
        async for chunk in export_resp.aiter_bytes():
            content += chunk

        # 解析 SSE 事件
        events = {}
        for line in content.decode().split("\n"):
            if line.startswith("event: "):
                event_type = line[7:]
            elif line.startswith("data: "):
                try:
                    events[event_type] = json.loads(line[6:])
                except json.JSONDecodeError:
                    pass

        # 无模型加载 → error 或 done
        assert "error" in events or "done" in events
