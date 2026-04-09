"""
用量统计服务

功能:
- 记录 API 使用量
- 统计查询
- 按 Key 和时间段汇总
"""

import uuid
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

from backend.database import Database


@dataclass
class UsageRecord:
    """单次使用记录"""
    api_key_id: str
    session_id: Optional[str]
    model: str
    input_tokens: int
    output_tokens: int
    time_ms: int


@dataclass
class UsageSummary:
    """用量汇总"""
    api_key_id: str
    period: str
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_time_ms: int


class UsageService:
    """用量统计服务"""

    def __init__(self, db: Database):
        self.db = db

    async def record_usage(self, record: UsageRecord) -> str:
        """
        记录一次 API 调用

        Args:
            record: UsageRecord 数据类

        Returns:
            str: 记录 ID
        """
        log_id = str(uuid.uuid4())

        await self.db.execute(
            """
            INSERT INTO usage_logs
            (id, api_key_id, session_id, model, input_tokens, output_tokens, time_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                log_id,
                record.api_key_id,
                record.session_id,
                record.model,
                record.input_tokens,
                record.output_tokens,
                record.time_ms,
            )
        )
        await self.db.commit()

        return log_id

    async def get_usage_summary(
        self,
        api_key_id: str,
        period: Optional[str] = None
    ) -> UsageSummary:
        """
        获取用量汇总

        Args:
            api_key_id: API Key ID
            period: 时间段 (格式: YYYY-MM)，None 表示全部

        Returns:
            UsageSummary: 汇总数据
        """
        where_clause = "WHERE api_key_id = ?"
        params = [api_key_id]

        if period:
            where_clause += " AND strftime('%Y-%m', created_at) = ?"
            params.append(period)

        row = await self.db.fetchone(
            f"""
            SELECT
                COUNT(*) as total_requests,
                COALESCE(SUM(input_tokens), 0) as total_input_tokens,
                COALESCE(SUM(output_tokens), 0) as total_output_tokens,
                COALESCE(SUM(time_ms), 0) as total_time_ms
            FROM usage_logs
            {where_clause}
            """,
            params
        )

        return UsageSummary(
            api_key_id=api_key_id,
            period=period or "all",
            total_requests=row["total_requests"] or 0,
            total_input_tokens=row["total_input_tokens"] or 0,
            total_output_tokens=row["total_output_tokens"] or 0,
            total_time_ms=row["total_time_ms"] or 0,
        )

    async def get_recent_logs(
        self,
        api_key_id: str,
        limit: int = 10
    ) -> list:
        """
        获取最近的用量日志

        Args:
            api_key_id: API Key ID
            limit: 返回数量

        Returns:
            list: 日志列表
        """
        rows = await self.db.fetchall(
            """
            SELECT id, session_id, model, input_tokens, output_tokens, time_ms, created_at
            FROM usage_logs
            WHERE api_key_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (api_key_id, limit)
        )

        return rows