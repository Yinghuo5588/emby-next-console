<template>
  <div class="stats-page">
    <PageHeader title="内容分析" />
    <StatsTabs :filterActive="activeFilterCount > 0" @toggle-filter="showFilter = !showFilter" />

    <div class="active-filters" v-if="activeFilterCount > 0">
      <n-tag v-if="contentType !== 'all'" size="small" closable @close="contentType = 'all'">{{ contentTypeLabel }}</n-tag>
      <n-tag v-if="period !== '30d'" size="small" closable @close="period = '30d'">{{ periodLabel }}</n-tag>
      <n-tag v-if="sortBy !== 'duration'" size="small" closable @click="sortBy = 'duration'">{{ sortLabel }}</n-tag>
      <n-tag v-if="selectedUserId" size="small" closable @click="clearUserFilter">👤 {{ selectedUserName }}</n-tag>
    </div>

    <div class="content-list">
      <div v-if="loading" class="empty-text">加载中...</div>
      <div v-else-if="items.length === 0" class="empty-text">暂无数据</div>

      <div v-else class="card-list">
        <div
          v-for="(item, i) in items"
          :key="item.item_id"
          class="media-card"
          :class="{ active: selectedItemId === item.item_id }"
          @click="selectItem(item.item_id)"
        >
          <!-- 排名 -->
          <div class="card-rank" :class="{ 'rank-1': i === 0, 'rank-2': i === 1, 'rank-3': i === 2 }">
            <span>{{ (page - 1) * size + i + 1 }}</span>
          </div>

          <!-- 海报 -->
          <div class="poster-wrap">
            <img
              v-if="item.poster_url"
              :src="item.poster_url"
              class="poster-img"
              loading="lazy"
              @error="($event.target as HTMLImageElement).style.display='none'"
            />
            <div v-else class="poster-fallback">{{ item.name?.charAt(0) || '?' }}</div>
          </div>

          <!-- 信息 -->
          <div class="card-body">
            <div class="card-title">{{ item.display_title || item.name }}</div>
            <div class="card-tags">
              <span class="tag" :class="item.type === 'Movie' ? 'tag-movie' : 'tag-series'">
                {{ item.type === 'Movie' ? '电影' : '剧集' }}
              </span>
              <span v-for="tag in (item.quality_tags || []).slice(0, 3)" :key="tag" class="tag tag-quality">{{ tag }}</span>
            </div>
          </div>

          <!-- 右侧统计 -->
          <div class="card-stats">
            <div class="stat-play">
              <span class="stat-icon">▶</span>
              <span>{{ item.play_count }}</span>
            </div>
            <div class="stat-duration">
              <div class="duration-bar">
                <div class="duration-fill" :style="{ width: durPct(item.total_duration_min) + '%' }"></div>
              </div>
              <span class="duration-text">{{ formatDuration(item.total_duration_min) }}</span>
            </div>
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

    <!-- 详情抽屉（保留 hero 风格） -->
    <n-drawer v-model:show="showDetail" :width="isMobile ? undefined : 520" :placement="isMobile ? 'bottom' : 'right'" :height="isMobile ? '92vh' : undefined">
      <n-drawer-content v-if="detail" :title="detail.name" closable>
        <div class="detail-hero" :style="detailHeroStyle(detail)">
          <div class="detail-hero-overlay"></div>
          <div class="detail-poster-wrap">
            <img v-if="detail.poster_url" :src="detail.poster_url" class="detail-poster" loading="lazy" />
            <n-avatar v-else :size="64">{{ detail.name?.charAt(0) || '?' }}</n-avatar>
          </div>
          <div class="detail-hero-info">
            <h3>{{ detail.name }}</h3>
            <div class="detail-meta-row">
              <span class="tag" :class="detail.type === 'Movie' ? 'tag-movie' : 'tag-series'">{{ detail.type === 'Movie' ? '电影' : '剧集' }}</span>
              <span v-if="detail.production_year" class="tag tag-quality">{{ detail.production_year }}</span>
              <span v-for="tag in (detail.quality_tags || []).slice(0, 3)" :key="tag" class="tag tag-quality">{{ tag }}</span>
            </div>
            <p v-if="detail.overview" class="detail-overview">{{ detail.overview }}</p>
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
              <n-avatar :src="`/api/v1/manage/users/${v.user_id}/avatar`" :size="28" round fallback-src="">{{ v.username?.charAt(0) || '?' }}</n-avatar>
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
const activeFilterCount = computed(() =>
  (contentType.value !== 'all' ? 1 : 0) +
  (period.value !== '30d' ? 1 : 0) +
  (sortBy.value !== 'duration' ? 1 : 0) +
  (selectedUserId.value ? 1 : 0)
)

