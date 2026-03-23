<template>
  <div class="stats-page">
    <PageHeader title="分析总览" desc="一眼看全局" />
    <StatsTabs />

    <!-- KPI 卡片 -->
    <div class="kpi-grid" v-if="overview">
      <div class="kpi-card">
        <div class="kpi-icon brand"><span class="kpi-emoji">🎬</span></div>
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

    <!-- 播放趋势 — AreaChart 面积图 -->
    <div class="section-card">
      <div class="section-header">
        <h3 class="section-title">播放趋势</h3>
        <div class="segment-group">
          <button v-for="p in trendPeriods" :key="p.value"
            class="seg-btn" :class="{ active: trendPeriod === p.value }"
            @click="trendPeriod = p.value">{{ p.label }}</button>
        </div>
      </div>
      <AreaChart :xData="trendXData" :series="[{ name: '播放时长', data: trendYData }]" height="260px" />
    </div>

    <!-- 热力图 + 设备分布 -->
    <div class="split-row">
      <div class="section-card">
        <div class="section-header">
          <h3 class="section-title">观影生物钟</h3>
          <div class="segment-group sm">
            <button v-for="p in heatPeriods" :key="p.value"
              class="seg-btn" :class="{ active: heatPeriod === p.value }"
              @click="heatPeriod = p.value">{{ p.label }}</button>
          </div>
        </div>
        <HeatmapChart :data="heatmapData" height="240px" />
      </div>

      <div class="section-card">
        <div class="section-header">
          <h3 class="section-title">设备分布</h3>
        </div>
        <PieChart v-if="deviceData.length > 0" :data="deviceData" height="240px" />
        <div v-else class="empty-chart">暂无数据</div>
      </div>
    </div>

    <!-- Top 5 内容 + Top 5 用户 -->
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
        <div v-if="topContent.length === 0" class="empty-text">暂无数据</div>
        <div v-else class="rank-list">
          <div v-for="(item, i) in topContent" :key="i" class="rank-item">
            <span class="rank-num" :class="{ 'rank-top': i < 3 }">{{ i + 1 }}</span>
            <n-avatar :src="item.poster_url" :size="36" round class="rank-avatar" fallback-src="" />
            <div class="rank-body">
              <div class="rank-name">{{ item.name }}</div>
              <div class="rank-sub">{{ item.play_count }} 次 · {{ item.total_duration_hours }}h</div>
            </div>
          </div>
        </div>
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
        <div v-if="topUsers.length === 0" class="empty-text">暂无数据</div>
        <div v-else class="rank-list">
          <div v-for="(item, i) in topUsers" :key="i" class="rank-item">
            <span class="rank-num" :class="{ 'rank-top': i < 3 }">{{ i + 1 }}</span>
            <n-avatar :size="36" round class="rank-avatar">{{ item.username?.charAt(0) || '?' }}</n-avatar>
            <div class="rank-body">
              <div class="rank-name">{{ item.username }}</div>
              <div class="rank-sub">{{ item.play_count }} 次 · {{ item.total_duration_hours }}h</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue'
import { NAvatar } from 'naive-ui'
import PageHeader from '@/components/common/PageHeader.vue'
import StatsTabs from '@/components/stats/StatsTabs.vue'
import AreaChart from '@/components/charts/AreaChart.vue'
import PieChart from '@/components/charts/PieChart.vue'
import HeatmapChart from '@/components/charts/HeatmapChart.vue'
import { statsApiV3 } from '@/api/stats-v3'

const overview = ref<any>(null)
const trendData = ref<Record<string, number>>({})
const topContent = ref<any[]>([])
const topUsers = ref<any[]>([])
const heatmapData = ref<number[][]>([])
const deviceData = ref<{ name: string; value: number }[]>([])

const trendPeriod = ref('30d')
const contentPeriod = ref('7d')
const userPeriod = ref('7d')
const heatPeriod = ref('30d')

const trendPeriods = [{ label: '30天', value: '30d' }, { label: '12周', value: '12w' }, { label: '12月', value: '12m' }]
const contentPeriods = [{ label: '7天', value: '7d' }, { label: '30天', value: '30d' }]
const userPeriods = [{ label: '7天', value: '7d' }, { label: '30天', value: '30d' }]
const heatPeriods = [{ label: '30天', value: '30d' }, { label: '90天', value: '90d' }]

// AreaChart props
const trendXData = computed(() => Object.keys(trendData.value))
const trendYData = computed(() => Object.values(trendData.value))

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
async function loadHeatmap() {
  const res = await statsApiV3.heatmap(heatPeriod.value)
  heatmapData.value = res.data?.data ?? res.data ?? []
}
async function loadDeviceDist() {
  const res = await statsApiV3.deviceDist('30d')
  deviceData.value = res.data?.data ?? res.data ?? []
}

watch(trendPeriod, loadTrend)
watch(contentPeriod, loadTopContent)
watch(userPeriod, loadTopUsers)
watch(heatPeriod, loadHeatmap)

onMounted(() => {
  loadOverview(); loadTrend(); loadTopContent(); loadTopUsers(); loadHeatmap(); loadDeviceDist()
})
</script>

<style scoped>
.stats-page { padding: 0.5rem 0; }
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem; margin-bottom: 1rem; }
.kpi-card { display: flex; align-items: center; gap: 0.75rem; background: var(--surface); border-radius: var(--radius-lg); padding: 1rem; border: 1px solid var(--border); }
.kpi-icon { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.kpi-icon.brand { background: var(--brand); }
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
.rank-list { display: flex; flex-direction: column; gap: 0.25rem; }
.rank-item { display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0.25rem; border-radius: var(--radius); }
.rank-num { width: 20px; font-size: 0.8rem; font-weight: 700; color: var(--text-muted); text-align: center; flex-shrink: 0; }
.rank-top { color: var(--brand); }
.rank-avatar { flex-shrink: 0; }
.rank-body { flex: 1; min-width: 0; }
.rank-name { font-size: 0.85rem; font-weight: 600; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.rank-sub { font-size: 0.7rem; color: var(--text-muted); }
.empty-text { text-align: center; padding: 2rem; color: var(--text-muted); font-size: 0.85rem; }
.empty-chart { text-align: center; padding: 3rem 1rem; color: var(--text-muted); font-size: 0.85rem; }
@media (max-width: 767px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .split-row { grid-template-columns: 1fr; }
}
</style>
