"""
Emby playback_reporting.db SQLite 读取器
同机部署时直接读取 Emby 的数据库文件。
"""
from __future__ import annotations

import logging
import os
import sqlite3
from pathlib import Path
from typing import Any

from app.core.settings import settings

logger = logging.getLogger("app.emby_db")


def _db_exists() -> bool:
    return os.path.isfile(settings.EMBY_DB_PATH)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.EMBY_DB_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_dict(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    return dict(row)


def _rows_to_list(rows: list[sqlite3.Row]) -> list[dict]:
    return [dict(r) for r in rows]


# ── 播放记录查询 ─────────────────────────────────────────────

def get_playback_activity(
    user_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """查询播放记录（PlaybackActivity 表）"""
    if not _db_exists():
        return []
    conditions = ["1=1"]
    params: list[Any] = []
    if user_id:
        conditions.append("UserId = ?")
        params.append(user_id)
    if start_date:
        conditions.append("DateCreated >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("DateCreated <= ?")
        params.append(end_date)
    where = " AND ".join(conditions)
    sql = f"SELECT * FROM PlaybackActivity WHERE {where} ORDER BY DateCreated DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    try:
        conn = _connect()
        rows = conn.execute(sql, params).fetchall()
        conn.close()
        return _rows_to_list(rows)
    except Exception as e:
        logger.error("查询 PlaybackActivity 失败: %s", e)
        return []


def get_today_play_count() -> int:
    if not _db_exists():
        return 0
    try:
        conn = _connect()
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM PlaybackActivity WHERE DateCreated >= date('now', 'start of day')"
        ).fetchone()
        conn.close()
        return row["cnt"] if row else 0
    except Exception as e:
        logger.error("查询今日播放次数失败: %s", e)
        return 0


def get_today_play_duration() -> int:
    """今日播放总时长（秒）"""
    if not _db_exists():
        return 0
    try:
        conn = _connect()
        row = conn.execute(
            "SELECT COALESCE(SUM(PlayDuration), 0) as total FROM PlaybackActivity WHERE DateCreated >= date('now', 'start of day')"
        ).fetchone()
        conn.close()
        return row["total"] if row else 0
    except Exception as e:
        logger.error("查询今日播放时长失败: %s", e)
        return 0


def get_active_users_today() -> int:
    """今日活跃用户数"""
    if not _db_exists():
        return 0
    try:
        conn = _connect()
        row = conn.execute(
            "SELECT COUNT(DISTINCT UserId) as cnt FROM PlaybackActivity WHERE DateCreated >= date('now', 'start of day')"
        ).fetchone()
        conn.close()
        return row["cnt"] if row else 0
    except Exception as e:
        logger.error("查询今日活跃用户失败: %s", e)
        return 0


def get_playback_trend(days: int = 7) -> list[dict]:
    """获取最近 N 天的播放趋势"""
    if not _db_exists():
        return []
    try:
        conn = _connect()
        rows = conn.execute(
            """
            SELECT
                DATE(DateCreated) as date,
                COUNT(*) as play_count,
                COUNT(DISTINCT UserId) as active_users,
                COALESCE(SUM(PlayDuration), 0) as total_duration
            FROM PlaybackActivity
            WHERE DateCreated >= date('now', ? || ' days')
            GROUP BY DATE(DateCreated)
            ORDER BY date ASC
            """,
            (f"-{days}",),
        ).fetchall()
        conn.close()
        return _rows_to_list(rows)
    except Exception as e:
        logger.error("查询播放趋势失败: %s", e)
        return []


def get_user_playback_rank(limit: int = 10) -> list[dict]:
    """用户播放排行"""
    if not _db_exists():
        return []
    try:
        conn = _connect()
        rows = conn.execute(
            """
            SELECT
                UserId as user_id,
                UserName as username,
                COUNT(*) as play_count,
                COALESCE(SUM(PlayDuration), 0) as total_duration
            FROM PlaybackActivity
            WHERE DateCreated >= date('now', '-30 days')
            GROUP BY UserId
            ORDER BY play_count DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        conn.close()
        return _rows_to_list(rows)
    except Exception as e:
        logger.error("查询用户播放排行失败: %s", e)
        return []


def get_media_playback_rank(limit: int = 10) -> list[dict]:
    """热门媒体排行"""
    if not _db_exists():
        return []
    try:
        conn = _connect()
        rows = conn.execute(
            """
            SELECT
                ItemName as item_name,
                COUNT(*) as play_count,
                COUNT(DISTINCT UserId) as unique_users
            FROM PlaybackActivity
            WHERE DateCreated >= date('now', '-30 days')
            GROUP BY ItemName
            ORDER BY play_count DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        conn.close()
        return _rows_to_list(rows)
    except Exception as e:
        logger.error("查询媒体播放排行失败: %s", e)
        return []


def get_user_media_history(user_id: str, limit: int = 50) -> list[dict]:
    """某个用户的播放历史"""
    if not _db_exists():
        return []
    try:
        conn = _connect()
        rows = conn.execute(
            "SELECT * FROM PlaybackActivity WHERE UserId = ? ORDER BY DateCreated DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        conn.close()
        return _rows_to_list(rows)
    except Exception as e:
        logger.error("查询用户播放历史失败: %s", e)
        return []


# ── 执行原始 SQL（用于灵活查询） ──────────────────────────────

def raw_query(sql: str, params: tuple = ()) -> list[dict]:
    """执行任意 SQL 查询（只读场景）"""
    if not _db_exists():
        return []
    try:
        conn = _connect()
        rows = conn.execute(sql, params).fetchall()
        conn.close()
        return _rows_to_list(rows)
    except Exception as e:
        logger.error("原始查询失败: %s | SQL: %s", e, sql[:200])
        return []


def check_db_accessible() -> tuple[bool, str]:
    """检查数据库文件是否可访问"""
    path = settings.EMBY_DB_PATH
    if not os.path.exists(path):
        return False, f"文件不存在: {path}"
    if not os.path.isfile(path):
        return False, f"不是文件: {path}"
    try:
        conn = _connect()
        conn.execute("SELECT COUNT(*) FROM PlaybackActivity").fetchone()
        conn.close()
        return True, "OK"
    except Exception as e:
        return False, str(e)
