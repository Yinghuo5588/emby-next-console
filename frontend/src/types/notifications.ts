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