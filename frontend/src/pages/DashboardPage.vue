<template>
  <div>
    <PageHeader title="仪表盘" desc="系统实时总览">
      <template #actions>
        <button class="btn btn-ghost" :disabled="loading" @click="refresh">
          {{ loading ? '刷新中...' : '刷新' }}
        </button>
      </template>
    </PageHeader>

    <section class="stat-grid">
      <template v-if="summaryLoading && !summary">
        <div v-for="i in 6" :key="i" class="card skeleton" />
      </template>
      <template v-else-if="summary">
        <StatCard label="总用户" :value="summary.overview?.total_users ?? 0" />
        <StatCard label="今日活跃" :value="summary.overview?.active_users_today ?? 0" />
        <StatCard label="在线会话" :value="summary.overview?.current_active_sessions ?? 0" :highlight="(summary.overview?.current_active_sessions ?? 0) > 0" />
        <StatCard label="媒体总量" :value="summary.overview?.total_media_count ?? 0" />
        <StatCard label="今日播放" :value="summary.playback?.today_play_count ?? 0" />
        <StatCard label="未读通知" :value="summary.notifications?.unread_count ?? 0" :danger="(summary.notifications?.unread_count ?? 0) > 0" />
      </template>
    </section>

    <div class="body-grid">
      <div class="left">
        <div class="card">
          <div class="card-head">
            <span class="card-title">播放趋势</span>
            <div class="tabs">
              <button v-for="d in [7, 14, 30]" :key="d" class="tab" :class="{ active: trendDays === d }" @click="trendDays = d; fetchTrends()">{{ d }}天</button>
            </div>
          </div>
          <LoadingState v-if="trendsLoading" height="200px" />
          <TrendChart v-else-if="trends.length > 0" :x-data="trends.map((t: any) => (t.date || '').slice(5))" :series="[{ name: '播放', data: trends.map((t: any) => t.play_count ?? 0) }, { name: '活跃', data: trends.map((t: any) => t.active_users ?? 0), color: '#34c759' }]" />
          <div v-else class="empty-chart">暂无趋势数据</div>
        </div>

        <div class="card">
          <div class="card-head">
            <span class="card-title">当前播放</span>
            <span class="tag tag-green">{{ sessions.length }} 活跃</span>
          </div>
          <LoadingState v-if="sessionsLoading && sessions.length === 0" height="100px" />
          <EmptyState v-else-if="sessions.length === 0" title="暂无活跃会话" />
          <ul v-else class="session-list">
            <li v-for="s in sessions" :key="s.session_id" class="session-item">
              <div class="session-dot" />
              <div class="session-info">
                <span class="session-user">{{ s.username }}</span>
                <span class="session-media">{{ s.media_name }}</span>
              </div>
            </li>
          </ul>
        </div>
      </div>

      <div class="right">
        <div class="card">
          <div class="card-head"><span class="card-title">风控</span><RouterLink to="/risk" class="link">详情 →</RouterLink></div>
          <div class="summary-row"><span>待处理</span><span class="tag" :class="(summary?.risk?.open_risk_count ?? 0) > 0 ? 'tag-yellow' : 'tag-green'">{{ summary?.risk?.open_risk_count ?? 0 }}</span></div>
          <div class="summary-row"><span>高危</span><span class="tag" :class="(summary?.risk?.high_risk_count ?? 0) > 0 ? 'tag-red' : 'tag-green'">{{ summary?.risk?.high_risk_count ?? 0 }}</span></div>
        </div>
        <div class="card">
          <div class="card-head"><span class="card-title">今日播放</span><RouterLink to="/stats" class="link">统计 →</RouterLink></div>
          <div class="summary-row"><span>播放次数</span><span>{{ summary?.playback?.today_play_count ?? 0 }}</span></div>
          <div class="summary-row"><span>峰值并发</span><span>{{ summary?.playback?.peak_concurrent_today ?? 0 }}</span></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import TrendChart from '@/components/charts/TrendChart.vue'
import { dashboardApi } from '@/api/dashboard'
import { statsApi } from '@/api/stats'

const summary = ref<any>(null)
const summaryLoading = ref(false)
const sessions = ref<any[]>([])
const sessionsLoading = ref(false)
const trends = ref<any[]>([])
const trendsLoading = ref(false)
const trendDays = ref(7)
const loading = ref(false)

async function fetchSummary() { summaryLoading.value = true; try { summary.value = (await dashboardApi.summary()).data } finally { summaryLoading.value = false } }
async function fetchSessions() { sessionsLoading.value = true; try { const r = await dashboardApi.summary(); sessions.value = r.data?.sessions ?? [] } finally { sessionsLoading.value = false } }
async function fetchTrends() { trendsLoading.value = true; try { trends.value = (await statsApi.trends(trendDays.value)).data ?? [] } finally { trendsLoading.value = false } }
async function refresh() { loading.value = true; await Promise.all([fetchSummary(), fetchSessions(), fetchTrends()]); loading.value = false }

onMounted(refresh)
</script>

<style scoped>
.stat-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; margin-bottom: 20px; }
.skeleton { height: 88px; background: var(--bg-secondary); border-radius: var(--radius); }
.body-grid { display: grid; grid-template-columns: 1fr 280px; gap: 16px; align-items: start; }
.left, .right { display: flex; flex-direction: column; gap: 16px; }
.card-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.card-title { font-weight: 600; font-size: 14px; }
.link { font-size: 12px; color: var(--brand); }
.tabs { display: flex; gap: 4px; }
.tab { padding: 3px 10px; border-radius: 6px; font-size: 12px; background: transparent; color: var(--text-muted); border: 1px solid var(--border); cursor: pointer; }
.tab.active { background: var(--brand); color: #fff; border-color: var(--brand); }
.empty-chart { height: 200px; display: flex; align-items: center; justify-content: center; color: var(--text-muted); font-size: 13px; background: var(--bg-secondary); border-radius: 8px; }
.session-list { list-style: none; }
.session-item { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--border); }
.session-item:last-child { border-bottom: none; }
.session-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--success); flex-shrink: 0; }
.session-info { display: flex; flex-direction: column; min-width: 0; }
.session-user { font-size: 13px; font-weight: 500; }
.session-media { font-size: 12px; color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.summary-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 13px; }
.summary-row:last-child { border-bottom: none; }
@media (max-width: 768px) { .body-grid { grid-template-columns: 1fr; } }
</style>
