<template>
  <div>
    <div class="welcome-card card">
      <div class="wc-avatar" v-if="auth.user?.avatar">
        <img :src="auth.user.avatar" alt="avatar" />
      </div>
      <div class="wc-info">
        <h3>你好，{{ auth.user?.display_name || auth.user?.username }} 👋</h3>
        <p class="muted">欢迎来到 Emby 门户</p>
      </div>
    </div>

    <div class="quick-stats">
      <div class="qs-card card">
        <div class="qs-value">{{ stats?.active_sessions ?? '-' }}</div>
        <div class="qs-label">活跃设备</div>
      </div>
    </div>

    <div v-if="stats?.now_playing?.length" class="section">
      <div class="section-title">正在播放</div>
      <div v-for="(item, i) in stats.now_playing" :key="i" class="card np-card">
        <div class="np-item">{{ item.item }}</div>
        <div class="np-device muted">{{ item.device }}</div>
      </div>
    </div>

    <div class="section">
      <div class="section-title">快捷操作</div>
      <div class="quick-actions">
        <RouterLink to="/portal/stats" class="qa-item card">
          <span class="qa-icon">📊</span>
          <span>观看统计</span>
        </RouterLink>
        <RouterLink to="/portal/profile" class="qa-item card">
          <span class="qa-icon">👤</span>
          <span>个人信息</span>
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { usePortalAuthStore } from '@/stores/portal-auth'
import { portalApi, type PortalStats } from '@/api/portal'

const auth = usePortalAuthStore()
const stats = ref<PortalStats | null>(null)

onMounted(async () => {
  const res = await portalApi.stats()
  stats.value = res.data ?? null
})
</script>

<style scoped>
.welcome-card { display: flex; align-items: center; gap: 16px; padding: 20px; margin-bottom: 16px; }
.wc-avatar img { width: 48px; height: 48px; border-radius: 50%; }
.wc-info h3 { margin: 0 0 4px; font-size: 18px; }
.muted { color: var(--text-muted); font-size: 13px; margin: 0; }
.quick-stats { display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 12px; margin-bottom: 16px; }
.qs-card { text-align: center; padding: 16px; }
.qs-value { font-size: 28px; font-weight: 700; color: var(--primary); }
.qs-label { font-size: 12px; color: var(--text-muted); margin-top: 4px; }
.section { margin-bottom: 16px; }
.section-title { font-size: 14px; font-weight: 600; margin-bottom: 8px; }
.np-card { padding: 12px; margin-bottom: 8px; }
.np-item { font-weight: 500; }
.np-device { font-size: 12px; margin-top: 4px; }
.quick-actions { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.qa-item { display: flex; align-items: center; gap: 10px; padding: 14px; text-decoration: none; color: var(--text); }
.qa-icon { font-size: 24px; }
</style>