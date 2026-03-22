<template>
  <div class="trakt-cal">
    <!-- 顶部日期导航条 -->
    <div class="date-nav">
      <button class="nav-arrow" @click="$emit('prev')">‹</button>
      <div class="date-pills">
        <button
          v-for="col in waterfall"
          :key="col.dow"
          class="date-pill"
          :class="{
            'is-today': col.date === todayStr,
            'is-past': col.date < todayStr,
          }"
          @click="scrollToDay(col.dow)"
        >
          <span class="pill-weekday">{{ shortDay(col.label) }}</span>
          <span class="pill-num" :class="{ 'num-today': col.date === todayStr }">{{ dayNum(col.date) }}</span>
        </button>
      </div>
      <button class="nav-arrow" @click="$emit('next')">›</button>
    </div>

    <!-- 日期分组列表 -->
    <div class="day-groups">
      <div
        v-for="col in waterfall"
        :key="col.dow"
        :id="`day-${col.dow}`"
        class="day-group"
      >
        <!-- 组标题：周三 03-18 -->
        <div class="group-header">
          <span class="group-weekday">{{ col.label }}</span>
          <span class="group-date">{{ formatDate(col.date) }}</span>
        </div>

        <!-- 剧集条目列表 -->
        <div v-if="col.entries.length" class="entry-list">
          <div
            v-for="e in col.entries"
            :key="e.id"
            class="episode-card"
            @click="$emit('select', e)"
          >
            <!-- 左侧竖版封面 -->
            <div class="card-poster">
              <img
                v-if="e.backdrop_url"
                :src="e.backdrop_url"
                :alt="e.series_name"
                loading="lazy"
              />
              <div v-else class="poster-placeholder">
                <span>{{ e.series_name?.charAt(0) || '?' }}</span>
              </div>
            </div>

            <!-- 右侧文字区 -->
            <div class="card-body">
              <!-- 顶部：剧名 + 日期 -->
              <div class="card-top">
                <h3 class="series-name">{{ e.series_name }}</h3>
                <span class="update-date">{{ formatDate(e.air_date) }}</span>
              </div>

              <!-- 季集标签 -->
              <div class="ep-tag">S{{ pad(e.season_number) }}E{{ pad(e.episode_number) }}</div>

              <!-- 剧情简介 -->
              <p v-if="e.episode_title" class="ep-title">{{ e.episode_title }}</p>
              <p v-if="e.overview" class="ep-overview">{{ e.overview }}</p>

              <!-- 底部状态标签 -->
              <span class="status-badge" :class="statusClass(e)">{{ statusText(e) }}</span>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-else class="day-empty">暂无更新</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { WeekWaterfallItem, CalendarEntry } from '@/api/calendar'

const props = defineProps<{
  waterfall: WeekWaterfallItem[]
}>()

defineEmits<{
  select: [entry: CalendarEntry]
  prev: []
  next: []
}>()

const today = new Date()
const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`

function pad(n: number): string {
  return String(n).padStart(2, '0')
}

function dayNum(dateStr: string): string {
  return parseInt(dateStr.split('-')[2]).toString()
}

function shortDay(label: string): string {
  return label.slice(0, 1)
}

function formatDate(dateStr: string): string {
  const parts = dateStr.split('-')
  return `${pad(parseInt(parts[1]))}-${pad(parseInt(parts[2]))}`
}

function statusClass(e: CalendarEntry): string {
  if (e.has_file) return 'status-ready'
  if (e.air_date < todayStr) return 'status-missing'
  if (e.air_date === todayStr) return 'status-today'
  return 'status-upcoming'
}

function statusText(e: CalendarEntry): string {
  if (e.has_file) return '已入库'
  if (e.air_date < todayStr) return '待补货'
  if (e.air_date === todayStr) return '今日更新'
  return '待更新'
}

function scrollToDay(dow: number) {
  document.getElementById(`day-${dow}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
</script>

