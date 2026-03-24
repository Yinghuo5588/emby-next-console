from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.emby import emby
from app.core.exceptions import UnauthorizedError
from app.core.security import create_access_token
from app.db.models.user import User


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def login(self, username: str, password: str) -> dict:
        """Emby 直接认证，返回 JWT"""
        emby_user = await emby.auth_with_password(username, password)
        if not emby_user:
            raise UnauthorizedError("用户名或密码错误")

        emby_user_id = emby_user.get("Id")
        emby_role = emby_user.get("Policy", {}).get("IsAdministrator", False)
        display_name = emby_user.get("Name") or username

        # 同步到本地 User 表（upsert）
        result = await self.db.execute(
            select(User).where(User.emby_user_id == emby_user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                emby_user_id=emby_user_id,
                username=username,
                display_name=display_name,
                role="admin" if emby_role else "user",
                source="emby",
            )
            self.db.add(user)
        else:
            user.username = username
            user.display_name = display_name
            user.role = "admin" if emby_role else "user"
        await self.db.commit()

        token = create_access_token(
            subject=emby_user_id,
            role=user.role,
        )
        return {
            "access_token": token,
            "is_admin": emby_role,
            "username": username,
        }

    async def get_user_info(self, user_id: str) -> dict:
        """获取当前用户信息"""
        result = await self.db.execute(
            select(User).where(User.emby_user_id == user_id).options(selectinload(User.profile))
        )
        user = result.scalar_one_or_none()
        if not user:
            raise UnauthorizedError("用户不存在")
        profile = user.profile
        return {
            "id": str(user.id),
            "username": user.username,
            "display_name": user.display_name,
            "role": user.role,
            "emby_user_id": user.emby_user_id,
            "avatar_url": emby.get_user_image_url(user.emby_user_id) if user.emby_user_id else None,
            "created_at": user.created_at,
        }
