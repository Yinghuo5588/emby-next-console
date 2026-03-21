import { defineStore } from 'pinia'
import { ref } from 'vue'
import { dashboardApi, type DashboardSummary, type ActiveSession, type DashboardTrendPoint } from '@/api/dashboard'

export const useDashboardStore = defineStore('dashboard', () => {
 const summary = ref<DashboardSummary | null>(null)
 const sessions = ref<ActiveSession[]>([])
 const trends = ref<DashboardTrendPoint[]>([])

 const summaryLoading = ref(false)
 const sessionsLoading = ref(false)
 const trendsLoading = ref(false)

 const summaryError = ref<string | null>(null)
 const sessionsError = ref<string | null>(null)

 async function fetchSummary() {
 summaryLoading.value = true
 summaryError.value = null
 try {
 summary.value = await dashboardApi.summary()
 } catch {
 summaryError.value = '获取概览数据失败'
 } finally {
 summaryLoading.value = false
 }
 }

 async function fetchSessions() {
 sessionsLoading.value = true
 sessionsError.value = null
 try {
 sessions.value = await dashboardApi.activeSessions()
 } catch {
 sessionsError.value = '获取会话数据失败'
 } finally {
 sessionsLoading.value = false
 }
 }

 async function fetchTrends(days = 7) {
 trendsLoading.value = true
 try {
 trends.value = await dashboardApi.trends(days)
 } finally {
 trendsLoading.value = false
 }
 }

 async function fetchAll(days = 7) {
 await Promise.all([fetchSummary(), fetchSessions(), fetchTrends(days)])
 }

 return {
 summary, sessions, trends,
 summaryLoading, sessionsLoading, trendsLoading,
 summaryError, sessionsError,
 fetchSummary, fetchSessions, fetchTrends, fetchAll,
 }
})