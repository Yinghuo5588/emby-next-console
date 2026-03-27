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
            SettingItem(
                setting_key="EMBY_WEBHOOK_TOKEN",
                setting_group="webhook",
                value=settings.EMBY_WEBHOOK_TOKEN or "",
                description="Webhook 鉴权 Token（环境变量 EMBY_WEBHOOK_TOKEN）",
            ),
            SettingItem(
                setting_key="TMDB_IMG_PROXY",
                setting_group="api",
                value="",
                description="TMDB 图片代理域名，替换 image.tmdb.org",
            ),
        ]

        try:
            stmt = select(SystemSetting)
            result = await self.db.execute(stmt)
            db_settings = {s.setting_key: s for s in result.scalars().all()}
            default_keys = {item.setting_key for item in defaults}
            for item in defaults:
                if item.setting_key in db_settings:
                    db_s = db_settings[item.setting_key]
                    if db_s.value_json is not None:
                        item.value = db_s.value_json
            # 加入数据库中有但 defaults 没有的设置
            for key, db_s in db_settings.items():
                if key not in default_keys and db_s.value_json is not None:
                    defaults.append(SettingItem(
                        setting_key=key,
                        setting_group=db_s.setting_group or "general",
                        value=db_s.value_json,
                        description=None,
                    ))
        except Exception:
            pass

        return defaults

    async def update_setting(self, key: str, value) -> SettingItem:
        from app.db.models.system import SystemSetting
        from sqlalchemy import select
        from datetime import datetime, timezone

        stmt = select(SystemSetting).where(SystemSetting.setting_key == key)
        result = await self.db.execute(stmt)
        setting = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)
        if setting:
            setting.value_json = value
            setting.updated_at = now
        else:
            setting = SystemSetting(
                setting_key=key,
                setting_group="general",
                value_json=value,
                updated_at=now,
            )
            self.db.add(setting)

        await self.db.flush()

        if key == "TMDB_API_KEY":
            from app.core.settings import settings as _s
            _s.TMDB_API_KEY = value or ""

        return SettingItem(setting_key=key, setting_group="general", value=value, description=None)

    async def get_tmdb_setting(self) -> SettingItem:
        value = settings.TMDB_API_KEY or ""
        try:
            all_settings = await self.get_settings()
            for item in all_settings:
                if item.setting_key == "TMDB_API_KEY":
                    value = item.value or ""
                    break
        except Exception:
            pass
        return SettingItem(
            setting_key="TMDB_API_KEY",
            setting_group="api",
            value=value,
            description="TMDB API Key，用于获取媒体简介与图片回退",
        )

    async def update_tmdb_setting(self, value) -> SettingItem:
        return await self.update_setting("TMDB_API_KEY", value or "")

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
        return []
