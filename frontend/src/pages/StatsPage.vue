<template>
 <div class="stats-page">
 <!-- 页头 -->
 <PageHeader title="播放统计" desc="数据分析与趋势概览">
 <template #actions>
 <div class="range-tabs">
 <button
 v-for="opt in RANGE_OPTIONS"
 :key="opt.value"
 class="range-tab"
 :class="{ active: selectedDays === opt.value }"
 @click="changeRange(opt.value)"
 >
 {{ opt.label }}
 </button>
 </div>
 </template>
 </PageHeader>

 <!-- ① 概览卡片 -->
 <section class="overview-row">
 <template v-if="overviewLoading && !overview">
 <div v-for="i in 4" :key="i" class="stat-card card skeleton-card" />
 </template>
 <div v-else-if="overviewError" class="overview-error">
 <ErrorState :message="overviewError" compact @retry="loadOverview" />
 </div>
 <template v-else-if="overview">
 <StatCard
 label="总播放次数"
 :value="formatNumber(overview.total_play_count)"
 />
 <StatCard
 label="总播放时长"
 :value="formatDuration(overview.total_play_duration_sec)"
 />
 <StatCard
 label="活跃用户数"
 :value="overview.unique_users"
 sub="人"
 />
 <StatCard
 label="覆盖媒体数"
 :value="overview.unique_media"
 sub="个"
 />
 </template>
 </section>

 <!-- ② 趋势图 -->
 <div class="card trend-section">
 <div class="card-head">
 <div class="trend-head-left">
 <span class="card-title">播放趋势</span>
 <span class="trend-range-hint">最近 {{ selectedDays }} 天</span>
 </div>
 <div class="trend-legend">
 <span class="legend-dot" style="background: #6366f1;" />
 <span class="legend-label">播放次数</span>
 <span class="legend-dot" style="background: #22c55e; margin-left: 14px;" />
 <span class="legend-label">活跃用户</span>
 </div>
 </div>

 <LoadingState v-if="trendsLoading" height="240px" />
 <ErrorState
 v-else-if="trendsError"
 :message="trendsError"
 compact
 @retry="loadTrends"
 />
 <TrendChart
 v-else-if="trends.length > 0"
 :x-data="trends.map(t => t.date.slice(5))"
 :series="[
 { name: '播放次数', data: trends.map(t => t.play_count) },
 { name: '活跃用户', data: trends.map(t => t.active_users), color: '#22c55e' },
 ]"
 height="240px"
 />
 <div v-else class="chart-empty">暂无趋势数据</div>
 </div>

 <!-- ③ 双列排行榜 -->
 <div class="rank-grid">
 <!-- 活跃用户 Top 10 -->
 <div class="card rank-card">
 <div class="card-head">
 <span class="card-title">活跃用户 Top 10</span>
 <span class="rank-hint">按播放次数</span>
 </div>

 <LoadingState v-if="topUsersLoading" height="320px" />
 <ErrorState
 v-else-if="topUsersError"
 :message="topUsersError"
 compact
 @retry="loadTopUsers"
 />
 <div v-else-if="topUsers.length === 0" class="rank-empty">暂无数据</div>
 <ol v-else class="rank-list">
 <li
 v-for="(u, idx) in topUsers"
 :key="u.user_id"
 class="rank-item"
 >
 <!-- 排名 -->
 <span class="rank-badge" :class="rankBadgeClass(idx + 1)">
 {{ idx + 1 }}
 </span>

 <!-- 用户信息 + 进度条 -->
 <div class="rank-body">
 <div class="rank-top-row">
 <RouterLink :to="`/users/${u.user_id}`" class="rank-name">
 {{ u.username }}
 </RouterLink>
 <span class="rank-count">{{ u.play_count }} 次</span>
 </div>
 <div class="rank-bar-track">
 <div
 class="rank-bar-fill"
 :style="{
 width: barPercent(u.play_count, topUsers[0].play_count),
 background: rankBarColor(idx),
 }"
 />
 </div>
 <div class="rank-sub-row">
 <span class="rank-duration">{{ formatDuration(u.play_duration_sec) }}</span>
 </div>
 </div>
 </li>
 </ol>
 </div>

 <!-- 热门媒体 Top 10 -->
 <div class="card rank-card">
 <div class="card-head">
 <span class="card-title">热门媒体 Top 10</span>
 <span class="rank-hint">按播放次数</span>
 </div>

 <LoadingState v-if="topMediaLoading" height="320px" />
 <ErrorState
 v-else-if="topMediaError"
 :message="topMediaError"
 compact
 @retry="loadTopMedia"
 />
 <div v-else-if="topMedia.length === 0" class="rank-empty">暂无数据</div>
 <ol v-else class="rank-list">
 <li
 v-for="(m, idx) in topMedia"
 :key="m.media_id"
 class="rank-item"
 >
 <span class="rank-badge" :class="rankBadgeClass(idx + 1)">
 {{ idx + 1 }}
 </span>
 <div class="rank-body">
 <div class="rank-top-row">
 <span class="rank-name rank-name-plain">{{ m.media_name }}</span>
 <span class="rank-count">{{ m.play_count }} 次</span>
 </div>
 <div class="rank-bar-track">
 <div
 class="rank-bar-fill"
 :style="{
 width: barPercent(m.play_count, topMedia[0].play_count),
 background: rankBarColor(idx),
 }"
 />
 </div>
 <div class="rank-sub-row">
 <span class="media-type-tag tag tag-gray">
 {{ mediaTypeLabel(m.media_type) }}
 </span>
 </div>
 </div>
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
import ErrorState from '@/components/common/ErrorState.vue'
import TrendChart from '@/components/charts/TrendChart.vue'
import {
 statsApi,
 type StatsOverview,
 type TopUserItem,
 type TopMediaItem,
 type StatsTrendPoint,
} from '@/api/stats'
import { formatDuration, formatNumber } from '@/utils/time'

