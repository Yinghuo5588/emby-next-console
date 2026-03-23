"""
统计服务 V3 — 全部走 Emby Playback Reporting 插件 API
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.core.emby import emby

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


# ════════════════════════════════════════════════════════════
# 总览页
# ════════════════════════════════════════════════════════════

async def get_overview() -> dict:
    """核心指标 + 媒体库总量"""
    # 播放统计
    rows = await _query(
        "SELECT COUNT(*) as total_plays, "
        "COALESCE(SUM(PlayDuration), 0) as total_duration, "
        "COUNT(DISTINCT UserId) as unique_users "
        "FROM PlaybackActivity"
    )
    r = rows[0] if rows else {}

    # 30 天活跃用户
    active_rows = await _query(
        "SELECT COUNT(DISTINCT UserId) as cnt FROM PlaybackActivity "
        "WHERE DateCreated >= date('now', '-30 days')"
    )

    # 媒体库总量
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
        "active_users_30d": active_rows[0].get("cnt", 0) if active_rows else 0,
        "library": library,
    }


async def get_trend_by_period(period: str = "30d") -> dict:
    """播放趋势：只有播放时长"""
    if period == "12w":
        rows = await _query(
            "SELECT strftime('%Y-%W', substr(replace(DateCreated, 'T', ' '), 1, 19)) as label, "
            "COALESCE(SUM(PlayDuration), 0) as duration "
            "FROM PlaybackActivity WHERE DateCreated >= date('now', '-84 days') "
            "GROUP BY label ORDER BY label"
        )
    elif period == "12m":
        rows = await _query(
            "SELECT substr(replace(DateCreated, 'T', ' '), 1, 7) as label, "
            "COALESCE(SUM(PlayDuration), 0) as duration "
            "FROM PlaybackActivity WHERE DateCreated >= date('now', '-365 days') "
            "GROUP BY label ORDER BY label"
        )
    else:  # 30d
        rows = await _query(
            "SELECT DATE(DateCreated) as label, "
            "COALESCE(SUM(PlayDuration), 0) as duration "
            "FROM PlaybackActivity WHERE DateCreated >= date('now', '-30 days') "
            "GROUP BY label ORDER BY label"
        )

    return {r["label"]: round(r["duration"] / 3600, 1) for r in rows} if rows else {}


async def get_top_content(limit: int = 5, period: str = "7d") -> list[dict]:
    """Top 内容（按时长排）"""
    pf = _period_filter(period)
    rows = await _query(
        f"SELECT ItemName, ItemId, ItemType, "
        f"COUNT(*) as play_count, COALESCE(SUM(PlayDuration), 0) as total_duration "
        f"FROM PlaybackActivity WHERE {pf} "
        f"GROUP BY ItemName ORDER BY total_duration DESC LIMIT {limit * 3}"
    )
    # 按作品级聚合
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
    for item in result:
        iid = item.get("item_id")
        if iid:
            item["poster_url"] = f"/api/proxy/smart_image?item_id={iid}&type=Primary"
    return result


async def get_top_users_ranked(limit: int = 5, period: str = "7d") -> list[dict]:
    """Top 用户（按时长排）"""
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
    page: int = 1,
    size: int = 20,
    user_id: str = None,
) -> dict:
    """内容排行榜（筛选+分页）"""
    pf = _period_filter(period)

    type_filter = ""
    if content_type == "movie":
        type_filter = " AND ItemType = 'Movie'"
    elif content_type == "series":
        type_filter = " AND ItemType IN ('Series', 'Episode')"

    user_filter = f" AND UserId = '{user_id}'" if user_id else ""

    order = "total_duration DESC" if sort == "duration" else "play_count DESC"

    rows = await _query(
        f"SELECT ItemName, ItemId, ItemType, "
        f"COUNT(*) as play_count, COALESCE(SUM(PlayDuration), 0) as total_duration "
        f"FROM PlaybackActivity WHERE {pf}{type_filter}{user_filter} "
        f"GROUP BY ItemName ORDER BY {order} LIMIT 500"
    )

    # 按作品级聚合
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

    for item in page_items:
        iid = item.get("item_id")
        if iid:
            item["poster_url"] = f"/api/proxy/smart_image?item_id={iid}&type=Primary"

    return {"total": total, "items": page_items}


async def get_content_detail(item_id: str) -> dict:
    """单个内容详情"""
    # 基本信息
    try:
        resp = await emby.get(f"/Items/{item_id}")
        resp.raise_for_status()
        info = resp.json()
        name = info.get("Name", "未知")
        item_type = info.get("Type", "")
    except Exception:
        name = "未知"
        item_type = ""

    # 播放趋势（近 30 天，按天）
    rows = await _query(
        f"SELECT DATE(DateCreated) as date, COUNT(*) as play_count, "
        f"COALESCE(SUM(PlayDuration), 0) as duration "
        f"FROM PlaybackActivity WHERE ItemId = '{item_id}' "
        f"AND DateCreated >= date('now', '-30 days') "
        f"GROUP BY date ORDER BY date"
    )
    trend = {r["date"]: {"plays": r["play_count"], "hours": round(r["duration"] / 3600, 1)} for r in rows} if rows else {}

    # 观看用户
    user_rows = await _query(
        f"SELECT UserId, COUNT(*) as play_count, COALESCE(SUM(PlayDuration), 0) as duration "
        f"FROM PlaybackActivity WHERE ItemId = '{item_id}' "
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
        "poster_url": f"/api/proxy/smart_image?item_id={item_id}&type=Primary",
    }


# ════════════════════════════════════════════════════════════
# 用户分析页
# ════════════════════════════════════════════════════════════

async def get_user_rankings(
    period: str = "30d",
    page: int = 1,
    size: int = 20,
) -> dict:
    """用户排行榜（分页）"""
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
    """单个用户画像 — 所有数据按 period 筛选"""
    pf = _period_filter(period)
    where = f"UserId = '{user_id}' AND {pf}"

    # KPI
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

    # 用户信息
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

    # 内容偏好
    pref_rows = await _query(
        f"SELECT ItemType, COUNT(*) as cnt FROM PlaybackActivity WHERE {where} GROUP BY ItemType"
    )
    movie_plays = episode_plays = 0
    for r in pref_rows:
        if r["ItemType"] == "Movie":
            movie_plays = r["cnt"]
        elif r["ItemType"] == "Episode":
            episode_plays = r["cnt"]

    # Top 最爱
    fav_rows = await _query(
        f"SELECT ItemName, ItemId, ItemType, COALESCE(SUM(PlayDuration), 0) as dur "
        f"FROM PlaybackActivity WHERE {where} GROUP BY ItemName ORDER BY dur DESC LIMIT 1"
    )
    top_fav = None
    if fav_rows:
        f = fav_rows[0]
        top_fav = {
            "name": _clean_name(f.get("ItemName", ""), f.get("ItemType", "")),
            "hours": round(f["dur"] / 3600, 1),
            "poster_url": f"/api/proxy/smart_image?item_id={f['ItemId']}&type=Primary" if f.get("ItemId") else "",
        }

    # 播放趋势（近30天按天）
    trend_rows = await _query(
        f"SELECT DATE(DateCreated) as label, "
        f"COALESCE(SUM(PlayDuration), 0) as duration "
        f"FROM PlaybackActivity WHERE {where} "
        f"AND DateCreated >= date('now', '-30 days') "
        f"GROUP BY label ORDER BY label"
    )
    trend = {r["label"]: round(r["duration"] / 3600, 1) for r in trend_rows} if trend_rows else {}

    # 观影生物钟（二维热力图：day_of_week × hour）
    dc_rows = await _query(
        f"SELECT DateCreated FROM PlaybackActivity WHERE {where}"
    )
    # 热力图 [day_of_week][hour]，day 0=周一 ... 6=周日
    heatmap = [[0] * 24 for _ in range(7)]
    for r in dc_rows:
        dc = r.get("DateCreated")
        if dc:
            m = re.search(r"(\d{4})-(\d{2})-(\d{2})[T\s](\d{2}):", str(dc))
            if m:
                from datetime import date as _d
                dt = _d(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                dow = dt.weekday()  # 0=Mon
                h = int(m.group(4))
                if 0 <= h < 24 and 0 <= dow < 7:
                    heatmap[dow][h] += 1

    # 设备分布：软件 + 硬件
    client_rows = await _query(
        f"SELECT COALESCE(ClientName, '未知') as device, COUNT(*) as cnt "
        f"FROM PlaybackActivity WHERE {where} GROUP BY device ORDER BY cnt DESC LIMIT 5"
    )
    device_rows = await _query(
        f"SELECT COALESCE(DeviceName, '未知') as device, COUNT(*) as cnt "
        f"FROM PlaybackActivity WHERE {where} GROUP BY device ORDER BY cnt DESC LIMIT 5"
    )

    # 最近播放
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
            "poster_url": f"/api/proxy/smart_image?item_id={r['ItemId']}&type=Primary" if r.get("ItemId") else "",
        })

    # 成就徽章
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
    """趣味成就徽章"""
    rows = await _query(
        f"SELECT DateCreated, PlayDuration, COALESCE(ClientName, DeviceName) as client, "
        f"ItemId, ItemName, ItemType FROM PlaybackActivity WHERE {where}"
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
        badges.append({"id": "night", "name": "深夜修仙", "icon": "fa-moon", "color": "text-indigo-500", "desc": "深夜是灵魂最自由的时刻"})
    if weekend_c >= 5:
        badges.append({"id": "weekend", "name": "周末狂欢", "icon": "fa-champagne-glasses", "color": "text-pink-500", "desc": "工作日唯唯诺诺，周末重拳出击"})
    if dur_total > 180000:
        badges.append({"id": "liver", "name": "核心肝帝", "icon": "fa-fire", "color": "text-red-500", "desc": "阅片无数，肝度爆表"})
    if fish_c >= 5:
        badges.append({"id": "fish", "name": "带薪观影", "icon": "fa-fish", "color": "text-cyan-500", "desc": "工作是老板的，快乐是自己的"})
    if morning_c >= 2:
        badges.append({"id": "morning", "name": "晨练追剧", "icon": "fa-sun", "color": "text-amber-500", "desc": "比你优秀的人，连看片都比你早"})
    if len(devices) >= 2:
        badges.append({"id": "device", "name": "全平台制霸", "icon": "fa-gamepad", "color": "text-emerald-500", "desc": "手机、平板、电视，哪里都能看"})
    if items:
        loyal = max(items.values(), key=lambda x: x["c"])
        if loyal["c"] >= 3:
            safe = str(loyal.get("name") or "未知").split(" - ")[0][:10]
            badges.append({"id": "loyal", "name": "N刷狂魔", "icon": "fa-repeat", "color": "text-teal-500", "desc": f"对《{safe}》爱得深沉"})
    total = movies + eps
    if total > 10:
        if movies / total > 0.6:
            badges.append({"id": "movie_lover", "name": "电影鉴赏家", "icon": "fa-film", "color": "text-blue-500", "desc": "沉浸在两小时的艺术光影世界"})
        elif eps / total > 0.6:
            badges.append({"id": "tv_lover", "name": "追剧狂魔", "icon": "fa-tv", "color": "text-purple-500", "desc": "一集接一集，根本停不下来"})

    return badges


# ════════════════════════════════════════════════════════════
# 总览页额外数据
# ════════════════════════════════════════════════════════════

async def get_heatmap(period: str = "30d") -> list[list[int]]:
    """24×7 热力图数据：grid[hour][day_of_week] = 播放次数"""
    pf = _period_filter(period)
    rows = await _query(
        f"SELECT DateCreated FROM PlaybackActivity WHERE {pf}"
    )
    grid = [[0] * 7 for _ in range(24)]
    day_names = ['一', '二', '三', '四', '五', '六', '日']
    for r in rows:
        dc = r.get("DateCreated")
        if dc:
            m = re.search(r"(\d{4})-(\d{2})-(\d{2})[T\s](\d{2})", str(dc))
            if m:
                hour = int(m.group(4))
                try:
                    dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                    dow = dt.weekday()  # 0=Mon
                    if 0 <= hour < 24:
                        grid[hour][dow] += 1
                except ValueError:
                    pass
    return grid


async def get_device_dist(period: str = "30d", dist_type: str = "client") -> list[dict]:
    """设备分布 — client=软件(客户端) / hardware=硬件(设备型号)"""
    pf = _period_filter(period)
    col = "DeviceName" if dist_type == "hardware" else "ClientName"
    label = "硬件" if dist_type == "hardware" else "软件"
    rows = await _query(
        f"SELECT COALESCE({col}, '未知') as device, COUNT(*) as cnt "
        f"FROM PlaybackActivity WHERE {pf} GROUP BY device ORDER BY cnt DESC LIMIT 8"
    )
    return [{"name": r["device"], "value": r["cnt"]} for r in rows]
