from fastapi import APIRouter, Depends, Query

from app.db.session import AsyncSessionDep
from app.core.dependencies import get_current_user_id
from app.shared.responses import ApiResponse
from .schemas import StatsOverview, TopUser, TopMedia, TrendPoint
from .service import StatsService

router = APIRouter(prefix="/stats", tags=["stats"])


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
