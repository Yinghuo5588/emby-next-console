<template>
  <div class="stats-page">
    <PageHeader title="用户分析" />
    <StatsTabs />

    <!-- 顶部搜索 -->
    <div class="top-bar">
      <n-select
        v-model:value="selectedUserId"
        :options="userOptions"
        filterable
        placeholder="搜索用户..."
        clearable
        :loading="searchingUsers"
        :filter="() => true"
        remote
        @search="onSearchUser"
        @update:value="onSelectUser"
        size="small"
        class="user-search"
      />
    </div>

    <!-- 用户列表 -->
    <div class="ranking-card">
      <div v-if="loading" class="empty-text">加载中...</div>
      <div v-else-if="items.length === 0" class="empty-text">暂无数据</div>
      <div v-else class="ranking-list">
        <div v-for="(item, i) in items" :key="i"
          class="ranking-item"
          :class="{ active: selectedDetailUserId === item.user_id }"
          @click="selectUser(item.user_id)">
          <span class="ranking-num" :class="{ 'num-top': i < 3 }">{{ (page - 1) * size + i + 1 }}</span>
          <n-avatar :size="36" round class="ranking-avatar">{{ item.username?.charAt(0) || '?' }}</n-avatar>
          <div class="ranking-body">
            <div class="ranking-name">{{ item.username }}</div>
            <div class="ranking-meta">
              <span>{{ item.total_duration_hours }}h</span>
              <span>·</span>
              <span>{{ item.play_count }} 次</span>
            </div>
          </div>
          <div class="ranking-bars desktop-only">
            <div class="bar" :style="{ width: barWidth(item.total_duration_hours, maxDuration) + '%' }"></div>
          </div>
        </div>
      </div>
      <div v-if="total > size" class="pagination-row">
        <n-button size="small" :disabled="page <= 1" @click="page--">上一页</n-button>
        <span class="page-info">{{ page }} / {{ Math.ceil(total / size) }}</span>
        <n-button size="small" :disabled="page >= Math.ceil(total / size)" @click="page++">下一页</n-button>
      </div>
    </div>

    <!-- 用户画像抽屉 -->
    <n-drawer v-model:show="showDrawer" :width="isMobile ? undefined : 560" :placement="isMobile ? 'bottom' : 'right'" :height="isMobile ? '90vh' : undefined">
      <n-drawer-content v-if="userDetail" :title="userDetail.username" closable>

        <!-- KPI -->
        <div class="kpi-row">
          <div class="kpi-item">
            <div class="kpi-val">{{ userDetail.kpis.total_plays }}</div>
            <div class="kpi-lbl">播放次数</div>
          </div>
          <div class="kpi-item">
            <div class="kpi-val">{{ userDetail.kpis.total_duration_hours }}h</div>
            <div class="kpi-lbl">沉浸时长</div>
          </div>
          <div class="kpi-item">
            <div class="kpi-val">{{ userDetail.kpis.avg_session_min }}m</div>
            <div class="kpi-lbl">单次平均</div>
          </div>
        </div>

        <!-- 时间筛选 + 入驻天数 -->
        <div class="header-row">
          <div class="segment-group small">
            <button v-for="p in periodOptions" :key="p.value"
              class="seg-btn" :class="{ active: detailPeriod === p.value }"
              @click="detailPeriod = p.value">{{ p.label }}</button>
          </div>
          <span class="age-text">入驻 <b>{{ userDetail.account_age_days }}</b> 天</span>
        </div>

        <!-- 内容偏好 -->
        <div class="section-sub">
          <h4>内容偏好</h4>
          <div class="pref-row">
            <span class="pref-tag">{{ userDetail.preference.tag }}</span>
            <span class="pref-stats">电影 {{ userDetail.preference.movie_plays }} · 剧集 {{ userDetail.preference.episode_plays }}</span>
          </div>
          <div v-if="userDetail.top_fav" class="fav-item">
            <n-avatar :src="userDetail.top_fav.poster_url" :size="32" round />
            <div>
              <div class="fav-name">最爱: {{ userDetail.top_fav.name }}</div>
              <div class="fav-sub">{{ userDetail.top_fav.hours }}h</div>
            </div>
          </div>
        </div>

        <!-- 播放趋势 -->
        <div class="section-sub" v-if="trendHasData">
          <h4>播放趋势</h4>
          <AreaChart :xData="trendXData" :series="[{ name: '播放时长', data: trendYData }]" height="200px" />
        </div>

        <!-- 观影生物钟 -->
        <div class="section-sub" v-if="heatmapHasData">
          <h4>观影生物钟</h4>
          <HeatmapChart :data="userDetail.heatmap" height="240px" />
        </div>

        <!-- 软件分布 + 硬件分布 -->
        <div class="section-sub dist-row">
          <div>
            <h4>软件分布</h4>
            <PieChart v-if="userDetail.client_dist?.length > 0" :data="userDetail.client_dist" height="200px" />
            <div v-else class="empty-chart">暂无数据</div>
          </div>
          <div>
            <h4>硬件分布</h4>
            <PieChart v-if="userDetail.device_dist?.length > 0" :data="userDetail.device_dist" height="200px" />
            <div v-else class="empty-chart">暂无数据</div>
          </div>
        </div>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue'
