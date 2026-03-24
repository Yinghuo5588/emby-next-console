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
      path: '/:pathMatch(.*)*',
      redirect: '/stats',
    },
  ],
})

export default router
