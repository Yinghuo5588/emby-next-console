from datetime import datetime
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    is_admin: bool = False
    username: str | None = None


class MeResponse(BaseModel):
    id: str
    username: str
    display_name: str | None
    role: str
    emby_user_id: str | None
    avatar_url: str | None
    created_at: datetime | None
