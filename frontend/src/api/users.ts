import apiClient from './client'

export interface UserInfo {
  user_id: string
  name: string
  is_disabled: boolean
  is_admin: boolean
  last_login_date: string
  create_date: string
  primary_image_tag: string
  has_password: boolean
  policy: Record<string, any>
  expire_date: string | null
  max_concurrent: number
  is_vip: boolean
  note: string
  template_name: string
}

export interface CreateUserRequest {
  name: string
  password: string
  template_user_id?: string
  expire_days?: number
  max_concurrent?: number
  is_vip?: boolean
  note?: string
}

export interface UpdateUserRequest {
  name?: string
  password?: string
  is_disabled?: boolean
  simultaneous_stream_limit?: number
  enable_content_downloading?: boolean
  enable_video_transcoding?: boolean
  max_parental_rating?: number
  enable_remote_access?: boolean
  enable_all_folders?: boolean
  enabled_folders?: string[]
  block_unrated_items?: string[]
  expire_date?: string
  max_concurrent?: number
  is_vip?: boolean
  note?: string
}

export const usersApi = {
  list: () => apiClient.get('/manage/users'),
  get: (id: string) => apiClient.get(`/manage/users/${id}`),
  create: (data: CreateUserRequest) => apiClient.post('/manage/users', data),
  update: (id: string, data: UpdateUserRequest) => apiClient.put(`/manage/users/${id}`, data),
  delete: (id: string) => apiClient.delete(`/manage/users/${id}`),
  batch: (data: { operation: string; user_ids: string[]; days?: number }) =>
    apiClient.post('/manage/users/batch', data),
  libraryFolders: () => apiClient.get('/manage/users/libraries'),
  avatarUrl: (id: string) => `/api/v1/manage/users/${id}/avatar`,
  avatarUrl: (id: string) => `/api/v1/manage/users/${id}/avatar`,
  uploadAvatar: (id: string, file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return apiClient.post(`/manage/users/${id}/avatar`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  deleteAvatar: (id: string) => apiClient.delete(`/manage/users/${id}/avatar`),
}
