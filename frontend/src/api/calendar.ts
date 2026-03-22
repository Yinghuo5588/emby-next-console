import apiClient, { type ApiResponse } from './client'

export interface CalendarEntry {
  id: number
  emby_item_id: string
  series_name: string
  season_number: number
  episode_number: number
  episode_title: string
  air_date: string
  backdrop_url: string | null
  overview: string
}

export interface CalendarMonthData {
  entries: Record<string, CalendarEntry[]>
  total: number
}

export interface CalendarStats {
  month_entries: number
  upcoming_7d: number
  tracked_series: number
}

export const calendarApi = {
  async month(year: number, month: number): Promise<ApiResponse<CalendarMonthData>> {
    const res = await apiClient.get('/calendar/month', { params: { year, month } })
    return res.data
  },

  async upcoming(days = 7): Promise<ApiResponse<CalendarEntry[]>> {
    const res = await apiClient.get('/calendar/upcoming', { params: { days } })
    return res.data
  },

  async sync(): Promise<ApiResponse<{ synced: number }>> {
    const res = await apiClient.post('/calendar/sync')
    return res.data
  },

  async stats(): Promise<ApiResponse<CalendarStats>> {
    const res = await apiClient.get('/calendar/stats')
    return res.data
  },
}