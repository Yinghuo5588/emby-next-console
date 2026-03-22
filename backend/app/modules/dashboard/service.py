import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis import cache_get, cache_set
from app.core.emby_data import data as emby_data
from app.db.models.playback import PlaybackSession
from app.db.models.notification import Notification
from app.db.models.risk import RiskEvent
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

        # 概览数据
        overview = await _get_overview(self.db)

        # 播放数据
        playback = await _get_playback(self.db)

        # 活跃会话（从 PlaybackSession 表读实时数据）
        sessions = await _get_active_sessions(self.db)

        # 风控
        risk = await _get_risk_summary(self.db)

        # 通知
        notifications = await _get_notification_summary(self.db)

        result = DashboardSummary(
            overview=overview,
            playback=playback,
            sessions=sessions,
            risk=risk,
            notifications=notifications,
        )

        await cache_set(CACHE_KEY, result.model_dump(mode="json"), ttl=CACHE_TTL)
        return result


async def _get_overview(db: AsyncSession) -> OverviewData:
    """从 Emby API 获取概览"""
    try:
        users = await emby_data.get_users()
        active = await emby_data.get_playing_sessions()
        return OverviewData(
            total_users=len(users),
            active_users_today=len(set(s.get("UserId", "") for s in active if s.get("UserId"))),
            current_active_sessions=len(active),
            total_media_count=0,  # TODO: 从 Emby 库获取媒体总数
        )
    except Exception as e:
        logger.warning(f"Emby API 降级: {e}")
        return OverviewData()


async def _get_playback(db: AsyncSession) -> PlaybackData:
    """从 PlaybackSession 表获取今日播放统计"""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    # 今日创建的会话数
    stmt = select(func.count()).select_from(PlaybackSession).where(
        PlaybackSession.started_at >= today_start
    )
    today_count = (await db.execute(stmt)).scalar() or 0

    # 今日播放时长
    dur_stmt = select(func.coalesce(func.sum(PlaybackSession.play_duration), 0)).where(
        PlaybackSession.started_at >= today_start
    )
    today_duration = (await db.execute(dur_stmt)).scalar() or 0

    # 当前活跃会话数
    active_stmt = select(func.count()).select_from(PlaybackSession).where(
        PlaybackSession.status == "active"
    )
    peak = (await db.execute(active_stmt)).scalar() or 0

    return PlaybackData(today_play_count=today_count, today_play_duration_sec=today_duration, peak_concurrent_today=peak)


async def _get_active_sessions(db: AsyncSession) -> list[SessionInfo]:
    """从 PlaybackSession 获取当前活跃会话"""
    stmt = (
        select(PlaybackSession)
        .where(PlaybackSession.status == "active")
        .order_by(PlaybackSession.last_seen_at.desc())
        .limit(20)
    )
    rows = (await db.execute(stmt)).scalars().all()

    # 同时从 Emby API 获取（作为补充）
    try:
        emby_sessions = await emby_data.get_playing_sessions()
    except Exception:
        emby_sessions = []

    # 优先用数据库的，Emby API 补充
    seen_session_ids = {s.emby_session_id for s in rows}
    sessions = []

    for s in rows:
        sessions.append(SessionInfo(
            session_id=s.emby_session_id,
            username=str(s.user_id or "未知"),
            media_name=s.media_name,
            device_name=s.device_name or "",
            client=s.client_name or "",
        ))

    # 补充 Emby API 有但数据库没有的会话
    for es in emby_sessions:
        sid = es.get("Id", "")
        if sid not in seen_session_ids:
            sessions.append(SessionInfo(
                session_id=sid,
                username=es.get("UserName", "未知"),
                media_name=es.get("NowPlayingItem", {}).get("Name", "未知") if es.get("NowPlayingItem") else "未知",
                device_name=es.get("DeviceName", ""),
                client=es.get("Client", ""),
            ))

    return sessions[:20]


async def _get_risk_summary(db: AsyncSession) -> RiskSummaryData:
    """从 RiskEvent 表获取未处理事件数"""
    stmt = select(func.count()).select_from(RiskEvent).where(RiskEvent.status == "open")
    open_count = (await db.execute(stmt)).scalar() or 0

    high_stmt = select(func.count()).select_from(RiskEvent).where(
        RiskEvent.status == "open",
        RiskEvent.severity == "high",
    )
    high_count = (await db.execute(high_stmt)).scalar() or 0

    return RiskSummaryData(open_risk_count=open_count, high_risk_count=high_count)


async def _get_notification_summary(db: AsyncSession) -> NotificationSummaryData:
    """从 Notification 表获取未读通知数"""
    stmt = select(func.count()).select_from(Notification).where(
        Notification.is_read == False,
    )
    unread = (await db.execute(stmt)).scalar() or 0
    return NotificationSummaryData(unread_count=unread)
