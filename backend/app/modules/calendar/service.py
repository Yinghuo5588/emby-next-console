from datetime import date, timedelta, datetime
from sqlalchemy import select, func, text, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.calendar import CalendarEntry, ContentSubscription
from app.core.emby import emby


class CalendarService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_month_entries(self, year: int, month: int) -> dict:
        """获取指定月份的日历条目，按日期分组"""
        stmt = select(CalendarEntry).where(
            and_(
                extract("year", CalendarEntry.air_date) == year,
                extract("month", CalendarEntry.air_date) == month,
            )
        ).order_by(CalendarEntry.air_date, CalendarEntry.series_name, CalendarEntry.episode_number)
        result = await self.db.execute(stmt)
        entries = result.scalars().all()

        # 按日期分组
        by_date: dict[str, list] = {}
        for e in entries:
            d = e.air_date.isoformat()
            if d not in by_date:
                by_date[d] = []
            by_date[d].append({
                "id": e.id,
                "emby_item_id": e.emby_item_id,
                "series_name": e.series_name,
                "season_number": e.season_number,
                "episode_number": e.episode_number,
                "episode_title": e.episode_title,
                "air_date": d,
                "backdrop_url": e.backdrop_url,
                "overview": e.overview,
            })
        return {"entries": by_date, "total": len(entries)}

    async def get_upcoming(self, days: int = 7) -> list[dict]:
        """获取未来 N 天更新"""
        today = date.today()
        end = today + timedelta(days=days)
        stmt = select(CalendarEntry).where(
            and_(CalendarEntry.air_date >= today, CalendarEntry.air_date <= end)
        ).order_by(CalendarEntry.air_date, CalendarEntry.series_name)
        result = await self.db.execute(stmt)
        entries = result.scalars().all()
        return [
            {
                "id": e.id,
                "series_name": e.series_name,
                "season_number": e.season_number,
                "episode_number": e.episode_number,
                "episode_title": e.episode_title,
                "air_date": e.air_date.isoformat(),
                "backdrop_url": e.backdrop_url,
            }
            for e in entries
        ]

    async def sync_from_emby(self) -> int:
        """从 Emby API 同步剧集日历条目"""
        try:
            series_list = await emby.get_items(include_item_types="Series", limit=200)
        except Exception:
            return 0

        count = 0
        for series in series_list:
            series_id = series.get("Id")
            series_name = series.get("Name", "")
            try:
                children = await emby.get_items(parent_id=series_id, include_item_types="Episode", fields="AirDate,Overview,ParentIndexNumber,IndexNumber,ImageTags", limit=200)
            except Exception:
                continue

            for ep in children:
                air_date_str = ep.get("AirDate")
                if not air_date_str:
                    continue
                try:
                    air_date = date.fromisoformat(air_date_str[:10])
                except Exception:
                    continue

                emby_item_id = ep.get("Id", "")
                # upsert: check if exists
                exists_stmt = select(CalendarEntry).where(CalendarEntry.emby_item_id == emby_item_id)
                result = await self.db.execute(exists_stmt)
                if result.scalar_one_or_none():
                    continue

                backdrop = None
                image_tags = ep.get("ImageTags", {})
                if image_tags.get("Primary"):
                    backdrop = f"/Items/{emby_item_id}/Images/Primary"

                entry = CalendarEntry(
                    emby_item_id=emby_item_id,
                    series_name=series_name,
                    season_number=ep.get("ParentIndexNumber"),
                    episode_number=ep.get("IndexNumber"),
                    episode_title=ep.get("Name", ""),
                    air_date=air_date,
                    backdrop_url=backdrop,
                    overview=(ep.get("Overview") or "")[:500],
                )
                self.db.add(entry)
                count += 1

        await self.db.commit()
        return count

    async def get_stats(self) -> dict:
        """日历统计"""
        today = date.today()
        # 本月更新数
        stmt = select(func.count()).where(
            and_(
                extract("year", CalendarEntry.air_date) == today.year,
                extract("month", CalendarEntry.air_date) == today.month,
            )
        )
        result = await self.db.execute(stmt)
        month_count = result.scalar() or 0

        # 未来 7 天
        upcoming_stmt = select(func.count()).where(
            and_(CalendarEntry.air_date >= today, CalendarEntry.air_date <= today + timedelta(days=7))
        )
        result = await self.db.execute(upcoming_stmt)
        upcoming_count = result.scalar() or 0

        # 追踪剧集数
        series_stmt = select(func.count(func.distinct(CalendarEntry.series_name)))
        result = await self.db.execute(series_stmt)
        series_count = result.scalar() or 0

        return {
            "month_entries": month_count,
            "upcoming_7d": upcoming_count,
            "tracked_series": series_count,
        }