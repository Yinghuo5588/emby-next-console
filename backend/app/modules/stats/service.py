"""
统计服务 — 全部走 Emby Playback Reporting 插件 API
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.emby import emby
from app.core.emby_data import data as emby_data

logger = logging.getLogger("app.stats")


async def _query(sql: str) -> list[dict]:
    """统一走 Playback Reporting 插件 API"""
    try:
        return await emby.query_playback_stats(sql)
    except Exception as e:
        logger.warning("Playback API 查询失败: %s", e)
        return []


def _clean_name(name: str, item_type: str = "") -> str:
    """智能清洗媒体名称"""
    if not name:
        return "未知内容"
    name = str(name)
    if str(item_type) != "Episode":
        return name.split(" - ")[0]
    # 剧集: "系列名 - S01E05" or "系列名 - 第5集"
    parts = [p.strip() for p in name.split(" - ")]
    series = parts[0]
    cn_map = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    for part in parts[1:]:
        m = re.search(r"(?:S|Season\s*)0*(\d+)", part, re.I)
        if m:
            return f"{series} - 第{int(m.group(1))}季"
        m = re.search(r"第\s*([一二三四五六七八九十\d]+)\s*季", part)
        if m:
            num = cn_map.get(m.group(1), int(m.group(1)) if m.group(1).isdigit() else 1)
            return f"{series} - 第{num}季"
    return series


async def _get_user_map() -> dict:
    """获取 UserId → UserName 映射"""
    try:
        resp = await emby.get("/Users")
        resp.raise_for_status()
        return {u["Id"]: u["Name"] for u in resp.json()}
    except Exception:
        return {}


# ════════════════════════════════════════════════════════════
# 统计服务 — 公开方法
# ════════════════════════════════════════════════════════════

async def get_overview() -> dict:
    """概览数据"""
    rows = await _query(
        "SELECT COUNT(*) as total_plays, "
        "COALESCE(SUM(PlayDuration), 0) as total_duration, "
        "COUNT(DISTINCT UserId) as unique_users "
        "FROM PlaybackActivity"
    )
    r = rows[0] if rows else {}
    today_rows = await _query(
        "SELECT COUNT(*) as cnt FROM PlaybackActivity "
        "WHERE DateCreated >= date('now', 'start of day')"
    )
    return {
        "total_plays": r.get("total_plays", 0),
        "total_duration_sec": r.get("total_duration", 0),
        "unique_users": r.get("unique_users", 0),
        "today_plays": today_rows[0].get("cnt", 0) if today_rows else 0,
    }


async def get_trend(days: int = 7) -> list[dict]:
    """播放趋势"""
    return await _query(
        f"SELECT DATE(DateCreated) as date, COUNT(*) as play_count, "
        f"COUNT(DISTINCT UserId) as active_users, "
        f"COALESCE(SUM(PlayDuration), 0) as total_duration "
        f"FROM PlaybackActivity WHERE DateCreated >= date('now', '-{days} days') "
        f"GROUP BY DATE(DateCreated) ORDER BY date ASC"
    )


async def get_top_users(limit: int = 10) -> list[dict]:
    """用户排行"""
    rows = await _query(
        f"SELECT UserId as user_id, UserName as username, "
        f"COUNT(*) as play_count, COALESCE(SUM(PlayDuration), 0) as total_duration "
        f"FROM PlaybackActivity GROUP BY UserId ORDER BY play_count DESC LIMIT {limit}"
    )
    # 补充用户名
    user_map = await _get_user_map()
    for r in rows:
        uid = str(r.get("user_id", ""))
        r["username"] = user_map.get(uid, r.get("username", f"用户 {uid[:6]}"))
    return rows


async def get_top_media(limit: int = 10, days: int = 30) -> list[dict]:
    """热门媒体排行"""
    rows = await _query(
        f"SELECT ItemName as item_name, ItemId as item_id, ItemType as item_type, "
        f"COUNT(*) as play_count, COALESCE(SUM(PlayDuration), 0) as total_duration "
        f"FROM PlaybackActivity "
        f"WHERE DateCreated >= date('now', '-{days} days') "
        f"GROUP BY ItemName ORDER BY play_count DESC LIMIT {limit}"
    )
    # 智能名称清洗 + 海报
    for r in rows:
        r["clean_name"] = _clean_name(r.get("item_name", ""), r.get("item_type", ""))
        iid = r.get("item_id")
        if iid:
            r["poster_url"] = f"/api/proxy/smart_image?item_id={iid}&type=Primary"
    return rows


async def get_watch_history(
    user_id: Optional[str] = None, limit: int = 50, days: int = 30
) -> list[dict]:
    """观看历史"""
    where = f"DateCreated >= date('now', '-{days} days')"
    if user_id:
        where += f" AND UserId = '{user_id}'"
    return await _query(
        f"SELECT DateCreated, ItemName, ItemId, ItemType, PlayDuration, "
        f"COALESCE(ClientName, DeviceName) as client, UserId "
        f"FROM PlaybackActivity WHERE {where} ORDER BY DateCreated DESC LIMIT {limit}"
    )


async def get_clock_heatmap(days: int = 30) -> list[list[int]]:
    """生物钟热力图 (24x7)"""
    rows = await _query(
        f"SELECT DateCreated FROM PlaybackActivity "
        f"WHERE DateCreated >= date('now', '-{days} days')"
    )
    grid = [[0] * 7 for _ in range(24)]
    for r in rows:
        dc = r.get("DateCreated")
        if dc:
            m = re.search(r"(\d{4})-(\d{2})-(\d{2})[T\s](\d{2})", str(dc))
            if m:
                hour = int(m.group(4))
                try:
                    dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                    dow = dt.weekday()  # 0=Mon, 6=Sun
                except ValueError:
                    continue
                if 0 <= hour < 24 and 0 <= dow < 7:
                    grid[hour][dow] += 1
    return grid


async def get_device_distribution(days: int = 30) -> list[dict]:
    """设备分布"""
    return await _query(
        f"SELECT COALESCE(ClientName, '未知') as device, COUNT(*) as count "
        f"FROM PlaybackActivity "
        f"WHERE DateCreated >= date('now', '-{days} days') "
        f"GROUP BY ClientName ORDER BY count DESC LIMIT 10"
    )


async def get_genre_preference(days: int = 30) -> list[dict]:
    """类型偏好（需要配合 Emby API 查询 genres）"""
    # 先从 PlaybackActivity 获取热门内容
    top = await _query(
        f"SELECT DISTINCT ItemId FROM PlaybackActivity "
        f"WHERE DateCreated >= date('now', '-{days} days') LIMIT 100"
    )
    if not top:
        return []

    # 批量查询 Emby 获取 genres
    ids = ",".join(str(r["ItemId"]) for r in top if r.get("ItemId"))
    if not ids:
        return []
    try:
        resp = await emby.get("/Items", params={"Ids": ids, "Fields": "Genres"})
        resp.raise_for_status()
        items = resp.json().get("Items", [])
    except Exception:
        return []

    genre_counts: dict[str, int] = {}
    for item in items:
        for g in item.get("Genres", []):
            genre_counts[g] = genre_counts.get(g, 0) + 1

    total = sum(genre_counts.values()) or 1
    sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:15]
    return [
        {"genre": g, "count": c, "percentage": round(c / total * 100, 1)}
        for g, c in sorted_genres
    ]


# ── 质量盘点缓存（24h） ──────────────────────────────────
_quality_cache: dict | None = None
_quality_cache_time: float = 0
_QUALITY_CACHE_TTL = 86400  # 24 小时


async def get_quality_analysis(days: int = 30, force_refresh: bool = False) -> dict:
    """质量盘点：分辨率 + 编码 + HDR + 转码率（参考 Emby Pulse）"""
    import time
    global _quality_cache, _quality_cache_time

    now = time.time()
    if not force_refresh and _quality_cache and (now - _quality_cache_time < _QUALITY_CACHE_TTL):
        return _quality_cache

    # 转码率：查当前会话
    transcode_rate = 0.0
    try:
        resp = await emby.get("/Sessions")
        resp.raise_for_status()
        sessions = resp.json()
        total_s = len(sessions) or 1
        transcode = sum(1 for s in sessions if s.get("PlayState", {}).get("PlayMethod") == "Transcode")
        transcode_rate = round(transcode / total_s * 100, 1)
    except Exception:
        pass

    # 扫描所有电影的 MediaStreams
    stats: dict = {
        "total_count": 0,
        "transcoding_rate": transcode_rate,
        "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "resolution": {"4k": 0, "1080p": 0, "720p": 0, "sd": 0},
        "codec": {"hevc": 0, "h264": 0, "av1": 0, "other": 0},
        "hdr": {"dolby_vision": 0, "hdr10": 0, "sdr": 0},
    }

    try:
        resp = await emby.get("/Items", params={
            "IncludeItemTypes": "Movie",
            "Recursive": "true",
            "Fields": "MediaSources,MediaStreams",
        })
        resp.raise_for_status()
        items = resp.json().get("Items", [])
        stats["total_count"] = len(items)

        for item in items:
            media_sources = item.get("MediaSources")
            if not media_sources or not isinstance(media_sources, list):
                continue

            streams = media_sources[0].get("MediaStreams", [])
            video_stream = next((s for s in streams if s.get("Type") == "Video"), None)
            if not video_stream:
                continue

            width = video_stream.get("Width", 0) or 0
            height = video_stream.get("Height", 0) or 0
            if width == 0 and height == 0:
                continue

            # 分辨率
            w = max(width, height)
            if w >= 3800:
                stats["resolution"]["4k"] += 1
            elif w >= 1900:
                stats["resolution"]["1080p"] += 1
            elif w >= 1200:
                stats["resolution"]["720p"] += 1
            else:
                stats["resolution"]["sd"] += 1

            # 编码
            codec = (video_stream.get("Codec") or "").lower()
            if "hevc" in codec or "h265" in codec:
                stats["codec"]["hevc"] += 1
            elif "h264" in codec or "avc" in codec:
                stats["codec"]["h264"] += 1
            elif "av1" in codec:
                stats["codec"]["av1"] += 1
            else:
                stats["codec"]["other"] += 1

            # HDR
            video_range = (video_stream.get("VideoRange") or "").lower()
            display_title = (video_stream.get("DisplayTitle") or "").lower()
            if "dolby" in display_title or "dv" in display_title or "dolby" in video_range:
                stats["hdr"]["dolby_vision"] += 1
            elif "hdr" in video_range or "hdr" in display_title or "pq" in video_range:
                stats["hdr"]["hdr10"] += 1
            else:
                stats["hdr"]["sdr"] += 1

    except Exception as e:
        logger.warning("质量盘点扫描失败: %s", e)

    _quality_cache = stats
    _quality_cache_time = now
    return stats


async def get_badges(user_id: Optional[str] = None) -> list[dict]:
    """趣味成就徽章"""
    where = "1=1"
    if user_id:
        where += f" AND UserId = '{user_id}'"

    rows = await _query(
        f"SELECT DateCreated, PlayDuration, COALESCE(ClientName, DeviceName) as client, "
        f"ItemId, ItemName, ItemType "
        f"FROM PlaybackActivity WHERE {where}"
    )
    if not rows:
        return []

    night_c = weekend_c = fish_c = morning_c = 0
    dur_total = 0
    devices = set()
    items: dict[str, dict] = {}
    movies = eps = 0

    for r in rows:
        dur = r.get("PlayDuration") or 0
        dur_total += dur
        client = r.get("client")
        if client:
            devices.add(client)
        iid = r.get("ItemId")
        if iid:
            items.setdefault(iid, {"name": r.get("ItemName"), "c": 0})
            items[iid]["c"] += 1
        it = r.get("ItemType")
        if it == "Movie":
            movies += 1
        elif it == "Episode":
            eps += 1

        dc = r.get("DateCreated")
        if dc:
            m = re.search(r"(\d{4})-(\d{2})-(\d{2})[T\s](\d{2})", str(dc))
            if m:
                hour = int(m.group(4))
                try:
                    dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                except ValueError:
                    continue
                wd = dt.weekday()
                if 2 <= hour <= 5:
                    night_c += 1
                if wd in (5, 6):
                    weekend_c += 1
                if 0 <= wd <= 4 and 9 <= hour <= 17:
                    fish_c += 1
                if 5 <= hour <= 8:
                    morning_c += 1

    badges = []
    if night_c >= 2:
        badges.append({"id": "night", "name": "深夜修仙", "icon": "fa-moon", "color": "text-indigo-500", "bg": "bg-indigo-100", "desc": "深夜是灵魂最自由的时刻"})
    if weekend_c >= 5:
        badges.append({"id": "weekend", "name": "周末狂欢", "icon": "fa-champagne-glasses", "color": "text-pink-500", "bg": "bg-pink-100", "desc": "工作日唯唯诺诺，周末重拳出击"})
    if dur_total > 180000:
        badges.append({"id": "liver", "name": "核心肝帝", "icon": "fa-fire", "color": "text-red-500", "bg": "bg-red-100", "desc": "阅片无数，肝度爆表"})
    if fish_c >= 5:
        badges.append({"id": "fish", "name": "带薪观影", "icon": "fa-fish", "color": "text-cyan-500", "bg": "bg-cyan-100", "desc": "工作是老板的，快乐是自己的"})
    if morning_c >= 2:
        badges.append({"id": "morning", "name": "晨练追剧", "icon": "fa-sun", "color": "text-amber-500", "bg": "bg-amber-100", "desc": "比你优秀的人，连看片都比你早"})
    if len(devices) >= 2:
        badges.append({"id": "device", "name": "全平台制霸", "icon": "fa-gamepad", "color": "text-emerald-500", "bg": "bg-emerald-100", "desc": "手机、平板、电视，哪里都能看"})

    if items:
        loyal = max(items.values(), key=lambda x: x["c"])
        if loyal["c"] >= 3:
            safe = str(loyal.get("name") or "未知").split(" - ")[0][:10]
            badges.append({"id": "loyal", "name": "N刷狂魔", "icon": "fa-repeat", "color": "text-teal-500", "bg": "bg-teal-100", "desc": f"对《{safe}》爱得深沉"})

    total = movies + eps
    if total > 10:
        if movies / total > 0.6:
            badges.append({"id": "movie_lover", "name": "电影鉴赏家", "icon": "fa-film", "color": "text-blue-500", "bg": "bg-blue-100", "desc": "沉浸在两小时的艺术光影世界"})
        elif eps / total > 0.6:
            badges.append({"id": "tv_lover", "name": "追剧狂魔", "icon": "fa-tv", "color": "text-purple-500", "bg": "bg-purple-100", "desc": "一集接一集，根本停不下来"})

    return badges
