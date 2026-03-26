<template>
  <div class="quality-page">
    <PageHeader title="质量盘点" subtitle="扫描媒体库，分析视频质量" />

    <!-- 扫描状态 -->
    <div v-if="scanStatus.running" class="scan-card">
      <div class="scan-label">扫描中 {{ scanStatus.scanned }}/{{ scanStatus.total }}</div>
      <n-progress type="line" :percentage="scanPercent" :show-indicator="false" status="info" :height="6" />
    </div>
    <div v-else-if="scanStatus.error" class="scan-card scan-error">
      <span>❌ {{ scanStatus.error }}</span>
      <n-button size="tiny" type="error" @click="startScan">重试</n-button>
    </div>

    <!-- 操作栏 -->
    <div class="action-row">
      <n-button v-if="!scanStatus.running" type="primary" size="small" round @click="startScan">
        {{ hasData ? '重新扫描' : '开始扫描' }}
      </n-button>
      <n-button v-if="filterResolution || filterRange" size="small" quaternary round @click="clearFilter">
        清除筛选
      </n-button>
    </div>

    <!-- 环形图区 -->
    <div v-if="hasData" class="charts-section">
      <div class="chart-card">
        <div class="chart-title">分辨率分布</div>
        <div ref="resChartRef" class="chart-box"></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">动态范围分布</div>
        <div ref="vrChartRef" class="chart-box"></div>
      </div>
    </div>

    <!-- 筛选提示 -->
    <div v-if="activeFilter" class="filter-row">
      <n-tag type="info" size="small" round closable @close="clearFilter">
        {{ activeFilter }}
      </n-tag>
    </div>

    <!-- 列表 -->
    <div v-if="hasData" class="list-section">
      <div v-for="item in items" :key="item.item_id" class="item-row">
        <div class="item-poster">
          <img
            :src="`/api/v1/proxy/image/${item.item_id}/Primary`"
            :alt="item.name"
            loading="lazy"
            @error="onImgError($event)"
          />
        </div>
        <div class="item-body">
          <div class="item-name">{{ item.name }}</div>
          <div class="item-meta">
            <n-tag :type="resTagType(item.resolution)" size="tiny" round>{{ item.resolution }}</n-tag>
            <n-tag :type="vrTagType(item.video_range)" size="tiny" round>{{ item.video_range }}</n-tag>
            <span class="item-type">{{ item.item_type === 'Movie' ? '电影' : '剧集' }}</span>
          </div>
        </div>
        <n-button
          size="tiny"
          :type="item.is_ignored ? 'default' : 'warning'"
          quaternary
          round
          @click.stop="toggleIgnore(item)"
        >
          {{ item.is_ignored ? '恢复' : '忽略' }}
        </n-button>
      </div>

      <!-- 分页 -->
      <div v-if="totalPages > 1" class="pager-row">
        <n-button :disabled="page <= 1" size="small" quaternary @click="page--">上一页</n-button>
        <span class="pager-info">{{ page }} / {{ totalPages }}</span>
        <n-button :disabled="page >= totalPages" size="small" quaternary @click="page++">下一页</n-button>
      </div>
    </div>

    <div v-if="!hasData && !scanStatus.running" class="empty-state">
      <n-empty description="暂无数据，点击开始扫描" />
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
import { useUiStore } from '@/stores/ui'

echarts.use([PieChart, TooltipComponent, LegendComponent, CanvasRenderer])

const message = useMessage()
const uiStore = useUiStore()

// ── 数据 ──
interface Overview {
  resolution: Record<string, number>
  video_range: Record<string, number>
  total: number
  scan: { running: boolean; total: number; scanned: number; error: string | null }
}

const overview = ref<Overview>({ resolution: {}, video_range: {}, total: 0, scan: { running: false, total: 0, scanned: 0, error: null } })
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
  if (filterResolution.value) parts.push(filterResolution.value)
  if (filterRange.value) parts.push(filterRange.value)
  return parts.join(' + ')
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
  return s.total ? Math.round((s.scanned / s.total) * 100) : 0
})
const hasData = computed(() => overview.value.total > 0)
const totalPages = computed(() => Math.ceil(total.value / pageSize))

// ── 图表 ──
const RESOLUTION_ORDER = ['4K', '1080P', '720P', 'SD']
const RESOLUTION_COLORS = ['#007AFF', '#5AC8FA', '#5856D6', '#8E8E93']
const VR_ORDER = ['Dolby Vision', 'HDR10+', 'HDR10', 'HLG', 'SDR']
const VR_COLORS = ['#FF9500', '#FF3B30', '#FF6B35', '#AF52DE', '#8E8E93']

const resChartRef = ref<HTMLElement>()
const vrChartRef = ref<HTMLElement>()
let resChart: echarts.ECharts | null = null
let vrChart: echarts.ECharts | null = null

