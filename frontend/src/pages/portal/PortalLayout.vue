<template>
  <div style="min-height:100vh;display:flex;flex-direction:column;background:var(--bg-secondary)">
    <header style="display:flex;align-items:center;justify-content:space-between;padding:12px 16px;background:var(--bg);border-bottom:1px solid var(--border);position:sticky;top:0;z-index:100">
      <router-link to="/portal" style="text-decoration:none;font-weight:700;font-size:16px;color:var(--text)">🎬 门户</router-link>
      <div style="display:flex;align-items:center;gap:8px">
        <span style="font-size:13px;color:var(--text-muted)">{{ auth.user?.display_name || auth.user?.username }}</span>
        <n-button quaternary size="tiny" @click="handleLogout">退出</n-button>
      </div>
    </header>

    <main style="flex:1;padding:16px;max-width:640px;width:100%;margin:0 auto">
      <router-view />
    </main>

    <nav style="display:flex;background:var(--bg);border-top:1px solid var(--border);position:sticky;bottom:0">
      <router-link v-for="tab in tabs" :key="tab.to" :to="tab.to" class="tab-item" :class="{ active: route.path === tab.to }">
        <span style="font-size:20px">{{ tab.icon }}</span>
        <span style="font-size:11px">{{ tab.label }}</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NButton } from 'naive-ui'
import { usePortalAuthStore } from '@/stores/portal-auth'

const route = useRoute()
const router = useRouter()
const auth = usePortalAuthStore()

const tabs = [
  { to: '/portal', icon: '🏠', label: '首页' },
  { to: '/portal/stats', icon: '📊', label: '统计' },
  { to: '/portal/profile', icon: '👤', label: '我的' },
]

function handleLogout() { auth.logout(); router.push('/portal/login') }
onMounted(() => { if (!auth.isLoggedIn) router.push('/portal/login'); else auth.loadUser() })
</script>

<style scoped>
.tab-item { flex: 1; display: flex; flex-direction: column; align-items: center; padding: 8px 0; text-decoration: none; color: var(--text-muted); transition: color 0.2s; }
.tab-item.active { color: var(--brand); }
</style>
