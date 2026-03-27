<template>
  <div class="stats-page">
    <PageHeader title="分析总览" />
    <StatsTabs :filterActive="true" @toggle-filter="showTime = !showTime" />

    <!-- 时间筛选 -->
    <div class="unified-filter" v-show="showTime">
      <div class="segment-group">
        <button v-for="p in periods" :key="p.value"
          class="seg-btn" :class="{ active: period === p.value }"
          @click="period = p.value">{{ p.label }}</button>
      </div>
    </div>

    <!-- KPI 卡片 -->
    <KpiSkeleton v-if="loading" />
    <div class="kpi-grid" v-else-if="overview">
      <div class="kpi-card" style="--i:0">
        <div class="kpi-icon brand"><IosIcon name="film" :size="20" color="#fff" :stroke-width="2" /></div>
        <div class="kpi-body"><div class="kpi-value">{{ movieCount }}</div><div class="kpi-label">媒体总量</div></div>
      </div>
      <div class="kpi-card" style="--i:1">
        <div class="kpi-icon green"><IosIcon name="play" :size="20" color="#fff" :stroke-width="2" /></div>
        <div class="kpi-body"><div class="kpi-value">{{ playsCount }}</div><div class="kpi-label">播放总次数</div></div>
      </div>
      <div class="kpi-card" style="--i:2">
        <div class="kpi-icon purple"><IosIcon name="users" :size="20" color="#fff" :stroke-width="2" /></div>
        <div class="kpi-body"><div class="kpi-value">{{ usersCount }}</div><div class="kpi-label">活跃用户</div></div>
      </div>
      <div class="kpi-card" style="--i:3">
        <div class="kpi-icon pink"><IosIcon name="clock" :size="20" color="#fff" :stroke-width="2" /></div>
        <div class="kpi-body"><div class="kpi-value">{{ hoursCount }}</div><div class="kpi-label">总时长 (小时)</div></div>
      </div>
    </div>

    <!-- 播放趋势 -->
    <div class="section-card anim-in" style="--i:4">
      <h3 class="section-title">播放趋势</h3>
      <AreaChart :xData="trendXData" :series="[{ name: '播放时长', data: trendYData }]" height="260px" />
    </div>

    <!-- 热力图 + 设备分布（翻转卡片） -->
    <div class="two-col">
      <div class="section-card anim-in" style="--i:5">
        <h3 class="section-title">观影生物钟</h3>
        <HeatmapChart :data="heatmapData" height="240px" />
      </div>

      <FlipCard class="anim-in" style="--i:6">
        <template #front>
          <div class="section-card">
            <h3 class="section-title">软件分布</h3>
            <PieChart v-if="clientDist.length > 0" :data="clientDist" height="240px" />
            <div v-else class="empty-state-sm"><IosIcon name="device" :size="28" color="var(--text-muted)" :stroke-width="1.5" /><span>暂无数据</span></div>
          </div>
        </template>
        <template #back>
          <div class="section-card">
            <h3 class="section-title">硬件分布</h3>
            <PieChart v-if="hardwareDist.length > 0" :data="hardwareDist" height="240px" />
            <div v-else class="empty-state-sm"><IosIcon name="device" :size="28" color="var(--text-muted)" :stroke-width="1.5" /><span>暂无数据</span></div>
          </div>
        </template>
      </FlipCard>
    </div>

    <!-- Top 5 翻转卡片（热门内容 / 活跃用户） -->
    <FlipCard class="anim-in" style="--i:7">
      <template #front>
        <div class="section-card">
          <h3 class="section-title">热门内容 Top 5</h3>
          <div v-if="topContent.length === 0" class="empty-state-sm"><IosIcon name="fire" :size="28" color="var(--text-muted)" :stroke-width="1.5" /><span>暂无数据</span></div>
          <div v-else class="rank-list">
            <div v-for="(item, i) in topContent" :key="i" class="rank-item" @click.stop="$router.push(`/stats/content?item=${item.item_id}`)">
              <span class="rank-num" :class="rankClass(i)">{{ i + 1 }}</span>
              <n-avatar :src="item.poster_url" :size="36" round class="rank-avatar" />
              <div class="rank-body">
                <div class="rank-name">{{ item.name }}</div>
                <div class="rank-tags">
                  <span class="tag tag-plays">{{ item.play_count }} 次</span>
                  <span class="tag tag-hours">{{ item.total_duration_hours }}h</span>
                </div>
              </div>
              <span class="rank-arrow">›</span>
            </div>
          </div>
        </div>
      </template>
      <template #back>
        <div class="section-card">
          <h3 class="section-title">活跃用户 Top 5</h3>
          <div v-if="topUsers.length === 0" class="empty-state-sm"><IosIcon name="users" :size="28" color="var(--text-muted)" :stroke-width="1.5" /><span>暂无数据</span></div>
          <div v-else class="rank-list">
            <div v-for="(item, i) in topUsers" :key="i" class="rank-item" @click.stop="$router.push(`/stats/users?user=${item.user_id}`)">
              <span class="rank-num" :class="rankClass(i)">{{ i + 1 }}</span>
              <span class="avatar-wrap"><img :src="`/api/v1/manage/users/${item.user_id}/avatar`" @error="($event.target as HTMLImageElement).classList.add('hide')" />{{ item.username?.charAt(0) || '?' }}</span>
              <div class="rank-body">
                <div class="rank-name"><span class="link-name" @click.stop="$router.push(`/users/${item.user_id}`)">{{ item.username }}</span></div>
                <div class="rank-tags">
                  <span class="tag tag-plays">{{ item.play_count }} 次</span>
                  <span class="tag tag-hours">{{ item.total_duration_hours }}h</span>
                </div>
              </div>
              <span class="rank-arrow">›</span>
            </div>
          </div>
        </div>
      </template>
    </FlipCard>
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
import IosIcon from '@/components/common/IosIcon.vue'
import KpiSkeleton from '@/components/common/KpiSkeleton.vue'
import FlipCard from '@/components/common/FlipCard.vue'
import { useCountUp } from '@/composables/useCountUp'
import { statsApiV3 } from '@/api/stats-v3'

