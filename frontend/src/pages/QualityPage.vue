<template>
  <div class="quality-page">
    <PageHeader title="质量盘点" subtitle="扫描媒体库，分析视频质量">
      <template #actions>
        <div class="header-actions">
          <n-button size="small" secondary round @click="openIgnoredView">
            查看忽略
            <span v-if="ignoredCount > 0" class="header-btn-count">{{ ignoredCount }}</span>
          </n-button>
          <n-button
            v-if="!scanStatus.running"
            type="primary"
            size="small"
            round
            @click="startScan"
          >
            {{ hasData ? '重新扫描' : '开始扫描' }}
          </n-button>
        </div>
      </template>
    </PageHeader>

    <!-- 扫描状态 -->
    <div v-if="scanStatus.running" class="scan-card">
      <div class="scan-header">
        <div class="scan-label">扫描中</div>
        <div class="scan-pct">{{ scanPercent }}%</div>
      </div>
      <n-progress type="line" :percentage="scanPercent" :show-indicator="false" status="info" :height="6" />
      <div class="scan-sub">{{ scanStatus.scanned }} / {{ scanStatus.total }} 已扫描</div>
    </div>
    <div v-else-if="scanStatus.error" class="scan-card scan-error">
      <span>❌ {{ scanStatus.error }}</span>
      <n-button size="tiny" type="error" @click="startScan">重试</n-button>
    </div>

    <!-- 清除筛选/退出忽略 -->
    <div v-if="activeFilter || isIgnoredView" class="action-row">
      <n-tag v-if="activeFilter" type="info" size="small" round closable @close="clearFilter">
        {{ activeFilter }}
      </n-tag>
      <n-tag v-if="isIgnoredView" type="warning" size="small" round closable @close="exitIgnoredView">
        已忽略内容
      </n-tag>
    </div>

    <!-- 环形图区（支持翻转） -->
    <div v-if="hasData" class="charts-section">
      <!-- 分辨率卡片 -->
      <div
        class="chart-card-wrapper tone-blue"
        :class="{ flipped: flippedCard === 'resolution' }"
        @click="flipCard('resolution')"
      >
        <div class="chart-card-inner">
          <div class="chart-card-front">
            <div class="chart-header">
              <div class="chart-title">分辨率分布</div>
              <div class="chart-total">共 {{ resolutionTotal }} 项</div>
            </div>
            <div ref="resChartRef" class="chart-box"></div>
            <div class="flip-hint">点击查看详情</div>
          </div>
          <div class="chart-card-back">
            <div class="chart-title">分辨率明细</div>
            <div class="detail-rows">
              <div
                v-for="entry in resolutionEntries"
                :key="entry.key"
                class="detail-row"
                :class="{ selected: filterResolution === entry.key }"
                @click.stop="toggleResFilter(entry.key)"
              >
                <span class="detail-dot" :style="{ background: entry.color }"></span>
                <span class="detail-name">{{ entry.key }}</span>
                <span class="detail-count">{{ entry.count }}</span>
                <span class="detail-pct">{{ entry.percent }}%</span>
              </div>
            </div>
            <div class="flip-hint">点击返回图表</div>
          </div>
        </div>
      </div>

      <!-- 动态范围卡片 -->
      <div
        class="chart-card-wrapper tone-orange"
        :class="{ flipped: flippedCard === 'range' }"
        @click="flipCard('range')"
      >
        <div class="chart-card-inner">
          <div class="chart-card-front">
            <div class="chart-header">
              <div class="chart-title">动态范围分布</div>
              <div class="chart-total">共 {{ rangeTotal }} 项</div>
            </div>
            <div ref="vrChartRef" class="chart-box"></div>
            <div class="flip-hint">点击查看详情</div>
          </div>
          <div class="chart-card-back">
            <div class="chart-title">动态范围明细</div>
            <div class="detail-rows">
              <div
                v-for="entry in rangeEntries"
                :key="entry.key"
                class="detail-row"
                :class="{ selected: filterRange === entry.key }"
                @click.stop="toggleRangeFilter(entry.key)"
              >
                <span class="detail-dot" :style="{ background: entry.color }"></span>
                <span class="detail-name">{{ entry.key }}</span>
                <span class="detail-count">{{ entry.count }}</span>
                <span class="detail-pct">{{ entry.percent }}%</span>
              </div>
            </div>
            <div class="flip-hint">点击返回图表</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 列表 -->
    <div v-if="hasData" class="list-section">
      <div v-for="(item, idx) in items" :key="item.item_id" class="item-card anim-in" :style="{ '--i': idx % 10 }" @click="toggleIgnore(item)">
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
            <span class="q-tag" :class="resClass(item.resolution)">{{ item.resolution }}</span>
            <span class="q-tag" :class="vrClass(item.video_range)">{{ item.video_range }}</span>
            <span class="q-tag q-type">{{ item.item_type === 'Movie' ? '电影' : '剧集' }}</span>
          </div>
        </div>
        <span class="item-action" :class="{ 'action-ignored': item.is_ignored }">
          {{ item.is_ignored ? '恢复' : '忽略' }}
        </span>
      </div>

      <!-- 分页 -->
      <div v-if="totalPages > 1" class="pager-row">
        <button class="pager-btn" :disabled="page <= 1" @click="page--">‹</button>
        <template v-for="p in pagerPages" :key="p">
          <span v-if="p === '...'" class="pager-ellipsis">…</span>
          <button v-else class="pager-num" :class="{ active: p === page }" @click="page = Number(p)">{{ p }}</button>
        </template>
        <button class="pager-btn" :disabled="page >= totalPages" @click="page++">›</button>
      </div>
    </div>

    <div v-if="!hasData && !scanStatus.running" class="empty-state">
      <div class="empty-icon"><IosIcon name="palette" :size="36" color="var(--text-muted)" :stroke-width="1.5" /></div>
      <div class="empty-title">还没有扫描数据</div>
      <div class="empty-desc">点击「开始扫描」获取媒体库质量信息</div>
      <n-button type="primary" size="medium" round @click="startScan">开始扫描</n-button>
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
import IosIcon from '@/components/common/IosIcon.vue'
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
const ignoredCount = ref(0)