const trendXData = computed(() => Object.keys(detail.value?.trend || {}))
const trendSeries = computed(() => {
  const trend = detail.value?.trend || {}
  return [
    { name: '播放时长', data: Object.values(trend).map((v: any) => v.hours ?? 0) },
    { name: '播放次数', data: Object.values(trend).map((v: any) => v.plays ?? 0) },
  ]
})

function formatDuration(min: number): string {
  if (!min) return '0m'
  const h = Math.floor(min / 60)
  const m = Math.round(min % 60)
  if (h === 0) return `${m}m`
  if (m === 0) return `${h}h`
  return `${h}h ${m}m`
}

const maxDur = computed(() => Math.max(...items.value.map(i => i.total_duration_min || 1), 1))
function durPct(min: number): number {
  return Math.round((min / maxDur.value) * 100)
}

function detailHeroStyle(item: any) {
  const bg = item.backdrop_url || item.poster_url || ''
  const gradient = 'linear-gradient(90deg, rgba(8,10,18,0.35) 0%, rgba(8,10,18,0.45) 18%, rgba(8,10,18,0.72) 52%, rgba(8,10,18,0.92) 100%)'
  return {
    backgroundImage: bg ? `${gradient}, url(${bg})` : 'linear-gradient(135deg, #1f2937 0%, #0f172a 60%, #020617 100%)',
  }
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
.stats-page { padding: 0.5rem 0; }
.active-filters { display: flex; gap: 0.5rem; margin-bottom: 0.75rem; flex-wrap: wrap; }
.card-list { display: flex; flex-direction: column; gap: 10px; }

/* ===== 简洁卡片 ===== */
.media-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 14px;
  background: rgba(255,255,255,0.85);
  border: 1.5px solid rgba(0,0,0,0.10);
  cursor: pointer;
  transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
}
.media-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 28px rgba(15, 23, 42, 0.12);
  border-color: rgba(0,0,0,0.18);
}
.media-card.active {
  border-color: rgba(99, 102, 241, 0.6);
  box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.25), 0 8px 28px rgba(79, 70, 229, 0.10);
}

