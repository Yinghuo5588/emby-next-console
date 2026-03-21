<template>
 <div class="dashboard">
 <!-- 页头 -->
 <PageHeader title="仪表盘" desc="系统实时总览">
 <template #actions>
 <button
 class="btn btn-ghost refresh-btn"
 :disabled="anyLoading"
 @click="handleRefresh"
 >
 <span class="refresh-icon" :class="{ spinning: anyLoading }">↻</span>
 {{ anyLoading ? '刷新中...' : '刷新' }}
 </button>
 </template>
 </PageHeader>

 <!-- ① 概览卡片行 -->
 <section class="overview-row">
 <!-- skeleton -->
 <template v-if="store.summaryLoading && !store.summary">
 <div v-for="i in 6" :key="i" class="stat-card card skeleton-card" />
 </template>
 <!-- error -->
 <div v-else-if="store.summaryError" class="overview-error">
 <ErrorState :message="store.summaryError" compact @retry="store.fetchSummary()" />
 </div>
 <!-- data -->
 <template v-else-if="store.summary">
 <StatCard
 label="总用户数"
 :value="store.summary.overview.total_users"
 />
 <StatCard
 label="今日活跃"
 :value="store.summary.overview.active_users_today"
 sub="人"
 />
 <StatCard
 label="当前在线会话"
 :value="store.summary.overview.current_active_sessions"
 :highlight="store.summary.overview.current_active_sessions > 0"
 />
 <StatCard
 label="媒体总量"
 :value="store.summary.overview.total_media_count"
 />
 <StatCard
 label="今日播放"
 :value="store.summary.playback.today_play_count"
 :sub="formatDuration(store.summary.playback.today_play_duration_sec)"
 />
 <StatCard
 label="未读通知"
 :value="store.summary.notifications.unread_count"
 :danger="store.summary.notifications.unread_count > 0"
 />
 </template>
 </section>

 <!-- ② 主内容区：左列 + 右列 -->
 <div class="dashboard-body">

 <!-- 左列 -->
 <div class="col-left">

 <!-- 播放趋势图 -->
 <div class="card trend-card">
 <div class="card-head">
 <span class="card-title">播放趋势</span>
 <div class="day-tabs">
 <button
 v-for="opt in DAY_OPTIONS"
 :key="opt.value"
 class="day-tab"
 :class="{ active: trendDays === opt.value }"
 @click="changeTrendDays(opt.value)"
 >
 {{ opt.label }}
 </button>
 </div>
 </div>

 <LoadingState v-if="store.trendsLoading" height="200px" />
 <ErrorState
 v-else-if="store.trendsError"
 :message="store.trendsError"
 compact
 @retry="store.fetchTrends(trendDays)"
 />
 <TrendChart
 v-else-if="store.trends.length > 0"
 :x-data="store.trends.map(t => t.date.slice(5))"
 :series="[
 { name: '播放次数', data: store.trends.map(t => t.play_count) },
 { name: '活跃用户', data: store.trends.map(t => t.active_users), color: '#22c55e' },
 ]"
 height="200px"
 />
 <div v-else class="chart-empty">暂无趋势数据</div>
 </div>

 <!-- 当前播放会话 -->
 <div class="card sessions-card">
 <div class="card-head">
 <span class="card-title">当前播放会话</span>
 <div class="sessions-meta">
 <span
 v-if="!store.sessionsLoading"
 class="tag"
 :class="store.sessions.length > 0 ? 'tag-green' : 'tag-gray'"
 >
 {{ store.sessions.length }} 个活跃
 </span>
 <button
 class="icon-btn"
 title="刷新会话"
 :disabled="store.sessionsLoading"
 @click="store.fetchSessions()"
 >
 <span :class="{ spinning: store.sessionsLoading }">↻</span>
 </button>
 </div>
 </div>

 <LoadingState v-if="store.sessionsLoading && store.sessions.length === 0" height="100px" />
 <ErrorState
 v-else-if="store.sessionsError"
 :message="store.sessionsError"
 compact
 @retry="store.fetchSessions()"
 />
 <div v-else-if="store.sessions.length === 0" class="sessions-empty">
 <span class="empty-dot" />
 当前没有活跃播放会话
 </div>
 <ul v-else class="sessions-list">
 <li
 v-for="s in store.sessions"
 :key="s.session_id"
 class="session-item"
 >
 <div class="session-indicator" />
 <div class="session-body">
 <div class="session-top">
 <RouterLink :to="`/users/${s.user_id}`" class="session-username">
 {{ s.username }}
 </RouterLink>
 <span class="session-media">{{ s.media_name }}</span>
 </div>
 <div class="session-bottom">
 <span class="session-chip">{{ s.client_name ?? '未知客户端' }}</span>
 <span class="session-chip">{{ s.ip_address ?? '—' }}</span>
 <span class="session-since">{{ fromNow(s.started_at) }}</span>
 </div>
 </div>
 </li>
 </ul>
 </div>

 </div>

 <!-- 右列 -->
 <div class="col-right">

 <!-- 风控摘要 -->
 <div class="card summary-card risk-card">
 <div class="card-head">
 <span class="card-title">风控状态</span>
 <RouterLink to="/risk" class="card-link">查看全部 →</RouterLink>
 </div>

 <LoadingState v-if="store.summaryLoading && !store.summary" height="80px" />
 <template v-else-if="store.summary">
 <div class="summary-row">
 <span class="summary-label">待处理事件</span>
 <span
 class="tag"
 :class="store.summary.risk.open_risk_count > 0 ? 'tag-yellow' : 'tag-green'"
 >
 {{ store.summary.risk.open_risk_count }}
 </span>
 </div>
 <div class="summary-row">
 <span class="summary-label">高危事件</span>
 <span
 class="tag"
 :class="store.summary.risk.high_risk_count > 0 ? 'tag-red' : 'tag-green'"
 >
 {{ store.summary.risk.high_risk_count }}
 </span>
 </div>
 <div
 v-if="store.summary.risk.open_risk_count > 0"
 class="risk-alert"
 >
 ⚠ 有待处理的风控事件，请尽快处理
 </div>
 <div v-else class="risk-ok">✓ 当前无待处理风险</div>
 </template>
 </div>

 <!-- 今日播放摘要 -->
 <div class="card summary-card play-card">
 <div class="card-head">
 <span class="card-title">今日播放</span>
 <RouterLink to="/stats" class="card-link">统计详情 →</RouterLink>
 </div>

 <LoadingState v-if="store.summaryLoading && !store.summary" height="80px" />
 <template v-else-if="store.summary">
 <div class="summary-row">
 <span class="summary-label">播放次数</span>
 <span class="summary-value">{{ store.summary.playback.today_play_count }}</span>
 </div>
 <div class="summary-row">
 <span class="summary-label">播放时长</span>
 <span class="summary-value">
 {{ formatDuration(store.summary.playback.today_play_duration_sec) }}
 </span>
 </div>
 <div class="summary-row">
 <span class="summary-label">峰值并发</span>
 <span class="summary-value">{{ store.summary.playback.peak_concurrent_today }}</span>
 </div>
 </template>
 </div>

 </div>
 </div>
 </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import TrendChart from '@/components/charts/TrendChart.vue'
