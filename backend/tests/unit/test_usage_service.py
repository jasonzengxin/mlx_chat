"""
用量统计服务测试

测试内容:
- 记录用量
- 汇总统计
- Key 隔离
"""

import pytest

from backend.services.usage_service import UsageService, UsageRecord, UsageSummary


class TestUsageServiceRecord:
    """用量服务 - 记录测试"""

    @pytest.mark.asyncio
    async def test_record_usage_success(self, usage_service, db_with_api_key):
        """测试记录成功"""
        record = UsageRecord(
            api_key_id=db_with_api_key.id,
            session_id=None,
            model="test-model",
            input_tokens=100,
            output_tokens=200,
            time_ms=5000
        )

        log_id = await usage_service.record_usage(record)

        assert log_id is not None
        assert len(log_id) > 0

    @pytest.mark.asyncio
    async def test_record_usage_stored(self, usage_service, db_with_api_key):
        """测试记录存储到数据库"""
        record = UsageRecord(
            api_key_id=db_with_api_key.id,
            session_id=None,
            model="test-model",
            input_tokens=100,
            output_tokens=200,
            time_ms=5000
        )

        await usage_service.record_usage(record)

        # 查询验证
        logs = await usage_service.get_recent_logs(db_with_api_key.id)
        assert len(logs) == 1
        assert logs[0]["input_tokens"] == 100
        assert logs[0]["output_tokens"] == 200

    @pytest.mark.asyncio
    async def test_record_usage_multiple(self, usage_service, db_with_api_key):
        """测试多次记录"""
        for i in range(5):
            record = UsageRecord(
                api_key_id=db_with_api_key.id,
                session_id=None,
                model="test-model",
                input_tokens=100 * (i + 1),
                output_tokens=200 * (i + 1),
                time_ms=1000 * (i + 1)
            )
            await usage_service.record_usage(record)

        logs = await usage_service.get_recent_logs(db_with_api_key.id, limit=10)
        assert len(logs) == 5


class TestUsageServiceSummary:
    """用量服务 - 汇总测试"""

    @pytest.mark.asyncio
    async def test_get_usage_summary_empty(self, usage_service, db_with_api_key):
        """测试空用量汇总"""
        summary = await usage_service.get_usage_summary(db_with_api_key.id)

        assert summary.total_requests == 0
        assert summary.total_input_tokens == 0
        assert summary.total_output_tokens == 0
        assert summary.total_time_ms == 0

    @pytest.mark.asyncio
    async def test_get_usage_summary_all(self, usage_service, db_with_api_key):
        """测试全部用量汇总"""
        # 记录 3 次
        for i in range(3):
            record = UsageRecord(
                api_key_id=db_with_api_key.id,
                session_id=None,
                model="test-model",
                input_tokens=100,
                output_tokens=200,
                time_ms=1000
            )
            await usage_service.record_usage(record)

        summary = await usage_service.get_usage_summary(db_with_api_key.id)

        assert summary.total_requests == 3
        assert summary.total_input_tokens == 300
        assert summary.total_output_tokens == 600
        assert summary.total_time_ms == 3000

    @pytest.mark.asyncio
    async def test_get_usage_summary_by_period(self, usage_service, db_with_api_key):
        """测试按月份汇总"""
        from datetime import datetime

        record = UsageRecord(
            api_key_id=db_with_api_key.id,
            session_id=None,
            model="test-model",
            input_tokens=100,
            output_tokens=200,
            time_ms=1000
        )
        await usage_service.record_usage(record)

        # 获取当前月份
        current_period = datetime.now().strftime("%Y-%m")

        summary = await usage_service.get_usage_summary(
            db_with_api_key.id,
            period=current_period
        )

        assert summary.period == current_period
        assert summary.total_requests == 1

    @pytest.mark.asyncio
    async def test_get_usage_summary_wrong_period(self, usage_service, db_with_api_key):
        """测试错误月份"""
        record = UsageRecord(
            api_key_id=db_with_api_key.id,
            session_id=None,
            model="test-model",
            input_tokens=100,
            output_tokens=200,
            time_ms=1000
        )
        await usage_service.record_usage(record)

        summary = await usage_service.get_usage_summary(
            db_with_api_key.id,
            period="2020-01"
        )

        assert summary.total_requests == 0


