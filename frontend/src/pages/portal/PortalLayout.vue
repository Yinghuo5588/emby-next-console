<template>
  <div class="portal-layout">
    <header class="portal-header">
      <div class="ph-left">
        <RouterLink to="/portal" class="ph-logo">🎬 门户</RouterLink>
      </div>
      <div class="ph-right">
        <span class="ph-user">{{ auth.user?.display_name || auth.user?.username }}</span>
        <button class="btn btn-ghost btn-sm" @click="handleLogout">退出</button>
      </div>
    </header>

    <main class="portal-main">
      <RouterView />
    </main>

    <nav class="portal-tab-bar">
      <RouterLink to="/portal" class="tab-item" :class="{ active: route.path === '/portal' }">
        <span class="tab-icon">🏠</span>
        <span class="tab-label">首页</span>
      </RouterLink>
      <RouterLink to="/portal/stats" class="tab-item" :class="{ active: route.path === '/portal/stats' }">
        <span class="tab-icon">📊</span>
        <span class="tab-label">统计</span>
      </RouterLink>
      <RouterLink to="/portal/profile" class="tab-item" :class="{ active: route.path === '/portal/profile' }">
        <span class="tab-icon">👤</span>
        <span class="tab-label">我的</span>
      </RouterLink>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePortalAuthStore } from '@/stores/portal-auth'

const route = useRoute()
const router = useRouter()
const auth = usePortalAuthStore()

function handleLogout() {
  auth.logout()
  router.push('/portal/login')
}

onMounted(() => {
  if (!auth.isLoggedIn) {
    router.push('/portal/login')
  } else {
    auth.loadUser()
  }
})
</script>

<style scoped>
.portal-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
}
.portal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--bg);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 100;
}
.ph-logo { text-decoration: none; font-weight: 700; font-size: 16px; color: var(--text); }
.ph-right { display: flex; align-items: center; gap: 8px; }
.ph-user { font-size: 13px; color: var(--text-muted); }
.portal-main { flex: 1; padding: 16px; max-width: 640px; width: 100%; margin: 0 auto; }
.portal-tab-bar {
  display: flex;
  background: var(--bg);
  border-top: 1px solid var(--border);
  position: sticky;
  bottom: 0;
}
.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 0;
  text-decoration: none;
  color: var(--text-muted);
  font-size: 11px;
  transition: color 0.2s;
}
.tab-item.active { color: var(--primary); }
.tab-icon { font-size: 20px; margin-bottom: 2px; }
.tab-label { font-size: 11px; }
.btn-sm { padding: 3px 10px; font-size: 12px; }
</style>