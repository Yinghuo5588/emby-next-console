<template>
  <div class="stats-page">
    <PageHeader title="内容分析" />
    <StatsTabs :filterActive="activeFilterCount > 0" @toggle-filter="showFilter = !showFilter" />

    <div class="active-filters" v-if="activeFilterCount > 0">
      <n-tag v-if="contentType !== 'all'" size="small" closable @close="contentType = 'all'">{{ contentTypeLabel }}</n-tag>
      <n-tag v-if="period !== '30d'" size="small" closable @close="period = '30d'">{{ periodLabel }}</n-tag>
      <n-tag v-if="sortBy !== 'duration'" size="small" closable @close="sortBy = 'duration'">{{ sortLabel }}</n-tag>
      <n-tag v-if="selectedUserId" size="small" closable @close="clearUserFilter">👤 {{ selectedUserName }}</n-tag>
    </div>

    <div class="ranking-card">
      <div v-if="loading" class="empty-text">加载中...</div>
      <div v-else-if="items.length === 0" class="empty-text">暂无数据</div>
      <div v-else class="ranking-list">
        <div v-for="(item, i) in items" :key="i"
          class="ranking-item"
          :class="{ active: selectedItemId === item.item_id }"
          @click="selectItem(item.item_id)">
          <span class="ranking-num" :class="{ 'num-top': i < 3 }">{{ (page - 1) * size + i + 1 }}</span>
          <img v-if="item.poster_url" :src="item.poster_url" class="ranking-poster" loading="lazy" />
          <n-avatar v-else :size="36" class="ranking-avatar">{{ item.name?.charAt(0) || '?' }}</n-avatar>
          <div class="ranking-body">
            <div class="ranking-name">{{ item.name }}</div>
            <div class="ranking-meta">
              <span>{{ item.total_duration_min }}m</span>
              <span>·</span>
              <span>{{ item.play_count }} 次</span>
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
    <n-drawer v-model:show="showFilter" :width="320" placement="bottom" height="420px">
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
        <div class="filter-group">
          <div class="filter-label">按用户</div>
          <n-select
            v-model:value="selectedUserId"
            :options="userOptions"
            filterable
            placeholder="全部用户"
            clearable
            :loading="searchingUsers"
            :filter="() => true"
            remote
            @search="onSearchUser"
            size="small"
          />
        </div>
        <n-button block type="primary" @click="showFilter = false" style="margin-top: 16px">确定</n-button>
      </n-drawer-content>
    </n-drawer>

    <!-- 内容详情抽屉 -->
    <n-drawer v-model:show="showDetail" :width="isMobile ? undefined : 480" :placement="isMobile ? 'bottom' : 'right'" :height="isMobile ? '90vh' : undefined">
      <n-drawer-content v-if="detail" :title="detail.name" closable>
        <div class="detail-hero">
          <img v-if="detail.poster_url" :src="detail.poster_url" class="detail-poster" loading="lazy" />
          <n-avatar v-else :size="56">{{ detail.name?.charAt(0) || '?' }}</n-avatar>
          <div>
            <h3>{{ detail.name }}</h3>
            <div class="detail-meta">{{ detail.type === 'Movie' ? '电影' : '剧集' }}</div>
          </div>
        </div>

        <div class="detail-section" v-if="trendXData.length > 0">
          <h4>播放趋势</h4>
          <AreaChart :xData="trendXData" :series="trendSeries" height="220px" />
        </div>

        <div class="detail-section" v-if="detail.viewers?.length > 0">
          <h4>观看用户</h4>
          <div class="viewer-list">
            <div v-for="v in detail.viewers" :key="v.user_id" class="viewer-row">
              <n-avatar :size="28" round>{{ v.username?.charAt(0) || '?' }}</n-avatar>
              <div class="viewer-body">
                <div class="viewer-name">{{ v.username }}</div>
                <div class="viewer-meta">{{ v.duration_hours }}h · {{ v.play_count }}次</div>
              </div>
            </div>
          </div>
        </div>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue'
import { NButton, NButtonGroup, NTag, NAvatar, NDrawer, NDrawerContent, NSelect } from 'naive-ui'
import { useWindowSize } from '@vueuse/core'
import PageHeader from '@/components/common/PageHeader.vue'
import StatsTabs from '@/components/stats/StatsTabs.vue'
import AreaChart from '@/components/charts/AreaChart.vue'
import { statsApiV3 } from '@/api/stats-v3'

const { width: winWidth } = useWindowSize()
const isMobile = computed(() => winWidth.value < 768)

