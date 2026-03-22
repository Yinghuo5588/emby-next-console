<template>
  <div>
    <PageHeader title="数据分析" desc="多维度观看数据分析">
      <template #actions>
        <select v-model="days" @change="refreshAll" class="days-select">
          <option :value="7">近 7 天</option>
          <option :value="30">近 30 天</option>
          <option :value="90">近 90 天</option>
        </select>
      </template>
    </PageHeader>

    <!-- Tab 栏 -->
    <div class="tab-bar">
      <button v-for="t in tabs" :key="t.key" class="tab-btn" :class="{ active: activeTab === t.key }" @click="activeTab = t.key">
        {{ t.icon }} {{ t.label }}
      </button>
    </div>

    <!-- Tab 1: 总览 -->
    <div v-show="activeTab === 'overview'">
      <div class="grid-2">
        <div class="card">
          <h4>24H 观影生物钟</h4>
          <HeatmapChart v-if="heatmapData" :data="heatmapData" />
          <EmptyState v-else title="暂无数据" />
        </div>
        <div class="card">
          <h4>设备分布</h4>
          <div v-if="devices.length">
            <div v-for="d in devices" :key="d.device" class="bar-row">
              <span class="bar-label">{{ d.device }}</span>
              <div class="bar-track"><div class="bar-fill" :style="{ width: barPct(d.count, devices) }"></div></div>
              <span class="bar-val">{{ d.count }}</span>
            </div>
          </div>
          <EmptyState v-else title="暂无数据" />
        </div>
      </div>
      <div class="card" style="margin-top: 16px;">
        <h4>类型偏好</h4>
        <div v-if="genres.length" class="genre-grid">
          <div v-for="g in genres" :key="g.genre" class="genre-item">
            <span class="genre-name">{{ g.genre }}</span>
            <span class="genre-pct">{{ g.percentage }}%</span>
          </div>
        </div>
        <EmptyState v-else title="暂无数据" />
      </div>
    </div>

    <!-- Tab 2: 排行 -->
    <div v-show="activeTab === 'ranking'">
      <div class="grid-2">
        <div class="card">
          <h4>热度排行</h4>
          <div v-if="hotRank.length">
            <div v-for="(item, i) in hotRank" :key="i" class="rank-row">
              <span class="rank-num" :class="{ top3: i < 3 }">{{ i + 1 }}</span>
              <span class="rank-name">{{ item.item_name }}</span>
              <span class="rank-val">{{ item.play_count }}次</span>
            </div>
          </div>
          <EmptyState v-else title="暂无数据" />
        </div>
        <div class="card">
          <h4>时长排行</h4>
          <div v-if="durationRank.length">
            <div v-for="(item, i) in durationRank" :key="i" class="rank-row">
              <span class="rank-num" :class="{ top3: i < 3 }">{{ i + 1 }}</span>
              <span class="rank-name">{{ item.item_name }}</span>
              <span class="rank-val">{{ formatDuration(item.total_duration_min) }}</span>
            </div>
          </div>
          <EmptyState v-else title="暂无数据" />
        </div>
      </div>
      <div class="card" style="margin-top: 16px;">
        <h4>用户排行</h4>
        <div v-if="userRank.length">
          <table>
            <thead><tr><th>排名</th><th>用户</th><th>播放次数</th><th>总时长</th><th>最近播放</th></tr></thead>
            <tbody>
              <tr v-for="(u, i) in userRank" :key="i">
                <td><span class="rank-num" :class="{ top3: i < 3 }">{{ i + 1 }}</span></td>
                <td>{{ u.username }}</td>
                <td>{{ u.play_count }}</td>
                <td>{{ formatDuration(u.total_duration_min) }}</td>
                <td class="muted">{{ new Date(u.last_played).toLocaleDateString('zh-CN') }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <EmptyState v-else title="暂无数据" />
      </div>
    </div>

    <!-- Tab 3: 历史 -->
    <div v-show="activeTab === 'history'">
      <div class="card" style="padding: 0; overflow: auto;">
        <LoadingState v-if="historyLoading" height="120px" />
        <table v-else>
          <thead><tr><th>用户</th><th>内容</th><th>设备</th><th>时间</th><th>时长</th><th>完成度</th></tr></thead>
          <tbody>
            <tr v-if="!historyItems.length"><td colspan="6" class="empty">暂无观看记录</td></tr>
            <tr v-for="(h, i) in historyItems" :key="i">
              <td>{{ h.user_name }}</td>
              <td>{{ h.item_name }}</td>
              <td class="muted">{{ h.device }}</td>
              <td class="muted">{{ new Date(h.start_time).toLocaleString('zh-CN') }}</td>
              <td>{{ h.duration_min }}分钟</td>
              <td>
                <div class="pct-bar"><div class="pct-fill" :style="{ width: h.pct_complete + '%' }"></div></div>
                <span class="muted" style="margin-left:4px">{{ h.pct_complete }}%</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Tab 4: 质量 -->
    <div v-show="activeTab === 'quality'">
      <div class="grid-2">
        <div class="card">
          <h4>分辨率分布</h4>
          <div v-if="quality?.resolution_dist?.length">
            <div v-for="r in quality.resolution_dist" :key="r.resolution" class="bar-row">
              <span class="bar-label">{{ r.resolution }}</span>
              <div class="bar-track"><div class="bar-fill" :style="{ width: barPct(r.count, quality.resolution_dist) }"></div></div>
              <span class="bar-val">{{ r.count }}</span>
            </div>
          </div>
          <EmptyState v-else title="暂无数据" />
        </div>
        <div class="card">
          <h4>转码率</h4>
          <div v-if="quality" style="text-align:center; padding: 24px;">
            <div style="font-size: 36px; font-weight: 700; color: var(--brand);">{{ quality.transcoding_rate }}%</div>
            <div class="muted">转码播放占比</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import HeatmapChart from '@/components/charts/HeatmapChart.vue'
import { analyticsApi } from '@/api/analytics'
import type { ClockHeatmap, DeviceItem, GenreItem, HotRankItem, DurationRankItem, UserRankItem, QualityData, WatchHistoryItem } from '@/api/analytics'

const days = ref(30)
const activeTab = ref('overview')

const tabs = [
  { key: 'overview', icon: '📊', label: '总览' },
  { key: 'ranking', icon: '🏆', label: '排行' },
  { key: 'history', icon: '📋', label: '历史' },
  { key: 'quality', icon: '🎬', label: '质量' },
]

// 总览数据
const heatmapData = ref<number[][] | null>(null)
const devices = ref<DeviceItem[]>([])
const genres = ref<GenreItem[]>([])

// 排行数据
const hotRank = ref<HotRankItem[]>([])
const durationRank = ref<DurationRankItem[]>([])
const userRank = ref<UserRankItem[]>([])

// 历史数据
const historyItems = ref<WatchHistoryItem[]>([])
const historyLoading = ref(false)

// 质量数据
const quality = ref<QualityData | null>(null)

function barPct(val: number, arr: { count: number }[]) {
  const max = Math.max(...arr.map(a => a.count), 1)
  return (val / max * 100) + '%'
}

function formatDuration(min: number) {
  if (min < 60) return `${min}分钟`
  return `${Math.floor(min / 60)}小时${min % 60 ? min % 60 + '分' : ''}`
}

async function refreshAll() {
  const d = days.value
  // 总览
  const [hRes, devRes, genRes] = await Promise.all([
    analyticsApi.clock24h(d),
    analyticsApi.deviceDist(d),
    analyticsApi.genrePreference(d),
  ])
  heatmapData.value = hRes.data?.grid ?? null
  devices.value = devRes.data ?? []
  genres.value = genRes.data ?? []

  // 排行
  const [hotRes, durRes, usrRes] = await Promise.all([
    analyticsApi.hotRank(d),
    analyticsApi.durationRank(d),
    analyticsApi.userRank(d),
  ])
  hotRank.value = hotRes.data ?? []
  durationRank.value = durRes.data ?? []
  userRank.value = usrRes.data ?? []

  // 质量
  const qRes = await analyticsApi.quality(d)
  quality.value = qRes.data ?? null
}

async function loadHistory() {
  historyLoading.value = true
  try {
    const res = await analyticsApi.watchHistory({ days: days.value, page_size: 50 })
    historyItems.value = res.data?.items ?? []
  } finally {
    historyLoading.value = false
  }
}

onMounted(() => { refreshAll(); loadHistory() })
</script>

<style scoped>
.days-select { min-width: 100px; }
.tab-bar { display: flex; gap: 4px; margin-bottom: 16px; overflow-x: auto; }
.tab-btn { padding: 6px 14px; border: 1px solid var(--border); border-radius: 6px; background: var(--bg); color: var(--text-muted); cursor: pointer; font-size: 13px; white-space: nowrap; }
.tab-btn.active { background: var(--brand); color: #fff; border-color: var(--brand); }
.grid-2 { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
.card h4 { margin: 0 0 12px; font-size: 15px; }
.bar-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.bar-label { width: 80px; font-size: 13px; text-align: right; flex-shrink: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bar-track { flex: 1; height: 8px; background: var(--bg-secondary); border-radius: 4px; overflow: hidden; }
.bar-fill { height: 100%; background: var(--brand); border-radius: 4px; min-width: 2px; transition: width 0.3s; }
.bar-val { width: 40px; font-size: 13px; color: var(--text-muted); }
.genre-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.genre-item { padding: 4px 12px; border-radius: 16px; background: var(--bg-secondary); font-size: 13px; }
.genre-name { font-weight: 500; }
.genre-pct { color: var(--text-muted); margin-left: 4px; }
.rank-row { display: flex; align-items: center; gap: 8px; padding: 6px 0; border-bottom: 1px solid var(--border); }
.rank-row:last-child { border-bottom: none; }
.rank-num { width: 24px; height: 24px; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600; background: var(--bg-secondary); }
.rank-num.top3 { background: var(--brand); color: #fff; }
.rank-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rank-val { color: var(--text-muted); font-size: 13px; }
.pct-bar { display: inline-block; width: 60px; height: 6px; background: var(--bg-secondary); border-radius: 3px; overflow: hidden; vertical-align: middle; }
.pct-fill { height: 100%; background: var(--brand); border-radius: 3px; }
.muted { color: var(--text-muted); font-size: 12px; }
.empty { text-align: center; padding: 32px !important; color: var(--text-muted); }
</style>