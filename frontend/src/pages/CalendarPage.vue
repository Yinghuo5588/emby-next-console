<template>
  <div class="calendar-page">
    <!-- 页面头部 -->
    <div class="cal-header">
      <div class="cal-title">
        <div class="cal-icon">📅</div>
        <div>
          <h2 class="cal-h2">追剧排期</h2>
          <p class="cal-sub">智能联动 Emby 媒体库状态</p>
        </div>
      </div>
      <div class="cal-actions">
        <div class="week-nav">
          <button class="nav-pill" @click="prevWeek">‹</button>
          <span class="week-range">{{ weekRange }}</span>
          <button class="nav-pill" @click="nextWeek">›</button>
        </div>
        <button class="sync-btn" :disabled="syncing" @click="doSync">
          🔄 {{ syncing ? '同步中...' : '同步' }}
        </button>
      </div>
    </div>

    <!-- 移动端横向日期导航 -->
    <div class="mobile-nav">
      <button
        v-for="col in weekData" :key="col.dow"
        class="mob-pill" :class="{ active: col.date === todayStr }"
        @click="scrollToDay(col.dow)"
      >
        <span class="mob-day">{{ col.label.slice(0, 2) }}</span>
        <span class="mob-num">{{ dayNum(col.date) }}</span>
      </button>
    </div>

    <LoadingState v-if="loading" height="400px" />

    <!-- 按日期分组的纵向列表 -->
    <div v-else class="day-groups">
      <div
        v-for="col in weekData" :key="col.dow"
        :id="`day-${col.dow}`" class="day-group"
      >
        <!-- 组标题 -->
        <div class="group-head">
          <span class="group-label">{{ col.label }}</span>
          <span class="group-date">{{ formatMD(col.date) }}</span>
          <span v-if="col.date === todayStr" class="today-tag">今日更新</span>
          <div class="group-line"></div>
        </div>

        <!-- 剧集条目列表 -->
        <div v-if="col.entries.length" class="entries">
          <div
            v-for="e in col.entries" :key="e.id"
            class="ep-card" @click="openDetail(e)"
          >
            <!-- 左侧封面 -->
            <div class="ep-poster">
              <img
                v-if="e.backdrop_url" :src="e.backdrop_url" :alt="e.series_name"
                loading="lazy"
              />
              <div v-else class="poster-ph">{{ e.series_name?.charAt(0) }}</div>
            </div>

            <!-- 右侧信息 -->
            <div class="ep-body">
              <div class="ep-top">
                <h3 class="ep-name">{{ e.series_name }}</h3>
                <span class="ep-date">{{ formatMD(e.air_date) }}</span>
              </div>
              <span class="ep-tag">S{{ pad(e.season_number) }}E{{ pad(e.episode_number) }}</span>
              <p v-if="e.episode_title" class="ep-subtitle">{{ e.episode_title }}</p>
              <p v-if="e.overview" class="ep-desc">{{ e.overview }}</p>
              <span class="status-tag" :class="statusClass(e)">{{ statusLabel(e) }}</span>
            </div>
          </div>
        </div>

        <div v-else class="day-empty">无排期</div>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <Teleport to="body">
      <div v-if="detail" class="modal-mask" @click.self="detail = null">
        <div class="modal-box">
          <button class="modal-close" @click="detail = null">✕</button>
          <div class="modal-row">
            <div class="modal-poster">
              <img v-if="detail.backdrop_url" :src="detail.backdrop_url" />
              <div v-else class="poster-ph large">{{ detail.series_name?.charAt(0) }}</div>
            </div>
            <div class="modal-body">
              <h3 class="modal-title">{{ detail.series_name }}</h3>
              <div class="modal-tags">
                <span class="ep-badge">S{{ pad(detail.season_number) }}E{{ pad(detail.episode_number) }}</span>
                <span class="status-tag" :class="statusClass(detail)">{{ statusLabel(detail) }}</span>
              </div>
              <div class="modal-date">🕐 {{ formatFull(detail.air_date) }}</div>
              <p v-if="detail.episode_title" class="modal-ep-subtitle">{{ detail.episode_title }}</p>
              <p v-if="detail.overview" class="modal-desc">{{ detail.overview }}</p>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import LoadingState from '@/components/common/LoadingState.vue'
import { calendarApi } from '@/api/calendar'
import type { CalendarEntry, WeekWaterfallItem } from '@/api/calendar'

const today = new Date()
const year = ref(today.getFullYear())
const month = ref(today.getMonth() + 1)
const week = ref(Math.ceil((today.getDate() + new Date(year.value, month.value - 1, 1).getDay()) / 7))

const loading = ref(true)
const syncing = ref(false)
const weekData = ref<WeekWaterfallItem[]>([])
const detail = ref<CalendarEntry | null>(null)

