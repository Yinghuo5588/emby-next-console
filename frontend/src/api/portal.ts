import apiClient, { type ApiResponse } from './client'

export interface PortalUser {
  emby_user_id: string
  username: string
  display_name: string
  is_admin: boolean
  is_vip: boolean
  max_concurrent: number
  avatar: string | null
}

export interface PortalStats {
  overview: {
    total_plays: number
    total_duration: number
    total_duration_hours: number
    active_sessions: number
  }
  trend: Array<{ date: string; play_count: number; dur: number }>
  top_media: Array<{ clean_name: string; play_count: number; total_duration: number; poster_url?: string; item_type?: string }>
  recent: Array<{ date_created: string; clean_name: string; device: string; play_duration: number; poster_url?: string }>
  devices: Array<{ device: string; count: number }>
  clock: number[][]
}

export interface PortalBadge {
  id: string
  name: string
  icon: string
  color: string
  bg: string
  desc: string
}

export const portalApi = {
  async login(username: string, password: string): Promise<ApiResponse<{ token: string; user: PortalUser }>> {
    const res = await apiClient.post('/portal/login', { username, password })
    return res.data
  },

  async me(): Promise<ApiResponse<PortalUser>> {
    const res = await apiClient.get('/portal/me')
    return res.data
  },

  async stats(): Promise<ApiResponse<PortalStats>> {
    const res = await apiClient.get('/portal/me/stats')
    return res.data
  },

  async badges(): Promise<ApiResponse<PortalBadge[]>> {
    const res = await apiClient.get('/portal/me/badges')
    return res.data
  },

  async updateProfile(data: { display_name?: string; avatar_url?: string }): Promise<ApiResponse<void>> {
    const res = await apiClient.put('/portal/me/profile', data)
    return res.data
  },

  async changePassword(oldPassword: string, newPassword: string): Promise<ApiResponse<void>> {
    const res = await apiClient.post('/portal/me/change-password', { old_password: oldPassword, new_password: newPassword })
    return res.data
  },
}
