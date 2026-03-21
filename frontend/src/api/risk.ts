import apiClient, { type ApiResponse } from './client'

export interface RiskEventItem {
  event_id: string
  user_id: string
  event_type: string
  severity: string
  status: string
  title: string
  description: string | null
  detected_at: string
}

export interface RiskSummary {
  open_count: number
  high_count: number
  recent_events: RiskEventItem[]
}

export interface RiskEventsResponse {
  items: RiskEventItem[]
  total: number
}

export const riskApi = {
  async summary(): Promise<ApiResponse<RiskSummary>> {
    const response = await apiClient.get<ApiResponse<RiskSummary>>('/risk/summary')
    return response.data
  },

  async events(params: { page?: number; page_size?: number } = {}): Promise<ApiResponse<RiskEventsResponse>> {
    const response = await apiClient.get<ApiResponse<RiskEventsResponse>>('/risk/events', { params })
    return response.data
  },

  async action(eventId: string, action: 'ignore' | 'resolve'): Promise<ApiResponse<void>> {
    const response = await apiClient.post<ApiResponse<void>>(`/risk/events/${eventId}/action`, { action })
    return response.data
  },
}
