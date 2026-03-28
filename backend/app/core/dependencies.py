from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
import hashlib

from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedError, ForbiddenError

bearer_scheme = HTTPBearer(auto_error=False)


async def _verify_api_key(x_api_key: str | None = Header(None)) -> dict | None:
    """验证 API Key，返回 key 信息或 None"""
    if not x_api_key:
        return None
    try:
        from app.db.models.api_key import ApiKey
        from app.db.session import AsyncSessionFactory
        from sqlalchemy import select
        from datetime import datetime, timezone

        key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
        async with AsyncSessionFactory() as db:
            result = await db.execute(
                select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active == True)
            )
            key = result.scalar_one_or_none()
            if key:
                key.last_used_at = datetime.now(timezone.utc).replace(tzinfo=None)
                await db.commit()
                return {"type": "api_key", "name": key.name, "scopes": key.scopes}
    except Exception:
        pass
    return None


async def get_current_user_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    x_api_key: str | None = Header(None),
) -> dict:
    # 优先尝试 API Key
    api_key_info = await _verify_api_key(x_api_key)
    if api_key_info:
        return api_key_info

    # 回退到 JWT
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
    if payload.get("role") != "admin" and not payload.get("is_admin", False):
        raise ForbiddenError("Admin access required")
    return payload
