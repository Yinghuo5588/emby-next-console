from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis import cache_get, cache_set
from .schemas import DashboardSummary, OverviewData, PlaybackData, RiskSummaryData, NotificationSummaryData

CACHE_KEY = "dashboard:summary"
CACHE_TTL = 30


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_summary(self) -> DashboardSummary:
        cached = await cache_get(CACHE_KEY)
        if cached:
            return DashboardSummary(**cached)

        # TODO: 替换为真实聚合查询
        result = DashboardSummary(
            overview=OverviewData(total_users=0, active_users_today=0, current_active_sessions=0, total_media_count=0),
            playback=PlaybackData(today_play_count=0, today_play_duration_sec=0, peak_concurrent_today=0),
            risk=RiskSummaryData(open_risk_count=0, high_risk_count=0),
            notifications=NotificationSummaryData(unread_count=0),
        )
        await cache_set(CACHE_KEY, result.model_dump(), ttl=CACHE_TTL)
        return result
