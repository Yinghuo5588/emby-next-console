"""
统计服务 V3 — 全部走 Emby Playback Reporting 插件 API
"""
from __future__ import annotations

import logging
import re
import urllib.parse
from datetime import datetime, timedelta, timezone

import httpx

from app.core.emby import emby
from app.core.settings import settings

logger = logging.getLogger("app.stats")


# ════════════════════════════════════════════════════════════
# 工具函数
# ════════════════════════════════════════════════════════════

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


def _build_proxy_image(item_id: str | None, img_type: str, name: str = "") -> str:
    if not item_id:
        return ""
    return f"/api/v1/proxy/smart_image?item_id={item_id}&type={img_type}&name={urllib.parse.quote(name or '')}"


def _extract_quality_tags(file_name: str | None) -> list[str]:
    if not file_name:
        return []
    fn = str(file_name).upper()
    tags: list[str] = []
    if "2160P" in fn or "4K" in fn:
        tags.append("4K")
    elif "1080P" in fn:
        tags.append("1080P")
    elif "720P" in fn:
        tags.append("720P")

    if "HDR10+" in fn:
        tags.append("HDR10+")
    elif "HDR" in fn and "SDR" not in fn:
        tags.append("HDR")
    elif "DV" in fn or "DOLBY.VISION" in fn or "DOLBYVISION" in fn:
        tags.append("DV")

    if "H.265" in fn or "HEVC" in fn or "X265" in fn:
        tags.append("H.265")
    elif "H.264" in fn or "AVC" in fn or "X264" in fn:
        tags.append("H.264")
    return tags


async def _enrich_media_cards(items: list[dict]) -> None:
    """补充媒体卡片常用字段：poster/backdrop/title/meta/quality_tags
    不修改 item_id，让 proxy 按原始 ID 自己解析上溯源码"""
    for item in items:
        iid = item.get("item_id")
        name = item.get("name", "")
        item_type = item.get("type", "")
        item["poster_url"] = _build_proxy_image(iid, "Primary", name)
        item["backdrop_url"] = _build_proxy_image(iid, "Backdrop", name)
        item["display_title"] = name
        item["display_subtitle"] = "剧集" if item_type in ("Series", "Episode") else "电影" if item_type == "Movie" else item_type or "媒体"
        item.setdefault("quality_tags", [])


def _period_filter(period: str) -> str:
    """时间范围条件"""
    if period == "7d":
        return "DateCreated >= date('now', '-7 days')"
    elif period == "30d":
        return "DateCreated >= date('now', '-30 days')"
    elif period == "90d":
        return "DateCreated >= date('now', '-90 days')"
    else:  # all
        return "1=1"


async def _get_user_map() -> dict:
    """获取 UserId → UserName 映射"""
    try:
        resp = await emby.get("/Users")
        resp.raise_for_status()
        return {u["Id"]: u["Name"] for u in resp.json()}
    except Exception:
        return {}


async def search_tmdb_first(name: str, media_type: str = "movie") -> dict:
    """调用 TMDB search API，返回首个结果的 overview、poster_path、backdrop_path"""
    api_key = (settings.TMDB_API_KEY or "").strip()
    if not api_key or not name.strip():
        return {"overview": "", "poster_path": "", "backdrop_path": ""}

    async def _do_search(client, url, params):
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        first = (data.get("results") or [{}])[0] if (data.get("results") or []) else {}
        return {
            "overview": first.get("overview") or "",
            "poster_path": first.get("poster_path") or "",
            "backdrop_path": first.get("backdrop_path") or "",
        }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            base = {"api_key": api_key, "query": name.strip(), "language": "zh-CN"}
            # 先按类型搜索
            result = await _do_search(client, f"https://api.themoviedb.org/3/search/{media_type}", base)
            # 没结果时用 multi 搜索
            if not result["overview"] and not result["poster_path"]:
                result = await _do_search(client, "https://api.themoviedb.org/3/search/multi", base)
            return result
    except Exception as e:
        logger.warning("TMDB 查询失败: %s", e)
        return {"overview": "", "poster_path": "", "backdrop_path": ""}


