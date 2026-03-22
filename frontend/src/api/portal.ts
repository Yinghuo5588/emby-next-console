import apiClient, { type ApiResponse } from './client'

export interface PortalUser {
  emby_user_id: string
  username: string
  display_name: string
  is_admin: boolean
  avatar: string | null
}

export interface PortalStats {
  active_sessions: number
  now_playing: Array<{ device: string; item: string }>
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

  async updateProfile(data: { display_name?: string; avatar_url?: string }): Promise<ApiResponse<void>> {
    const res = await apiClient.put('/portal/me/profile', data)
    return res.data
  },

  async changePassword(oldPassword: string, newPassword: string): Promise<ApiResponse<void>> {
    const res = await apiClient.post('/portal/me/change-password', { old_password: oldPassword, new_password: newPassword })
    return res.data
  },
}