"""
模型 API 路由

提供模型列表、加载、状态查询
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from backend.auth.dependencies import verify_api_key
from backend.mlx_instance import get_mlx_service


router = APIRouter()


class LoadModelRequest(BaseModel):
    """加载模型请求"""
    model: str  # 可以是 model_id 或 registry 中的 id


def get_model_registry(request: Request):
    """获取模型注册服务"""
    return request.app.state.model_registry


@router.get("")
async def list_models(
    request: Request,
    api_key: dict = Depends(verify_api_key)
):
    """
    获取可用模型列表

    返回所有注册的 MLX 模型
    """
    registry = get_model_registry(request)
    models = await registry.list_models(active_only=True)

    # 获取当前加载的模型
    mlx_service = get_mlx_service()
    current_model = mlx_service.get_current_model()

    result = []
    for m in models:
        model_dict = m.to_dict()
        model_dict["is_loaded"] = (m.model_id == current_model)
        result.append(model_dict)

    return result


@router.post("/load")
async def load_model(
    request: Request,
    request_body: LoadModelRequest,
    api_key: dict = Depends(verify_api_key)
):
    """
    加载指定模型

    model 参数可以是:
    - 模型注册表中的 ID (UUID)
    - HuggingFace 模型 ID (如 mlx-community/Qwen2.5-7B-4bit)
    """
    registry = get_model_registry(request)

    # 尝试从注册表获取模型
    model_info = await registry.get_model(request_body.model)

    if model_info:
        # 使用注册表中的模型 ID
        model_id = model_info.model_id
    else:
        # 直接使用传入的 model 作为 HuggingFace ID
        model_id = request_body.model

    # 加载模型
    mlx_service = get_mlx_service()
    result = await mlx_service.load_model(model_id)

    # 添加模型信息
    if result.get("status") == "loaded" and model_info:
        result["model_info"] = model_info.to_dict()

    return result


@router.get("/current")
async def get_current_model(
    request: Request,
    api_key: dict = Depends(verify_api_key)
):
    """
    获取当前加载的模型

    返回当前加载的模型信息，包括注册表中的详细信息（如果有）
    """
    mlx_service = get_mlx_service()
    current_model_id = mlx_service.get_current_model()

    if current_model_id is None:
        return {"model": None, "model_info": None}

    # 尝试从注册表获取详细信息
    registry = get_model_registry(request)
    model_info = await registry.get_model(current_model_id)

    return {
        "model": current_model_id,
        "model_info": model_info.to_dict() if model_info else None
    }