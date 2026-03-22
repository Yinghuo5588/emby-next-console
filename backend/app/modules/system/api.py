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


# ── 客户端黑名单 ─────────────────────────────────────────────

@router.get("/client-blacklist")
async def get_client_blacklist(db: AsyncSessionDep, _: str = Depends(get_current_user_id)):
    from app.db.models.system import SystemSetting
    from sqlalchemy import select

    stmt = select(SystemSetting).where(SystemSetting.setting_key == "client_blacklist")
    result = await db.execute(stmt)
    setting = result.scalar_one_or_none()
    blacklist = setting.value_json if setting and setting.value_json else []
    return ApiResponse.ok(data=blacklist)


class BlacklistItem:
    def __init__(self, app_name: str = ""):
        self.app_name = app_name


@router.post("/client-blacklist")
async def add_client_blacklist(app_name: str, db: AsyncSessionDep, _: str = Depends(get_current_user_id)):
    from app.db.models.system import SystemSetting
    from sqlalchemy import select
    from datetime import datetime, timezone

    app_name = app_name.strip()
    if not app_name:
        return ApiResponse.error("客户端名不能为空")

    stmt = select(SystemSetting).where(SystemSetting.setting_key == "client_blacklist")
    result = await db.execute(stmt)
    setting = result.scalar_one_or_none()

    if setting:
        current = setting.value_json if isinstance(setting.value_json, list) else []
        if app_name not in current:
            current.append(app_name)
            setting.value_json = current
            setting.updated_at = datetime.now(timezone.utc)
    else:
        setting = SystemSetting(
            setting_key="client_blacklist",
            value_json=[app_name],
            updated_at=datetime.now(timezone.utc),
        )
        db.add(setting)

    return ApiResponse.ok(message=f"已添加 {app_name} 到黑名单")


@router.delete("/client-blacklist/{app_name}")
async def remove_client_blacklist(app_name: str, db: AsyncSessionDep, _: str = Depends(get_current_user_id)):
    from app.db.models.system import SystemSetting
    from sqlalchemy import select
    from datetime import datetime, timezone

    stmt = select(SystemSetting).where(SystemSetting.setting_key == "client_blacklist")
    result = await db.execute(stmt)
    setting = result.scalar_one_or_none()

    if setting and isinstance(setting.value_json, list):
        setting.value_json = [x for x in setting.value_json if x != app_name]
        setting.updated_at = datetime.now(timezone.utc)

    return ApiResponse.ok(message=f"已从黑名单移除 {app_name}")


# ── 实时会话 ─────────────────────────────────────────────

@router.get("/sessions")
async def get_active_sessions(_: str = Depends(get_current_user_id)):
    """获取 Emby 实时播放会话"""
    from app.core.emby import emby
    try:
        sessions = await emby.get_sessions(active_only=False)
        # 只返回有播放内容的会话
        active = [s for s in sessions if s.get("NowPlayingItem")]
        return ApiResponse.ok(data=active)
    except Exception:
        return ApiResponse.ok(data=[])
