from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError
from .schemas import NotificationsResponse, UnreadCountResponse, NotificationItem


class NotificationsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_notifications(self, user_id: str, page: int = 1, page_size: int = 20) -> NotificationsResponse:
        # TODO: SELECT notifications WHERE user_id = ... OR user_id IS NULL
        return NotificationsResponse(items=[], total=0, unread_count=0)

    async def get_unread_count(self, user_id: str) -> UnreadCountResponse:
        return UnreadCountResponse(unread_count=0)

    async def mark_read(self, notification_id: str, user_id: str) -> None:
        # TODO: UPDATE notifications SET is_read = true
        raise NotFoundError(f"Notification {notification_id} not found")

    async def mark_all_read(self, user_id: str) -> None:
        # TODO: UPDATE notifications SET is_read = true WHERE user_id = ...
        return None
