import apiClient from './client'

export const calendarApi = {
  upcoming(weekOffset = 0) {
    return apiClient.get('/calendar/upcoming', { params: { week_offset: weekOffset } })
  },
  refresh(weekOffset = 0) {
    return apiClient.post('/calendar/refresh', null, { params: { week_offset: weekOffset } })
  },
  embyInfo() {
    return apiClient.get('/calendar/emby-info')
  },
}
