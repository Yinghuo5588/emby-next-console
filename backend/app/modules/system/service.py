import logging

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis import get_redis
from app.core.emby_data import data as emby_data
from app.core.settings import settings
from .schemas import SettingItem, HealthResponse, JobRunItem

logger = logging.getLogger("app.system")


class SystemService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_settings(self) -> list[SettingItem]:
        # TODO: SELECT system_settings
        return []

    async def update_setting(self, key: str, value) -> SettingItem:
        # TODO: UPSERT system_settings
        return SettingItem(setting_key=key, setting_group="general", value=value, description=None)

    async def health(self) -> HealthResponse:
        db_ok = "ok"
        redis_ok = "ok"
        emby_ok = "ok"
        playback_db_ok = "ok"

        try:
            await self.db.execute(sqlalchemy.text("SELECT 1"))
        except Exception:
            db_ok = "error"

        try:
            r = await get_redis()
            await r.ping()
        except Exception:
            redis_ok = "error"

        try:
            checks = await emby_data.health_check()
            emby_ok = "ok" if checks["emby_api"]["ok"] else "error"
            playback_db_ok = "ok" if checks["playback_db"]["ok"] else "unavailable"
        except Exception as e:
            logger.warning("Emby 健康检查失败: %s", e)
            emby_ok = "error"

        status = "ok" if db_ok == "ok" and redis_ok == "ok" else "degraded"

        return HealthResponse(
            status=status,
            db=db_ok,
            redis=redis_ok,
        )

    async def list_jobs(self) -> list[JobRunItem]:
        # TODO: SELECT job_runs ORDER BY created_at DESC LIMIT 50
        return []
