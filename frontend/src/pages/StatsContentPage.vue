<template>
  <div class="stats-page">
    <PageHeader title="内容分析" />
    <StatsTabs :filterActive="activeFilterCount > 0" @toggle-filter="showFilter = !showFilter" />

    <div class="active-filters" v-if="activeFilterCount > 0">
      <n-tag v-if="contentType !== 'all'" size="small" closable @close="contentType = 'all'">{{ contentTypeLabel }}</n-tag>
      <n-tag v-if="period !== '30d'" size="small" closable @close="period = '30d'">{{ periodLabel }}</n-tag>
      <n-tag v-if="sortBy !== 'duration'" size="small" closable @close="sortBy = 'duration'">{{ sortLabel }}</n-tag>
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
          :style="heroStyle(item)"
          @click="selectItem(item.item_id)"
        >
          <div class="media-card-overlay"></div>
          <div class="media-card-glow"></div>

          <div class="card-rank" :class="{ 'rank-1': i === 0, 'rank-2': i === 1, 'rank-3': i === 2 }">
            <span>{{ (page - 1) * size + i + 1 }}</span>
          </div>

          <div class="poster-float">
            <img
              v-if="item.poster_url"
              :src="item.poster_url"
              class="poster-img"
              loading="lazy"
              @error="($event.target as HTMLImageElement).style.display='none'"
            />
            <div v-if="!item.poster_url" class="poster-fallback">
              {{ item.name?.charAt(0) || '?' }}
            </div>
          </div>

          <div class="media-card-body">
            <div class="media-card-topline">
              <span class="media-type" :class="item.type === 'Movie' ? 'type-movie' : 'type-series'">
                {{ item.type === 'Movie' ? '电影' : '剧集' }}
              </span>
              <span v-for="tag in (item.quality_tags || []).slice(0, 3)" :key="tag" class="glass-pill quality-pill">{{ tag }}</span>
            </div>

            <div class="media-title">{{ item.display_title || item.name }}</div>
            <div class="media-subtitle">{{ item.display_subtitle || defaultSubtitle(item.type) }}</div>

            <div class="media-footer-bar">
              <div class="footer-metrics">
                <span class="glass-pill stat-pill-blue">{{ item.play_count }} 次播放</span>
                <span class="glass-pill stat-pill-purple">{{ formatDuration(item.total_duration_min) }}</span>
              </div>
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
              <span class="glass-pill">{{ detail.type === 'Movie' ? '电影' : '剧集' }}</span>
              <span v-if="detail.production_year" class="glass-pill">{{ detail.production_year }}</span>
              <span v-for="tag in (detail.quality_tags || []).slice(0, 3)" :key="tag" class="glass-pill">{{ tag }}</span>
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

function defaultSubtitle(type: string): string {
  return type === 'Movie' ? '电影' : '剧集'
}

function formatDuration(min: number): string {
  if (!min) return '0m'
  const h = Math.floor(min / 60)
  const m = Math.round(min % 60)
  if (h === 0) return `${m}m`
  if (m === 0) return `${h}h`
  return `${h}h ${m}m`
}

