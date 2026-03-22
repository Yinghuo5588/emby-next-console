import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { portalApi, type PortalUser } from '@/api/portal'

export const usePortalAuthStore = defineStore('portal-auth', () => {
  const token = ref(localStorage.getItem('portal_token') || '')
  const user = ref<PortalUser | null>(null)

  const isLoggedIn = computed(() => !!token.value)

  async function login(username: string, password: string) {
    const res = await portalApi.login(username, password)
    if (res.success && res.data) {
      token.value = res.data.token
      user.value = res.data.user
      localStorage.setItem('portal_token', res.data.token)
      // 设置 axios 默认 header
      const { default: apiClient } = await import('@/api/client')
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${res.data.token}`
    }
    return res
  }

  async function loadUser() {
    if (!token.value) return
    try {
      const res = await portalApi.me()
      if (res.success) {
        user.value = res.data ?? null
      }
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('portal_token')
  }

  // 初始化时设置 axios header
  if (token.value) {
    import('@/api/client').then(({ default: apiClient }) => {
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
    })
  }

  return { token, user, isLoggedIn, login, loadUser, logout }
})