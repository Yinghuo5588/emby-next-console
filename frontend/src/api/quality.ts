import apiClient from './client'

export interface QualityOverview {
  resolution: Record<string, number>
  video_range: Record<string, number>
  total: number
  scan: { running: boolean; total: number; scanned: number; error: string | null }
}

export interface QualityItem {
  item_id: string
  name: string
  path: string
  resolution: string
  video_range: string
  width: number | null
  height: number | null
  item_type: string
  poster_url: string
  is_ignored: boolean
}

export const qualityApi = {
  startScan: () => apiClient.post('/quality/scan'),
  scanStatus: () => apiClient.get('/quality/scan-status'),
  overview: () => apiClient.get<QualityOverview>('/quality/overview'),
  items: (params: {
    resolution?: string; video_range?: string; is_ignored?: boolean
    sort?: string; page?: number; size?: number
  }) => apiClient.get('/quality/items', { params }),
  ignore: (id: string) => apiClient.post(`/quality/${id}/ignore`),
  unignore: (id: string) => apiClient.delete(`/quality/${id}/ignore`),
}
