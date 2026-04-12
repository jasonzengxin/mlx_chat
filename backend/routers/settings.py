"""
设置 API 路由

提供设置管理、API Key 管理和远程 Provider 管理
"""

import uuid
from typing import Optional, List
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from backend.auth.dependencies import verify_api_key
from backend.services.auth_service import AuthService
from backend.database import Database


router = APIRouter()


class UpdateSettingsRequest(BaseModel):
    cors_allow_origins: Optional[List[str]] = None
    default_model: Optional[str] = None
    default_temperature: Optional[float] = None
    default_max_tokens: Optional[int] = None


class CreateAPIKeyRequest(BaseModel):
    name: str


def get_auth_service(request: Request) -> AuthService:
    db = request.app.state.db
    return AuthService(db)


def get_db(request: Request) -> Database:
    return request.app.state.db


_app_settings = {
    "cors_allow_origins": ["http://localhost:3000", "http://localhost:8000"],
    "default_model": "mlx-community/Qwen3.5-27B-4bit",
    "default_temperature": 0.7,
    "default_max_tokens": 4096,
}


# ── App Settings ──────────────────────────────────────────

@router.get("")
async def get_settings(api_key: dict = Depends(verify_api_key)):
    return _app_settings


@router.patch("")
async def update_settings(
    request_body: UpdateSettingsRequest,
    api_key: dict = Depends(verify_api_key),
):
    if request_body.cors_allow_origins is not None:
        _app_settings["cors_allow_origins"] = request_body.cors_allow_origins
    if request_body.default_model is not None:
        _app_settings["default_model"] = request_body.default_model
    if request_body.default_temperature is not None:
        _app_settings["default_temperature"] = request_body.default_temperature
    if request_body.default_max_tokens is not None:
        _app_settings["default_max_tokens"] = request_body.default_max_tokens
    return {"success": True}


# ── API Key Management ────────────────────────────────────

@router.get("/api-keys")
async def list_api_keys(
    request: Request,
    api_key: dict = Depends(verify_api_key),
):
    auth_service = get_auth_service(request)
    keys = await auth_service.list_keys()
    return {"keys": keys}


@router.post("/api-keys")
async def create_api_key(
    request: Request,
    request_body: CreateAPIKeyRequest,
    api_key: dict = Depends(verify_api_key),
):
    auth_service = get_auth_service(request)
    key_info, api_key_str, _, _ = await auth_service.create_key(request_body.name)
    return {
        "id": key_info.id,
        "key": api_key_str,
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
    auth_service = get_auth_service(request)
    success = await auth_service.delete_key(key_id)
    if not success:
        raise HTTPException(status_code=404, detail="API Key not found")
    return {"success": True}


# ── Remote Providers (DB-backed) ──────────────────────────

class CreateProviderRequest(BaseModel):
    name: str
    provider_type: Optional[str] = "custom"
    base_url: Optional[str] = ""
    api_key: Optional[str] = ""


class UpdateProviderRequest(BaseModel):
    name: Optional[str] = None
    provider_type: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None


class ValidateProviderRequest(BaseModel):
    base_url: Optional[str] = None
    api_key: Optional[str] = None


def _provider_row_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "provider_type": row["provider_type"] or "custom",
        "base_url": row["base_url"] or "",
        "has_api_key": bool(row["api_key"]),
        "is_active": bool(row["is_active"]),
        "created_at": row["created_at"],
    }


@router.get("/remote/providers")
async def list_providers(
    request: Request,
    api_key: dict = Depends(verify_api_key),
):
    db = get_db(request)
    rows = await db.fetchall(
        "SELECT * FROM remote_providers WHERE is_active = 1 ORDER BY created_at"
    )
    return [_provider_row_to_dict(r) for r in rows]


@router.post("/remote/providers")
async def create_provider(
    request: Request,
    request_body: CreateProviderRequest,
    api_key: dict = Depends(verify_api_key),
):
    db = get_db(request)
    name = request_body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Provider name is required")

    existing = await db.fetchone(
        "SELECT id FROM remote_providers WHERE name = ?", (name,)
    )
    if existing:
        raise HTTPException(status_code=409, detail=f"Provider '{name}' already exists")

    provider_id = str(uuid.uuid4())
    await db.execute(
        """INSERT INTO remote_providers (id, name, provider_type, base_url, api_key)
           VALUES (?, ?, ?, ?, ?)""",
        (provider_id, name, request_body.provider_type or "custom",
         (request_body.base_url or "").rstrip("/"), request_body.api_key or ""),
    )
    await db.commit()

    row = await db.fetchone("SELECT * FROM remote_providers WHERE id = ?", (provider_id,))
    return _provider_row_to_dict(row)


@router.patch("/remote/providers/{provider_id}")
async def update_provider(
    provider_id: str,
    request: Request,
    request_body: UpdateProviderRequest,
    api_key: dict = Depends(verify_api_key),
):
    db = get_db(request)
    row = await db.fetchone(
        "SELECT * FROM remote_providers WHERE id = ?", (provider_id,)
    )
    if not row:
        raise HTTPException(status_code=404, detail="Provider not found")

    updates, values = [], []
    if request_body.name is not None:
        updates.append("name = ?")
        values.append(request_body.name.strip())
    if request_body.provider_type is not None:
        updates.append("provider_type = ?")
        values.append(request_body.provider_type)
    if request_body.base_url is not None:
        updates.append("base_url = ?")
        values.append(request_body.base_url.rstrip("/"))
    if request_body.api_key is not None:
        updates.append("api_key = ?")
        values.append(request_body.api_key)

    if not updates:
        return _provider_row_to_dict(row)

    values.append(provider_id)
    await db.execute(
        f"UPDATE remote_providers SET {', '.join(updates)} WHERE id = ?",
        values,
    )
    await db.commit()

    updated = await db.fetchone("SELECT * FROM remote_providers WHERE id = ?", (provider_id,))
    return _provider_row_to_dict(updated)


