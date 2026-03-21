from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import UnauthorizedError
from app.core.security import verify_password, create_access_token
from app.db.models.user import User


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def login(self, username: str, password: str) -> str:
        stmt = select(User).where(User.username == username)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user or not user.hashed_password:
            raise UnauthorizedError("Invalid username or password")
        if not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Invalid username or password")
        return create_access_token(str(user.id))

    async def get_user_info(self, user_id: str) -> dict:
        stmt = (
            select(User)
            .where(User.id == int(user_id))
            .options(selectinload(User.profile))
        )
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise UnauthorizedError("User not found")
        profile = user.profile
        return {
            "id": str(user.id),
            "username": user.username,
            "display_name": user.display_name,
            "role": user.role,
            "avatar_url": profile.avatar_url if profile else None,
            "created_at": user.created_at,
        }
