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
    max_concurrent: int | None = None
    note: str | None = None


class UserDetail(UserListItem):
    emby_user_id: str | None
    concurrent_limit: int | None = None
    max_bitrate: int | None = None
    allow_transcode: bool | None = None
    client_blacklist: list[str] | None = None


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