const overview = ref<any>(null)
const trendData = ref<Record<string, number>>({})
const topContent = ref<any[]>([])
const topUsers = ref<any[]>([])
const heatmapData = ref<number[][]>([])
const clientDist = ref<{ name: string; value: number }[]>([])
const hardwareDist = ref<{ name: string; value: number }[]>([])
const loading = ref(true)

const showTime = ref(false)
const period = ref('30d')
const periods = [{ label: '7天', value: '7d' }, { label: '30天', value: '30d' }, { label: '90天', value: '90d' }, { label: '全部', value: 'all' }]

const trendXData = computed(() => Object.keys(trendData.value))
const trendYData = computed(() => Object.values(trendData.value))

const movieTarget = computed(() => overview.value ? (overview.value.library?.movie ?? 0) + (overview.value.library?.series ?? 0) : undefined)
const playsTarget = computed(() => overview.value?.total_plays)
const usersTarget = computed(() => overview.value?.active_users)
const hoursTarget = computed(() => overview.value?.total_duration_hours)

const movieCount = useCountUp(movieTarget)
const playsCount = useCountUp(playsTarget)
const usersCount = useCountUp(usersTarget)
const hoursCount = useCountUp(hoursTarget)

function rankClass(i: number) {
  if (i === 0) return 'rank-gold'
  if (i === 1) return 'rank-silver'
  if (i === 2) return 'rank-bronze'
  return ''
}

async function loadAll() {
  const p = period.value
  loadOverview(p)
  loadTrend(p)
  loadTopContent(p)
  loadTopUsers(p)
  loadHeatmap(p)
  loadDeviceDist(p)
}

async function loadOverview(p: string) {
  const res = await statsApiV3.overview(p)
  overview.value = res.data?.data ?? res.data
  loading.value = false
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

watch(period, () => { loading.value = true; loadAll() })
onMounted(loadAll)
</script>

<style scoped>
.stats-page { padding: 0.5rem 0; }
.unified-filter { margin-bottom: 0.75rem; animation: slideDown 0.2s ease; }
@keyframes slideDown { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: translateY(0); } }
.segment-group { display: inline-flex; background: var(--bg-secondary); border-radius: var(--radius-lg); padding: 3px; }
.seg-btn { border: none; background: none; padding: 6px 14px; font-size: 0.8rem; font-weight: 500; color: var(--text-muted); border-radius: var(--radius); cursor: pointer; transition: all 0.15s; font-family: inherit; }
.seg-btn.active { background: var(--surface); color: var(--text); box-shadow: 0 1px 3px rgba(0,0,0,0.08); }

