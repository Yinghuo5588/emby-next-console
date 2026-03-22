import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import text, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.emby_data import data as emby_data
from app.db.models.playback import PlaybackEvent
from .schemas import (
    StatsOverview, TopUser, TopMedia, TrendPoint,
    WatchHistoryResponse, ClockHeatmapResponse, DeviceDistributionItem,
    GenrePreferenceItem, HotRankItem, DurationRankItem, UserRankItem,
    QualityAnalysisResponse, WatchHistoryItem
)

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

    # Analytics methods
    async def get_watch_history(
        self, user_id: Optional[str] = None, page: int = 1, page_size: int = 20, days: int = 30
    ) -> WatchHistoryResponse:
        try:
            offset = (page - 1) * page_size
            start_time = datetime.utcnow() - timedelta(days=days)
            
            # Build query
            query = select(PlaybackEvent).where(PlaybackEvent.started_at >= start_time)
            
            if user_id:
                # Assuming user_id is string, need to convert to int for foreign key
                try:
                    user_id_int = int(user_id)
                    query = query.where(PlaybackEvent.user_id == user_id_int)
                except ValueError:
                    logger.warning(f"Invalid user_id format: {user_id}")
            
            # Get total count
            count_query = select(func.count()).select_from(PlaybackEvent).where(PlaybackEvent.started_at >= start_time)
            if user_id:
                try:
                    user_id_int = int(user_id)
                    count_query = count_query.where(PlaybackEvent.user_id == user_id_int)
                except ValueError:
                    pass
            
            total_result = await self.db.execute(count_query)
            total = total_result.scalar() or 0
            
            # Get paginated results
            query = query.order_by(PlaybackEvent.started_at.desc()).offset(offset).limit(page_size)
            result = await self.db.execute(query)
            events = result.scalars().all()
            
            items = []
            for event in events:
                duration_min = event.play_duration_sec / 60 if event.play_duration_sec else 0
                items.append(WatchHistoryItem(
                    item_name=event.media_name,
                    user_id=str(event.user_id) if event.user_id else None,
                    username=None,  # Would need to join with users table
                    start_time=event.started_at.isoformat() if event.started_at else "",
                    end_time=event.ended_at.isoformat() if event.ended_at else None,
                    duration_min=round(duration_min, 2),
                    client_name=event.client_name
                ))
            
            return WatchHistoryResponse(
                items=items,
                total=total,
                page=page,
                page_size=page_size
            )
        except Exception as e:
            logger.error("获取观看历史失败: %s", e)
            return WatchHistoryResponse(items=[], total=0, page=page, page_size=page_size)

    async def get_clock_heatmap(self, days: int = 30, user_id: Optional[str] = None) -> ClockHeatmapResponse:
        try:
            query = text("""
                SELECT EXTRACT(HOUR FROM started_at)::int as hour,
                       EXTRACT(DOW FROM started_at)::int as dow,
                       COUNT(*)::int as cnt
                FROM playback_events
                WHERE started_at >= NOW() - INTERVAL ':days days'
                GROUP BY hour, dow
                ORDER BY hour, dow
            """)
            
            result = await self.db.execute(query, {"days": days})
            rows = result.fetchall()
            
            # Initialize 24x7 grid
            grid = [[0] * 7 for _ in range(24)]
            
            for row in rows:
                hour = int(row.hour) if row.hour is not None else 0
                dow = int(row.dow) if row.dow is not None else 0
                cnt = int(row.cnt) if row.cnt is not None else 0
                
                # Ensure indices are within bounds
                if 0 <= hour < 24 and 0 <= dow < 7:
                    grid[hour][dow] = cnt
            
            return ClockHeatmapResponse(grid=grid)
        except Exception as e:
            logger.error("获取生物钟热力图失败: %s", e)
            return ClockHeatmapResponse(grid=[[0] * 7 for _ in range(24)])

    async def get_device_distribution(self, days: int = 30) -> List[DeviceDistributionItem]:
        try:
            query = text("""
                SELECT client_name as device, COUNT(*)::int as cnt
                FROM playback_events
                WHERE started_at >= NOW() - INTERVAL ':days days'
                    AND client_name IS NOT NULL
                GROUP BY client_name
                ORDER BY cnt DESC
            """)
            
            result = await self.db.execute(query, {"days": days})
            rows = result.fetchall()
            
            items = []
            for row in rows:
                device = row.device or "未知设备"
                count = int(row.cnt) if row.cnt is not None else 0
                items.append(DeviceDistributionItem(device=device, count=count))
            
            return items
        except Exception as e:
            logger.error("获取设备分布失败: %s", e)
            return []

    async def get_genre_preference(self, days: int = 30, user_id: Optional[str] = None) -> List[GenrePreferenceItem]:
        try:
            # Since genres field doesn't exist in playback_events table,
            # we'll return empty list for now
            # In a real implementation, this would need to join with media metadata table
            logger.warning("Genre preference analysis not implemented - genres field not available in playback_events")
            return []
        except Exception as e:
            logger.error("获取类型偏好失败: %s", e)
            return []

    async def get_hot_rank(self, days: int = 30, limit: int = 20) -> List[HotRankItem]:
        try:
            query = text("""
                SELECT media_name as item_name,
                       COUNT(*)::int as play_count,
                       COUNT(DISTINCT user_id)::int as unique_users
                FROM playback_events
                WHERE started_at >= NOW() - INTERVAL ':days days'
                GROUP BY media_name
                ORDER BY play_count DESC
                LIMIT :limit
            """)
            
            result = await self.db.execute(query, {"days": days, "limit": limit})
            rows = result.fetchall()
            
            items = []
            for row in rows:
                items.append(HotRankItem(
                    item_name=row.item_name or "未知媒体",
                    play_count=int(row.play_count) if row.play_count is not None else 0,
                    unique_users=int(row.unique_users) if row.unique_users is not None else 0
                ))
            
            return items
        except Exception as e:
            logger.error("获取热度排行失败: %s", e)
            return []

    async def get_duration_rank(self, days: int = 30, limit: int = 20) -> List[DurationRankItem]:
        try:
            query = text("""
                SELECT media_name as item_name,
                       SUM(play_duration_sec)::float / 60 as total_duration_min,
                       COUNT(*)::int as play_count
                FROM playback_events
                WHERE started_at >= NOW() - INTERVAL ':days days'
                GROUP BY media_name
                ORDER BY total_duration_min DESC
                LIMIT :limit
            """)
            
            result = await self.db.execute(query, {"days": days, "limit": limit})
            rows = result.fetchall()
            
            items = []
            for row in rows:
                items.append(DurationRankItem(
                    item_name=row.item_name or "未知媒体",
                    total_duration_min=float(row.total_duration_min) if row.total_duration_min is not None else 0.0,
                    play_count=int(row.play_count) if row.play_count is not None else 0
                ))
            
            return items
        except Exception as e:
            logger.error("获取时长排行失败: %s", e)
            return []

    async def get_user_rank(self, days: int = 30, limit: int = 20) -> List[UserRankItem]:
        try:
            query = text("""
                SELECT u.username,
                       COUNT(*)::int as play_count,
                       SUM(e.play_duration_sec)::float / 60 as total_duration_min,
                       MAX(e.started_at) as last_played
                FROM playback_events e
                LEFT JOIN users u ON e.user_id = u.id
                WHERE e.started_at >= NOW() - INTERVAL ':days days'
                GROUP BY u.username, e.user_id
                ORDER BY play_count DESC
                LIMIT :limit
            """)
            
            result = await self.db.execute(query, {"days": days, "limit": limit})
            rows = result.fetchall()
            
            items = []
            for row in rows:
                last_played = row.last_played.isoformat() if row.last_played else None
                items.append(UserRankItem(
                    username=row.username or "未知用户",
                    play_count=int(row.play_count) if row.play_count is not None else 0,
                    total_duration_min=float(row.total_duration_min) if row.total_duration_min is not None else 0.0,
                    last_played=last_played
                ))
            
            return items
        except Exception as e:
            logger.error("获取用户排行失败: %s", e)
            return []

    async def get_quality_analysis(self, days: int = 30) -> QualityAnalysisResponse:
        try:
            # Since resolution and transcoding info is not available in playback_events table,
            # we'll return placeholder data
            # In a real implementation, this would need additional fields or join with Emby API
            logger.warning("Quality analysis not fully implemented - resolution and transcoding data not available")
            
            # Placeholder resolution distribution
            resolution_dist = [
                {"resolution": "1080p", "count": 0},
                {"resolution": "720p", "count": 0},
                {"resolution": "480p", "count": 0},
                {"resolution": "4K", "count": 0}
            ]
            
            # Placeholder transcoding rate (0% for now)
            transcoding_rate = 0.0
            
            return QualityAnalysisResponse(
                resolution_dist=resolution_dist,
                transcoding_rate=transcoding_rate
            )
        except Exception as e:
            logger.error("获取质量分析失败: %s", e)
            return QualityAnalysisResponse(
                resolution_dist=[],
                transcoding_rate=0.0
            )
