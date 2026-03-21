from fastapi import APIRouter, Depends, Query

from app.db.session import AsyncSessionDep
from app.core.dependencies import get_current_user_id
from app.shared.responses import ApiResponse
from .schemas import RiskSummary, RiskEventsResponse, RiskEventAction, RiskEventItem
from .service import RiskService

router = APIRouter(prefix="/risk", tags=["risk"])


@router.get("/summary", response_model=ApiResponse[RiskSummary])
async def get_summary(db: AsyncSessionDep, _: str = Depends(get_current_user_id)):
    return ApiResponse.ok(data=await RiskService(db).get_summary())


@router.get("/events", response_model=ApiResponse[RiskEventsResponse])
async def list_events(
    db: AsyncSessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    severity: str | None = Query(None),
    _: str = Depends(get_current_user_id),
):
    return ApiResponse.ok(data=await RiskService(db).list_events(page, page_size, status, severity))


@router.post("/events/{event_id}/action", response_model=ApiResponse[RiskEventItem])
async def handle_event(event_id: str, body: RiskEventAction, db: AsyncSessionDep, _: str = Depends(get_current_user_id)):
    return ApiResponse.ok(data=await RiskService(db).handle_event_action(event_id, body))
