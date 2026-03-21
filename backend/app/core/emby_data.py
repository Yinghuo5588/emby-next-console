"""
Emby 数据提供器
根据配置自动选择 API 或 SQLite 数据源。
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.settings import settings
from app.core.emby import emby
from app.core import emby_db

logger = logging.getLogger("app.emby_data")

tz_cn = timezone(timedelta(hours=8))


class EmbyDataProvider:
    """统一数据接口，自动路由到 API 或 SQLite。"""

    @property
    def mode(self) -> str:
        if settings.EMBY_DATA_MODE == "auto":
            ok, _ = emby_db.check_db_accessible()
            return "sqlite" if ok else "api"
        return settings.EMBY_DATA_MODE

    def _use_db(self) -> bool:
        return self.mode == "sqlite"

    # ── 用户数据（统一走 API） ────────────────────────────────

    async def get_users(self) -> list[dict]:
        return await emby.get_users()

    async def get_user(self, user_id: str) -> dict:
        return await emby.get_user(user_id)

    # ── 当前会话（统一走 API） ────────────────────────────────

    async def get_playing_sessions(self) -> list[dict]:
        return await emby.get_playing_sessions()

    async def get_all_sessions(self) -> list[dict]:
        return await emby.get_sessions(active_only=False)

    # ── 播放数据 ─────────────────────────────────────────────

    async def get_today_play_count(self) -> int:
        if self._use_db():
            return emby_db.get_today_play_count()
        rows = await emby.query_playback_stats(
            "SELECT COUNT(*) as cnt FROM PlaybackActivity "
            "WHERE DateCreated >= date('now', 'start of day')"
        )
        return rows[0].get("cnt", 0) if rows else 0

    async def get_today_play_duration(self) -> int:
        if self._use_db():
            return emby_db.get_today_play_duration()
        rows = await emby.query_playback_stats(
            "SELECT COALESCE(SUM(PlayDuration), 0) as total FROM PlaybackActivity "
            "WHERE DateCreated >= date('now', 'start of day')"
        )
        return rows[0].get("total", 0) if rows else 0

    async def get_active_users_today(self) -> int:
        if self._use_db():
            return emby_db.get_active_users_today()
        rows = await emby.query_playback_stats(
            "SELECT COUNT(DISTINCT UserId) as cnt FROM PlaybackActivity "
            "WHERE DateCreated >= date('now', 'start of day')"
        )
        return rows[0].get("cnt", 0) if rows else 0

    async def get_playback_trend(self, days: int = 7) -> list[dict]:
        if self._use_db():
            return emby_db.get_playback_trend(days)
        return await emby.query_playback_stats(
            "SELECT DATE(DateCreated) as date, COUNT(*) as play_count, "
            "COUNT(DISTINCT UserId) as active_users, "
            "COALESCE(SUM(PlayDuration), 0) as total_duration "
            f"FROM PlaybackActivity WHERE DateCreated >= date('now', '-{days} days') "
            "GROUP BY DATE(DateCreated) ORDER BY date ASC"
        )

    async def get_user_playback_rank(self, limit: int = 10) -> list[dict]:
        if self._use_db():
            return emby_db.get_user_playback_rank(limit)
        return await emby.query_playback_stats(
            "SELECT UserId as user_id, UserName as username, "
            "COUNT(*) as play_count, COALESCE(SUM(PlayDuration), 0) as total_duration "
            f"FROM PlaybackActivity WHERE DateCreated >= date('now', '-30 days') "
            f"GROUP BY UserId ORDER BY play_count DESC LIMIT {limit}"
        )

    async def get_media_playback_rank(self, limit: int = 10) -> list[dict]:
        if self._use_db():
            return emby_db.get_media_playback_rank(limit)
        return await emby.query_playback_stats(
            "SELECT ItemName as item_name, COUNT(*) as play_count, "
            "COUNT(DISTINCT UserId) as unique_users "
            f"FROM PlaybackActivity WHERE DateCreated >= date('now', '-30 days') "
            f"GROUP BY ItemName ORDER BY play_count DESC LIMIT {limit}"
        )

    async def get_media_library_stats(self) -> list[dict]:
        """获取各媒体库统计"""
        try:
            folders = await emby.get_library_virtual_folders()
            result = []
            for f in folders:
                name = f.get("Name", "未知")
                item_count = f.get("ItemCount", 0)
                result.append({"name": name, "count": item_count})
            return result
        except Exception as e:
            logger.error("获取媒体库统计失败: %s", e)
            return []

    # ── 综合摘要 ─────────────────────────────────────────────

    async def get_dashboard_summary(self) -> dict:
        """仪表盘综合摘要数据"""
        import asyncio

        users, sessions, today_count, today_duration, active_users = await asyncio.gather(
            self.get_users(),
            self.get_playing_sessions(),
            self.get_today_play_count(),
            self.get_today_play_duration(),
            self.get_active_users_today(),
            return_exceptions=True,
        )

        total_users = len(users) if isinstance(users, list) else 0
        sessions = sessions if isinstance(sessions, list) else []
        today_count = today_count if isinstance(today_count, int) else 0
        today_duration = today_duration if isinstance(today_duration, int) else 0
        active_users = active_users if isinstance(active_users, int) else 0

        return {
            "overview": {
                "total_users": total_users,
                "active_users_today": active_users,
                "current_active_sessions": len(sessions),
            },
            "playback": {
                "today_play_count": today_count,
                "today_play_duration_sec": today_duration,
            },
            "sessions": [
                {
                    "session_id": s.get("Id", ""),
                    "username": s.get("UserName", "未知"),
                    "media_name": (s.get("NowPlayingItem") or {}).get("Name", "未知"),
                    "client": s.get("Client", ""),
                    "device_name": s.get("DeviceName", ""),
                }
                for s in sessions
            ],
        }

    # ── 健康检查 ─────────────────────────────────────────────

    async def health_check(self) -> dict[str, Any]:
        api_ok, api_msg = await emby.health_check()
        db_ok, db_msg = emby_db.check_db_accessible()
        return {
            "emby_api": {"ok": api_ok, "message": api_msg},
            "playback_db": {"ok": db_ok, "message": db_msg},
            "data_mode": self.mode,
        }


# ── 全局单例 ──────────────────────────────────────────────────

data = EmbyDataProvider()
