import apiClient, { type ApiResponse } from './client'

export interface HealthResponse {
  status: string
  db: string
  redis: string
}

export interface SettingItem {
  setting_key: string
  setting_group: string
  value: any
  description: string | null
}

export interface JobRunItem {
  job_id: string
  job_type: string
  status: string
  started_at: string | null
  finished_at: string | null
  error_message: string | null
}

export const systemApi = {
  async health(): Promise<ApiResponse<HealthResponse>> {
    const response = await apiClient.get<ApiResponse<HealthResponse>>('/system/health')
    return response.data
  },

  async settings(): Promise<ApiResponse<SettingItem[]>> {
    const response = await apiClient.get<ApiResponse<SettingItem[]>>('/system/settings')
    return response.data
  },

  async updateSetting(key: string, value: any): Promise<ApiResponse<SettingItem>> {
    const response = await apiClient.patch<ApiResponse<SettingItem>>(`/system/settings/${key}`, { value })
    return response.data
  },

  async jobs(): Promise<ApiResponse<JobRunItem[]>> {
    const response = await apiClient.get<ApiResponse<JobRunItem[]>>('/system/jobs')
    return response.data
  },
}
