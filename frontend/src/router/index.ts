import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/pages/LoginPage.vue'),
      meta: { title: '登录', public: true },
    },
    {
      path: '/',
      redirect: '/stats',
    },
    {
      path: '/stats',
      name: 'Stats',
      component: () => import('@/pages/StatsOverviewPage.vue'),
      meta: { title: '分析总览' },
    },
    {
      path: '/stats/content',
      name: 'StatsContent',
      component: () => import('@/pages/StatsContentPage.vue'),
      meta: { title: '内容分析' },
    },
    {
      path: '/stats/users',
      name: 'StatsUsers',
      component: () => import('@/pages/StatsUsersPage.vue'),
      meta: { title: '用户分析' },
    },
    {
      path: '/users',
      name: 'Users',
      component: () => import('@/pages/UsersPage.vue'),
      meta: { title: '用户管理' },
    },
    {
      path: '/users/:id',
      name: 'UserDetail',
      component: () => import('@/pages/UserDetailPage.vue'),
      meta: { title: '用户详情' },
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/stats',
    },
  ],
})

// 路由守卫
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  const isPublic = to.meta.public

  if (!token && !isPublic) {
    return next({ name: 'Login' })
  }
  if (token && to.name === 'Login') {
    return next({ name: 'Stats' })
  }
  next()
})

export default router
