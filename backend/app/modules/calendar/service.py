"""追剧日历 - 基于 TMDB 排期 + Emby 入库状态"""
import asyncio
import json
import logging
from datetime import date, datetime, timedelta, timezone

import httpx

from app.core.emby import emby
from app.core.settings import settings
from app.db.models.calendar import CalendarEntry
from app.db.models.system import SystemSetting
from app.db.session import AsyncSessionFactory
from sqlalchemy import select, and_, or_

logger = logging.getLogger("app.calendar")

# ── 内存缓存 ──
_cache: dict = {}
CACHE_TTL = timedelta(hours=12)

TMDB_IMG_BASE = "https://image.tmdb.org/t/p/w300"


def _pad(n: int) -> str:
    return f"{n:02d}"


async def _get_tmdb_img_proxy() -> str:
    """获取 TMDB 图片代理域名（从数据库 settings 读取）"""
    try:
        async with AsyncSessionFactory() as db:
            result = await db.execute(select(SystemSetting).where(SystemSetting.setting_key == "TMDB_IMG_PROXY"))
            row = result.scalar_one_or_none()
            if row and row.value_json:
                return str(row.value_json).rstrip("/")
    except Exception:
        pass
    return ""


def _build_poster_url(poster_path: str | None, img_proxy: str) -> str:
    """构建海报 URL（支持代理替换）"""
    if not poster_path:
        return ""
    if img_proxy:
        return f"{img_proxy}/t/p/w300{poster_path}"
    return f"{TMDB_IMG_BASE}{poster_path}"


# ════════════════════════════════════════════════════════════
# Emby 交互
# ════════════════════════════════════════════════════════════

async def _get_continuing_series() -> list[dict]:
    """获取 Emby 中状态为 Continuing 且有 TMDB ID 的剧集"""
    try:
        resp = await emby.get("/Items", params={
            "IncludeItemTypes": "Series",
            "Recursive": "true",
            "Fields": "ProviderIds,Status",
            "IsVirtual": "false",
            "Limit": 1000,
        })
        if resp.status_code != 200:
            return []
        items = resp.json().get("Items", [])
        result = []
        for item in items:
            providers = item.get("ProviderIds") or {}
            tmdb_id = providers.get("Tmdb") or providers.get("TMDB")
            status = item.get("Status", "")
            if status and status != "Continuing":
                continue
            if not tmdb_id:
                continue
            result.append({
                "id": item["Id"],
                "name": item.get("Name", ""),
                "tmdb_id": int(tmdb_id),
                "status": status,
            })
        return result
    except Exception as e:
        logger.warning(f"获取剧集列表失败: {e}")
        return []


async def _check_episode_exists(series_id: str, season: int, episode: int) -> bool:
    """严格物理校验：检查 Emby 中该集是否实际存在"""
    try:
        resp = await emby.get("/Items", params={
            "ParentId": series_id,
            "Recursive": "true",
            "IncludeItemTypes": "Episode",
            "Fields": "Path,MediaSources,LocationType",
            "Limit": 500,
        })
        if resp.status_code != 200:
            return False
        for item in resp.json().get("Items", []):
            if item.get("ParentIndexNumber") == season and item.get("IndexNumber") == episode:
                if item.get("LocationType") == "Virtual":
                    continue
                if item.get("IsMissing"):
                    continue
                if item.get("Path") or item.get("MediaSources"):
                    return True
        return False
    except Exception:
        return False


# ════════════════════════════════════════════════════════════
# TMDB 交互
# ════════════════════════════════════════════════════════════

