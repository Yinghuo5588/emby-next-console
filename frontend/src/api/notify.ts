import apiClient from './client'

export const notifyApi = {
  list() {
    return apiClient.get('/notify/destinations')
  },
  events() {
    return apiClient.get('/notify/events')
  },
  create(data: { name: string; url: string; secret?: string; events: string[]; is_active: boolean }) {
    return apiClient.post('/notify/destinations', data)
  },
  update(id: number, data: Partial<{ name: string; url: string; secret: string; events: string[]; is_active: boolean }>) {
    return apiClient.patch(`/notify/destinations/${id}`, data)
  },
  delete(id: number) {
    return apiClient.delete(`/notify/destinations/${id}`)
  },
  test(id: number) {
    return apiClient.post(`/notify/destinations/${id}/test`)
  },
}
