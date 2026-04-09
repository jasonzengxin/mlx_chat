"""
模型注册 API 路由

管理支持的 MLX 模型列表
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from backend.auth.dependencies import verify_api_key
from backend.services.model_registry_service import ModelRegistryService


router = APIRouter()


# === 请求模型 ===

class AddModelRequest(BaseModel):
    """添加模型请求"""
    name: str = Field(..., min_length=1, max_length=100)
    model_id: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default="", max_length=500)
    params_count: Optional[str] = Field(default="", max_length=20)
    quantization: Optional[str] = Field(default="", max_length=20)


class UpdateModelRequest(BaseModel):
    """更新模型请求"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    params_count: Optional[str] = Field(default=None, max_length=20)
    quantization: Optional[str] = Field(default=None, max_length=20)
    is_active: Optional[bool] = None


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

    模型 ID 格式: organization/model-name
    例如: mlx-community/Qwen2.5-7B-4bit
    """
    registry = get_model_registry(request)

    # 验证模型 ID 格式
    if not await registry.validate_model_id(request_body.model_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid model_id format. Expected: organization/model-name"
        )

    # 检查是否已存在
    existing = await registry.get_model(request_body.model_id)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Model {request_body.model_id} already exists"
        )

    # 添加模型
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