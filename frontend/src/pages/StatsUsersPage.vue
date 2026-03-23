<template>
  <div class="stats-page">
    <PageHeader title="用户分析" desc="谁在看？怎么看的？">
      <template #actions>
        <n-button size="small" @click="showFilter = true">
          <span>筛选</span>
          <span v-if="period !== '30d'" class="filter-badge">1</span>
        </n-button>
      </template>
    </PageHeader>
    <StatsTabs />

    <div class="active-filters" v-if="period !== '30d'">
      <n-tag size="small" closable @close="period = '30d'">{{ periodLabel }}</n-tag>
    </div>

    <!-- 用户列表 -->
    <div class="ranking-card">
      <div v-if="loading" class="empty-text">加载中...</div>
      <div v-else-if="items.length === 0" class="empty-text">暂无数据</div>
      <div v-else class="ranking-list">
        <div v-for="(item, i) in items" :key="i"
          class="ranking-item"
          :class="{ active: selectedUserId === item.user_id }"
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

    <!-- 筛选抽屉 -->
    <n-drawer v-model:show="showFilter" :width="320" placement="bottom" :height="'auto'">
      <n-drawer-content title="筛选" closable :body-content-style="{ padding: '16px' }">
        <div class="filter-group">
          <div class="filter-label">时间范围</div>
          <n-button-group size="small">
            <n-button v-for="p in periodOptions" :key="p.value"
              :type="period === p.value ? 'primary' : 'default'"
              @click="period = p.value">{{ p.label }}</n-button>
          </n-button-group>
        </div>
        <n-button block type="primary" @click="showFilter = false" style="margin-top: 16px">确定</n-button>
      </n-drawer-content>
    </n-drawer>

    <!-- 用户画像抽屉 -->
    <n-drawer v-model:show="showDrawer" :width="480" placement="right">
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

        <div class="age-text">入驻服务器第 <b>{{ userDetail.account_age_days }}</b> 天</div>

        <!-- 徽章 -->
        <div class="section-sub" v-if="userDetail.badges.length > 0">
          <h4>成就徽章</h4>
          <div class="badge-grid">
            <div v-for="b in userDetail.badges" :key="b.id" class="badge-item">
              <div>
                <div class="badge-name">{{ b.name }}</div>
                <div class="badge-desc">{{ b.desc }}</div>
              </div>
            </div>
          </div>
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

        <!-- 时段柱状图 — BarChart -->
        <div class="section-sub" v-if="hourlyHasData">
          <h4>时段分布</h4>
          <BarChart :yData="hourLabels" :data="userDetail.hourly" :horizontal="false" height="180px" />
        </div>

        <!-- 设备环形图 — PieChart -->
        <div class="section-sub" v-if="userDetail.devices.length > 0">
          <h4>设备分布</h4>
          <PieChart :data="pieDevices" height="240px" />
        </div>

        <!-- 最近播放 -->
        <div class="section-sub" v-if="userDetail.recent_plays.length > 0">
          <h4>最近播放</h4>
          <div class="recent-list">
            <div v-for="r in userDetail.recent_plays" :key="r.item_id" class="recent-item">
              <n-avatar :src="r.poster_url" :size="28" round />
              <div class="recent-body">
                <div class="recent-name">{{ r.name }}</div>
                <div class="recent-meta">{{ r.date }} · {{ r.duration_min }}m</div>
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
import { NButton, NButtonGroup, NTag, NAvatar, NDrawer, NDrawerContent } from 'naive-ui'
import PageHeader from '@/components/common/PageHeader.vue'
import StatsTabs from '@/components/stats/StatsTabs.vue'
import PieChart from '@/components/charts/PieChart.vue'
import BarChart from '@/components/charts/BarChart.vue'
import { statsApiV3 } from '@/api/stats-v3'

const showFilter = ref(false)
const period = ref('30d')
const page = ref(1)
const size = ref(20)
const total = ref(0)
const items = ref<any[]>([])
const loading = ref(false)
const selectedUserId = ref<string | null>(null)
const showDrawer = ref(false)
const userDetail = ref<any>(null)

