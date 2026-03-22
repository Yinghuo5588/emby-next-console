<template>
  <div>
    <div class="page-title">
      <IosIcon name="chart" :size="22" color="var(--brand)" />
      <span>观看统计</span>
    </div>

    <LoadingState v-if="loading" compact />
    <template v-else-if="stats">

      <!-- 生物钟 -->
      <n-card v-if="hasClock" size="small" style="margin-bottom: 16px">
        <template #header><CardTitle icon="clock" title="观影生物钟" /></template>
        <HeatmapChart :data="stats.clock" height="200px" />
      </n-card>

      <!-- 播放趋势 -->
      <n-card v-if="stats.trend?.length" size="small" style="margin-bottom: 16px">
        <template #header><CardTitle icon="chart" title="播放趋势" /></template>
        <AreaChart :x-data="trendX" :series="[{ name: '播放次数', data: trendY }]" height="200px" />
      </n-card>

      <!-- 双列：设备 + 热门 -->
      <div class="grid-2">
        <n-card v-if="stats.devices?.length" size="small">
          <template #header><CardTitle icon="device" title="设备分布" /></template>
          <PieChart :data="stats.devices.map(d => ({ name: d.device, value: d.count }))" height="240px" />
        </n-card>
        <n-card v-if="stats.top_media?.length" size="small">
          <template #header><CardTitle icon="fire" title="热门内容" icon-color="#FF3B30" /></template>
          <BarChart :y-data="topNames" :data="topCounts" horizontal height="240px" color="#FF3B30" />
        </n-card>
      </div>

      <!-- 最近观看 -->
      <n-card v-if="stats.recent?.length" size="small" style="margin-top: 16px">
        <template #header><CardTitle icon="clock" title="最近观看" /></template>
        <div v-for="(r, i) in stats.recent.slice(0, 8)" :key="i" class="recent-row">
          <div style="font-weight: 500">{{ r.clean_name }}</div>
          <div style="font-size: 12px; color: var(--text-muted)">{{ r.device }} · {{ formatMin(r.play_duration) }} · {{ timeAgo(r.date_created) }}</div>
        </div>
      </n-card>

      <n-empty v-if="!hasData" description="看几部电影之后这里就会有内容啦" />
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NCard, NEmpty } from 'naive-ui'
import LoadingState from '@/components/common/LoadingState.vue'
import CardTitle from '@/components/common/CardTitle.vue'
import IosIcon from '@/components/common/IosIcon.vue'
import HeatmapChart from '@/components/charts/HeatmapChart.vue'
import PieChart from '@/components/charts/PieChart.vue'
import AreaChart from '@/components/charts/AreaChart.vue'
import BarChart from '@/components/charts/BarChart.vue'
import { portalApi, type PortalStats } from '@/api/portal'

const loading = ref(true)
const stats = ref<PortalStats | null>(null)

const hasClock = computed(() => stats.value?.clock?.some(row => row.some(v => v > 0)) ?? false)
const hasData = computed(() => hasClock.value || (stats.value?.top_media?.length ?? 0) > 0 || (stats.value?.recent?.length ?? 0) > 0)
const trendX = computed(() => stats.value?.trend?.map(t => t.date.slice(5)) ?? [])
const trendY = computed(() => stats.value?.trend?.map(t => t.play_count) ?? [])
const topNames = computed(() => stats.value?.top_media?.slice(0, 10).map(m => m.clean_name) ?? [])
const topCounts = computed(() => stats.value?.top_media?.slice(0, 10).map(m => m.play_count) ?? [])

function formatMin(seconds: number) { if (!seconds) return '0分钟'; const m = Math.round(seconds / 60); if (m < 60) return `${m}分钟`; return `${Math.floor(m / 60)}小时${m % 60 ? m % 60 + '分' : ''}` }
function timeAgo(dateStr: string) { if (!dateStr) return ''; const d = new Date(dateStr.replace(' ', 'T')); const diff = Date.now() - d.getTime(); const min = Math.floor(diff / 60000); if (min < 60) return `${min}分钟前`; const h = Math.floor(min / 60); if (h < 24) return `${h}小时前`; return `${Math.floor(h / 24)}天前` }

onMounted(async () => { try { stats.value = (await portalApi.stats()).data ?? null } finally { loading.value = false } })
</script>

<style scoped>
.page-title { display: flex; align-items: center; gap: 8px; font-size: 18px; font-weight: 700; margin-bottom: 16px; }
.grid-2 { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }
.recent-row { padding: 8px 0; border-bottom: 0.5px solid var(--separator); }
.recent-row:last-child { border-bottom: none; }
</style>
