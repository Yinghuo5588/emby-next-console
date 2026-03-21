import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi, type MeResponse } from '@/api/auth'
import { useRouter } from 'vue-router'

export const useAuthStore = defineStore('auth', () => {
  const router = useRouter()

  const user = ref<MeResponse | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => !!token.value)

  const login = async (username: string, password: string) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await authApi.login({ username, password })

      if (response.success) {
        token.value = response.data.access_token
        localStorage.setItem('token', response.data.access_token)

        // Fetch user info after login
        await fetchUser()
        error.value = null
        return { success: true }
      } else {
        error.value = response.message
        return { success: false, message: response.message }
      }
    } catch (err: any) {
      error.value = err.response?.data?.message || '登录失败'
      return { success: false, message: error.value }
    } finally {
      isLoading.value = false
    }
  }

  const fetchUser = async () => {
    if (!token.value) return { success: false, message: 'No token' }

    isLoading.value = true
    error.value = null

    try {
      const response = await authApi.me()
      if (response.success) {
        user.value = response.data
        return { success: true }
      } else {
        error.value = response.message
        return { success: false, message: response.message }
      }
    } catch (err: any) {
      error.value = err.response?.data?.message || '获取用户信息失败'
      return { success: false, message: error.value }
    } finally {
      isLoading.value = false
    }
  }

  const logout = async () => {
    isLoading.value = true
    try {
      if (token.value) await authApi.logout()
    } catch {}
    finally {
      token.value = null
      user.value = null
      localStorage.removeItem('token')
      isLoading.value = false
      router.push('/login')
    }
  }

  const init = async () => {
    if (token.value && !user.value) {
      await fetchUser()
    }
  }

  return { user, token, isLoading, error, isAuthenticated, login, fetchUser, logout, init }
})
