from datetime import datetime
from pydantic import BaseModel
from app.shared.enums import RiskSeverity, RiskEventStatus


class RiskEventItem(BaseModel):
    event_id: str
    user_id: str
    event_type: str
    severity: RiskSeverity
    status: RiskEventStatus
    title: str
    description: str | None
    detected_at: datetime


class RiskSummary(BaseModel):
    open_count: int
    high_count: int
    recent_events: list[RiskEventItem]


class RiskEventAction(BaseModel):
    action: str  # ignore / resolve


class RiskEventsResponse(BaseModel):
    items: list[RiskEventItem]
    total: int
