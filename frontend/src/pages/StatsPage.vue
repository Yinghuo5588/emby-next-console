<template>
  <div>
    <PageHeader title="统计分析" desc="播放数据概览与趋势">
      <template #actions>
        <div class="day-tabs">
          <button v-for="d in [7, 30, 90]" :key="d" class="tab" :class="{ active: days === d }" @click="days = d; loadAll()">{{ d }}天</button>
        </div>
      </template>
    </PageHeader>

    <section class="stat-grid">
      <StatCard label="总播放次数" :value="overview?.total_play_count ?? 0" />
      <StatCard label="总播放时长" :value="formatDuration(overview?.total_play_duration_sec ?? 0)" />
      <StatCard label="活跃用户" :value="overview?.active_users ?? 0" />
      <StatCard label="覆盖媒体" :value="overview?.media_count ?? 0" />
    </section>

    <div class="card" style="margin-bottom: 16px;">
      <div class="card-head"><span class="card-title">趋势</span></div>
      <LoadingState v-if="trendsLoading" height="220px" />
      <TrendChart v-else-if="trends.length > 0" :x-data="trends.map((t: any) => t.date?.slice(5) ?? '')" :series="[{ name: '播放', data: trends.map((t: any) => t.play_count ?? 0) }, { name: '活跃用户', data: trends.map((t: any) => t.active_users ?? 0), color: '#34c759' }]" height="240px" />
    </div>

    <div class="rank-grid">
      <div class="card">
        <div class="card-head"><span class="card-title">活跃用户 Top</span></div>
        <LoadingState v-if="topUsersLoading" height="120px" />
        <ol v-else class="rank-list">
          <li v-for="(u, i) in topUsers" :key="i" class="rank-item">
            <span class="rank-num" :class="{ 'rank-top': i < 3 }">{{ i + 1 }}</span>
            <RouterLink v-if="u.user_id" :to="`/users/${u.user_id}`" class="rank-name">{{ u.username || u.user_id }}</RouterLink>
            <span v-else class="rank-name">{{ u.username }}</span>
            <span class="rank-val">{{ u.play_count }}</span>
            <div class="rank-bar"><div class="rank-fill" :style="{ width: barWidth(u.play_count, topUsers[0]?.play_count) }" /></div>
          </li>
        </ol>
      </div>
      <div class="card">
        <div class="card-head"><span class="card-title">热门媒体 Top</span></div>
        <LoadingState v-if="topMediaLoading" height="120px" />
        <ol v-else class="rank-list">
          <li v-for="(m, i) in topMedia" :key="i" class="rank-item">
            <span class="rank-num" :class="{ 'rank-top': i < 3 }">{{ i + 1 }}</span>
            <span class="rank-name">{{ m.media_name }}</span>
            <span class="rank-val">{{ m.play_count }}</span>
            <div class="rank-bar"><div class="rank-fill" :style="{ width: barWidth(m.play_count, topMedia[0]?.play_count) }" /></div>
          </li>
        </ol>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import TrendChart from '@/components/charts/TrendChart.vue'
import { statsApi } from '@/api/stats'

const days = ref(7)
const overview = ref<any>(null)
const trends = ref<any[]>([])
const topUsers = ref<any[]>([])
const topMedia = ref<any[]>([])
const trendsLoading = ref(false)
const topUsersLoading = ref(false)
const topMediaLoading = ref(false)

function formatDuration(sec: number) { if (sec < 60) return `${sec}s`; const h = Math.floor(sec / 3600); const m = Math.floor((sec % 3600) / 60); return h > 0 ? `${h}h ${m}m` : `${m}m` }
function barWidth(val: number, max: number) { return max > 0 ? `${(val / max) * 100}%` : '0%' }

async function loadAll() {
  trendsLoading.value = true; topUsersLoading.value = true; topMediaLoading.value = true
  try {
    const [ov, tr, tu, tm] = await Promise.all([statsApi.overview(), statsApi.trends(days.value), statsApi.topUsers(10), statsApi.topMedia(10)])
    overview.value = ov.data; trends.value = tr.data ?? []; topUsers.value = tu.data ?? []; topMedia.value = tm.data ?? []
  } catch {} finally { trendsLoading.value = false; topUsersLoading.value = false; topMediaLoading.value = false }
}

onMounted(loadAll)
</script>

<style scoped>
.stat-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; margin-bottom: 16px; }
.card-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.card-title { font-weight: 600; font-size: 14px; }
.day-tabs { display: flex; gap: 4px; }
.tab { padding: 3px 10px; border-radius: 6px; font-size: 12px; background: transparent; color: var(--text-muted); border: 1px solid var(--border); cursor: pointer; }
.tab.active { background: var(--brand); color: #fff; border-color: var(--brand); }
.rank-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.rank-list { list-style: none; }
.rank-item { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--border); }
.rank-item:last-child { border-bottom: none; }
.rank-num { width: 24px; height: 24px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600; background: var(--bg-secondary); color: var(--text-muted); flex-shrink: 0; }
.rank-top { background: var(--brand-light); color: var(--brand); }
.rank-name { font-size: 13px; flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text); }
.rank-val { font-size: 12px; color: var(--text-muted); flex-shrink: 0; }
.rank-bar { width: 60px; height: 4px; background: var(--bg-secondary); border-radius: 2px; flex-shrink: 0; overflow: hidden; }
.rank-fill { height: 100%; background: var(--brand); border-radius: 2px; transition: width 0.3s; }
@media (max-width: 768px) { .rank-grid { grid-template-columns: 1fr; } }
</style>
