"""
Chat API 路由

提供聊天接口，支持 SSE 流式响应
"""

import time
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.auth.dependencies import verify_api_key, get_mlx_service
from backend.services.session_service import SessionService
from backend.services.usage_service import UsageService, UsageRecord
from backend.database import Database


router = APIRouter()


# === 请求模型 ===

class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(..., min_length=1)
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 4096
    system_prompt: Optional[str] = None


def _safe_rate(total_units: int, duration_ms: int) -> float:
    """按毫秒时长计算速率，避免除零"""
    if duration_ms <= 0:
        return 0.0
    return round(total_units / (duration_ms / 1000), 2)


# === 辅助函数 ===

def get_db(request: Request) -> Database:
    """从 app.state 获取数据库"""
    return request.app.state.db


def get_session_service(request: Request) -> SessionService:
    """获取会话服务"""
    db = get_db(request)
    return SessionService(db)


def get_usage_service(request: Request) -> UsageService:
    """获取用量服务"""
    db = get_db(request)
    return UsageService(db)


# === API 端点 ===

@router.post("")
async def chat(
    request: Request,
    request_body: ChatRequest,
    api_key: dict = Depends(verify_api_key),
    mlx_service = Depends(get_mlx_service),
):
    """聊天接口，返回 SSE 流式响应"""
    session_service = get_session_service(request)
    usage_service = get_usage_service(request)

    # 验证会话存在
    session = await session_service.get_session(
        request_body.session_id,
        api_key["id"]
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # 获取历史消息
    messages = await session_service.get_messages(
        request_body.session_id,
        api_key["id"]
    )

    start_time = time.perf_counter()

    async def event_generator():
        try:
            # 添加用户消息
            await session_service.add_message(
                request_body.session_id,
                api_key["id"],
                "user",
                request_body.message
            )

            # 流式生成
            full_response = ""
            first_token_at: float | None = None
            async for token in mlx_service.generate_stream(
                messages=[{"role": m["role"], "content": m["content"]} for m in messages] + [
                    {"role": "user", "content": request_body.message}
                ],
                temperature=request_body.temperature or session.get("temperature", 0.7),
                max_tokens=request_body.max_tokens or session.get("max_tokens", 4096),
                system_prompt=request_body.system_prompt or session.get("system_prompt")
            ):
                if first_token_at is None:
                    first_token_at = time.perf_counter()
                full_response += token
                yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"

            # 计算生成耗时
            end_time = time.perf_counter()
            duration_ms = int((end_time - start_time) * 1000)
            ttft_ms = int((first_token_at - start_time) * 1000) if first_token_at is not None else duration_ms
            generation_ms = max(duration_ms - ttft_ms, 0)
            output_chars_per_second = _safe_rate(len(full_response), generation_ms)

            # 保存助手消息 (包含耗时)
            await session_service.add_message(
                request_body.session_id,
                api_key["id"],
                "assistant",
                full_response,
                duration_ms=duration_ms
            )

            # 记录用量
            elapsed = int((time.perf_counter() - start_time) * 1000)
            await usage_service.record_usage(UsageRecord(
                api_key_id=api_key["id"],
                session_id=request_body.session_id,
                model=session.get("model", "unknown"),
                input_tokens=len(request_body.message),
                output_tokens=len(full_response),
                time_ms=elapsed
            ))

            yield (
                "event: done\n"
                f"data: {json.dumps({
                    'total_tokens': len(full_response),
                    'duration_ms': duration_ms,
                    'ttft_ms': ttft_ms,
                    'generation_ms': generation_ms,
                    'output_chars_per_second': output_chars_per_second,
                })}\n\n"
            )

        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )