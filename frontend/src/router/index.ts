import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
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
      path: '/:pathMatch(.*)*',
      redirect: '/stats',
    },
  ],
})

router.beforeEach((to, _from, next) => {
  // 直接放行所有路由（暂无登录）
  next()
})

export default router
