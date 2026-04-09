"""
认证依赖注入

功能:
- API Key 验证
- 依赖注入
"""

from typing import Optional

from fastapi import Depends, HTTPException, Header, Request

from backend.services.auth_service import AuthService
from backend.services.session_service import SessionService
from backend.services.usage_service import UsageService
from backend.services.mlx_service import MLXService
from backend.mlx_instance import get_mlx_service


def get_db(request: Request):
    """从 app.state 获取数据库"""
    return request.app.state.db


def get_auth_service(request: Request) -> AuthService:
    """获取认证服务"""
    db = get_db(request)
    return AuthService(db)


def get_session_service(request: Request) -> SessionService:
    """获取会话服务"""
    db = get_db(request)
    return SessionService(db)


def get_usage_service(request: Request) -> UsageService:
    """获取用量服务"""
    db = get_db(request)
    return UsageService(db)


async def verify_api_key(
    request: Request,
    authorization: Optional[str] = Header(None),
    auth_service: AuthService = Depends(get_auth_service)
) -> dict:
    """
    验证 API Key 的依赖

    Header: Authorization: Bearer <key>
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header"
        )

    try:
        scheme, key = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization scheme. Use 'Bearer <key>'"
            )
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format"
        )

    api_key = await auth_service.verify_and_update(key)
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    return api_key