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
        <!-- 周导航 -->
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
        v-for="col in weekData"
        :key="col.dow"
        class="mob-pill"
        :class="{ active: col.date === todayStr }"
        @click="scrollToDay(col.dow)"
      >
        <span class="mob-day">{{ col.label.slice(0, 2) }}</span>
        <span class="mob-num">{{ dayNum(col.date) }}</span>
      </button>
    </div>

    <!-- 7 列网格 -->
    <LoadingState v-if="loading" height="400px" />
    <div v-else class="week-grid">
      <div
        v-for="col in weekData"
        :key="col.dow"
        :id="`day-${col.dow}`"
        class="day-col"
        :class="{ 'is-today': col.date === todayStr }"
      >
        <!-- 列头 -->
        <div class="col-head">
          <span class="col-weekday">{{ col.label }}</span>
          <span class="col-date">{{ formatMD(col.date) }}</span>
          <span v-if="col.entries.length" class="col-count">{{ col.entries.length }}集</span>
        </div>

        <!-- 卡片列表 -->
        <div class="col-cards">
          <div
            v-for="e in col.entries"
            :key="e.id"
            class="show-card"
            @click="openDetail(e)"
          >
            <!-- 竖版海报 2:3 -->
            <div class="card-poster">
              <img
                v-if="e.backdrop_url"
                :src="e.backdrop_url"
                :alt="e.series_name"
                loading="lazy"
              />
              <div v-else class="poster-ph">{{ e.series_name?.charAt(0) }}</div>
              <!-- 状态圆点 -->
              <span class="dot" :class="dotClass(e)"></span>
            </div>
            <!-- 文字 -->
            <div class="card-info">
              <div class="card-title">{{ e.series_name }}</div>
              <div class="card-ep">S{{ pad(e.season_number) }}E{{ pad(e.episode_number) }}</div>
            </div>
          </div>

          <div v-if="!col.entries.length" class="col-empty">无排期</div>
        </div>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <Teleport to="body">
      <div v-if="detail" class="modal-mask" @click.self="detail = null">
        <div class="modal-box">
          <button class="modal-close" @click="detail = null">✕</button>

          <div class="modal-layout">
            <!-- 左侧海报 -->
            <div class="modal-poster">
              <img v-if="detail.backdrop_url" :src="detail.backdrop_url" />
              <div v-else class="poster-ph large">{{ detail.series_name?.charAt(0) }}</div>
            </div>

            <!-- 右侧信息 -->
            <div class="modal-body">
              <h3 class="modal-title">{{ detail.series_name }}</h3>

              <div class="modal-tags">
                <span class="ep-badge">S{{ pad(detail.season_number) }}E{{ pad(detail.episode_number) }}</span>
                <span class="status-badge" :class="badgeClass(detail)">
                  <span class="badge-dot" :class="dotClass(detail)"></span>
                  {{ statusText(detail) }}
                </span>
              </div>

              <div class="modal-date">
                🕐 {{ formatFull(detail.air_date) }}
              </div>

              <p v-if="detail.episode_title" class="modal-ep-title">{{ detail.episode_title }}</p>
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
function formatMD(d: string) { const p = d.split('-'); return `${pad(parseInt(p[1]))}/${pad(parseInt(p[2]))}` }
function formatFull(d: string) { return d ? d.replace(/-/g, '.') : '' }

function dotClass(e: CalendarEntry) {
  if (e.has_file) return 'dot-green'
  if (e.air_date < todayStr) return 'dot-red'
  if (e.air_date === todayStr) return 'dot-blue'
  return 'dot-gray'
}
function badgeClass(e: CalendarEntry) {
  if (e.has_file) return 'badge-green'
  if (e.air_date < todayStr) return 'badge-red'
  if (e.air_date === todayStr) return 'badge-blue'
  return 'badge-gray'
}
function statusText(e: CalendarEntry) {
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
.calendar-page { max-width: 1400px; margin: 0 auto; }

/* ── 头部 ── */
.cal-header {
  display: flex; align-items: center; justify-content: space-between;
  flex-wrap: wrap; gap: 12px; margin-bottom: 20px;
  background: var(--surface); border: 1px solid var(--border); border-radius: 16px;
  padding: 16px 20px; backdrop-filter: blur(20px);
}
.cal-title { display: flex; align-items: center; gap: 12px; }
.cal-icon { font-size: 28px; }
.cal-h2 { font-size: 20px; font-weight: 800; margin: 0; }
.cal-sub { font-size: 12px; color: var(--text-muted); margin: 2px 0 0; }
.cal-actions { display: flex; align-items: center; gap: 12px; }
.week-nav { display: flex; align-items: center; gap: 8px; background: var(--bg-secondary); border-radius: 24px; padding: 4px; }
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

/* ── 7 列网格 ── */
.week-grid {
  display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px;
}
.day-col {
  background: var(--surface); border: 1px solid var(--border); border-radius: 16px;
  overflow: hidden; backdrop-filter: blur(20px);
  display: flex; flex-direction: column;
}
.day-col.is-today { border-color: var(--brand); box-shadow: 0 0 0 1px var(--brand), 0 4px 16px rgba(37, 99, 235, 0.12); }

/* ── 列头 ── */
.col-head {
  padding: 12px 10px 8px; text-align: center;
  border-bottom: 1px solid var(--border); background: var(--bg-secondary);
}
.col-weekday { display: block; font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }
.col-date { display: block; font-size: 13px; font-weight: 600; margin-top: 2px; }
.is-today .col-weekday { color: var(--brand); }
.col-count { display: inline-block; margin-top: 4px; font-size: 10px; font-weight: 700; color: var(--brand); background: var(--brand-light); padding: 1px 8px; border-radius: 10px; }

/* ── 卡片列表 ── */
.col-cards { flex: 1; padding: 8px; display: flex; flex-direction: column; gap: 8px; overflow-y: auto; }

/* ── 单个剧集卡片 ── */
.show-card {
  border-radius: 12px; overflow: hidden; background: var(--bg);
  border: 1px solid var(--border); cursor: pointer;
  transition: all 0.2s;
}
.show-card:hover { border-color: var(--brand); transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.12); }

