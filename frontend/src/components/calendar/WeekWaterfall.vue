<template>
  <div class="waterfall">
    <div v-for="col in waterfall" :key="col.dow" class="wf-col" :class="{ 'wf-today': col.date === todayStr }">
      <div class="wf-header">
        <div class="wf-label">{{ col.label }}</div>
        <div class="wf-date">{{ formatDate(col.date) }}</div>
        <div v-if="col.entries.length" class="wf-count">{{ col.entries.length }} 集</div>
      </div>
      <div class="wf-entries">
        <div
          v-for="e in col.entries"
          :key="e.id"
          class="wf-entry card"
          :style="entryStyle(e)"
        >
          <div v-if="e.backdrop_url" class="wf-thumb">
            <img :src="e.backdrop_url" loading="lazy" />
          </div>
          <div class="wf-body">
            <div class="wf-series">{{ e.series_name }}</div>
            <div class="wf-ep">S{{ pad(e.season_number) }}E{{ pad(e.episode_number) }}</div>
            <div v-if="e.episode_title" class="wf-title">{{ e.episode_title }}</div>
          </div>
        </div>
        <div v-if="!col.entries.length" class="wf-empty muted">暂无更新</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { WeekWaterfallItem, CalendarEntry } from '@/api/calendar'

defineProps<{
  waterfall: WeekWaterfallItem[]
}>()

const today = new Date()
const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`

function pad(n: number): string {
  return String(n).padStart(2, '0')
}

function formatDate(dateStr: string): string {
  const parts = dateStr.split('-')
  return `${parts[1]}/${parts[2]}`
}

// Color hash for series
const colorMap: Record<string, string> = {}
const colors = [
  'var(--primary)',
  '#ef4444',
  '#f59e0b',
  '#10b981',
  '#8b5cf6',
  '#ec4899',
  '#06b6d4',
]
let colorIdx = 0

function getColor(name: string): string {
  if (!colorMap[name]) {
    colorMap[name] = colors[colorIdx % colors.length]
    colorIdx++
  }
  return colorMap[name]
}

function entryStyle(e: CalendarEntry): Record<string, string> {
  return { borderLeftColor: getColor(e.series_name), borderLeftWidth: '3px', borderLeftStyle: 'solid' }
}
</script>

<style scoped>
.waterfall {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 8px;
  min-height: 300px;
}
.wf-col {
  display: flex;
  flex-direction: column;
  border-radius: 10px;
  background: var(--card-bg);
  border: 1px solid var(--border);
  overflow: hidden;
}
.wf-today {
  border-color: var(--primary);
  background: var(--primary-light, rgba(59, 130, 246, 0.03));
}
.wf-header {
  padding: 10px 8px;
  text-align: center;
  border-bottom: 1px solid var(--border);
  background: var(--bg-secondary);
}
.wf-label { font-weight: 700; font-size: 13px; }
.wf-today .wf-label { color: var(--primary); }
.wf-date { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
.wf-count { font-size: 11px; color: var(--primary); margin-top: 2px; font-weight: 600; }
.wf-entries {
  flex: 1;
  padding: 6px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  overflow-y: auto;
}
.wf-entry {
  padding: 8px;
  border-radius: 8px;
  cursor: default;
  transition: transform 0.15s;
}
.wf-entry:hover { transform: translateY(-1px); }
.wf-thumb { width: 100%; height: 40px; border-radius: 4px; overflow: hidden; margin-bottom: 6px; }
.wf-thumb img { width: 100%; height: 100%; object-fit: cover; }
.wf-series { font-size: 12px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.wf-ep { font-size: 10px; color: var(--text-muted); }
.wf-title { font-size: 10px; color: var(--text-muted); margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.wf-empty { text-align: center; padding: 20px 8px; font-size: 12px; }

@media (max-width: 767px) {
  .waterfall {
    grid-template-columns: repeat(3, 1fr);
    gap: 4px;
  }
  .wf-thumb { display: none; }
}
</style>
