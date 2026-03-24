from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy import select

from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedError, ForbiddenError
from app.db.session import AsyncSessionDep
from app.db.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    if not credentials:
        raise UnauthorizedError()
    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str = payload.get("sub")
        if not user_id:
            raise UnauthorizedError()
        return user_id
    except jwt.PyJWTError:
        raise UnauthorizedError("Invalid or expired token")


CurrentUserIdDep = Depends(get_current_user_id)


async def get_current_admin(
    db: AsyncSessionDep,
    user_id: str = Depends(get_current_user_id),
) -> User:
    """获取当前管理员用户"""
    # 兼容两种 token: auth token sub=int(User.id), portal token sub=emby_user_id(UUID)
    if user_id.isdigit():
        result = await db.execute(select(User).where(User.id == int(user_id)))
    else:
        result = await db.execute(select(User).where(User.emby_user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise UnauthorizedError("用户不存在")
    if user.role != "admin":
        raise ForbiddenError("需要管理员权限")
    return user


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
