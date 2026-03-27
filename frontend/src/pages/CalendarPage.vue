<template>
  <div class="calendar-page">
    <PageHeader title="追剧日历" />

    <!-- 统计条：KPI 风格 -->
    <div class="kpi-bar" v-if="!loading">
      <div class="kpi-item" style="--i:0">
        <div class="kpi-icon kpi-brand"><IosIcon name="film" :size="16" color="#fff" :stroke-width="2" /></div>
        <div class="kpi-body"><span class="kpi-val">{{ seriesCount }}</span><span class="kpi-lbl">连载中</span></div>
      </div>
      <div class="kpi-item" style="--i:1">
        <div class="kpi-icon kpi-blue"><IosIcon name="calendar" :size="16" color="#fff" :stroke-width="2" /></div>
        <div class="kpi-body"><span class="kpi-val">{{ upcomingCount }}</span><span class="kpi-lbl">本周更新</span></div>
      </div>
      <div class="kpi-item" style="--i:2">
        <div class="kpi-icon kpi-green"><IosIcon name="check" :size="16" color="#fff" :stroke-width="2" /></div>
        <div class="kpi-body"><span class="kpi-val">{{ readyCount }}</span><span class="kpi-lbl">已入库</span></div>
      </div>
      <div class="kpi-item" style="--i:3">
        <div class="kpi-icon kpi-orange"><IosIcon name="clock" :size="16" color="#fff" :stroke-width="2" /></div>
        <div class="kpi-body"><span class="kpi-val">{{ pendingCount }}</span><span class="kpi-lbl">待入库</span></div>
      </div>
    </div>

    <!-- 骨架屏 -->
    <template v-if="loading">
      <div class="skel-bar">
        <div v-for="i in 4" :key="i" class="skel-kpi" />
      </div>
      <div v-for="i in 3" :key="i" class="skel-day" style="--i:0">
        <div class="skel-head" />
        <div class="skel-ep" />
        <div class="skel-ep" />
      </div>
      <div class="loading-hint">同步 TMDB 排期中…首次加载可能较慢</div>
    </template>

    <!-- 周导航 -->
    <div class="week-nav" v-if="!loading">
      <button class="week-btn" @click="changeWeek(-1)">
        <IosIcon name="search" :size="18" color="var(--text-muted)" :stroke-width="2.5" style="transform:rotate(90deg)" />
      </button>
      <div class="week-center">
        <span class="week-label">{{ dateRange }}</span>
        <span v-if="weekOffset === 0" class="week-badge">本周</span>
      </div>
      <button class="week-btn" @click="changeWeek(1)">
        <IosIcon name="search" :size="18" color="var(--text-muted)" :stroke-width="2.5" style="transform:rotate(-90deg)" />
      </button>
    </div>

    <!-- 日历列表 -->
    <div class="cal-list" v-if="!loading">
      <div
        v-for="(day, di) in days"
        :key="day.date"
        class="day-card anim-in"
        :class="{ today: day.is_today }"
        :style="{ '--i': di }"
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
            <!-- 状态竖条 -->
            <div class="ep-status-bar" :class="'bar-' + item.status" />

            <img :src="item.poster_url" class="ep-poster" loading="lazy" @error="onImgErr" />
            <div class="ep-body">
              <div class="ep-title">{{ item.series_name }}</div>
              <div class="ep-meta-row">
                <span class="ep-num">S{{ pad(item.season) }}E{{ item.episode }}</span>
                <span class="tag" :class="statusClass(item.status)">{{ statusLabel(item.status) }}</span>
              </div>
              <div class="ep-name" v-if="item.episode_name">{{ item.episode_name }}</div>
            </div>
            <div class="ep-expand-icon" :class="{ rotated: expandedId === itemKey(item, idx) }">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M6 9l6 6 6-6"/></svg>
            </div>

            <!-- 展开详情 -->
            <Transition name="expand">
              <div class="ep-detail" v-if="expandedId === itemKey(item, idx)">
                <div class="ep-overview" v-if="item.series_overview">
                  <div class="detail-label">剧集简介</div>
                  <p>{{ item.series_overview }}</p>
                </div>
                <div class="ep-overview" v-if="item.ep_overview">
                  <div class="detail-label">本集简介</div>
                  <p>{{ item.ep_overview }}</p>
                </div>
                <div class="ep-no-detail" v-if="!item.series_overview && !item.ep_overview">暂无简介</div>
              </div>
            </Transition>
          </div>
        </div>

        <!-- 空日 -->
        <div class="day-empty" v-else>
          <span>无更新</span>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!loading && days.length === 0" class="empty-wrap">
      <IosIcon name="calendar" :size="42" color="var(--text-muted)" :stroke-width="1.2" />
      <p>这周没有剧集更新</p>
    </div>

    <!-- 刷新 FAB -->
    <n-button class="fab-refresh" type="primary" circle size="large" @click="refresh" :loading="loading">
      <n-icon size="20"><svg :class="{ spinning: loading }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M23 4v6h-6"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg></n-icon>
    </n-button>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useMessage } from 'naive-ui'
