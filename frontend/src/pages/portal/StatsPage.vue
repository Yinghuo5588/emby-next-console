<template>
  <div class="portal-stats">
    <h3 class="page-title">📊 观看统计</h3>

    <LoadingState v-if="loading" height="120px" />
    <template v-else-if="stats">
      <!-- 生物钟热力图 -->
      <div class="card" v-if="hasClock" style="margin-bottom: 16px;">
        <h4 style="margin: 0 0 10px; font-size: 15px;">🕐 生物钟</h4>
        <div class="clock-grid">
          <div class="clock-col" v-for="(col, hi) in clockCols" :key="hi">
            <div
              v-for="(val, di) in col"
              :key="di"
              class="clock-cell"
              :style="{ background: cellColor(val) }"
              :title="`${hi}:00 ${dowLabels[di]} — ${val} 次`"
            />
          </div>
        </div>
        <div class="clock-days">
          <span v-for="d in dowLabels" :key="d">{{ d }}</span>
        </div>
      </div>

      <!-- 设备分布 -->
      <div v-if="stats.devices?.length" class="card" style="margin-bottom: 16px;">
        <h4 style="margin: 0 0 10px; font-size: 15px;">📱 设备分布</h4>
        <div v-for="d in stats.devices" :key="d.device" class="bar-row">
          <span class="bar-label">{{ d.device }}</span>
          <div class="bar-track"><div class="bar-fill" :style="{ width: barPct(d.count) }"></div></div>
          <span class="bar-val">{{ d.count }}</span>
        </div>
      </div>

      <!-- 趋势 -->
      <div v-if="stats.trend?.length" class="card" style="margin-bottom: 16px;">
        <h4 style="margin: 0 0 10px; font-size: 15px;">📈 播放趋势（30天）</h4>
        <div class="trend-bars">
          <div v-for="t in stats.trend" :key="t.date" class="trend-item">
            <div class="trend-bar" :style="{ height: trendPct(t.play_count) }"></div>
            <div class="trend-label">{{ t.date.slice(5) }}</div>
          </div>
        </div>
      </div>

      <EmptyState v-if="!stats.top_media?.length && !stats.recent?.length" title="暂无播放数据" desc="看几部电影之后这里就会有内容啦" />
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import LoadingState from '@/components/common/LoadingState.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { portalApi, type PortalStats } from '@/api/portal'

const loading = ref(true)
const stats = ref<PortalStats | null>(null)

const dowLabels = ['一', '二', '三', '四', '五', '六', '日']

const clockCols = computed(() => {
  if (!stats.value?.clock) return []
  return stats.value.clock // 24 x 7
})

const hasClock = computed(() => {
  if (!stats.value?.clock) return false
  return stats.value.clock.some(row => row.some(v => v > 0))
})

function cellColor(val: number) {
  if (val === 0) return 'var(--bg-secondary)'
  if (val <= 2) return '#dbeafe'
  if (val <= 5) return '#93c5fd'
  if (val <= 10) return '#3b82f6'
  return '#1d4ed8'
}

function barPct(val: number) {
  const max = Math.max(...(stats.value?.devices?.map(d => d.count) || [1]))
  return (val / max * 100) + '%'
}

const maxTrend = computed(() => Math.max(...(stats.value?.trend?.map(t => t.play_count) || [1]), 1))

function trendPct(val: number) {
  return (val / maxTrend.value * 100) + '%'
}

onMounted(async () => {
  try {
    const res = await portalApi.stats()
    stats.value = res.data ?? null
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page-title { font-size: 18px; margin-bottom: 16px; }
.clock-grid { display: flex; gap: 2px; justify-content: center; }
.clock-col { display: flex; flex-direction: column; gap: 2px; }
.clock-cell { width: 12px; height: 12px; border-radius: 2px; background: var(--bg-secondary); }
.clock-days { display: flex; justify-content: space-around; margin-top: 4px; font-size: 11px; color: var(--text-muted); }
.bar-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.bar-label { width: 80px; font-size: 13px; text-align: right; flex-shrink: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bar-track { flex: 1; height: 8px; background: var(--bg-secondary); border-radius: 4px; overflow: hidden; }
.bar-fill { height: 100%; background: var(--brand); border-radius: 4px; min-width: 2px; transition: width 0.3s; }
.bar-val { width: 40px; font-size: 13px; color: var(--text-muted); }
.trend-bars { display: flex; align-items: flex-end; gap: 3px; height: 100px; }
.trend-item { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100%; }
.trend-bar { width: 100%; background: var(--brand); border-radius: 2px 2px 0 0; min-height: 2px; transition: height 0.3s; }
.trend-label { font-size: 9px; color: var(--text-muted); margin-top: 2px; writing-mode: vertical-lr; transform: rotate(180deg); }
</style>
