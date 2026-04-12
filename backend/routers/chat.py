"""
Chat API 路由

提供聊天接口，支持 SSE 流式响应
"""

import time
import json
from typing import Optional
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.auth.dependencies import verify_api_key, get_mlx_service
from backend.services.session_service import SessionService
from backend.services.usage_service import UsageService, UsageRecord
from backend.services.model_registry_service import ModelRegistryService
from backend.database import Database


router = APIRouter()


async def generate_remote_stream(
    base_url: str,
    api_key: str,
    endpoint: str,
    model: str,
    messages: list,
    temperature: float,
    max_tokens: int,
):
    """生成远程 API 的流式响应"""
    url = f"{base_url}{endpoint}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
        async with client.stream("POST", url, headers=headers, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data = line[6:]  # Remove "data: " prefix
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    if "choices" in chunk and len(chunk["choices"]) > 0:
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                except json.JSONDecodeError:
                    continue


# === 请求模型 ===

class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(..., min_length=1)
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 4096
    system_prompt: Optional[str] = None
    context_messages: Optional[int] = None


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
    all_messages = await session_service.get_messages(
        request_body.session_id,
        api_key["id"]
    )

    # 确定上下文窗口大小: 请求级 > session 级 > 默认 20
    ctx_limit = (
        request_body.context_messages
        if request_body.context_messages is not None
        else session.get("context_messages")
    )
    if ctx_limit is None:
        ctx_limit = 20
    # 0 = 不带历史; 负数 = 全部
    if ctx_limit >= 0:
        messages = all_messages[-ctx_limit:] if ctx_limit > 0 else []
    else:
        messages = all_messages

    # 获取模型类型
    model_registry = request.app.state.model_registry
    session_model = session.get("model", "")
    model_info = await model_registry.get_model(session_model) if session_model and session_model != "default" else None
    model_type = model_info.model_type if model_info else "local"

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

            # 构建消息列表
            chat_messages = [{"role": m["role"], "content": m["content"]} for m in messages] + [
                {"role": "user", "content": request_body.message}
            ]

            # 获取生成参数
            temperature = request_body.temperature or session.get("temperature", 0.7)
            max_tokens = request_body.max_tokens or session.get("max_tokens", 4096)

            full_response = ""
            first_token_at: float | None = None

            if model_type == "remote":
                r_base = getattr(model_info, "remote_base_url", "") or ""
                r_key = getattr(model_info, "remote_api_key", "") or ""
                if not r_base or not r_key:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"Remote model '{model_info.name}' is missing credentials. "
                            "Re-add this model from a configured provider."
                        ),
                    )

                async for token in generate_remote_stream(
                    base_url=r_base,
                    api_key=r_key,
                    endpoint=model_info.endpoint or "/chat/completions",
                    model=session.get("model", ""),
                    messages=chat_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                ):
                    if first_token_at is None:
                        first_token_at = time.perf_counter()
                    full_response += token
                    yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"
            else:
                # 本地 MLX 模型
                async for token in mlx_service.generate_stream(
                    messages=chat_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
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