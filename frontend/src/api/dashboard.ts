import apiClient, { type ApiResponse } from './client'

export interface SessionInfo {
  session_id: string
  username: string
  media_name: string
  client: string
  device_name: string
}

export interface DashboardSummary {
  overview: {
    total_users: number
    active_users_today: number
    current_active_sessions: number
    total_media_count: number
  }
  playback: {
    today_play_count: number
    today_play_duration_sec: number
    peak_concurrent_today: number
  }
  risk: {
    open_risk_count: number
    high_risk_count: number
  }
  notifications: {
    unread_count: number
  }
  sessions: SessionInfo[]
}

export const dashboardApi = {
  async summary(): Promise<ApiResponse<DashboardSummary>> {
    const response = await apiClient.get<ApiResponse<DashboardSummary>>('/dashboard/summary')
    return response.data
  },
}
