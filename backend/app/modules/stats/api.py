from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.db.session import AsyncSessionDep
from app.core.dependencies import get_current_user_id
from app.shared.responses import ApiResponse
from .schemas import (
    StatsOverview, TopUser, TopMedia, TrendPoint,
    WatchHistoryResponse, ClockHeatmapResponse, DeviceDistributionItem,
    GenrePreferenceItem, HotRankItem, DurationRankItem, UserRankItem,
    QualityAnalysisResponse
)
from .service import StatsService

router = APIRouter(prefix="/stats", tags=["stats"])
analytics_router = APIRouter(prefix="/admin/analytics", tags=["analytics"])


@router.get("/overview", response_model=ApiResponse[StatsOverview])
async def get_overview(db: AsyncSessionDep, _: str = Depends(get_current_user_id)):
    return ApiResponse.ok(data=await StatsService(db).get_overview())


@router.get("/top-users", response_model=ApiResponse[list[TopUser]])
async def get_top_users(db: AsyncSessionDep, limit: int = Query(10, ge=1, le=50), _: str = Depends(get_current_user_id)):
    return ApiResponse.ok(data=await StatsService(db).get_top_users(limit))


@router.get("/top-media", response_model=ApiResponse[list[TopMedia]])
async def get_top_media(db: AsyncSessionDep, limit: int = Query(10, ge=1, le=50), _: str = Depends(get_current_user_id)):
    return ApiResponse.ok(data=await StatsService(db).get_top_media(limit))


@router.get("/trends", response_model=ApiResponse[list[TrendPoint]])
async def get_trends(db: AsyncSessionDep, days: int = Query(7, ge=1, le=90), _: str = Depends(get_current_user_id)):
    return ApiResponse.ok(data=await StatsService(db).get_trends(days))


# Analytics endpoints
@analytics_router.get("/watch-history", response_model=ApiResponse[WatchHistoryResponse])
async def get_watch_history(
    db: AsyncSessionDep,
    user_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    days: int = Query(30, ge=1, le=365),
    _: str = Depends(get_current_user_id)
):
    return ApiResponse.ok(data=await StatsService(db).get_watch_history(
        user_id=user_id, page=page, page_size=page_size, days=days
    ))


@analytics_router.get("/clock-24h", response_model=ApiResponse[ClockHeatmapResponse])
async def get_clock_heatmap(
    db: AsyncSessionDep,
    days: int = Query(30, ge=1, le=365),
    user_id: Optional[str] = Query(None),
    _: str = Depends(get_current_user_id)
):
    return ApiResponse.ok(data=await StatsService(db).get_clock_heatmap(days=days, user_id=user_id))


@analytics_router.get("/device-dist", response_model=ApiResponse[list[DeviceDistributionItem]])
async def get_device_distribution(
    db: AsyncSessionDep,
    days: int = Query(30, ge=1, le=365),
    _: str = Depends(get_current_user_id)
):
    return ApiResponse.ok(data=await StatsService(db).get_device_distribution(days=days))


@analytics_router.get("/genre-preference", response_model=ApiResponse[list[GenrePreferenceItem]])
async def get_genre_preference(
    db: AsyncSessionDep,
    days: int = Query(30, ge=1, le=365),
    user_id: Optional[str] = Query(None),
    _: str = Depends(get_current_user_id)
):
    return ApiResponse.ok(data=await StatsService(db).get_genre_preference(days=days, user_id=user_id))


@analytics_router.get("/hot-rank", response_model=ApiResponse[list[HotRankItem]])
async def get_hot_rank(
    db: AsyncSessionDep,
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
    _: str = Depends(get_current_user_id)
):
    return ApiResponse.ok(data=await StatsService(db).get_hot_rank(days=days, limit=limit))


@analytics_router.get("/duration-rank", response_model=ApiResponse[list[DurationRankItem]])
async def get_duration_rank(
    db: AsyncSessionDep,
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
    _: str = Depends(get_current_user_id)
):
    return ApiResponse.ok(data=await StatsService(db).get_duration_rank(days=days, limit=limit))


@analytics_router.get("/user-rank", response_model=ApiResponse[list[UserRankItem]])
async def get_user_rank(
    db: AsyncSessionDep,
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
    _: str = Depends(get_current_user_id)
):
    return ApiResponse.ok(data=await StatsService(db).get_user_rank(days=days, limit=limit))


@analytics_router.get("/quality", response_model=ApiResponse[QualityAnalysisResponse])
async def get_quality_analysis(
    db: AsyncSessionDep,
    days: int = Query(30, ge=1, le=365),
    _: str = Depends(get_current_user_id)
):
    return ApiResponse.ok(data=await StatsService(db).get_quality_analysis(days=days))
