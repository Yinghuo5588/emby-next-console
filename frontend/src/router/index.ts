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
    // Portal 路由
    {
      path: '/portal/login',
      name: 'PortalLogin',
      component: () => import('@/pages/portal/LoginPage.vue'),
      meta: { title: '门户登录' },
    },
    {
      path: '/portal',
      component: () => import('@/pages/portal/PortalLayout.vue'),
      children: [
        { path: '', name: 'PortalHome', component: () => import('@/pages/portal/HomePage.vue'), meta: { title: '门户首页' } },
        { path: 'stats', name: 'PortalStats', component: () => import('@/pages/portal/StatsPage.vue'), meta: { title: '观看统计' } },
        { path: 'profile', name: 'PortalProfile', component: () => import('@/pages/portal/ProfilePage.vue'), meta: { title: '个人信息' } },
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
        { path: 'stats', name: 'Stats', component: () => import('@/pages/StatsPage.vue'), meta: { title: '数据分析', icon: 'stats' } },
        { path: 'media', name: 'Media', component: () => import('@/pages/MediaPage.vue'), meta: { title: '媒体管理', icon: 'media' } },
        { path: 'calendar', name: 'Calendar', component: () => import('@/pages/CalendarPage.vue'), meta: { title: '追剧日历' } },
        { path: 'risk', name: 'Risk', component: () => import('@/pages/RiskPage.vue'), meta: { title: '风控', icon: 'risk' } },
        { path: 'notifications', name: 'Notifications', component: () => import('@/pages/NotificationsPage.vue'), meta: { title: '通知' } },
        { path: 'settings', name: 'Settings', component: () => import('@/pages/SettingsPage.vue'), meta: { title: '设置' } },
        { path: 'tasks', name: 'Tasks', component: () => import('@/pages/TasksPage.vue'), meta: { title: '任务中心' } },
        { path: 'poster', name: 'Poster', component: () => import('@/pages/PosterPage.vue'), meta: { title: '海报工坊' } },
      ],
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  const portalToken = localStorage.getItem('portal_token')
  
  // 管理员路由检查
  if (to.path.startsWith('/') && to.path !== '/login' && !token) {
    next('/login')
  } 
  // Portal 路由检查
  else if (to.path.startsWith('/portal') && to.path !== '/portal/login' && !portalToken) {
    next('/portal/login')
  }
  else {
    next()
  }
})

export default router