import { NButton, NAvatar, NDrawer, NDrawerContent, NSelect } from 'naive-ui'
import { useWindowSize } from '@vueuse/core'
import PageHeader from '@/components/common/PageHeader.vue'
import StatsTabs from '@/components/stats/StatsTabs.vue'
import PieChart from '@/components/charts/PieChart.vue'
import AreaChart from '@/components/charts/AreaChart.vue'
import HeatmapChart from '@/components/charts/HeatmapChart.vue'
import { statsApiV3 } from '@/api/stats-v3'

const { width: winWidth } = useWindowSize()
const isMobile = computed(() => winWidth.value < 768)

const page = ref(1)
const size = ref(20)
const total = ref(0)
const items = ref<any[]>([])
const loading = ref(false)
const selectedDetailUserId = ref<string | null>(null)
const showDrawer = ref(false)
const userDetail = ref<any>(null)

// 搜索用户
const selectedUserId = ref<string | null>(null)
const userOptions = ref<{ label: string; value: string }[]>([])
const searchingUsers = ref(false)
let searchTimer: any = null

// 抽屉内时间筛选（默认7天）
const detailPeriod = ref('7d')
const periodOptions = [{ label: '7天', value: '7d' }, { label: '30天', value: '30d' }, { label: '90天', value: '90d' }, { label: '全部', value: 'all' }]

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

function onSelectUser(uid: string | null) {
  if (uid) selectUser(uid)
}

const maxDuration = computed(() => Math.max(...items.value.map(i => i.total_duration_hours), 1))

const trendXData = computed(() => Object.keys(userDetail.value?.trend || {}))
const trendYData = computed(() => Object.values(userDetail.value?.trend || {}) as number[])
const trendHasData = computed(() => Object.keys(userDetail.value?.trend || {}).length > 0)

const heatmapHasData = computed(() => {
  const hm = userDetail.value?.heatmap
  return hm?.some((row: number[]) => row.some((v: number) => v > 0))
})

function barWidth(val: number, max: number) { return max > 0 ? (val / max) * 100 : 0 }

async function loadRankings() {
  loading.value = true
  try {
    const res = await statsApiV3.userRankings({ period: '30d', page: page.value, size: size.value })
    const data = res.data?.data ?? res.data ?? {}
    items.value = data.items || []
    total.value = data.total || 0
  } finally { loading.value = false }
}

async function loadUserDetail() {
  if (!selectedDetailUserId.value) return
  const res = await statsApiV3.userDetail(selectedDetailUserId.value, detailPeriod.value)
  userDetail.value = res.data?.data ?? res.data
}

async function selectUser(uid: string) {
  selectedDetailUserId.value = uid
  showDrawer.value = true
  const res = await statsApiV3.userDetail(uid, detailPeriod.value)
  userDetail.value = res.data?.data ?? res.data
}

