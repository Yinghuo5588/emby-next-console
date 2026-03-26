<template>
  <div class="calendar-page">
    <PageHeader title="追剧日历" />

    <!-- 统计条 -->
    <div class="stats-bar" v-if="!loading">
      <div class="stat-item">
        <span class="stat-num">{{ stats.total_series }}</span>
        <span class="stat-label">连载中</span>
      </div>
      <div class="stat-item">
        <span class="stat-num">{{ stats.total_upcoming }}</span>
        <span class="stat-label">本周更新</span>
      </div>
      <div class="stat-item">
        <span class="stat-num num-ready">{{ stats.ready }}</span>
        <span class="stat-label">已入库</span>
      </div>
      <div class="stat-item">
        <span class="stat-num num-pending">{{ stats.pending }}</span>
        <span class="stat-label">待入库</span>
      </div>
    </div>

    <!-- 周导航 -->
    <div class="week-nav" v-if="!loading">
      <button class="week-btn" @click="changeWeek(-1)">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M15 18l-6-6 6-6"/></svg>
      </button>
      <span class="week-label">{{ dateRange }}</span>
      <button class="week-btn" @click="changeWeek(1)">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M9 18l6-6-6-6"/></svg>
      </button>
    </div>

    <!-- 日历 - 垂直滚动 -->
    <div class="cal-list" v-if="!loading">
      <div
        v-for="day in days"
        :key="day.date"
        class="day-card"
        :class="{ today: day.is_today }"
      >
        <!-- 日期头部 -->
        <div class="day-head">
          <div class="day-left">
            <span class="day-num">{{ dayNum(day.date) }}</span>
            <div class="day-meta">
              <span class="day-weekday">{{ day.weekday_cn }}</span>
              <span class="day-full-date">{{ dayFullDate(day.date) }}</span>
            </div>
          </div>
          <span v-if="day.is_today" class="today-badge">今天</span>
          <span v-else-if="day.items.length > 0" class="day-count">{{ day.items.length }} 集</span>
        </div>

        <!-- 剧集列表 -->
        <div class="ep-list" v-if="day.items.length > 0">
          <div
            v-for="(item, idx) in day.items"
            :key="`${item.tmdb_id}-${item.season}-${item.episode}-${idx}`"
            class="ep-card"
            :class="[item.status, { expanded: expandedId === itemKey(item, idx) }]"
            @click="toggleExpand(item, idx)"
          >
            <!-- 主行 -->
            <img :src="item.poster_url" class="ep-poster" loading="lazy" @error="onImgErr" />
            <div class="ep-body">
              <div class="ep-title">{{ item.series_name }}</div>
              <div class="ep-meta-row">
                <span class="ep-num">S{{ pad(item.season) }}E{{ item.episode }}</span>
                <span class="tag" :class="statusClass(item.status)">{{ statusLabel(item.status) }}</span>
              </div>
              <div class="ep-name" v-if="item.episode_name">{{ item.episode_name }}</div>
            </div>
            <div class="ep-expand-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M6 9l6 6 6-6"/>
              </svg>
            </div>

            <!-- 展开详情 -->
            <div class="ep-detail" v-if="expandedId === itemKey(item, idx)">
              <div class="ep-overview" v-if="item.series_overview">
                <div class="detail-label">剧集简介</div>
                <p>{{ item.series_overview }}</p>
              </div>
              <div class="ep-overview" v-if="item.ep_overview">
                <div class="detail-label">本集简介</div>
                <p>{{ item.ep_overview }}</p>
              </div>
              <div class="ep-no-detail" v-if="!item.series_overview && !item.ep_overview">
                暂无简介
              </div>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div class="day-empty" v-else>
          <span>无更新</span>
        </div>
      </div>
    </div>

    <!-- 加载 -->
    <div v-if="loading" class="loading-wrap">
      <n-spin size="large" />
      <span>正在从 TMDB 拉取排期…首次加载可能较慢</span>
    </div>

    <!-- 空状态 -->
    <div v-if="!loading && days.length === 0" class="empty-wrap">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.3"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
      <p>这周没有剧集更新</p>
    </div>

    <!-- 刷新 FAB -->
    <n-button class="fab-refresh" type="primary" circle size="large" @click="refresh" :loading="loading">
      <n-icon size="20"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M23 4v6h-6"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg></n-icon>
    </n-button>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import PageHeader from '@/components/common/PageHeader.vue'
