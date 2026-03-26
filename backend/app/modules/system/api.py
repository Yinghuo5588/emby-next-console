from fastapi import APIRouter

from app.db.session import AsyncSessionDep
from app.shared.responses import ApiResponse
from .schemas import SettingItem, SettingUpdateRequest, HealthResponse, JobRunItem
from .service import SystemService

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/health", response_model=ApiResponse[HealthResponse])
async def health(db: AsyncSessionDep):
    return ApiResponse.ok(data=await SystemService(db).health())


@router.get("/settings", response_model=ApiResponse[list[SettingItem]])
async def get_settings(db: AsyncSessionDep):
    return ApiResponse.ok(data=await SystemService(db).get_settings())


@router.patch("/settings/{key}", response_model=ApiResponse[SettingItem])
async def update_setting(key: str, body: SettingUpdateRequest, db: AsyncSessionDep):
    return ApiResponse.ok(data=await SystemService(db).update_setting(key, body.value))


@router.get("/settings/tmdb", response_model=ApiResponse[SettingItem])
async def get_tmdb_setting(db: AsyncSessionDep):
    return ApiResponse.ok(data=await SystemService(db).get_tmdb_setting())


@router.put("/settings/tmdb", response_model=ApiResponse[SettingItem])
async def update_tmdb_setting(body: SettingUpdateRequest, db: AsyncSessionDep):
    return ApiResponse.ok(data=await SystemService(db).update_tmdb_setting(body.value))


@router.get("/jobs", response_model=ApiResponse[list[JobRunItem]])
async def list_jobs(db: AsyncSessionDep):
    return ApiResponse.ok(data=await SystemService(db).list_jobs())


@router.get("/sessions")
async def get_active_sessions():
    """获取 Emby 实时播放会话（公开，用于管控页）"""
    from app.core.emby import emby
    try:
        sessions = await emby.get_sessions(active_only=False)
        active = [s for s in sessions if s.get("NowPlayingItem")]
        return ApiResponse.ok(data=active)
    except Exception:
        return ApiResponse.ok(data=[])
