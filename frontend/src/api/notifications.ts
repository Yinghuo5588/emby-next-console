import apiClient, { type ApiResponse } from './client'

export interface Notification {
  id: string
  level: 'info' | 'warning' | 'error' | 'success'
  title: string
  body: string
  read: boolean
  action_url?: string
  action_text?: string
  created_at: string
}

export interface NotificationListParams {
  page?: number
  pageSize?: number
  unread_only?: boolean
}

export const notificationsApi = {
  // List notifications
  async list(params: NotificationListParams = {}): Promise<ApiResponse<Notification[]>> {
    const response = await apiClient.get<ApiResponse<Notification[]>>('/notifications', { params })
    return response.data
  },

  // Get unread count
  async unreadCount(): Promise<ApiResponse<{ count: number }>> {
    const response = await apiClient.get<ApiResponse<{ count: number }>>('/notifications/unread-count')
    return response.data
  },

  // Mark notification as read
  async markRead(id: string): Promise<ApiResponse<void>> {
    const response = await apiClient.post<ApiResponse<void>>(`/notifications/${id}/read`)
    return response.data
  },

  // Mark all notifications as read
  async markAllRead(): Promise<ApiResponse<void>> {
    const response = await apiClient.post<ApiResponse<void>>('/notifications/read-all')
    return response.data
  },
}