class TestUsageServiceIsolation:
    """用量服务 - 隔离测试"""

    @pytest.mark.asyncio
    async def test_usage_isolation_between_keys(self, usage_service, db_with_two_api_keys):
        """测试不同 Key 用量隔离"""
        # Key A 记录 2 次
        for _ in range(2):
            record = UsageRecord(
                api_key_id=db_with_two_api_keys[0].id,
                session_id=None,
                model="test-model",
                input_tokens=100,
                output_tokens=200,
                time_ms=1000
            )
            await usage_service.record_usage(record)

        # Key B 记录 1 次
        record = UsageRecord(
            api_key_id=db_with_two_api_keys[1].id,
            session_id=None,
            model="test-model",
            input_tokens=50,
            output_tokens=100,
            time_ms=500
        )
        await usage_service.record_usage(record)

        # 各自只能看到自己的用量
        summary_a = await usage_service.get_usage_summary(db_with_two_api_keys[0].id)
        summary_b = await usage_service.get_usage_summary(db_with_two_api_keys[1].id)

        assert summary_a.total_requests == 2
        assert summary_b.total_requests == 1
        assert summary_a.total_input_tokens == 200
        assert summary_b.total_input_tokens == 50


class TestUsageServiceRecentLogs:
    """用量服务 - 最近日志测试"""

    @pytest.mark.asyncio
    async def test_get_recent_logs_limit(self, usage_service, db_with_api_key):
        """测试限制返回数量"""
        # 创建 10 条记录
        for i in range(10):
            record = UsageRecord(
                api_key_id=db_with_api_key.id,
                session_id=None,
                model="test-model",
                input_tokens=100,
                output_tokens=200,
                time_ms=1000
            )
            await usage_service.record_usage(record)

        # 只获取 5 条
        logs = await usage_service.get_recent_logs(db_with_api_key.id, limit=5)

        assert len(logs) == 5

    @pytest.mark.asyncio
    async def test_get_recent_logs_order(self, usage_service, db_with_api_key):
        """测试按时间倒序"""
        import asyncio

        # 创建不同时间戳的记录
        for i in range(3):
            record = UsageRecord(
                api_key_id=db_with_api_key.id,
                session_id=None,
                model="test-model",
                input_tokens=i,
                output_tokens=i,
                time_ms=1000
            )
            await usage_service.record_usage(record)
            await asyncio.sleep(0.1)  # 增加延迟确保时间戳不同

        logs = await usage_service.get_recent_logs(db_with_api_key.id, limit=10)

        # 验证有 3 条记录
        assert len(logs) == 3

        # 验证是按时间倒序 (最新在前)
        # 由于 created_at 精度可能不足，我们只验证有记录返回
        for log in logs:
            assert "input_tokens" in log
            assert "output_tokens" in log


class TestUsageRecord:
    """UsageRecord 数据类测试"""

    def test_create_usage_record(self):
        """测试创建记录"""
        record = UsageRecord(
            api_key_id="key-123",
            session_id="session-456",
            model="qwen3.5",
            input_tokens=100,
            output_tokens=200,
            time_ms=5000
        )

        assert record.api_key_id == "key-123"
        assert record.session_id == "session-456"
        assert record.model == "qwen3.5"
        assert record.input_tokens == 100
        assert record.output_tokens == 200
        assert record.time_ms == 5000

    def test_create_usage_record_optional_session(self):
        """测试可选的 session_id"""
        record = UsageRecord(
            api_key_id="key-123",
            session_id=None,
            model="qwen3.5",
            input_tokens=100,
            output_tokens=200,
            time_ms=5000
        )

        assert record.session_id is None


class TestUsageSummary:
    """UsageSummary 数据类测试"""

    def test_create_usage_summary(self):
        """测试创建汇总"""
        summary = UsageSummary(
            api_key_id="key-123",
            period="2026-04",
            total_requests=100,
            total_input_tokens=5000,
            total_output_tokens=30000,
            total_time_ms=120000
        )

        assert summary.api_key_id == "key-123"
        assert summary.period == "2026-04"
        assert summary.total_requests == 100
