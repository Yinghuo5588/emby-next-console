import apiClient, { type ApiResponse } from './client'

export interface User {
  id: string
  username: string
  email?: string
  avatar?: string
  role: string
  is_active: boolean
  created_at: string
  last_login?: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  token: string
  user: User
}

export const authApi = {
  // Login
  async login(data: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    const response = await apiClient.post<ApiResponse<LoginResponse>>('/auth/login', data)
    return response.data
  },

  // Get current user
  async me(): Promise<ApiResponse<User>> {
    const response = await apiClient.get<ApiResponse<User>>('/auth/me')
    return response.data
  },

  // Logout
  async logout(): Promise<ApiResponse<void>> {
    const response = await apiClient.post<ApiResponse<void>>('/auth/logout')
    return response.data
  },
}