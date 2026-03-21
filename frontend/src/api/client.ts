import axios, { type AxiosInstance } from 'axios'
import type { ApiResponse } from '@/types/api'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const http: AxiosInstance = axios.create({
 baseURL: `${BASE_URL}/api/v1`,
 timeout: 15000,
 headers: { 'Content-Type': 'application/json' },
})

// 请求拦截：注入 token
http.interceptors.request.use((config) => {
 const token = localStorage.getItem('access_token')
 if (token) config.headers.Authorization = `Bearer ${token}`
 return config
})

// 响应拦截：处理 401
http.interceptors.response.use(
 (res) => res,
 (err) => {
 if (err.response?.status === 401) {
 localStorage.removeItem('access_token')
 window.location.href = '/login'
 }
 return Promise.reject(err)
 }
)

export async function get<T>(url: string, params?: Record<string, unknown>): Promise<T> {
 const res = await http.get<ApiResponse<T>>(url, { params })
 return res.data.data as T
}

export async function post<T>(url: string, body?: unknown): Promise<T> {
 const res = await http.post<ApiResponse<T>>(url, body)
 return res.data.data as T
}

export async function patch<T>(url: string, body?: unknown): Promise<T> {
 const res = await http.patch<ApiResponse<T>>(url, body)
 return res.data.data as T
}