const showFilter = ref(false)
const showDetail = ref(false)
const contentType = ref('all')
const period = ref('30d')
const sortBy = ref('duration')
const page = ref(1)
const size = ref(20)
const total = ref(0)
const items = ref<any[]>([])
const loading = ref(false)
const detail = ref<any>(null)
const selectedItemId = ref<string | null>(null)
const selectedUserId = ref<string | null>(null)
const selectedUserName = ref('')

// 用户搜索
const userOptions = ref<{ label: string; value: string }[]>([])
const searchingUsers = ref(false)
let searchTimer: any = null

function onSearchUser(query: string) {
  clearTimeout(searchTimer)
  if (!query) { userOptions.value = []; return }
  searchTimer = setTimeout(async () => {
    searchingUsers.value = true
    try {
      const res = await statsApiV3.searchUsers(query)
      const users = res.data?.data ?? res.data ?? res.users ?? []
      userOptions.value = (Array.isArray(users) ? users : []).map((u: any) => ({
        label: u.username || u.name || u.display_name,
        value: u.user_id || u.id,
      }))
    } catch { userOptions.value = [] }
    finally { searchingUsers.value = false }
  }, 300)
}

function clearUserFilter() {
  selectedUserId.value = null
  selectedUserName.value = ''
}

const typeOptions = [{ label: '全部', value: 'all' }, { label: '电影', value: 'movie' }, { label: '剧集', value: 'series' }]
const periodOptions = [{ label: '30天', value: '30d' }, { label: '90天', value: '90d' }, { label: '全部', value: 'all' }]
const sortOptions = [{ label: '按时长', value: 'duration' }, { label: '按次数', value: 'count' }]

const contentTypeLabel = computed(() => typeOptions.find(t => t.value === contentType.value)?.label || '')
const periodLabel = computed(() => periodOptions.find(p => p.value === period.value)?.label || '')
const sortLabel = computed(() => sortOptions.find(s => s.value === sortBy.value)?.label || '')
const maxDuration = computed(() => Math.max(...items.value.map(i => i.total_duration_min), 1))
const activeFilterCount = computed(() =>
  (contentType.value !== 'all' ? 1 : 0) +
  (period.value !== '30d' ? 1 : 0) +
  (sortBy.value !== 'duration' ? 1 : 0) +
  (selectedUserId.value ? 1 : 0)
)

// detail trend
const trendXData = computed(() => Object.keys(detail.value?.trend || {}))
const trendSeries = computed(() => {
  const trend = detail.value?.trend || {}
  return [
    { name: '播放时长', data: Object.values(trend).map((v: any) => v.hours ?? 0) },
    { name: '播放次数', data: Object.values(trend).map((v: any) => v.plays ?? 0) },
  ]
})

function barWidth(val: number, max: number) { return max > 0 ? (val / max) * 100 : 0 }

async function loadRankings() {
  loading.value = true
  try {
    const params: any = {
      type: contentType.value,
      period: period.value,
      sort: sortBy.value,
      page: page.value,
      size: size.value,
    }
    if (selectedUserId.value) params.user_id = selectedUserId.value
    const res = await statsApiV3.contentRankings(params)
    const data = res.data?.data ?? res.data ?? {}
    items.value = data.items || []
    total.value = data.total || 0
  } finally { loading.value = false }
}

async function selectItem(item_id: string) {
  selectedItemId.value = item_id
  const res = await statsApiV3.contentDetail(item_id)
  detail.value = res.data?.data ?? res.data
  showDetail.value = true
}

watch([contentType, period, sortBy, selectedUserId], () => { page.value = 1; loadRankings() })
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
.ranking-poster { width: 36px; height: 50px; object-fit: cover; border-radius: 4px; flex-shrink: 0; }
.detail-poster { width: 56px; height: 80px; object-fit: cover; border-radius: 6px; flex-shrink: 0; }
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
.detail-hero { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem; }
.detail-hero h3 { margin: 0; font-size: 1rem; }
.detail-meta { font-size: 0.8rem; color: var(--text-muted); }
.detail-section { margin-bottom: 1.25rem; }
.detail-section h4 { font-size: 0.85rem; font-weight: 600; margin: 0 0 0.5rem; }
.viewer-list { display: flex; flex-direction: column; gap: 0.5rem; }
.viewer-row { display: flex; align-items: center; gap: 0.5rem; }
.viewer-body { flex: 1; }
.viewer-name { font-size: 0.8rem; font-weight: 600; }
.viewer-meta { font-size: 0.7rem; color: var(--text-muted); }
@media (max-width: 767px) { .desktop-only { display: none; } }
</style>