function buildDonutOption(
  data: Record<string, number>,
  order: string[],
  colors: string[],
  totalLabel: string,
  selectedKey: string | null
) {
  const seriesData = order
    .filter(k => (data[k] || 0) > 0)
    .map((k) => ({
      name: k,
      value: data[k] || 0,
      itemStyle: { color: colors[order.indexOf(k)] },
      selected: selectedKey === k,
      selectedOffset: 6,
    }))

  const total = seriesData.reduce((s, d) => s + d.value, 0)

  return {
    color: colors,
    tooltip: {
      trigger: 'item',
      backgroundColor: uiStore.isDark ? 'rgba(44,44,46,0.95)' : 'rgba(255,255,255,0.95)',
      borderColor: uiStore.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.06)',
      textStyle: { color: uiStore.isDark ? '#fff' : '#000', fontSize: 13 },
      formatter: '{b}: {c} ({d}%)',
    },
    series: [{
      type: 'pie',
      radius: ['48%', '72%'],
      center: ['50%', '52%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 6, borderColor: uiStore.isDark ? '#1c1c1e' : '#fff', borderWidth: 2 },
      label: { show: false },
      emphasis: {
        label: { show: true, fontSize: 12, fontWeight: 'bold' },
        itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.15)' },
      },
      data: seriesData,
    }],
    graphic: [{
      type: 'text',
      left: 'center',
      top: '38%',
      style: {
        text: String(total),
        textAlign: 'center',
        fill: uiStore.isDark ? '#fff' : '#1c1c1e',
        fontSize: 20,
        fontWeight: 700,
      },
    }, {
      type: 'text',
      left: 'center',
      top: '52%',
      style: {
        text: totalLabel,
        textAlign: 'center',
        fill: uiStore.isDark ? '#8e8e93' : '#8e8e93',
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
      resChart.setOption(buildDonutOption(overview.value.resolution, RESOLUTION_ORDER, RESOLUTION_COLORS, '分辨率', filterResolution.value))
      resChart.off('click')
      resChart.on('click', (params: any) => {
        filterResolution.value = filterResolution.value === params.name ? null : params.name
        filterRange.value = null
        page.value = 1
        loadItems()
        renderCharts()
      })
    }
    if (vrChartRef.value) {
      vrChart?.dispose()
      vrChart = echarts.init(vrChartRef.value)
      vrChart.setOption(buildDonutOption(overview.value.video_range, VR_ORDER, VR_COLORS, '动态范围', filterRange.value))
      vrChart.off('click')
      vrChart.on('click', (params: any) => {
        filterRange.value = filterRange.value === params.name ? null : params.name
        filterResolution.value = null
        page.value = 1
        loadItems()
        renderCharts()
      })
    }
  })
}

// ── 数据加载 ──
async function loadOverview() {
  try {
    const data = await qualityApi.overview()
    overview.value = data
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
    items.value = res.items || []
    total.value = res.total || 0
  } catch {
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

async function toggleIgnore(item: any) {
  try {
    if (item.is_ignored) {
      await qualityApi.unignore(item.item_id)
      item.is_ignored = false
      message.success('已恢复')
    } else {
      await qualityApi.ignore(item.item_id)
      item.is_ignored = true
      message.success('已忽略')
    }
    loadOverview()
  } catch {
    message.error('操作失败')
  }
}

function onImgError(e: Event) {
  const img = e.target as HTMLImageElement
  img.style.display = 'none'
}

function resTagType(res: string) {
  return res === '4K' ? 'info' : res === '1080P' ? 'success' : 'warning'
}
function vrTagType(vr: string) {
  if (vr === 'Dolby Vision') return 'warning'
  if (vr === 'HDR10+' || vr === 'HDR10') return 'error'
  if (vr === 'HLG') return 'info'
  return 'default'
}

watch(page, loadItems)

onMounted(() => {
  loadOverview()
  loadItems()
})
</script>

<style scoped>
.quality-page {
  padding-bottom: 100px;
}

.scan-card {
  background: var(--surface-grouped);
  border-radius: 12px;
  padding: 12px 16px;
  margin-bottom: 12px;
}
.scan-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 8px;
  text-align: center;
}
.scan-error {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--danger);
  font-size: 13px;
}

.action-row {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.charts-section {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}
.chart-card {
  flex: 1;
  background: var(--surface-grouped);
  border-radius: 14px;
  padding: 10px 4px 8px;
  min-width: 0;
}
.chart-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  text-align: center;
  margin-bottom: 2px;
}
.chart-box {
  width: 100%;
  height: 180px;
}

.filter-row {
  margin-bottom: 12px;
}

.list-section {
  display: flex;
  flex-direction: column;
}
.item-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 0.5px solid var(--separator);
}
.item-poster {
  width: 44px;
  height: 62px;
  border-radius: 8px;
  overflow: hidden;
  background: var(--bg-secondary);
  flex-shrink: 0;
}
.item-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.item-body {
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
  gap: 4px;
  margin-top: 4px;
}
.item-type {
  font-size: 10px;
  color: var(--text-muted);
}

.pager-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 16px;
  padding-bottom: 20px;
}
.pager-info {
  font-size: 13px;
  color: var(--text-muted);
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

@media (min-width: 769px) {
  .charts-section {
    gap: 16px;
  }
  .chart-box {
    height: 220px;
  }
}
</style>