// ── 翻转 ──
const flippedCard = ref<string | null>(null)
function flipCard(card: string) {
  flippedCard.value = flippedCard.value === card ? null : card
}

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
  renderCharts()
}

function toggleResFilter(key: string) {
  filterResolution.value = filterResolution.value === key ? null : key
  filterRange.value = null
  page.value = 1
  loadItems()
  renderCharts()
}

function toggleRangeFilter(key: string) {
  filterRange.value = filterRange.value === key ? null : key
  filterResolution.value = null
  page.value = 1
  loadItems()
  renderCharts()
}

// ── 忽略 ──
async function openIgnoredView() {
  filterResolution.value = null
  filterRange.value = null
  isIgnoredView.value = true
  page.value = 1
  await loadIgnoredItems()
}

async function exitIgnoredView() {
  isIgnoredView.value = false
  page.value = 1
  await loadItems()
}

const isIgnoredView = ref(false)

async function loadIgnoredItems() {
  loading.value = true
  try {
    const res = await qualityApi.items({ is_ignored: true, page: page.value, size: pageSize })
    items.value = res.items || []
    total.value = res.total || 0
  } catch {
    message.error('加载列表失败')
  } finally {
    loading.value = false
  }
}

async function loadIgnoredCount() {
  try {
    const res = await qualityApi.items({ is_ignored: true, page: 1, size: 1 })
    ignoredCount.value = res.total || 0
  } catch {
    ignoredCount.value = 0
  }
}

// ── 扫描 ──
const scanStatus = computed(() => overview.value.scan || { running: false })
const scanPercent = computed(() => {
  const s = scanStatus.value
  return s.total ? Math.round((s.scanned / s.total) * 100) : 0
})
const hasData = computed(() => overview.value.total > 0)
const totalPages = computed(() => Math.ceil(total.value / pageSize))

// ── 明细 ──
const RESOLUTION_ORDER = ['4K', '1080P', '720P', 'SD']
const RESOLUTION_COLORS = ['#007AFF', '#5AC8FA', '#5856D6', '#A284E0']
const VR_ORDER = ['Dolby Vision', 'HDR10+', 'HDR10', 'HLG', 'SDR']
const VR_COLORS = ['#FF9500', '#FF3B30', '#FF6B35', '#AF52DE', '#5AC8FA']

interface DetailEntry { key: string; count: number; percent: number; color: string }

function buildEntries(data: Record<string, number>, order: string[], colors: string[]): DetailEntry[] {
  const totalCount = Object.values(data).reduce((s, v) => s + v, 0) || 1
  return order
    .filter(k => (data[k] || 0) > 0)
    .map(k => ({
      key: k,
      count: data[k],
      percent: Math.round((data[k] / totalCount) * 1000) / 10,
      color: colors[order.indexOf(k)] || '#8E8E93',
    }))
}

const resolutionEntries = computed(() => buildEntries(overview.value.resolution, RESOLUTION_ORDER, RESOLUTION_COLORS))
const rangeEntries = computed(() => buildEntries(overview.value.video_range, VR_ORDER, VR_COLORS))
const resolutionTotal = computed(() => Object.values(overview.value.resolution).reduce((s, v) => s + v, 0))
const rangeTotal = computed(() => Object.values(overview.value.video_range).reduce((s, v) => s + v, 0))

