import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      component: () => import('@/layouts/AuthLayout.vue'),
      children: [
        { path: '', component: () => import('@/pages/LoginPage.vue') },
      ],
    },
    {
      path: '/',
      component: () => import('@/layouts/DefaultLayout.vue'),
      redirect: '/dashboard',
      children: [
        { path: 'dashboard', name: 'Dashboard', component: () => import('@/pages/DashboardPage.vue'), meta: { title: '仪表盘', icon: 'dashboard' } },
        { path: 'users', name: 'Users', component: () => import('@/pages/UsersPage.vue'), meta: { title: '用户', icon: 'users' } },
        { path: 'users/:id', name: 'UserDetail', component: () => import('@/pages/UserDetailPage.vue'), meta: { title: '用户详情' } },
        { path: 'users/invites', name: 'Invites', component: () => import('@/pages/InvitesPage.vue'), meta: { title: '邀请管理' } },
        { path: 'users/invites/create', name: 'CreateInvite', component: () => import('@/pages/CreateInvitePage.vue'), meta: { title: '创建邀请' } },
        { path: 'users/templates', name: 'Templates', component: () => import('@/pages/TemplatesPage.vue'), meta: { title: '权限模板' } },
        { path: 'stats', name: 'Stats', component: () => import('@/pages/StatsPage.vue'), meta: { title: '统计', icon: 'stats' } },
        { path: 'risk', name: 'Risk', component: () => import('@/pages/RiskPage.vue'), meta: { title: '风控', icon: 'risk' } },
        { path: 'notifications', name: 'Notifications', component: () => import('@/pages/NotificationsPage.vue'), meta: { title: '通知' } },
        { path: 'settings', name: 'Settings', component: () => import('@/pages/SettingsPage.vue'), meta: { title: '设置' } },
      ],
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router
