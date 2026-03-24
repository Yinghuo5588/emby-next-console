from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedError, ForbiddenError

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    """从 JWT 中提取当前用户（返回 payload dict）"""
    if not credentials:
        raise UnauthorizedError()
    try:
        payload = decode_access_token(credentials.credentials)
        if not payload.get("sub"):
            raise UnauthorizedError()
        return payload
    except jwt.PyJWTError:
        raise UnauthorizedError("Invalid or expired token")


async def get_current_user_id(
    payload: dict = Depends(get_current_user),
) -> str:
    """获取当前用户 ID（Emby UUID）"""
    return payload["sub"]


CurrentUserIdDep = Depends(get_current_user_id)


async def get_current_admin(
    payload: dict = Depends(get_current_user),
) -> dict:
    """校验管理员权限（从 JWT role 字段判断，不查库）"""
    if payload.get("role") != "admin":
        raise ForbiddenError("需要管理员权限")
    return payload


CurrentAdminDep = Depends(get_current_admin)


async def get_current_portal_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    """从 JWT 中提取 portal 用户的 emby_user_id"""
    if not credentials:
        raise UnauthorizedError()
    try:
        payload = decode_access_token(credentials.credentials)
        if payload.get("type") != "portal":
            raise ForbiddenError("需要 portal token")
        emby_user_id = payload.get("sub")
        if not emby_user_id:
            raise UnauthorizedError("无效的 token")
        return emby_user_id
    except jwt.PyJWTError:
        raise UnauthorizedError("Invalid or expired token")
