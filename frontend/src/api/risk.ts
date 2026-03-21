import { get, post } from './client'

export type RiskSeverity = 'low' | 'medium' | 'high'
export type RiskEventStatus = 'open' | 'ignored' | 'resolved'

export interface RiskEventItem {
 event_id: string
 user_id: string | null
 username: string | null
 event_type: string
 severity: RiskSeverity
 status: RiskEventStatus
 title: string
 description: string | null
 detected_at: string
 resolved_at: string | null
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
 summary: () => get<RiskSummary>('/risk/summary'),
 events: (page = 1, page_size = 20, status?: string, severity?: string) =>
 get<RiskEventsResponse>('/risk/events', { page, page_size, status, severity }),
 action: (eventId: string, action: string) => post(`/risk/events/${eventId}/actions`, { action }),
}