// ── 图表 ──
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
      label: {
        show: true,
        fontSize: 11,
        color: uiStore.isDark ? '#e5e5ea' : '#3c3c43',
        formatter: '{b}',
      },
      labelLine: { show: true, length: 6, length2: 8 },
      emphasis: {
        label: { show: true, fontSize: 13, fontWeight: 'bold' },
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
    }
    if (vrChartRef.value) {
      vrChart?.dispose()
      vrChart = echarts.init(vrChartRef.value)
      vrChart.setOption(buildDonutOption(overview.value.video_range, VR_ORDER, VR_COLORS, '动态范围', filterRange.value))
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
  if (isIgnoredView.value) {
    return loadIgnoredItems()
  }
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
  isIgnoredView.value = false
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
      loadIgnoredCount()
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
    loadIgnoredCount()
    if (isIgnoredView.value) loadIgnoredItems()
  } catch {
    message.error('操作失败')
  }
}

function onImgError(e: Event) {
  const img = e.target as HTMLImageElement
  img.style.display = 'none'
}

function resClass(res: string) {
  if (res === '4K' || res === '2160p') return 'q-res-4k'
  if (res === '1080P' || res === '1080p') return 'q-res-1080'
  if (res === '720P' || res === '720p') return 'q-res-720'
  return 'q-res-low'
}
function vrClass(vr: string) {
  if (vr === 'Dolby Vision') return 'q-vr-dv'
  if (vr === 'HDR10+' || vr === 'HDR10') return 'q-vr-hdr'
  if (vr === 'HLG') return 'q-vr-hlg'
  return 'q-vr-sdr'
}

const pagerPages = computed(() => {
  const total = totalPages.value
  const cur = page.value
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  const pages: (number | string)[] = [1]
  if (cur > 3) pages.push('...')
  for (let i = Math.max(2, cur - 1); i <= Math.min(total - 1, cur + 1); i++) pages.push(i)
  if (cur < total - 2) pages.push('...')
  pages.push(total)
  return pages
})

watch(page, loadItems)

onMounted(() => {
  loadOverview()
  loadItems()
  loadIgnoredCount()
})
</script>

<style scoped>
.quality-page {
  padding-bottom: 100px;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}
.header-btn-count {
  margin-left: 4px;
  font-size: 11px;
  opacity: 0.7;
}

/* ── 扫描卡片 ── */
.scan-card {
  background: var(--surface-grouped);
  border-radius: 14px;
  padding: 14px 16px;
  margin-bottom: 12px;
}
.scan-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 10px;
}
.scan-label {
  font-size: 13px;
  font-weight: 600;
}
.scan-pct {
  font-size: 22px;
  font-weight: 700;
  color: var(--brand);
}
.scan-sub {
  font-size: 11px;
  color: var(--text-muted);
  text-align: center;
  margin-top: 6px;
}
.scan-error {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--danger);
  font-size: 13px;
}

.action-row {
  margin-bottom: 12px;
}

/* ── 图表卡片区 ── */
.charts-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.chart-card-wrapper {
  perspective: 800px;
  cursor: pointer;
  min-width: 0;
}

.chart-card-inner {
  position: relative;
  width: 100%;
  min-height: 240px;
  transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  transform-style: preserve-3d;
}

.chart-card-wrapper.flipped .chart-card-inner {
  transform: rotateY(180deg);
}

.chart-card-front,
.chart-card-back {
  position: absolute;
  inset: 0;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
  border-radius: 16px;
  padding: 14px 12px 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  border: 1px solid var(--border);
}

.chart-card-front {
  background: var(--surface-grouped);
}
.tone-blue .chart-card-front {
  background: linear-gradient(160deg, rgba(0, 122, 255, 0.04) 0%, var(--surface-grouped) 60%);
}
.tone-orange .chart-card-front {
  background: linear-gradient(160deg, rgba(255, 149, 0, 0.04) 0%, var(--surface-grouped) 60%);
}

.chart-card-back {
  transform: rotateY(180deg);
  background: var(--surface-grouped);
  padding: 14px 16px 12px;
  justify-content: center;
}

.chart-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  width: 100%;
  margin-bottom: 4px;
  padding: 0 4px;
}
.chart-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
}
.chart-total {
  font-size: 12px;
  color: var(--text-muted);
}
.chart-box {
  width: 100%;
  height: 180px;
}
.flip-hint {
  font-size: 10px;
  color: var(--text-muted);
  opacity: 0.45;
  margin-top: 6px;
  text-align: center;
}

/* ── 背面明细 ── */
.detail-rows {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
  margin-top: 10px;
}

.detail-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.015);
  border: 1px solid transparent;
  transition: all 0.2s;
}
.detail-row:hover {
  border-color: rgba(59, 130, 246, 0.25);
  background: rgba(59, 130, 246, 0.04);
}
.detail-row.selected {
  background: rgba(59, 130, 246, 0.08);
  border-color: rgba(59, 130, 246, 0.3);
}

