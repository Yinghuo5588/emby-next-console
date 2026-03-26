<template>
  <div class="stats-page">
    <PageHeader title="分析总览" />
    <StatsTabs :filterActive="true" @toggle-filter="showTime = !showTime" />

    <!-- 时间筛选（默认展开） -->
    <div class="unified-filter" v-show="showTime">
      <div class="segment-group">
        <button v-for="p in periods" :key="p.value"
          class="seg-btn" :class="{ active: period === p.value }"
          @click="period = p.value">{{ p.label }}</button>
      </div>
    </div>

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
          <div class="kpi-value">{{ overview.active_users }}</div>
          <div class="kpi-label">活跃用户</div>
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

    <!-- 播放趋势 -->
    <div class="section-card">
      <h3 class="section-title">播放趋势</h3>
      <AreaChart :xData="trendXData" :series="[{ name: '播放时长', data: trendYData }]" height="260px" />
    </div>

    <!-- 热力图 + 软件分布 + 硬件分布 -->
    <div class="three-col">
      <div class="section-card">
        <h3 class="section-title">观影生物钟</h3>
        <HeatmapChart :data="heatmapData" height="240px" />
      </div>
      <div class="section-card">
        <h3 class="section-title">软件分布</h3>
        <PieChart v-if="clientDist.length > 0" :data="clientDist" height="240px" />
        <div v-else class="empty-chart">暂无数据</div>
      </div>
      <div class="section-card">
        <h3 class="section-title">硬件分布</h3>
        <PieChart v-if="hardwareDist.length > 0" :data="hardwareDist" height="240px" />
        <div v-else class="empty-chart">暂无数据</div>
      </div>
    </div>

    <!-- Top 5 内容 + Top 5 用户 -->
    <div class="split-row">
      <div class="section-card">
        <h3 class="section-title">热门内容 Top 5</h3>
        <div v-if="topContent.length === 0" class="empty-text">暂无数据</div>
        <div v-else class="rank-list">
          <div v-for="(item, i) in topContent" :key="i" class="rank-item">
            <span class="rank-num" :class="{ 'rank-top': i < 3 }">{{ i + 1 }}</span>
            <n-avatar :src="item.poster_url" :size="36" round class="rank-avatar" />
            <div class="rank-body">
              <div class="rank-name">{{ item.name }}</div>
              <div class="rank-sub">{{ item.play_count }} 次 · {{ item.total_duration_hours }}h</div>
            </div>
          </div>
        </div>
      </div>

      <div class="section-card">
        <h3 class="section-title">活跃用户 Top 5</h3>
        <div v-if="topUsers.length === 0" class="empty-text">暂无数据</div>
        <div v-else class="rank-list">
          <div v-for="(item, i) in topUsers" :key="i" class="rank-item">
            <span class="rank-num" :class="{ 'rank-top': i < 3 }">{{ i + 1 }}</span>
            <span class="avatar-wrap"><img :src="`/api/v1/manage/users/${item.user_id}/avatar`" @error="($event.target as HTMLImageElement).classList.add('hide')" />{{ item.username?.charAt(0) || '?' }}</span>
            <div class="rank-body">
              <div class="rank-name rank-name-link" @click="$router.push(`/users/${item.user_id}`)">{{ item.username }}</div>
              <div class="rank-sub">{{ item.play_count }} 次 · {{ item.total_duration_hours }}h</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
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
const clientDist = ref<{ name: string; value: number }[]>([])
const hardwareDist = ref<{ name: string; value: number }[]>([])

const showTime = ref(false) // 默认收起，点击总览tab弹出
const period = ref('30d')
const periods = [{ label: '7天', value: '7d' }, { label: '30天', value: '30d' }, { label: '90天', value: '90d' }, { label: '全部', value: 'all' }]

const trendXData = computed(() => Object.keys(trendData.value))
const trendYData = computed(() => Object.values(trendData.value))

async function loadAll() {
  const p = period.value
  const trendP = p // 后端已支持 7d/30d/90d/all
  loadOverview(p)
  loadTrend(trendP)
  loadTopContent(p)
  loadTopUsers(p)
  loadHeatmap(p)
  loadDeviceDist(p)
}

async function loadOverview(p: string) {
  const res = await statsApiV3.overview(p)
  overview.value = res.data?.data ?? res.data
}
async function loadTrend(p: string) {
  const res = await statsApiV3.trend(p)
  trendData.value = res.data?.data ?? res.data ?? {}
}
async function loadTopContent(p: string) {
  const res = await statsApiV3.topContent(5, p)
  topContent.value = res.data?.data ?? res.data ?? []
}
async function loadTopUsers(p: string) {
  const res = await statsApiV3.topUsers(5, p)
  topUsers.value = res.data?.data ?? res.data ?? []
}
async function loadHeatmap(p: string) {
  const res = await statsApiV3.heatmap(p)
  heatmapData.value = res.data?.data ?? res.data ?? []
}
async function loadDeviceDist(p: string) {
  const [cRes, hRes] = await Promise.all([
    statsApiV3.deviceDist(p, 'client'),
    statsApiV3.deviceDist(p, 'hardware'),
  ])
  clientDist.value = cRes.data?.data ?? cRes.data ?? []
  hardwareDist.value = hRes.data?.data ?? hRes.data ?? []
}

watch(period, loadAll)
onMounted(loadAll)
</script>

<style scoped>
.stats-page { padding: 0.5rem 0; }
.unified-filter { margin-bottom: 0.75rem; animation: slideDown 0.2s ease; }
@keyframes slideDown { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: translateY(0); } }
.segment-group { display: inline-flex; background: var(--bg-secondary); border-radius: var(--radius-lg); padding: 3px; }
.seg-btn { border: none; background: none; padding: 6px 14px; font-size: 0.8rem; font-weight: 500; color: var(--text-muted); border-radius: var(--radius); cursor: pointer; transition: all 0.15s; font-family: inherit; }
.seg-btn.active { background: var(--surface); color: var(--text); box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
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
.section-title { font-size: 0.9rem; font-weight: 600; color: var(--text); margin: 0 0 0.75rem; }
.three-col { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; }
.split-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.rank-list { display: flex; flex-direction: column; gap: 0.25rem; }
.rank-item { display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0.25rem; border-radius: var(--radius); }
.rank-num { width: 20px; font-size: 0.8rem; font-weight: 700; color: var(--text-muted); text-align: center; flex-shrink: 0; }
.rank-top { color: var(--brand); }
.rank-avatar { flex-shrink: 0; }
.rank-body { flex: 1; min-width: 0; }
.rank-name { font-size: 0.85rem; font-weight: 600; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.rank-name-link { color: var(--brand); cursor: pointer; }
.rank-name-link:hover { text-decoration: underline; }
.rank-sub { font-size: 0.7rem; color: var(--text-muted); }
.empty-text { text-align: center; padding: 2rem; color: var(--text-muted); font-size: 0.85rem; }
.empty-chart { text-align: center; padding: 3rem 1rem; color: var(--text-muted); font-size: 0.85rem; }
@media (max-width: 767px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .three-col { grid-template-columns: 1fr; }
  .split-row { grid-template-columns: 1fr; }
}
</style>
