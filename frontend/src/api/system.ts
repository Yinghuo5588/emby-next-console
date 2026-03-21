import apiClient, { type ApiResponse } from './client'

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy'
  uptime_seconds: number
  version: string
  database: {
    status: 'connected' | 'disconnected'
    latency_ms: number
  }
  cache: {
    status: 'connected' | 'disconnected'
    hit_rate: number
  }
  storage: {
    total_gb: number
    used_gb: number
    free_gb: number
  }
  last_check: string
}

export interface SystemSetting {
  key: string
  value: any
  category: string
  label: string
  description?: string
  type: 'string' | 'number' | 'boolean' | 'select'
  options?: Array<{ label: string; value: any }>
  editable: boolean
}

export interface SystemJob {
  id: string
  name: string
  type: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  started_at?: string
  completed_at?: string
  duration_ms?: number
  result?: any
  error?: string
}

export const systemApi = {
  // Get system health
  async health(): Promise<ApiResponse<SystemHealth>> {
    const response = await apiClient.get<ApiResponse<SystemHealth>>('/system/health')
    return response.data
  },

  // Get system settings
  async settings(): Promise<ApiResponse<SystemSetting[]>> {
    const response = await apiClient.get<ApiResponse<SystemSetting[]>>('/system/settings')
    return response.data
  },

  // Update system setting
  async updateSetting(key: string, value: any): Promise<ApiResponse<SystemSetting>> {
    const response = await apiClient.patch<ApiResponse<SystemSetting>>(`/system/settings/${key}`, { value })
    return response.data
  },

  // Get system jobs
  async jobs(): Promise<ApiResponse<SystemJob[]>> {
    const response = await apiClient.get<ApiResponse<SystemJob[]>>('/system/jobs')
    return response.data
  },
}