import apiClient, { type ApiResponse } from './client'

export interface StatsOverview {
  total_playbacks: number
  unique_users: number
  total_duration_hours: number
  avg_session_minutes: number
  peak_concurrent: number
  bandwidth_gb: number
}

export interface TrendPoint {
  date: string
  playbacks: number
  users: number
  duration: number
}

export interface TopUser {
  user_id: string
  username: string
  playbacks: number
  duration_hours: number
  last_active: string
}

export interface TopMedia {
  media_id: string
  title: string
  type: string
  playbacks: number
  duration_hours: number
  last_played: string
}

export const statsApi = {
  // Get overview stats
  async overview(): Promise<ApiResponse<StatsOverview>> {
    const response = await apiClient.get<ApiResponse<StatsOverview>>('/stats/overview')
    return response.data
  },

  // Get trends
  async trends(days: number = 7): Promise<ApiResponse<TrendPoint[]>> {
    const response = await apiClient.get<ApiResponse<TrendPoint[]>>('/stats/trends', {
      params: { days },
    })
    return response.data
  },

  // Get top users
  async topUsers(limit: number = 10): Promise<ApiResponse<TopUser[]>> {
    const response = await apiClient.get<ApiResponse<TopUser[]>>('/stats/top-users', {
      params: { limit },
    })
    return response.data
  },

  // Get top media
  async topMedia(limit: number = 10): Promise<ApiResponse<TopMedia[]>> {
    const response = await apiClient.get<ApiResponse<TopMedia[]>>('/stats/top-media', {
      params: { limit },
    })
    return response.data
  },
}