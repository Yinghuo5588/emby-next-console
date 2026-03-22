<template>
  <div>
    <PageHeader title="追剧日历" desc="剧集更新日历视图">
      <template #actions>
        <button class="btn btn-primary" :disabled="syncing" @click="doSync">
          {{ syncing ? '同步中...' : '🔄 从 Emby 同步' }}
        </button>
      </template>
    </PageHeader>

    <!-- 统计卡片 -->
    <div v-if="stats" class="stats-row" style="margin-bottom: 16px;">
      <div class="card stat-mini"><div class="sm-val">{{ stats.month_entries }}</div><div class="sm-label">本月更新</div></div>
      <div class="card stat-mini"><div class="sm-val">{{ stats.upcoming_7d }}</div><div class="sm-label">未来 7 天</div></div>
      <div class="card stat-mini"><div class="sm-val">{{ stats.tracked_series }}</div><div class="sm-label">追踪剧集</div></div>
    </div>

    <!-- 视图切换 + 导航 -->
    <div class="view-bar">
      <div class="view-tabs">
        <button class="btn btn-sm" :class="{ 'btn-primary': view === 'month' }" @click="view = 'month'">📅 月视图</button>
        <button class="btn btn-sm" :class="{ 'btn-primary': view === 'week' }" @click="view = 'week'">📊 周视图</button>
      </div>
      <div class="month-nav">
        <button class="btn btn-ghost" @click="prevPeriod">◀</button>
        <span class="month-label" v-if="view === 'month'">{{ year }}年{{ month }}月</span>
        <span class="month-label" v-else>第 {{ week }} 周 ({{ weekLabel }})</span>
        <button class="btn btn-ghost" @click="nextPeriod">▶</button>
      </div>
    </div>

    <!-- 月视图 -->
    <LoadingState v-if="loading" height="200px" />
    <template v-else>
      <CalendarGrid v-if="view === 'month'" :year="year" :month="month" :entries="entries" @select-day="onSelectDay" />
      <WeekWaterfall v-else-if="view === 'week'" :waterfall="weekData" />
    </template>

    <!-- 日期详情弹窗 -->
    <DayDetail v-if="selectedDay" :date="selectedDay" :entries="selectedEntries" @close="selectedDay = null" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import CalendarGrid from '@/components/calendar/CalendarGrid.vue'
import WeekWaterfall from '@/components/calendar/WeekWaterfall.vue'
import DayDetail from '@/components/calendar/DayDetail.vue'
import { calendarApi } from '@/api/calendar'
import type { CalendarEntry, CalendarStats, WeekWaterfallItem } from '@/api/calendar'

const today = new Date()
const year = ref(today.getFullYear())
const month = ref(today.getMonth() + 1)
const week = ref(1)
const view = ref<'month' | 'week'>('month')

const loading = ref(true)
const syncing = ref(false)
const entries = ref<Record<string, CalendarEntry[]>>({})
const weekData = ref<WeekWaterfallItem[]>([])
const stats = ref<CalendarStats | null>(null)

const selectedDay = ref<string | null>(null)
const selectedEntries = ref<CalendarEntry[]>([])

const weekLabel = ref('')

function prevPeriod() {
  if (view.value === 'month') {
    if (month.value === 1) { year.value--; month.value = 12 }
    else month.value--
  } else {
    if (week.value > 1) { week.value-- }
    else {
      // Go to previous month's last week
      if (month.value === 1) { year.value--; month.value = 12 }
      else month.value--
      week.value = 4
    }
  }
}

function nextPeriod() {
  if (view.value === 'month') {
    if (month.value === 12) { year.value++; month.value = 1 }
    else month.value++
  } else {
    if (week.value < 5) { week.value++ }
    else {
      if (month.value === 12) { year.value++; month.value = 1 }
      else month.value++
      week.value = 1
    }
  }
}

function onSelectEntry(entry: CalendarEntry) {
  // Show entry detail
  selectedDay.value = entry.air_date
  selectedEntries.value = [entry]
}

function prevWeek() {
  if (week.value > 1) week.value--
  else {
    if (month.value === 1) { year.value--; month.value = 12 }
    else month.value--
    week.value = 4
  }
}

function nextWeek() {
  if (week.value < 5) week.value++
  else {
    if (month.value === 12) { year.value++; month.value = 1 }
    else month.value++
    week.value = 1
  }
}

function goToday() {
  const now = new Date()
  year.value = now.getFullYear()
  month.value = now.getMonth() + 1
  // Calculate week of month
  const firstDay = new Date(year.value, month.value - 1, 1)
  const dayOfMonth = now.getDate()
  week.value = Math.ceil((dayOfMonth + firstDay.getDay()) / 7)
}

function onSelectDay(date: string, dayEntries: CalendarEntry[]) {
  selectedDay.value = date
  selectedEntries.value = dayEntries
}

async function loadMonth() {
  loading.value = true
  try {
    const res = await calendarApi.month(year.value, month.value)
    entries.value = res.data?.entries ?? {}
  } finally { loading.value = false }
}

async function loadWeek() {
  loading.value = true
  try {
    const res = await calendarApi.week(year.value, month.value, week.value)
    weekData.value = res.data?.waterfall ?? []
    if (res.data) {
      weekLabel.value = `${res.data.week_start} ~ ${res.data.week_end}`
    }
  } finally { loading.value = false }
}

async function loadStats() {
  try {
    const res = await calendarApi.stats()
    stats.value = res.data ?? null
  } catch {}
}

async function doSync() {
  syncing.value = true
  try {
    await calendarApi.sync()
    await Promise.all([view.value === 'month' ? loadMonth() : loadWeek(), loadStats()])
  } finally { syncing.value = false }
}

watch([year, month], () => {
  if (view.value === 'month') loadMonth()
})

watch([year, month, week], () => {
  if (view.value === 'week') loadWeek()
})

watch(view, (v) => {
  if (v === 'month') loadMonth()
  else loadWeek()
})

onMounted(() => {
  loadMonth()
  loadStats()
})
</script>

<style scoped>
.stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.stat-mini { text-align: center; padding: 12px; }
.sm-val { font-size: 24px; font-weight: 700; color: var(--primary); }
.sm-label { font-size: 12px; color: var(--text-muted); margin-top: 4px; }
.view-bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; flex-wrap: wrap; gap: 8px; }
.view-tabs { display: flex; gap: 4px; }
.view-tabs .btn { font-size: 12px; padding: 4px 12px; }
.view-tabs .btn:not(.btn-primary) { background: var(--bg-secondary); color: var(--text-muted); }
.month-nav { display: flex; align-items: center; gap: 16px; }
.month-label { font-size: 16px; font-weight: 700; min-width: 120px; text-align: center; }
</style>
