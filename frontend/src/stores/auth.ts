import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import type { MeResponse } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
 const token = ref<string | null>(localStorage.getItem('access_token'))
 const user = ref<MeResponse | null>(null)

 const isLoggedIn = computed(() => !!token.value)
 const isAdmin = computed(() => user.value?.role === 'admin')

 async function login(username: string, password: string) {
 const res = await authApi.login({ username, password })
 token.value = res.access_token
 localStorage.setItem('access_token', res.access_token)
 await fetchMe()
 }

 async function fetchMe() {
 try {
 user.value = await authApi.me()
 } catch {
 user.value = null
 }
 }

 async function logout() {
 await authApi.logout().catch(() => {})
 token.value = null
 user.value = null
 localStorage.removeItem('access_token')
 }

 return { token, user, isLoggedIn, isAdmin, login, fetchMe, logout }
})