// 时间筛选变化重新加载详情
watch(detailPeriod, loadUserDetail)
watch(page, loadRankings)
onMounted(loadRankings)
</script>

<style scoped>
.stats-page { padding: 0.5rem 0; }
.top-bar { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem; }
.user-search { width: 100%; max-width: 300px; }
.ranking-card { background: var(--surface); border-radius: var(--radius-lg); padding: 0.5rem; border: 1px solid var(--border); }
.ranking-list { display: flex; flex-direction: column; }
.ranking-item { display: flex; align-items: center; gap: 0.5rem; padding: 0.6rem 0.5rem; border-radius: var(--radius); cursor: pointer; transition: background 0.15s; }
.ranking-item:hover, .ranking-item.active { background: var(--bg-secondary); }
.ranking-num { width: 24px; font-size: 0.8rem; font-weight: 700; color: var(--text-muted); text-align: center; flex-shrink: 0; }
.num-top { color: var(--brand); }
.ranking-avatar { flex-shrink: 0; background: var(--brand); color: #fff; font-weight: 700; }
.ranking-body { flex: 1; min-width: 0; }
.ranking-name { font-size: 0.9rem; font-weight: 600; color: var(--text); }
.ranking-meta { font-size: 0.75rem; color: var(--text-muted); display: flex; gap: 0.25rem; }
.ranking-bars { width: 80px; flex-shrink: 0; }
.bar { height: 4px; background: var(--brand); border-radius: 2px; transition: width 0.3s; }
.pagination-row { display: flex; align-items: center; justify-content: center; gap: 1rem; padding: 0.75rem 0; }
.page-info { font-size: 0.8rem; color: var(--text-muted); }
.empty-text { text-align: center; padding: 2rem; color: var(--text-muted); font-size: 0.85rem; }
.kpi-row { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
.kpi-item { flex: 1; text-align: center; background: var(--bg-secondary); border-radius: var(--radius); padding: 0.6rem 0.25rem; }
.kpi-val { font-size: 1.3rem; font-weight: 700; color: var(--text); }
.kpi-lbl { font-size: 0.7rem; color: var(--text-muted); }
.header-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.25rem; gap: 0.5rem; }
.segment-group { display: inline-flex; background: var(--bg-secondary); border-radius: var(--radius-lg); padding: 3px; }
.segment-group.small .seg-btn { padding: 4px 10px; font-size: 0.75rem; }
.seg-btn { border: none; background: none; padding: 6px 14px; font-size: 0.8rem; font-weight: 500; color: var(--text-muted); border-radius: var(--radius); cursor: pointer; transition: all 0.15s; font-family: inherit; }
.seg-btn.active { background: var(--surface); color: var(--text); box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.age-text { font-size: 0.8rem; color: var(--text-muted); white-space: nowrap; }
.age-text b { color: var(--brand); }
.section-sub { margin-bottom: 1.25rem; }
.section-sub h4 { font-size: 0.85rem; font-weight: 600; margin: 0 0 0.5rem; color: var(--text); }
.dist-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.pref-row { display: flex; align-items: center; gap: 0.75rem; }
.pref-tag { display: inline-block; padding: 0.15rem 0.6rem; background: var(--brand); color: #fff; border-radius: 1rem; font-size: 0.75rem; font-weight: 600; }
.pref-stats { font-size: 0.75rem; color: var(--text-muted); }
.fav-item { display: flex; align-items: center; gap: 0.5rem; margin-top: 0.5rem; }
.fav-name { font-size: 0.8rem; font-weight: 600; color: var(--text); }
.fav-sub { font-size: 0.7rem; color: var(--text-muted); }
.empty-chart { text-align: center; padding: 2rem 1rem; color: var(--text-muted); font-size: 0.8rem; }
@media (max-width: 767px) {
  .desktop-only { display: none; }
  .dist-row { grid-template-columns: 1fr; }
  .user-search { max-width: 100%; }
}
</style>
