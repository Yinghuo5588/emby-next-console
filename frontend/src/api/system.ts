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
    return (await apiClient.get('/system/health')).data
  },
  async settings(): Promise<ApiResponse<SettingItem[]>> {
    return (await apiClient.get('/system/settings')).data
  },
  async updateSetting(key: string, value: any): Promise<ApiResponse<SettingItem>> {
    return (await apiClient.patch(`/system/settings/${key}`, { value })).data
  },
  async jobs(): Promise<ApiResponse<JobRunItem[]>> {
    return (await apiClient.get('/system/jobs')).data
  },
}
