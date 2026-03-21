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