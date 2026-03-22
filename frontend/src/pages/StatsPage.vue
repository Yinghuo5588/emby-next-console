<template>
  <div>
    <PageHeader title="数据分析" desc="多维度观看数据分析">
      <template #actions>
        <n-select v-model:value="days" :options="daysOptions" size="small" style="width: 120px" @update:value="refreshAll" />
      </template>
    </PageHeader>

    <n-tabs v-model:value="activeTab" type="segment" size="small" style="margin-bottom: 16px;">
      <!-- 总览 -->
      <n-tab-pane name="overview">
        <template #tab><IosIcon name="chart" :size="16" /> 总览</template>
        <div class="section-grid">
          <n-card size="small">
            <template #header><CardTitle icon="clock" title="观影生物钟" /></template>
            <HeatmapChart v-if="heatmapData" :data="heatmapData" height="200px" />
            <n-empty v-else description="暂无数据" />
          </n-card>
          <n-card size="small">
            <template #header><CardTitle icon="device" title="设备分布" /></template>
            <PieChart v-if="devices.length" :data="devices.map(d => ({ name: d.device, value: d.count }))" height="240px" />
            <n-empty v-else description="暂无数据" />
          </n-card>
        </div>
        <div class="section-grid" style="margin-top: 16px">
          <n-card size="small">
            <template #header><CardTitle icon="chart" title="播放趋势" /></template>
            <AreaChart v-if="trendX.length" :x-data="trendX" :series="[{ name: '播放次数', data: trendY }]" height="200px" />
            <n-empty v-else description="暂无数据" />
          </n-card>
          <n-card size="small">
            <template #header><CardTitle icon="palette" title="类型偏好" /></template>
            <div v-if="genres.length" class="genre-grid">
              <n-tag v-for="g in genres" :key="g.genre" size="small" round>{{ g.genre }} {{ g.percentage }}%</n-tag>
            </div>
            <n-empty v-else description="暂无数据" />
          </n-card>
        </div>
      </n-tab-pane>

      <!-- 排行 -->
      <n-tab-pane name="ranking">
        <template #tab><IosIcon name="trophy" :size="16" /> 排行</template>
        <div class="section-grid">
          <n-card size="small">
            <template #header><CardTitle icon="fire" title="热度排行" icon-color="#FF3B30" /></template>
            <BarChart v-if="hotRank.length" :y-data="hotRank.map(h => h.item_name)" :data="hotRank.map(h => h.play_count)" horizontal height="300px" color="#FF3B30" />
            <n-empty v-else description="暂无数据" />
          </n-card>
          <n-card size="small">
            <template #header><CardTitle icon="clock" title="时长排行" icon-color="#FF9500" /></template>
            <BarChart v-if="durationRank.length" :y-data="durationRank.map(d => d.item_name)" :data="durationRank.map(d => Math.round(d.total_duration_min / 60))" horizontal height="300px" color="#FF9500" />
            <n-empty v-else description="暂无数据" />
          </n-card>
        </div>
        <n-card size="small" style="margin-top: 16px">
          <template #header><CardTitle icon="users" title="用户排行" /></template>
          <n-empty v-if="!userRank.length" description="暂无数据" />
          <n-data-table v-else :columns="userColumns" :data="userRank" size="small" :bordered="false" />
        </n-card>
      </n-tab-pane>

      <!-- 历史 -->
      <n-tab-pane name="history">
        <template #tab><IosIcon name="check" :size="16" /> 历史</template>
        <n-card size="small" style="padding: 0; overflow: auto;">
          <LoadingState v-if="historyLoading" compact />
          <n-empty v-else-if="!historyItems.length" description="暂无观看记录" />
          <n-data-table v-else :columns="historyColumns" :data="historyItems" size="small" :bordered="false" />
        </n-card>
      </n-tab-pane>

      <!-- 质量 -->
      <n-tab-pane name="quality">
        <template #tab><IosIcon name="film" :size="16" /> 质量</template>
        <div class="stat-cards">
          <StatCard label="电影总数" :value="quality?.total_count || 0" />
          <StatCard label="转码率" :value="(quality?.transcoding_rate || 0) + '%'" :highlight="(quality?.transcoding_rate || 0) > 50" />
          <StatCard label="扫描时间" :value="quality?.scan_time?.slice(5, 16) || '-'" />
        </div>
        <div class="section-grid-3">
          <n-card size="small">
            <template #header><CardTitle icon="ratio" title="分辨率分布" /></template>
            <PieChart v-if="resolutionData.length" :data="resolutionData" height="200px" />
            <n-empty v-else description="暂无数据" />
          </n-card>
          <n-card size="small">
            <template #header><CardTitle icon="film" title="编码分布" /></template>
            <PieChart v-if="codecData.length" :data="codecData" height="200px" />
            <n-empty v-else description="暂无数据" />
          </n-card>
          <n-card size="small">
            <template #header><CardTitle icon="eye" title="HDR 分布" /></template>
            <PieChart v-if="hdrData.length" :data="hdrData" height="200px" />
            <n-empty v-else description="暂无数据" />
          </n-card>
        </div>
      </n-tab-pane>
    </n-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import type { DataTableColumns } from 'naive-ui'
