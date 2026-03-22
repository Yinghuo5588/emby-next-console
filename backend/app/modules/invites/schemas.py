from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel


class InviteCreateRequest(BaseModel):
    max_uses: int = 1
    expires_days: int | None = None  # 过期天数
    template_emby_user_id: str | None = None
    permission_template_id: int | None = None
    concurrent_limit: int | None = None
    custom_code: str | None = None  # 自定义邀请码，不填自动生成


class InviteCodeResponse(BaseModel):
    id: int
    code: str
    template_emby_user_id: str | None
    permission_template_id: int | None
    max_uses: int
    used_count: int
    expires_at: datetime | None
    concurrent_limit: int | None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class InviteStatsResponse(BaseModel):
    total: int
    active: int
    used: int
    expired: int
    disabled: int


class InviteListResponse(BaseModel):
    items: list[InviteCodeResponse]
    total: int