<template>
  <div class="trakt-cal">
    <!-- 周导航 -->
    <div class="week-nav">
      <button class="nav-btn" @click="$emit('prev')">‹</button>
      <div class="week-range">{{ weekLabel }}</div>
      <button class="nav-btn" @click="$emit('next')">›</button>
      <button class="nav-btn today-btn" @click="$emit('today')">今天</button>
    </div>

    <!-- 7 列瀑布流 -->
    <div class="week-grid">
      <div
        v-for="col in waterfall"
        :key="col.dow"
        class="day-col"
        :class="{ 'is-today': col.date === todayStr, 'is-past': col.date < todayStr }"
      >
        <!-- 日期标头 -->
        <div class="day-header">
          <div class="day-name">{{ col.label }}</div>
          <div class="day-num" :class="{ 'num-today': col.date === todayStr }">{{ dayNum(col.date) }}</div>
          <div v-if="col.entries.length" class="day-badge">{{ col.entries.length }}</div>
        </div>

        <!-- 剧集列表 -->
        <div class="day-entries">
          <div
            v-for="e in col.entries"
            :key="e.id"
            class="entry-card"
            @click="$emit('select', e)"
          >
            <!-- 海报 -->
            <div class="entry-poster">
              <img
                v-if="e.backdrop_url"
                :src="e.backdrop_url"
                :alt="e.series_name"
                loading="lazy"
              />
              <div v-else class="poster-placeholder">
                {{ e.series_name?.charAt(0) || '?' }}
              </div>
              <!-- 状态指示灯 -->
              <div class="status-dot" :class="statusClass(e)" :title="statusText(e)">
                <span class="dot-inner"></span>
              </div>
            </div>

            <!-- 信息 -->
            <div class="entry-info">
              <div class="entry-series">{{ e.series_name }}</div>
              <div class="entry-ep">
                <span class="ep-tag">S{{ pad(e.season_number) }}E{{ pad(e.episode_number) }}</span>
                <span v-if="e.episode_title" class="entry-title">{{ e.episode_title }}</span>
              </div>
            </div>
          </div>

          <!-- 空状态 -->
          <div v-if="!col.entries.length" class="day-empty">
            <span class="empty-icon">{{ col.date < todayStr ? '✓' : '·' }}</span>
            <span>{{ col.date < todayStr ? '已过' : '暂无' }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { WeekWaterfallItem, CalendarEntry } from '@/api/calendar'

const props = defineProps<{
  waterfall: WeekWaterfallItem[]
}>()

defineEmits<{
  select: [entry: CalendarEntry]
  prev: []
  next: []
  today: []
}>()

const today = new Date()
const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`

const weekLabel = computed(() => {
  if (!props.waterfall.length) return ''
  const s = props.waterfall[0].date
  const e = props.waterfall[6]?.date || s
  return `${formatMonthDay(s)} — ${formatMonthDay(e)}`
})

function pad(n: number): string {
  return String(n).padStart(2, '0')
}

function dayNum(dateStr: string): string {
  return dateStr.split('-')[2]
}

function formatMonthDay(dateStr: string): string {
  const parts = dateStr.split('-')
  return `${parseInt(parts[1])}月${parseInt(parts[2])}日`
}

function statusClass(e: CalendarEntry): string {
  if (e.has_file) return 'status-ready'
  if (e.air_date < todayStr) return 'status-missing'
  if (e.air_date === todayStr) return 'status-today'
  return 'status-upcoming'
}

function statusText(e: CalendarEntry): string {
  if (e.has_file) return '已入库'
  if (e.air_date < todayStr) return '缺失'
  if (e.air_date === todayStr) return '今日播出'
  return '待播出'
}
</script>

<style scoped>
.trakt-cal {
  --cal-radius: 12px;
  --cal-card-bg: var(--card-bg, #1a1a2e);
}

/* ── 周导航 ── */
.week-nav {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  justify-content: center;
}
.week-range {
  font-size: 18px;
  font-weight: 700;
  min-width: 200px;
  text-align: center;
}
.nav-btn {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--bg-secondary);
  color: var(--text);
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}
.nav-btn:hover { background: var(--primary); color: #fff; border-color: var(--primary); }
.today-btn {
  width: auto;
  padding: 0 14px;
  font-size: 12px;
  font-weight: 600;
}

/* ── 7 列网格 ── */
.week-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 6px;
  min-height: 400px;
}

/* ── 单日列 ── */
.day-col {
  background: var(--cal-card-bg);
  border-radius: var(--cal-radius);
  border: 1px solid var(--border);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: border-color 0.2s;
}
.day-col.is-today {
  border-color: var(--primary);
  box-shadow: 0 0 0 1px var(--primary), 0 4px 12px rgba(59, 130, 246, 0.15);
}
.day-col.is-past { opacity: 0.7; }
.day-col:hover { opacity: 1; }

/* ── 日期标头 ── */
.day-header {
  padding: 10px 8px 8px;
  text-align: center;
  border-bottom: 1px solid var(--border);
  background: var(--bg-secondary);
  position: relative;
}
.day-name {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--text-muted);
  letter-spacing: 0.5px;
}
.day-num {
  font-size: 22px;
  font-weight: 800;
  line-height: 1.2;
  margin-top: 2px;
}
.num-today {
  color: var(--primary);
  background: rgba(59, 130, 246, 0.1);
  border-radius: 50%;
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
}
.day-badge {
  position: absolute;
  top: 6px;
  right: 6px;
  background: var(--primary);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  min-width: 18px;
  height: 18px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
}

/* ── 剧集列表 ── */
.day-entries {
  flex: 1;
  padding: 6px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  overflow-y: auto;
}

/* ── 单条剧集卡片 ── */
.entry-card {
  border-radius: 8px;
  overflow: hidden;
  background: var(--bg);
  border: 1px solid var(--border);
  cursor: pointer;
  transition: all 0.2s;
}
.entry-card:hover {
  border-color: var(--primary);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

/* ── 海报区域 ── */
.entry-poster {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  overflow: hidden;
  background: var(--bg-secondary);
}
.entry-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}
.entry-card:hover .entry-poster img { transform: scale(1.05); }
.poster-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-muted);
  background: var(--bg-secondary);
}

/* ── 状态指示灯 ── */
.status-dot {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
}
.dot-inner {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.status-ready .dot-inner { background: #22c55e; box-shadow: 0 0 6px #22c55e; }
.status-missing .dot-inner { background: #ef4444; box-shadow: 0 0 6px #ef4444; }
.status-today .dot-inner { background: #f59e0b; box-shadow: 0 0 6px #f59e0b; }
.status-upcoming .dot-inner { background: #6b7280; }

/* ── 信息区域 ── */
.entry-info {
  padding: 8px;
}
.entry-series {
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.entry-ep {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 3px;
}
.ep-tag {
  font-size: 10px;
  font-weight: 700;
  color: var(--primary);
  background: rgba(59, 130, 246, 0.1);
  padding: 1px 5px;
  border-radius: 4px;
  flex-shrink: 0;
}
.entry-title {
  font-size: 10px;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── 空状态 ── */
.day-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px 8px;
  color: var(--text-muted);
  font-size: 11px;
  gap: 4px;
}
.empty-icon { font-size: 16px; }

/* ── 移动端 ── */
@media (max-width: 767px) {
  .week-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 4px;
  }
  .entry-poster { aspect-ratio: 2 / 1; }
  .week-range { font-size: 14px; min-width: 160px; }
}
</style>
