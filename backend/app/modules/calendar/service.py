"""追剧日历服务 — 基于 TMDB 播出排期 + Emby 库对比"""
from __future__ import annotations

import logging
from datetime import date as ddate, datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.emby import emby
from app.core.settings import settings
from app.db.models.calendar import CalendarEntry

logger = logging.getLogger("app.calendar")

# ── TMDB 辅助 ────────────────────────────────────────────

async def _tmdb_get(path: str, params: dict | None = None) -> dict | list | None:
    """调用 TMDB API"""
    import httpx
    if not settings.TMDB_API_KEY:
        return None
    url = f"https://api.themoviedb.org/3{path}"
    p = {"api_key": settings.TMDB_API_KEY, "language": "zh-CN"}
    if params:
        p.update(params)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=p)
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.warning("TMDB 请求失败 %s: %s", path, e)
    return None


class CalendarService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── 同步：从 Emby 获取系列 + TMDB 获取播出排期 ────────

    async def sync_from_tmdb(self) -> int:
        """从 TMDB 获取本周 + 下周的播出排期，与 Emby 库对比"""
        if not settings.TMDB_API_KEY:
            logger.warning("未配置 TMDB_API_KEY，无法同步日历")
            return 0

        # 1. 从 Emby 获取所有 Series 及其 TMDB ID
        series_list = await self._get_emby_series_with_tmdb()
        if not series_list:
            logger.warning("未找到带 TMDB ID 的系列")
            return 0

        # 2. 计算同步范围（本周 + 下周）
        today = ddate.today()
        start_of_week = today - timedelta(days=today.weekday())  # 周一
        range_start = start_of_week - timedelta(days=7)  # 上周一开始
        range_end = start_of_week + timedelta(days=20)  # 下下周日

        total = 0
        for series in series_list:
            try:
                count = await self._sync_series_schedule(
                    series, range_start, range_end
                )
                total += count
            except Exception as e:
                logger.warning("同步系列 %s 失败: %s", series["name"], e)

        logger.info("日历同步完成: %d 条目", total)
        return total

    async def _get_emby_series_with_tmdb(self) -> list[dict]:
        """从 Emby 获取有 TMDB ID 的系列"""
        try:
            resp = await emby.get(
                "/Items",
                params={
                    "IncludeItemTypes": "Series",
                    "Recursive": "true",
                    "Fields": "ProviderIds,Status",
                    "Limit": 500,
                },
            )
            resp.raise_for_status()
            items = resp.json().get("Items", [])
            return [
                {
                    "id": it["Id"],
                    "name": it.get("Name", ""),
                    "tmdb_id": it.get("ProviderIds", {}).get("Tmdb"),
                }
                for it in items
                if it.get("ProviderIds", {}).get("Tmdb")
            ]
        except Exception:
            return []

    async def _sync_series_schedule(
        self, series: dict, start: ddate, end: ddate
    ) -> int:
        """同步单个系列的播出排期"""
        tmdb_id = series["tmdb_id"]
        emby_id = series["id"]
        series_name = series["name"]

        # 获取 TMDB 系列信息
        tv = await _tmdb_get(f"/tv/{tmdb_id}")
        if not tv:
            return 0

        # 获取海报
        poster_path = tv.get("poster_path")
        poster_url = f"https://image.tmdb.org/t/p/w300{poster_path}" if poster_path else None

        # 确定要同步的季（当前季 + 最近一季）
        target_seasons = set()
        if tv.get("last_episode_to_air"):
            target_seasons.add(tv["last_episode_to_air"].get("season_number"))
        if tv.get("next_episode_to_air"):
            target_seasons.add(tv["next_episode_to_air"].get("season_number"))
        # 也看看所有还在播出的季
        for s in tv.get("seasons", []):
            if s.get("air_date") and s["air_date"] >= start.isoformat():
                target_seasons.add(s.get("season_number"))
        target_seasons.discard(None)

        count = 0
        for season_num in target_seasons:
            season_data = await _tmdb_get(f"/tv/{tmdb_id}/season/{season_num}")
            if not season_data:
                continue
            for ep in season_data.get("episodes", []):
                air_date_str = ep.get("air_date")
                if not air_date_str:
                    continue
                try:
                    air_date = ddate.fromisoformat(air_date_str)
                except ValueError:
                    continue
                if air_date < start or air_date > end:
                    continue

                # 检查 Emby 是否有此集
                has_episode = await self._check_emby_episode(
                    emby_id, season_num, ep["episode_number"]
                )

                await self._upsert_entry(
                    emby_item_id=emby_id,
                    series_name=series_name,
                    season_number=season_num,
                    episode_number=ep["episode_number"],
                    episode_title=ep.get("name", ""),
                    air_date=air_date,
                    backdrop_url=poster_url,
                    overview=ep.get("overview", ""),
                    has_file=has_episode,
                )
                count += 1
        return count

    async def _check_emby_episode(
        self, series_id: str, season: int, episode: int
    ) -> bool:
        """检查 Emby 中是否有该集"""
        try:
            resp = await emby.get(
                "/Items",
                params={
                    "ParentId": series_id,
                    "Recursive": "true",
                    "IncludeItemTypes": "Episode",
                    "ParentIndexNumber": season,
                    "IndexNumber": episode,
                    "Fields": "Path,MediaSources",
                    "Limit": 1,
                },
            )
            resp.raise_for_status()
            items = resp.json().get("Items", [])
            if items:
                it = items[0]
                if it.get("LocationType") != "Virtual" and not it.get("IsMissing"):
                    if it.get("Path") or it.get("MediaSources"):
                        return True
        except Exception:
            pass
        return False

    async def _upsert_entry(self, **kw):
        """插入或更新日历条目"""
        stmt = select(CalendarEntry).where(
            and_(
                CalendarEntry.emby_item_id == kw["emby_item_id"],
                CalendarEntry.season_number == kw["season_number"],
                CalendarEntry.episode_number == kw["episode_number"],
            )
        )
        result = await self.db.execute(stmt)
        entry = result.scalar_one_or_none()

        if entry:
            entry.series_name = kw["series_name"]
            entry.episode_title = kw["episode_title"]
            entry.air_date = kw["air_date"]
            entry.backdrop_url = kw.get("backdrop_url")
            entry.overview = kw.get("overview", "")
            entry.has_file = kw.get("has_file", False)
        else:
            entry = CalendarEntry(
                emby_item_id=kw["emby_item_id"],
                series_name=kw["series_name"],
                season_number=kw["season_number"],
                episode_number=kw["episode_number"],
                episode_title=kw["episode_title"],
                air_date=kw["air_date"],
                backdrop_url=kw.get("backdrop_url"),
                overview=kw.get("overview", ""),
                has_file=kw.get("has_file", False),
            )
            self.db.add(entry)

    # ── 查询 ──────────────────────────────────────────────

    async def get_month_entries(self, year: int, month: int) -> dict:
        """获取指定月份的日历条目"""
        import calendar as cal
        days_in = cal.monthrange(year, month)[1]
        start = ddate(year, month, 1)
        end = ddate(year, month, days_in)

        stmt = select(CalendarEntry).where(
            and_(CalendarEntry.air_date >= start, CalendarEntry.air_date <= end)
        ).order_by(CalendarEntry.air_date, CalendarEntry.series_name)

        result = await self.db.execute(stmt)
        entries = result.scalars().all()

        by_date: dict[str, list] = {}
        for e in entries:
            key = e.air_date.isoformat()
            by_date.setdefault(key, []).append({
                "id": e.id,
                "emby_item_id": e.emby_item_id,
                "series_name": e.series_name,
                "season_number": e.season_number,
                "episode_number": e.episode_number,
                "episode_title": e.episode_title,
                "air_date": key,
                "backdrop_url": e.backdrop_url,
                "overview": e.overview,
                "has_file": e.has_file,
            })

        return {"entries": by_date, "total": len(entries)}

    async def get_week_entries(self, year: int, month: int, week: int) -> dict:
        """获取指定周的瀑布流数据"""
        first_day = ddate(year, month, 1)
        first_dow = first_day.weekday()
        start = first_day - timedelta(days=first_dow) + timedelta(days=(week - 1) * 7)
        end = start + timedelta(days=6)

        stmt = select(CalendarEntry).where(
            and_(CalendarEntry.air_date >= start, CalendarEntry.air_date <= end)
        ).order_by(CalendarEntry.air_date, CalendarEntry.series_name)

        result = await self.db.execute(stmt)
        entries = result.scalars().all()

        by_dow: dict[int, list] = {i: [] for i in range(7)}
        for e in entries:
            dow = e.air_date.weekday()
            by_dow[dow].append({
                "id": e.id,
                "emby_item_id": e.emby_item_id,
                "series_name": e.series_name,
                "season_number": e.season_number,
                "episode_number": e.episode_number,
                "episode_title": e.episode_title,
                "air_date": e.air_date.isoformat(),
                "backdrop_url": e.backdrop_url,
                "overview": e.overview,
                "has_file": e.has_file,
            })

        dow_labels = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        waterfall = []
        for i in range(7):
            waterfall.append({
                "dow": i,
                "label": dow_labels[i],
                "date": (start + timedelta(days=i)).isoformat(),
                "entries": by_dow[i],
            })

        return {
            "waterfall": waterfall,
            "week_start": start.isoformat(),
            "week_end": end.isoformat(),
            "total": len(entries),
        }

    async def get_upcoming(self, days: int = 7) -> list[dict]:
        """获取未来 N 天的更新"""
        today = ddate.today()
        end = today + timedelta(days=days)

        stmt = (
            select(CalendarEntry)
            .where(and_(CalendarEntry.air_date >= today, CalendarEntry.air_date <= end))
            .order_by(CalendarEntry.air_date, CalendarEntry.series_name)
        )
        result = await self.db.execute(stmt)
        return [
            {
                "id": e.id,
                "series_name": e.series_name,
                "season_number": e.season_number,
                "episode_number": e.episode_number,
                "episode_title": e.episode_title,
                "air_date": e.air_date.isoformat(),
                "backdrop_url": e.backdrop_url,
                "has_file": e.has_file,
            }
            for e in result.scalars().all()
        ]

    async def get_stats(self) -> dict:
        """获取日历统计"""
        today = ddate.today()
        month_start = ddate(today.year, today.month, 1)
        week_end = today + timedelta(days=7)

        month_stmt = select(func.count()).select_from(CalendarEntry).where(
            CalendarEntry.air_date >= month_start
        )
        month_count = (await self.db.execute(month_stmt)).scalar() or 0

        upcoming_stmt = select(func.count()).select_from(CalendarEntry).where(
            and_(CalendarEntry.air_date >= today, CalendarEntry.air_date <= week_end)
        )
        upcoming_count = (await self.db.execute(upcoming_stmt)).scalar() or 0

        series_stmt = select(func.count(func.distinct(CalendarEntry.emby_item_id)))
        series_count = (await self.db.execute(series_stmt)).scalar() or 0

        return {
            "month_entries": month_count,
            "upcoming_7d": upcoming_count,
            "tracked_series": series_count,
        }