import { useDashboardStore } from '@/stores/dashboard'
import { fromNow, formatDuration } from '@/utils/time'

const store = useDashboardStore()

const trendDays = ref(7)

const DAY_OPTIONS = [
 { label: '7 天', value: 7 },
 { label: '14 天', value: 14 },
 { label: '30 天', value: 30 },
]

const anyLoading = computed(
 () => store.summaryLoading || store.sessionsLoading || store.trendsLoading,
)

function changeTrendDays(days: number) {
 trendDays.value = days
 store.fetchTrends(days)
}

function handleRefresh() {
 store.fetchAll(trendDays.value)
}

onMounted(() => {
 store.fetchAll(trendDays.value)
})
</script>

<style scoped>
/* ── 概览卡片行 ────────────────────────────────── */
.overview-row {
 display: grid;
 grid-template-columns: repeat(auto-fill, minmax(148px, 1fr));
 gap: 12px;
 margin-bottom: 20px;
}

.skeleton-card {
 height: 88px;
 background: linear-gradient(
 90deg,
 var(--color-surface-2) 25%,
 var(--color-border) 50%,
 var(--color-surface-2) 75%
 );
 background-size: 200% 100%;
 animation: shimmer 1.4s infinite;
 border-radius: 10px;
}

@keyframes shimmer {
 to { background-position: -200% 0; }
}

.overview-error {
 grid-column: 1 / -1;
}

/* ── 主体布局 ──────────────────────────────────── */
.dashboard-body {
 display: grid;
 grid-template-columns: 1fr 300px;
 gap: 16px;
 align-items: start;
}

.col-left,
.col-right {
 display: flex;
 flex-direction: column;
 gap: 16px;
}

/* ── 通用 card head ─────────────────────────────── */
.card-head {
 display: flex;
 align-items: center;
 justify-content: space-between;
 margin-bottom: 14px;
}

.card-title {
 font-weight: 600;
 font-size: 14px;
}

.card-link {
 font-size: 12px;
 color: var(--color-primary);
}

/* ── 趋势图 ─────────────────────────────────────── */
.trend-card { }

.day-tabs {
 display: flex;
 gap: 4px;
}

