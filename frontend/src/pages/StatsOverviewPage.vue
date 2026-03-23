<template>
  <div class="stats-page">
    <PageHeader title="分析总览" desc="一眼看全局，3 秒了解 Emby 服务器状态" />

    <!-- 核心指标卡片 -->
    <div class="kpi-grid" v-if="overview">
      <div class="kpi-card">
        <div class="kpi-icon bg-blue-500"><span>🎬</span></div>
        <div class="kpi-body">
          <div class="kpi-value">{{ overview.library.movie + overview.library.series }}</div>
          <div class="kpi-label">媒体总量</div>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-icon bg-green-500"><span>▶</span></div>
        <div class="kpi-body">
          <div class="kpi-value">{{ overview.total_plays }}</div>
          <div class="kpi-label">播放总次数</div>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-icon bg-indigo-500"><span>👥</span></div>
        <div class="kpi-body">
          <div class="kpi-value">{{ overview.active_users_30d }}</div>
          <div class="kpi-label">30 天活跃</div>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-icon bg-pink-500"><span>⏱</span></div>
        <div class="kpi-body">
          <div class="kpi-value">{{ overview.total_duration_hours }}</div>
          <div class="kpi-label">总时长 (小时)</div>
        </div>
      </div>
    </div>

    <!-- 趋势图 -->
    <n-card class="section-card" title="播放趋势">
      <template #header-extra>
        <n-button-group size="small">
          <n-button v-for="p in trendPeriods" :key="p.value"
            :type="trendPeriod === p.value ? 'primary' : 'default'"
            :quaternary="trendPeriod !== p.value"
            @click="trendPeriod = p.value">{{ p.label }}</n-button>
        </n-button-group>
      </template>
      <div class="trend-chart">
        <v-chart :option="trendOption" autoresize style="height: 260px" />
      </div>
    </n-card>

    <div class="split-row">
      <!-- Top 内容 -->
      <n-card class="section-card" title="热门内容" size="small">
        <template #header-extra>
          <n-button-group size="small">
            <n-button v-for="p in contentPeriods" :key="p.value"
              :type="contentPeriod === p.value ? 'primary' : 'default'"
              :quaternary="contentPeriod !== p.value"
              @click="contentPeriod = p.value">{{ p.label }}</n-button>
          </n-button-group>
        </template>
        <div v-if="topContent.length === 0" class="empty-text">暂无数据</div>
        <div v-else class="rank-list">
          <div v-for="(item, i) in topContent" :key="i" class="rank-item"
            @click="$router.push(`/stats/content?item=${item.item_id}`)">
            <span class="rank-num" :class="{ 'rank-top': i < 3 }">{{ i + 1 }}</span>
            <n-avatar :src="item.poster_url" :size="36" round class="rank-avatar" fallback-src="" />
            <div class="rank-body">
              <div class="rank-name">{{ item.name }}</div>
              <div class="rank-sub">{{ item.play_count }} 次播放 · {{ item.total_duration_hours }}h</div>
            </div>
          </div>
        </div>
      </n-card>

      <!-- Top 用户 -->
      <n-card class="section-card" title="活跃用户" size="small">
        <template #header-extra>
          <n-button-group size="small">
            <n-button v-for="p in userPeriods" :key="p.value"
              :type="userPeriod === p.value ? 'primary' : 'default'"
              :quaternary="userPeriod !== p.value"
              @click="userPeriod = p.value">{{ p.label }}</n-button>
          </n-button-group>
        </template>
        <div v-if="topUsers.length === 0" class="empty-text">暂无数据</div>
        <div v-else class="rank-list">
          <div v-for="(item, i) in topUsers" :key="i" class="rank-item"
            @click="$router.push(`/stats/users?user=${item.user_id}`)">
            <span class="rank-num" :class="{ 'rank-top': i < 3 }">{{ i + 1 }}</span>
            <n-avatar :size="36" round class="rank-avatar">
              {{ item.username?.charAt(0) || '?' }}
            </n-avatar>
            <div class="rank-body">
              <div class="rank-name">{{ item.username }}</div>
              <div class="rank-sub">{{ item.play_count }} 次播放 · {{ item.total_duration_hours }}h</div>
            </div>
          </div>
        </div>
      </n-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { NCard, NButton, NButtonGroup, NAvatar } from 'naive-ui'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'