import PageHeader from '@/components/common/PageHeader.vue'
import IosIcon from '@/components/common/IosIcon.vue'
import { useCountUp } from '@/composables/useCountUp'
import { calendarApi } from '@/api/calendar'

const msg = useMessage()
const loading = ref(true)
const weekOffset = ref(0)
const days = ref<any[]>([])
const dateRange = ref('')
const stats = reactive({ total_series: 0, total_upcoming: 0, ready: 0, pending: 0 })
const expandedId = ref('')

// Count-up
const seriesCount = useCountUp(computed(() => loading.value ? undefined : stats.total_series))
const upcomingCount = useCountUp(computed(() => loading.value ? undefined : stats.total_upcoming))
const readyCount = useCountUp(computed(() => loading.value ? undefined : stats.ready))
const pendingCount = useCountUp(computed(() => loading.value ? undefined : stats.pending))

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

/* ── 入场动画 ── */
.anim-in {
  opacity: 0; transform: translateY(14px);
  animation: cardIn 0.45s cubic-bezier(0.22, 1, 0.36, 1) forwards;
  animation-delay: calc(var(--i, 0) * 60ms);
}
@keyframes cardIn { to { opacity: 1; transform: translateY(0); } }

/* ── KPI 统计条 ── */
.kpi-bar { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.5rem; margin-bottom: 0.75rem; }
.kpi-item {
  display: flex; align-items: center; gap: 0.5rem;
  background: var(--surface); border-radius: 12px; padding: 0.65rem;
  border: 1px solid var(--border);
  opacity: 0; animation: cardIn 0.4s cubic-bezier(0.22,1,0.36,1) forwards;
  animation-delay: calc(var(--i, 0) * 50ms);
}
.kpi-icon { width: 30px; height: 30px; border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.kpi-brand { background: linear-gradient(135deg, #0A84FF, #0055D6); }
.kpi-blue { background: linear-gradient(135deg, #5AC8FA, #007AFF); }
.kpi-green { background: linear-gradient(135deg, #34C759, #248A3D); }
.kpi-orange { background: linear-gradient(135deg, #FF9F0A, #E08600); }
.kpi-body { display: flex; flex-direction: column; }
.kpi-val { font-size: 1.1rem; font-weight: 800; color: var(--text); line-height: 1.2; font-variant-numeric: tabular-nums; }
.kpi-lbl { font-size: 0.6rem; color: var(--text-muted); }

/* ── 骨架屏 ── */
.skel-bar { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.5rem; margin-bottom: 0.75rem; }
.skel-kpi {
  height: 56px; border-radius: 12px;
  background: linear-gradient(90deg, var(--bg-secondary) 25%, var(--bg) 50%, var(--bg-secondary) 75%);
  background-size: 200% 100%; animation: shimmer 1.5s infinite;
}
.skel-day {
  border-radius: 14px; overflow: hidden; margin-bottom: 12px;
  background: var(--surface); border: 1px solid var(--border);
  opacity: 0; animation: cardIn 0.4s ease forwards;
  animation-delay: calc(var(--i, 0) * 80ms);
}
.skel-head { height: 56px; background: linear-gradient(90deg, var(--bg-secondary) 25%, var(--bg) 50%, var(--bg-secondary) 75%); background-size: 200% 100%; animation: shimmer 1.5s infinite; }
.skel-ep { height: 72px; margin: 8px 12px; border-radius: 10px; background: linear-gradient(90deg, var(--bg-secondary) 25%, var(--bg) 50%, var(--bg-secondary) 75%); background-size: 200% 100%; animation: shimmer 1.5s infinite; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
.loading-hint { text-align: center; color: var(--text-muted); font-size: 0.8rem; padding: 1rem 0 2rem; opacity: 0.6; }

/* ── 周导航 ── */
.week-nav { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem; padding: 0 0.25rem; }
.week-btn { background: none; border: none; color: var(--text-muted); cursor: pointer; padding: 6px; border-radius: 8px; display: flex; align-items: center; transition: background 0.15s; }
.week-btn:active { background: var(--bg-secondary); }
.week-center { display: flex; align-items: center; gap: 8px; }
.week-label { font-size: 0.9rem; font-weight: 700; color: var(--text); }
.week-badge { font-size: 0.6rem; font-weight: 700; padding: 2px 6px; border-radius: 4px; background: rgba(0,122,255,0.1); color: var(--brand); }

/* ── 日历列表 ── */
.cal-list { display: flex; flex-direction: column; gap: 12px; }

/* ── 天卡片 ── */
.day-card { background: var(--surface); border-radius: 14px; overflow: hidden; box-shadow: 0 1px 6px rgba(0,0,0,0.04); border: 1.5px solid transparent; transition: border-color 0.3s, box-shadow 0.3s; }
.day-card.today { border-color: var(--brand); box-shadow: 0 2px 16px rgba(0,122,255,0.1); }

/* ── 日期头部 ── */
.day-head { display: flex; align-items: center; justify-content: space-between; padding: 12px 14px; border-bottom: 0.5px solid var(--border); }
.day-left { display: flex; align-items: center; gap: 10px; }
.day-num { font-size: 1.8rem; font-weight: 800; color: var(--text); line-height: 1; min-width: 40px; text-align: center; font-variant-numeric: tabular-nums; }
.today .day-num { color: var(--brand); }
.day-meta { display: flex; flex-direction: column; gap: 1px; }
.day-weekday { font-size: 0.9rem; font-weight: 700; color: var(--text); }
.day-full-date { font-size: 0.7rem; color: var(--text-muted); }
.today-badge { background: var(--brand); color: #fff; font-size: 0.65rem; font-weight: 700; padding: 3px 10px; border-radius: 20px; }
.day-count { font-size: 0.72rem; color: var(--text-muted); font-weight: 600; }

/* ── 剧集列表 ── */
.ep-list { padding: 6px 10px; display: flex; flex-direction: column; gap: 6px; }

/* ── 单集卡片 ── */
.ep-card { display: flex; flex-wrap: wrap; padding: 10px; padding-left: 13px; border-radius: 10px; cursor: pointer; transition: all 0.2s; position: relative; overflow: hidden; }
.ep-card.ready { background: rgba(16,185,129,0.05); }
.ep-card.missing { background: rgba(239,68,68,0.05); }
.ep-card.today { background: rgba(59,130,246,0.05); }
.ep-card.upcoming { background: rgba(245,158,11,0.05); }
.ep-card:active { transform: scale(0.98); }

/* 状态竖条 */
.ep-status-bar { position: absolute; left: 0; top: 8px; bottom: 8px; width: 3px; border-radius: 2px; }
.bar-ready { background: #10b981; }
.bar-missing { background: #ef4444; }
.bar-today { background: #3b82f6; }
.bar-upcoming { background: #f59e0b; }

.ep-poster { width: 48px; height: 68px; border-radius: 8px; object-fit: cover; flex-shrink: 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-left: 4px; }
.ep-poster.hide { display: none; }
.ep-body { flex: 1; min-width: 0; display: flex; flex-direction: column; justify-content: center; gap: 3px; padding-left: 10px; }
.ep-title { font-size: 0.9rem; font-weight: 700; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ep-meta-row { display: flex; align-items: center; gap: 6px; }
.ep-num { font-size: 0.75rem; color: var(--text-muted); font-weight: 600; font-variant-numeric: tabular-nums; }
.ep-name { font-size: 0.72rem; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ep-expand-icon { display: flex; align-items: center; padding: 0 2px; color: var(--text-muted); transition: transform 0.25s cubic-bezier(0.4,0,0.2,1); }
.ep-expand-icon.rotated { transform: rotate(180deg); }

/* ── 展开详情过渡 ── */
.expand-enter-active, .expand-leave-active { transition: all 0.25s ease; overflow: hidden; }
.expand-enter-from, .expand-leave-to { opacity: 0; max-height: 0; }
.expand-enter-to, .expand-leave-from { opacity: 1; max-height: 300px; }

.ep-detail { width: 100%; padding: 10px 0 2px; border-top: 0.5px solid var(--border); margin-top: 6px; }
.ep-overview { margin-bottom: 6px; }
.detail-label { font-size: 0.7rem; font-weight: 700; color: var(--text-muted); margin-bottom: 3px; }
.ep-overview p { font-size: 0.8rem; color: var(--text); line-height: 1.6; margin: 0; }
.ep-no-detail { font-size: 0.78rem; color: var(--text-muted); text-align: center; padding: 6px 0; }

/* Tags */
.tag { display: inline-block; padding: 1px 6px; border-radius: 4px; font-size: 0.65rem; font-weight: 700; line-height: 1.5; }
.tag-ready { background: rgba(16,185,129,0.12); color: #10b981; }
.tag-missing { background: rgba(239,68,68,0.12); color: #ef4444; }
.tag-today { background: rgba(59,130,246,0.12); color: #3b82f6; }
.tag-pending { background: rgba(245,158,11,0.12); color: #f59e0b; }

/* ── 空日 ── */
.day-empty { display: flex; align-items: center; justify-content: center; padding: 1rem 0; color: var(--text-muted); font-size: 0.75rem; opacity: 0.4; }

/* ── 空状态 ── */
.empty-wrap { display: flex; flex-direction: column; align-items: center; gap: 0.75rem; padding: 4rem 1rem; color: var(--text-muted); font-size: 0.9rem; }

/* ── FAB ── */
.fab-refresh {
  position: fixed; bottom: calc(80px + 1rem); right: 1.5rem;
  width: 52px; height: 52px;
  box-shadow: 0 4px 16px rgba(0,122,255,0.3);
  z-index: 50; transition: transform 0.15s;
}
.fab-refresh:active { transform: scale(0.9); }
.spinning { animation: spin 0.8s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

@media (max-width: 767px) {
  .kpi-bar { grid-template-columns: repeat(2, 1fr); }
  .ep-poster { width: 40px; height: 56px; }
  .day-num { font-size: 1.5rem; min-width: 32px; }
  .fab-refresh { bottom: calc(80px + 0.5rem); right: 1rem; width: 48px; height: 48px; }
}
</style>
