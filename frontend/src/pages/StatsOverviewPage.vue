<template>
  <div class="stats-page">
    <PageHeader title="分析总览" desc="一眼看全局" />
    <StatsTabs />

    <!-- 核心指标卡片 -->
    <div class="kpi-grid" v-if="overview">
      <div class="kpi-card">
        <div class="kpi-icon"><span class="kpi-emoji">🎬</span></div>
        <div class="kpi-body">
          <div class="kpi-value">{{ overview.library.movie + overview.library.series }}</div>
          <div class="kpi-label">媒体总量</div>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-icon green"><span class="kpi-emoji">▶</span></div>
        <div class="kpi-body">
          <div class="kpi-value">{{ overview.total_plays }}</div>
          <div class="kpi-label">播放总次数</div>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-icon purple"><span class="kpi-emoji">👥</span></div>
        <div class="kpi-body">
          <div class="kpi-value">{{ overview.active_users_30d }}</div>
          <div class="kpi-label">30 天活跃</div>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-icon pink"><span class="kpi-emoji">⏱</span></div>
        <div class="kpi-body">
          <div class="kpi-value">{{ overview.total_duration_hours }}</div>
          <div class="kpi-label">总时长 (小时)</div>
        </div>
      </div>
    </div>

    <!-- 趋势图 — 面积图 -->
    <div class="section-card">
      <div class="section-header">
        <h3 class="section-title">播放趋势</h3>
        <div class="segment-group">
          <button v-for="p in trendPeriods" :key="p.value"
            class="seg-btn" :class="{ active: trendPeriod === p.value }"
            @click="trendPeriod = p.value">{{ p.label }}</button>
        </div>
      </div>
      <v-chart v-if="trendHasData" :option="trendOption" autoresize style="height: 260px" />
      <div v-else class="empty-chart">暂无趋势数据</div>
    </div>

    <!-- 热门内容 — 水平条形图 + 最近播放 -->
    <div class="split-row">
      <div class="section-card">
        <div class="section-header">
          <h3 class="section-title">热门内容 Top 5</h3>
          <div class="segment-group sm">
            <button v-for="p in contentPeriods" :key="p.value"
              class="seg-btn" :class="{ active: contentPeriod === p.value }"
              @click="contentPeriod = p.value">{{ p.label }}</button>
          </div>
        </div>
        <v-chart v-if="topContent.length > 0" :option="contentBarOption" autoresize style="height: 220px" />
        <div v-else class="empty-chart">暂无数据</div>
      </div>

      <div class="section-card">
        <div class="section-header">
          <h3 class="section-title">活跃用户 Top 5</h3>
          <div class="segment-group sm">
            <button v-for="p in userPeriods" :key="p.value"
              class="seg-btn" :class="{ active: userPeriod === p.value }"
              @click="userPeriod = p.value">{{ p.label }}</button>
          </div>
        </div>
        <v-chart v-if="topUsers.length > 0" :option="userBarOption" autoresize style="height: 220px" />
        <div v-else class="empty-chart">暂无数据</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue'
