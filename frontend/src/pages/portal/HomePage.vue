<template>
  <div class="portal-home">
    <!-- 用户头卡 -->
    <div class="hero-card card">
      <div class="hero-avatar">
        <img v-if="auth.user?.avatar" :src="auth.user.avatar" alt="avatar" />
        <div v-else class="avatar-placeholder">{{ (auth.user?.display_name || auth.user?.username || '?')[0] }}</div>
      </div>
      <div class="hero-info">
        <h3>{{ auth.user?.display_name || auth.user?.username }}</h3>
        <div class="hero-badges">
          <span v-if="auth.user?.is_vip" class="vip-badge">VIP</span>
          <span class="muted">限额 {{ auth.user?.max_concurrent ?? 2 }} 路</span>
        </div>
      </div>
    </div>

    <!-- 概览数据 -->
    <div class="stat-grid">
      <div class="stat-card card">
        <div class="sc-value">{{ stats?.overview?.total_plays ?? '-' }}</div>
        <div class="sc-label">总播放</div>
      </div>
      <div class="stat-card card">
        <div class="sc-value">{{ stats?.overview?.total_duration_hours ?? '-' }}<span class="sc-unit">h</span></div>
        <div class="sc-label">总时长</div>
      </div>
      <div class="stat-card card">
        <div class="sc-value">{{ stats?.overview?.active_sessions ?? '-' }}</div>
        <div class="sc-label">活跃设备</div>
      </div>
    </div>

    <!-- 成就徽章 -->
    <div v-if="badges.length" class="section">
      <div class="section-title">成就徽章</div>
      <div class="badge-grid">
        <div v-for="b in badges" :key="b.id" class="badge-item card" :class="b.bg">
          <div class="badge-icon">🏅</div>
          <div class="badge-name">{{ b.name }}</div>
          <div class="badge-desc">{{ b.desc }}</div>
        </div>
      </div>
    </div>

    <!-- 热门媒体 -->
    <div v-if="stats?.top_media?.length" class="section">
      <div class="section-title">热门内容</div>
      <div class="top-list">
        <div v-for="(m, i) in stats.top_media.slice(0, 5)" :key="i" class="top-item card">
          <div class="top-rank" :class="{ 'top-3': i < 3 }">{{ i + 1 }}</div>
          <img v-if="m.poster_url" :src="m.poster_url" class="top-poster" />
          <div class="top-info">
            <div class="top-name">{{ m.clean_name }}</div>
            <div class="top-meta">
              <span>{{ m.play_count }} 次播放</span>
              <span>{{ formatMin(m.total_duration) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 最近观看 -->
    <div v-if="stats?.recent?.length" class="section">
      <div class="section-title">最近观看</div>
      <div v-for="(r, i) in stats.recent.slice(0, 8)" :key="i" class="recent-item card">
        <div class="ri-info">
          <div class="ri-name">{{ r.clean_name }}</div>
          <div class="ri-meta muted">{{ r.device }} · {{ formatMin(r.play_duration) }} · {{ timeAgo(r.date_created) }}</div>
        </div>
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
import { portalApi, type PortalStats, type PortalBadge } from '@/api/portal'

const auth = usePortalAuthStore()
const stats = ref<PortalStats | null>(null)
const badges = ref<PortalBadge[]>([])

function formatMin(seconds: number) {
  if (!seconds) return '0分钟'
  const m = Math.round(seconds / 60)
  if (m < 60) return `${m}分钟`
  return `${Math.floor(m / 60)}小时${m % 60 ? m % 60 + '分' : ''}`
}

function timeAgo(dateStr: string) {
  if (!dateStr) return ''
  const d = new Date(dateStr.replace(' ', 'T'))
  const diff = Date.now() - d.getTime()
  const min = Math.floor(diff / 60000)
  if (min < 60) return `${min}分钟前`
  const h = Math.floor(min / 60)
  if (h < 24) return `${h}小时前`
  return `${Math.floor(h / 24)}天前`
}

onMounted(async () => {
  const [statsRes, badgesRes] = await Promise.all([
    portalApi.stats(),
    portalApi.badges(),
  ])
  stats.value = statsRes.data ?? null
  badges.value = badgesRes.data ?? []
})
</script>

<style scoped>
.portal-home { display: flex; flex-direction: column; gap: 16px; }
.hero-card { display: flex; align-items: center; gap: 16px; padding: 20px; }
.hero-avatar img, .avatar-placeholder { width: 56px; height: 56px; border-radius: 50%; }
.avatar-placeholder { background: var(--brand); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: 700; }
.hero-info h3 { margin: 0 0 4px; font-size: 18px; }
.hero-badges { display: flex; align-items: center; gap: 8px; font-size: 13px; }
.vip-badge { background: linear-gradient(135deg, #f59e0b, #ef4444); color: #fff; padding: 1px 8px; border-radius: 10px; font-size: 11px; font-weight: 700; }
.stat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.stat-card { text-align: center; padding: 16px 8px; }
.sc-value { font-size: 24px; font-weight: 800; color: var(--brand); }
.sc-unit { font-size: 14px; font-weight: 400; margin-left: 1px; }
.sc-label { font-size: 12px; color: var(--text-muted); margin-top: 4px; }
.section { margin-top: 4px; }
.section-title { font-size: 14px; font-weight: 600; margin-bottom: 8px; }
.badge-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 8px; }
.badge-item { text-align: center; padding: 12px 8px; }
.badge-icon { font-size: 20px; margin-bottom: 4px; }
.badge-name { font-size: 13px; font-weight: 600; }
.badge-desc { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
.top-list { display: flex; flex-direction: column; gap: 8px; }
.top-item { display: flex; align-items: center; gap: 10px; padding: 10px; }
.top-rank { width: 24px; height: 24px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; background: var(--bg-secondary); flex-shrink: 0; }
.top-rank.top-3 { background: var(--brand); color: #fff; }
.top-poster { width: 36px; height: 50px; border-radius: 4px; object-fit: cover; flex-shrink: 0; }
.top-info { flex: 1; min-width: 0; }
.top-name { font-size: 14px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.top-meta { font-size: 12px; color: var(--text-muted); margin-top: 2px; display: flex; gap: 10px; }
.recent-item { padding: 10px 12px; }
.ri-name { font-size: 14px; font-weight: 500; }
.ri-meta { font-size: 12px; margin-top: 2px; }
.muted { color: var(--text-muted); }
.quick-actions { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.qa-item { display: flex; align-items: center; gap: 10px; padding: 14px; text-decoration: none; color: var(--text); }
.qa-icon { font-size: 24px; }
</style>
