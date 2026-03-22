<template>
  <div style="min-height:100vh;display:flex;flex-direction:column;background:var(--bg)">
    <!-- 顶栏 -->
    <header class="portal-header">
      <router-link to="/portal" class="ph-logo">
        <IosIcon name="film" :size="20" color="var(--brand)" />
        <span>门户</span>
      </router-link>
      <div class="ph-right">
        <span class="ph-user">{{ auth.user?.display_name || auth.user?.username }}</span>
        <n-button quaternary size="tiny" @click="handleLogout">退出</n-button>
      </div>
    </header>

    <main class="portal-main">
      <router-view />
    </main>

    <!-- 底部 Tab -->
    <nav class="portal-tab-bar">
      <router-link v-for="tab in tabs" :key="tab.to" :to="tab.to" class="tab-item" :class="{ active: route.path === tab.to }">
        <IosIcon :name="tab.icon" :size="24" :color="route.path === tab.to ? 'var(--brand)' : 'var(--text-muted)'" />
        <span class="tab-label">{{ tab.label }}</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NButton } from 'naive-ui'
import IosIcon from '@/components/common/IosIcon.vue'
import { usePortalAuthStore } from '@/stores/portal-auth'

const route = useRoute()
const router = useRouter()
const auth = usePortalAuthStore()

const tabs = [
  { to: '/portal', icon: 'home', label: '首页' },
  { to: '/portal/stats', icon: 'chart', label: '统计' },
  { to: '/portal/profile', icon: 'users', label: '我的' },
]

function handleLogout() { auth.logout(); router.push('/portal/login') }
onMounted(() => { if (!auth.isLoggedIn) router.push('/portal/login'); else auth.loadUser() })
</script>

<style scoped>
.portal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px; padding-top: calc(var(--safe-top) + 12px);
  background: var(--surface-strong); backdrop-filter: blur(var(--blur-heavy)); -webkit-backdrop-filter: blur(var(--blur-heavy));
  border-bottom: 0.5px solid var(--separator);
  position: sticky; top: 0; z-index: 100;
}
.ph-logo { display: flex; align-items: center; gap: 6px; text-decoration: none; font-weight: 700; font-size: 16px; color: var(--text); }
.ph-right { display: flex; align-items: center; gap: 8px; }
.ph-user { font-size: 13px; color: var(--text-muted); }
.portal-main { flex: 1; padding: 12px 16px; padding-bottom: calc(var(--tab-height) + 12px); max-width: 640px; width: 100%; margin: 0 auto; }
.portal-tab-bar {
  display: flex;
  background: var(--surface-strong); backdrop-filter: blur(var(--blur-heavy)); -webkit-backdrop-filter: blur(var(--blur-heavy));
  border-top: 0.5px solid var(--separator);
  padding-bottom: var(--safe-bottom);
  position: fixed; bottom: 0; left: 0; right: 0; z-index: 100;
}
.tab-item { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 2px; padding: 6px 0 2px; text-decoration: none; }
.tab-label { font-size: 10px; font-weight: 600; color: var(--text-muted); }
.tab-item.active .tab-label { color: var(--brand); }
</style>
