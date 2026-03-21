from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError
from .schemas import UserDetail, UserListItem, UserListResponse, UserUpdateRequest


class UsersService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_users(self, page: int = 1, page_size: int = 20) -> UserListResponse:
        # TODO: SELECT users JOIN user_profiles
        return UserListResponse(items=[], total=0, page=page, page_size=page_size)

    async def get_user(self, user_id: str) -> UserDetail:
        # TODO: 查询 users + user_profiles
        raise NotFoundError(f"User {user_id} not found")

    async def update_user(self, user_id: str, body: UserUpdateRequest) -> UserDetail:
        # TODO: PATCH users + user_profiles
        raise NotFoundError(f"User {user_id} not found")
