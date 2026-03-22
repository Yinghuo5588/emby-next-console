<template>
  <div>
    <div style="font-size:18px;font-weight:700;margin-bottom:16px">📊 观看统计</div>

    <LoadingState v-if="loading" compact />
    <template v-else-if="stats">
      <n-card v-if="hasClock" title="🕐 生物钟" size="small" style="margin-bottom:16px">
        <div class="clock-grid">
          <div class="clock-col" v-for="(col, hi) in clockCols" :key="hi">
            <div v-for="(val, di) in col" :key="di" class="clock-cell" :style="{ background: cellColor(val) }" :title="`${hi}:00 ${dowLabels[di]} — ${val} 次`" />
          </div>
        </div>
        <div class="clock-days"><span v-for="d in dowLabels" :key="d">{{ d }}</span></div>
      </n-card>

      <n-card v-if="stats.devices?.length" title="📱 设备分布" size="small" style="margin-bottom:16px">
        <div v-for="d in stats.devices" :key="d.device" class="bar-row">
          <span class="bar-label">{{ d.device }}</span>
          <n-progress :percentage="barPct(d.count)" :show-indicator="false" style="flex:1" />
          <span class="bar-val">{{ d.count }}</span>
        </div>
      </n-card>

      <n-card v-if="stats.trend?.length" title="📈 播放趋势（30天）" size="small" style="margin-bottom:16px">
        <div class="trend-bars">
          <div v-for="t in stats.trend" :key="t.date" class="trend-item">
            <div class="trend-bar" :style="{ height: trendPct(t.play_count) }"></div>
            <div class="trend-label">{{ t.date.slice(5) }}</div>
          </div>
        </div>
      </n-card>

      <n-empty v-if="!stats.top_media?.length && !stats.recent?.length" description="看几部电影之后这里就会有内容啦" />
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NCard, NProgress, NEmpty } from 'naive-ui'
import LoadingState from '@/components/common/LoadingState.vue'
import { portalApi, type PortalStats } from '@/api/portal'

const loading = ref(true)
const stats = ref<PortalStats | null>(null)
const dowLabels = ['一', '二', '三', '四', '五', '六', '日']

const clockCols = computed(() => stats.value?.clock ?? [])
const hasClock = computed(() => stats.value?.clock?.some(row => row.some(v => v > 0)) ?? false)

function cellColor(val: number) { if (val === 0) return 'var(--bg-secondary)'; if (val <= 2) return '#dbeafe'; if (val <= 5) return '#93c5fd'; if (val <= 10) return '#3b82f6'; return '#1d4ed8' }
function barPct(val: number) { const max = Math.max(...(stats.value?.devices?.map(d => d.count) || [1])); return Math.round(val / max * 100) }
const maxTrend = computed(() => Math.max(...(stats.value?.trend?.map(t => t.play_count) || [1]), 1))
function trendPct(val: number) { return (val / maxTrend.value * 100) + '%' }

onMounted(async () => { try { stats.value = (await portalApi.stats()).data ?? null } finally { loading.value = false } })
</script>

<style scoped>
.clock-grid { display: flex; gap: 2px; justify-content: center; }
.clock-col { display: flex; flex-direction: column; gap: 2px; }
.clock-cell { width: 12px; height: 12px; border-radius: 2px; }
.clock-days { display: flex; justify-content: space-around; margin-top: 4px; font-size: 11px; color: var(--text-muted); }
.bar-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.bar-label { width: 80px; font-size: 13px; text-align: right; flex-shrink: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bar-val { width: 40px; font-size: 13px; color: var(--text-muted); }
.trend-bars { display: flex; align-items: flex-end; gap: 3px; height: 100px; }
.trend-item { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100%; }
.trend-bar { width: 100%; background: var(--brand); border-radius: 2px 2px 0 0; min-height: 2px; }
.trend-label { font-size: 9px; color: var(--text-muted); margin-top: 2px; writing-mode: vertical-lr; transform: rotate(180deg); }
</style>
