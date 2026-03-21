import { get } from './client'

export interface OverviewData {
 total_users: number
 active_users_today: number
 current_active_sessions: number
 total_media_count: number
}

export interface PlaybackSummaryData {
 today_play_count: number
 today_play_duration_sec: number
 peak_concurrent_today: number
}

export interface DashboardSummary {
 overview: OverviewData
 playback: PlaybackSummaryData
 risk: { open_risk_count: number; high_risk_count: number }
 notifications: { unread_count: number }
}

export interface ActiveSession {
 session_id: string
 user_id: string
 username: string
 media_name: string
 client_name: string | null
 device_name: string | null
 ip_address: string | null
 started_at: string
}

export interface DashboardTrendPoint {
 date: string
 play_count: number
 active_users: number
}

export const dashboardApi = {
 summary: () => get<DashboardSummary>('/dashboard/summary'),
 activeSessions: () => get<ActiveSession[]>('/dashboard/active-sessions'),
 trends: (days = 7) => get<DashboardTrendPoint[]>('/dashboard/trends', { days }),
}