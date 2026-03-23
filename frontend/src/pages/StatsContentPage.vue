<template>
  <div class="stats-page">
    <PageHeader title="内容分析" desc="哪些内容最火？">
      <template #actions>
        <n-button size="small" @click="showFilter = true">
          <span>筛选</span>
          <span v-if="activeFilterCount > 0" class="filter-badge">{{ activeFilterCount }}</span>
        </n-button>
      </template>
    </PageHeader>

    <!-- 当前筛选标签 -->
    <div class="active-filters" v-if="activeFilterCount > 0">
      <n-tag v-if="contentType !== 'all'" size="small" closable @close="contentType = 'all'">
        {{ typeLabel }}
      </n-tag>
      <n-tag v-if="period !== '30d'" size="small" closable @close="period = '30d'">
        {{ periodLabel }}
      </n-tag>
      <n-tag v-if="sortBy !== 'duration'" size="small" closable @close="sortBy = 'duration'">
        {{ sortLabel }}
      </n-tag>
    </div>

    <!-- 排行表 -->
    <div class="ranking-card">
      <div v-if="loading" class="empty-text">加载中...</div>
      <div v-else-if="items.length === 0" class="empty-text">暂无数据</div>
      <div v-else class="ranking-list">
        <div v-for="(item, i) in items" :key="i"
          class="ranking-item"
          :class="{ active: selectedItem?.item_id === item.item_id }"
          @click="selectItem(item)">
          <span class="ranking-num" :class="{ 'num-top': i < 3 }">{{ (page - 1) * size + i + 1 }}</span>
          <n-avatar :src="item.poster_url" :size="44" round class="ranking-avatar" fallback-src="" />
          <div class="ranking-body">
            <div class="ranking-name">{{ item.name }}</div>
            <div class="ranking-meta">
              <span>{{ item.type === 'Movie' ? '电影' : item.type === 'Series' ? '剧集' : item.type }}</span>
              <span>·</span>
              <span>{{ item.play_count }} 次</span>
              <span>·</span>
              <span>{{ formatDuration(item.total_duration_min) }}</span>
            </div>
          </div>
          <div class="ranking-bars desktop-only">
            <div class="bar" :style="{ width: barWidth(item.total_duration_min, maxDuration) + '%' }"></div>
          </div>
        </div>
      </div>
      <div v-if="total > size" class="pagination-row">
        <n-button size="small" :disabled="page <= 1" @click="page--">上一页</n-button>
        <span class="page-info">{{ page }} / {{ Math.ceil(total / size) }}</span>
        <n-button size="small" :disabled="page >= Math.ceil(total / size)" @click="page++">下一页</n-button>
      </div>
    </div>

    <!-- 筛选抽屉 -->
    <n-drawer v-model:show="showFilter" :width="320" placement="bottom" :height="'auto'">
      <n-drawer-content title="筛选" closable :body-content-style="{ padding: '16px' }">
        <div class="filter-group">
          <div class="filter-label">内容类型</div>
          <n-button-group size="small">
            <n-button v-for="t in typeOptions" :key="t.value"
              :type="contentType === t.value ? 'primary' : 'default'"
              @click="contentType = t.value">{{ t.label }}</n-button>
          </n-button-group>
        </div>
        <div class="filter-group">
          <div class="filter-label">时间范围</div>
          <n-button-group size="small">
            <n-button v-for="p in periodOptions" :key="p.value"
              :type="period === p.value ? 'primary' : 'default'"
              @click="period = p.value">{{ p.label }}</n-button>
          </n-button-group>
        </div>
        <div class="filter-group">
          <div class="filter-label">排序方式</div>
          <n-button-group size="small">
            <n-button v-for="s in sortOptions" :key="s.value"
              :type="sortBy === s.value ? 'primary' : 'default'"
              @click="sortBy = s.value">{{ s.label }}</n-button>
          </n-button-group>
        </div>
        <n-button block type="primary" @click="showFilter = false" style="margin-top: 16px">确定</n-button>
      </n-drawer-content>
    </n-drawer>

    <!-- 内容详情抽屉 -->
    <n-drawer v-model:show="showDetail" :width="480" placement="right">
      <n-drawer-content v-if="detail" :title="detail.name" closable>
        <div class="detail-section">
          <div class="detail-header">
            <n-avatar :src="detail.poster_url" :size="64" round />
            <div>
              <h3>{{ detail.name }}</h3>
              <div class="detail-meta">{{ detail.type === 'Movie' ? '电影' : '剧集' }}</div>
            </div>
          </div>
        </div>
        <div class="detail-section" v-if="Object.keys(detail.trend).length > 0">
          <h4>30 天播放趋势</h4>
          <v-chart :option="detailTrendOption" autoresize style="height: 180px" />
        </div>
        <div class="detail-section" v-if="detail.viewers.length > 0">
          <h4>观看用户</h4>
          <div class="viewer-list">
            <div v-for="v in detail.viewers" :key="v.user_id" class="viewer-item">
              <span>{{ v.username }}</span>
              <span class="viewer-meta">{{ v.play_count }} 次 · {{ v.duration_hours }}h</span>
            </div>
          </div>
        </div>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { NButton, NButtonGroup, NTag, NAvatar, NDrawer, NDrawerContent } from 'naive-ui'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'
import PageHeader from '@/components/common/PageHeader.vue'
import { statsApiV3 } from '@/api/stats-v3'

use([LineChart, GridComponent, TooltipComponent, CanvasRenderer])

const route = useRoute()
const showFilter = ref(false)
const contentType = ref('all')
const period = ref('30d')
const sortBy = ref('duration')
const page = ref(1)
const size = ref(20)
const total = ref(0)
const items = ref<any[]>([])
const loading = ref(false)
const selectedItem = ref<any>(null)
const showDetail = ref(false)
const detail = ref<any>(null)

