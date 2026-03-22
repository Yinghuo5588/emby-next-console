from pydantic import BaseModel
from typing import List, Optional, Dict, Any


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


# Analytics schemas
class WatchHistoryItem(BaseModel):
    item_name: str
    user_id: Optional[str] = None
    username: Optional[str] = None
    start_time: str
    end_time: Optional[str] = None
    duration_min: float
    client_name: Optional[str] = None


class WatchHistoryResponse(BaseModel):
    items: List[WatchHistoryItem]
    total: int
    page: int
    page_size: int


class ClockHeatmapResponse(BaseModel):
    grid: List[List[int]]  # 24x7 matrix


class DeviceDistributionItem(BaseModel):
    device: str
    count: int


class GenrePreferenceItem(BaseModel):
    genre: str
    count: int
    percentage: float


class HotRankItem(BaseModel):
    item_name: str
    play_count: int
    unique_users: int


class DurationRankItem(BaseModel):
    item_name: str
    total_duration_min: float
    play_count: int


class UserRankItem(BaseModel):
    username: str
    play_count: int
    total_duration_min: float
    last_played: Optional[str] = None


class QualityAnalysisResponse(BaseModel):
    resolution_dist: List[Dict[str, Any]]
    transcoding_rate: float
