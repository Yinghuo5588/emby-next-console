<template>
  <div class="quality-page">
    <PageHeader title="质量盘点" subtitle="扫描媒体库，分析视频质量" />

    <!-- 扫描状态 -->
    <div v-if="scanStatus.running" class="scan-bar">
      <n-progress type="line" :percentage="scanPercent" :show-indicator="false" status="info" />
      <div class="scan-info">扫描中 {{ scanStatus.scanned }}/{{ scanStatus.total }}</div>
    </div>
    <div v-else-if="scanStatus.error" class="scan-bar scan-error">
      <span>❌ {{ scanStatus.error }}</span>
      <n-button size="small" type="error" @click="startScan">重试</n-button>
    </div>

    <!-- 操作栏 -->
    <div class="action-bar">
      <n-button v-if="!scanStatus.running" type="primary" size="small" @click="startScan">
        {{ hasData ? '重新扫描' : '开始扫描' }}
      </n-button>
      <n-button v-if="activeFilter" size="small" quaternary @click="clearFilter">
        清除筛选 ✕
      </n-button>
    </div>

    <!-- 环形图 -->
    <div v-if="hasData" class="charts-row">
      <div class="chart-card" @click="chartClick('resolution')">
        <div ref="resChartRef" class="chart-box"></div>
      </div>
      <div class="chart-card" @click="chartClick('range')">
        <div ref="vrChartRef" class="chart-box"></div>
      </div>
    </div>

    <!-- 筛选提示 -->
    <div v-if="activeFilter" class="filter-chip">
      <n-tag closable @close="clearFilter" type="info" size="medium">
        {{ activeFilter }}
      </n-tag>
    </div>

    <!-- 列表 -->
    <div v-if="hasData" class="item-list">
      <div v-for="item in items" :key="item.item_id" class="item-row">
        <n-avatar
          :src="item.poster_url"
          :size="40"
          round
          fallback-src=""
        >{{ item.name?.charAt(0) }}</n-avatar>
        <div class="item-info">
          <div class="item-name">{{ item.name }}</div>
          <div class="item-meta">
            <n-tag :type="resTagType(item.resolution)" size="tiny" round>{{ item.resolution }}</n-tag>
            <n-tag :type="vrTagType(item.video_range)" size="tiny" round>{{ item.video_range }}</n-tag>
            <span class="item-type">{{ item.item_type === 'Movie' ? '电影' : '剧集' }}</span>
          </div>
        </div>
      </div>
      <n-pagination
        v-if="totalPages > 1"
        v-model:page="page"
        :page-count="totalPages"
        class="pagination"
      />
    </div>

    <div v-if="!hasData && !scanStatus.running" class="empty">
      <n-empty description="暂无数据，请先扫描" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useMessage } from 'naive-ui'
import * as echarts from 'echarts/core'
import { PieChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { qualityApi } from '@/api/quality'
import PageHeader from '@/components/common/PageHeader.vue'

echarts.use([PieChart, TooltipComponent, LegendComponent, CanvasRenderer])

const message = useMessage()

// ── 数据 ──
const overview = ref<{ resolution: Record<string,number>; video_range: Record<string,number>; total: number; scan: any }>({
  resolution: {}, video_range: {}, total: 0, scan: {}
})
const items = ref<any[]>([])
const page = ref(1)
const pageSize = 25
const total = ref(0)
const loading = ref(false)

// ── 筛选 ──
const filterResolution = ref<string | null>(null)
const filterRange = ref<string | null>(null)
const activeFilter = computed(() => {
  const parts = []
  if (filterResolution.value) parts.push(`分辨率: ${filterResolution.value}`)
  if (filterRange.value) parts.push(`动态范围: ${filterRange.value}`)
  return parts.join(' + ') || ''
})

function clearFilter() {
  filterResolution.value = null
  filterRange.value = null
  page.value = 1
  loadItems()
}

// ── 扫描 ──
const scanStatus = computed(() => overview.value.scan || { running: false })
const scanPercent = computed(() => {
  const s = scanStatus.value
  if (!s.total) return 0
  return Math.round((s.scanned / s.total) * 100)
})
const hasData = computed(() => overview.value.total > 0)
const totalPages = computed(() => Math.ceil(total.value / pageSize))

// ── 环形图 ──
const resChartRef = ref<HTMLElement>()
const vrChartRef = ref<HTMLElement>()
let resChart: echarts.ECharts | null = null
let vrChart: echarts.ECharts | null = null

const RESOLUTION_ORDER = ['4K', '1080P', '720P', 'SD']
const RESOLUTION_COLORS = ['#3b82f6', '#60a5fa', '#93c5fd', '#cbd5e1']

const VR_ORDER = ['Dolby Vision', 'HDR10+', 'HDR10', 'HLG', 'SDR']
const VR_COLORS = ['#f59e0b', '#ef4444', '#f97316', '#a855f7', '#94a3b8']

function buildDonutOption(
  data: Record<string, number>,
  order: string[],
  colors: string[],
  title: string
) {
  const seriesData = order
    .filter(k => (data[k] || 0) > 0)
    .map((k, i) => ({
      name: k,
      value: data[k] || 0,
      itemStyle: { color: colors[order.indexOf(k)] },
    }))

  const total = seriesData.reduce((s, d) => s + d.value, 0)

  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    series: [{
      type: 'pie',
      radius: ['55%', '78%'],
      center: ['50%', '55%'],
      avoidLabelOverlap: true,
      label: { show: false },
      emphasis: {
        label: { show: true, fontSize: 13, fontWeight: 'bold' },
      },
      labelLine: { show: false },
      data: seriesData,
    }],
    graphic: [{
      type: 'text',
      left: 'center',
      top: '42%',
      style: {
        text: String(total),
        textAlign: 'center',
        fill: 'var(--text)',
        fontSize: 22,
        fontWeight: 700,
      },
    }, {
      type: 'text',
      left: 'center',
      top: '56%',
      style: {
        text: title,
        textAlign: 'center',
        fill: 'var(--text-muted)',
        fontSize: 11,
      },
    }],
  }
}

