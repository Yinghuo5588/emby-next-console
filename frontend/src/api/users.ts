import apiClient, { type ApiResponse } from './client'

export interface User {
  id: string
  username: string
  email?: string
  avatar?: string
  role: string
  is_active: boolean
  is_vip: boolean
  created_at: string
  last_login?: string
  total_playbacks: number
  total_duration_hours: number
  devices: string[]
}

export interface UserListParams {
  page?: number
  pageSize?: number
  search?: string
  status?: 'active' | 'inactive' | 'all'
  is_vip?: boolean | 'all'
  role?: string
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

export interface UserUpdateData {
  username?: string
  email?: string
  role?: string
  is_active?: boolean
  is_vip?: boolean
}

export const usersApi = {
  // List users with filters
  async list(params: UserListParams = {}): Promise<ApiResponse<User[]>> {
    const response = await apiClient.get<ApiResponse<User[]>>('/users', { params })
    return response.data
  },

  // Get single user
  async get(id: string): Promise<ApiResponse<User>> {
    const response = await apiClient.get<ApiResponse<User>>(`/users/${id}`)
    return response.data
  },

  // Update user
  async update(id: string, data: UserUpdateData): Promise<ApiResponse<User>> {
    const response = await apiClient.patch<ApiResponse<User>>(`/users/${id}`, data)
    return response.data
  },
}