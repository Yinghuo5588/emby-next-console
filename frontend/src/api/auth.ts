import { get, post } from './client'

export interface LoginPayload { username: string; password: string }
export interface TokenResponse { access_token: string; token_type: string }
export interface MeResponse { user_id: string; username: string; role: string; display_name?: string }

export const authApi = {
 login: (payload: LoginPayload) => post<TokenResponse>('/auth/login', payload),
 me: () => get<MeResponse>('/auth/me'),
 logout: () => post<void>('/auth/logout'),
}