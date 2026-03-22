import apiClient, { type ApiResponse } from './client'

export interface PermissionTemplate {
  id: number
  name: string
  description: string | null
  library_access: string[] | null
  policy_json: Record<string, any> | null
  configuration_json: Record<string, any> | null
  is_default: boolean
  created_at: string
}

export const templatesApi = {
  async create(data: {
    name: string
    description?: string | null
    library_access?: string[] | null
    policy_json?: Record<string, any> | null
    configuration_json?: Record<string, any> | null
    is_default?: boolean
  }): Promise<ApiResponse<PermissionTemplate>> {
    const res = await apiClient.post('/admin/templates', data)
    return res.data
  },

  async list(page = 1, pageSize = 50): Promise<ApiResponse<{ items: PermissionTemplate[]; total: number }>> {
    const res = await apiClient.get('/admin/templates', { params: { page, page_size: pageSize } })
    return res.data
  },

  async get(id: number): Promise<ApiResponse<PermissionTemplate>> {
    const res = await apiClient.get(`/admin/templates/${id}`)
    return res.data
  },

  async update(id: number, data: Partial<PermissionTemplate>): Promise<ApiResponse<PermissionTemplate>> {
    const res = await apiClient.put(`/admin/templates/${id}`, data)
    return res.data
  },

  async remove(id: number): Promise<ApiResponse<void>> {
    const res = await apiClient.delete(`/admin/templates/${id}`)
    return res.data
  },
}