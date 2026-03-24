from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedError, ForbiddenError

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if not credentials:
        raise UnauthorizedError()
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedError()
        return payload
    except jwt.PyJWTError:
        raise UnauthorizedError("Invalid or expired token")


async def get_current_user_id(
    payload: dict = Depends(get_current_user_payload),
) -> str:
    """从 JWT 提取用户 ID（Emby UUID）"""
    return str(payload.get("sub"))


async def get_current_admin(
    payload: dict = Depends(get_current_user_payload),
) -> dict:
    import logging
    logging.getLogger("app.auth").info(f"Admin check: role={payload.get('role')!r}, is_admin={payload.get('is_admin')!r}")
    if payload.get("role") != "admin" and not payload.get("is_admin", False):
        raise ForbiddenError("Admin access required")
    return payload
