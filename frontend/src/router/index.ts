import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
 history: createWebHistory(),
 routes: [
 {
 path: '/login',
 name: 'login',
 component: () => import('@/pages/LoginPage.vue'),
 meta: { layout: 'auth', public: true },
 },
 {
 path: '/',
 redirect: '/dashboard',
 },
 {
 path: '/dashboard',
 name: 'dashboard',
 component: () => import('@/pages/DashboardPage.vue'),
 meta: { title: '仪表盘' },
 },
 {
 path: '/users',
 name: 'users',
 component: () => import('@/pages/UsersPage.vue'),
 meta: { title: '用户管理' },
 },
 {
 path: '/users/:id',
 name: 'user-detail',
 component: () => import('@/pages/UserDetailPage.vue'),
 meta: { title: '用户详情' },
 },
 {
 path: '/stats',
 name: 'stats',
 component: () => import('@/pages/StatsPage.vue'),
 meta: { title: '播放统计' },
 },
 {
 path: '/risk',
 name: 'risk',
 component: () => import('@/pages/RiskPage.vue'),
 meta: { title: '风控' },
 },
 {
 path: '/notifications',
 name: 'notifications',
 component: () => import('@/pages/NotificationsPage.vue'),
 meta: { title: '通知中心' },
 },
 {
 path: '/settings',
 name: 'settings',
 component: () => import('@/pages/SettingsPage.vue'),
 meta: { title: '系统设置' },
 },
 ],
})

router.beforeEach(async (to) => {
 const auth = useAuthStore()
 if (to.meta.public) return true
 if (!auth.isLoggedIn) return { name: 'login' }
 if (!auth.user) {
 await auth.fetchMe().catch(() => auth.logout())
 }
 return true
})

export default router