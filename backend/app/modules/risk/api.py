from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.db.session import AsyncSessionDep
from app.core.dependencies import get_current_user_id
from app.core.emby import emby
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


# ── 风控执法 ──────────────────────────────────────────────

class KickRequest(BaseModel):
    session_id: str
    reason: str = "管理员强制中止播放"

class UserIdRequest(BaseModel):
    user_id: str


@router.post("/kick")
async def kick_playback(body: KickRequest, db: AsyncSessionDep, _: str = Depends(get_current_user_id)):
    """踢出播放会话"""
    ok = await emby.kick_session(body.session_id, body.reason)
    if ok:
        await RiskService(db).log_action("kick", body.session_id, body.reason)
    return ApiResponse.ok(data={"success": ok})


@router.post("/ban")
async def ban_user(body: UserIdRequest, db: AsyncSessionDep, _: str = Depends(get_current_user_id)):
    """封禁用户"""
    ok = await emby.ban_user(body.user_id)
    if ok:
        await RiskService(db).log_action("ban", body.user_id, "管理员封禁")
    return ApiResponse.ok(data={"success": ok})


@router.post("/unban")
async def unban_user(body: UserIdRequest, db: AsyncSessionDep, _: str = Depends(get_current_user_id)):
    """解封用户"""
    ok = await emby.unban_user(body.user_id)
    if ok:
        await RiskService(db).log_action("unban", body.user_id, "管理员解封")
    return ApiResponse.ok(data={"success": ok})


@router.get("/logs")
async def get_action_logs(
    db: AsyncSessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: str = Depends(get_current_user_id),
):
    """获取执法日志"""
    return ApiResponse.ok(data=await RiskService(db).get_action_logs(page, page_size))
