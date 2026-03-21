import apiClient, { type ApiResponse } from './client'

export interface StatsOverview {
  total_play_count: number
  total_play_duration_sec: number
  unique_users: number
  unique_media: number
}

export interface TrendPoint {
  date: string
  play_count: number
  active_users: number
}

export interface TopUser {
  user_id: string
  username: string
  play_count: number
  play_duration_sec: number
}

export interface TopMedia {
  media_id: string
  media_name: string
  play_count: number
}

export const statsApi = {
  async overview(): Promise<ApiResponse<StatsOverview>> {
    const response = await apiClient.get<ApiResponse<StatsOverview>>('/stats/overview')
    return response.data
  },

  async trends(days: number = 7): Promise<ApiResponse<TrendPoint[]>> {
    const response = await apiClient.get<ApiResponse<TrendPoint[]>>('/stats/trends', {
      params: { days },
    })
    return response.data
  },

  async topUsers(limit: number = 10): Promise<ApiResponse<TopUser[]>> {
    const response = await apiClient.get<ApiResponse<TopUser[]>>('/stats/top-users', {
      params: { limit },
    })
    return response.data
  },

  async topMedia(limit: number = 10): Promise<ApiResponse<TopMedia[]>> {
    const response = await apiClient.get<ApiResponse<TopMedia[]>>('/stats/top-media', {
      params: { limit },
    })
    return response.data
  },
}