import { calendarApi } from '@/api/calendar'

const msg = useMessage()
const loading = ref(true)
const weekOffset = ref(0)
const days = ref<any[]>([])
const dateRange = ref('')
const stats = reactive({ total_series: 0, total_upcoming: 0, ready: 0, pending: 0 })
const expandedId = ref('')

function pad(n: any) { return String(n ?? 0).padStart(2, '0') }
function dayNum(d: string) { return parseInt(d.split('-')[2], 10) }
function dayFullDate(d: string) {
  const p = d.split('-')
  return `${p[0]}年${parseInt(p[1])}月${parseInt(p[2])}日`
}
function itemKey(item: any, idx: number) {
  return `${item.tmdb_id}-${item.season}-${item.episode}-${idx}`
}
function statusClass(s: string) {
  return s === 'ready' ? 'tag-ready' : s === 'missing' ? 'tag-missing' : s === 'today' ? 'tag-today' : 'tag-pending'
}
function statusLabel(s: string) {
  return s === 'ready' ? '已入库' : s === 'missing' ? '缺失' : s === 'today' ? '今日播出' : '待更新'
}
function onImgErr(e: Event) {
  (e.target as HTMLImageElement).classList.add('hide')
}

function toggleExpand(item: any, idx: number) {
  const key = itemKey(item, idx)
  expandedId.value = expandedId.value === key ? '' : key
}

async function loadData(refresh = false) {
  loading.value = true
  try {
    const api = refresh ? calendarApi.refresh : calendarApi.upcoming
    const res = await api(weekOffset.value)
    const d = res.data?.data ?? res.data
    days.value = d.days || []
    dateRange.value = d.date_range || ''
    Object.assign(stats, d.stats || {})
  } catch (e: any) {
    msg.error('加载日历失败: ' + (e.message || ''))
  } finally {
    loading.value = false
  }
}

function changeWeek(dir: number) {
  weekOffset.value += dir
  expandedId.value = ''
  loadData()
}

async function refresh() {
  await loadData(true)
  msg.success('已刷新')
}

onMounted(() => loadData())
</script>

<style scoped>
.calendar-page { padding: 0.5rem 0; padding-bottom: 120px; }

