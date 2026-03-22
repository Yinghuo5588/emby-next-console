import apiClient, { type ApiResponse } from './client'

export interface PosterTemplate {
  id: number
  name: string
  description: string | null
  layout: string
  background_color: string
  text_color: string
  accent_color: string
  columns: number
  show_rating: boolean
  show_year: boolean
  show_genres: boolean
  cover_text: string | null
}

export interface GeneratedPoster {
  id: number
  template_id: number | null
  title: string
  item_ids: string[] | null
  status: string
}

export const posterApi = {
  async listTemplates(): Promise<ApiResponse<PosterTemplate[]>> {
    const res = await apiClient.get('/admin/poster/templates')
    return res.data
  },
  async createTemplate(data: Partial<PosterTemplate>): Promise<ApiResponse<PosterTemplate>> {
    const res = await apiClient.post('/admin/poster/templates', data)
    return res.data
  },
  async generate(data: { template_id?: number; item_ids?: string[]; title?: string }): Promise<ApiResponse<GeneratedPoster>> {
    const res = await apiClient.post('/admin/poster/generate', data)
    return res.data
  },
  async listGenerated(page = 1, pageSize = 20): Promise<ApiResponse<{ items: GeneratedPoster[]; total: number }>> {
    const res = await apiClient.get('/admin/poster/generated', { params: { page, page_size: pageSize } })
    return res.data
  },
  async getHtml(posterId: number): Promise<ApiResponse<{ html: string }>> {
    const res = await apiClient.get(`/admin/poster/generated/${posterId}/html`)
    return res.data
  },
}
