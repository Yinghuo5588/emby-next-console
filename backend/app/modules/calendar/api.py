"""追剧日历 API"""
from fastapi import APIRouter, Query
from app.shared.responses import ApiResponse
from . import service

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/upcoming")
async def get_calendar(week_offset: int = Query(0, ge=-4, le=4)):
    """获取周历数据"""
    data = await service.get_weekly_calendar(week_offset=week_offset)
    return ApiResponse.ok(data=data)


@router.post("/refresh")
async def refresh_calendar(week_offset: int = Query(0, ge=-4, le=4)):
    """强制刷新周历缓存"""
    data = await service.get_weekly_calendar(week_offset=week_offset, force_refresh=True)
    return ApiResponse.ok(data=data)


@router.get("/emby-info")
async def emby_info():
    """获取 Emby 地址 + ServerId"""
    data = await service.get_emby_info()
    return ApiResponse.ok(data=data)