/* 统计条 */
.stats-bar { display: flex; gap: 0; background: var(--card); border-radius: var(--radius); overflow: hidden; margin-bottom: 0.75rem; box-shadow: 0 1px 6px rgba(0,0,0,0.06); }
.stat-item { flex: 1; text-align: center; padding: 0.75rem 0.25rem; }
.stat-item + .stat-item { border-left: 1px solid var(--border); }
.stat-num { display: block; font-size: 1.3rem; font-weight: 800; color: var(--text); line-height: 1.3; }
.stat-label { font-size: 0.7rem; color: var(--text-muted); }
.num-ready { color: #10b981; }
.num-pending { color: #f59e0b; }

/* 周导航 */
.week-nav { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem; padding: 0 0.25rem; }
.week-btn { background: none; border: none; color: var(--text-muted); cursor: pointer; padding: 6px; border-radius: 8px; display: flex; align-items: center; }
.week-btn:hover { background: var(--bg-secondary); }
.week-label { font-size: 0.9rem; font-weight: 700; color: var(--text); }

/* 日历列表 */
.cal-list { display: flex; flex-direction: column; gap: 12px; }

/* 天卡片 */
.day-card { background: var(--card); border-radius: 14px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.06); border: 2px solid transparent; }
.day-card.today { border-color: var(--brand); box-shadow: 0 2px 16px rgba(59,130,246,0.12); }

/* 日期头部 */
.day-head { display: flex; align-items: center; justify-content: space-between; padding: 14px 16px; border-bottom: 1px solid var(--border); }
.day-left { display: flex; align-items: center; gap: 12px; }
.day-num { font-size: 2rem; font-weight: 800; color: var(--text); line-height: 1; min-width: 44px; text-align: center; }
.today .day-num { color: var(--brand); }
.day-meta { display: flex; flex-direction: column; gap: 2px; }
.day-weekday { font-size: 0.95rem; font-weight: 700; color: var(--text); }
.day-full-date { font-size: 0.75rem; color: var(--text-muted); }
.today-badge { background: var(--brand); color: #fff; font-size: 0.7rem; font-weight: 700; padding: 3px 10px; border-radius: 20px; }
.day-count { font-size: 0.75rem; color: var(--text-muted); font-weight: 600; }

/* 剧集列表 */
.ep-list { padding: 8px 12px; display: flex; flex-direction: column; gap: 8px; }

/* 单集卡片 */
.ep-card { display: flex; flex-wrap: wrap; padding: 10px; border-radius: 12px; cursor: pointer; transition: all 0.2s; }
.ep-card.ready { background: rgba(16,185,129,0.06); }
.ep-card.missing { background: rgba(239,68,68,0.06); }
.ep-card.today { background: rgba(59,130,246,0.06); }
.ep-card.upcoming { background: rgba(245,158,11,0.06); }
.ep-card.expanded { background: rgba(0,0,0,0.04); }
.ep-poster { width: 52px; height: 72px; border-radius: 10px; object-fit: cover; flex-shrink: 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
.ep-poster.hide { display: none; }
.ep-body { flex: 1; min-width: 0; display: flex; flex-direction: column; justify-content: center; gap: 4px; padding-left: 12px; }
.ep-title { font-size: 0.95rem; font-weight: 700; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ep-meta-row { display: flex; align-items: center; gap: 8px; }
.ep-num { font-size: 0.8rem; color: var(--text-muted); font-weight: 600; }
.ep-name { font-size: 0.75rem; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ep-expand-icon { display: flex; align-items: center; padding: 0 4px; color: var(--text-muted); transition: transform 0.2s; }
.ep-card.expanded .ep-expand-icon { transform: rotate(180deg); }

/* 展开详情 */
.ep-detail { width: 100%; padding: 12px 0 4px; border-top: 1px solid var(--border); margin-top: 8px; }
.ep-overview { margin-bottom: 8px; }
.detail-label { font-size: 0.75rem; font-weight: 700; color: var(--text-muted); margin-bottom: 4px; }
.ep-overview p { font-size: 0.82rem; color: var(--text); line-height: 1.6; margin: 0; }
.ep-no-detail { font-size: 0.8rem; color: var(--text-muted); text-align: center; padding: 8px 0; }

/* Tags */
.tag { display: inline-block; padding: 2px 8px; border-radius: 8px; font-size: 0.7rem; font-weight: 700; }
.tag-ready { background: rgba(16,185,129,0.15); color: #10b981; }
.tag-missing { background: rgba(239,68,68,0.15); color: #ef4444; }
.tag-today { background: rgba(59,130,246,0.15); color: #3b82f6; }
.tag-pending { background: rgba(245,158,11,0.15); color: #f59e0b; }

/* 空日 */
.day-empty { display: flex; align-items: center; justify-content: center; padding: 1.2rem 0; color: var(--text-muted); font-size: 0.8rem; opacity: 0.5; }

/* 加载 / 空 */
.loading-wrap, .empty-wrap { display: flex; flex-direction: column; align-items: center; gap: 0.75rem; padding: 4rem 1rem; color: var(--text-muted); font-size: 0.9rem; }

/* FAB */
.fab-refresh { position: fixed; bottom: calc(80px + 1rem); right: 1.5rem; width: 52px; height: 52px; box-shadow: 0 4px 16px rgba(0,122,255,0.3); z-index: 50; }

@media (max-width: 767px) {
  .ep-poster { width: 44px; height: 62px; }
  .day-num { font-size: 1.6rem; min-width: 36px; }
  .fab-refresh { bottom: calc(80px + 0.5rem); right: 1rem; width: 48px; height: 48px; }
}
</style>
