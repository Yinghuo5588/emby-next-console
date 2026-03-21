from datetime import datetime
from pydantic import BaseModel
from app.shared.enums import UserRole, UserStatus


class UserListItem(BaseModel):
    user_id: str
    username: str
    display_name: str | None
    role: UserRole
    status: UserStatus
    expire_at: datetime | None
    is_vip: bool
    created_at: datetime


class UserDetail(UserListItem):
    note: str | None
    max_concurrent: int | None
    emby_user_id: str | None


class UserUpdateRequest(BaseModel):
    display_name: str | None = None
    status: UserStatus | None = None
    expire_at: datetime | None = None
    note: str | None = None
    is_vip: bool | None = None
    max_concurrent: int | None = None


class UserListResponse(BaseModel):
    items: list[UserListItem]
    total: int
    page: int
    page_size: int
