from pydantic import BaseModel


class StatsOverview(BaseModel):
    total_play_count: int
    total_play_duration_sec: int
    unique_users: int
    unique_media: int


class TopUser(BaseModel):
    user_id: str
    username: str
    play_count: int
    play_duration_sec: int


class TopMedia(BaseModel):
    media_id: str
    media_name: str
    play_count: int


class TrendPoint(BaseModel):
    date: str
    play_count: int
    active_users: int
