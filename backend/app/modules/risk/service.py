from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError
from .schemas import RiskSummary, RiskEventItem, RiskEventsResponse, RiskEventAction


class RiskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_summary(self) -> RiskSummary:
        # TODO: 聚合 risk_events
        return RiskSummary(open_count=0, high_count=0, recent_events=[])

    async def list_events(self, page: int = 1, page_size: int = 20) -> RiskEventsResponse:
        return RiskEventsResponse(items=[], total=0)

    async def handle_event_action(self, event_id: str, action: RiskEventAction) -> RiskEventItem:
        raise NotFoundError(f"Risk event {event_id} not found")