const typeOptions = [{ label: '全部', value: 'all' }, { label: '电影', value: 'movie' }, { label: '剧集', value: 'series' }]
const periodOptions = [{ label: '30天', value: '30d' }, { label: '90天', value: '90d' }, { label: '全部', value: 'all' }]
const sortOptions = [{ label: '按时长', value: 'duration' }, { label: '按次数', value: 'count' }]

const typeLabel = computed(() => typeOptions.find(t => t.value === contentType.value)?.label || '')
const periodLabel = computed(() => periodOptions.find(p => p.value === period.value)?.label || '')
const sortLabel = computed(() => sortOptions.find(s => s.value === sortBy.value)?.label || '')
const activeFilterCount = computed(() => (contentType.value !== 'all' ? 1 : 0) + (period.value !== '30d' ? 1 : 0) + (sortBy.value !== 'duration' ? 1 : 0))
const maxDuration = computed(() => Math.max(...items.value.map(i => i.total_duration_min), 1))

function barWidth(val: number, max: number) { return max > 0 ? (val / max) * 100 : 0 }
function formatDuration(min: number) { return min >= 60 ? `${(min / 60).toFixed(1)}h` : `${Math.round(min)}m` }

async function loadRankings() {
  loading.value = true
  try {
    const res = await statsApiV3.contentRankings({ type: contentType.value, period: period.value, sort: sortBy.value, page: page.value, size: size.value })
    const data = res.data?.data ?? res.data ?? {}
    items.value = data.items || []
    total.value = data.total || 0
  } finally { loading.value = false }
}

async function selectItem(item: any) {
  selectedItem.value = item
  const res = await statsApiV3.contentDetail(item.item_id)
  detail.value = res.data?.data ?? res.data
  showDetail.value = true
}

const detailTrendOption = computed(() => {
  if (!detail.value) return {}
  const labels = Object.keys(detail.value.trend)
  const values = labels.map(k => detail.value.trend[k].hours)
  return {
    tooltip: { trigger: 'axis', valueFormatter: (v: number) => `${v} 小时` },
    grid: { top: 10, right: 10, bottom: 24, left: 36 },
    xAxis: { type: 'category', data: labels, axisLabel: { fontSize: 10, color: '#8e8e93' } },
    yAxis: { type: 'value', axisLabel: { fontSize: 10, color: '#8e8e93' }, splitLine: { lineStyle: { type: 'dashed', color: '#f0f0f0' } } },
    series: [{ type: 'line', data: values, smooth: true, symbol: 'none', lineStyle: { width: 2, color: '#3b82f6' }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(59,130,246,0.2)' }, { offset: 1, color: 'rgba(59,130,246,0.02)' }] } } }],
  }
})

watch([contentType, period, sortBy], () => { page.value = 1; loadRankings() })
watch(page, loadRankings)
onMounted(() => { loadRankings() })
</script>

<style scoped>
.stats-page { padding: 0.5rem 0; }
.active-filters { display: flex; gap: 0.5rem; margin-bottom: 0.75rem; flex-wrap: wrap; }
.filter-badge { display: inline-flex; align-items: center; justify-content: center; width: 16px; height: 16px; border-radius: 50%; background: var(--brand); color: #fff; font-size: 0.65rem; margin-left: 4px; }
.ranking-card { background: var(--surface); border-radius: var(--radius-lg); padding: 0.5rem; border: 1px solid var(--border); }
.ranking-list { display: flex; flex-direction: column; }
.ranking-item { display: flex; align-items: center; gap: 0.5rem; padding: 0.6rem 0.5rem; border-radius: var(--radius); cursor: pointer; transition: background 0.15s; }
.ranking-item:hover, .ranking-item.active { background: var(--bg-secondary); }
.ranking-num { width: 24px; font-size: 0.8rem; font-weight: 700; color: var(--text-muted); text-align: center; flex-shrink: 0; }
.num-top { color: var(--brand); }
.ranking-avatar { flex-shrink: 0; }
.ranking-body { flex: 1; min-width: 0; }
.ranking-name { font-size: 0.9rem; font-weight: 600; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ranking-meta { font-size: 0.75rem; color: var(--text-muted); display: flex; gap: 0.25rem; }
.ranking-bars { width: 80px; flex-shrink: 0; }
.bar { height: 4px; background: var(--brand); border-radius: 2px; transition: width 0.3s; }
.pagination-row { display: flex; align-items: center; justify-content: center; gap: 1rem; padding: 0.75rem 0; }
.page-info { font-size: 0.8rem; color: var(--text-muted); }
.empty-text { text-align: center; padding: 2rem; color: var(--text-muted); font-size: 0.85rem; }
.filter-group { margin-bottom: 1rem; }
.filter-label { font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.5rem; }
.detail-section { margin-bottom: 1.5rem; }
.detail-header { display: flex; gap: 1rem; align-items: center; margin-bottom: 1rem; }
.detail-header h3 { font-size: 1.1rem; font-weight: 700; margin: 0; }
.detail-meta { font-size: 0.8rem; color: var(--text-muted); }
.detail-section h4 { font-size: 0.9rem; font-weight: 600; margin-bottom: 0.75rem; }
.viewer-list { display: flex; flex-direction: column; gap: 0.5rem; }
.viewer-item { display: flex; justify-content: space-between; padding: 0.5rem; background: var(--bg-secondary); border-radius: var(--radius); font-size: 0.85rem; }
.viewer-meta { color: var(--text-muted); font-size: 0.8rem; }
@media (max-width: 767px) {
  .desktop-only { display: none; }
}
</style>