.day-tab {
 padding: 3px 10px;
 border-radius: 4px;
 font-size: 12px;
 background: var(--color-surface-2);
 color: var(--color-text-muted);
 border: 1px solid var(--color-border);
 cursor: pointer;
 transition: all 0.15s;
}

.day-tab:hover:not(.active) {
 color: var(--color-text);
}

.day-tab.active {
 background: var(--color-primary);
 color: #fff;
 border-color: var(--color-primary);
}

.chart-empty {
 height: 200px;
 display: flex;
 align-items: center;
 justify-content: center;
 background: var(--color-surface-2);
 border-radius: 6px;
 color: var(--color-text-muted);
 font-size: 13px;
 border: 1px dashed var(--color-border);
}

/* ── 当前会话 ────────────────────────────────────── */
.sessions-card { padding: 0; overflow: hidden; }

.sessions-card .card-head {
 padding: 14px 18px 14px;
 margin-bottom: 0;
 border-bottom: 1px solid var(--color-border);
}

.sessions-meta {
 display: flex;
 align-items: center;
 gap: 8px;
}

.icon-btn {
 background: none;
 border: none;
 color: var(--color-text-muted);
 font-size: 15px;
 cursor: pointer;
 padding: 2px 4px;
 line-height: 1;
}

.icon-btn:hover { color: var(--color-text); }
.icon-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.sessions-empty {
 display: flex;
 align-items: center;
 gap: 8px;
 padding: 24px 18px;
 color: var(--color-text-muted);
 font-size: 13px;
}

.empty-dot {
 width: 6px;
 height: 6px;
 border-radius: 50%;
 background: var(--color-border);
 flex-shrink: 0;
}

.sessions-list {
 list-style: none;
 margin: 0;
 padding: 0;
}

.session-item {
 display: flex;
 align-items: center;
 gap: 12px;
 padding: 10px 18px;
 border-bottom: 1px solid var(--color-border);
 transition: background 0.12s;
}

.session-item:last-child {
 border-bottom: none;
}

.session-item:hover {
 background: var(--color-surface-2);
}

.session-indicator {
 width: 6px;
 height: 6px;
 border-radius: 50%;
 background: var(--color-success);
 flex-shrink: 0;
 box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.15);
 animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
 0%, 100% { box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.15); }
 50% { box-shadow: 0 0 0 5px rgba(34, 197, 94, 0.05); }
}

.session-body {
 flex: 1;
 min-width: 0;
}

.session-top {
 display: flex;
 align-items: baseline;
 gap: 8px;
 margin-bottom: 4px;
}

.session-username {
 font-size: 13px;
 font-weight: 600;
 color: var(--color-text);
 white-space: nowrap;
 flex-shrink: 0;
}

.session-username:hover { color: var(--color-primary); }

.session-media {
 font-size: 12px;
 color: var(--color-text-muted);
 white-space: nowrap;
 overflow: hidden;
 text-overflow: ellipsis;
}

.session-bottom {
 display: flex;
 align-items: center;
 gap: 6px;
 flex-wrap: wrap;
}

.session-chip {
 font-size: 11px;
 color: var(--color-text-muted);
 background: var(--color-surface-2);
 border: 1px solid var(--color-border);
 border-radius: 3px;
 padding: 1px 5px;
}

.session-since {
 font-size: 11px;
 color: var(--color-primary);
 margin-left: auto;
 flex-shrink: 0;
}

/* ── 右列摘要卡 ─────────────────────────────────── */
.summary-card { }

.summary-row {
 display: flex;
 align-items: center;
 justify-content: space-between;
 padding: 9px 0;
 border-bottom: 1px solid var(--color-border);
}

.summary-row:last-of-type {
 border-bottom: none;
}

.summary-label {
 color: var(--color-text-muted);
 font-size: 13px;
}

.summary-value {
 font-weight: 600;
 font-size: 14px;
}

.risk-alert {
 margin-top: 10px;
 padding: 8px 10px;
 background: rgba(245, 158, 11, 0.08);
 border-left: 3px solid var(--color-warning);
 border-radius: 4px;
 font-size: 12px;
 color: var(--color-warning);
}

.risk-ok {
 margin-top: 10px;
 padding: 8px 10px;
 background: rgba(34, 197, 94, 0.07);
 border-left: 3px solid var(--color-success);
 border-radius: 4px;
 font-size: 12px;
 color: var(--color-success);
}

/* ── 刷新按钮 ────────────────────────────────────── */
.refresh-btn {
 display: flex;
 align-items: center;
 gap: 5px;
}

.refresh-icon {
 display: inline-block;
 font-size: 15px;
 line-height: 1;
}

.spinning {
 animation: spin 0.7s linear infinite;
}

@keyframes spin {
 to { transform: rotate(360deg); }
}
</style>