from fastapi import APIRouter, Depends, Query

from app.db.session import AsyncSessionDep
from app.core.dependencies import get_current_user_id
from app.shared.responses import ApiResponse
from .schemas import CalendarMonthResponse, CalendarStatsResponse, CalendarWeekResponse
from .service import CalendarService

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/month", response_model=ApiResponse[CalendarMonthResponse])
async def get_month(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    db: AsyncSessionDep = None,
    _: str = Depends(get_current_user_id),
):
    svc = CalendarService(db)
    return ApiResponse.ok(data=await svc.get_month_entries(year, month))


@router.get("/week", response_model=ApiResponse[CalendarWeekResponse])
async def get_week(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    week: int = Query(..., ge=1, le=5),
    db: AsyncSessionDep = None,
    _: str = Depends(get_current_user_id),
):
    svc = CalendarService(db)
    return ApiResponse.ok(data=await svc.get_week_entries(year, month, week))


@router.get("/upcoming")
async def get_upcoming(days: int = Query(7, ge=1, le=30), db: AsyncSessionDep = None, _: str = Depends(get_current_user_id)):
    svc = CalendarService(db)
    return ApiResponse.ok(data=await svc.get_upcoming(days))


@router.post("/sync")
async def sync_calendar(db: AsyncSessionDep = None, _: str = Depends(get_current_user_id)):
    """从 TMDB 同步播出排期 + Emby 库对比"""
    svc = CalendarService(db)
    synced = await svc.sync_from_tmdb()
    return ApiResponse.ok(data={"synced": synced})


@router.get("/stats", response_model=ApiResponse[CalendarStatsResponse])
async def get_stats(db: AsyncSessionDep = None, _: str = Depends(get_current_user_id)):
    svc = CalendarService(db)
    return ApiResponse.ok(data=await svc.get_stats())
