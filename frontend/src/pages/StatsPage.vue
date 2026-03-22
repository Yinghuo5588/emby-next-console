<template>
  <div>
    <PageHeader title="数据分析" desc="多维度观看数据分析">
      <template #actions>
        <n-select v-model:value="days" :options="daysOptions" size="small" style="width: 120px" @update:value="refreshAll" />
      </template>
    </PageHeader>

    <n-tabs v-model:value="activeTab" type="segment" size="small" style="margin-bottom: 16px;">
      <n-tab-pane name="overview" tab="📊 总览">
        <div class="grid-2">
          <n-card title="24H 观影生物钟" size="small">
            <HeatmapChart v-if="heatmapData" :data="heatmapData" />
            <n-empty v-else description="暂无数据" />
          </n-card>
          <n-card title="设备分布" size="small">
            <div v-if="devices.length">
              <div v-for="d in devices" :key="d.device" class="bar-row">
                <span class="bar-label">{{ d.device }}</span>
                <div class="bar-track"><div class="bar-fill" :style="{ width: barPct(d.count, devices) }"></div></div>
                <span class="bar-val">{{ d.count }}</span>
              </div>
            </div>
            <n-empty v-else description="暂无数据" />
          </n-card>
        </div>
        <n-card title="类型偏好" size="small" style="margin-top: 16px;">
          <div v-if="genres.length" class="genre-grid">
            <n-tag v-for="g in genres" :key="g.genre" size="small" round>{{ g.genre }} {{ g.percentage }}%</n-tag>
          </div>
          <n-empty v-else description="暂无数据" />
        </n-card>
      </n-tab-pane>

      <n-tab-pane name="ranking" tab="🏆 排行">
        <div class="grid-2">
          <n-card title="热度排行" size="small">
            <div v-if="hotRank.length">
              <div v-for="(item, i) in hotRank" :key="i" class="rank-row">
                <n-tag :type="i < 3 ? 'info' : 'default'" size="tiny" round>{{ i + 1 }}</n-tag>
                <span class="rank-name">{{ item.item_name }}</span>
                <span class="rank-val">{{ item.play_count }}次</span>
              </div>
            </div>
            <n-empty v-else description="暂无数据" />
          </n-card>
          <n-card title="时长排行" size="small">
            <div v-if="durationRank.length">
              <div v-for="(item, i) in durationRank" :key="i" class="rank-row">
                <n-tag :type="i < 3 ? 'info' : 'default'" size="tiny" round>{{ i + 1 }}</n-tag>
                <span class="rank-name">{{ item.item_name }}</span>
                <span class="rank-val">{{ formatDuration(item.total_duration_min) }}</span>
              </div>
            </div>
            <n-empty v-else description="暂无数据" />
          </n-card>
        </div>
        <n-card title="用户排行" size="small" style="margin-top: 16px;">
          <n-empty v-if="!userRank.length" description="暂无数据" />
          <n-data-table v-else :columns="userColumns" :data="userRank" size="small" :bordered="false" />
        </n-card>
      </n-tab-pane>

      <n-tab-pane name="history" tab="📋 历史">
        <n-card size="small" style="padding: 0; overflow: auto;">
          <LoadingState v-if="historyLoading" compact />
          <n-empty v-else-if="!historyItems.length" description="暂无观看记录" />
          <n-data-table v-else :columns="historyColumns" :data="historyItems" size="small" :bordered="false" />
        </n-card>
      </n-tab-pane>

      <n-tab-pane name="quality" tab="🎬 质量">
        <div class="quality-summary">
          <StatCard label="电影总数" :value="quality?.total_count || 0" />
          <StatCard label="转码率" :value="(quality?.transcoding_rate || 0) + '%'" :highlight="(quality?.transcoding_rate || 0) > 50" />
          <StatCard label="扫描时间" :value="quality?.scan_time?.slice(5, 16) || '-'" />
        </div>
        <div class="grid-3">
          <n-card title="📐 分辨率分布" size="small">
            <div v-if="quality?.resolution">
              <div v-for="(count, key) in quality.resolution" :key="key" class="bar-row">
                <span class="bar-label">{{ resLabels[key] || key }}</span>
                <div class="bar-track"><div class="bar-fill bar-blue" :style="{ width: pct(count, quality.resolution) }"></div></div>
                <span class="bar-val">{{ count }}</span>
              </div>
            </div>
          </n-card>
          <n-card title="🎞️ 编码分布" size="small">
            <div v-if="quality?.codec">
              <div v-for="(count, key) in quality.codec" :key="key" class="bar-row">
                <span class="bar-label">{{ codecLabels[key] || key }}</span>
                <div class="bar-track"><div class="bar-fill bar-green" :style="{ width: pct(count, quality.codec) }"></div></div>
                <span class="bar-val">{{ count }}</span>
              </div>
            </div>
          </n-card>
          <n-card title="🌈 HDR 分布" size="small">
            <div v-if="quality?.hdr">
              <div v-for="(count, key) in quality.hdr" :key="key" class="bar-row">
                <span class="bar-label">{{ hdrLabels[key] || key }}</span>
                <div class="bar-track"><div class="bar-fill bar-purple" :style="{ width: pct(count, quality.hdr) }"></div></div>
                <span class="bar-val">{{ count }}</span>
              </div>
            </div>
          </n-card>
        </div>
      </n-tab-pane>
    </n-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import type { DataTableColumns } from 'naive-ui'