const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`

const weekRange = computed(() => {
  if (!weekData.value.length) return ''
  const s = weekData.value[0].date
  const e = weekData.value[weekData.value.length - 1]?.date || s
  return `${s.slice(5).replace('-', '/')} — ${e.slice(5).replace('-', '/')}`
})

function pad(n: number) { return String(n).padStart(2, '0') }
function dayNum(d: string) { return parseInt(d.split('-')[2]).toString() }
function formatMD(d: string) { if (!d) return ''; const p = d.split('-'); return `${pad(parseInt(p[1]))}-${pad(parseInt(p[2]))}` }
function formatFull(d: string) { return d ? d.replace(/-/g, '.') : '' }

function statusClass(e: CalendarEntry) {
  if (e.has_file) return 'st-ready'
  if (e.air_date < todayStr) return 'st-missing'
  if (e.air_date === todayStr) return 'st-today'
  return 'st-upcoming'
}
function statusLabel(e: CalendarEntry) {
  if (e.has_file) return '已入库'
  if (e.air_date < todayStr) return '待补货'
  if (e.air_date === todayStr) return '今日更新'
  return '待更新'
}

async function loadWeek() {
  loading.value = true
  try {
    const res = await calendarApi.week(year.value, month.value, week.value)
    weekData.value = res.data?.waterfall ?? []
  } finally { loading.value = false }
}
async function doSync() {
  syncing.value = true
  try { await calendarApi.sync(); await loadWeek() }
  finally { syncing.value = false }
}
function prevWeek() {
  if (week.value > 1) week.value--
  else { if (month.value === 1) { year.value--; month.value = 12 } else month.value--; week.value = 4 }
}
function nextWeek() {
  if (week.value < 5) week.value++
  else { if (month.value === 12) { year.value++; month.value = 1 } else month.value++; week.value = 1 }
}
function scrollToDay(dow: number) {
  document.getElementById(`day-${dow}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
function openDetail(e: CalendarEntry) { detail.value = e }

watch([year, month, week], loadWeek)
onMounted(loadWeek)
</script>

<style scoped>
.calendar-page { max-width: 960px; margin: 0 auto; }

/* ── 头部 ── */
.cal-header {
  display: flex; align-items: center; justify-content: space-between;
  flex-wrap: wrap; gap: 12px; margin-bottom: 20px;
  background: var(--surface); border: 1px solid var(--border); border-radius: 16px;
  padding: 16px 20px;
}
.cal-title { display: flex; align-items: center; gap: 12px; }
.cal-icon { font-size: 28px; }
.cal-h2 { font-size: 20px; font-weight: 800; margin: 0; }
.cal-sub { font-size: 12px; color: var(--text-muted); margin: 2px 0 0; }
.cal-actions { display: flex; align-items: center; gap: 12px; }
.week-nav {
  display: flex; align-items: center; gap: 8px;
  background: var(--bg-secondary); border-radius: 24px; padding: 4px;
}
.nav-pill {
  width: 32px; height: 32px; border-radius: 50%; border: none;
  background: transparent; color: var(--text-muted); font-size: 16px;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: all 0.15s;
}
.nav-pill:hover { background: var(--brand-light); color: var(--brand); }
.week-range { font-size: 13px; font-weight: 700; min-width: 120px; text-align: center; }
.sync-btn {
  padding: 8px 16px; border-radius: 24px; border: 1px solid var(--border);
  background: var(--brand); color: #fff; font-size: 13px; font-weight: 600;
  cursor: pointer; transition: all 0.15s;
}
.sync-btn:hover { opacity: 0.85; }
.sync-btn:disabled { opacity: 0.5; }

