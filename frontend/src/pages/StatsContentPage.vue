<template>
  <div class="stats-page">
    <PageHeader title="内容分析" />
    <StatsTabs :filterActive="activeFilterCount > 0" @toggle-filter="showFilter = !showFilter" />

    <!-- 激活的筛选标签 -->
    <div class="active-filters" v-if="activeFilterCount > 0">
      <n-tag v-if="contentType !== 'all'" size="small" closable @close="contentType = 'all'">{{ contentTypeLabel }}</n-tag>
      <n-tag v-if="period !== '30d'" size="small" closable @close="period = '30d'">{{ periodLabel }}</n-tag>
      <n-tag v-if="sortBy !== 'duration'" size="small" closable @close="sortBy = 'duration'">{{ sortLabel }}</n-tag>
      <n-tag v-if="selectedUserId" size="small" closable @click="clearUserFilter">👤 {{ selectedUserName }}</n-tag>
    </div>

    <!-- 列表 -->
    <div class="content-list">
      <div v-if="loading" class="empty-text">加载中...</div>
      <div v-else-if="items.length === 0" class="empty-text">暂无数据</div>

      <div v-else class="card-list">
        <div
          v-for="(item, i) in items"
          :key="item.item_id"
          class="content-card"
          :class="{ active: selectedItemId === item.item_id }"
          @click="selectItem(item.item_id)"
        >
          <!-- 排名 -->
          <div class="card-rank" :class="{ 'rank-1': i === 0, 'rank-2': i === 1, 'rank-3': i === 2 }">
            <span>{{ (page - 1) * size + i + 1 }}</span>
          </div>

          <!-- 封面 -->
          <div class="card-cover">
            <img
              v-if="item.poster_url"
              :src="item.poster_url"
              class="cover-img"
              loading="lazy"
              @error="($event.target as HTMLImageElement).style.display='none'"
            />
            <div v-if="!item.poster_url" class="cover-fallback">
              {{ item.name?.charAt(0) || '?' }}
            </div>
          </div>

          <!-- 信息 -->
          <div class="card-info">
            <div class="card-title">{{ item.name }}</div>
            <div class="card-sub">
              <span class="card-type" :class="item.type === 'Movie' ? 'type-movie' : 'type-series'">
                {{ item.type === 'Movie' ? '电影' : '剧集' }}
              </span>
              <span class="tag-pill tag-plays">{{ item.play_count }} 次</span>
              <span class="tag-pill tag-duration">{{ formatDuration(item.total_duration_min) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 分页 -->
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
              <n-avatar :src="`/api/v1/proxy/user_image/${v.user_id}`" :size="28" round fallback-src="">{{ v.username?.charAt(0) || '?' }}</n-avatar>
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

function formatDuration(min: number): string {
  if (!min) return '0m'
  const h = Math.floor(min / 60)
  const m = Math.round(min % 60)
  if (h === 0) return `${m}m`
  if (m === 0) return `${h}h`
  return `${h}h ${m}m`
}

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
.stats-page {
  padding: 0.5rem 0;
}

.active-filters {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  flex-wrap: wrap;
}

/* ── 卡片列表 ── */
.card-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.content-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: var(--surface);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.content-card:hover {
  background: var(--surface-hover);
  border-color: var(--border-strong);
  transform: translateY(-1px);
  box-shadow: var(--shadow);
}

.content-card.active {
  background: var(--brand-light);
  border-color: var(--brand);
}

/* ── 排名 ── */
.card-rank {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--text-muted);
  background: var(--bg-secondary);
  flex-shrink: 0;
}

.card-rank.rank-1 {
  background: linear-gradient(135deg, #FFD700, #FFA500);
  color: #fff;
  box-shadow: 0 2px 8px rgba(255, 165, 0, 0.35);
}

.card-rank.rank-2 {
  background: linear-gradient(135deg, #C0C0C0, #A0A0A0);
  color: #fff;
  box-shadow: 0 2px 8px rgba(160, 160, 160, 0.3);
}

.card-rank.rank-3 {
  background: linear-gradient(135deg, #CD7F32, #B87333);
  color: #fff;
  box-shadow: 0 2px 8px rgba(205, 127, 50, 0.3);
}

/* ── 封面 ── */
.card-cover {
  width: 56px;
  height: 78px;
  flex-shrink: 0;
  border-radius: 8px;
  overflow: hidden;
  background: var(--bg-secondary);
  position: relative;
}

.cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.cover-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--text-muted);
  background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
}

/* ── 信息区 ── */
.card-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.card-title {
  font-size: 0.92rem;
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.3;
}

.card-sub {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.card-type {
  display: inline-flex;
  align-items: center;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 500;
  line-height: 1.5;
}

.type-movie {
  background: rgba(255, 149, 0, 0.1);
  color: #e68a00;
}

.type-series {
  background: rgba(52, 199, 89, 0.1);
  color: #28a745;
}

/* ── 彩色小标签 ── */
.tag-pill {
  display: inline-flex;
  align-items: center;
  padding: 1px 7px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 500;
  line-height: 1.6;
}

.tag-plays {
  background: rgba(0, 122, 255, 0.1);
  color: #007AFF;
}

.tag-duration {
  background: rgba(175, 82, 222, 0.1);
  color: #AF52DE;
}

/* ── 分页 ── */
.pagination-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 0.75rem 0;
}

.page-info {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.empty-text {
  text-align: center;
  padding: 2rem;
  color: var(--text-muted);
  font-size: 0.85rem;
}

/* ── 筛选 ── */
.filter-group {
  margin-bottom: 1rem;
}

.filter-label {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

/* ── 详情抽屉 ── */
.detail-hero {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.detail-hero h3 {
  margin: 0;
  font-size: 1rem;
}

.detail-meta {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.detail-poster {
  width: 56px;
  height: 80px;
  object-fit: cover;
  border-radius: 6px;
  flex-shrink: 0;
}

.detail-section {
  margin-bottom: 1.25rem;
}

.detail-section h4 {
  font-size: 0.85rem;
  font-weight: 600;
  margin: 0 0 0.5rem;
}

.viewer-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.viewer-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.viewer-body {
  flex: 1;
}

.viewer-name {
  font-size: 0.8rem;
  font-weight: 600;
}

.viewer-meta {
  font-size: 0.7rem;
  color: var(--text-muted);
}

/* ── 暗色主题 ── */
:root.dark .type-movie {
  background: rgba(255, 149, 0, 0.15);
  color: #ffa940;
}

:root.dark .type-series {
  background: rgba(52, 199, 89, 0.15);
  color: #51cf66;
}

:root.dark .tag-plays {
  background: rgba(0, 122, 255, 0.18);
  color: #5AC8FA;
}

:root.dark .tag-duration {
  background: rgba(175, 82, 222, 0.18);
  color: #BF7FEF;
}

/* ── 移动端 ── */
@media (max-width: 767px) {
  .content-card {
    padding: 8px 10px;
    gap: 10px;
  }

  .card-cover {
    width: 48px;
    height: 67px;
  }

  .card-title {
    font-size: 0.85rem;
  }

  .duration-bar-bg {
    display: none;
  }
}
</style>