function heroStyle(item: any) {
  const bg = item.backdrop_url || item.poster_url || ''
  const gradient = 'linear-gradient(90deg, rgba(8,10,18,0.30) 0%, rgba(8,10,18,0.45) 22%, rgba(8,10,18,0.72) 52%, rgba(8,10,18,0.92) 100%)'
  return {
    backgroundImage: bg ? `${gradient}, url(${bg})` : 'linear-gradient(135deg, #1f2937 0%, #0f172a 60%, #020617 100%)',
  }
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
.card-list { display: flex; flex-direction: column; gap: 14px; }

.media-card {
  position: relative;
  min-height: 186px;
  border-radius: 22px;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.08);
  background-size: cover;
  background-position: center;
  cursor: pointer;
  transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease;
  box-shadow: 0 12px 36px rgba(15, 23, 42, 0.18);
}
.media-card:hover { transform: translateY(-2px); box-shadow: 0 18px 46px rgba(15, 23, 42, 0.24); }
.media-card.active { border-color: rgba(99, 102, 241, 0.55); box-shadow: 0 18px 50px rgba(79, 70, 229, 0.24); }
.media-card-overlay,
.media-card-glow {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.media-card-glow {
  background: radial-gradient(circle at 18% 22%, rgba(255,255,255,0.16) 0%, rgba(255,255,255,0) 34%);
}
.card-rank {
  position: absolute;
  top: 14px;
  left: 14px;
  z-index: 4;
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  font-size: 0.86rem;
  font-weight: 800;
  color: #fff;
  background: rgba(15, 23, 42, 0.55);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.10);
}
.card-rank.rank-1 { background: linear-gradient(135deg, #FFD700, #FFA500); }
.card-rank.rank-2 { background: linear-gradient(135deg, #C0C0C0, #A0A0A0); }
.card-rank.rank-3 { background: linear-gradient(135deg, #CD7F32, #B87333); }
.poster-float {
  position: absolute;
  left: 20px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 3;
  width: 100px;
  aspect-ratio: 2 / 3;
  border-radius: 16px;
  overflow: hidden;
  background: rgba(255,255,255,0.08);
  box-shadow: 0 18px 40px rgba(0,0,0,0.35), 0 4px 12px rgba(0,0,0,0.22);
  border: 1px solid rgba(255,255,255,0.14);
}
.poster-img { width: 100%; height: 100%; object-fit: cover; display: block; aspect-ratio: 2 / 3; }
.poster-fallback {
  width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;
  font-size: 1.6rem; font-weight: 800; color: rgba(255,255,255,0.88);
  background: linear-gradient(135deg, rgba(99,102,241,.55), rgba(30,41,59,.95));
}
.media-card-body {
  position: relative;
  z-index: 3;
  margin-left: 144px;
  min-height: 186px;
  padding: 22px 20px 18px 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.media-card-topline { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 10px; }
.media-title {
  font-size: 1.28rem;
  font-weight: 800;
  color: #fff;
  line-height: 1.25;
  text-shadow: 0 3px 14px rgba(0,0,0,0.45);
  max-width: 92%;
}
.media-subtitle {
  margin-top: 6px;
  font-size: 0.88rem;
  color: rgba(255,255,255,0.72);
  text-shadow: 0 2px 10px rgba(0,0,0,0.35);
}
.media-footer-bar {
  margin-top: 16px;
  display: inline-flex;
  width: fit-content;
  max-width: 100%;
  padding: 8px 10px;
  border-radius: 999px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.12);
  backdrop-filter: blur(14px);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.08);
}
.footer-metrics { display: flex; gap: 8px; flex-wrap: wrap; }
.glass-pill {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
  color: rgba(255,255,255,0.88);
  background: rgba(255,255,255,0.10);
  border: 1px solid rgba(255,255,255,0.10);
  backdrop-filter: blur(10px);
}
.media-type.type-movie { background: rgba(245, 158, 11, 0.20); }
.media-type.type-series { background: rgba(16, 185, 129, 0.20); }
.stat-pill-blue { background: rgba(59, 130, 246, 0.20); }
.stat-pill-purple { background: rgba(168, 85, 247, 0.20); }
.quality-pill { background: rgba(15, 23, 42, 0.35); }

.pagination-row { display: flex; align-items: center; justify-content: center; gap: 1rem; padding: 0.75rem 0; }
.page-info { font-size: 0.8rem; color: var(--text-muted); }
.empty-text { text-align: center; padding: 2rem; color: var(--text-muted); font-size: 0.85rem; }
.filter-group { margin-bottom: 1rem; }
.filter-label { font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.5rem; }

.detail-hero {
  position: relative;
  overflow: hidden;
  border-radius: 22px;
  min-height: 220px;
  background-size: cover;
  background-position: center;
  margin-bottom: 1rem;
  border: 1px solid rgba(255,255,255,0.08);
}
.detail-hero-overlay { position: absolute; inset: 0; background: radial-gradient(circle at 18% 22%, rgba(255,255,255,0.14) 0%, rgba(255,255,255,0) 34%); }
.detail-poster-wrap {
  position: absolute; left: 18px; bottom: 18px; z-index: 2;
  width: 92px; aspect-ratio: 2 / 3; border-radius: 16px; overflow: hidden;
  box-shadow: 0 18px 40px rgba(0,0,0,.35), 0 4px 12px rgba(0,0,0,.22);
  border: 1px solid rgba(255,255,255,.14);
  background: rgba(255,255,255,.08);
}
.detail-poster { width: 100%; height: 100%; object-fit: cover; display: block; aspect-ratio: 2 / 3; }
.detail-hero-info {
  position: relative; z-index: 2; margin-left: 128px; padding: 22px 18px 20px 0; color: #fff;
}
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

@media (max-width: 767px) {
  .media-card { min-height: 170px; border-radius: 18px; }
  .poster-float { width: 78px; aspect-ratio: 2 / 3; left: 16px; }
  .media-card-body { margin-left: 112px; min-height: 170px; padding: 18px 14px 16px 0; }
  .media-title { font-size: 1.02rem; max-width: 100%; }
  .media-subtitle { font-size: 0.8rem; }
  .media-footer-bar { margin-top: 12px; border-radius: 16px; }
  .detail-hero { min-height: 200px; }
  .detail-poster-wrap { width: 76px; aspect-ratio: 2 / 3; }
  .detail-hero-info { margin-left: 108px; padding: 18px 14px 18px 0; }
  .detail-overview { -webkit-line-clamp: 3; }
}
</style>
