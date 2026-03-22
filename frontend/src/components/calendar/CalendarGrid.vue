<template>
  <div class="calendar-grid">
    <!-- 星期头 -->
    <div class="cg-header">
      <div v-for="d in weekDays" :key="d" class="cg-weekday">{{ d }}</div>
    </div>
    <!-- 日期格子 -->
    <div class="cg-body">
      <div
        v-for="(day, i) in calendarDays"
        :key="i"
        class="cg-day"
        :class="{
          'cg-empty': !day.date,
          'cg-today': day.isToday,
          'cg-other-month': day.otherMonth,
          'cg-has-entries': day.entries.length > 0,
        }"
        @click="day.date && $emit('select-day', day.date, day.entries)"
      >
        <div class="cg-date">{{ day.dayNum }}</div>
        <div class="cg-entries">
          <div v-for="e in day.entries.slice(0, 3)" :key="e.id" class="cg-entry" :title="`${e.series_name} S${e.season_number}E${e.episode_number}`">
            <span class="cg-series">{{ e.series_name }}</span>
          </div>
          <div v-if="day.entries.length > 3" class="cg-more">+{{ day.entries.length - 3 }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { CalendarEntry } from '@/api/calendar'

interface DayData {
  date: string | null
  dayNum: number
  isToday: boolean
  otherMonth: boolean
  entries: CalendarEntry[]
}

const props = defineProps<{
  year: number
  month: number
  entries: Record<string, CalendarEntry[]>
}>()

defineEmits<{
  'select-day': [date: string, entries: CalendarEntry[]]
}>()

const weekDays = ['日', '一', '二', '三', '四', '五', '六']

const today = new Date()
const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`

const calendarDays = computed<DayData[]>(() => {
  const firstDay = new Date(props.year, props.month - 1, 1)
  const startDow = firstDay.getDay()
  const daysInMonth = new Date(props.year, props.month, 0).getDate()
  const daysInPrev = new Date(props.year, props.month - 1, 0).getDate()

  const days: DayData[] = []

  // 上月填充
  for (let i = startDow - 1; i >= 0; i--) {
    const d = daysInPrev - i
    days.push({ date: null, dayNum: d, isToday: false, otherMonth: true, entries: [] })
  }

  // 本月
  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${props.year}-${String(props.month).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    days.push({
      date: dateStr,
      dayNum: d,
      isToday: dateStr === todayStr,
      otherMonth: false,
      entries: props.entries[dateStr] || [],
    })
  }

  // 下月填充到 6 行
  const remaining = 42 - days.length
  for (let d = 1; d <= remaining; d++) {
    days.push({ date: null, dayNum: d, isToday: false, otherMonth: true, entries: [] })
  }

  return days
})
</script>

<style scoped>
.calendar-grid { width: 100%; }
.cg-header { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; margin-bottom: 4px; }
.cg-weekday { text-align: center; font-size: 12px; font-weight: 600; color: var(--text-muted); padding: 8px 0; }
.cg-body { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; }
.cg-day { min-height: 80px; padding: 6px; border: 1px solid var(--border); border-radius: 6px; background: var(--card-bg); cursor: pointer; transition: background 0.15s; overflow: hidden; }
.cg-day:hover { background: var(--bg-secondary); }
.cg-empty { cursor: default; background: transparent; border-color: transparent; }
.cg-other-month { opacity: 0.4; }
.cg-today { border-color: var(--primary); background: var(--primary-light, rgba(59, 130, 246, 0.05)); }
.cg-has-entries { border-left: 3px solid var(--primary); }
.cg-date { font-size: 13px; font-weight: 600; margin-bottom: 4px; }
.cg-today .cg-date { color: var(--primary); }
.cg-entries { display: flex; flex-direction: column; gap: 2px; }
.cg-entry { font-size: 10px; background: var(--primary-light, rgba(59, 130, 246, 0.1)); color: var(--primary); padding: 1px 4px; border-radius: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cg-series { font-weight: 500; }
.cg-more { font-size: 10px; color: var(--text-muted); }
@media (max-width: 767px) {
  .cg-day { min-height: 50px; padding: 4px; }
  .cg-entry { display: none; }
  .cg-has-entries::after { content: '●'; font-size: 8px; color: var(--primary); display: block; text-align: center; }
}
</style>