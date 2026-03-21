from sqlalchemy.ext.asyncio import AsyncSession
from .schemas import StatsOverview, TopUser, TopMedia, TrendPoint


class StatsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_overview(self) -> StatsOverview:
        # TODO: 聚合 playback_events
        return StatsOverview(total_play_count=0, total_play_duration_sec=0, unique_users=0, unique_media=0)

    async def get_top_users(self, limit: int = 10) -> list[TopUser]:
        # TODO: 查询 playback_events GROUP BY user_id
        return []

    async def get_top_media(self, limit: int = 10) -> list[TopMedia]:
        return []

    async def get_trends(self, days: int = 7) -> list[TrendPoint]:
        return []