const periodOptions = [{ label: '30天', value: '30d' }, { label: '90天', value: '90d' }, { label: '全部', value: 'all' }]
const periodLabel = computed(() => periodOptions.find(p => p.value === period.value)?.label || '')
const maxDuration = computed(() => Math.max(...items.value.map(i => i.total_duration_hours), 1))

const hourLabels = Array.from({ length: 24 }, (_, i) => `${i}:00`)
const hourlyHasData = computed(() => userDetail.value?.hourly?.some((h: number) => h > 0))

// BarChart 需要 yData + data（垂直柱状图用 yData 作为 x 轴标签）
const pieDevices = computed(() => {
  if (!userDetail.value?.devices?.length) return []
  return userDetail.value.devices.map((d: any) => ({ name: d.device, value: d.count }))
})

function barWidth(val: number, max: number) { return max > 0 ? (val / max) * 100 : 0 }

async function loadRankings() {
  loading.value = true
  try {
    const res = await statsApiV3.userRankings({ period: period.value, page: page.value, size: size.value })
    const data = res.data?.data ?? res.data ?? {}
    items.value = data.items || []
    total.value = data.total || 0
  } finally { loading.value = false }
}

async function selectUser(uid: string) {
  selectedUserId.value = uid
  const res = await statsApiV3.userDetail(uid)
  userDetail.value = res.data?.data ?? res.data
  showDrawer.value = true
}

watch(period, () => { page.value = 1; loadRankings() })
watch(page, loadRankings)
onMounted(() => { loadRankings() })
</script>

<style scoped>
.stats-page { padding: 0.5rem 0; }
.active-filters { display: flex; gap: 0.5rem; margin-bottom: 0.75rem; }
.filter-badge { display: inline-flex; align-items: center; justify-content: center; width: 16px; height: 16px; border-radius: 50%; background: var(--brand); color: #fff; font-size: 0.65rem; margin-left: 4px; }
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
.filter-group { margin-bottom: 1rem; }
.filter-label { font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.5rem; }
.kpi-row { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
.kpi-item { flex: 1; text-align: center; background: var(--bg-secondary); border-radius: var(--radius); padding: 0.6rem 0.25rem; }
.kpi-val { font-size: 1.3rem; font-weight: 700; color: var(--text); }
.kpi-lbl { font-size: 0.7rem; color: var(--text-muted); }
.age-text { font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1.25rem; }
.age-text b { color: var(--brand); }
.section-sub { margin-bottom: 1.25rem; }
.section-sub h4 { font-size: 0.85rem; font-weight: 600; margin: 0 0 0.5rem; }
.badge-grid { display: flex; flex-direction: column; gap: 0.4rem; }
.badge-item { padding: 0.4rem 0.5rem; background: var(--bg-secondary); border-radius: var(--radius); }
.badge-name { font-size: 0.8rem; font-weight: 600; color: var(--text); }
.badge-desc { font-size: 0.7rem; color: var(--text-muted); }
.pref-row { display: flex; align-items: center; gap: 0.75rem; }
.pref-tag { display: inline-block; padding: 0.15rem 0.6rem; background: var(--brand); color: #fff; border-radius: 1rem; font-size: 0.75rem; font-weight: 600; }
.pref-stats { font-size: 0.75rem; color: var(--text-muted); }
.fav-item { display: flex; align-items: center; gap: 0.5rem; margin-top: 0.5rem; }
.fav-name { font-size: 0.8rem; font-weight: 600; color: var(--text); }
.fav-sub { font-size: 0.7rem; color: var(--text-muted); }
.recent-list { display: flex; flex-direction: column; gap: 0.4rem; }
.recent-item { display: flex; align-items: center; gap: 0.5rem; }
.recent-body { flex: 1; min-width: 0; }
.recent-name { font-size: 0.8rem; font-weight: 600; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.recent-meta { font-size: 0.7rem; color: var(--text-muted); }
@media (max-width: 767px) { .desktop-only { display: none; } }
</style>
