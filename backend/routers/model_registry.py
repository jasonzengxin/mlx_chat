"""
模型注册 API 路由

管理支持的 MLX 模型列表
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from backend.auth.dependencies import verify_api_key
from backend.services.model_registry_service import ModelRegistryService
from backend.routers.settings import get_provider_config_by_name


router = APIRouter()


# === 请求模型 ===

class AddModelRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    model_id: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default="", max_length=500)
    params_count: Optional[str] = Field(default="", max_length=20)
    quantization: Optional[str] = Field(default="", max_length=20)
    model_type: Optional[str] = Field(default="local", max_length=20)
    endpoint: Optional[str] = Field(default="", max_length=200)
    remote_provider: Optional[str] = Field(default="", max_length=100)
    provider_id: Optional[str] = Field(default=None, max_length=100)


class UpdateModelRequest(BaseModel):
    """更新模型请求"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    params_count: Optional[str] = Field(default=None, max_length=20)
    quantization: Optional[str] = Field(default=None, max_length=20)
    is_active: Optional[bool] = None
    endpoint: Optional[str] = Field(default=None, max_length=200)  # for remote models
    remote_provider: Optional[str] = Field(default=None, max_length=100)


# === 辅助函数 ===

def get_model_registry(request: Request) -> ModelRegistryService:
    """获取模型注册服务"""
    return request.app.state.model_registry


# === API 端点 ===

@router.get("")
async def list_models(
    request: Request,
    active_only: bool = True,
    api_key: dict = Depends(verify_api_key),
):
    """
    列出所有支持的模型

    Args:
        active_only: 是否只返回激活的模型 (默认 True)
    """
    registry = get_model_registry(request)
    models = await registry.list_models(active_only=active_only)
    return [m.to_dict() for m in models]


@router.post("")
async def add_model(
    request: Request,
    request_body: AddModelRequest,
    api_key: dict = Depends(verify_api_key),
):
    """
    添加新模型到注册表

    模型 ID 格式:
    - 本地模型: organization/model-name (如 mlx-community/Qwen2.5-7B-4bit)
    - 远程模型: 任意名称 (如 gpt-4o, claude-3-opus)
    """
    registry = get_model_registry(request)

    model_type = request_body.model_type or "local"

    if model_type == "remote":
        # 远程模型 - 只验证非空
        if not request_body.model_id:
            raise HTTPException(
                status_code=400,
                detail="model_id is required for remote models"
            )
    else:
        # 本地模型 - 验证 HuggingFace 格式
        if not await registry.validate_model_id(request_body.model_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid model_id format. Expected: organization/model-name"
            )

    # 检查是否已存在
    existing = await registry.get_model(request_body.model_id)
    if existing and existing.is_active:
        raise HTTPException(
            status_code=409,
            detail=f"Model {request_body.model_id} already exists"
        )

    # Resolve provider credentials for remote models
    remote_base_url = ""
    remote_api_key = ""
    provider_name = request_body.remote_provider or ""

    if model_type == "remote":
        if request_body.provider_id:
            db = request.app.state.db
            prow = await db.fetchone(
                "SELECT * FROM remote_providers WHERE id = ? AND is_active = 1",
                (request_body.provider_id,),
            )
            if prow:
                remote_base_url = prow["base_url"] or ""
                remote_api_key = prow["api_key"] or ""
                provider_name = prow["name"] or provider_name
        elif provider_name:
            db = request.app.state.db
            cfg = await get_provider_config_by_name(db, provider_name)
            remote_base_url = cfg.get("base_url", "")
            remote_api_key = cfg.get("api_key", "")

    # Reactivate soft-deleted model
    if existing and not existing.is_active:
        update_fields: dict = {"is_active": True, "name": request_body.name}
        if request_body.description:
            update_fields["description"] = request_body.description
        if model_type == "remote":
            update_fields["endpoint"] = request_body.endpoint or "/chat/completions"
            update_fields["remote_provider"] = provider_name
            update_fields["remote_base_url"] = remote_base_url
            update_fields["remote_api_key"] = remote_api_key
        model = await registry.update_model(existing.id, **update_fields)
        return model.to_dict()

    # 根据类型添加模型
    if model_type == "remote":
        model = await registry.add_remote_model(
            name=request_body.name,
            model_id=request_body.model_id,
            description=request_body.description or "",
            endpoint=request_body.endpoint or "/chat/completions",
            remote_provider=provider_name,
            remote_base_url=remote_base_url,
            remote_api_key=remote_api_key,
        )
    else:
        model = await registry.add_model(
            name=request_body.name,
            model_id=request_body.model_id,
            description=request_body.description or "",
            params_count=request_body.params_count or "",
            quantization=request_body.quantization or ""
        )

    return model.to_dict()


@router.get("/{model_id}")
async def get_model(
    model_id: str,
    request: Request,
    api_key: dict = Depends(verify_api_key),
):
    """获取模型详情"""
    registry = get_model_registry(request)
    model = await registry.get_model(model_id)

    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    return model.to_dict()


@router.patch("/{model_id}")
async def update_model(
    model_id: str,
    request: Request,
    request_body: UpdateModelRequest,
    api_key: dict = Depends(verify_api_key),
):
    """更新模型信息"""
    registry = get_model_registry(request)

    # 构建更新数据
    update_data = {}
    if request_body.name is not None:
        update_data["name"] = request_body.name
    if request_body.description is not None:
        update_data["description"] = request_body.description
    if request_body.params_count is not None:
        update_data["params_count"] = request_body.params_count
    if request_body.quantization is not None:
        update_data["quantization"] = request_body.quantization
    if request_body.is_active is not None:
        update_data["is_active"] = request_body.is_active
    if request_body.endpoint is not None:
        update_data["endpoint"] = request_body.endpoint
    if request_body.remote_provider is not None:
        update_data["remote_provider"] = request_body.remote_provider

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    model = await registry.update_model(model_id, **update_data)

    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    return model.to_dict()


@router.delete("/{model_id}")
async def delete_model(
    model_id: str,
    request: Request,
    api_key: dict = Depends(verify_api_key),
):
    """
    删除模型 (软删除，设置为不活跃)

    删除后模型仍保留在数据库中，但不会出现在默认列表中
    """
    registry = get_model_registry(request)
    success = await registry.delete_model(model_id)

    if not success:
        raise HTTPException(status_code=404, detail="Model not found")

    return {"success": True, "message": f"Model {model_id} deactivated"}