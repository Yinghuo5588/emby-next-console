import apiClient, { type ApiResponse } from './client'

export interface InviteCode {
  id: number
  code: string
  template_emby_user_id: string | null
  permission_template_id: number | null
  max_uses: number
  used_count: number
  expires_at: string | null
  concurrent_limit: number | null
  status: string
  created_at: string
}

export interface InviteStats {
  total: number
  active: number
  used: number
  expired: number
  disabled: number
}

export const invitesApi = {
  async create(data: {
    max_uses?: number
    expires_days?: number | null
    template_emby_user_id?: string | null
    permission_template_id?: number | null
    concurrent_limit?: number | null
    custom_code?: string | null
  }): Promise<ApiResponse<InviteCode>> {
    const res = await apiClient.post('/admin/invites', data)
    return res.data
  },

  async list(status?: string, page = 1, pageSize = 20): Promise<ApiResponse<{ items: InviteCode[]; total: number }>> {
    const params: any = { page, page_size: pageSize }
    if (status) params.status = status
    const res = await apiClient.get('/admin/invites', { params })
    return res.data
  },

  async stats(): Promise<ApiResponse<InviteStats>> {
    const res = await apiClient.get('/admin/invites/stats')
    return res.data
  },

  async disable(id: number): Promise<ApiResponse<void>> {
    const res = await apiClient.delete(`/admin/invites/${id}`)
    return res.data
  },

  async validate(code: string): Promise<{ valid: boolean; message?: string }> {
    const res = await apiClient.get(`/admin/invites/public/validate/${code}`)
    return res.data
  },
}