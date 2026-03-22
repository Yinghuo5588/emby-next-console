<template>
  <div class="portal-home">
    <!-- 用户卡片 -->
    <n-card size="small" class="user-card">
      <div class="user-info">
        <n-avatar :size="52" round>
          <template v-if="auth.user?.avatar"><img :src="auth.user.avatar" /></template>
          <template v-else>{{ (auth.user?.display_name || auth.user?.username || '?')[0] }}</template>
        </n-avatar>
        <div>
          <div class="user-name">{{ auth.user?.display_name || auth.user?.username }}</div>
          <div class="user-meta">
            <n-tag v-if="auth.user?.is_vip" type="warning" size="tiny">VIP</n-tag>
            <span class="user-limit">限额 {{ auth.user?.max_concurrent ?? 2 }} 路</span>
          </div>
        </div>
      </div>
    </n-card>

    <!-- 概览卡片 -->
    <div class="stat-grid">
      <StatCard label="总播放" :value="stats?.overview?.total_plays ?? '-'" highlight />
      <StatCard label="总时长" :value="(stats?.overview?.total_duration_hours ?? '-') + 'h'" />
      <StatCard label="活跃设备" :value="stats?.overview?.active_sessions ?? '-'" />
    </div>

    <!-- 成就徽章 -->
    <template v-if="badges.length">
      <div class="section-label">成就徽章</div>
      <div class="badge-grid">
        <n-card v-for="b in badges" :key="b.id" size="small" class="badge-card">
          <div style="font-size: 20px; margin-bottom: 4px">🏅</div>
          <div class="badge-name">{{ b.name }}</div>
          <div class="badge-desc">{{ b.desc }}</div>
        </n-card>
      </div>
    </template>

    <!-- 热门内容 -->
    <template v-if="stats?.top_media?.length">
      <n-card size="small">
        <template #header><CardTitle icon="fire" title="热门内容" icon-color="#FF3B30" /></template>
        <div v-for="(m, i) in stats.top_media.slice(0, 5)" :key="i" class="hot-row">
          <n-tag :type="i < 3 ? 'info' : 'default'" size="tiny" round style="min-width: 24px; justify-content: center;">{{ i + 1 }}</n-tag>
          <img v-if="m.poster_url" :src="m.poster_url" class="hot-poster" />
          <div class="hot-info">
            <div class="hot-name">{{ m.clean_name }}</div>
            <div class="hot-meta">{{ m.play_count }} 次 · {{ formatMin(m.total_duration) }}</div>
          </div>
        </div>
      </n-card>
    </template>

    <!-- 最近观看 -->
    <template v-if="stats?.recent?.length">
      <n-card size="small" style="margin-top: 12px">
        <template #header><CardTitle icon="clock" title="最近观看" /></template>
        <div v-for="(r, i) in stats.recent.slice(0, 6)" :key="i" class="recent-row">
          <div class="recent-name">{{ r.clean_name }}</div>
          <div class="recent-meta">{{ r.device }} · {{ formatMin(r.play_duration) }} · {{ timeAgo(r.date_created) }}</div>
        </div>
      </n-card>
    </template>

    <!-- 快捷操作 -->
    <div class="section-label">快捷操作</div>
    <div class="action-grid">
      <router-link v-for="action in quickActions" :key="action.to" :to="action.to" class="action-item">
        <n-card size="small" hoverable class="action-card">
          <IosIcon :name="action.icon" :size="24" color="var(--brand)" />
          <div class="action-label">{{ action.label }}</div>
        </n-card>
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NCard, NAvatar, NTag } from 'naive-ui'
import CardTitle from '@/components/common/CardTitle.vue'
import IosIcon from '@/components/common/IosIcon.vue'
import StatCard from '@/components/common/StatCard.vue'
import { usePortalAuthStore } from '@/stores/portal-auth'
import { portalApi, type PortalStats, type PortalBadge } from '@/api/portal'

const auth = usePortalAuthStore()
const stats = ref<PortalStats | null>(null)
const badges = ref<PortalBadge[]>([])

const quickActions = [
  { icon: 'chart', label: '观看统计', to: '/portal/stats' },
  { icon: 'users', label: '个人信息', to: '/portal/profile' },
]

function formatMin(seconds: number) { if (!seconds) return '0分钟'; const m = Math.round(seconds / 60); if (m < 60) return `${m}分钟`; return `${Math.floor(m / 60)}小时${m % 60 ? m % 60 + '分' : ''}` }
function timeAgo(dateStr: string) { if (!dateStr) return ''; const d = new Date(dateStr.replace(' ', 'T')); const diff = Date.now() - d.getTime(); const min = Math.floor(diff / 60000); if (min < 60) return `${min}分钟前`; const h = Math.floor(min / 60); if (h < 24) return `${h}小时前`; return `${Math.floor(h / 24)}天前` }

onMounted(async () => { const [s, b] = await Promise.all([portalApi.stats(), portalApi.badges()]); stats.value = s.data ?? null; badges.value = b.data ?? [] })
</script>

<style scoped>
.portal-home { display: flex; flex-direction: column; gap: 12px; }
.user-card { border-radius: var(--radius-lg); }
.user-info { display: flex; align-items: center; gap: 14px; }
.user-name { font-size: 17px; font-weight: 700; }
.user-meta { display: flex; align-items: center; gap: 8px; margin-top: 4px; }
.user-limit { font-size: 13px; color: var(--text-muted); }
.stat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.section-label { font-size: 13px; font-weight: 500; color: var(--text-muted); letter-spacing: 0.02em; }
.badge-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 8px; }
.badge-card { text-align: center; border-radius: var(--radius); }
.badge-name { font-size: 13px; font-weight: 600; }
.badge-desc { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
.hot-row { display: flex; align-items: center; gap: 10px; padding: 6px 0; border-bottom: 0.5px solid var(--separator); }
.hot-row:last-child { border-bottom: none; }
.hot-poster { width: 32px; height: 44px; border-radius: 6px; object-fit: cover; flex-shrink: 0; }
.hot-info { flex: 1; min-width: 0; }
.hot-name { font-weight: 500; font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.hot-meta { font-size: 12px; color: var(--text-muted); }
.recent-row { padding: 6px 0; border-bottom: 0.5px solid var(--separator); }
.recent-row:last-child { border-bottom: none; }
.recent-name { font-weight: 500; font-size: 14px; }
.recent-meta { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
.action-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
.action-item { text-decoration: none; }
.action-card { text-align: center; cursor: pointer; border-radius: var(--radius); display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 16px !important; }
.action-label { font-size: 13px; color: var(--text); }
</style>
