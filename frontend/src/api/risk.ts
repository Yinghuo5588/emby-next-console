import apiClient, { type ApiResponse } from './client'

export interface RiskSummary {
  total_open: number
  total_high: number
  total_medium: number
  total_low: number
  resolved_24h: number
  new_24h: number
}

export interface RiskEvent {
  id: string
  type: string
  severity: 'high' | 'medium' | 'low'
  status: 'open' | 'resolved' | 'ignored'
  title: string
  description: string
  user_id?: string
  username?: string
  ip_address?: string
  device?: string
  metadata?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface RiskEventListParams {
  page?: number
  pageSize?: number
  status?: 'open' | 'resolved' | 'ignored' | 'all'
  severity?: 'high' | 'medium' | 'low' | 'all'
  search?: string
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

export type RiskAction = 'resolve' | 'ignore'

export const riskApi = {
  // Get risk summary
  async summary(): Promise<ApiResponse<RiskSummary>> {
    const response = await apiClient.get<ApiResponse<RiskSummary>>('/risk/summary')
    return response.data
  },

  // List risk events
  async events(params: RiskEventListParams = {}): Promise<ApiResponse<RiskEvent[]>> {
    const response = await apiClient.get<ApiResponse<RiskEvent[]>>('/risk/events', { params })
    return response.data
  },

  // Take action on risk event
  async action(eventId: string, action: RiskAction): Promise<ApiResponse<void>> {
    const response = await apiClient.post<ApiResponse<void>>(`/risk/events/${eventId}/actions`, { action })
    return response.data
  },
}