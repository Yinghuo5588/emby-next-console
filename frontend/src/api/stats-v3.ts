/**
 * 统计 V3 API — 每个端点只做一件事
 */
import client from './client'

export interface OverviewData {
  total_plays: number
  total_duration_hours: number
  active_users_30d: number
  library: { movie: number; series: number; episode: number }
}

export interface TopContentItem {
  item_id: string
  name: string
  type: string
  play_count: number
  total_duration_hours: number
  poster_url: string
}

export interface TopUserItem {
  user_id: string
  username: string
  play_count: number
  total_duration_hours: number
}

export interface ContentRankingItem {
  item_id: string
  name: string
  type: string
  play_count: number
  total_duration_min: number
  poster_url: string
}

export interface ContentRankings {
  total: number
  items: ContentRankingItem[]
}

export interface ContentDetail {
  name: string
  type: string
  trend: Record<string, { plays: number; hours: number }>
  viewers: { user_id: string; username: string; play_count: number; duration_hours: number }[]
  poster_url: string
}

export interface UserRankings {
  total: number
  items: TopUserItem[]
}

export interface Badge {
  id: string
  name: string
  icon: string
  color: string
  desc: string
}

export interface UserDetail {
  user_id: string
  username: string
  account_age_days: number
  kpis: { total_plays: number; total_duration_hours: number; avg_session_min: number }
  preference: { movie_plays: number; episode_plays: number; tag: string }
  top_fav: { name: string; hours: number; poster_url: string } | null
  hourly: number[]
  devices: { device: string; count: number }[]
  recent_plays: { name: string; item_id: string; date: string; duration_min: number; poster_url: string }[]
  badges: Badge[]
}

export const statsApiV3 = {
  overview: () => client.get('/stats/overview'),
  trend: (period: string = '30d') => client.get('/stats/trend', { params: { period } }),
  topContent: (limit: number = 5, period: string = '7d') =>
    client.get('/stats/top-content', { params: { limit, period } }),
  topUsers: (limit: number = 5, period: string = '7d') =>
    client.get('/stats/top-users', { params: { limit, period } }),
  contentRankings: (params: { type?: string; period?: string; sort?: string; page?: number; size?: number }) =>
    client.get('/stats/content-rankings', { params }),
  contentDetail: (item_id: string) => client.get(`/stats/content/${item_id}`),
  userRankings: (params: { period?: string; page?: number; size?: number }) =>
    client.get('/stats/user-rankings', { params }),
  userDetail: (user_id: string) => client.get(`/stats/users/${user_id}`),
  heatmap: (period: string = '30d') => client.get('/stats/heatmap', { params: { period } }),
  deviceDist: (period: string = '30d', type: string = 'client') =>
    client.get('/stats/device-dist', { params: { period, type } }),
}
