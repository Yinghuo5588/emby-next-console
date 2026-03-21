import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.emby_data import data as emby_data
from .schemas import StatsOverview, TopUser, TopMedia, TrendPoint

logger = logging.getLogger("app.stats")


class StatsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_overview(self) -> StatsOverview:
        try:
            trend = await emby_data.get_playback_trend(30)
            total_count = sum(t.get("play_count", 0) for t in trend)
            total_duration = sum(t.get("total_duration", 0) for t in trend)
            unique_users = sum(t.get("active_users", 0) for t in trend) // max(len(trend), 1)
            return StatsOverview(
                total_play_count=total_count,
                total_play_duration_sec=total_duration,
                unique_users=unique_users,
                unique_media=0,
            )
        except Exception as e:
            logger.error("获取统计概览失败: %s", e)
            return StatsOverview(total_play_count=0, total_play_duration_sec=0, unique_users=0, unique_media=0)

    async def get_top_users(self, limit: int = 10) -> list[TopUser]:
        try:
            rows = await emby_data.get_user_playback_rank(limit)
            return [
                TopUser(
                    user_id=str(r.get("user_id", "")),
                    username=r.get("username", "未知"),
                    play_count=r.get("play_count", 0),
                    play_duration_sec=r.get("total_duration", 0),
                )
                for r in rows
            ]
        except Exception as e:
            logger.error("获取用户排行失败: %s", e)
            return []

    async def get_top_media(self, limit: int = 10) -> list[TopMedia]:
        try:
            rows = await emby_data.get_media_playback_rank(limit)
            return [
                TopMedia(
                    media_id=str(i),
                    media_name=r.get("item_name", "未知"),
                    play_count=r.get("play_count", 0),
                )
                for i, r in enumerate(rows)
            ]
        except Exception as e:
            logger.error("获取媒体排行失败: %s", e)
            return []

    async def get_trends(self, days: int = 7) -> list[TrendPoint]:
        try:
            rows = await emby_data.get_playback_trend(days)
            return [
                TrendPoint(
                    date=r.get("date", ""),
                    play_count=r.get("play_count", 0),
                    active_users=r.get("active_users", 0),
                )
                for r in rows
            ]
        except Exception as e:
            logger.error("获取播放趋势失败: %s", e)
            return []
