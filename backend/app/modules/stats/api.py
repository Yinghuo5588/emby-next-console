"""统计 API — 全部走 Playback Reporting 插件"""
from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user_id
from app.shared.responses import ApiResponse
from . import service

router = APIRouter(prefix="/stats", tags=["stats"])
analytics_router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
async def overview(_: str = Depends(get_current_user_id)):
    return ApiResponse.ok(data=await service.get_overview())


@router.get("/trend")
async def trend(days: int = Query(7, ge=1, le=365), _: str = Depends(get_current_user_id)):
    return ApiResponse.ok(data=await service.get_trend(days))


@router.get("/top-users")
async def top_users(limit: int = Query(10, ge=1, le=50), _: str = Depends(get_current_user_id)):
    return ApiResponse.ok(data=await service.get_top_users(limit))


@router.get("/top-media")
async def top_media(
    limit: int = Query(10, ge=1, le=50),
    days: int = Query(30, ge=1, le=365),
    _: str = Depends(get_current_user_id),
):
    return ApiResponse.ok(data=await service.get_top_media(limit, days))


@router.get("/watch-history")
async def watch_history(
    user_id: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    days: int = Query(30, ge=1, le=365),
    _: str = Depends(get_current_user_id),
):
    return ApiResponse.ok(data=await service.get_watch_history(user_id, limit, days))


@router.get("/clock-heatmap")
async def clock_heatmap(days: int = Query(30, ge=1, le=365), _: str = Depends(get_current_user_id)):
    return ApiResponse.ok(data=await service.get_clock_heatmap(days))


@router.get("/device-dist")
async def device_dist(days: int = Query(30, ge=1, le=365), _: str = Depends(get_current_user_id)):
    return ApiResponse.ok(data=await service.get_device_distribution(days))


@router.get("/genre-pref")
async def genre_pref(days: int = Query(30, ge=1, le=365), _: str = Depends(get_current_user_id)):
    return ApiResponse.ok(data=await service.get_genre_preference(days))


@router.get("/quality")
async def quality(days: int = Query(30, ge=1, le=365), _: str = Depends(get_current_user_id)):
    return ApiResponse.ok(data=await service.get_quality_analysis(days))


@router.get("/badges")
async def badges(user_id: str | None = None, _: str = Depends(get_current_user_id)):
    return ApiResponse.ok(data=await service.get_badges(user_id))


# Analytics — 别名路由，前端可能用 /analytics/ 前缀
@analytics_router.get("/clock-heatmap")
async def analytics_heatmap(days: int = Query(30, ge=1, le=365), _: str = Depends(get_current_user_id)):
    return ApiResponse.ok(data=await service.get_clock_heatmap(days))


@analytics_router.get("/device-dist")
async def analytics_device(days: int = Query(30, ge=1, le=365), _: str = Depends(get_current_user_id)):
    return ApiResponse.ok(data=await service.get_device_distribution(days))
