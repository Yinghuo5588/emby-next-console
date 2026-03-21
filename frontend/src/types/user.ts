export type UserRole = 'admin' | 'user'
export type UserStatus = 'active' | 'disabled' | 'expired'

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