/* ── 入场动画 ── */
.anim-in, .kpi-card {
  opacity: 0;
  transform: translateY(14px);
  animation: cardIn 0.45s cubic-bezier(0.22, 1, 0.36, 1) forwards;
  animation-delay: calc(var(--i, 0) * 60ms);
}
@keyframes cardIn { to { opacity: 1; transform: translateY(0); } }

/* ── KPI 卡片 ── */
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem; margin-bottom: 1rem; }
.kpi-card {
  display: flex; align-items: center; gap: 0.75rem;
  background: var(--surface); border-radius: 16px; padding: 1.1rem;
  border: 1px solid var(--border);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); cursor: default;
}
.kpi-card:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,0.06); }
.kpi-icon { width: 42px; height: 42px; border-radius: 12px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.kpi-icon.brand { background: linear-gradient(135deg, #0A84FF, #0055D6); box-shadow: 0 4px 12px rgba(0,122,255,0.25); }
.kpi-icon.green { background: linear-gradient(135deg, #34C759, #248A3D); box-shadow: 0 4px 12px rgba(52,199,89,0.25); }
.kpi-icon.purple { background: linear-gradient(135deg, #AF52DE, #8944AB); box-shadow: 0 4px 12px rgba(175,82,222,0.25); }
.kpi-icon.pink { background: linear-gradient(135deg, #FF2D55, #D70040); box-shadow: 0 4px 12px rgba(255,45,85,0.25); }
.kpi-value { font-size: 1.6rem; font-weight: 800; color: var(--text); line-height: 1.2; font-variant-numeric: tabular-nums; letter-spacing: -0.02em; }
.kpi-label { font-size: 0.72rem; color: var(--text-muted); margin-top: 2px; }

/* ── Section 卡片 ── */
.section-card {
  background: var(--surface); border-radius: 16px; padding: 1.1rem;
  border: 1px solid var(--border); margin-bottom: 0;
  box-shadow: 0 1px 3px rgba(0,0,0,0.03);
  transition: box-shadow 0.2s;
}
.section-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.05); }
.section-title { font-size: 0.9rem; font-weight: 600; color: var(--text); margin: 0 0 0.75rem; }

/* ── 布局 ── */
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem; }

/* ── 排行榜 ── */
.rank-list { display: flex; flex-direction: column; gap: 2px; }
.rank-item {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.6rem 0.5rem; border-radius: 10px;
  transition: background 0.15s; cursor: pointer;
}
.rank-item:hover { background: rgba(0,122,255,0.04); }
.rank-num {
  width: 22px; height: 22px; font-size: 0.7rem; font-weight: 700;
  color: var(--text-muted); text-align: center; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; border-radius: 6px;
}
.rank-num.rank-gold { background: linear-gradient(135deg, #FFD700, #FFA500); color: #fff; border-radius: 50%; box-shadow: 0 2px 6px rgba(255,165,0,0.3); }
.rank-num.rank-silver { background: linear-gradient(135deg, #C0C0C0, #A8A8A8); color: #fff; border-radius: 50%; box-shadow: 0 2px 6px rgba(160,160,160,0.3); }
.rank-num.rank-bronze { background: linear-gradient(135deg, #CD7F32, #B8860B); color: #fff; border-radius: 50%; box-shadow: 0 2px 6px rgba(205,127,50,0.3); }
.rank-avatar { flex-shrink: 0; box-shadow: 0 2px 8px rgba(0,0,0,0.12); }
.rank-body { flex: 1; min-width: 0; }
.rank-name { font-size: 0.85rem; font-weight: 600; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.link-name { color: var(--brand); cursor: pointer; }
.link-name:hover { text-decoration: underline; }
.rank-tags { display: flex; gap: 4px; margin-top: 3px; }
.tag { font-size: 0.65rem; font-weight: 600; padding: 1px 6px; border-radius: 4px; line-height: 1.5; }
.tag-plays { background: rgba(0,122,255,0.1); color: #007AFF; }
.tag-hours { background: rgba(52,199,89,0.1); color: #248A3D; }
.rank-arrow {
  font-size: 1.2rem; color: var(--text-muted); opacity: 0.3;
  flex-shrink: 0; transition: opacity 0.15s;
}
.rank-item:hover .rank-arrow { opacity: 0.6; }

/* ── 空状态 ── */
.empty-state-sm {
  display: flex; flex-direction: column; align-items: center;
  gap: 0.5rem; padding: 2.5rem 1rem; color: var(--text-muted); font-size: 0.8rem; opacity: 0.7;
}

@media (max-width: 767px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .two-col { grid-template-columns: 1fr; }
}
</style>
