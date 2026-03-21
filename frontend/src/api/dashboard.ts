import apiClient, { type ApiResponse } from './client'

export interface DashboardSummary {
  total_users: number
  active_users: number
  total_playbacks: number
  active_playbacks: number
  total_storage_gb: number
  used_storage_gb: number
  risk_events_open: number
  risk_events_high: number
  recent_sessions: Array<{
    id: string
    user_id: string
    username: string
    device: string
    ip: string
    started_at: string
    last_activity: string
  }>
}

export const dashboardApi = {
  // Get dashboard summary
  async summary(): Promise<ApiResponse<DashboardSummary>> {
    const response = await apiClient.get<ApiResponse<DashboardSummary>>('/dashboard/summary')
    return response.data
  },
}