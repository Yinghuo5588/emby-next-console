import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis import cache_get, cache_set
from app.core.emby_data import data as emby_data
from .schemas import (
    DashboardSummary, OverviewData, PlaybackData,
    RiskSummaryData, NotificationSummaryData, SessionInfo,
)

logger = logging.getLogger("app.dashboard")

CACHE_KEY = "dashboard:summary"
CACHE_TTL = 30


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_summary(self) -> DashboardSummary:
        cached = await cache_get(CACHE_KEY)
        if cached:
            return DashboardSummary(**cached)

        try:
            raw = await emby_data.get_dashboard_summary()
            overview = raw.get("overview", {})
            playback = raw.get("playback", {})
            sessions_raw = raw.get("sessions", [])

            result = DashboardSummary(
                overview=OverviewData(
                    total_users=overview.get("total_users", 0),
                    active_users_today=overview.get("active_users_today", 0),
                    current_active_sessions=overview.get("current_active_sessions", 0),
                    total_media_count=0,  # 需要单独查询
                ),
                playback=PlaybackData(
                    today_play_count=playback.get("today_play_count", 0),
                    today_play_duration_sec=playback.get("today_play_duration_sec", 0),
                    peak_concurrent_today=playback.get("peak_concurrent_today", 0),
                ),
                risk=RiskSummaryData(open_risk_count=0, high_risk_count=0),
                notifications=NotificationSummaryData(unread_count=0),
                sessions=[SessionInfo(**s) for s in sessions_raw],
            )
        except Exception as e:
            logger.error("获取仪表盘摘要失败: %s", e)
            result = DashboardSummary(
                overview=OverviewData(total_users=0, active_users_today=0, current_active_sessions=0, total_media_count=0),
                playback=PlaybackData(today_play_count=0, today_play_duration_sec=0, peak_concurrent_today=0),
                risk=RiskSummaryData(open_risk_count=0, high_risk_count=0),
                notifications=NotificationSummaryData(unread_count=0),
                sessions=[],
            )

        await cache_set(CACHE_KEY, result.model_dump(), ttl=CACHE_TTL)
        return result

    async def get_trend(self, days: int = 7) -> list[dict]:
        try:
            return await emby_data.get_playback_trend(days)
        except Exception as e:
            logger.error("获取播放趋势失败: %s", e)
            return []

    async def get_top_users(self, limit: int = 10) -> list[dict]:
        try:
            return await emby_data.get_user_playback_rank(limit)
        except Exception as e:
            logger.error("获取用户排行失败: %s", e)
            return []

    async def get_top_media(self, limit: int = 10) -> list[dict]:
        try:
            return await emby_data.get_media_playback_rank(limit)
        except Exception as e:
            logger.error("获取热门媒体失败: %s", e)
            return []