import { use } from 'echarts/core'
import { LineChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'
import PageHeader from '@/components/common/PageHeader.vue'
import StatsTabs from '@/components/stats/StatsTabs.vue'
import { statsApiV3 } from '@/api/stats-v3'

use([LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const overview = ref<any>(null)
const trendData = ref<Record<string, number>>({})
const topContent = ref<any[]>([])
const topUsers = ref<any[]>([])

const trendPeriod = ref('30d')
const contentPeriod = ref('7d')
const userPeriod = ref('7d')

const trendPeriods = [{ label: '30天', value: '30d' }, { label: '12周', value: '12w' }, { label: '12月', value: '12m' }]
const contentPeriods = [{ label: '7天', value: '7d' }, { label: '30天', value: '30d' }]
const userPeriods = [{ label: '7天', value: '7d' }, { label: '30天', value: '30d' }]

async function loadOverview() {
  const res = await statsApiV3.overview()
  overview.value = res.data?.data ?? res.data
}

async function loadTrend() {
  const res = await statsApiV3.trend(trendPeriod.value)
  trendData.value = res.data?.data ?? res.data ?? {}
}

async function loadTopContent() {
  const res = await statsApiV3.topContent(5, contentPeriod.value)
  topContent.value = res.data?.data ?? res.data ?? []
}

async function loadTopUsers() {
  const res = await statsApiV3.topUsers(5, userPeriod.value)
  topUsers.value = res.data?.data ?? res.data ?? []
}

watch(trendPeriod, loadTrend)
watch(contentPeriod, loadTopContent)
watch(userPeriod, loadTopUsers)

const trendHasData = computed(() => Object.values(trendData.value).some(v => v > 0))

// 面积图
const trendOption = computed(() => {
  const labels = Object.keys(trendData.value)
  const values = Object.values(trendData.value)
  return {
    tooltip: { trigger: 'axis', valueFormatter: (v: number) => `${v} 小时` },
    grid: { top: 10, right: 16, bottom: 24, left: 44 },
    xAxis: { type: 'category', data: labels, boundaryGap: false, axisLabel: { fontSize: 10, color: '#8e8e93' }, axisLine: { show: false }, axisTick: { show: false } },
    yAxis: { type: 'value', axisLabel: { fontSize: 10, color: '#8e8e93', formatter: '{value}h' }, splitLine: { lineStyle: { type: 'dashed', color: '#f0f0f0' } } },
    series: [{
      type: 'line', data: values, smooth: true, symbol: 'circle', symbolSize: 4,
      lineStyle: { width: 2.5, color: '#3b82f6' },
      itemStyle: { color: '#3b82f6' },
      areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(59,130,246,0.35)' }, { offset: 1, color: 'rgba(59,130,246,0.03)' }] } },
    }],
  }
})

// 热门内容 — 水平条形图
const contentBarOption = computed(() => {
  const sorted = [...topContent.value].reverse()
  const names = sorted.map(c => c.name?.length > 12 ? c.name.slice(0, 12) + '…' : c.name)
  const durations = sorted.map(c => c.total_duration_hours)
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, valueFormatter: (v: number) => `${v} 小时` },
    grid: { top: 5, right: 16, bottom: 10, left: 10, containLabel: true },
    xAxis: { type: 'value', show: false },
    yAxis: { type: 'category', data: names, axisLabel: { fontSize: 11, color: '#333', overflow: 'truncate' }, axisLine: { show: false }, axisTick: { show: false } },
    series: [{
      type: 'bar', data: durations, barWidth: 18,
      itemStyle: { borderRadius: [0, 4, 4, 0], color: '#3b82f6' },
      label: { show: true, position: 'right', fontSize: 11, color: '#8e8e93', formatter: '{c}h' },
    }],
  }
})

// 活跃用户 — 水平条形图
const userBarOption = computed(() => {
  const sorted = [...topUsers.value].reverse()
  const names = sorted.map(u => u.username)
  const durations = sorted.map(u => u.total_duration_hours)
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, valueFormatter: (v: number) => `${v} 小时` },
    grid: { top: 5, right: 16, bottom: 10, left: 10, containLabel: true },
    xAxis: { type: 'value', show: false },
    yAxis: { type: 'category', data: names, axisLabel: { fontSize: 11, color: '#333' }, axisLine: { show: false }, axisTick: { show: false } },
    series: [{
      type: 'bar', data: durations, barWidth: 18,
      itemStyle: { borderRadius: [0, 4, 4, 0], color: '#af52de' },
      label: { show: true, position: 'right', fontSize: 11, color: '#8e8e93', formatter: '{c}h' },
    }],
  }
})

onMounted(() => { loadOverview(); loadTrend(); loadTopContent(); loadTopUsers() })
</script>

<style scoped>
.stats-page { padding: 0.5rem 0; }
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem; margin-bottom: 1rem; }
.kpi-card { display: flex; align-items: center; gap: 0.75rem; background: var(--surface); border-radius: var(--radius-lg); padding: 1rem; border: 1px solid var(--border); }
.kpi-icon { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; background: var(--brand); flex-shrink: 0; }
.kpi-icon.green { background: #34c759; }
.kpi-icon.purple { background: #af52de; }
.kpi-icon.pink { background: #ff2d55; }
.kpi-emoji { font-size: 1.1rem; filter: brightness(10); }
.kpi-value { font-size: 1.5rem; font-weight: 700; color: var(--text); line-height: 1.2; }
.kpi-label { font-size: 0.75rem; color: var(--text-muted); }
.section-card { background: var(--surface); border-radius: var(--radius-lg); padding: 1rem; border: 1px solid var(--border); margin-bottom: 1rem; }
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem; }
.section-title { font-size: 0.9rem; font-weight: 600; color: var(--text); margin: 0; }
.segment-group { display: flex; background: var(--bg-secondary); border-radius: var(--radius); padding: 2px; }
.segment-group.sm { transform: scale(0.9); transform-origin: right center; }
.seg-btn { border: none; background: none; padding: 4px 10px; font-size: 0.75rem; font-weight: 500; color: var(--text-muted); border-radius: var(--radius); cursor: pointer; transition: all 0.15s; font-family: inherit; }
.seg-btn.active { background: var(--surface); color: var(--text); box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.split-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.empty-chart { text-align: center; padding: 3rem 1rem; color: var(--text-muted); font-size: 0.85rem; }
@media (max-width: 767px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .split-row { grid-template-columns: 1fr; }
}
</style>
