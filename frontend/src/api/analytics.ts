import apiClient, { type ApiResponse } from './client'

export interface ClockHeatmap {
  grid: number[][] // 24 x 7
}

export interface DeviceItem {
  device: string
  count: number
}

export interface GenreItem {
  genre: string
  count: number
  percentage: number
}

export interface HotRankItem {
  item_name: string
  play_count: number
  unique_users: number
}

export interface DurationRankItem {
  item_name: string
  total_duration_min: number
  play_count: number
}

export interface UserRankItem {
  username: string
  play_count: number
  total_duration_min: number
  last_played: string
}

export interface QualityData {
  total_count: number
  transcoding_rate: number
  scan_time: string
  resolution: { '4k': number; '1080p': number; '720p': number; 'sd': number }
  codec: { hevc: number; h264: number; av1: number; other: number }
  hdr: { dolby_vision: number; hdr10: number; sdr: number }
}

export interface WatchHistoryItem {
  user_name: string
  item_name: string
  device: string
  start_time: string
  duration_min: number
  pct_complete: number
}

export const analyticsApi = {
  async watchHistory(params: { user_id?: string; page?: number; page_size?: number; days?: number } = {}): Promise<ApiResponse<{ items: WatchHistoryItem[]; total: number }>> {
    const res = await apiClient.get('/admin/analytics/watch-history', { params })
    return res.data
  },

  async clock24h(days = 30, userId?: string): Promise<ApiResponse<ClockHeatmap>> {
    const res = await apiClient.get('/admin/analytics/clock-24h', { params: { days, user_id: userId } })
    return res.data
  },

  async deviceDist(days = 30): Promise<ApiResponse<DeviceItem[]>> {
    const res = await apiClient.get('/admin/analytics/device-dist', { params: { days } })
    return res.data
  },

  async genrePreference(days = 30, userId?: string): Promise<ApiResponse<GenreItem[]>> {
    const res = await apiClient.get('/admin/analytics/genre-preferences', { params: { days, user_id: userId } })
    return res.data
  },

  async hotRank(days = 30, limit = 20): Promise<ApiResponse<HotRankItem[]>> {
    const res = await apiClient.get('/admin/analytics/hot-rank', { params: { days, limit } })
    return res.data
  },

  async durationRank(days = 30, limit = 20): Promise<ApiResponse<DurationRankItem[]>> {
    const res = await apiClient.get('/admin/analytics/duration-rank', { params: { days, limit } })
    return res.data
  },

  async userRank(days = 30, limit = 20): Promise<ApiResponse<UserRankItem[]>> {
    const res = await apiClient.get('/admin/analytics/user-rank', { params: { days, limit } })
    return res.data
  },

  async quality(days = 30): Promise<ApiResponse<QualityData>> {
    const res = await apiClient.get('/admin/analytics/quality', { params: { days } })
    return res.data
  },
}