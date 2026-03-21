import apiClient, { type ApiResponse } from './client'

export interface MeResponse {
  id: string
  username: string
  display_name: string | null
  role: string
  avatar_url: string | null
  created_at: string | null
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export const authApi = {
  async login(data: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    const response = await apiClient.post<ApiResponse<LoginResponse>>('/auth/login', data)
    return response.data
  },

  async me(): Promise<ApiResponse<MeResponse>> {
    const response = await apiClient.get<ApiResponse<MeResponse>>('/auth/me')
    return response.data
  },

  async logout(): Promise<ApiResponse<void>> {
    const response = await apiClient.post<ApiResponse<void>>('/auth/logout')
    return response.data
  },
}
