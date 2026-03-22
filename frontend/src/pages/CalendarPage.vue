<template>
  <div class="calendar-page">
    <!-- 页面头部 -->
    <n-card size="small" style="margin-bottom:20px">
      <div class="cal-header">
        <div class="cal-title">
          <span style="font-size:28px">📅</span>
          <div>
            <div style="font-size:20px;font-weight:800">追剧排期</div>
            <div style="font-size:12px;color:var(--text-muted)">智能联动 Emby 媒体库状态</div>
          </div>
        </div>
        <div class="cal-actions">
          <n-button-group size="small">
            <n-button quaternary @click="prevWeek">‹</n-button>
            <n-button quaternary disabled style="min-width:120px;font-weight:700">{{ weekRange }}</n-button>
            <n-button quaternary @click="nextWeek">›</n-button>
          </n-button-group>
          <n-button type="primary" size="small" :loading="syncing" round @click="doSync">🔄 同步</n-button>
        </div>
      </div>
    </n-card>

    <!-- 移动端横向日期导航 -->
    <div class="mobile-nav">
      <button v-for="col in weekData" :key="col.dow" class="mob-pill" :class="{ active: col.date === todayStr }" @click="scrollToDay(col.dow)">
        <span class="mob-day">{{ col.label.slice(0, 2) }}</span>
        <span class="mob-num">{{ dayNum(col.date) }}</span>
      </button>
    </div>

    <LoadingState v-if="loading" height="400px" />

    <div v-else class="day-groups">
      <div v-for="col in weekData" :key="col.dow" :id="`day-${col.dow}`" class="day-group">
        <div class="group-head">
          <span class="group-label">{{ col.label }}</span>
          <span class="group-date">{{ formatMD(col.date) }}</span>
          <n-tag v-if="col.date === todayStr" type="info" size="tiny" round>今日更新</n-tag>
          <div class="group-line"></div>
        </div>

        <div v-if="col.entries.length" class="entries">
          <n-card v-for="e in col.entries" :key="e.id" size="small" class="ep-card" hoverable @click="openDetail(e)">
            <div class="ep-inner">
              <div class="ep-poster">
                <img v-if="e.backdrop_url" :src="e.backdrop_url" :alt="e.series_name" loading="lazy" />
                <div v-else class="poster-ph">{{ e.series_name?.charAt(0) }}</div>
              </div>
              <div class="ep-body">
                <div class="ep-top">
                  <div class="ep-name">{{ e.series_name }}</div>
                  <span class="ep-date">{{ formatMD(e.air_date) }}</span>
                </div>
                <n-tag size="tiny" round style="font-family:monospace">S{{ pad(e.season_number) }}E{{ pad(e.episode_number) }}</n-tag>
                <div v-if="e.episode_title" class="ep-subtitle">{{ e.episode_title }}</div>
                <div v-if="e.overview" class="ep-desc">{{ e.overview }}</div>
                <n-tag :type="statusType(e)" size="tiny" round>{{ statusLabel(e) }}</n-tag>
              </div>
            </div>
          </n-card>
        </div>
        <div v-else class="day-empty">无排期</div>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <n-modal v-model:show="showDetail" preset="card" style="max-width:680px;padding:0" :bordered="false">
      <template v-if="detail">
        <div class="modal-row">
          <div class="modal-poster">
            <img v-if="detail.backdrop_url" :src="detail.backdrop_url" />
            <div v-else class="poster-ph large">{{ detail.series_name?.charAt(0) }}</div>
          </div>
          <div class="modal-body">
            <div style="font-size:20px;font-weight:800">{{ detail.series_name }}</div>
            <div style="display:flex;gap:8px;flex-wrap:wrap">
              <n-tag size="small" round style="font-family:monospace">S{{ pad(detail.season_number) }}E{{ pad(detail.episode_number) }}</n-tag>
              <n-tag :type="statusType(detail)" size="small" round>{{ statusLabel(detail) }}</n-tag>
            </div>
            <div style="font-size:13px;color:var(--text-muted)">🕐 {{ formatFull(detail.air_date) }}</div>
            <div v-if="detail.episode_title" style="font-size:14px;font-weight:600">{{ detail.episode_title }}</div>
            <p v-if="detail.overview" style="font-size:13px;color:var(--text-muted);line-height:1.6">{{ detail.overview }}</p>
          </div>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { NCard, NButton, NButtonGroup, NTag, NModal } from 'naive-ui'
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
const showDetail = ref(false)

const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
const weekRange = computed(() => { if (!weekData.value.length) return ''; const s = weekData.value[0].date; const e = weekData.value[weekData.value.length - 1]?.date || s; return `${s.slice(5).replace('-', '/')} — ${e.slice(5).replace('-', '/')}` })