# ════════════════════════════════════════════════════════════
# 总览页
# ════════════════════════════════════════════════════════════

async def get_overview(period: str = "30d") -> dict:
    """核心指标（按 period 筛选）+ 媒体库总量"""
    pf = _period_filter(period)

    rows = await _query(
        f"SELECT COUNT(*) as total_plays, "
        f"COALESCE(SUM(PlayDuration), 0) as total_duration, "
        f"COUNT(DISTINCT UserId) as unique_users "
        f"FROM PlaybackActivity WHERE {pf}"
    )
    r = rows[0] if rows else {}

    library = {"movie": 0, "series": 0, "episode": 0}
    try:
        resp = await emby.get("/Items/Counts")
        resp.raise_for_status()
        d = resp.json()
        library = {
            "movie": d.get("MovieCount", 0),
            "series": d.get("SeriesCount", 0),
            "episode": d.get("EpisodeCount", 0),
        }
    except Exception:
        pass

    return {
        "total_plays": r.get("total_plays", 0),
        "total_duration_hours": round(r.get("total_duration", 0) / 3600, 1),
        "active_users": r.get("unique_users", 0),
        "library": library,
    }


async def get_trend_by_period(period: str = "30d") -> dict:
    """播放趋势：只有播放时长"""
    if period == "7d":
        rows = await _query(
            "SELECT DATE(DateCreated) as label, "
            "COALESCE(SUM(PlayDuration), 0) as duration "
            "FROM PlaybackActivity WHERE DateCreated >= date('now', '-7 days') "
            "GROUP BY label ORDER BY label"
        )
    elif period == "90d":
        rows = await _query(
            "SELECT strftime('%Y-%m-%d', DateCreated) as label, "
            "COALESCE(SUM(PlayDuration), 0) as duration "
            "FROM PlaybackActivity WHERE DateCreated >= date('now', '-90 days') "
            "GROUP BY label ORDER BY label"
        )
    elif period == "all":
        rows = await _query(
            "SELECT substr(replace(DateCreated, 'T', ' '), 1, 7) as label, "
            "COALESCE(SUM(PlayDuration), 0) as duration "
            "FROM PlaybackActivity "
            "GROUP BY label ORDER BY label"
        )
    else:
        rows = await _query(
            "SELECT DATE(DateCreated) as label, "
            "COALESCE(SUM(PlayDuration), 0) as duration "
            "FROM PlaybackActivity WHERE DateCreated >= date('now', '-30 days') "
            "GROUP BY label ORDER BY label"
        )

    return {r["label"]: round(r["duration"] / 3600, 1) for r in rows} if rows else {}


async def get_top_content(limit: int = 5, period: str = "7d") -> list[dict]:
    pf = _period_filter(period)
    rows = await _query(
        f"SELECT ItemName, ItemId, ItemType, "
        f"COUNT(*) as play_count, COALESCE(SUM(PlayDuration), 0) as total_duration "
        f"FROM PlaybackActivity WHERE {pf} "
        f"GROUP BY ItemName ORDER BY total_duration DESC LIMIT {limit * 3}"
    )
    agg: dict[str, dict] = {}
    for r in rows:
        clean = _clean_name(r.get("ItemName", ""), r.get("ItemType", ""))
        if clean not in agg:
            agg[clean] = {
                "item_id": r.get("ItemId"),
                "name": clean,
                "type": r.get("ItemType", ""),
                "play_count": 0,
                "total_duration_hours": 0,
            }
        agg[clean]["play_count"] += r.get("play_count", 0)
        agg[clean]["total_duration_hours"] += round(r.get("total_duration", 0) / 3600, 1)

    result = sorted(agg.values(), key=lambda x: x["total_duration_hours"], reverse=True)[:limit]
    await _enrich_media_cards(result)
    return result


