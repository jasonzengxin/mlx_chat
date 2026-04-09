"""
Usage API 测试

测试内容:
- 获取用量统计
- 按时间段查询
"""

import pytest
import pytest_asyncio


class TestUsageAPI:
    """用量统计 API 测试"""

    @pytest.mark.asyncio
    async def test_get_usage_requires_auth(self, api_client):
        """测试获取用量需要认证"""
        response = await api_client.get("/api/v1/usage")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_usage_success(self, api_client, db_with_api_key):
        """测试成功获取用量"""
        response = await api_client.get(
            "/api/v1/usage",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
        assert "total_input_tokens" in data
        assert "total_output_tokens" in data
        assert "total_time_ms" in data

    @pytest.mark.asyncio
    async def test_get_usage_with_period(self, api_client, db_with_api_key):
        """测试按月份查询用量"""
        from datetime import datetime
        current_period = datetime.now().strftime("%Y-%m")

        response = await api_client.get(
            f"/api/v1/usage?period={current_period}",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["period"] == current_period

    @pytest.mark.asyncio
    async def test_usage_isolation(self, api_client, db_with_two_api_keys, usage_service):
        """测试用量隔离 - 不同 Key 看不到彼此的用量"""
        from backend.services.usage_service import UsageRecord

        # Key A 产生用量
        await usage_service.record_usage(UsageRecord(
            api_key_id=db_with_two_api_keys[0].id,
            session_id=None,
            model="test",
            input_tokens=100,
            output_tokens=200,
            time_ms=1000
        ))

        # Key B 查询用量
        response_b = await api_client.get(
            "/api/v1/usage",
            headers={"Authorization": f"Bearer {db_with_two_api_keys[1].key}"}
        )

        assert response_b.status_code == 200
        assert response_b.json()["total_requests"] == 0

    @pytest.mark.asyncio
    async def test_usage_after_chat(self, api_client, db_with_api_key, db_with_session, usage_service):
        """测试聊天后用量增加"""
        from backend.services.usage_service import UsageRecord

        # 初始用量
        response1 = await api_client.get(
            "/api/v1/usage",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        initial_count = response1.json()["total_requests"]

        # 记录一次用量
        await usage_service.record_usage(UsageRecord(
            api_key_id=db_with_api_key.id,
            session_id=db_with_session.id,
            model="test",
            input_tokens=10,
            output_tokens=20,
            time_ms=100
        ))

        # 验证用量增加
        response2 = await api_client.get(
            "/api/v1/usage",
            headers={"Authorization": f"Bearer {db_with_api_key.key}"}
        )
        assert response2.json()["total_requests"] == initial_count + 1