<style scoped>
.trakt-cal {
  --cal-bg: var(--bg, #f5f5f5);
  --cal-card: var(--card-bg, #ffffff);
  --cal-text: var(--text, #1a1a1a);
  --cal-muted: var(--text-muted, #8e8e93);
  --cal-border: var(--border, rgba(0, 0, 0, 0.06));
  --cal-brand: var(--brand, #2563eb);
  --cal-brand-light: var(--brand-light, rgba(37, 99, 235, 0.08));
}

/* ── 顶部日期导航条 ── */
.date-nav {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 12px 0;
  margin-bottom: 20px;
}
.nav-arrow {
  width: 32px;
  height: 48px;
  flex-shrink: 0;
  border: none;
  background: transparent;
  color: var(--cal-muted);
  font-size: 20px;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.15s;
}
.nav-arrow:hover {
  background: var(--cal-brand-light);
  color: var(--cal-brand);
}
.date-pills {
  flex: 1;
  display: flex;
  gap: 2px;
  justify-content: space-between;
}
.date-pill {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 2px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 10px;
  transition: all 0.15s;
}
.date-pill:hover {
  background: var(--cal-brand-light);
}
.pill-weekday {
  font-size: 11px;
  font-weight: 600;
  color: var(--cal-muted);
  text-transform: uppercase;
}
.pill-num {
  font-size: 18px;
  font-weight: 700;
  color: var(--cal-text);
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s;
}
.num-today {
  background: var(--cal-brand);
  color: #fff;
}
.is-past .pill-num {
  color: var(--cal-muted);
}
.is-past .pill-weekday {
  color: var(--cal-border);
}

/* ── 日期分组 ── */
.day-groups {
  display: flex;
  flex-direction: column;
  gap: 28px;
}
.day-group {
  scroll-margin-top: 80px;
}
.group-header {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--cal-border);
}
.group-weekday {
  font-size: 16px;
  font-weight: 700;
  color: var(--cal-text);
}
.group-date {
  font-size: 13px;
  color: var(--cal-muted);
  font-weight: 500;
}

/* ── 剧集条目列表 ── */
.entry-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* ── 单条剧集卡片 ── */
.episode-card {
  display: flex;
  gap: 14px;
  background: var(--cal-card);
  border: 1px solid var(--cal-border);
  border-radius: 12px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.2s;
}
.episode-card:hover {
  border-color: var(--cal-brand);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

/* ── 左侧竖版封面 ── */
.card-poster {
  width: 80px;
  min-height: 110px;
  flex-shrink: 0;
  border-radius: 8px;
  overflow: hidden;
  background: var(--cal-bg);
}
.card-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.poster-placeholder {
  width: 100%;
  height: 100%;
  min-height: 110px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--cal-brand-light), var(--cal-bg));
  font-size: 28px;
  font-weight: 700;
  color: var(--cal-brand);
}

/* ── 右侧文字区 ── */
.card-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.card-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}
.series-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--cal-text);
  line-height: 1.3;
  flex: 1;
}
.update-date {
  font-size: 12px;
  color: var(--cal-muted);
  flex-shrink: 0;
  margin-top: 2px;
}

/* ── 季集标签 ── */
.ep-tag {
  display: inline-flex;
  align-self: flex-start;
  padding: 2px 8px;
  background: var(--cal-brand-light);
  color: var(--cal-brand);
  font-size: 12px;
  font-weight: 700;
  border-radius: 6px;
  letter-spacing: 0.3px;
}

/* ── 剧情简介 ── */
.ep-title {
  font-size: 13px;
  color: var(--cal-muted);
  margin: 0;
  line-height: 1.4;
}
.ep-overview {
  font-size: 12px;
  color: var(--cal-muted);
  margin: 0;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ── 状态标签 ── */
.status-badge {
  display: inline-flex;
  align-self: flex-start;
  padding: 3px 10px;
  font-size: 11px;
  font-weight: 600;
  border-radius: 6px;
  margin-top: auto;
}
.status-ready {
  background: rgba(34, 197, 94, 0.1);
  color: #16a34a;
}
.status-missing {
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
}
.status-today {
  background: rgba(37, 99, 235, 0.1);
  color: #2563eb;
}
.status-upcoming {
  background: var(--cal-bg);
  color: var(--cal-muted);
}

/* ── 空状态 ── */
.day-empty {
  text-align: center;
  padding: 20px;
  color: var(--cal-muted);
  font-size: 13px;
  background: var(--cal-card);
  border-radius: 12px;
  border: 1px dashed var(--cal-border);
}

/* ── 移动端 ── */
@media (max-width: 767px) {
  .card-poster {
    width: 64px;
    min-height: 90px;
  }
  .series-name {
    font-size: 14px;
  }
  .episode-card {
    padding: 10px;
    gap: 10px;
  }
  .pill-num {
    font-size: 16px;
    width: 32px;
    height: 32px;
  }
}
</style>
