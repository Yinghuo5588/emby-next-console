import axios, { type AxiosInstance, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'

export interface ApiResponse<T = any> {
  success: boolean
  message: string
  data: T
  meta?: {
    total?: number
    page?: number
    pageSize?: number
    totalPages?: number
  }
}

const apiClient: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 优先读 portal_token，其次读 admin token
    const portalToken = localStorage.getItem('portal_token')
    const adminToken = localStorage.getItem('token')
    const token = portalToken || adminToken
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

apiClient.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => response,
  (error) => {
    if (error.response?.status === 401) {
      const isPortal = window.location.pathname.startsWith('/portal')
      if (isPortal) {
        localStorage.removeItem('portal_token')
        window.location.href = '/portal/login'
      } else {
        localStorage.removeItem('token')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default apiClient
