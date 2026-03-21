import { defineStore } from 'pinia'
import { ref } from 'vue'
import { notificationsApi } from '@/api/notifications'

export const useNotificationsStore = defineStore('notifications', () => {
  // State
  const unreadCount = ref(0)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Actions
  const fetchUnreadCount = async () => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await notificationsApi.unreadCount()
      
      if (response.success) {
        unreadCount.value = response.data.count
        return { success: true, count: response.data.count }
      } else {
        error.value = response.message
        return { success: false, message: response.message }
      }
    } catch (err: any) {
      error.value = err.response?.data?.message || 'Failed to fetch unread count'
      return { success: false, message: error.value }
    } finally {
      isLoading.value = false
    }
  }

  const decrementCount = (amount: number = 1) => {
    unreadCount.value = Math.max(0, unreadCount.value - amount)
  }

  const incrementCount = (amount: number = 1) => {
    unreadCount.value += amount
  }

  const resetCount = () => {
    unreadCount.value = 0
  }

  return {
    // State
    unreadCount,
    isLoading,
    error,
    
    // Actions
    fetchUnreadCount,
    decrementCount,
    incrementCount,
    resetCount,
  }
})