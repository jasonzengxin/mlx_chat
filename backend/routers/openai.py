"""
OpenAI 兼容 API 路由

提供与 OpenAI API 兼容的接口，支持 Chrome 插件等第三方客户端接入
"""

import time
import json
import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.auth.dependencies import verify_api_key
from backend.mlx_instance import get_mlx_service


router = APIRouter()


# === 请求/响应模型 ===

class ChatMessage(BaseModel):
    """聊天消息"""
    role: str = Field(..., pattern="^(system|user|assistant)$")
    content: str


class ChatCompletionRequest(BaseModel):
    """Chat Completion 请求"""
    model: str
    messages: List[ChatMessage] = Field(..., min_length=1)
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 4096
    stream: Optional[bool] = False


class ChatCompletionResponse(BaseModel):
    """Chat Completion 响应"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[dict]
    usage: dict


class ModelResponse(BaseModel):
    """模型响应"""
    id: str
    object: str = "model"
    created: int
    owned_by: str = "local"


class ModelsListResponse(BaseModel):
    """模型列表响应"""
    object: str = "list"
    data: List[ModelResponse]


# === API 端点 ===

@router.get("/models")
async def list_models(
    request: Request,
    api_key: dict = Depends(verify_api_key)
):
    """
    列出可用模型

    OpenAI 兼容的 /v1/models 端点
    返回所有注册的模型
    """
    mlx_service = get_mlx_service()
    current_model = mlx_service.get_current_model()

    # 获取注册表中的模型
    registry = request.app.state.model_registry
    registered_models = await registry.list_models(active_only=True)

    models = []
    for m in registered_models:
        models.append(ModelResponse(
            id=m.model_id,
            created=int(time.time()),
        ))

    # 如果有当前加载的模型且不在列表中，添加它
    if current_model and not any(m.id == current_model for m in models):
        models.append(ModelResponse(
            id=current_model,
            created=int(time.time()),
        ))

    return ModelsListResponse(data=models)


@router.post("/chat/completions")
async def chat_completions(
    request: Request,
    request_body: ChatCompletionRequest,
    api_key: dict = Depends(verify_api_key),
):
    """
    Chat Completions API

    OpenAI 兼容的聊天接口，支持流式和非流式响应
    """
    mlx_service = get_mlx_service()

    # 生成响应 ID
    completion_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
    created_time = int(time.time())

    # 准备消息
    messages = [{"role": m.role, "content": m.content} for m in request_body.messages]

    if request_body.stream:
        return await _stream_response(
            mlx_service=mlx_service,
            completion_id=completion_id,
            created_time=created_time,
            model=request_body.model,
            messages=messages,
            temperature=request_body.temperature,
            max_tokens=request_body.max_tokens
        )
    else:
        return await _non_stream_response(
            mlx_service=mlx_service,
            completion_id=completion_id,
            created_time=created_time,
            model=request_body.model,
            messages=messages,
            temperature=request_body.temperature,
            max_tokens=request_body.max_tokens
        )


async def _non_stream_response(
    mlx_service,
    completion_id: str,
    created_time: int,
    model: str,
    messages: List[dict],
    temperature: float,
    max_tokens: int
) -> ChatCompletionResponse:
    """生成非流式响应"""
    full_content = ""

    # 提取 system prompt
    system_prompt = None
    chat_messages = []
    for msg in messages:
        if msg["role"] == "system":
            system_prompt = msg["content"]
        else:
            chat_messages.append(msg)

    # 生成响应
    async for token in mlx_service.generate_stream(
        messages=chat_messages,
        temperature=temperature,
        max_tokens=max_tokens,
        system_prompt=system_prompt
    ):
        full_content += token

    # 计算用量
    prompt_tokens = sum(len(m["content"]) for m in messages)
    completion_tokens = len(full_content)

    return ChatCompletionResponse(
        id=completion_id,
        created=created_time,
        model=model,
        choices=[{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": full_content
            },
            "finish_reason": "stop"
        }],
        usage={
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens
        }
    )


async def _stream_response(
    mlx_service,
    completion_id: str,
    created_time: int,
    model: str,
    messages: List[dict],
    temperature: float,
    max_tokens: int
) -> StreamingResponse:
    """生成流式响应"""

    async def event_generator():
        try:
            # 发送初始事件
            yield _format_sse_event({
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created_time,
                "model": model,
                "choices": [{
                    "index": 0,
                    "delta": {"role": "assistant"},
                    "finish_reason": None
                }]
            })

            # 提取 system prompt
            system_prompt = None
            chat_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system_prompt = msg["content"]
                else:
                    chat_messages.append(msg)

            # 流式生成内容
            async for token in mlx_service.generate_stream(
                messages=chat_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt
            ):
                yield _format_sse_event({
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": created_time,
                    "model": model,
                    "choices": [{
                        "index": 0,
                        "delta": {"content": token},
                        "finish_reason": None
                    }]
                })

            # 发送结束事件
            yield _format_sse_event({
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created_time,
                "model": model,
                "choices": [{
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }]
            })

            # 发送 [DONE]
            yield "data: [DONE]\n\n"

        except Exception as e:
            yield _format_sse_event({
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created_time,
                "model": model,
                "choices": [{
                    "index": 0,
                    "delta": {"content": f"\n\nError: {str(e)}"},
                    "finish_reason": "stop"
                }]
            })
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


def _format_sse_event(data: dict) -> str:
    """格式化 SSE 事件"""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
