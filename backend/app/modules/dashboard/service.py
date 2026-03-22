import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis import cache_get, cache_set
from app.core.emby_data import data as emby_data
from app.shared.schemas import ApiResponse

logger = logging.getLogger("app.dashboard")

CACHE_KEY = "dashboard:summary"
CACHE_TTL = 30


async def get_summary():
    cached = await cache_get(CACHE_KEY)
    if cached:
        return cached

    try:
        raw = await emby_data.get_dashboard_summary()
        overview = raw.get("overview", {})
        playback = raw.get("playback", {})
        sessions = raw.get("sessions", [])

        result = {
            "overview": {
                "total_users": overview.get("total_users", 0),
                "active_users_today": overview.get("active_users_today", 0),
                "current_active_sessions": overview.get("current_active_sessions", 0),
                "total_media_count": 0,
            },
            "playback": {
                "today_play_count": playback.get("today_play_count", 0),
                "today_play_duration_sec": playback.get("today_play_duration_sec", 0),
                "peak_concurrent_today": overview.get("current_active_sessions", 0),
            },
            "risk": {"open_risk_count": 0, "high_risk_count": 0},
            "notifications": {"unread_count": 0},
            "sessions": sessions,
        }

        await cache_set(CACHE_KEY, result, ttl=CACHE_TTL)
        return result
    except Exception as e:
        logger.warning(f"Dashboard fallback: {e}")
        return {
            "overview": {"total_users": 0, "active_users_today": 0, "current_active_sessions": 0, "total_media_count": 0},
            "playback": {"today_play_count": 0, "today_play_duration_sec": 0, "peak_concurrent_today": 0},
            "risk": {"open_risk_count": 0, "high_risk_count": 0},
            "notifications": {"unread_count": 0},
            "sessions": [],
        }
