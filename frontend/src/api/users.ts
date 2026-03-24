import apiClient, { type ApiResponse } from './client'

export interface UserListItem {
  user_id: string
  username: string
  display_name: string | null
  role: 'admin' | 'user'
  status: 'active' | 'disabled'
  expire_at: string | null
  is_vip: boolean
  created_at: string
  max_concurrent: number | null
  note: string | null
}

export interface UserDetail extends UserListItem {
  emby_user_id: string | null
  concurrent_limit: number | null
  max_bitrate: number | null
  allow_transcode: boolean | null
  client_blacklist: string[] | null
}

export interface UserListResponse {
  items: UserListItem[]
  total: number
  page: number
  page_size: number
}

export interface BatchResult {
  success: string[]
  failed: { user_id: string; error: string }[]
}

export const usersApi = {
  async list(params: { page?: number; page_size?: number } = {}): Promise<ApiResponse<UserListResponse>> {
    const response = await apiClient.get<ApiResponse<UserListResponse>>('/users', { params })
    return response.data
  },

  async get(id: string): Promise<ApiResponse<UserDetail>> {
    const response = await apiClient.get<ApiResponse<UserDetail>>(`/users/${id}`)
    return response.data
  },

  async delete(id: string): Promise<ApiResponse<any>> {
    const res = await apiClient.delete(`/admin/users/${id}`)
    return res.data
  },

  // 手动创建用户
  async createUser(data: {
    username: string
    password?: string | null
    note?: string | null
    expires_days?: number | null
    concurrent_limit?: number | null
    template_emby_user_id?: string | null
  }): Promise<ApiResponse<any>> {
    const res = await apiClient.post('/admin/users/create', data)
    return res.data
  },

  // 用户权限
  async getPermissions(userId: string): Promise<ApiResponse<{ policy: any; configuration: any }>> {
    const res = await apiClient.get(`/admin/users/${userId}/permissions`)
    return res.data
  },

  async updatePermissions(userId: string, policy: any): Promise<ApiResponse<void>> {
    const res = await apiClient.put(`/admin/users/${userId}/permissions`, policy)
    return res.data
  },

  // 用户级覆盖
  async getOverride(userId: string): Promise<ApiResponse<any>> {
    const res = await apiClient.get(`/admin/users/${userId}/override`)
    return res.data
  },

  async upsertOverride(userId: string, data: {
    concurrent_limit?: number | null
    max_bitrate?: number | null
    allow_transcode?: boolean | null
    client_blacklist?: string[] | null
    note?: string | null
  }): Promise<ApiResponse<void>> {
    const res = await apiClient.put(`/admin/users/${userId}/override`, data)
    return res.data
  },

  // 强制下线
  async forceLogout(userId: string): Promise<ApiResponse<void>> {
    const res = await apiClient.post(`/admin/users/${userId}/force-logout`)
    return res.data
  },

  // 批量操作
  async batch(data: {
    action: 'delete' | 'enable' | 'disable' | 'renew' | 'apply_template'
    user_ids: string[]
    days?: number | null
    expires_at?: string | null
    template_id?: string | null
  }): Promise<ApiResponse<BatchResult>> {
    const res = await apiClient.post('/admin/users/batch', data)
    return res.data
  },
}