import { NTabs, NTabPane, NCard, NTag, NSelect, NEmpty, NDataTable } from 'naive-ui'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import HeatmapChart from '@/components/charts/HeatmapChart.vue'
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

const daysOptions = [
  { label: '近 7 天', value: 7 },
  { label: '近 30 天', value: 30 },
  { label: '近 90 天', value: 90 },
]

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

function barPct(val: number, arr: { count: number }[]) { const max = Math.max(...arr.map(a => a.count), 1); return (val / max * 100) + '%' }
function pct(val: number, obj: Record<string, number>) { const max = Math.max(...Object.values(obj), 1); return (val / max * 100) + '%' }
function formatDuration(min: number) { if (min < 60) return `${min}分钟`; return `${Math.floor(min / 60)}小时${min % 60 ? min % 60 + '分' : ''}` }

const resLabels: Record<string, string> = { '4k': '4K UHD', '1080p': '1080p FHD', '720p': '720p HD', 'sd': 'SD 标清' }
const codecLabels: Record<string, string> = { hevc: 'HEVC (H.265)', h264: 'H.264 (AVC)', av1: 'AV1', other: '其他' }
const hdrLabels: Record<string, string> = { dolby_vision: 'Dolby Vision', hdr10: 'HDR10', sdr: 'SDR' }

async function refreshAll() {
  const d = days.value
  const [hRes, devRes, genRes, hotRes, durRes, usrRes, qRes] = await Promise.all([
    analyticsApi.clock24h(d), analyticsApi.deviceDist(d), analyticsApi.genrePreference(d),
    analyticsApi.hotRank(d), analyticsApi.durationRank(d), analyticsApi.userRank(d),
    analyticsApi.quality(d),
  ])
  heatmapData.value = hRes.data?.grid ?? null
  devices.value = devRes.data ?? []
  genres.value = genRes.data ?? []
  hotRank.value = hotRes.data ?? []
  durationRank.value = durRes.data ?? []
  userRank.value = usrRes.data ?? []
  quality.value = qRes.data ?? null
}

async function loadHistory() {
  historyLoading.value = true
  try { const res = await analyticsApi.watchHistory({ days: days.value, page_size: 50 }); historyItems.value = res.data?.items ?? [] }
  finally { historyLoading.value = false }
}

onMounted(() => { refreshAll(); loadHistory() })
</script>

<style scoped>
.grid-2 { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
.grid-3 { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
.quality-summary { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px; }
.bar-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.bar-label { width: 80px; font-size: 13px; text-align: right; flex-shrink: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bar-track { flex: 1; height: 8px; background: var(--bg-secondary); border-radius: 4px; overflow: hidden; }
.bar-fill { height: 100%; background: var(--brand); border-radius: 4px; min-width: 2px; transition: width 0.3s; }
.bar-blue { background: #2563eb; }
.bar-green { background: #16a34a; }
.bar-purple { background: #9333ea; }
.bar-val { width: 40px; font-size: 13px; color: var(--text-muted); }
.genre-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.rank-row { display: flex; align-items: center; gap: 8px; padding: 6px 0; border-bottom: 1px solid var(--border); }
.rank-row:last-child { border-bottom: none; }
.rank-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rank-val { color: var(--text-muted); font-size: 13px; }
</style>