// ── 常量 ─────────────────────────────────────────
const RANGE_OPTIONS = [
 { label: '7 天', value: 7 },
 { label: '30 天', value: 30 },
 { label: '90 天', value: 90 },
]

const BAR_COLORS = [
 '#6366f1',
 '#818cf8',
 '#a5b4fc',
 '#c7d2fe',
 '#e0e7ff',
]

// ── 状态 ─────────────────────────────────────────
const selectedDays = ref(7)

const overview = ref<StatsOverview | null>(null)
const overviewLoading = ref(false)
const overviewError = ref<string | null>(null)

const trends = ref<StatsTrendPoint[]>([])
const trendsLoading = ref(false)
const trendsError = ref<string | null>(null)

const topUsers = ref<TopUserItem[]>([])
const topUsersLoading = ref(false)
const topUsersError = ref<string | null>(null)

const topMedia = ref<TopMediaItem[]>([])
const topMediaLoading = ref(false)
const topMediaError = ref<string | null>(null)

// ── 数据加载 ──────────────────────────────────────
async function loadOverview() {
 overviewLoading.value = true
 overviewError.value = null
 try {
 overview.value = await statsApi.overview()
 } catch {
 overviewError.value = '获取概览数据失败'
 } finally {
 overviewLoading.value = false
 }
}

async function loadTrends() {
 trendsLoading.value = true
 trendsError.value = null
 try {
 trends.value = await statsApi.trends(selectedDays.value)
 } catch {
 trendsError.value = '获取趋势数据失败'
 } finally {
 trendsLoading.value = false
 }
}

async function loadTopUsers() {
 topUsersLoading.value = true
 topUsersError.value = null
 try {
 topUsers.value = await statsApi.topUsers(10)
 } catch {
 topUsersError.value = '获取用户排行失败'
 } finally {
 topUsersLoading.value = false
 }
}

async function loadTopMedia() {
 topMediaLoading.value = true
 topMediaError.value = null
 try {
 topMedia.value = await statsApi.topMedia(10)
 } catch {
 topMediaError.value = '获取媒体排行失败'
 } finally {
 topMediaLoading.value = false
 }
}

// 切换时间范围只刷新趋势图
function changeRange(days: number) {
 selectedDays.value = days
 loadTrends()
}

// ── 工具函数 ──────────────────────────────────────
function barPercent(val: number, max: number): string {
 if (!max) return '0%'
 const pct = Math.round((val / max) * 100)
 return `${Math.max(pct, 4)}%` // 最小 4% 保证可见
}

function rankBarColor(idx: number): string {
 return BAR_COLORS[Math.min(idx, BAR_COLORS.length - 1)]
}

function rankBadgeClass(rank: number): string {
 return { 1: 'badge-gold', 2: 'badge-silver', 3: 'badge-bronze' }[rank] ?? 'badge-plain'
}

function mediaTypeLabel(t: string): string {
 return (
 { movie: '电影', episode: '剧集', series: '剧集', music: '音乐' }[t] ?? t
 )
}

// ── 初始化 ────────────────────────────────────────
onMounted(() => {
 Promise.all([loadOverview(), loadTrends(), loadTopUsers(), loadTopMedia()])
})
</script>

