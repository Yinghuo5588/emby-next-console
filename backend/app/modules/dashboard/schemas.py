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


class SessionInfo(BaseModel):
    session_id: str
    username: str
    media_name: str
    client: str = ""
    device_name: str = ""


class DashboardSummary(BaseModel):
    overview: OverviewData
    playback: PlaybackData
    risk: RiskSummaryData
    notifications: NotificationSummaryData
    sessions: list[SessionInfo] = []
