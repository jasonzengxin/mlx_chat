"""
会话 API 路由

提供会话 CRUD 操作
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel

from backend.auth.dependencies import verify_api_key
from backend.services.session_service import SessionService
from backend.database import Database


router = APIRouter()


class CreateSessionRequest(BaseModel):
    """创建会话请求"""
    name: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 4096
    system_prompt: Optional[str] = ""
    context_messages: Optional[int] = 20


class UpdateSessionRequest(BaseModel):
    """更新会话请求"""
    name: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    context_messages: Optional[int] = None


def get_session_service(request: Request) -> SessionService:
    """获取会话服务"""
    db = request.app.state.db
    return SessionService(db)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_session(
    request: Request,
    request_body: CreateSessionRequest,
    api_key: dict = Depends(verify_api_key),
):
    """创建新会话"""
    session_service = get_session_service(request)

    session = await session_service.create_session(
        api_key_id=api_key["id"],
        name=request_body.name,
        model=request_body.model or "default",
        temperature=request_body.temperature,
        max_tokens=request_body.max_tokens,
        system_prompt=request_body.system_prompt,
        context_messages=request_body.context_messages,
    )

    return session


@router.get("")
async def list_sessions(
    request: Request,
    api_key: dict = Depends(verify_api_key),
):
    """列出所有会话"""
    session_service = get_session_service(request)

    sessions = await session_service.list_sessions(api_key["id"])
    return sessions


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    request: Request,
    api_key: dict = Depends(verify_api_key),
):
    """获取会话详情"""
    session_service = get_session_service(request)

    session = await session_service.get_session(session_id, api_key["id"])
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # 获取消息
    messages = await session_service.get_messages(session_id, api_key["id"])

    return {**session, "messages": messages}


@router.patch("/{session_id}")
async def update_session(
    session_id: str,
    request: Request,
    request_body: UpdateSessionRequest,
    api_key: dict = Depends(verify_api_key),
):
    """更新会话"""
    session_service = get_session_service(request)

    update_data = {}
    if request_body.name is not None:
        update_data["name"] = request_body.name
    if request_body.model is not None:
        update_data["model"] = request_body.model
    if request_body.temperature is not None:
        update_data["temperature"] = request_body.temperature
    if request_body.max_tokens is not None:
        update_data["max_tokens"] = request_body.max_tokens
    if request_body.system_prompt is not None:
        update_data["system_prompt"] = request_body.system_prompt
    if request_body.context_messages is not None:
        update_data["context_messages"] = request_body.context_messages

    session = await session_service.update_session(
        session_id,
        api_key["id"],
        **update_data
    )

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return session


@router.delete("", status_code=status.HTTP_200_OK)
async def delete_all_sessions(
    request: Request,
    api_key: dict = Depends(verify_api_key),
):
    """删除所有会话"""
    session_service = get_session_service(request)

    count = await session_service.delete_all_sessions(api_key["id"])

    return {"deleted_count": count}


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    request: Request,
    api_key: dict = Depends(verify_api_key),
):
    """删除会话"""
    session_service = get_session_service(request)

    success = await session_service.delete_session(session_id, api_key["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")