async def get_top_users_ranked(limit: int = 5, period: str = "7d") -> list[dict]:
    pf = _period_filter(period)
    rows = await _query(
        f"SELECT UserId as user_id, "
        f"COUNT(*) as play_count, COALESCE(SUM(PlayDuration), 0) as total_duration "
        f"FROM PlaybackActivity WHERE {pf} "
        f"GROUP BY UserId ORDER BY total_duration DESC LIMIT {limit}"
    )
    user_map = await _get_user_map()
    result = []
    for r in rows:
        uid = str(r.get("user_id", ""))
        result.append({
            "user_id": uid,
            "username": user_map.get(uid, f"用户 {uid[:6]}"),
            "play_count": r.get("play_count", 0),
            "total_duration_hours": round(r.get("total_duration", 0) / 3600, 1),
        })
    return result


# ════════════════════════════════════════════════════════════
# 内容分析页
# ════════════════════════════════════════════════════════════

async def get_content_rankings(
    content_type: str = "all",
    period: str = "30d",
    sort: str = "duration",
    search: str = None,
    page: int = 1,
    size: int = 20,
    user_id: str = None,
) -> dict:
    pf = _period_filter(period) if not search else "1=1"

    type_filter = ""
    if not search and content_type == "movie":
        type_filter = " AND ItemType = 'Movie'"
    elif not search and content_type == "series":
        type_filter = " AND ItemType IN ('Series', 'Episode')"

    user_filter = f" AND UserId = '{str(user_id).replace(chr(39), chr(39)+chr(39))}'" if user_id else ""
    search_filter = ""
    if search:
        kw = search.replace("'", "''").strip()
        search_filter = f" AND ItemName LIKE '%{kw}%'"

    order = "total_duration DESC" if sort == "duration" else "play_count DESC"

    rows = await _query(
        f"SELECT ItemName, ItemId, ItemType, "
        f"COUNT(*) as play_count, COALESCE(SUM(PlayDuration), 0) as total_duration "
        f"FROM PlaybackActivity WHERE {pf}{type_filter}{user_filter}{search_filter} "
        f"GROUP BY ItemName ORDER BY {order} LIMIT 500"
    )

    agg: dict[str, dict] = {}
    for r in rows:
        clean = _clean_name(r.get("ItemName", ""), r.get("ItemType", ""))
        if clean not in agg:
            agg[clean] = {
                "item_id": r.get("ItemId"),
                "name": clean,
                "type": r.get("ItemType", ""),
                "play_count": 0,
                "total_duration_min": 0,
                "quality_tags": _extract_quality_tags(r.get("file_name")),
            }
        agg[clean]["play_count"] += r.get("play_count", 0)
        agg[clean]["total_duration_min"] += round(r.get("total_duration", 0) / 60, 1)

    all_items = sorted(
        agg.values(),
        key=lambda x: x["total_duration_min"] if sort == "duration" else x["play_count"],
        reverse=True,
    )

    total = len(all_items)
    start = (page - 1) * size
    page_items = all_items[start : start + size]

    await _enrich_media_cards(page_items)
    return {"total": total, "items": page_items}


