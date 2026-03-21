import apiClient, { type ApiResponse } from './client'

export interface NotificationItem {
  notification_id: string
  type: string
  title: string
  message: string
  level: string
  is_read: boolean
  action_url: string | null
  created_at: string
}

export interface NotificationsResponse {
  items: NotificationItem[]
  total: number
  unread_count: number
}

export const notificationsApi = {
  async list(page = 1, pageSize = 20): Promise<ApiResponse<NotificationsResponse>> {
    const response = await apiClient.get<ApiResponse<NotificationsResponse>>('/notifications', { params: { page, page_size: pageSize } })
    return response.data
  },

  async unreadCount(): Promise<ApiResponse<{ unread_count: number }>> {
    const response = await apiClient.get<ApiResponse<{ unread_count: number }>>('/notifications/unread-count')
    return response.data
  },

  async markRead(id: string): Promise<ApiResponse<void>> {
    const response = await apiClient.post<ApiResponse<void>>(`/notifications/${id}/read`)
    return response.data
  },

  async markAllRead(): Promise<ApiResponse<void>> {
    const response = await apiClient.post<ApiResponse<void>>('/notifications/read-all')
    return response.data
  },
}