/* 排名 */
.card-rank {
  flex-shrink: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  font-size: 0.78rem;
  font-weight: 800;
  color: rgba(0,0,0,0.45);
  background: rgba(0,0,0,0.05);
  border: 1px solid rgba(0,0,0,0.08);
}
.card-rank.rank-1 { background: linear-gradient(135deg, #FFD700, #FFA500); color: #1a1a1a; border-color: rgba(255,215,0,0.4); }
.card-rank.rank-2 { background: linear-gradient(135deg, #C0C0C0, #9CA3AF); color: #1a1a1a; border-color: rgba(192,192,192,0.4); }
.card-rank.rank-3 { background: linear-gradient(135deg, #CD7F32, #B87333); color: #1a1a1a; border-color: rgba(205,127,50,0.4); }

/* 海报 */
.poster-wrap {
  flex-shrink: 0;
  width: 56px;
  aspect-ratio: 2 / 3;
  border-radius: 10px;
  overflow: hidden;
  background: rgba(0,0,0,0.04);
  border: 1px solid rgba(0,0,0,0.08);
}
.poster-img { width: 100%; height: 100%; object-fit: cover; display: block; aspect-ratio: 2 / 3; }
.poster-fallback {
  width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;
  font-size: 1.2rem; font-weight: 800; color: rgba(0,0,0,0.35);
  background: linear-gradient(135deg, rgba(99,102,241,.15), rgba(30,41,59,.08));
}

/* 信息区 */
.card-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.card-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: #1a1a2e;
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.card-tags { display: flex; gap: 6px; flex-wrap: wrap; }

/* 标签 */
.tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.68rem;
  font-weight: 700;
  line-height: 1.4;
}
.tag-movie { background: rgba(245, 158, 11, 0.15); color: #B45309; }
.tag-series { background: rgba(16, 185, 129, 0.15); color: #047857; }
.tag-quality { background: rgba(0,0,0,0.06); color: rgba(0,0,0,0.55); }

/* 右侧统计 */
.card-stats {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  min-width: 90px;
}
.stat-play {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.78rem;
  font-weight: 600;
  color: #2563EB;
}
.stat-icon { font-size: 0.65rem; }
.stat-duration {
  display: flex;
  align-items: center;
  gap: 6px;
}
.duration-bar {
  width: 50px;
  height: 4px;
  border-radius: 2px;
  background: rgba(0,0,0,0.06);
  overflow: hidden;
}
.duration-fill {
  height: 100%;
  border-radius: 2px;
  background: linear-gradient(90deg, #3B82F6, #06B6D4);
  transition: width .4s ease;
}
.duration-text {
  font-size: 0.75rem;
  font-weight: 700;
  color: #7C3AED;
  min-width: 45px;
  text-align: right;
}

/* 分页 & 空状态 */
.pagination-row { display: flex; align-items: center; justify-content: center; gap: 1rem; padding: 0.75rem 0; }
.page-info { font-size: 0.8rem; color: var(--text-muted); }
.empty-text { text-align: center; padding: 2rem; color: var(--text-muted); font-size: 0.85rem; }
.filter-group { margin-bottom: 1rem; }
.filter-label { font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.5rem; }

/* ===== 详情抽屉 hero 风格 ===== */
.detail-hero {
  position: relative; overflow: hidden; border-radius: 22px;
  min-height: 220px; background-size: cover; background-position: center;
  margin-bottom: 1rem; border: 1px solid rgba(255,255,255,0.08);
}
.detail-hero-overlay { position: absolute; inset: 0; background: radial-gradient(circle at 18% 22%, rgba(255,255,255,0.14) 0%, rgba(255,255,255,0) 34%); }
.detail-poster-wrap {
  position: absolute; left: 18px; bottom: 18px; z-index: 2;
  width: 92px; aspect-ratio: 2 / 3; border-radius: 16px; overflow: hidden;
  box-shadow: 0 18px 40px rgba(0,0,0,.35), 0 4px 12px rgba(0,0,0,.22);
  border: 1px solid rgba(255,255,255,.14); background: rgba(255,255,255,.08);
}
.detail-poster { width: 100%; height: 100%; object-fit: cover; display: block; aspect-ratio: 2 / 3; }
.detail-hero-info { position: relative; z-index: 2; margin-left: 128px; padding: 22px 18px 20px 0; color: #fff; }
.detail-hero-info h3 { margin: 0 0 10px; font-size: 1.3rem; line-height: 1.25; text-shadow: 0 3px 14px rgba(0,0,0,0.45); }
.detail-meta-row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
.detail-overview {
  margin: 0; font-size: 0.88rem; line-height: 1.7; color: rgba(255,255,255,0.78);
  text-shadow: 0 2px 10px rgba(0,0,0,0.35);
  display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden;
}
.detail-section { margin-bottom: 1.25rem; }
.detail-section h4 { font-size: 0.85rem; font-weight: 600; margin: 0 0 0.5rem; }
.viewer-list { display: flex; flex-direction: column; gap: 0.5rem; }
.viewer-row { display: flex; align-items: center; gap: 0.5rem; }
.viewer-body { flex: 1; }
.viewer-name { font-size: 0.8rem; font-weight: 600; }
.viewer-meta { font-size: 0.7rem; color: var(--text-muted); }

/* 移动端 */
@media (max-width: 767px) {
  .media-card { padding: 8px 10px; gap: 10px; border-radius: 12px; }
  .poster-wrap { width: 48px; aspect-ratio: 2 / 3; border-radius: 8px; }
  .card-title { font-size: 0.88rem; }
  .card-stats { min-width: 76px; }
  .duration-bar { width: 40px; }
  .duration-text { font-size: 0.7rem; min-width: 38px; }
  .detail-hero { min-height: 200px; }
  .detail-poster-wrap { width: 76px; aspect-ratio: 2 / 3; }
  .detail-hero-info { margin-left: 108px; padding: 18px 14px 18px 0; }
  .detail-overview { -webkit-line-clamp: 3; }
}
</style>
