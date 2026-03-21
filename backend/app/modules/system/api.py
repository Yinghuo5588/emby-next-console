from fastapi import APIRouter, Depends

from app.db.session import AsyncSessionDep
from app.core.dependencies import get_current_user_id
from app.shared.responses import ApiResponse
from .schemas import SettingItem, SettingUpdateRequest, HealthResponse, JobRunItem
from .service import SystemService

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/health", response_model=ApiResponse[HealthResponse])
async def health(db: AsyncSessionDep):
    return ApiResponse.ok(data=await SystemService(db).health())


@router.get("/settings", response_model=ApiResponse[list[SettingItem]])
async def get_settings(db: AsyncSessionDep, _: str = Depends(get_current_user_id)):
    return ApiResponse.ok(data=await SystemService(db).get_settings())


@router.patch("/settings/{key}", response_model=ApiResponse[SettingItem])
async def update_setting(key: str, body: SettingUpdateRequest, db: AsyncSessionDep, _: str = Depends(get_current_user_id)):
    return ApiResponse.ok(data=await SystemService(db).update_setting(key, body.value))


@router.get("/jobs", response_model=ApiResponse[list[JobRunItem]])
async def list_jobs(db: AsyncSessionDep, _: str = Depends(get_current_user_id)):
    return ApiResponse.ok(data=await SystemService(db).list_jobs())
