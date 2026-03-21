from datetime import datetime, timezone

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.risk import RiskEvent, RiskRule
from .schemas import RiskSummary, RiskEventItem, RiskEventsResponse, RiskEventAction


class RiskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_summary(self) -> RiskSummary:
        open_stmt = select(func.count()).select_from(RiskEvent).where(RiskEvent.status == "open")
        open_count = (await self.db.execute(open_stmt)).scalar() or 0

        high_stmt = select(func.count()).select_from(RiskEvent).where(
            and_(RiskEvent.status == "open", RiskEvent.severity == "high")
        )
        high_count = (await self.db.execute(high_stmt)).scalar() or 0

        # 最近事件
        recent_stmt = (
            select(RiskEvent)
            .where(RiskEvent.status == "open")
            .order_by(RiskEvent.detected_at.desc())
            .limit(5)
        )
        recent_rows = (await self.db.execute(recent_stmt)).scalars().all()

        return RiskSummary(
            open_count=open_count,
            high_count=high_count,
            recent_events=[_to_item(r) for r in recent_rows],
        )

    async def list_events(
        self, page: int = 1, page_size: int = 20,
        status: str | None = None, severity: str | None = None,
    ) -> RiskEventsResponse:
        filters = []
        if status:
            filters.append(RiskEvent.status == status)
        if severity:
            filters.append(RiskEvent.severity == severity)

        base = select(RiskEvent)
        if filters:
            base = base.where(and_(*filters))

        # 总数
        count_stmt = select(func.count()).select_from(RiskEvent)
        if filters:
            count_stmt = count_stmt.where(and_(*filters))
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # 列表
        stmt = (
            base.order_by(RiskEvent.detected_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self.db.execute(stmt)).scalars().all()

        return RiskEventsResponse(
            items=[_to_item(r) for r in rows],
            total=total,
        )

    async def handle_event_action(self, event_id: str, body: RiskEventAction) -> RiskEventItem:
        stmt = select(RiskEvent).where(RiskEvent.id == int(event_id))
        result = await self.db.execute(stmt)
        event = result.scalar_one_or_none()

        if not event:
            from app.core.exceptions import NotFoundError
            raise NotFoundError(f"Risk event {event_id} not found")

        event.status = body.action  # "resolve" or "ignore"
        if body.action == "resolve":
            event.resolved_at = datetime.now(timezone.utc)

        return _to_item(event)


def _to_item(r: RiskEvent) -> RiskEventItem:
    return RiskEventItem(
        event_id=str(r.id),
        user_id=str(r.user_id or ""),
        event_type=r.event_type,
        severity=r.severity,
        status=r.status,
        title=r.title,
        description=r.description,
        detected_at=r.detected_at,
    )
