import { get, patch, post } from './client'

export type UserStatus = 'active' | 'disabled' | 'expired'
export type UserRole = 'admin' | 'user'

export interface UserListItem {
 user_id: string
 username: string
 display_name: string | null
 role: UserRole
 status: UserStatus
 expire_at: string | null
 is_vip: boolean
 created_at: string
}

export interface UserDetail extends UserListItem {
 note: string | null
 max_concurrent: number | null
 emby_user_id: string | null
}

export interface UserUpdateRequest {
 display_name?: string
 status?: UserStatus
 expire_at?: string | null
 note?: string
 is_vip?: boolean
 max_concurrent?: number | null
}

export interface UserListResponse {
 items: UserListItem[]
 total: number
 page: number
 page_size: number
}

export const usersApi = {
 list: (params: { page?: number; page_size?: number; status?: string } = {}) =>
 get<UserListResponse>('/users', params),
 detail: (userId: string) => get<UserListItem>(`/users/${userId}`),
 update: (userId: string, body: UserUpdateRequest) =>
 patch<UserListItem>(`/users/${userId}`, body),
 action: (userId: string, action: string) =>
 post<UserListItem>(`/users/${userId}/actions`, { action }),
}