/* ── 移动端日期导航 ── */
.mobile-nav {
  display: none; gap: 6px; overflow-x: auto; padding: 8px 0 16px;
  -webkit-overflow-scrolling: touch;
}
.mobile-nav::-webkit-scrollbar { display: none; }
.mob-pill {
  flex-shrink: 0; display: flex; flex-direction: column; align-items: center;
  gap: 2px; padding: 8px 14px; border-radius: 12px; border: none;
  background: var(--bg-secondary); cursor: pointer; transition: all 0.2s;
}
.mob-pill.active { background: var(--brand); color: #fff; }
.mob-pill .mob-day { font-size: 11px; font-weight: 600; }
.mob-pill .mob-num { font-size: 16px; font-weight: 800; }

/* ── 日期分组 ── */
.day-groups { display: flex; flex-direction: column; gap: 24px; }
.day-group { scroll-margin-top: 80px; }
.group-head {
  display: flex; align-items: center; gap: 8px; margin-bottom: 12px;
}
.group-label { font-size: 16px; font-weight: 800; }
.group-date { font-size: 13px; color: var(--text-muted); font-weight: 600; font-family: monospace; }
.today-tag {
  font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 6px;
  background: var(--brand-light); color: var(--brand);
}
.group-line { flex: 1; height: 1px; background: var(--border); }

/* ── 条目列表 ── */
.entries { display: flex; flex-direction: column; gap: 10px; }

/* ── 单条剧集卡片（横排：封面左 + 信息右） ── */
.ep-card {
  display: flex; gap: 14px;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 14px; padding: 14px;
  cursor: pointer; transition: all 0.2s;
}
.ep-card:hover {
  border-color: var(--brand);
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
  transform: translateY(-1px);
}

/* ── 左侧封面（竖版） ── */
.ep-poster {
  width: 72px; flex-shrink: 0; aspect-ratio: 2 / 3;
  border-radius: 10px; overflow: hidden; background: var(--bg-secondary);
}
.ep-poster img { width: 100%; height: 100%; object-fit: cover; display: block; }
.poster-ph {
  width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;
  font-size: 24px; font-weight: 800; color: var(--text-muted);
  background: linear-gradient(135deg, var(--brand-light), var(--bg-secondary));
}
.poster-ph.large { font-size: 48px; }

/* ── 右侧信息区 ── */
.ep-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 5px; }
.ep-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; }
.ep-name {
  font-size: 15px; font-weight: 700; line-height: 1.3;
  flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.ep-date { font-size: 12px; color: var(--text-muted); flex-shrink: 0; margin-top: 2px; font-family: monospace; }
.ep-tag {
  display: inline-flex; align-self: flex-start;
  padding: 1px 8px; font-size: 11px; font-weight: 700; font-family: monospace;
  background: var(--brand-light); color: var(--brand); border-radius: 5px;
}
.ep-subtitle {
  font-size: 12px; color: var(--text-muted); margin: 0; line-height: 1.3;
  font-weight: 500;
}
.ep-desc {
  font-size: 12px; color: var(--text-muted); margin: 0; line-height: 1.5;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ── 状态标签 ── */
.status-tag {
  display: inline-flex; align-self: flex-start;
  padding: 2px 10px; font-size: 10px; font-weight: 700; border-radius: 6px;
  margin-top: auto; gap: 5px; align-items: center;
}
.st-ready { background: rgba(34,197,94,0.12); color: #16a34a; }
.st-missing { background: rgba(239,68,68,0.12); color: #dc2626; }
.st-today { background: rgba(37,99,235,0.12); color: #2563eb; }
.st-upcoming { background: var(--bg-secondary); color: var(--text-muted); }

/* ── 空日期 ── */
.day-empty {
  text-align: center; padding: 20px; color: var(--text-muted); font-size: 12px;
  border-radius: 12px; border: 1px dashed var(--border);
}

/* ── 详情弹窗 ── */
.modal-mask {
  position: fixed; inset: 0; z-index: 1000;
  background: rgba(0,0,0,0.6); backdrop-filter: blur(8px);
  display: flex; align-items: center; justify-content: center; padding: 20px;
}
.modal-box {
  background: var(--surface-strong, var(--surface)); border: 1px solid var(--border);
  border-radius: 20px; width: 100%; max-width: 680px; max-height: 85vh;
  overflow: hidden; position: relative; box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}
.modal-close {
  position: absolute; top: 12px; right: 12px; z-index: 10;
  width: 32px; height: 32px; border-radius: 50%; border: none;
  background: rgba(0,0,0,0.4); color: #fff; font-size: 14px;
  cursor: pointer; backdrop-filter: blur(4px);
}
.modal-row { display: flex; }
.modal-poster {
  width: 240px; flex-shrink: 0; aspect-ratio: 2 / 3;
  overflow: hidden; background: var(--bg-secondary);
}
.modal-poster img { width: 100%; height: 100%; object-fit: cover; }
.modal-body {
  flex: 1; padding: 24px 20px; overflow-y: auto;
  display: flex; flex-direction: column; gap: 10px;
}
.modal-title { font-size: 20px; font-weight: 800; line-height: 1.3; margin: 0; }
.modal-tags { display: flex; gap: 8px; flex-wrap: wrap; }
.ep-badge {
  font-size: 12px; font-weight: 700; font-family: monospace;
  padding: 3px 10px; border-radius: 6px;
  background: var(--brand-light); color: var(--brand);
}
.modal-date { font-size: 13px; color: var(--text-muted); }
.modal-ep-subtitle { font-size: 14px; font-weight: 600; margin: 0; }
.modal-desc { font-size: 13px; color: var(--text-muted); line-height: 1.6; margin: 0; }

/* ── 响应式 ── */
@media (max-width: 767px) {
  .mobile-nav { display: flex; }
  .week-nav { display: none; }
  .cal-header { padding: 12px 16px; }
  .cal-h2 { font-size: 17px; }
  .ep-card { padding: 10px; gap: 10px; }
  .ep-poster { width: 60px; }
  .ep-name { font-size: 14px; }
  .ep-desc { -webkit-line-clamp: 2; }
  .modal-row { flex-direction: column; }
  .modal-poster { width: 100%; max-height: 200px; aspect-ratio: 16/9; }
}
</style>
