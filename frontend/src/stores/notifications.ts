import { defineStore } from 'pinia'
import { ref } from 'vue'
import { notificationsApi } from '@/api/notifications'

export const useNotificationsStore = defineStore('notifications', () => {
 const unreadCount = ref(0)

 async function fetchUnreadCount() {
 try {
 const res = await notificationsApi.unreadCount()
 unreadCount.value = res.unread_count
 } catch {
 unreadCount.value = 0
 }
 }

 return { unreadCount, fetchUnreadCount }
})