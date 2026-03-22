from pydantic import BaseModel


class CalendarEntryItem(BaseModel):
    id: int
    emby_item_id: str
    series_name: str
    season_number: int
    episode_number: int
    episode_title: str
    air_date: str
    backdrop_url: str | None = None
    overview: str = ""
    has_file: bool = False


class CalendarMonthResponse(BaseModel):
    entries: dict[str, list[CalendarEntryItem]]
    total: int


class WeekDayItem(BaseModel):
    dow: int
    label: str
    date: str
    entries: list[CalendarEntryItem]


class CalendarWeekResponse(BaseModel):
    waterfall: list[WeekDayItem]
    week_start: str
    week_end: str
    total: int


class CalendarStatsResponse(BaseModel):
    month_entries: int
    upcoming_7d: int
    tracked_series: int
