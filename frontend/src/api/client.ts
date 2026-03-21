import axios, { type AxiosInstance, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'
import { useRouter } from 'vue-router'

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

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle 401
apiClient.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    // You can transform response data here if needed
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('token')
      // Use router to redirect if in browser context
      if (typeof window !== 'undefined') {
        const router = useRouter()
        router.push('/login')
      }
    }
    return Promise.reject(error)
  }
)

export default apiClient