async def get_content_detail(item_id: str, period: str = "30d") -> dict:
    safe_id = str(item_id).replace("'", "''")

    db_rows = await _query(
        f"SELECT ItemName FROM PlaybackActivity WHERE ItemId = '{safe_id}' LIMIT 1"
    )
    db_name = db_rows[0]["ItemName"] if db_rows and db_rows[0].get("ItemName") else "未知"

    overview = ""
    production_year = None
    quality_tags: list[str] = []
    item_type = ""
    name = db_name
    try:
        resp = await emby.get(f"/Items/{item_id}")
        if resp.status_code == 200:
            info = resp.json()
            name = info.get("Name") or db_name
            item_type = info.get("Type", "")
            overview = info.get("Overview", "") or ""
            production_year = info.get("ProductionYear")
            path_or_name = info.get("Path") or info.get("FileName") or ""
            quality_tags = _extract_quality_tags(path_or_name)
    except Exception:
        pass

    if not overview.strip():
        tmdb_type = "tv" if item_type in ("Series", "Episode") else "movie"
        # 优先用 Emby 原始标题搜索 TMDB，去掉 " - 第N季" 等后缀
        orig_name = ""
        try:
            orig_name = info.get("OriginalTitle") or ""
        except Exception:
            pass
        search_name = orig_name or name
        # 去掉 " - 第1季" / " - Season 1" 等后缀
        search_name = re.split(r'\s*-\s*(?:第\d+季|Season\s*\d+|S\d+)', search_name, flags=re.I)[0].strip()
        tmdb_data = await search_tmdb_first(name=search_name, media_type=tmdb_type)
        overview = tmdb_data.get("overview") or overview

    pf = _period_filter(period)
    rows = await _query(
        f"SELECT DATE(DateCreated) as date, COUNT(*) as play_count, "
        f"COALESCE(SUM(PlayDuration), 0) as duration "
        f"FROM PlaybackActivity WHERE ItemId = '{safe_id}' "
        f"AND {pf} "
        f"GROUP BY date ORDER BY date"
    )
    trend = {r["date"]: {"plays": r["play_count"], "hours": round(r["duration"] / 3600, 1)} for r in rows} if rows else {}

    user_rows = await _query(
        f"SELECT UserId, COUNT(*) as play_count, COALESCE(SUM(PlayDuration), 0) as duration "
        f"FROM PlaybackActivity WHERE ItemId = '{safe_id}' "
        f"GROUP BY UserId ORDER BY duration DESC"
    )
    user_map = await _get_user_map()
    viewers = []
    for r in user_rows:
        uid = str(r.get("UserId", ""))
        viewers.append({
            "user_id": uid,
            "username": user_map.get(uid, f"用户 {uid[:6]}"),
            "play_count": r.get("play_count", 0),
            "duration_hours": round(r.get("duration", 0) / 3600, 1),
        })

    return {
        "name": name,
        "type": item_type,
        "trend": trend,
        "viewers": viewers,
        "poster_url": _build_proxy_image(item_id, "Primary", name),
        "backdrop_url": _build_proxy_image(item_id, "Backdrop", name),
        "item_id": item_id,
        "overview": overview,
        "production_year": production_year,
        "quality_tags": quality_tags,
    }


# ════════════════════════════════════════════════════════════
# 用户分析页
# ════════════════════════════════════════════════════════════

async def get_user_rankings(
    period: str = "30d",
    page: int = 1,
    size: int = 20,
) -> dict:
    pf = _period_filter(period)

    rows = await _query(
        f"SELECT UserId as user_id, "
        f"COUNT(*) as play_count, COALESCE(SUM(PlayDuration), 0) as total_duration "
        f"FROM PlaybackActivity WHERE {pf} "
        f"GROUP BY UserId ORDER BY total_duration DESC"
    )

    user_map = await _get_user_map()
    all_users = []
    for r in rows:
        uid = str(r.get("user_id", ""))
        all_users.append({
            "user_id": uid,
            "username": user_map.get(uid, f"用户 {uid[:6]}"),
            "play_count": r.get("play_count", 0),
            "total_duration_hours": round(r.get("total_duration", 0) / 3600, 1),
        })

    total = len(all_users)
    start = (page - 1) * size
    page_items = all_users[start : start + size]

    return {"total": total, "items": page_items}


