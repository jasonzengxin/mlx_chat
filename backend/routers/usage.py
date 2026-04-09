"""
用量统计 API 路由

提供用量查询
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Request

from backend.auth.dependencies import verify_api_key
from backend.services.usage_service import UsageService
from backend.database import Database


router = APIRouter()


def get_usage_service(request: Request) -> UsageService:
    """获取用量服务"""
    db = request.app.state.db
    return UsageService(db)


@router.get("")
async def get_usage(
    request: Request,
    period: Optional[str] = Query(None, description="格式: YYYY-MM"),
    api_key: dict = Depends(verify_api_key),
):
    """获取当前 API Key 的用量统计"""
    usage_service = get_usage_service(request)

    summary = await usage_service.get_usage_summary(
        api_key_id=api_key["id"],
        period=period
    )

    return {
        "api_key_id": summary.api_key_id,
        "period": summary.period,
        "total_requests": summary.total_requests,
        "total_input_tokens": summary.total_input_tokens,
        "total_output_tokens": summary.total_output_tokens,
        "total_time_ms": summary.total_time_ms,
    }