import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiClient from '@/api/client'

interface LoginResult {
  access_token: string
  user_id: string
  username: string
  avatar_url: string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const username = ref(localStorage.getItem('username') || '')
  const avatarUrl = ref(localStorage.getItem('avatarUrl') || '')

  const isLoggedIn = computed(() => !!token.value)

  async function login(usernameInput: string, password: string) {
    const { data } = await apiClient.post<LoginResult>('/auth/login', {
      username: usernameInput,
      password,
    })
    token.value = data.access_token
    username.value = data.username
    avatarUrl.value = data.avatar_url
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('username', data.username)
    if (data.avatar_url) localStorage.setItem('avatarUrl', data.avatar_url)
  }

  function logout() {
    token.value = null
    username.value = ''
    avatarUrl.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('avatarUrl')
    window.location.href = '/login'
  }

  // 验证 token 有效性
  async function checkAuth() {
    if (!token.value) return false
    try {
      await apiClient.get('/auth/me')
      return true
    } catch {
      logout()
      return false
    }
  }

  return { token, username, avatarUrl, isLoggedIn, login, logout, checkAuth }
})