@router.delete("/remote/providers/{provider_id}")
async def delete_provider(
    provider_id: str,
    request: Request,
    api_key: dict = Depends(verify_api_key),
):
    db = get_db(request)
    row = await db.fetchone(
        "SELECT id FROM remote_providers WHERE id = ?", (provider_id,)
    )
    if not row:
        raise HTTPException(status_code=404, detail="Provider not found")

    await db.execute(
        "UPDATE remote_providers SET is_active = 0 WHERE id = ?", (provider_id,)
    )
    await db.commit()
    return {"success": True}


@router.post("/remote/providers/{provider_id}/validate")
async def validate_provider(
    provider_id: str,
    request: Request,
    request_body: ValidateProviderRequest,
    api_key: dict = Depends(verify_api_key),
):
    db = get_db(request)
    row = await db.fetchone(
        "SELECT * FROM remote_providers WHERE id = ?", (provider_id,)
    )
    if not row:
        raise HTTPException(status_code=404, detail="Provider not found")

    base_url = (request_body.base_url or row["base_url"] or "").rstrip("/")
    auth_key = request_body.api_key if request_body.api_key else (row["api_key"] or "")

    if not base_url or not auth_key:
        raise HTTPException(
            status_code=400,
            detail="Provider must have both base_url and api_key to validate.",
        )

    result = await _validate_remote_api(base_url, auth_key)
    result["base_url"] = base_url
    result["provider_name"] = row["name"]
    return result


@router.post("/remote/validate")
async def validate_credentials(
    request_body: ValidateProviderRequest,
    api_key: dict = Depends(verify_api_key),
):
    """Validate base_url + api_key without needing an existing provider."""
    base_url = (request_body.base_url or "").rstrip("/")
    auth_key = request_body.api_key or ""

    if not base_url or not auth_key:
        raise HTTPException(
            status_code=400,
            detail="Both base_url and api_key are required for validation.",
        )

    result = await _validate_remote_api(base_url, auth_key)
    result["base_url"] = base_url
    return result


# ── Provider lookup helper ────────────────────────────────

async def get_provider_config_by_name(db: Database, provider_name: str) -> dict:
    """Look up a provider by name. Used by model_registry when copying creds to models."""
    row = await db.fetchone(
        "SELECT * FROM remote_providers WHERE name = ? AND is_active = 1",
        (provider_name,),
    )
    if not row:
        return {"base_url": "", "api_key": ""}
    return {
        "base_url": row["base_url"] or "",
        "api_key": row["api_key"] or "",
        "provider_type": row["provider_type"] or "custom",
    }


# ── Validation helpers ────────────────────────────────────

def _build_models_probe_urls(base_url: str) -> list[str]:
    base = base_url.rstrip("/")
    urls = [f"{base}/models"]
    if not base.endswith("/v1"):
        urls.append(f"{base}/v1/models")
    return urls


async def _validate_remote_api(base_url: str, api_key: str) -> dict:
    probe_urls = _build_models_probe_urls(base_url)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    timeout = httpx.Timeout(20.0)
    last_status_code = None
    last_message = "Validation failed"

    async with httpx.AsyncClient(timeout=timeout) as client:
        for url in probe_urls:
            try:
                response = await client.get(url, headers=headers)
                last_status_code = response.status_code

                if response.status_code == 200:
                    models_count = None
                    try:
                        data = response.json()
                        if isinstance(data, dict) and isinstance(data.get("data"), list):
                            models_count = len(data["data"])
                    except Exception:
                        pass
                    return {
                        "valid": True,
                        "status_code": response.status_code,
                        "message": "API key is valid",
                        "models_count": models_count,
                        "probe_url": url,
                    }

                if response.status_code in (401, 403):
                    return {
                        "valid": False,
                        "status_code": response.status_code,
                        "message": "Invalid API key or insufficient permissions",
                        "models_count": None,
                        "probe_url": url,
                    }

                if response.status_code == 404:
                    last_message = "Provider endpoint not found, trying fallback URL"
                    continue

                body_excerpt = (response.text or "")[:160]
                last_message = f"Provider returned {response.status_code}: {body_excerpt}"
            except httpx.RequestError as exc:
                last_message = f"Network error: {str(exc)}"

    return {
        "valid": False,
        "status_code": last_status_code,
        "message": last_message,
        "models_count": None,
        "probe_url": probe_urls[-1],
    }


# ── Backward-compat shims (keep old endpoints alive temporarily) ──

@router.get("/remote")
async def get_remote_settings_legacy(
    request: Request,
    api_key: dict = Depends(verify_api_key),
):
    db = get_db(request)
    rows = await db.fetchall(
        "SELECT * FROM remote_providers WHERE is_active = 1 ORDER BY created_at"
    )
    providers = [_provider_row_to_dict(r) for r in rows]
    first = providers[0] if providers else {}
    return {
        "provider_name": first.get("name", ""),
        "provider_type": first.get("provider_type", "custom"),
        "base_url": first.get("base_url", ""),
        "has_api_key": first.get("has_api_key", False),
        "default_provider": first.get("name", ""),
        "providers": providers,
    }
