<template>
  <div class="portal-home">
    <n-card size="small">
      <div style="display:flex;align-items:center;gap:16px">
        <n-avatar :size="56" round>
          <template v-if="auth.user?.avatar"><img :src="auth.user.avatar" /></template>
          <template v-else>{{ (auth.user?.display_name || auth.user?.username || '?')[0] }}</template>
        </n-avatar>
        <div>
          <div style="font-size:18px;font-weight:700">{{ auth.user?.display_name || auth.user?.username }}</div>
          <div style="display:flex;align-items:center;gap:8px;margin-top:4px">
            <n-tag v-if="auth.user?.is_vip" type="warning" size="tiny">VIP</n-tag>
            <span style="font-size:13px;color:var(--text-muted)">限额 {{ auth.user?.max_concurrent ?? 2 }} 路</span>
          </div>
        </div>
      </div>
    </n-card>

    <div class="stat-grid">
      <StatCard label="总播放" :value="stats?.overview?.total_plays ?? '-'" highlight />
      <StatCard label="总时长" :value="(stats?.overview?.total_duration_hours ?? '-') + 'h'" />
      <StatCard label="活跃设备" :value="stats?.overview?.active_sessions ?? '-'" />
    </div>

    <template v-if="badges.length">
      <div style="font-size:14px;font-weight:600;margin-top:4px">成就徽章</div>
      <div class="badge-grid">
        <n-card v-for="b in badges" :key="b.id" size="small" style="text-align:center">
          <div style="font-size:20px">🏅</div>
          <div style="font-size:13px;font-weight:600">{{ b.name }}</div>
          <div style="font-size:11px;color:var(--text-muted)">{{ b.desc }}</div>
        </n-card>
      </div>
    </template>

    <template v-if="stats?.top_media?.length">
      <div style="font-size:14px;font-weight:600">热门内容</div>
      <n-card v-for="(m, i) in stats.top_media.slice(0, 5)" :key="i" size="small" style="margin-bottom:8px">
        <div style="display:flex;align-items:center;gap:10px">
          <n-tag :type="i < 3 ? 'info' : 'default'" size="tiny" round>{{ i + 1 }}</n-tag>
          <img v-if="m.poster_url" :src="m.poster_url" style="width:36px;height:50px;border-radius:4px;object-fit:cover" />
          <div style="flex:1;min-width:0">
            <div style="font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ m.clean_name }}</div>
            <div style="font-size:12px;color:var(--text-muted)">{{ m.play_count }} 次 · {{ formatMin(m.total_duration) }}</div>
          </div>
        </div>
      </n-card>
    </template>

    <template v-if="stats?.recent?.length">
      <div style="font-size:14px;font-weight:600">最近观看</div>
      <n-card v-for="(r, i) in stats.recent.slice(0, 8)" :key="i" size="small" style="margin-bottom:4px">
        <div style="font-weight:500">{{ r.clean_name }}</div>
        <div style="font-size:12px;color:var(--text-muted)">{{ r.device }} · {{ formatMin(r.play_duration) }} · {{ timeAgo(r.date_created) }}</div>
      </n-card>
    </template>

    <div style="font-size:14px;font-weight:600">快捷操作</div>
    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px">
      <router-link to="/portal/stats" style="text-decoration:none">
        <n-card size="small" hoverable style="text-align:center;cursor:pointer">
          <div style="font-size:24px">📊</div>
          <div>观看统计</div>
        </n-card>
      </router-link>
      <router-link to="/portal/profile" style="text-decoration:none">
        <n-card size="small" hoverable style="text-align:center;cursor:pointer">
          <div style="font-size:24px">👤</div>
          <div>个人信息</div>
        </n-card>
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NCard, NAvatar, NTag } from 'naive-ui'
import StatCard from '@/components/common/StatCard.vue'
import { usePortalAuthStore } from '@/stores/portal-auth'
import { portalApi, type PortalStats, type PortalBadge } from '@/api/portal'

const auth = usePortalAuthStore()
const stats = ref<PortalStats | null>(null)
const badges = ref<PortalBadge[]>([])

function formatMin(seconds: number) { if (!seconds) return '0分钟'; const m = Math.round(seconds / 60); if (m < 60) return `${m}分钟`; return `${Math.floor(m / 60)}小时${m % 60 ? m % 60 + '分' : ''}` }
function timeAgo(dateStr: string) { if (!dateStr) return ''; const d = new Date(dateStr.replace(' ', 'T')); const diff = Date.now() - d.getTime(); const min = Math.floor(diff / 60000); if (min < 60) return `${min}分钟前`; const h = Math.floor(min / 60); if (h < 24) return `${h}小时前`; return `${Math.floor(h / 24)}天前` }

onMounted(async () => { const [s, b] = await Promise.all([portalApi.stats(), portalApi.badges()]); stats.value = s.data ?? null; badges.value = b.data ?? [] })
</script>

<style scoped>
.portal-home { display: flex; flex-direction: column; gap: 16px; }
.stat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.badge-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 8px; }
</style>
