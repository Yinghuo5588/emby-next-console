"""
统计 API — 全部走 Playback Reporting 插件
前端调用路径:
  /api/v1/stats/overview
  /api/v1/stats/trends
  /api/v1/stats/top-users
  /api/v1/stats/top-media
  /api/v1/admin/analytics/watch-history
  /api/v1/admin/analytics/clock-24h
  /api/v1/admin/analytics/device-dist
  /api/v1/admin/analytics/genre-preferences
  /api/v1/admin/analytics/hot-rank
  /api/v1/admin/analytics/duration-rank
  /api/v1/admin/analytics/user-rank
  /api/v1/admin/analytics/quality
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from app.core.dependencies import get_current_user_id
from app.shared.responses import ApiResponse
from . import service

# ── /stats/* 路由（概览页用） ───────────────────────────────
router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/overview")
async def overview(_: str = Depends(get_current_user_id)):
    return ApiResponse.ok(data=await service.get_overview())


@router.get("/trends")
async def trends(days: int = Query(7, ge=1, le=365), _: str = Depends(get_current_user_id)):
    return ApiResponse.ok(data=await service.get_trend(days))


@router.get("/top-users")
async def top_users(limit: int = Query(10, ge=1, le=50), _: str = Depends(get_current_user_id)):
    return ApiResponse.ok(data=await service.get_top_users(limit))


@router.get("/top-media")
async def top_media(limit: int = Query(10, ge=1, le=50), _: str = Depends(get_current_user_id)):
    return ApiResponse.ok(data=await service.get_top_media(limit))


# ── /admin/analytics/* 路由（数据分析页用） ──────────────────
analytics_router = APIRouter(prefix="/admin/analytics", tags=["analytics"])


@analytics_router.get("/watch-history")
async def analytics_watch_history(
    user_id: Optional[str] = None,
    days: int = Query(30, ge=1, le=365),
    page_size: int = Query(50, ge=1, le=200),
    _: str = Depends(get_current_user_id),
):
    raw = await service.get_watch_history(user_id, page_size, days)
    user_map = await service._get_user_map()
    items = []
    for r in raw:
        uid = str(r.get("UserId", ""))
        dur = r.get("PlayDuration") or 0
        items.append({
            "user_name": user_map.get(uid, f"用户 {uid[:6]}"),
            "item_name": r.get("ItemName", "未知"),
            "device": r.get("client", r.get("DeviceName", "")),
            "start_time": r.get("DateCreated", ""),
            "duration_min": round(dur / 60, 1) if dur else 0,
            "pct_complete": 100,
        })
    return ApiResponse.ok(data={"items": items, "total": len(items)})


@analytics_router.get("/clock-24h")
async def analytics_clock(days: int = Query(30, ge=1, le=365), _: str = Depends(get_current_user_id)):
    grid = await service.get_clock_heatmap(days)
    return ApiResponse.ok(data={"grid": grid})


@analytics_router.get("/device-dist")
async def analytics_device(days: int = Query(30, ge=1, le=365), _: str = Depends(get_current_user_id)):
    return ApiResponse.ok(data=await service.get_device_distribution(days))


@analytics_router.get("/genre-preferences")
async def analytics_genre(days: int = Query(30, ge=1, le=365), _: str = Depends(get_current_user_id)):
    return ApiResponse.ok(data=await service.get_genre_preference(days))


@analytics_router.get("/hot-rank")
async def analytics_hot_rank(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(20, ge=1, le=50),
    _: str = Depends(get_current_user_id),
):
    return ApiResponse.ok(data=await service.get_top_media(limit, days))


@analytics_router.get("/duration-rank")
async def analytics_duration_rank(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(20, ge=1, le=50),
    _: str = Depends(get_current_user_id),
):
    # duration-rank 需要按总时长排序，复用 Playback API
    from app.core.emby import emby
    rows = await emby.query_playback_stats(
        f"SELECT ItemName as item_name, "
        f"ROUND(CAST(SUM(PlayDuration) AS REAL) / 60.0, 1) as total_duration_min, "
        f"COUNT(*) as play_count "
        f"FROM PlaybackActivity "
        f"WHERE DateCreated >= date('now', '-{days} days') "
        f"GROUP BY ItemName ORDER BY total_duration_min DESC LIMIT {limit}"
    )
    return ApiResponse.ok(data=rows)


@analytics_router.get("/user-rank")
async def analytics_user_rank(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(20, ge=1, le=50),
    _: str = Depends(get_current_user_id),
):
    from app.core.emby import emby
    user_map = await service._get_user_map()
    rows = await emby.query_playback_stats(
        f"SELECT UserId as user_id, "
        f"COUNT(*) as play_count, "
        f"ROUND(CAST(SUM(PlayDuration) AS REAL) / 60.0, 1) as total_duration_min, "
        f"MAX(DateCreated) as last_played "
        f"FROM PlaybackActivity "
        f"WHERE DateCreated >= date('now', '-{days} days') "
        f"GROUP BY UserId ORDER BY play_count DESC LIMIT {limit}"
    )
    for r in rows:
        uid = str(r.get("user_id", ""))
        r["username"] = user_map.get(uid, f"用户 {uid[:6]}")
    return ApiResponse.ok(data=rows)


@analytics_router.get("/quality")
async def analytics_quality(days: int = Query(30, ge=1, le=365), _: str = Depends(get_current_user_id)):
    return ApiResponse.ok(data=await service.get_quality_analysis(days))
