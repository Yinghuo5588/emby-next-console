from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.dependencies import get_current_user_id
from app.modules.calendar.service import CalendarService

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/month")
async def get_month_entries(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    admin=Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取指定月份的追剧日历条目"""
    svc = CalendarService(db)
    return {"success": True, "data": await svc.get_month_entries(year, month)}


@router.get("/upcoming")
async def get_upcoming(
    days: int = Query(7, ge=1, le=30),
    admin=Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取未来 N 天的更新"""
    svc = CalendarService(db)
    return {"success": True, "data": await svc.get_upcoming(days)}


@router.post("/sync")
async def sync_from_emby(
    admin=Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """从 Emby 同步剧集日历"""
    svc = CalendarService(db)
    count = await svc.sync_from_emby()
    return {"success": True, "data": {"synced": count}}


@router.get("/stats")
async def get_calendar_stats(
    admin=Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """日历统计 — 本月更新数、订阅数等"""
    svc = CalendarService(db)
    return {"success": True, "data": await svc.get_stats()}