import { NTabs, NTabPane, NCard, NTag, NSelect, NEmpty, NDataTable } from 'naive-ui'
import PageHeader from '@/components/common/PageHeader.vue'
import CardTitle from '@/components/common/CardTitle.vue'
import IosIcon from '@/components/common/IosIcon.vue'
import StatCard from '@/components/common/StatCard.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import HeatmapChart from '@/components/charts/HeatmapChart.vue'
import PieChart from '@/components/charts/PieChart.vue'
import AreaChart from '@/components/charts/AreaChart.vue'
import BarChart from '@/components/charts/BarChart.vue'
import { analyticsApi } from '@/api/analytics'
import type { ClockHeatmap, DeviceItem, GenreItem, HotRankItem, DurationRankItem, UserRankItem, QualityData, WatchHistoryItem } from '@/api/analytics'

const days = ref(30)
const activeTab = ref('overview')
const heatmapData = ref<number[][] | null>(null)
const devices = ref<DeviceItem[]>([])
const genres = ref<GenreItem[]>([])
const hotRank = ref<HotRankItem[]>([])
const durationRank = ref<DurationRankItem[]>([])
const userRank = ref<UserRankItem[]>([])
const historyItems = ref<WatchHistoryItem[]>([])
const historyLoading = ref(false)
const quality = ref<QualityData | null>(null)
const trendX = ref<string[]>([])
const trendY = ref<number[]>([])

const daysOptions = [
  { label: '近 7 天', value: 7 },
  { label: '近 30 天', value: 30 },
  { label: '近 90 天', value: 90 },
]

const resLabels: Record<string, string> = { '4k': '4K UHD', '1080p': '1080p FHD', '720p': '720p HD', 'sd': 'SD 标清' }
const codecLabels: Record<string, string> = { hevc: 'HEVC (H.265)', h264: 'H.264 (AVC)', av1: 'AV1', other: '其他' }
const hdrLabels: Record<string, string> = { dolby_vision: 'Dolby Vision', hdr10: 'HDR10', sdr: 'SDR' }

const resolutionData = computed(() => quality.value?.resolution ? Object.entries(quality.value.resolution).map(([k, v]) => ({ name: resLabels[k] || k, value: v })) : [])
const codecData = computed(() => quality.value?.codec ? Object.entries(quality.value.codec).map(([k, v]) => ({ name: codecLabels[k] || k, value: v })) : [])
const hdrData = computed(() => quality.value?.hdr ? Object.entries(quality.value.hdr).map(([k, v]) => ({ name: hdrLabels[k] || k, value: v })) : [])

const userColumns: DataTableColumns = [
  { title: '排名', key: 'rank', width: 60, render: (_r: any, i: number) => h(NTag, { type: i < 3 ? 'info' : 'default', size: 'tiny', round: true }, { default: () => i + 1 }) },
  { title: '用户', key: 'username' },
  { title: '播放次数', key: 'play_count', sorter: (a: any, b: any) => a.play_count - b.play_count },
  { title: '总时长', key: 'total_duration_min', render: (r: any) => formatDuration(r.total_duration_min), sorter: (a: any, b: any) => a.total_duration_min - b.total_duration_min },
  { title: '最近播放', key: 'last_played', render: (r: any) => new Date(r.last_played).toLocaleDateString('zh-CN') },
]

const historyColumns: DataTableColumns = [
  { title: '用户', key: 'user_name', width: 100 },
  { title: '内容', key: 'item_name', ellipsis: true },
  { title: '设备', key: 'device', width: 100, ellipsis: true },
  { title: '时间', key: 'start_time', width: 160, render: (r: any) => new Date(r.start_time).toLocaleString('zh-CN') },
  { title: '时长', key: 'duration_min', width: 80, render: (r: any) => r.duration_min + '分钟' },
  { title: '完成度', key: 'pct_complete', width: 100, render: (r: any) => r.pct_complete + '%' },
]

function formatDuration(min: number) { if (min < 60) return `${min}分钟`; return `${Math.floor(min / 60)}小时${min % 60 ? min % 60 + '分' : ''}` }

async function refreshAll() {
  const d = days.value
  const [hRes, devRes, genRes, hotRes, durRes, usrRes, qRes, trRes] = await Promise.all([
    analyticsApi.clock24h(d), analyticsApi.deviceDist(d), analyticsApi.genrePreference(d),
    analyticsApi.hotRank(d), analyticsApi.durationRank(d), analyticsApi.userRank(d),
    analyticsApi.quality(d), analyticsApi.playTrend(d),
  ])
  heatmapData.value = hRes.data?.grid ?? null
  devices.value = devRes.data ?? []
  genres.value = genRes.data ?? []
  hotRank.value = hotRes.data ?? []
  durationRank.value = durRes.data ?? []
  userRank.value = usrRes.data ?? []
  quality.value = qRes.data ?? null
  const trend = trRes.data ?? []
  trendX.value = trend.map((t: any) => t.date.slice(5))
  trendY.value = trend.map((t: any) => t.play_count)
}

async function loadHistory() {
  historyLoading.value = true
  try { const res = await analyticsApi.watchHistory({ days: days.value, page_size: 50 }); historyItems.value = res.data?.items ?? [] }
  finally { historyLoading.value = false }
}

onMounted(() => { refreshAll(); loadHistory() })
</script>

<style scoped>
.section-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 12px; }
.section-grid-3 { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 12px; }
.stat-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px; }
.genre-grid { display: flex; flex-wrap: wrap; gap: 8px; padding: 4px 0; }
</style>
