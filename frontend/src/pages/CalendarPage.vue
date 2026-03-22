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

    <!-- 月份导航 -->
    <div class="month-nav">
      <button class="btn btn-ghost" @click="prevMonth">◀</button>
      <span class="month-label">{{ year }}年{{ month }}月</span>
      <button class="btn btn-ghost" @click="nextMonth">▶</button>
    </div>

    <!-- 日历网格 -->
    <LoadingState v-if="loading" height="200px" />
    <CalendarGrid v-else :year="year" :month="month" :entries="entries" @select-day="onSelectDay" />

    <!-- 日期详情弹窗 -->
    <DayDetail v-if="selectedDay" :date="selectedDay" :entries="selectedEntries" @close="selectedDay = null" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import CalendarGrid from '@/components/calendar/CalendarGrid.vue'
import DayDetail from '@/components/calendar/DayDetail.vue'
import { calendarApi } from '@/api/calendar'
import type { CalendarEntry, CalendarStats } from '@/api/calendar'

const today = new Date()
const year = ref(today.getFullYear())
const month = ref(today.getMonth() + 1)

const loading = ref(true)
const syncing = ref(false)
const entries = ref<Record<string, CalendarEntry[]>>({})
const stats = ref<CalendarStats | null>(null)

const selectedDay = ref<string | null>(null)
const selectedEntries = ref<CalendarEntry[]>([])

function prevMonth() {
  if (month.value === 1) { year.value--; month.value = 12 }
  else month.value--
}

function nextMonth() {
  if (month.value === 12) { year.value++; month.value = 1 }
  else month.value++
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
    await Promise.all([loadMonth(), loadStats()])
  } finally { syncing.value = false }
}

watch([year, month], loadMonth)

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
.month-nav { display: flex; align-items: center; justify-content: center; gap: 16px; margin-bottom: 16px; }
.month-label { font-size: 18px; font-weight: 700; }
</style>