import apiClient, { type ApiResponse } from './client'

export interface TaskItem {
  id: string
  task_type: string
  status: string
  progress: number
  params: Record<string, any>
  result: any
  error: string | null
  created_at: string | null
  started_at: string | null
  finished_at: string | null
}

export interface TaskStats {
  total: number
  pending: number
  running: number
  completed: number
  failed: number
  cancelled: number
}

export const tasksApi = {
  async list(status?: string, page = 1, pageSize = 20): Promise<ApiResponse<{ items: TaskItem[]; total: number; page: number }>> {
    const res = await apiClient.get('/admin/tasks', { params: { status, page, page_size: pageSize } })
    return res.data
  },
  async get(id: string): Promise<ApiResponse<TaskItem>> {
    const res = await apiClient.get(`/admin/tasks/${id}`)
    return res.data
  },
  async cancel(id: string): Promise<ApiResponse<TaskItem>> {
    const res = await apiClient.post(`/admin/tasks/${id}/cancel`)
    return res.data
  },
  async stats(): Promise<ApiResponse<TaskStats>> {
    const res = await apiClient.get('/admin/tasks/stats/overview')
    return res.data
  },
}
