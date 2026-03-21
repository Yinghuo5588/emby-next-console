from datetime import datetime

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.notification import Notification
from .schemas import NotificationsResponse, UnreadCountResponse, NotificationItem


class NotificationsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_notifications(self, user_id: str, page: int = 1, page_size: int = 20) -> NotificationsResponse:
        uid = int(user_id)
        offset = (page - 1) * page_size

        # 查用户的通知（自己 + 全局通知）
        base_filter = and_(
            (Notification.user_id == uid) | (Notification.user_id.is_(None)),
        )

        # 总数
        count_stmt = select(func.count()).select_from(Notification).where(base_filter)
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # 未读数
        unread_stmt = select(func.count()).select_from(Notification).where(
            and_(base_filter, Notification.is_read == False)
        )
        unread_count = (await self.db.execute(unread_stmt)).scalar() or 0

        # 列表
        stmt = (
            select(Notification)
            .where(base_filter)
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        rows = (await self.db.execute(stmt)).scalars().all()

        items = [
            NotificationItem(
                notification_id=str(n.id),
                type=n.type,
                title=n.title,
                message=n.message,
                level=n.level,
                is_read=n.is_read,
                action_url=n.action_url,
                created_at=n.created_at,
            )
            for n in rows
        ]

        return NotificationsResponse(items=items, total=total, unread_count=unread_count)

    async def get_unread_count(self, user_id: str) -> UnreadCountResponse:
        uid = int(user_id)
        stmt = select(func.count()).select_from(Notification).where(
            and_(
                (Notification.user_id == uid) | (Notification.user_id.is_(None)),
                Notification.is_read == False,
            )
        )
        count = (await self.db.execute(stmt)).scalar() or 0
        return UnreadCountResponse(unread_count=count)

    async def mark_read(self, notification_id: str, user_id: str) -> None:
        uid = int(user_id)
        stmt = select(Notification).where(
            Notification.id == int(notification_id),
            (Notification.user_id == uid) | (Notification.user_id.is_(None)),
        )
        result = await self.db.execute(stmt)
        notif = result.scalar_one_or_none()
        if not notif:
            return
        notif.is_read = True
        notif.read_at = datetime.utcnow()

    async def mark_all_read(self, user_id: str) -> int:
        uid = int(user_id)
        stmt = select(Notification).where(
            and_(
                (Notification.user_id == uid) | (Notification.user_id.is_(None)),
                Notification.is_read == False,
            )
        )
        rows = (await self.db.execute(stmt)).scalars().all()
        now = datetime.utcnow()
        for n in rows:
            n.is_read = True
            n.read_at = now
        return len(rows)
