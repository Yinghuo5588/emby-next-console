from pydantic import BaseModel


class OverviewData(BaseModel):
    total_users: int
    active_users_today: int
    current_active_sessions: int
    total_media_count: int


class PlaybackData(BaseModel):
    today_play_count: int
    today_play_duration_sec: int
    peak_concurrent_today: int


class RiskSummaryData(BaseModel):
    open_risk_count: int
    high_risk_count: int


class NotificationSummaryData(BaseModel):
    unread_count: int


class DashboardSummary(BaseModel):
    overview: OverviewData
    playback: PlaybackData
    risk: RiskSummaryData
    notifications: NotificationSummaryData