async def get_user_detail(user_id: str, period: str = "7d") -> dict:
    pf = _period_filter(period)
    where = f"UserId = '{user_id}' AND {pf}"

    kpi_rows = await _query(
        f"SELECT COUNT(*) as total_plays, "
        f"COALESCE(SUM(PlayDuration), 0) as total_duration, "
        f"COUNT(DISTINCT ItemId) as unique_items "
        f"FROM PlaybackActivity WHERE {where}"
    )
    kpi = kpi_rows[0] if kpi_rows else {}
    total_plays = kpi.get("total_plays", 0)
    total_dur = kpi.get("total_duration", 0)
    avg_min = round(total_dur / total_plays / 60, 1) if total_plays else 0

    username = f"用户 {user_id[:6]}"
    account_age_days = 1
    try:
        resp = await emby.get(f"/Users/{user_id}")
        resp.raise_for_status()
        u = resp.json()
        username = u.get("Name", username)
        dc = u.get("DateCreated", "")
        if dc:
            m = re.search(r"(\d{4})-(\d{2})-(\d{2})", str(dc))
            if m:
                fd = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                account_age_days = max(1, (datetime.now() - fd).days)
    except Exception:
        pass

    pref_rows = await _query(
        f"SELECT ItemType, COUNT(*) as cnt FROM PlaybackActivity WHERE {where} GROUP BY ItemType"
    )
    movie_plays = episode_plays = 0
    for r in pref_rows:
        if r["ItemType"] == "Movie":
            movie_plays = r["cnt"]
        elif r["ItemType"] == "Episode":
            episode_plays = r["cnt"]

    fav_rows = await _query(
        f"SELECT ItemName, ItemId, ItemType, COALESCE(SUM(PlayDuration), 0) as dur "
        f"FROM PlaybackActivity WHERE {where} GROUP BY ItemName ORDER BY dur DESC LIMIT 1"
    )
    top_fav = None
    if fav_rows:
        f = fav_rows[0]
        top_fav = {
            "item_id": str(f.get("ItemId", "")),
            "name": _clean_name(f.get("ItemName", ""), f.get("ItemType", "")),
            "hours": round(f["dur"] / 3600, 1),
            "poster_url": f"/api/v1/proxy/smart_image?item_id={f['ItemId']}&type=Primary&name={urllib.parse.quote(_clean_name(f.get('ItemName', ''), f.get('ItemType', '')))}" if f.get("ItemId") else "",
        }

    trend_rows = await _query(
        f"SELECT DATE(DateCreated) as label, "
        f"COALESCE(SUM(PlayDuration), 0) as duration "
        f"FROM PlaybackActivity WHERE {where} "
        f"AND DateCreated >= date('now', '-30 days') "
        f"GROUP BY label ORDER BY label"
    )
    trend = {r["label"]: round(r["duration"] / 3600, 1) for r in trend_rows} if trend_rows else {}

    dc_rows = await _query(
        f"SELECT DateCreated FROM PlaybackActivity WHERE {where}"
    )
    heatmap = [[0] * 24 for _ in range(7)]
    for r in dc_rows:
        dc = r.get("DateCreated")
        if dc:
            m = re.search(r"(\d{4})-(\d{2})-(\d{2})[T\s](\d{2}):", str(dc))
            if m:
                # 数据库时间视为 UTC，加上配置的时区偏移转成本地时间
                dt_utc = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), tzinfo=timezone.utc)
                tz_offset = timezone(timedelta(hours=settings.HEATMAP_TIMEZONE_OFFSET))
                dt_local = dt_utc.astimezone(tz_offset)
                dow = dt_local.weekday()
                h = dt_local.hour
                if 0 <= h < 24 and 0 <= dow < 7:
                    heatmap[dow][h] += 1

    client_rows = await _query(
        f"SELECT COALESCE(ClientName, '未知') as device, COUNT(*) as cnt "
        f"FROM PlaybackActivity WHERE {where} GROUP BY device ORDER BY cnt DESC LIMIT 5"
    )
    device_rows = await _query(
        f"SELECT COALESCE(DeviceName, '未知') as device, COUNT(*) as cnt "
        f"FROM PlaybackActivity WHERE {where} GROUP BY device ORDER BY cnt DESC LIMIT 5"
    )

    recent_rows = await _query(
        f"SELECT ItemName, ItemId, ItemType, DateCreated, PlayDuration "
        f"FROM PlaybackActivity WHERE {where} ORDER BY DateCreated DESC LIMIT 10"
    )
    recent = []
    for r in recent_rows:
        recent.append({
            "name": _clean_name(r.get("ItemName", ""), r.get("ItemType", "")),
            "item_id": r.get("ItemId"),
            "date": r.get("DateCreated", "")[:16].replace("T", " "),
            "duration_min": round((r.get("PlayDuration") or 0) / 60, 1),
            "poster_url": f"/api/v1/proxy/smart_image?item_id={r['ItemId']}&type=Primary&name={urllib.parse.quote(_clean_name(r.get('ItemName', ''), r.get('ItemType', '')))}" if r.get("ItemId") else "",
        })

    badges = await _get_badges(where)

    return {
        "user_id": user_id,
        "username": username,
        "account_age_days": account_age_days,
        "kpis": {
            "total_plays": total_plays,
            "total_duration_hours": round(total_dur / 3600, 1),
            "avg_session_min": avg_min,
        },
        "preference": {
            "movie_plays": movie_plays,
            "episode_plays": episode_plays,
            "tag": "电影党" if movie_plays > episode_plays else "追剧党" if episode_plays > 0 else "未知",
        },
        "top_fav": top_fav,
        "trend": trend,
        "heatmap": heatmap,
        "client_dist": [{"name": r["device"], "value": r["cnt"]} for r in client_rows],
        "device_dist": [{"name": r["device"], "value": r["cnt"]} for r in device_rows],
        "recent_plays": recent,
    }