/* ── 竖版海报 2:3 ── */
.card-poster {
  position: relative; width: 100%; aspect-ratio: 2 / 3;
  overflow: hidden; background: var(--bg-secondary);
}
.card-poster img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.4s; }
.show-card:hover .card-poster img { transform: scale(1.06); }
.poster-ph {
  width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;
  font-size: 32px; font-weight: 800; color: var(--text-muted);
  background: linear-gradient(135deg, var(--brand-light), var(--bg-secondary));
}

/* ── 状态圆点 ── */
.dot {
  position: absolute; top: 8px; right: 8px;
  width: 10px; height: 10px; border-radius: 50%;
  border: 2px solid rgba(255,255,255,0.8);
}
.dot-green { background: #22c55e; }
.dot-red { background: #ef4444; box-shadow: 0 0 6px rgba(239,68,68,0.5); }
.dot-blue { background: #2563eb; box-shadow: 0 0 6px rgba(37,99,235,0.5); animation: pulse-blue 2s infinite; }
.dot-gray { background: #9ca3af; }
@keyframes pulse-blue { 0%,100% { box-shadow: 0 0 6px rgba(37,99,235,0.5); } 50% { box-shadow: 0 0 12px rgba(37,99,235,0.8); } }

/* ── 卡片文字 ── */
.card-info { padding: 10px; }
.card-title { font-size: 12px; font-weight: 700; line-height: 1.3; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.card-ep { font-size: 10px; color: var(--text-muted); margin-top: 4px; font-weight: 600; font-family: monospace; }

/* ── 空列 ── */
.col-empty { text-align: center; padding: 24px 8px; color: var(--text-muted); font-size: 12px; }

/* ── 详情弹窗 ── */
.modal-mask {
  position: fixed; inset: 0; z-index: 1000;
  background: rgba(0,0,0,0.6); backdrop-filter: blur(8px);
  display: flex; align-items: center; justify-content: center; padding: 20px;
}
.modal-box {
  background: var(--surface-strong); border: 1px solid var(--border);
  border-radius: 20px; width: 100%; max-width: 720px; max-height: 90vh;
  overflow: hidden; position: relative; box-shadow: var(--shadow-lg);
}
.modal-close {
  position: absolute; top: 12px; right: 12px; z-index: 10;
  width: 32px; height: 32px; border-radius: 50%; border: none;
  background: rgba(0,0,0,0.4); color: #fff; font-size: 14px;
  cursor: pointer; backdrop-filter: blur(4px);
}
.modal-layout { display: flex; flex-direction: row; }
.modal-poster {
  width: 280px; flex-shrink: 0; aspect-ratio: 2 / 3; overflow: hidden;
  background: var(--bg-secondary);
}
.modal-poster img { width: 100%; height: 100%; object-fit: cover; }
.poster-ph.large { font-size: 64px; }
.modal-body { flex: 1; padding: 28px 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
.modal-title { font-size: 22px; font-weight: 800; line-height: 1.3; margin: 0; }
.modal-tags { display: flex; gap: 8px; flex-wrap: wrap; }
.ep-badge {
  font-size: 12px; font-weight: 700; font-family: monospace;
  padding: 3px 10px; border-radius: 6px;
  background: var(--brand-light); color: var(--brand);
}
.status-badge {
  font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 6px;
  display: flex; align-items: center; gap: 6px;
}
.badge-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.badge-green { background: rgba(34,197,94,0.1); color: #16a34a; }
.badge-red { background: rgba(239,68,68,0.1); color: #dc2626; }
.badge-blue { background: rgba(37,99,235,0.1); color: #2563eb; }
.badge-gray { background: var(--bg-secondary); color: var(--text-muted); }
.modal-date { font-size: 13px; color: var(--text-muted); }
.modal-ep-title { font-size: 14px; font-weight: 600; color: var(--text); margin: 0; }
.modal-desc { font-size: 13px; color: var(--text-soft); line-height: 1.6; margin: 0; }

/* ── 响应式 ── */
@media (max-width: 767px) {
  .mobile-nav { display: flex; }
  .week-grid { grid-template-columns: 1fr; }
  .day-col { border-radius: 12px; }
  .cal-header { padding: 12px 16px; }
  .cal-h2 { font-size: 17px; }
  .week-nav { display: none; }
  .modal-layout { flex-direction: column; }
  .modal-poster { width: 100%; max-height: 240px; aspect-ratio: 16/9; }
}
</style>
