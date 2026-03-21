import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi, type User } from '@/api/auth'
import { useRouter } from 'vue-router'

export const useAuthStore = defineStore('auth', () => {
  const router = useRouter()
  
  // State
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Computed
  const isAuthenticated = computed(() => !!token.value && !!user.value)

  // Actions
  const login = async (username: string, password: string) => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await authApi.login({ username, password })
      
      if (response.success) {
        token.value = response.data.token
        user.value = response.data.user
        
        // Store token
        localStorage.setItem('token', response.data.token)
        
        // Clear any previous errors
        error.value = null
        
        return { success: true }
      } else {
        error.value = response.message
        return { success: false, message: response.message }
      }
    } catch (err: any) {
      error.value = err.response?.data?.message || 'Login failed'
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
      error.value = err.response?.data?.message || 'Failed to fetch user'
      return { success: false, message: error.value }
    } finally {
      isLoading.value = false
    }
  }

  const logout = async () => {
    isLoading.value = true
    
    try {
      // Call logout API if we have a token
      if (token.value) {
        await authApi.logout()
      }
    } catch (err) {
      // Silently fail logout API call
      console.error('Logout API call failed:', err)
    } finally {
      // Clear local state regardless of API result
      token.value = null
      user.value = null
      localStorage.removeItem('token')
      isLoading.value = false
      
      // Redirect to login
      router.push('/login')
    }
  }

  // Initialize user if token exists
  const init = async () => {
    if (token.value && !user.value) {
      await fetchUser()
    }
  }

  return {
    // State
    user,
    token,
    isLoading,
    error,
    
    // Computed
    isAuthenticated,
    
    // Actions
    login,
    fetchUser,
    logout,
    init,
  }
})