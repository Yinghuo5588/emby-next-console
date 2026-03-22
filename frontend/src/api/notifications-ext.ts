import apiClient, { type ApiResponse } from './client'

export interface NotificationChannel {
  id: number
  name: string
  channel_type: string
  config: Record<string, any> | null
  is_active: boolean
  created_at: string | null
}

export interface NotificationTemplate {
  id: number
  name: string
  template_type: string
  title_template: string
  body_template: string
  variables: string[] | null
  is_default: boolean
}

export interface NotificationRule {
  id: number
  event_type: string
  channel_id: number
  template_id: number | null
  is_active: boolean
}

export interface NotificationLog {
  id: number
  event_type: string
  channel_id: number | null
  template_id: number | null
  recipient_user_id: number | null
  title: string
  body: string
  status: string
  error_message: string | null
  sent_at: string | null
  created_at: string | null
}

export const notificationsExtApi = {
  // Channels
  async createChannel(data: Partial<NotificationChannel>): Promise<ApiResponse<NotificationChannel>> {
    const res = await apiClient.post('/notifications/channels', data)
    return res.data
  },
  async listChannels(): Promise<ApiResponse<NotificationChannel[]>> {
    const res = await apiClient.get('/notifications/channels')
    return res.data
  },
  async updateChannel(id: number, data: Partial<NotificationChannel>): Promise<ApiResponse<NotificationChannel>> {
    const res = await apiClient.put(`/notifications/channels/${id}`, data)
    return res.data
  },
  async deleteChannel(id: number): Promise<ApiResponse<void>> {
    const res = await apiClient.delete(`/notifications/channels/${id}`)
    return res.data
  },
  async testChannel(id: number): Promise<ApiResponse<any>> {
    const res = await apiClient.post(`/notifications/channels/${id}/test`)
    return res.data
  },

  // Templates
  async createTemplate(data: Partial<NotificationTemplate>): Promise<ApiResponse<NotificationTemplate>> {
    const res = await apiClient.post('/notifications/templates', data)
    return res.data
  },
  async listTemplates(type?: string): Promise<ApiResponse<NotificationTemplate[]>> {
    const res = await apiClient.get('/notifications/templates', { params: { template_type: type } })
    return res.data
  },
  async updateTemplate(id: number, data: Partial<NotificationTemplate>): Promise<ApiResponse<NotificationTemplate>> {
    const res = await apiClient.put(`/notifications/templates/${id}`, data)
    return res.data
  },
  async deleteTemplate(id: number): Promise<ApiResponse<void>> {
    const res = await apiClient.delete(`/notifications/templates/${id}`)
    return res.data
  },

  // Rules
  async createRule(data: Partial<NotificationRule>): Promise<ApiResponse<NotificationRule>> {
    const res = await apiClient.post('/notifications/rules', data)
    return res.data
  },
  async listRules(eventType?: string): Promise<ApiResponse<NotificationRule[]>> {
    const res = await apiClient.get('/notifications/rules', { params: { event_type: eventType } })
    return res.data
  },
  async updateRule(id: number, data: Partial<NotificationRule>): Promise<ApiResponse<NotificationRule>> {
    const res = await apiClient.put(`/notifications/rules/${id}`, data)
    return res.data
  },
  async deleteRule(id: number): Promise<ApiResponse<void>> {
    const res = await apiClient.delete(`/notifications/rules/${id}`)
    return res.data
  },

  // Logs
  async listLogs(page = 1, pageSize = 20, eventType?: string, status?: string): Promise<ApiResponse<{ items: NotificationLog[]; total: number; page: number; page_size: number }>> {
    const res = await apiClient.get('/notifications/logs', { params: { page, page_size: pageSize, event_type: eventType, status } })
    return res.data
  },
}