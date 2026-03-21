from datetime import datetime
from pydantic import BaseModel
from app.shared.enums import NotificationLevel


class NotificationItem(BaseModel):
    notification_id: str
    type: str
    title: str
    message: str
    level: NotificationLevel
    is_read: bool
    action_url: str | None
    created_at: datetime


class NotificationsResponse(BaseModel):
    items: list[NotificationItem]
    total: int
    unread_count: int


class UnreadCountResponse(BaseModel):
    unread_count: int
