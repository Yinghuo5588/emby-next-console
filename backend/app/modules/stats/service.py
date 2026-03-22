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
            if total_count > 0:
                return StatsOverview(
                    total_play_count=total_count,
                    total_play_duration_sec=total_duration,
                    unique_users=unique_users,
                    unique_media=0,
                )
        except Exception as e:
            logger.warning("Emby playback stats failed, trying local: %s", e)
        
        # Fallback: 从本地 PlaybackEvent 表获取
        try:
            total_r = await self.db.execute(select(func.count()).select_from(PlaybackEvent))
            total_count = total_r.scalar() or 0
            if total_count > 0:
                from datetime import timedelta
                dur_r = await self.db.execute(
                    select(func.coalesce(func.sum(PlaybackEvent.play_duration), 0))
                )
                users_r = await self.db.execute(
                    select(func.count(func.distinct(PlaybackEvent.user_id)))
                )
                return StatsOverview(
                    total_play_count=total_count,
                    total_play_duration_sec=dur_r.scalar() or 0,
                    unique_users=users_r.scalar() or 0,
                    unique_media=0,
                )
        except Exception:
            pass
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
            query = f"""
                SELECT EXTRACT(HOUR FROM started_at)::int as hour,
                       EXTRACT(DOW FROM started_at)::int as dow,
                       COUNT(*)::int as cnt
                FROM playback_events
                WHERE started_at >= NOW() - INTERVAL '{days} days'
                GROUP BY hour, dow
                ORDER BY hour, dow
            """
            
            result = await self.db.execute(text(query))
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
            query = f"""
                SELECT client_name as device, COUNT(*)::int as cnt
                FROM playback_events
                WHERE started_at >= NOW() - INTERVAL '{days} days'
                    AND client_name IS NOT NULL
                GROUP BY client_name
                ORDER BY cnt DESC
            """
            
            result = await self.db.execute(text(query))
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
            # 从 Emby API 获取各类型的播放量
            from app.core.emby import emby
            # 获取有播放记录的媒体 ID
            items_r = await emby_data.get_media_playback_rank(100)
            if not items_r:
                return []
            
            # 对前 50 个热门媒体查询 Emby 获取 genres
            genre_counts: dict[str, int] = {}
            for item in items_r[:50]:
                item_name = item.get("item_name", "")
                if not item_name:
                    continue
                try:
                    # 搜索媒体获取 genres
                    resp = await emby.get("/Items", params={"searchTerm": item_name, "limit": 1})
                    data = resp.json()
                    items_list = data.get("Items", [])
                    if items_list:
                        genres = items_list[0].get("Genres", [])
                        for g in genres:
                            genre_counts[g] = genre_counts.get(g, 0) + item.get("play_count", 1)
                except Exception:
                    continue
            
            # 排序并返回
            sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:15]
            total = sum(v for _, v in sorted_genres) or 1
            return [
                GenrePreferenceItem(genre=g, count=c, percentage=round(c / total * 100, 1))
                for g, c in sorted_genres
            ]
        except Exception as e:
            logger.error("获取类型偏好失败: %s", e)
            return []

    async def get_hot_rank(self, days: int = 30, limit: int = 20) -> List[HotRankItem]:
        try:
            query = f"""
                SELECT media_name as item_name,
                       COUNT(*)::int as play_count,
                       COUNT(DISTINCT user_id)::int as unique_users
                FROM playback_events
                WHERE started_at >= NOW() - INTERVAL '{days} days'
                GROUP BY media_name
                ORDER BY play_count DESC
                LIMIT {limit}
            """
            
            result = await self.db.execute(text(query))
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
            query = f"""
                SELECT media_name as item_name,
                       SUM(play_duration_sec)::float / 60 as total_duration_min,
                       COUNT(*)::int as play_count
                FROM playback_events
                WHERE started_at >= NOW() - INTERVAL '{days} days'
                GROUP BY media_name
                ORDER BY total_duration_min DESC
                LIMIT {limit}
            """
            
            result = await self.db.execute(text(query))
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
            query = f"""
                SELECT u.username,
                       COUNT(*)::int as play_count,
                       SUM(e.play_duration_sec)::float / 60 as total_duration_min,
                       MAX(e.started_at) as last_played
                FROM playback_events e
                LEFT JOIN users u ON e.user_id = u.id
                WHERE e.started_at >= NOW() - INTERVAL '{days} days'
                GROUP BY u.username, e.user_id
                ORDER BY play_count DESC
                LIMIT {limit}
            """
            
            result = await self.db.execute(text(query))
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
            from app.core.emby import emby
            # 从 Emby 获取最近播放的会话来分析转码率
            try:
                sessions = await emby.get_sessions(active_only=False)
                total_sessions = len(sessions)
                transcode_count = sum(1 for s in sessions if s.get("PlayState", {}).get("PlayMethod") == "Transcode")
                transcoding_rate = round(transcode_count / max(total_sessions, 1) * 100, 1)
            except Exception:
                transcoding_rate = 0.0
            
            # 从 Emby API 获取媒体分辨率分布
            resolution_counts: dict[str, int] = {}
            try:
                resp = await emby.get("/Items", params={"includeItemTypes": "Movie,Episode", "limit": 200, "fields": "MediaSources"})
                data = resp.json()
                for item in data.get("Items", []):
                    for src in item.get("MediaSources", []):
                        for stream in src.get("MediaStreams", []):
                            if stream.get("Type") == "Video":
                                h = stream.get("Height", 0)
                                if h >= 2160:
                                    res = "4K"
                                elif h >= 1080:
                                    res = "1080p"
                                elif h >= 720:
                                    res = "720p"
                                else:
                                    res = "480p"
                                resolution_counts[res] = resolution_counts.get(res, 0) + 1
                                break
            except Exception:
                pass
            
            if not resolution_counts:
                resolution_counts = {"1080p": 0, "720p": 0, "480p": 0, "4K": 0}
            
            resolution_dist = [{"resolution": k, "count": v} for k, v in sorted(resolution_counts.items(), key=lambda x: x[1], reverse=True)]
            
            return QualityAnalysisResponse(resolution_dist=resolution_dist, transcoding_rate=transcoding_rate)
        except Exception as e:
            logger.error("获取质量分析失败: %s", e)
            return QualityAnalysisResponse(resolution_dist=[], transcoding_rate=0.0)
