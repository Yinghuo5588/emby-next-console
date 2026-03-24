from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
import logging
from sqlalchemy import select

from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedError, ForbiddenError
from app.db.session import AsyncSessionDep
from app.db.models.user import User

logger = logging.getLogger("app.auth")
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    """从 JWT 中提取当前用户 payload"""
    if not credentials:
        logger.warning("get_current_user: no credentials provided")
        raise UnauthorizedError()
    try:
        logger.debug(f"get_current_user: decoding token of length {len(credentials.credentials)}")
        payload = decode_access_token(credentials.credentials)
        logger.debug(f"get_current_user: decoded sub={payload.get('sub')}, role={payload.get('role')}")
        if not payload.get("sub"):
            raise UnauthorizedError()
        return payload
    except jwt.PyJWTError as e:
        logger.warning(f"get_current_user: JWT decode failed: {type(e).__name__}: {e}")
        raise UnauthorizedError("Invalid or expired token")


async def get_current_user_id(
    payload: dict = Depends(get_current_user),
) -> str:
    return payload["sub"]


CurrentUserIdDep = Depends(get_current_user_id)


async def get_current_admin(
    db: AsyncSessionDep,
    payload: dict = Depends(get_current_user),
) -> User:
    """校验管理员权限（JWT role 字段）并返回 User 对象"""
    if payload.get("role") != "admin":
        raise ForbiddenError("需要管理员权限")
    emby_user_id = payload["sub"]
    result = await db.execute(select(User).where(User.emby_user_id == emby_user_id).order_by(User.id).limit(1))
    user = result.scalar_one_or_none()
    if not user:
        raise UnauthorizedError("用户不存在")
    return user


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
