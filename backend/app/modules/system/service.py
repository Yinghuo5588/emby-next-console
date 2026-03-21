import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession
from app.cache.redis import get_redis
from .schemas import SettingItem, HealthResponse, JobRunItem


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
        try:
            await self.db.execute(sqlalchemy.text("SELECT 1"))
        except Exception:
            db_ok = "error"
        try:
            r = await get_redis()
            await r.ping()
        except Exception:
            redis_ok = "error"
        status = "ok" if db_ok == "ok" and redis_ok == "ok" else "degraded"
        return HealthResponse(status=status, db=db_ok, redis=redis_ok)

    async def list_jobs(self) -> list[JobRunItem]:
        # TODO: SELECT job_runs ORDER BY created_at DESC LIMIT 50
        return []