async def _fetch_tmdb_episodes(tmdb_id: int, week_start: date, week_end: date) -> dict:
    """
    从 TMDB 获取某剧本周播出的集 + 剧集信息（poster_path, overview）。
    返回 {"poster_path": str, "overview": str, "episodes": [...]}
    """
    api_key = (settings.TMDB_API_KEY or "").strip()
    if not api_key:
        return {"poster_path": None, "overview": "", "episodes": []}

    proxy_cfg = None
    transport = httpx.AsyncHTTPTransport(proxy=proxy_cfg) if proxy_cfg else None

    try:
        async with httpx.AsyncClient(timeout=10, transport=transport) as client:
            # 1. 剧集基本信息
            resp = await client.get(
                f"https://api.themoviedb.org/3/tv/{tmdb_id}",
                params={"api_key": api_key, "language": "zh-CN"},
            )
            if resp.status_code != 200:
                return {"poster_path": None, "overview": "", "episodes": []}
            data = resp.json()
            series_overview = data.get("overview", "") or ""
            poster_path = data.get("poster_path") or ""

            # 2. 锁定目标季
            target_seasons: set[int] = set()
            last_ep = data.get("last_episode_to_air")
            next_ep = data.get("next_episode_to_air")
            if last_ep and last_ep.get("season_number") is not None:
                target_seasons.add(last_ep["season_number"])
            if next_ep and next_ep.get("season_number") is not None:
                target_seasons.add(next_ep["season_number"])
            if not target_seasons:
                seasons = data.get("seasons", [])
                if seasons:
                    target_seasons.add(seasons[-1].get("season_number", 0))

            episodes = []
            for season_num in target_seasons:
                if season_num is None or season_num == 0:
                    continue

                s_resp = await client.get(
                    f"https://api.themoviedb.org/3/tv/{tmdb_id}/season/{season_num}",
                    params={"api_key": api_key, "language": "zh-CN"},
                )
                if s_resp.status_code != 200:
                    continue

                for ep in s_resp.json().get("episodes", []):
                    air_date_str = ep.get("air_date")
                    if not air_date_str:
                        continue
                    try:
                        air_date = date.fromisoformat(air_date_str)
                    except ValueError:
                        continue
                    if week_start <= air_date <= week_end:
                        episodes.append({
                            "season": ep.get("season_number", season_num),
                            "episode": ep.get("episode_number", 0),
                            "episode_name": ep.get("name") or f"第{ep.get('episode_number', 0)}集",
                            "air_date": air_date_str,
                            "ep_overview": ep.get("overview", "") or "",
                        })

            return {
                "poster_path": poster_path,
                "overview": series_overview,
                "episodes": episodes,
            }
    except Exception as e:
        logger.warning(f"TMDB tv/{tmdb_id} 查询失败: {e}")
        return {"poster_path": None, "overview": "", "episodes": []}


# ════════════════════════════════════════════════════════════
# 持久化
# ════════════════════════════════════════════════════════════

async def _save_to_db(items: list[dict]):
    """将剧集条目写入 calendar_entries 表"""
    async with AsyncSessionFactory() as db:
        for item in items:
            if not all([item.get("series_id"), item.get("season"), item.get("episode")]):
                continue
            entry = CalendarEntry(
                emby_item_id=item["series_id"],
                series_name=item.get("series_name", ""),
                season_number=item["season"],
                episode_number=item["episode"],
                episode_title=item.get("episode_name", ""),
                air_date=date.fromisoformat(item["air_date"]),
                overview=item.get("ep_overview", ""),
                has_file=(item.get("status") == "ready"),
            )
            db.add(entry)
        try:
            await db.commit()
        except Exception:
            await db.rollback()


# ════════════════════════════════════════════════════════════
# 核心：获取周历
# ════════════════════════════════════════════════════════════