<style scoped>
/* ── 概览卡片 ──────────────────────────────────── */
.overview-row {
 display: grid;
 grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
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

/* ── 时间范围切换 ────────────────────────────────── */
.range-tabs {
 display: flex;
 gap: 4px;
}

.range-tab {
 padding: 5px 14px;
 border-radius: 5px;
 font-size: 13px;
 background: var(--color-surface-2);
 color: var(--color-text-muted);
 border: 1px solid var(--color-border);
 cursor: pointer;
 transition: all 0.15s;
}

.range-tab:hover:not(.active) {
 color: var(--color-text);
 border-color: var(--color-text-muted);
}

.range-tab.active {
 background: var(--color-primary);
 color: #fff;
 border-color: var(--color-primary);
}

/* ── 趋势图 ─────────────────────────────────────── */
.trend-section {
 margin-bottom: 20px;
}

.card-head {
 display: flex;
 align-items: center;
 justify-content: space-between;
 margin-bottom: 16px;
}

.card-title {
 font-weight: 600;
 font-size: 14px;
}

.trend-head-left {
 display: flex;
 align-items: baseline;
 gap: 8px;
}

.trend-range-hint {
 font-size: 12px;
 color: var(--color-text-muted);
}

.trend-legend {
 display: flex;
 align-items: center;
 gap: 5px;
}

.legend-dot {
 width: 8px;
 height: 8px;
 border-radius: 50%;
 flex-shrink: 0;
}

.legend-label {
 font-size: 12px;
 color: var(--color-text-muted);
}

.chart-empty {
 height: 240px;
 display: flex;
 align-items: center;
 justify-content: center;
 background: var(--color-surface-2);
 border-radius: 6px;
 color: var(--color-text-muted);
 font-size: 13px;
 border: 1px dashed var(--color-border);
}

/* ── 双列排行榜 ──────────────────────────────────── */
.rank-grid {
 display: grid;
 grid-template-columns: 1fr 1fr;
 gap: 16px;
}

.rank-card { }

.rank-hint {
 font-size: 12px;
 color: var(--color-text-muted);
}

.rank-empty {
 padding: 48px;
 text-align: center;
 color: var(--color-text-muted);
 font-size: 13px;
}

/* ── 排行榜条目 ──────────────────────────────────── */
.rank-list {
 list-style: none;
 margin: 0;
 padding: 0;
 display: flex;
 flex-direction: column;
 gap: 14px;
}

.rank-item {
 display: flex;
 align-items: flex-start;
 gap: 10px;
}

/* 排名徽章 */
.rank-badge {
 width: 24px;
 height: 24px;
 border-radius: 6px;
 display: flex;
 align-items: center;
 justify-content: center;
 font-size: 12px;
 font-weight: 700;
 flex-shrink: 0;
 margin-top: 1px;
}

.badge-gold { background: rgba(245, 158, 11, 0.2); color: #f59e0b; }
.badge-silver { background: rgba(148, 163, 184, 0.2); color: #94a3b8; }
.badge-bronze { background: rgba(180, 120, 60, 0.2); color: #b47c3c; }
.badge-plain { background: var(--color-surface-2); color: var(--color-text-muted); }

/* 条目主体 */
.rank-body {
 flex: 1;
 min-width: 0;
 display: flex;
 flex-direction: column;
 gap: 5px;
}

.rank-top-row {
 display: flex;
 align-items: baseline;
 justify-content: space-between;
 gap: 8px;
}

.rank-name {
 font-size: 13px;
 font-weight: 500;
 color: var(--color-text);
 white-space: nowrap;
 overflow: hidden;
 text-overflow: ellipsis;
 min-width: 0;
}

a.rank-name:hover {
 color: var(--color-primary);
}

.rank-name-plain {
 /* 非链接版本，不需要 hover */
}

.rank-count {
 font-size: 13px;
 font-weight: 600;
 color: var(--color-text);
 flex-shrink: 0;
}

/* 进度条 */
.rank-bar-track {
 height: 5px;
 background: var(--color-surface-2);
 border-radius: 3px;
 overflow: hidden;
}

.rank-bar-fill {
 height: 100%;
 border-radius: 3px;
 transition: width 0.5s ease;
 opacity: 0.85;
}

/* 副行信息 */
.rank-sub-row {
 display: flex;
 align-items: center;
 gap: 6px;
}

.rank-duration {
 font-size: 11px;
 color: var(--color-text-muted);
}

.media-type-tag {
 font-size: 11px;
 padding: 1px 6px;
}
</style>