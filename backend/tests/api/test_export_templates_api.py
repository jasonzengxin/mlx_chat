"""
导出模板 API 测试

测试内容:
- 列出模板 (需认证、返回预置模板)
- 获取模板详情
- 创建自定义模板 (需认证)
- 更新自定义模板 (预置不可修改)
- 删除自定义模板 (预置不可删除)
"""

import pytest


class TestExportTemplatesAPI:
    """导出模板 API 测试"""

    # === 列出模板 ===

    @pytest.mark.asyncio
    async def test_list_templates_requires_auth(self, api_client):
        """测试列出模板需要认证"""
        response = await api_client.get("/api/v1/export/templates")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_templates_returns_builtin(self, api_client, db_with_api_key):
        """测试列出模板返回 4 个预置模板"""
        response = await api_client.get(
            "/api/v1/export/templates",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # 应该有 4 个预置模板
        assert len(data) == 4

        # 验证预置模板字段
        names = [t["name"] for t in data]
        assert "学习笔记" in names
        assert "会议纪要" in names
        assert "技术文档" in names
        assert "知识卡片" in names

        # 验证预置模板的共同字段
        for template in data:
            assert template["is_builtin"] is True
            assert template["id"] is not None
            assert template["template_content"] is not None
            assert template["system_prompt"] is not None

    # === 获取模板详情 ===

    @pytest.mark.asyncio
    async def test_get_template_detail(self, api_client, db_with_api_key):
        """测试获取单个模板详情"""
        # 先获取列表
        list_response = await api_client.get(
            "/api/v1/export/templates",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        templates = list_response.json()
        template_id = templates[0]["id"]

        # 获取详情
        response = await api_client.get(
            f"/api/v1/export/templates/{template_id}",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == template_id
        assert "template_content" in data
        assert "system_prompt" in data

    @pytest.mark.asyncio
    async def test_get_template_not_found(self, api_client, db_with_api_key):
        """测试获取不存在的模板"""
        response = await api_client.get(
            "/api/v1/export/templates/non-existent-id",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )

        assert response.status_code == 404

    # === 创建模板 ===

    @pytest.mark.asyncio
    async def test_create_template_requires_auth(self, api_client):
        """测试创建模板需要认证"""
        response = await api_client.post(
            "/api/v1/export/templates",
            json={
                "name": "My Template",
                "template_content": "# Test\n{{content}}",
                "system_prompt": "Extract key points"
            }
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_custom_template(self, api_client, db_with_api_key):
        """测试创建自定义模板"""
        response = await api_client.post(
            "/api/v1/export/templates",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={
                "name": "我的自定义模板",
                "description": "一个测试模板",
                "language": "zh",
                "template_content": "# 自定义模板\n\n{{content}}",
                "system_prompt": "根据对话内容提取要点"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "我的自定义模板"
        assert data["description"] == "一个测试模板"
        assert data["language"] == "zh"
        assert data["is_builtin"] is False
        assert data["id"] is not None

    @pytest.mark.asyncio
    async def test_create_template_requires_name(self, api_client, db_with_api_key):
        """测试创建模板需要名称"""
        response = await api_client.post(
            "/api/v1/export/templates",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={
                "template_content": "# Test",
                "system_prompt": "Extract"
            }
        )

        assert response.status_code == 422  # Validation error

    # === 更新模板 ===

    @pytest.mark.asyncio
    async def test_update_custom_template(self, api_client, db_with_api_key):
        """测试更新自定义模板"""
        # 先创建模板
        create_response = await api_client.post(
            "/api/v1/export/templates",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={
                "name": "Original Name",
                "template_content": "# Original",
                "system_prompt": "Original prompt"
            }
        )
        template_id = create_response.json()["id"]

        # 更新模板
        response = await api_client.patch(
            f"/api/v1/export/templates/{template_id}",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={
                "name": "Updated Name",
                "description": "Updated description"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated description"
        # 原有字段保持不变
        assert data["template_content"] == "# Original"

    @pytest.mark.asyncio
    async def test_update_builtin_template_forbidden(self, api_client, db_with_api_key):
        """测试预置模板不可修改"""
        # 获取预置模板
        list_response = await api_client.get(
            "/api/v1/export/templates",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        builtin_template = list_response.json()[0]

        # 尝试更新
        response = await api_client.patch(
            f"/api/v1/export/templates/{builtin_template['id']}",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={"name": "Hacked Name"}
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_nonexistent_template(self, api_client, db_with_api_key):
        """测试更新不存在的模板"""
        response = await api_client.patch(
            "/api/v1/export/templates/non-existent-id",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={"name": "New Name"}
        )

        assert response.status_code == 404

    # === 删除模板 ===

    @pytest.mark.asyncio
    async def test_delete_custom_template(self, api_client, db_with_api_key):
        """测试删除自定义模板"""
        # 先创建模板
        create_response = await api_client.post(
            "/api/v1/export/templates",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"},
            json={
                "name": "To Be Deleted",
                "template_content": "# Delete me",
                "system_prompt": "Delete"
            }
        )
        template_id = create_response.json()["id"]

        # 删除模板
        response = await api_client.delete(
            f"/api/v1/export/templates/{template_id}",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )

        assert response.status_code == 200

        # 验证已删除
        get_response = await api_client.get(
            f"/api/v1/export/templates/{template_id}",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_builtin_template_forbidden(self, api_client, db_with_api_key):
        """测试预置模板不可删除"""
        # 获取预置模板
        list_response = await api_client.get(
            "/api/v1/export/templates",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        builtin_template = list_response.json()[0]

        # 尝试删除
        response = await api_client.delete(
            f"/api/v1/export/templates/{builtin_template['id']}",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )

        assert response.status_code == 403

        # 验证仍在列表中
        list_response2 = await api_client.get(
            "/api/v1/export/templates",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        templates = list_response2.json()
        assert any(t["id"] == builtin_template["id"] for t in templates)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_template(self, api_client, db_with_api_key):
        """测试删除不存在的模板"""
        response = await api_client.delete(
            "/api/v1/export/templates/non-existent-id",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )

        assert response.status_code == 404


class TestExportTemplatesService:
    """导出模板服务单元测试"""

    @pytest.mark.asyncio
    async def test_initialize_creates_builtin_templates(self, db_connection):
        """测试初始化创建预置模板"""
        from backend.services.export_template_service import ExportTemplateService

        service = ExportTemplateService(db_connection)
        await service.initialize()

        templates = await service.list_templates()
        assert len(templates) == 4

    @pytest.mark.asyncio
    async def test_list_templates_only_builtin(self, db_connection):
        """测试列出模板只返回预置模板"""
        from backend.services.export_template_service import ExportTemplateService

        service = ExportTemplateService(db_connection)
        await service.initialize()

        templates = await service.list_templates()
        assert len(templates) == 4
        assert all(t.is_builtin for t in templates)

    @pytest.mark.asyncio
    async def test_create_and_list_custom_template(self, db_connection):
        """测试创建并列出自定义模板"""
        from backend.services.export_template_service import ExportTemplateService

        service = ExportTemplateService(db_connection)
        await service.initialize()

        # 创建自定义模板
        custom = await service.create_template(
            name="My Template",
            template_content="# Content",
            system_prompt="Extract"
        )
        assert custom.is_builtin is False

        # 列表应包含预置 + 自定义
        templates = await service.list_templates()
        assert len(templates) == 5

    @pytest.mark.asyncio
    async def test_update_custom_template(self, db_connection):
        """测试更新自定义模板"""
        from backend.services.export_template_service import ExportTemplateService

        service = ExportTemplateService(db_connection)
        await service.initialize()

        # 创建自定义模板
        custom = await service.create_template(
            name="Original",
            template_content="# Original",
            system_prompt="Original"
        )

        # 更新
        updated = await service.update_template(custom.id, name="Updated")
        assert updated.name == "Updated"
        assert updated.template_content == "# Original"

    @pytest.mark.asyncio
    async def test_update_builtin_forbidden(self, db_connection):
        """测试更新预置模板被禁止"""
        from backend.services.export_template_service import ExportTemplateService

        service = ExportTemplateService(db_connection)
        await service.initialize()

        templates = await service.list_templates()
        builtin = templates[0]

        # 更新应返回 None 或抛出异常
        with pytest.raises(PermissionError):
            await service.update_template(builtin.id, name="Hacked")

    @pytest.mark.asyncio
    async def test_delete_custom_template(self, db_connection):
        """测试删除自定义模板"""
        from backend.services.export_template_service import ExportTemplateService

        service = ExportTemplateService(db_connection)
        await service.initialize()

        # 创建自定义模板
        custom = await service.create_template(
            name="To Delete",
            template_content="# Delete",
            system_prompt="Delete"
        )

        # 删除
        result = await service.delete_template(custom.id)
        assert result is True

        # 验证已删除
        templates = await service.list_templates()
        assert len(templates) == 4  # 只剩预置

    @pytest.mark.asyncio
    async def test_delete_builtin_forbidden(self, db_connection):
        """测试删除预置模板被禁止"""
        from backend.services.export_template_service import ExportTemplateService

        service = ExportTemplateService(db_connection)
        await service.initialize()

        templates = await service.list_templates()
        builtin = templates[0]

        # 删除应抛出 PermissionError
        with pytest.raises(PermissionError):
            await service.delete_template(builtin.id)

        # 验证仍在列表中
        templates = await service.list_templates()
        assert len(templates) == 4
