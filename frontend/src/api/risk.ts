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

export interface RiskActionLog {
  id: number
  action: string
  target: string
  reason: string | null
  created_at: string
}

export interface RiskActionLogsResponse {
  items: RiskActionLog[]
  total: number
}

export interface ConcurrentItem {
  user_id: string
  user_name: string
  current: number
  max: number
  exceeded: boolean
  sessions: Array<{
    session_id: string
    client: string
    device_name: string
    title: string
  }>
}

export interface RiskPolicy {
  client_policy: {
    mode: string
    fuzzy_match: boolean
    action: string
    escalation: boolean
    escalation_steps: string[]
    ban_hours: number
  }
  concurrent_policy: {
    default_max: number
    action: string
    kick_order: string
  }
}

export const riskApi = {
  async summary(): Promise<ApiResponse<RiskSummary>> {
    return (await apiClient.get('/risk/summary')).data
  },
  async events(page = 1, pageSize = 20, status?: string, severity?: string): Promise<ApiResponse<RiskEventsResponse>> {
    const params: Record<string, any> = { page, page_size: pageSize }
    if (status) params.status = status
    if (severity) params.severity = severity
    return (await apiClient.get('/risk/events', { params })).data
  },
  async action(eventId: string, action: 'ignore' | 'resolve'): Promise<ApiResponse<void>> {
    return (await apiClient.post(`/risk/events/${eventId}/action`, { action })).data
  },
  async logs(page = 1, pageSize = 20): Promise<ApiResponse<RiskActionLogsResponse>> {
    return (await apiClient.get('/risk/logs', { params: { page, page_size: pageSize } })).data
  },
  async kick(sessionId: string, deviceId = '', level = 'soft'): Promise<ApiResponse<{ success: boolean; level: string }>> {
    return (await apiClient.post('/risk/kick', { session_id: sessionId, device_id: deviceId, level })).data
  },
  async ban(userId: string): Promise<ApiResponse<{ success: boolean }>> {
    return (await apiClient.post('/risk/ban', { user_id: userId })).data
  },
  async unban(userId: string): Promise<ApiResponse<{ success: boolean }>> {
    return (await apiClient.post('/risk/unban', { user_id: userId })).data
  },
  async blacklist(): Promise<ApiResponse<string[]>> {
    return (await apiClient.get('/risk/blacklist')).data
  },
  async addBlacklist(name: string): Promise<ApiResponse<string[]>> {
    return (await apiClient.post('/risk/blacklist', { name })).data
  },
  async removeBlacklist(name: string): Promise<ApiResponse<string[]>> {
    return (await apiClient.delete(`/risk/blacklist/${encodeURIComponent(name)}`)).data
  },
  async sweep(): Promise<ApiResponse<any>> {
    return (await apiClient.post('/risk/sweep')).data
  },
  async scan(): Promise<ApiResponse<any>> {
    return (await apiClient.post('/risk/scan')).data
  },
  async concurrentStatus(): Promise<ApiResponse<ConcurrentItem[]>> {
    return (await apiClient.get('/risk/status')).data
  },

  async getPolicy(): Promise<ApiResponse<RiskPolicy>> {
    return (await apiClient.get('/risk/policy')).data
  },

  async updatePolicy(data: Partial<RiskPolicy>): Promise<ApiResponse<RiskPolicy>> {
    return (await apiClient.put('/risk/policy', data)).data
  },
}
