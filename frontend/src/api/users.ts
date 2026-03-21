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
}

export interface UserDetail extends UserListItem {
  note: string | null
  max_concurrent: number | null
  emby_user_id: string | null
}

export interface UserListResponse {
  items: UserListItem[]
  total: number
  page: number
  page_size: number
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
}