import PageHeader from '@/components/common/PageHeader.vue'
import { statsApiV3 } from '@/api/stats-v3'

use([LineChart, GridComponent, TooltipComponent, CanvasRenderer])

const overview = ref<any>(null)
const trendData = ref<Record<string, number>>({})
const topContent = ref<any[]>([])
const topUsers = ref<any[]>([])

const trendPeriod = ref('30d')
const contentPeriod = ref('7d')
const userPeriod = ref('7d')

const trendPeriods = [
  { label: '30天', value: '30d' },
  { label: '12周', value: '12w' },
  { label: '12月', value: '12m' },
]
const contentPeriods = [
  { label: '7天', value: '7d' },
  { label: '30天', value: '30d' },
]
const userPeriods = [
  { label: '7天', value: '7d' },
  { label: '30天', value: '30d' },
]

async function loadOverview() {
  const res = await statsApiV3.overview()
  overview.value = res.data?.data
}

async function loadTrend() {
  const res = await statsApiV3.trend(trendPeriod.value)
  trendData.value = res.data?.data || {}
}

async function loadTopContent() {
  const res = await statsApiV3.topContent(5, contentPeriod.value)
  topContent.value = res.data?.data || []
}

async function loadTopUsers() {
  const res = await statsApiV3.topUsers(5, userPeriod.value)
  topUsers.value = res.data?.data || []
}

watch(trendPeriod, loadTrend)
watch(contentPeriod, loadTopContent)
watch(userPeriod, loadTopUsers)

const trendOption = ref<any>({})
watch(trendData, (data) => {
  const labels = Object.keys(data)
  const values = Object.values(data)
  trendOption.value = {
    tooltip: { trigger: 'axis', valueFormatter: (v: number) => `${v} 小时` },
    grid: { top: 10, right: 16, bottom: 24, left: 40 },
    xAxis: { type: 'category', data: labels, axisLabel: { fontSize: 10, color: '#8e8e93' } },
    yAxis: { type: 'value', axisLabel: { fontSize: 10, color: '#8e8e93' }, splitLine: { lineStyle: { type: 'dashed', color: '#f0f0f0' } } },
    series: [{
      type: 'line',
      data: values,
      smooth: true,
      symbol: 'none',
      lineStyle: { width: 2.5, color: '#3b82f6' },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(59,130,246,0.25)' },
            { offset: 1, color: 'rgba(59,130,246,0.02)' },
          ],
        },
      },
    }],
  }
})

onMounted(() => {
  loadOverview()
  loadTrend()
  loadTopContent()
  loadTopUsers()
})
</script>

<style scoped>
.stats-page { padding: 0.5rem 0; }
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem; margin-bottom: 1rem; }
.kpi-card { display: flex; align-items: center; gap: 0.75rem; background: var(--surface); border-radius: var(--radius); padding: 1rem; border: 1px solid var(--border); }
.kpi-icon { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 1.1rem; flex-shrink: 0; }
.kpi-value { font-size: 1.5rem; font-weight: 700; color: var(--text); line-height: 1.2; }
.kpi-label { font-size: 0.75rem; color: var(--text-muted); }
.section-card { margin-bottom: 1rem; }
.split-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.rank-list { display: flex; flex-direction: column; gap: 0.5rem; }
.rank-item { display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0.25rem; border-radius: var(--radius); cursor: pointer; transition: background 0.15s; }
.rank-item:hover { background: var(--bg-secondary); }
.rank-num { width: 20px; font-size: 0.8rem; font-weight: 600; color: var(--text-muted); text-align: center; flex-shrink: 0; }
.rank-top { color: var(--brand); }
.rank-avatar { flex-shrink: 0; }
.rank-body { flex: 1; min-width: 0; }
.rank-name { font-size: 0.85rem; font-weight: 600; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.rank-sub { font-size: 0.75rem; color: var(--text-muted); }
.empty-text { text-align: center; padding: 2rem; color: var(--text-muted); font-size: 0.85rem; }
.trend-chart { min-height: 260px; }
@media (max-width: 767px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .split-row { grid-template-columns: 1fr; }
}
</style>
