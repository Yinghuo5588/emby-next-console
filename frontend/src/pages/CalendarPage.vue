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
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
      </button>
      <span class="week-label">{{ dateRange }}</span>
      <button class="week-btn" @click="changeWeek(1)">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
      </button>
    </div>

    <!-- 日历网格 -->
    <div class="cal-grid" v-if="!loading">
      <div
        v-for="day in days"
        :key="day.date"
        class="cal-day"
        :class="{ today: day.is_today, empty: day.items.length === 0 }"
      >
        <div class="day-header">
          <div class="day-date">{{ formatDate(day.date) }}</div>
          <div class="day-weekday">{{ day.weekday_cn }}</div>
        </div>
        <div class="day-items">
          <div
            v-for="(item, idx) in day.items"
            :key="`${item.tmdb_id}-${item.season}-${item.episode}-${idx}`"
            class="cal-card"
            :class="item.status"
          >
            <img :src="item.poster_url" class="cal-poster" loading="lazy"
              @error="onImgErr" />
            <div class="cal-info">
              <div class="cal-series">{{ item.series_name }}</div>
              <div class="cal-meta">
                <span class="cal-ep">S{{ pad(item.season) }}E{{ item.episode }}</span>
                <span class="tag" :class="statusClass(item.status)">{{ statusLabel(item.status) }}</span>
              </div>
              <div class="cal-ep-name" v-if="item.episode_name">{{ item.episode_name }}</div>
            </div>
          </div>
          <div v-if="day.items.length === 0" class="empty-day">
            <span>无更新</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 加载 -->
    <div v-if="loading" class="loading-wrap">
      <n-spin size="medium" />
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

function pad(n: any) { return String(n ?? 0).padStart(2, '0') }
function formatDate(d: string) {
  const parts = d.split('-')
  return `${parseInt(parts[1])}/${parseInt(parts[2])}`
}
function statusClass(s: string) {
  return s === 'ready' ? 'tag-ready' : s === 'missing' ? 'tag-missing' : s === 'today' ? 'tag-today' : 'tag-pending'
}
function statusLabel(s: string) {
  return s === 'ready' ? '已入库' : s === 'missing' ? '缺失' : s === 'today' ? '今日' : '待更新'
}
function onImgErr(e: Event) {
  (e.target as HTMLImageElement).classList.add('hide')
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
  loadData()
}

async function refresh() {
  await loadData(true)
  msg.success('已刷新')
}

onMounted(() => loadData())
</script>

<style scoped>
.calendar-page { padding: 0.5rem 0; padding-bottom: 100px; }

/* 统计条 */
.stats-bar { display: flex; gap: 0; background: var(--card); border-radius: var(--radius); overflow: hidden; margin-bottom: 1rem; box-shadow: 0 1px 6px rgba(0,0,0,0.06); }
.stat-item { flex: 1; text-align: center; padding: 0.75rem 0.25rem; }
.stat-item + .stat-item { border-left: 1px solid var(--border); }
.stat-num { display: block; font-size: 1.3rem; font-weight: 800; color: var(--text); line-height: 1.3; }
.stat-label { font-size: 0.7rem; color: var(--text-muted); }
.num-ready { color: #10b981; }
.num-pending { color: #f59e0b; }

/* 周导航 */
.week-nav { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem; padding: 0 0.25rem; }
.week-btn { background: none; border: none; color: var(--text-muted); cursor: pointer; padding: 4px; border-radius: 8px; display: flex; align-items: center; }
.week-btn:hover { background: var(--bg-secondary); }
.week-label { font-size: 0.9rem; font-weight: 700; color: var(--text); }

/* 日历网格 */
.cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px; }
.cal-day { background: var(--card); border-radius: var(--radius); overflow: hidden; min-height: 120px; border: 2px solid transparent; }
.cal-day.today { border-color: var(--brand); background: rgba(59,130,246,0.04); }
.day-header { padding: 6px 8px; border-bottom: 1px solid var(--border); }
.day-date { font-size: 0.85rem; font-weight: 700; color: var(--text); }
.today .day-date { color: var(--brand); }
.day-weekday { font-size: 0.65rem; color: var(--text-muted); }
.day-items { padding: 4px; display: flex; flex-direction: column; gap: 4px; }

/* 卡片 */
.cal-card { display: flex; gap: 6px; padding: 4px; border-radius: 8px; background: var(--bg-secondary); }
.cal-card.ready { background: rgba(16,185,129,0.06); }
.cal-card.missing { background: rgba(239,68,68,0.06); }
.cal-card.today { background: rgba(59,130,246,0.06); }
.cal-card.upcoming { background: rgba(245,158,11,0.06); }
.cal-poster { width: 28px; height: 42px; border-radius: 6px; object-fit: cover; flex-shrink: 0; }
.cal-poster.hide { display: none; }
.cal-info { flex: 1; min-width: 0; }
.cal-series { font-size: 0.7rem; font-weight: 700; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cal-meta { display: flex; align-items: center; gap: 4px; margin-top: 2px; }
.cal-ep { font-size: 0.65rem; color: var(--text-muted); font-weight: 600; }
.cal-ep-name { font-size: 0.6rem; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 1px; }

/* Tags */
.tag { display: inline-block; padding: 0 5px; border-radius: 6px; font-size: 0.6rem; font-weight: 700; line-height: 1.6; }
.tag-ready { background: rgba(16,185,129,0.15); color: #10b981; }
.tag-missing { background: rgba(239,68,68,0.15); color: #ef4444; }
.tag-today { background: rgba(59,130,246,0.15); color: #3b82f6; }
.tag-pending { background: rgba(245,158,11,0.15); color: #f59e0b; }

/* 空日 */
.empty-day { display: flex; align-items: center; justify-content: center; padding: 1rem 0; color: var(--text-muted); font-size: 0.7rem; }
.empty-day span { opacity: 0.4; }

/* 加载 / 空 */
.loading-wrap, .empty-wrap { display: flex; flex-direction: column; align-items: center; gap: 0.75rem; padding: 3rem 1rem; color: var(--text-muted); font-size: 0.85rem; }

/* FAB */
.fab-refresh { position: fixed; bottom: calc(80px + 0.5rem); right: 1.5rem; width: 52px; height: 52px; box-shadow: 0 4px 16px rgba(0,122,255,0.3); z-index: 50; }

@media (max-width: 767px) {
  .cal-grid { grid-template-columns: repeat(7, 1fr); overflow-x: auto; -webkit-overflow-scrolling: touch; }
  .cal-day { min-width: 100px; min-height: 100px; }
  .cal-poster { width: 24px; height: 36px; }
  .fab-refresh { bottom: calc(80px + 0.5rem); right: 1rem; width: 48px; height: 48px; }
}
</style>
