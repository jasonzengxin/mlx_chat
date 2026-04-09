"""
设置 API 路由

提供设置管理和 API Key 管理
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from backend.auth.dependencies import verify_api_key
from backend.services.auth_service import AuthService
from backend.database import Database


router = APIRouter()


class UpdateSettingsRequest(BaseModel):
    """更新设置请求"""
    cors_allow_origins: Optional[List[str]] = None
    default_model: Optional[str] = None
    default_temperature: Optional[float] = None
    default_max_tokens: Optional[int] = None


class CreateAPIKeyRequest(BaseModel):
    """创建 API Key 请求"""
    name: str


def get_auth_service(request: Request) -> AuthService:
    """获取认证服务"""
    db = request.app.state.db
    return AuthService(db)


# 应用设置
_app_settings = {
    "cors_allow_origins": ["http://localhost:3000", "http://localhost:8000"],
    "default_model": "mlx-community/Qwen3.5-27B-4bit",
    "default_temperature": 0.7,
    "default_max_tokens": 4096,
}


@router.get("")
async def get_settings(
    api_key: dict = Depends(verify_api_key),
):
    """获取应用设置"""
    return _app_settings


@router.patch("")
async def update_settings(
    request_body: UpdateSettingsRequest,
    api_key: dict = Depends(verify_api_key),
):
    """更新应用设置"""
    if request_body.cors_allow_origins is not None:
        _app_settings["cors_allow_origins"] = request_body.cors_allow_origins
    if request_body.default_model is not None:
        _app_settings["default_model"] = request_body.default_model
    if request_body.default_temperature is not None:
        _app_settings["default_temperature"] = request_body.default_temperature
    if request_body.default_max_tokens is not None:
        _app_settings["default_max_tokens"] = request_body.default_max_tokens

    return {"success": True}


# === API Key 管理 ===

@router.get("/api-keys")
async def list_api_keys(
    request: Request,
    api_key: dict = Depends(verify_api_key),
):
    """列出所有 API Keys (不含密钥)"""
    auth_service = get_auth_service(request)
    keys = await auth_service.list_keys()
    return {"keys": keys}


@router.post("/api-keys")
async def create_api_key(
    request: Request,
    request_body: CreateAPIKeyRequest,
    api_key: dict = Depends(verify_api_key),
):
    """创建新 API Key"""
    auth_service = get_auth_service(request)
    key_info, api_key_str, _, _ = await auth_service.create_key(request_body.name)

    return {
        "id": key_info.id,
        "key": api_key_str,  # 创建时返回明文
        "name": key_info.name,
        "key_prefix": key_info.key_prefix,
        "created_at": key_info.created_at.isoformat(),
    }


@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    request: Request,
    api_key: dict = Depends(verify_api_key),
):
    """删除 API Key"""
    auth_service = get_auth_service(request)
    success = await auth_service.delete_key(key_id)

    if not success:
        raise HTTPException(status_code=404, detail="API Key not found")

    return {"success": True}