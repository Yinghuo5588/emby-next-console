import { get, post } from './client'

export type NotificationLevel = 'info' | 'warning' | 'error'

export interface NotificationItem {
 notification_id: string
 type: string
 title: string
 message: string
 level: NotificationLevel
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
 list: (page = 1, page_size = 20) => get<NotificationsResponse>('/notifications', { page, page_size }),
 unreadCount: () => get<{ unread_count: number }>('/notifications/unread-count'),
 markRead: (id: string) => post(`/notifications/${id}/read`),
 markAllRead: () => post('/notifications/read-all'),
}