async def get_weekly_calendar(week_offset: int = 0, force_refresh: bool = False) -> dict:
    """获取指定周的日历数据"""
    now = datetime.now(timezone.utc)
    cache_key = f"week_{week_offset}"

    if not force_refresh:
        cached = _cache.get(cache_key)
        if cached and cached.get("expires") and cached["expires"] > now:
            return cached["data"]

    today = date.today()
    target = today + timedelta(weeks=week_offset)
    week_start = target - timedelta(days=target.weekday())
    week_end = week_start + timedelta(days=6)

    series_list = await _get_continuing_series()
    if not series_list:
        result = {
            "days": [],
            "date_range": f"{week_start.strftime('%m/%d')} - {week_end.strftime('%m/%d')}",
            "stats": {"total_series": 0, "total_upcoming": 0, "ready": 0, "pending": 0},
        }
        _cache[cache_key] = {"data": result, "expires": now + CACHE_TTL}
        return result

    # 获取 TMDB 图片代理
    img_proxy = await _get_tmdb_img_proxy()

    # 并发抓取 TMDB + Emby 入库校验
    sem = asyncio.Semaphore(5)
    all_episodes: list[dict] = []
    valid_series = 0

    async def process_series(s: dict):
        nonlocal valid_series
        async with sem:
            tmdb_data = await _fetch_tmdb_episodes(s["tmdb_id"], week_start, week_end)
            if not tmdb_data["episodes"]:
                return
            valid_series += 1
            poster_url = _build_poster_url(tmdb_data["poster_path"], img_proxy)

            for ep in tmdb_data["episodes"]:
                has_file = await _check_episode_exists(s["id"], ep["season"], ep["episode"])
                air_date = date.fromisoformat(ep["air_date"])
                if has_file:
                    status = "ready"
                elif air_date < today:
                    status = "missing"
                elif air_date == today:
                    status = "today"
                else:
                    status = "upcoming"

                all_episodes.append({
                    "series_name": s["name"],
                    "series_id": s["id"],
                    "tmdb_id": s["tmdb_id"],
                    "season": ep["season"],
                    "episode": ep["episode"],
                    "episode_name": ep["episode_name"],
                    "air_date": ep["air_date"],
                    "status": status,
                    "ep_overview": ep.get("ep_overview", ""),
                    "series_overview": tmdb_data["overview"],
                    "poster_url": poster_url or f"/api/v1/proxy/smart_image?item_id={s['id']}&type=Primary",
                })

    await asyncio.gather(*[process_series(s) for s in series_list])

    # 按天分组 + 多集聚合
    day_data: dict[int, list] = {i: [] for i in range(7)}
    for ep in all_episodes:
        try:
            air = date.fromisoformat(ep["air_date"])
            idx = (air - week_start).days
            if 0 <= idx <= 6:
                day_data[idx].append(ep)
        except (ValueError, TypeError):
            continue

    week_dates = [week_start + timedelta(days=i) for i in range(7)]
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

    final_days = []
    for i in range(7):
        items = day_data[i]
        grouped: dict[tuple, list] = {}
        for item in items:
            key = (item["tmdb_id"], item["season"])
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(item)

        merged = []
        for key, group in grouped.items():
            group.sort(key=lambda x: x["episode"])
            if len(group) <= 1:
                merged.extend(group)
            else:
                first, last = group[0], group[-1]
                item = first.copy()
                item["episode"] = f"{first['episode']}-{last['episode']}"
                statuses = [g["status"] for g in group]
                if "missing" in statuses:
                    item["status"] = "missing"
                elif "ready" in statuses:
                    item["status"] = "ready"
                elif "today" in statuses:
                    item["status"] = "today"
                else:
                    item["status"] = "upcoming"
                merged.append(item)

        merged.sort(key=lambda x: str(x["episode"]))
        final_days.append({
            "date": week_dates[i].isoformat(),
            "weekday_cn": weekdays[i],
            "is_today": week_dates[i] == today,
            "items": merged,
        })

    ready_count = sum(1 for ep in all_episodes if ep["status"] == "ready")
    result = {
        "days": final_days,
        "date_range": f"{week_start.strftime('%m/%d')} - {week_end.strftime('%m/%d')}",
        "stats": {
            "total_series": valid_series,
            "total_upcoming": len(all_episodes),
            "ready": ready_count,
            "pending": len(all_episodes) - ready_count,
        },
    }

    _cache[cache_key] = {"data": result, "expires": now + CACHE_TTL}
    await _save_to_db(all_episodes)

    return result


# ════════════════════════════════════════════════════════════
# Webhook 联动
# ════════════════════════════════════════════════════════════

async def mark_episode_ready(series_id: str, season: int, episode: int):
    """Webhook 联动：新剧集入库时校验并更新数据库 has_file"""
    logger.info(f"🟢 [日历] Webhook 触发入库: Series={series_id} S{season}E{episode}")

    # 1. 清内存缓存，下次请求强制刷新
    _cache.clear()

    # 2. 严格校验 Emby 中该集是否真实存在
    exists = await _check_episode_exists(series_id, season, episode)
    if not exists:
        logger.debug(f"🟡 [日历] 校验未通过，跳过 DB 更新: Series={series_id} S{season}E{episode}")
        return

    # 3. 更新数据库中匹配的 calendar_entries
    try:
        async with AsyncSessionFactory() as db:
            stmt = (
                select(CalendarEntry)
                .where(
                    CalendarEntry.emby_item_id == series_id,
                    CalendarEntry.season_number == season,
                    CalendarEntry.episode_number == episode,
                    CalendarEntry.has_file == False,
                )
            )
            result = await db.execute(stmt)
            entries = result.scalars().all()
            for entry in entries:
                entry.has_file = True
            if entries:
                await db.commit()
                logger.info(f"✅ [日历] 已更新 {len(entries)} 条记录 has_file=True: Series={series_id} S{season}E{episode}")
            else:
                logger.debug(f"🟡 [日历] 无匹配待入库记录: Series={series_id} S{season}E{episode}")
    except Exception as e:
        logger.error(f"❌ [日历] 更新 has_file 失败: {e}")


# ════════════════════════════════════════════════════════════
# Emby Server 信息
# ════════════════════════════════════════════════════════════

async def get_emby_info() -> dict:
    """获取 Emby 地址和 ServerId，用于前端跳转播放"""
    server_id = ""
    try:
        resp = await emby.get("/System/Info")
        if resp.status_code == 200:
            server_id = resp.json().get("Id", "")
    except Exception:
        pass
    return {
        "emby_url": (settings.EMBY_HOST or "").rstrip("/"),
        "server_id": server_id,
    }