function renderCharts() {
  nextTick(() => {
    if (resChartRef.value) {
      resChart?.dispose()
      resChart = echarts.init(resChartRef.value)
      resChart.setOption(buildDonutOption(overview.value.resolution, RESOLUTION_ORDER, RESOLUTION_COLORS, '分辨率'))
    }
    if (vrChartRef.value) {
      vrChart?.dispose()
      vrChart = echarts.init(vrChartRef.value)
      vrChart.setOption(buildDonutOption(overview.value.video_range, VR_ORDER, VR_COLORS, '动态范围'))
    }
  })
}

// ── 点击筛选 ──
function chartClick(type: 'resolution' | 'range') {
  const chart = type === 'resolution' ? resChart : vrChart
  if (!chart) return

  chart.on('click', (params: any) => {
    if (type === 'resolution') {
      filterResolution.value = filterResolution.value === params.name ? null : params.name
      filterRange.value = null
    } else {
      filterRange.value = filterRange.value === params.name ? null : params.name
      filterResolution.value = null
    }
    page.value = 1
    loadItems()
  })
}

// ── 数据加载 ──
async function loadOverview() {
  try {
    overview.value = await qualityApi.overview()
    renderCharts()
  } catch (e: any) {
    message.error('加载失败: ' + e.message)
  }
}

async function loadItems() {
  loading.value = true
  try {
    const res = await qualityApi.items({
      resolution: filterResolution.value || undefined,
      video_range: filterRange.value || undefined,
      page: page.value,
      size: pageSize,
    })
    items.value = res.items
    total.value = res.total
  } catch (e: any) {
    message.error('加载列表失败')
  } finally {
    loading.value = false
  }
}

async function startScan() {
  try {
    await qualityApi.startScan()
    message.success('扫描已开始')
    pollScan()
  } catch {
    message.error('启动扫描失败')
  }
}

function pollScan() {
  const timer = setInterval(async () => {
    await loadOverview()
    if (!scanStatus.value.running) {
      clearInterval(timer)
      loadItems()
    }
  }, 2000)
}

// ── 筛选变化 ──
watch([filterResolution, filterRange], () => {
  // highlight selected segment
  if (resChart) {
    const opt = buildDonutOption(overview.value.resolution, RESOLUTION_ORDER, RESOLUTION_COLORS, '分辨率')
    resChart.setOption(opt, true)
    if (filterResolution.value) {
      resChart.dispatchAction({ type: 'highlight', name: filterResolution.value })
    }
  }
  if (vrChart) {
    const opt = buildDonutOption(overview.value.video_range, VR_ORDER, VR_COLORS, '动态范围')
    vrChart.setOption(opt, true)
    if (filterRange.value) {
      vrChart.dispatchAction({ type: 'highlight', name: filterRange.value })
    }
  }
})

watch(page, loadItems)

// ── 标签样式 ──
function resTagType(res: string) {
  return res === '4K' ? 'info' : res === '1080P' ? 'success' : 'warning'
}
function vrTagType(vr: string) {
  if (vr === 'Dolby Vision') return 'warning'
  if (vr === 'HDR10+' || vr === 'HDR10') return 'error'
  if (vr === 'HLG') return 'info'
  return 'default'
}

onMounted(() => {
  loadOverview()
  loadItems()
})
</script>

<style scoped>
.quality-page {
  padding-bottom: 100px;
}

.scan-bar {
  margin: 0 0 12px;
  background: var(--surface-grouped, #f2f2f7);
  border-radius: 12px;
  padding: 12px 16px;
}
.scan-info {
  margin-top: 6px;
  font-size: 12px;
  color: var(--text-muted);
  text-align: center;
}
.scan-error {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--danger, #ff3b30);
  font-size: 13px;
}

.action-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.charts-row {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.chart-card {
  flex: 1;
  background: var(--surface-grouped, #f2f2f7);
  border-radius: 14px;
  padding: 8px;
  cursor: pointer;
}
.chart-box {
  width: 100%;
  height: 180px;
}

.filter-chip {
  margin-bottom: 12px;
}

.item-list {
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.item-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 4px;
  border-bottom: 0.5px solid var(--separator, rgba(0,0,0,0.06));
}
.item-info {
  flex: 1;
  min-width: 0;
}
.item-name {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.item-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
}
.item-type {
  font-size: 11px;
  color: var(--text-muted);
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

@media (min-width: 769px) {
  .charts-row {
    gap: 16px;
  }
  .chart-box {
    height: 220px;
  }
}
</style>