function pad(n: number) { return String(n).padStart(2, '0') }
function dayNum(d: string) { return parseInt(d.split('-')[2]).toString() }
function formatMD(d: string) { if (!d) return ''; const p = d.split('-'); return `${pad(parseInt(p[1]))}-${pad(parseInt(p[2]))}` }
function formatFull(d: string) { return d ? d.replace(/-/g, '.') : '' }

function statusType(e: CalendarEntry) { if (e.has_file) return 'success' as any; if (e.air_date < todayStr) return 'error' as any; if (e.air_date === todayStr) return 'info' as any; return 'default' as any }
function statusLabel(e: CalendarEntry) { if (e.has_file) return '已入库'; if (e.air_date < todayStr) return '待补货'; if (e.air_date === todayStr) return '今日更新'; return '待更新' }

async function loadWeek() { loading.value = true; try { weekData.value = (await calendarApi.week(year.value, month.value, week.value)).data?.waterfall ?? [] } finally { loading.value = false } }
async function doSync() { syncing.value = true; try { await calendarApi.sync(); await loadWeek() } finally { syncing.value = false } }
function prevWeek() { if (week.value > 1) week.value--; else { if (month.value === 1) { year.value--; month.value = 12 } else month.value--; week.value = 4 } }
function nextWeek() { if (week.value < 5) week.value++; else { if (month.value === 12) { year.value++; month.value = 1 } else month.value++; week.value = 1 } }
function scrollToDay(dow: number) { document.getElementById(`day-${dow}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' }) }
function openDetail(e: CalendarEntry) { detail.value = e; showDetail.value = true }

watch([year, month, week], loadWeek)
onMounted(loadWeek)
</script>

<style scoped>
.calendar-page { max-width: 960px; margin: 0 auto; }
.cal-header { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; }
.cal-title { display: flex; align-items: center; gap: 12px; }
.cal-actions { display: flex; align-items: center; gap: 12px; }
.mobile-nav { display: none; gap: 6px; overflow-x: auto; padding: 8px 0 16px; }
.mobile-nav::-webkit-scrollbar { display: none; }
.mob-pill { flex-shrink: 0; display: flex; flex-direction: column; align-items: center; gap: 2px; padding: 8px 14px; border-radius: 12px; border: none; background: var(--bg-secondary); cursor: pointer; transition: all 0.2s; }
.mob-pill.active { background: var(--brand); color: #fff; }
.mob-day { font-size: 11px; font-weight: 600; }
.mob-num { font-size: 16px; font-weight: 800; }
.day-groups { display: flex; flex-direction: column; gap: 24px; }
.day-group { scroll-margin-top: 80px; }
.group-head { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.group-label { font-size: 16px; font-weight: 800; }
.group-date { font-size: 13px; color: var(--text-muted); font-weight: 600; font-family: monospace; }
.group-line { flex: 1; height: 1px; background: var(--border); }
.entries { display: flex; flex-direction: column; gap: 10px; }
.ep-card { cursor: pointer; }
.ep-card :deep(.n-card__content) { padding: 0; }
.ep-inner { display: flex; gap: 14px; padding: 14px; }
.ep-poster { width: 72px; flex-shrink: 0; aspect-ratio: 2/3; border-radius: 10px; overflow: hidden; background: var(--bg-secondary); }
.ep-poster img { width: 100%; height: 100%; object-fit: cover; display: block; }
.poster-ph { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: 800; color: var(--text-muted); background: linear-gradient(135deg, var(--brand-light), var(--bg-secondary)); }
.poster-ph.large { font-size: 48px; }
.ep-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 5px; }
.ep-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; }
.ep-name { font-size: 15px; font-weight: 700; line-height: 1.3; flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ep-date { font-size: 12px; color: var(--text-muted); flex-shrink: 0; font-family: monospace; }
.ep-subtitle { font-size: 12px; color: var(--text-muted); margin: 0; line-height: 1.3; font-weight: 500; }
.ep-desc { font-size: 12px; color: var(--text-muted); margin: 0; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.day-empty { text-align: center; padding: 20px; color: var(--text-muted); font-size: 12px; border-radius: 12px; border: 1px dashed var(--border); }
.modal-row { display: flex; }
.modal-poster { width: 240px; flex-shrink: 0; aspect-ratio: 2/3; overflow: hidden; background: var(--bg-secondary); }
.modal-poster img { width: 100%; height: 100%; object-fit: cover; }
.modal-body { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
@media (max-width: 767px) {
  .mobile-nav { display: flex; }
  .cal-header { flex-direction: column; align-items: stretch; }
  .ep-inner { padding: 10px; gap: 10px; }
  .ep-poster { width: 60px; }
  .modal-row { flex-direction: column; }
  .modal-poster { width: 100%; max-height: 200px; aspect-ratio: 16/9; }
}
</style>
