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
        """返回默认配置项 + 数据库覆盖项"""
        from app.db.models.system import SystemSetting
        from sqlalchemy import select

        # 默认配置项
        defaults = [
            SettingItem(
                setting_key="TMDB_API_KEY",
                setting_group="api",
                value=settings.TMDB_API_KEY or "",
                description="TMDB API Key，用于获取媒体封面回退",
            ),
            SettingItem(
                setting_key="EMBY_HOST",
                setting_group="emby",
                value=str(settings.EMBY_HOST),
                description="Emby 服务器地址（只读，需改环境变量）",
            ),
        ]

        # 数据库覆盖
        try:
            stmt = select(SystemSetting)
            result = await self.db.execute(stmt)
            db_settings = {s.setting_key: s for s in result.scalars().all()}
            for item in defaults:
                if item.setting_key in db_settings:
                    db_s = db_settings[item.setting_key]
                    if db_s.value_json is not None:
                        item.value = db_s.value_json
                    # value_json only (no value_str column in model)
        except Exception:
            pass

        return defaults

    async def update_setting(self, key: str, value) -> SettingItem:
        """更新配置项"""
        from app.db.models.system import SystemSetting
        from sqlalchemy import select
        from datetime import datetime, timezone

        stmt = select(SystemSetting).where(SystemSetting.setting_key == key)
        result = await self.db.execute(stmt)
        setting = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)
        if setting:
            # SystemSetting only has value_json (JSONB)
            setting.value_json = value
            setting.updated_at = now
        else:
            setting = SystemSetting(
                setting_key=key,
                setting_group="general",
                value_json=value,
                updated_at=now,
            )
            db.add(setting)

        await self.db.flush()

        # 同步到 settings 对象
        if key == "TMDB_API_KEY":
            from app.core.settings import settings as _s
            _s.TMDB_API_KEY = value or ""

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