.tone-blue .detail-row:hover {
  border-color: rgba(0, 122, 255, 0.25);
  background: rgba(0, 122, 255, 0.04);
}
.tone-blue .detail-row.selected {
  background: rgba(0, 122, 255, 0.08);
  border-color: rgba(0, 122, 255, 0.3);
}
.tone-orange .detail-row:hover {
  border-color: rgba(255, 149, 0, 0.25);
  background: rgba(255, 149, 0, 0.04);
}
.tone-orange .detail-row.selected {
  background: rgba(255, 149, 0, 0.08);
  border-color: rgba(255, 149, 0, 0.3);
}

.detail-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.detail-name {
  flex: 1;
  font-size: 14px;
  font-weight: 600;
}
.detail-count {
  font-size: 14px;
  font-weight: 700;
  color: var(--text);
}
.detail-pct {
  font-size: 13px;
  color: var(--text-muted);
  width: 42px;
  text-align: right;
  flex-shrink: 0;
}

/* ── 列表 ── */
.list-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.item-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: var(--surface-grouped);
  border-radius: 14px;
  border: 1px solid var(--border);
  transition: box-shadow 0.2s;
}
.item-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.item-poster {
  width: 46px;
  height: 64px;
  border-radius: 10px;
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
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.item-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 5px;
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
  font-weight: 500;
}

/* ── 空状态 ── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 260px;
  gap: 10px;
}
.empty-icon {
  margin-bottom: 8px;
  opacity: 0.5;
}
.empty-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
}
.empty-desc {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 12px;
}

@media (min-width: 769px) {
  .chart-box { height: 220px; }
  .chart-card-inner { min-height: 280px; }
}

/* ── 入场动画 ── */
.anim-in {
  opacity: 0; transform: translateY(10px);
  animation: slideIn 0.35s cubic-bezier(0.22, 1, 0.36, 1) forwards;
  animation-delay: calc(var(--i, 0) * 40ms);
}
@keyframes slideIn { to { opacity: 1; transform: translateY(0); } }

/* ── 自定义质量标签 ── */
.q-tag {
  font-size: 0.6rem; font-weight: 700;
  padding: 1px 6px; border-radius: 4px;
  line-height: 1.5; display: inline-block;
}
.q-res-4k { background: rgba(52,199,89,0.12); color: #248A3D; }
.q-res-1080 { background: rgba(0,122,255,0.1); color: #007AFF; }
.q-res-720 { background: rgba(255,159,10,0.12); color: #B45309; }
.q-res-low { background: rgba(142,142,147,0.1); color: #8e8e93; }
.q-vr-dv { background: rgba(175,82,222,0.12); color: #8944AB; }
.q-vr-hdr { background: rgba(255,159,10,0.12); color: #E08600; }
.q-vr-hlg { background: rgba(90,200,250,0.12); color: #007AFF; }
.q-vr-sdr { background: rgba(142,142,147,0.08); color: #8e8e93; }
.q-type { background: rgba(0,0,0,0.04); color: var(--text-muted); }

/* ── 海报阴影 ── */
.item-poster img { box-shadow: 0 2px 8px rgba(0,0,0,0.12); border-radius: 10px; }

/* ── 操作按钮 ── */
.item-action {
  font-size: 0.7rem; font-weight: 600;
  padding: 3px 8px; border-radius: 6px;
  background: rgba(255,159,10,0.1); color: #E08600;
  flex-shrink: 0; cursor: pointer;
  transition: all 0.15s;
}
.item-action:active { transform: scale(0.95); }
.action-ignored { background: rgba(142,142,147,0.08); color: var(--text-muted); }

/* ── 分页器 ── */
.pager-row { display: flex; align-items: center; justify-content: center; gap: 4px; margin-top: 16px; padding-bottom: 20px; }
.pager-btn {
  width: 32px; height: 32px; border-radius: 8px;
  border: none; background: var(--bg-secondary); color: var(--text);
  font-size: 1.1rem; font-weight: 600; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.15s; font-family: inherit;
}
.pager-btn:disabled { opacity: 0.3; cursor: default; }
.pager-btn:active:not(:disabled) { transform: scale(0.9); }
.pager-num {
  width: 32px; height: 32px; border-radius: 8px;
  border: none; background: none; color: var(--text-muted);
  font-size: 0.8rem; font-weight: 600; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.15s; font-family: inherit;
}
.pager-num.active { background: var(--brand); color: #fff; }
.pager-num:active { transform: scale(0.9); }
.pager-ellipsis { color: var(--text-muted); font-size: 0.8rem; padding: 0 2px; }
</style>
