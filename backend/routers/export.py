"""
导出模板 API 路由

提供模板 CRUD 和知识库导出 API
"""

import json
import time
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional

from backend.auth.dependencies import verify_api_key, get_mlx_service
from backend.services.session_service import SessionService
from backend.services.export_template_service import ExportTemplateService
from backend.services.model_registry_service import ModelRegistryService

router = APIRouter()


# ============================================================
# Request Models
# ============================================================

class CreateTemplateRequest(BaseModel):
    """创建模板请求"""
    name: str
    description: str = ""
    language: str = "both"
    template_content: str
    system_prompt: str


class UpdateTemplateRequest(BaseModel):
    """更新模板请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None
    template_content: Optional[str] = None
    system_prompt: Optional[str] = None


class ExportEstimateRequest(BaseModel):
    """导出预估请求"""
    template_id: str
    language: str = "zh"


class ExportRequest(BaseModel):
    """导出请求"""
    template_id: str
    language: str = "zh"


# ============================================================
# Template CRUD Endpoints
# ============================================================

@router.get("/templates")
async def list_templates(
    request: Request,
    api_key: dict = Depends(verify_api_key)
):
    """列出所有模板"""
    service = ExportTemplateService(request.app.state.db)
    templates = await service.list_templates()

    return [t.to_dict() for t in templates]


@router.get("/templates/{template_id}")
async def get_template(
    template_id: str,
    request: Request,
    api_key: dict = Depends(verify_api_key)
):
    """获取单个模板详情"""
    service = ExportTemplateService(request.app.state.db)
    template = await service.get_template(template_id)

    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")

    return template.to_dict()


@router.post("/templates")
async def create_template(
    request: Request,
    request_body: CreateTemplateRequest,
    api_key: dict = Depends(verify_api_key)
):
    """创建自定义模板"""
    service = ExportTemplateService(request.app.state.db)
    template = await service.create_template(
        name=request_body.name,
        template_content=request_body.template_content,
        system_prompt=request_body.system_prompt,
        description=request_body.description,
        language=request_body.language,
    )

    return template.to_dict()


@router.patch("/templates/{template_id}")
async def update_template(
    template_id: str,
    request: Request,
    request_body: UpdateTemplateRequest,
    api_key: dict = Depends(verify_api_key)
):
    """更新自定义模板"""
    service = ExportTemplateService(request.app.state.db)

    try:
        template = await service.update_template(
            template_id,
            **request_body.model_dump(exclude_unset=True)
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail="Cannot update builtin template")

    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")

    return template.to_dict()


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str,
    request: Request,
    api_key: dict = Depends(verify_api_key)
):
    """删除自定义模板"""
    service = ExportTemplateService(request.app.state.db)

    try:
        result = await service.delete_template(template_id)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Cannot delete builtin template")

    if not result:
        raise HTTPException(status_code=404, detail="Template not found")

    return {"success": True}


# ============================================================
# Export Generation Endpoints
# ============================================================

@router.post("/sessions/{session_id}/export/estimate")
async def estimate_export(
    session_id: str,
    request: Request,
    request_body: ExportEstimateRequest,
    api_key: dict = Depends(verify_api_key)
):
    """预估导出所需的 token 数"""
    service = ExportTemplateService(request.app.state.db)
    session_service = SessionService(request.app.state.db)

    # 验证会话存在
    session = await session_service.get_session(session_id, api_key["id"])
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # 获取模板
    template = await service.get_template(request_body.template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")

    # 预估 token
    estimated_tokens = await service.estimate_export_tokens(
        session_id,
        api_key["id"],
        template
    )

    # 获取消息数
    messages = await session_service.get_messages(session_id, api_key["id"])

    # 检查是否为远程模型
    model_registry: ModelRegistryService = request.app.state.model_registry
    session_model = session.get("model", "")
    model_info = await model_registry.get_model(session_model) if session_model and session_model != "default" else None
    is_remote = model_info.model_type == "remote" if model_info else False

    if is_remote:
        if request_body.language == "zh":
            remote_warning = "此操作将调用远程 API 生成内容，会产生 token 消耗。"
        else:
            remote_warning = "This export calls a remote API and will consume tokens."
    else:
        remote_warning = None

    return {
        "estimated_tokens": estimated_tokens,
        "message_count": len(messages),
        "is_remote": is_remote,
        "warning": remote_warning,
    }


@router.post("/sessions/{session_id}/export")
async def export_session(
    session_id: str,
    request: Request,
    request_body: ExportRequest,
    api_key: dict = Depends(verify_api_key),
    mlx_service = Depends(get_mlx_service),
):
    """导出知识库 (SSE 流式响应)"""
    service = ExportTemplateService(request.app.state.db)
    session_service = SessionService(request.app.state.db)

    # 验证会话存在
    session = await session_service.get_session(session_id, api_key["id"])
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # 获取模板
    template = await service.get_template(request_body.template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")

    # 构建 prompt
    messages, system_prompt = await service.build_export_prompt(
        session_id,
        api_key["id"],
        template,
        request_body.language
    )

    # 获取模型类型
    model_registry: ModelRegistryService = request.app.state.model_registry
    session_model = session.get("model", "")
    model_info = await model_registry.get_model(session_model) if session_model and session_model != "default" else None
    model_type = model_info.model_type if model_info else "local"

    start_time = time.perf_counter()

    async def event_generator():
        try:
            full_response = ""
            first_token_at = None

            if model_type == "remote":
                r_base = getattr(model_info, "remote_base_url", "") or ""
                r_key = getattr(model_info, "remote_api_key", "") or ""

                if not r_base or not r_key:
                    yield f"event: error\ndata: {json.dumps({'error': 'Remote model missing credentials. Re-add this model from a configured provider.'})}\n\n"
                    return

                async for token in _generate_remote_stream(
                    base_url=r_base,
                    api_key=r_key,
                    endpoint=model_info.endpoint or "/chat/completions",
                    model=model_info.model_id,
                    messages=messages,
                    system_prompt=system_prompt,
                ):
                    if first_token_at is None:
                        first_token_at = time.perf_counter()
                    full_response += token
                    yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"
            else:
                if not mlx_service.is_model_loaded():
                    yield f"event: error\ndata: {json.dumps({'error': 'No model loaded. Please select and load a model first.'})}\n\n"
                    return

                async for token in mlx_service.generate_stream(
                    messages=messages,
                    temperature=0.7,
                    max_tokens=4096,
                    system_prompt=system_prompt,
                ):
                    if first_token_at is None:
                        first_token_at = time.perf_counter()
                    full_response += token
                    yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"

            if not full_response.strip():
                yield f"event: error\ndata: {json.dumps({'error': 'Model returned empty content. The session may have no messages, or the model failed to generate.'})}\n\n"
                return

            end_time = time.perf_counter()
            duration_ms = int((end_time - start_time) * 1000)
            ttft_ms = int((first_token_at - start_time) * 1000) if first_token_at else duration_ms

            done_data = json.dumps({
                "total_chars": len(full_response),
                "duration_ms": duration_ms,
                "ttft_ms": ttft_ms,
                "content": full_response,
            })
            yield f"event: done\ndata: {done_data}\n\n"

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


async def _generate_remote_stream(
    base_url: str,
    api_key: str,
    endpoint: str,
    model: str,
    messages: list,
    system_prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 4096,
):
    """生成远程 API 的流式响应"""
    import httpx

    url = f"{base_url}{endpoint}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # 添加 system message
    full_messages = [{"role": "system", "content": system_prompt}] + messages

    payload = {
        "model": model,
        "messages": full_messages,
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
                data = line[6:]
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