async def _get_badges(where: str) -> list[dict]:
    badges: list[dict] = []

    night_rows = await _query(
        f"SELECT COUNT(*) as cnt FROM PlaybackActivity WHERE {where} "
        f"AND cast(strftime('%H', DateCreated) as int) BETWEEN 0 AND 5"
    )
    if night_rows and (night_rows[0].get("cnt") or 0) >= 10:
        badges.append({"id": "night", "name": "夜猫子", "icon": "🌙", "color": "#6366f1", "desc": "深夜观影达人"})

    binge_rows = await _query(
        f"SELECT COUNT(*) as cnt FROM PlaybackActivity WHERE {where} AND PlayDuration >= 7200"
    )
    if binge_rows and (binge_rows[0].get("cnt") or 0) >= 3:
        badges.append({"id": "binge", "name": "刷剧狂魔", "icon": "🔥", "color": "#ef4444", "desc": "超长观看停不下来"})

    movie_rows = await _query(
        f"SELECT COUNT(*) as cnt FROM PlaybackActivity WHERE {where} AND ItemType = 'Movie'"
    )
    episode_rows = await _query(
        f"SELECT COUNT(*) as cnt FROM PlaybackActivity WHERE {where} AND ItemType = 'Episode'"
    )
    movie_cnt = (movie_rows[0].get("cnt") or 0) if movie_rows else 0
    episode_cnt = (episode_rows[0].get("cnt") or 0) if episode_rows else 0
    if movie_cnt >= 20 and movie_cnt > episode_cnt * 1.5:
        badges.append({"id": "cinephile", "name": "电影发烧友", "icon": "🎬", "color": "#f59e0b", "desc": "电影偏好明显"})
    elif episode_cnt >= 20 and episode_cnt > movie_cnt * 1.5:
        badges.append({"id": "series", "name": "追剧达人", "icon": "📺", "color": "#10b981", "desc": "剧集偏好明显"})

    return badges


async def get_heatmap(period: str = "30d") -> list[list[int]]:
    pf = _period_filter(period)
    rows = await _query(f"SELECT DateCreated FROM PlaybackActivity WHERE {pf}")
    heatmap = [[0] * 24 for _ in range(7)]
    for r in rows:
        dc = r.get("DateCreated")
        if dc:
            m = re.search(r"(\d{4})-(\d{2})-(\d{2})[T\s](\d{2}):", str(dc))
            if m:
                dt_utc = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), tzinfo=timezone.utc)
                tz_offset = timezone(timedelta(hours=settings.HEATMAP_TIMEZONE_OFFSET))
                dt_local = dt_utc.astimezone(tz_offset)
                dow = dt_local.weekday()
                h = dt_local.hour
                if 0 <= h < 24 and 0 <= dow < 7:
                    heatmap[dow][h] += 1
    return heatmap


async def get_device_dist(period: str = "30d", type: str = "client") -> list[dict]:
    pf = _period_filter(period)
    field = "ClientName" if type == "client" else "DeviceName"
    rows = await _query(
        f"SELECT COALESCE({field}, '未知') as name, COUNT(*) as value "
        f"FROM PlaybackActivity WHERE {pf} GROUP BY name ORDER BY value DESC LIMIT 10"
    )
    return [{"name": r["name"], "value": r["value"]} for r in rows]
